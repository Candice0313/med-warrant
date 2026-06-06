"""test_capping.py — enforce the invariants that ARE the thesis.

Run from the backend/ directory:  pytest -q
These tests are the contract. If a refactor breaks one, the refactor is wrong.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from capping import (
    EVIDENCE_CEILINGS,
    INDIVIDUAL_SCOPE_CEILING,
    LOW_CONFIDENCE_ESCALATION,
    TIER_ORDER,
    cap_confidence,
    escalation,
    evaluate,
)

ALL_TIERS = list(EVIDENCE_CEILINGS.keys())


# --- Invariant 1: displayed confidence never exceeds the tier ceiling ------------

@pytest.mark.parametrize("tier", ALL_TIERS)
@pytest.mark.parametrize("conf", [0.0, 0.3, 0.5, 0.7, 0.88, 0.95, 1.0])
def test_never_exceeds_ceiling(tier, conf):
    assert cap_confidence(conf, tier) <= EVIDENCE_CEILINGS[tier] + 1e-9


# --- Invariant 2: displayed confidence never exceeds model confidence ------------

@pytest.mark.parametrize("tier", ALL_TIERS)
@pytest.mark.parametrize("conf", [0.0, 0.2, 0.41, 0.6, 0.9, 1.0])
def test_never_inflates(tier, conf):
    assert cap_confidence(conf, tier) <= conf + 1e-9


# --- Invariant 3: safety claim on model_prior always escalates (danger) ----------

@pytest.mark.parametrize("conf", [0.0, 0.4, 0.7, 0.99, 1.0])
def test_safety_on_model_prior_always_escalates(conf):
    displayed = cap_confidence(conf, "model_prior")
    esc = escalation(safety_critical=True, grounded_tier="model_prior",
                     displayed_confidence=displayed)
    assert esc is not None
    assert esc["reason"] == "unverified_safety_claim"
    assert esc["severity"] == "danger"


# --- Invariant 4: individual-scope claims are capped harder ----------------------

@pytest.mark.parametrize("tier", ["systematic_review", "rct", "guideline"])
def test_individual_scope_extra_cap(tier):
    # population scope can exceed the individual ceiling for strong tiers...
    assert cap_confidence(1.0, tier, "population") > INDIVIDUAL_SCOPE_CEILING
    # ...but individual scope never does.
    assert cap_confidence(1.0, tier, "individual") <= INDIVIDUAL_SCOPE_CEILING + 1e-9


# --- Invariant 5: lowering the tier can only keep/raise escalation severity ------

def _severity_rank(esc):
    if esc is None:
        return 0
    return {"warning": 1, "danger": 2}[esc["severity"]]

def test_escalation_monotonic_as_evidence_weakens():
    # Walk strongest -> weakest. A non-safety, high-confidence verdict should only
    # ever get MORE concerning as evidence weakens, never less.
    conf = 0.95
    prev = -1
    for tier in TIER_ORDER:
        displayed = cap_confidence(conf, tier)
        esc = escalation(safety_critical=False, grounded_tier=tier,
                         displayed_confidence=displayed)
        rank = _severity_rank(esc)
        assert rank >= prev, f"escalation got LESS severe at {tier}"
        prev = rank


# --- Known reference values (lock the numbers in the demo) -----------------------

def test_known_values():
    # warfarin drug-interaction safety, ungrounded -> capped at the prior floor
    assert cap_confidence(0.88, "model_prior") == 0.40
    # dosing accuracy grounded to a guideline -> capped at 0.80
    assert cap_confidence(0.90, "guideline") == 0.80
    # grounding the same verdict to an RCT unlocks the model's real confidence
    assert cap_confidence(0.88, "rct") == 0.88


# --- The end-to-end "aha" the demo is built around -------------------------------

def test_grounding_a_safety_claim_clears_escalation():
    ungrounded = evaluate(0.88, "model_prior", safety_critical=True)
    assert ungrounded.trust_band == "escalated"
    assert ungrounded.displayed_confidence == 0.40

    grounded = evaluate(0.88, "rct", safety_critical=True)
    assert grounded.trust_band == "trustworthy"
    assert grounded.displayed_confidence == 0.88


def test_low_confidence_threshold_boundary():
    # exactly at threshold is NOT escalated; just below IS.
    assert escalation(False, "expert", LOW_CONFIDENCE_ESCALATION) is None
    assert escalation(False, "expert", LOW_CONFIDENCE_ESCALATION - 0.01) is not None
