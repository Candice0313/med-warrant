"""models.py — Pydantic / SQLModel schemas shared across the backend."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# --- Evidence ----------------------------------------------------------------

class EvidenceSource(BaseModel):
    source_id: str
    title: str
    tier: str
    text: str
    url: str
    topics: list[str]


# --- Case --------------------------------------------------------------------

class Dimension(BaseModel):
    id: str
    label: str
    safety_critical: bool
    claim_scope: str
    topics: list[str] = []


class Case(BaseModel):
    id: str
    patient_question: str
    candidate_answer: str
    complexity: dict[str, str]
    dimensions: list[Dimension]


class CaseSummary(BaseModel):
    id: str
    patient_question: str
    complexity: dict[str, str]


# --- Verdict -----------------------------------------------------------------

class GroundingSnippet(BaseModel):
    source_id: str
    tier: str
    snippet: str
    score: float


class EscalationFlag(BaseModel):
    flag: bool
    reason: str
    severity: str


class Verdict(BaseModel):
    verdict_id: str
    case_id: str
    dimension: str
    safety_critical: bool
    claim_scope: str
    model_confidence: float
    model_reasoning: str
    grounded_tier: str
    grounding: list[GroundingSnippet]
    displayed_confidence: float
    escalation: Optional[EscalationFlag]
    human_review: Optional[dict] = None


# --- Summary (never an average — counts only) --------------------------------

class Summary(BaseModel):
    trustworthy: int
    caution: int
    escalated: int
    mixed_average_suppressed: int


class JudgeResponse(BaseModel):
    verdicts: list[Verdict]
    summary: Summary


# --- Human review ------------------------------------------------------------

class ReviewRequest(BaseModel):
    verdict_id: str
    decision: str  # "approve" | "override"
    note: str = ""
