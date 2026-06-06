"""escalation.py — rules for routing verdicts to human review.

PURE module: no I/O, no LLM calls. Depends only on capping constants.
"""

from __future__ import annotations

from typing import Optional

LOW_CONFIDENCE_ESCALATION: float = 0.50


def escalation(
    safety_critical: bool,
    grounded_tier: str,
    displayed_confidence: float,
) -> Optional[dict]:
    """Decide whether a verdict must go to a human, and why.

    Returns None if no escalation is needed, else a dict with reason + severity.
    Severity ordering for callers: danger > warning > None.
    """
    if safety_critical and grounded_tier == "model_prior":
        return {"flag": True, "reason": "unverified_safety_claim", "severity": "danger"}
    if displayed_confidence < LOW_CONFIDENCE_ESCALATION:
        return {"flag": True, "reason": "low_confidence", "severity": "warning"}
    return None
