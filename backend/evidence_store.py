"""evidence_store.py — load evidence/*.json and retrieve by keyword match.

Retrieval is topic-keyword overlap (Phase 1). Embedding search is a stretch goal.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass

from models import EvidenceSource

_DATA_DIR = Path(__file__).parent.parent / "data" / "evidence"


@dataclass
class RetrievedSource:
    source: EvidenceSource
    score: float  # simple overlap count; 0 = no match


def _load_all() -> list[EvidenceSource]:
    sources = []
    for p in sorted(_DATA_DIR.glob("*.json")):
        raw = json.loads(p.read_text())
        sources.append(EvidenceSource(**raw))
    return sources


_SOURCES: list[EvidenceSource] = _load_all()


def all_sources() -> list[EvidenceSource]:
    return list(_SOURCES)


def retrieve(query_topics: list[str], top_k: int = 5) -> list[RetrievedSource]:
    """Return up to top_k sources ranked by topic-keyword overlap."""
    q_set = {t.lower() for t in query_topics}
    scored: list[RetrievedSource] = []
    for src in _SOURCES:
        overlap = len(q_set & {t.lower() for t in src.topics})
        scored.append(RetrievedSource(source=src, score=float(overlap)))
    scored.sort(key=lambda r: r.score, reverse=True)
    return [r for r in scored[:top_k] if r.score > 0]
