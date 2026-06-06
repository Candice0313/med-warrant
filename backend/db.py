"""db.py — SQLite persistence via a plain JSON file store for Phase 1.

Swappable for SQLModel + SQLAlchemy in a later phase without touching grader.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import Verdict, ReviewRequest

_DB_PATH = Path(__file__).parent.parent / "data" / "verdicts.json"


def _load() -> dict[str, dict]:
    if not _DB_PATH.exists():
        return {}
    return json.loads(_DB_PATH.read_text())


def _save(store: dict[str, dict]) -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DB_PATH.write_text(json.dumps(store, indent=2))


def upsert_verdict(verdict: Verdict) -> None:
    store = _load()
    store[verdict.verdict_id] = verdict.model_dump()
    _save(store)


def get_verdict(verdict_id: str) -> Optional[Verdict]:
    store = _load()
    raw = store.get(verdict_id)
    return Verdict(**raw) if raw else None


def list_verdicts() -> list[Verdict]:
    return [Verdict(**v) for v in _load().values()]


def escalation_queue() -> list[Verdict]:
    return [v for v in list_verdicts() if v.escalation and not v.human_review]


def apply_review(req: ReviewRequest) -> Optional[Verdict]:
    store = _load()
    raw = store.get(req.verdict_id)
    if not raw:
        return None
    raw["human_review"] = {"decision": req.decision, "note": req.note}
    store[req.verdict_id] = raw
    _save(store)
    return Verdict(**raw)
