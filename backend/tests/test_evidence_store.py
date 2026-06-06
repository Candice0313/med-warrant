"""test_evidence_store.py — retrieval contract.

Invariants:
  - all 30 seed sources load cleanly
  - retrieve() returns only sources with >0 topic overlap, ranked descending
  - top_k caps the result count
  - sources with zero overlap never appear
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from capping import EVIDENCE_CEILINGS
from evidence_store import all_sources, retrieve


def test_all_30_sources_load():
    assert len(all_sources()) == 30


def test_every_source_has_a_valid_tier():
    for src in all_sources():
        assert src.tier in EVIDENCE_CEILINGS, f"unknown tier {src.tier!r} on {src.source_id}"


def test_retrieve_excludes_zero_overlap_sources():
    results = retrieve(["xylophone", "quasar"])
    assert results == []


def test_retrieve_results_ranked_descending_by_score():
    results = retrieve(["warfarin", "nsaid", "ibuprofen", "bleeding"])
    assert len(results) > 1
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_all_results_have_positive_score():
    results = retrieve(["warfarin"])
    assert len(results) > 0
    assert all(r.score > 0 for r in results)


def test_retrieve_top_k_limits_result_count():
    results = retrieve(["warfarin", "nsaid", "ibuprofen", "bleeding", "anticoagulant"], top_k=3)
    assert len(results) <= 3


def test_retrieve_default_top_k_is_five():
    # The warfarin+nsaid query matches more than 5 sources; default should cap at 5.
    results = retrieve(["warfarin", "nsaid", "ibuprofen", "bleeding"])
    assert len(results) <= 5


def test_retrieved_source_fields_are_populated():
    results = retrieve(["warfarin"])
    src = results[0].source
    assert src.source_id
    assert src.title
    assert src.text
    assert src.url
    assert isinstance(src.topics, list)
