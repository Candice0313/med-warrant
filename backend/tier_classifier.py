"""tier_classifier.py — pick the strongest evidence tier from retrieved sources.

Rule-based for Phase 1: take the top-scored source's tier; fall back to model_prior.
"""

from __future__ import annotations

from capping import EVIDENCE_CEILINGS
from evidence_store import RetrievedSource
from models import GroundingSnippet

_TIER_STRENGTH = {t: c for t, c in EVIDENCE_CEILINGS.items()}


def classify(retrieved: list[RetrievedSource]) -> tuple[str, list[GroundingSnippet]]:
    """Return (grounded_tier, grounding_snippets).

    The grounded_tier is the strongest tier among the retrieved sources.
    If nothing was retrieved, return ("model_prior", []).
    """
    if not retrieved:
        return "model_prior", []

    best = max(retrieved, key=lambda r: (_TIER_STRENGTH.get(r.source.tier, 0), r.score))
    snippets = [
        GroundingSnippet(
            source_id=r.source.source_id,
            tier=r.source.tier,
            snippet=r.source.text[:300],
            score=r.score,
        )
        for r in retrieved
    ]
    return best.source.tier, snippets
