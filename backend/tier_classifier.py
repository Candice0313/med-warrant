"""tier_classifier.py — pick the strongest evidence tier from retrieved sources.

Rule-based for Phase 1: take the top-scored source's tier; fall back to model_prior.
Relevance gating: sources below MIN_RELEVANCE_SCORE are downgraded to avoid
"high-tier but low-relevance" evidence inflating confidence incorrectly.
"""

from __future__ import annotations

from .capping import EVIDENCE_CEILINGS
from .evidence_store import RetrievedSource
from .models import GroundingSnippet

_TIER_STRENGTH = {t: c for t, c in EVIDENCE_CEILINGS.items()}

# Minimum topic overlap score required for a source to be trusted at its full tier.
# Below this threshold, the tier is downgraded one level. This prevents a single
# low-relevance T1 from inflating the ceiling to 95% when it shouldn't.
MIN_RELEVANCE_SCORE = 2

# Tier downgrade map: if a source doesn't meet MIN_RELEVANCE_SCORE, drop it one level.
_DOWNGRADE_MAP = {
    "systematic_review": "rct",
    "rct": "guideline",
    "guideline": "cohort",
    "cohort": "expert",
    "expert": "model_prior",
    "model_prior": "model_prior",  # Can't go lower
}


def classify(retrieved: list[RetrievedSource]) -> tuple[str, list[GroundingSnippet]]:
    """Return (grounded_tier, grounding_snippets).

    The grounded_tier is the strongest tier among the retrieved sources, subject to
    relevance gating: if the best source scores below MIN_RELEVANCE_SCORE, its tier
    is downgraded to prevent spurious confidence inflation from irrelevant high-tier sources.

    If nothing was retrieved, return ("model_prior", []).
    """
    if not retrieved:
        return "model_prior", []

    best = max(retrieved, key=lambda r: (_TIER_STRENGTH.get(r.source.tier, 0), r.score))

    # Relevance gating: if the best source is not sufficiently relevant, downgrade it.
    final_tier = best.source.tier
    if best.score < MIN_RELEVANCE_SCORE:
        final_tier = _DOWNGRADE_MAP.get(best.source.tier, "model_prior")

    snippets = [
        GroundingSnippet(
            source_id=r.source.source_id,
            tier=r.source.tier,
            snippet=r.source.text[:300],
            score=r.score,
        )
        for r in retrieved
    ]
    return final_tier, snippets
