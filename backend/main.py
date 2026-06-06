"""main.py — FastAPI application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .grader import grade_case
from .llm_provider import get_provider
from .models import (
    Case,
    CaseSummary,
    EvidenceSource,
    JudgeResponse,
    ReviewRequest,
    Summary,
    Verdict,
)
from .evidence_store import all_sources

app = FastAPI(title="Medical LLM-as-Judge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_CASES_DIR = Path(__file__).parent.parent / "data" / "cases"


def _load_case(case_id: str) -> Case:
    p = _CASES_DIR / f"{case_id}.json"
    if not p.exists():
        raise HTTPException(404, f"case {case_id!r} not found")
    return Case(**json.loads(p.read_text()))


def _all_cases() -> list[Case]:
    return [Case(**json.loads(p.read_text())) for p in sorted(_CASES_DIR.glob("*.json"))]


def _build_summary(verdicts: list[Verdict]) -> Summary:
    trustworthy = caution = escalated = 0
    total_displayed = 0.0
    for v in verdicts:
        total_displayed += v.displayed_confidence
        if v.escalation:
            escalated += 1
        elif v.displayed_confidence >= 0.75:
            trustworthy += 1
        else:
            caution += 1
    # mixed_average_suppressed is included only so the UI can display it struck-through.
    # It is NEVER used in logic.
    avg_pct = round(total_displayed / len(verdicts) * 100) if verdicts else 0
    return Summary(
        trustworthy=trustworthy,
        caution=caution,
        escalated=escalated,
        mixed_average_suppressed=avg_pct,
    )


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases():
    return [
        CaseSummary(id=c.id, patient_question=c.patient_question, complexity=c.complexity)
        for c in _all_cases()
    ]


@app.get("/api/cases/{case_id}", response_model=Case)
def get_case(case_id: str):
    return _load_case(case_id)


@app.post("/api/judge", response_model=JudgeResponse)
def judge(body: dict):
    case_id: Optional[str] = body.get("case_id")
    if not case_id:
        raise HTTPException(400, "case_id required")
    case = _load_case(case_id)
    provider = get_provider()
    verdicts = grade_case(case, provider)
    for v in verdicts:
        db.upsert_verdict(v)
    return JudgeResponse(verdicts=verdicts, summary=_build_summary(verdicts))


@app.get("/api/evidence", response_model=list[EvidenceSource])
def search_evidence(q: str = ""):
    sources = all_sources()
    if q:
        q_lower = q.lower()
        sources = [s for s in sources if q_lower in s.title.lower() or any(q_lower in t for t in s.topics)]
    return sources


@app.get("/api/queue", response_model=list[Verdict])
def escalation_queue():
    return db.escalation_queue()


@app.post("/api/review", response_model=Verdict)
def review(req: ReviewRequest):
    updated = db.apply_review(req)
    if not updated:
        raise HTTPException(404, f"verdict {req.verdict_id!r} not found")
    return updated
