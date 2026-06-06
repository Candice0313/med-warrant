"""test_grader.py — grading pipeline contract (MockProvider, real retrieval).

Invariants carried through from §2 into the full pipeline:
  - every Verdict respects the ceiling invariant
  - every Verdict is never inflated
  - individual-scope dimensions are capped at INDIVIDUAL_SCOPE_CEILING
  - safety-critical + ungrounded → danger escalation
  - one verdict per dimension, keyed correctly
  - no aggregate/average score field on any Verdict
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path

import pytest

from capping import EVIDENCE_CEILINGS, INDIVIDUAL_SCOPE_CEILING
from grader import grade_case, grade_dimension
from llm_provider import MockProvider
from models import Case, Dimension

PROVIDER = MockProvider()
CASES_DIR = Path(__file__).parent.parent.parent / "data" / "cases"


def _load_case(case_id: str) -> Case:
    return Case(**json.loads((CASES_DIR / f"{case_id}.json").read_text()))


# --- Parametrize over all four seed cases ---------------------------------

ALL_CASE_IDS = ["case_0421", "case_0588", "case_0712", "case_0934"]


@pytest.fixture(params=ALL_CASE_IDS)
def any_case(request) -> Case:
    return _load_case(request.param)


def test_ceiling_invariant_holds_for_every_verdict(any_case):
    for v in grade_case(any_case, PROVIDER):
        assert v.displayed_confidence <= EVIDENCE_CEILINGS[v.grounded_tier] + 1e-9, (
            f"{v.verdict_id}: displayed {v.displayed_confidence} > ceiling "
            f"{EVIDENCE_CEILINGS[v.grounded_tier]} for tier {v.grounded_tier}"
        )


def test_never_inflates_above_model_confidence(any_case):
    for v in grade_case(any_case, PROVIDER):
        assert v.displayed_confidence <= v.model_confidence + 1e-9, (
            f"{v.verdict_id}: displayed {v.displayed_confidence} > model {v.model_confidence}"
        )


def test_one_verdict_per_dimension(any_case):
    verdicts = grade_case(any_case, PROVIDER)
    assert len(verdicts) == len(any_case.dimensions)


def test_verdict_ids_match_dimensions(any_case):
    verdicts = grade_case(any_case, PROVIDER)
    expected_ids = {f"{any_case.id}:{d.id}" for d in any_case.dimensions}
    actual_ids = {v.verdict_id for v in verdicts}
    assert actual_ids == expected_ids


def test_verdict_has_no_aggregate_score_field(any_case):
    for v in grade_case(any_case, PROVIDER):
        v_dict = v.model_dump()
        for bad_key in ("overall_score", "average_score", "score", "aggregate"):
            assert bad_key not in v_dict, f"banned field {bad_key!r} found on {v.verdict_id}"


# --- individual-scope cap -------------------------------------------------

def test_individual_scope_dimensions_capped_at_60_pct():
    case = _load_case("case_0421")
    individual_dims = [d for d in case.dimensions if d.claim_scope == "individual"]
    assert individual_dims, "test requires at least one individual-scope dimension in case_0421"
    for dim in individual_dims:
        v = grade_dimension(case, dim, PROVIDER)
        assert v.displayed_confidence <= INDIVIDUAL_SCOPE_CEILING + 1e-9, (
            f"{v.verdict_id}: individual-scope verdict exceeds {INDIVIDUAL_SCOPE_CEILING}"
        )


# --- safety-critical + ungrounded → escalation ---------------------------

def test_safety_critical_dimension_with_no_matching_evidence_escalates():
    """A safety dimension whose topics match nothing in the library → model_prior → danger."""
    dim = Dimension(
        id="test_ungrounded",
        label="Ungrounded safety claim",
        safety_critical=True,
        claim_scope="population",
        topics=["xylophone", "quasar"],   # guaranteed no evidence match
    )
    case = _load_case("case_0421")
    v = grade_dimension(case, dim, PROVIDER)
    assert v.grounded_tier == "model_prior"
    assert v.escalation is not None
    assert v.escalation.severity == "danger"
    assert v.escalation.reason == "unverified_safety_claim"


# --- grounding actually clears escalation --------------------------------

def test_drug_interaction_safety_grounds_to_strong_evidence():
    """case_0421 drug-interaction dimension has rich topic matches; should ground above model_prior."""
    case = _load_case("case_0421")
    drug_dim = next(d for d in case.dimensions if d.id == "drug_interaction_safety")
    v = grade_dimension(case, drug_dim, PROVIDER)
    assert v.grounded_tier != "model_prior", (
        "drug_interaction_safety has multiple systematic-review matches; "
        "should ground to at least expert level"
    )


# --- naturally-escalated verdicts (low_confidence path) ------------------

def test_monitoring_followup_case_0421_escalates_as_low_confidence():
    """Individual-scope, rct-grounded monitoring verdict lands at 0.45 < 0.50 threshold."""
    case = _load_case("case_0421")
    dim = next(d for d in case.dimensions if d.id == "monitoring_followup")
    v = grade_dimension(case, dim, PROVIDER)
    assert v.displayed_confidence < 0.50
    assert v.escalation is not None
    assert v.escalation.reason == "low_confidence"
    assert v.escalation.severity == "warning"


def test_caregiver_instructions_case_0712_escalates_as_low_confidence():
    """Expert-only evidence + low model confidence → displayed < 0.50."""
    case = _load_case("case_0712")
    dim = next(d for d in case.dimensions if d.id == "caregiver_instructions")
    v = grade_dimension(case, dim, PROVIDER)
    assert v.displayed_confidence < 0.50
    assert v.escalation is not None
    assert v.escalation.reason == "low_confidence"


# --- MockProvider determinism --------------------------------------------

def test_mock_provider_is_deterministic():
    case = _load_case("case_0421")
    verdicts_a = grade_case(case, PROVIDER)
    verdicts_b = grade_case(case, PROVIDER)
    for va, vb in zip(verdicts_a, verdicts_b):
        assert va.model_confidence == vb.model_confidence
        assert va.displayed_confidence == vb.displayed_confidence
