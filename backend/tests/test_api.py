"""test_api.py — FastAPI endpoint contract (uses TestClient, no network).

Key invariants:
  - /api/judge returns one verdict per dimension
  - summary counts (trustworthy + caution + escalated) == len(dimensions)
  - no "overall_score" / "average" / "score" field anywhere in the judge response
  - displayed_confidence never exceeds the tier ceiling in any verdict
  - /api/queue contains only escalated, unreviewed verdicts
  - /api/review marks a verdict reviewed and removes it from the queue
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from capping import EVIDENCE_CEILINGS
from main import app

client = TestClient(app)

AGGREGATE_BANNED = {"overall_score", "average_score", "score", "aggregate", "mean"}
_DB_PATH = Path(__file__).parent.parent.parent / "data" / "verdicts.json"


@pytest.fixture(autouse=True, scope="module")
def clean_db():
    """Remove the verdicts DB before the module runs so tests start from a clean slate."""
    if _DB_PATH.exists():
        _DB_PATH.unlink()
    yield
    # leave DB in place after tests so humans can inspect it


# --- /api/cases -----------------------------------------------------------

def test_list_cases_returns_four_cases():
    r = client.get("/api/cases")
    assert r.status_code == 200
    assert len(r.json()) == 4


def test_list_cases_have_required_fields():
    cases = client.get("/api/cases").json()
    for c in cases:
        assert "id" in c
        assert "patient_question" in c
        assert "complexity" in c


def test_get_case_by_id():
    r = client.get("/api/cases/case_0421")
    assert r.status_code == 200
    c = r.json()
    assert c["id"] == "case_0421"
    assert len(c["dimensions"]) == 4


def test_get_nonexistent_case_is_404():
    assert client.get("/api/cases/nonexistent").status_code == 404


# --- /api/judge -----------------------------------------------------------

@pytest.fixture(scope="module")
def judge_response_0421():
    return client.post("/api/judge", json={"case_id": "case_0421"}).json()


def test_judge_returns_200(judge_response_0421):
    r = client.post("/api/judge", json={"case_id": "case_0421"})
    assert r.status_code == 200


def test_judge_returns_one_verdict_per_dimension(judge_response_0421):
    assert len(judge_response_0421["verdicts"]) == 4


def test_summary_counts_partition_verdicts(judge_response_0421):
    s = judge_response_0421["summary"]
    total = s["trustworthy"] + s["caution"] + s["escalated"]
    assert total == len(judge_response_0421["verdicts"])


def test_summary_has_no_aggregate_score(judge_response_0421):
    s = judge_response_0421["summary"]
    for bad in AGGREGATE_BANNED:
        assert bad not in s, f"banned field {bad!r} in summary"
    # mixed_average_suppressed is allowed (shown struck-through in UI) but must not be used in logic
    assert "mixed_average_suppressed" in s


def test_judge_response_root_has_no_aggregate_score(judge_response_0421):
    for bad in AGGREGATE_BANNED:
        assert bad not in judge_response_0421, f"banned field {bad!r} at response root"


def test_displayed_confidence_never_exceeds_ceiling(judge_response_0421):
    for v in judge_response_0421["verdicts"]:
        ceiling = EVIDENCE_CEILINGS[v["grounded_tier"]]
        assert v["displayed_confidence"] <= ceiling + 1e-9, (
            f"{v['verdict_id']}: displayed {v['displayed_confidence']} > ceiling {ceiling}"
        )


def test_displayed_confidence_never_inflated(judge_response_0421):
    for v in judge_response_0421["verdicts"]:
        assert v["displayed_confidence"] <= v["model_confidence"] + 1e-9


def test_verdict_fields_present(judge_response_0421):
    required = {
        "verdict_id", "case_id", "dimension", "safety_critical", "claim_scope",
        "model_confidence", "model_reasoning", "grounded_tier",
        "grounding", "displayed_confidence",
    }
    for v in judge_response_0421["verdicts"]:
        missing = required - set(v.keys())
        assert not missing, f"verdict missing fields: {missing}"


def test_judge_unknown_case_is_404():
    r = client.post("/api/judge", json={"case_id": "nonexistent"})
    assert r.status_code == 404


def test_judge_all_four_cases():
    for case_id in ["case_0421", "case_0588", "case_0712", "case_0934"]:
        r = client.post("/api/judge", json={"case_id": case_id})
        assert r.status_code == 200, f"failed for {case_id}"
        data = r.json()
        assert len(data["verdicts"]) > 0
        s = data["summary"]
        total = s["trustworthy"] + s["caution"] + s["escalated"]
        assert total == len(data["verdicts"])


# --- /api/evidence --------------------------------------------------------

def test_evidence_search_returns_results():
    r = client.get("/api/evidence?q=warfarin")
    assert r.status_code == 200
    sources = r.json()
    assert len(sources) > 0


def test_evidence_search_results_match_query():
    sources = client.get("/api/evidence?q=warfarin").json()
    for s in sources:
        in_title = "warfarin" in s["title"].lower()
        in_topics = any("warfarin" in t.lower() for t in s["topics"])
        assert in_title or in_topics, f"source {s['source_id']} does not match 'warfarin'"


def test_evidence_no_query_returns_all():
    r = client.get("/api/evidence")
    assert r.status_code == 200
    assert len(r.json()) == 30


# --- /api/queue and /api/review ------------------------------------------

def test_queue_contains_escalated_verdicts_after_judging():
    """Judging case_0421 must produce at least one low-confidence escalation in the queue."""
    client.post("/api/judge", json={"case_id": "case_0421"})
    queue = client.get("/api/queue").json()
    assert len(queue) > 0, "expected ≥1 escalated verdict after judging case_0421"
    for v in queue:
        assert v["escalation"] is not None
        assert v["human_review"] is None


def test_review_approve_removes_from_queue():
    # Judge to populate the queue (case_0421 already judged above, but idempotent)
    client.post("/api/judge", json={"case_id": "case_0421"})
    queue_before = client.get("/api/queue").json()
    assert queue_before, "queue must be non-empty (case_0421 has low-confidence escalations)"
    verdict_id = queue_before[0]["verdict_id"]
    r = client.post("/api/review", json={
        "verdict_id": verdict_id,
        "decision": "approve",
        "note": "Looks correct given clinical context.",
    })
    assert r.status_code == 200
    reviewed = r.json()
    assert reviewed["human_review"]["decision"] == "approve"
    # Should no longer appear in queue
    queue_after = client.get("/api/queue").json()
    ids_after = {v["verdict_id"] for v in queue_after}
    assert verdict_id not in ids_after
