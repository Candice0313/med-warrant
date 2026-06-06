"""capping.py — the thesis, in code.

PURE module: no I/O, no network, no LLM calls. Everything here is a deterministic
function of its inputs so it can be exhaustively unit-tested. This is the part of the
system that must never be compromised for convenience.

Two rules:
  1. A verdict's displayed confidence is the model's confidence clamped DOWN by the
     strength of evidence it grounded to. Evidence raises a ceiling; it never inflates.
  2. Safety claims that rest only on the model's own prior are "unverified" and escalate,
     no matter how confident the model sounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from escalation import LOW_CONFIDENCE_ESCALATION, escalation  # re-export for callers

__all__ = [
    "EVIDENCE_CEILINGS",
    "EVIDENCE_META",
    "TIER_ORDER",
    "INDIVIDUAL_SCOPE_CEILING",
    "LOW_CONFIDENCE_ESCALATION",
    "cap_confidence",
    "escalation",
    "CappedVerdict",
    "evaluate",
]

# --- Evidence ladder -------------------------------------------------------------

EVIDENCE_CEILINGS: dict[str, float] = {
    "systematic_review": 0.95,
    "rct": 0.90,
    "guideline": 0.80,
    "cohort": 0.75,
    "expert": 0.60,
    "model_prior": 0.40,
}

EVIDENCE_META: dict[str, dict[str, str]] = {
    "systematic_review": {"label": "Systematic review / meta-analysis", "code": "T1"},
    "rct":               {"label": "Randomized controlled trial",        "code": "T2"},
    "guideline":         {"label": "Clinical guideline / consensus",     "code": "T4"},
    "cohort":            {"label": "Cohort / observational study",       "code": "T3"},
    "expert":            {"label": "Expert opinion / case report",       "code": "T5"},
    "model_prior":       {"label": "Model prior (ungrounded)",           "code": "T6"},
}

# Ordered strongest → weakest by ceiling; useful for UIs and monotonicity tests.
TIER_ORDER: list[str] = sorted(
    EVIDENCE_CEILINGS, key=lambda t: EVIDENCE_CEILINGS[t], reverse=True
)

# EBM tiers grade POPULATION-level evidence. A claim about applying something to THIS
# specific patient is not gradeable the same way, so it is never "highly certain".
INDIVIDUAL_SCOPE_CEILING: float = 0.60


# --- Core logic ------------------------------------------------------------------

def cap_confidence(
    model_confidence: float,
    grounded_tier: str,
    claim_scope: str = "population",
) -> float:
    """Clamp the model's self-reported confidence down to what the evidence supports.

    Result can never exceed the grounded tier's ceiling, can never exceed the model's
    own confidence, and (for individual-application claims) can never exceed the
    individual-scope ceiling. Evidence only ever lowers the number.
    """
    if grounded_tier not in EVIDENCE_CEILINGS:
        raise ValueError(f"unknown evidence tier: {grounded_tier!r}")
    if not 0.0 <= model_confidence <= 1.0:
        raise ValueError(f"model_confidence out of range: {model_confidence!r}")

    capped = min(model_confidence, EVIDENCE_CEILINGS[grounded_tier])
    if claim_scope == "individual":
        capped = min(capped, INDIVIDUAL_SCOPE_CEILING)
    return round(capped, 2)


@dataclass
class CappedVerdict:
    """Result of applying the thesis to a single dimension's judgment."""

    model_confidence: float
    grounded_tier: str
    claim_scope: str
    safety_critical: bool
    displayed_confidence: float
    ceiling: float
    escalation: Optional[dict]

    @property
    def trust_band(self) -> str:
        if self.escalation:
            return "escalated"
        if self.displayed_confidence >= 0.75:
            return "trustworthy"
        return "caution"


def evaluate(
    model_confidence: float,
    grounded_tier: str,
    safety_critical: bool = False,
    claim_scope: str = "population",
) -> CappedVerdict:
    """Convenience wrapper: cap + escalate in one call."""
    displayed = cap_confidence(model_confidence, grounded_tier, claim_scope)
    return CappedVerdict(
        model_confidence=round(model_confidence, 2),
        grounded_tier=grounded_tier,
        claim_scope=claim_scope,
        safety_critical=safety_critical,
        displayed_confidence=displayed,
        ceiling=EVIDENCE_CEILINGS[grounded_tier],
        escalation=escalation(safety_critical, grounded_tier, displayed),
    )
