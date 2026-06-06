"""grader.py — per-dimension judge: LLM → retrieval → tier → capping → Verdict."""

from __future__ import annotations

from capping import cap_confidence
from escalation import escalation
from evidence_store import retrieve
from llm_provider import LLMProvider
from models import Case, Dimension, Verdict, EscalationFlag
from tier_classifier import classify


def grade_dimension(
    case: Case,
    dim: Dimension,
    provider: LLMProvider,
) -> Verdict:
    # 1. Ask the judge model for confidence + reasoning.
    result = provider.judge_dimension(
        patient_question=case.patient_question,
        candidate_answer=case.candidate_answer,
        dimension_label=dim.label,
        dimension_id=dim.id,
        case_id=case.id,
    )

    # 2. Retrieve relevant evidence.
    retrieved = retrieve(dim.topics)

    # 3. Pick the strongest tier.
    grounded_tier, snippets = classify(retrieved)

    # 4. Cap the confidence.
    displayed = cap_confidence(result.model_confidence, grounded_tier, dim.claim_scope)

    # 5. Decide escalation.
    esc_dict = escalation(dim.safety_critical, grounded_tier, displayed)
    esc_flag = EscalationFlag(**esc_dict) if esc_dict else None

    return Verdict(
        verdict_id=f"{case.id}:{dim.id}",
        case_id=case.id,
        dimension=dim.id,
        safety_critical=dim.safety_critical,
        claim_scope=dim.claim_scope,
        model_confidence=round(result.model_confidence, 2),
        model_reasoning=result.reasoning,
        grounded_tier=grounded_tier,
        grounding=snippets,
        displayed_confidence=displayed,
        escalation=esc_flag,
    )


def grade_case(case: Case, provider: LLMProvider) -> list[Verdict]:
    return [grade_dimension(case, dim, provider) for dim in case.dimensions]
