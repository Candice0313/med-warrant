"""test_tier_classifier.py — tier selection contract.

Invariants:
  - empty retrieval → model_prior with no snippets
  - strongest tier by ceiling wins, even if another source has higher overlap score
  - every retrieved source produces a grounding snippet
  - snippets are truncated to ≤300 chars
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from capping import EVIDENCE_CEILINGS
from evidence_store import RetrievedSource
from models import EvidenceSource
from tier_classifier import classify


def _src(source_id: str, tier: str, text: str = "evidence text") -> RetrievedSource:
    return RetrievedSource(
        source=EvidenceSource(
            source_id=source_id,
            title=f"Title {source_id}",
            tier=tier,
            text=text,
            url="https://example.org",
            topics=[],
        ),
        score=1.0,
    )


# --- model_prior fallback -------------------------------------------------

def test_empty_retrieval_returns_model_prior():
    tier, snippets = classify([])
    assert tier == "model_prior"
    assert snippets == []


# --- strongest-tier selection ---------------------------------------------

def test_picks_systematic_review_over_guideline_regardless_of_score():
    expert = _src("a", "expert")
    expert.score = 10.0
    sr = _src("b", "systematic_review")
    sr.score = 1.0
    tier, _ = classify([expert, sr])
    assert tier == "systematic_review"


def test_picks_rct_over_cohort_over_expert():
    cohort = _src("c", "cohort")
    rct = _src("d", "rct")
    expert = _src("e", "expert")
    tier, _ = classify([expert, cohort, rct])
    assert tier == "rct"


def test_single_source_returns_its_tier():
    tier, _ = classify([_src("x", "guideline")])
    assert tier == "guideline"


# --- grounding snippets ---------------------------------------------------

def test_one_snippet_per_retrieved_source():
    sources = [_src("a", "rct"), _src("b", "cohort"), _src("c", "expert")]
    _, snippets = classify(sources)
    assert len(snippets) == 3


def test_snippet_source_id_matches():
    retrieved = [_src("my_source", "guideline", "some text")]
    _, snippets = classify(retrieved)
    assert snippets[0].source_id == "my_source"


def test_snippets_truncated_to_300_chars():
    long_text = "x" * 600
    retrieved = [_src("z", "rct", long_text)]
    _, snippets = classify(retrieved)
    assert len(snippets[0].snippet) <= 300


def test_short_text_not_truncated():
    short_text = "hello world"
    retrieved = [_src("s", "cohort", short_text)]
    _, snippets = classify(retrieved)
    assert snippets[0].snippet == short_text


def test_snippet_tier_matches_source_tier():
    retrieved = [_src("t", "expert", "text")]
    _, snippets = classify(retrieved)
    assert snippets[0].tier == "expert"
