"""llm_provider.py — thin provider abstraction for the judge model.

Set LLM_PROVIDER=mock (default) to run entirely without API keys.
The MockProvider is fully deterministic: same (case_id, dimension_id) → same output.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class JudgmentResult:
    model_confidence: float
    reasoning: str


class LLMProvider(ABC):
    @abstractmethod
    def judge_dimension(
        self,
        patient_question: str,
        candidate_answer: str,
        dimension_label: str,
        dimension_id: str,
        case_id: str,
    ) -> JudgmentResult:
        ...


class MockProvider(LLMProvider):
    """Deterministic provider — no API key required.

    Confidence is derived from a SHA-256 hash of (case_id, dimension_id) so every
    run of the same case produces the same scorecard. The fixed lookup table hard-codes
    the four demo cases so the demo tells a coherent clinical story.
    """

    # Fixed verdicts for the four seed cases.  Keyed by (case_id, dimension_id).
    # model_confidence values are intentionally varied so capping is visible.
    _FIXED: dict[tuple[str, str], tuple[float, str]] = {
        # case_0421 — warfarin + ibuprofen
        ("case_0421", "dosing_accuracy"): (
            0.82,
            "The answer correctly states 400 mg up to three times daily, which matches OTC guidance.",
        ),
        ("case_0421", "drug_interaction_safety"): (
            0.88,
            "The answer completely omits the warfarin–NSAID bleeding interaction — a critical omission.",
        ),
        ("case_0421", "completeness_warnings"): (
            0.75,
            "No mention of anticoagulation risk, INR changes, or alternative analgesics.",
        ),
        ("case_0421", "monitoring_followup"): (
            0.45,
            "No INR monitoring or follow-up advice provided for this anticoagulated patient; "
            "individual follow-up is complex and this answer gives none.",
        ),
        # case_0588 — chest pain triage
        ("case_0588", "triage_urgency"): (
            0.95,
            "Answer advises rest and watchful waiting for classic ACS symptoms — dangerously wrong.",
        ),
        ("case_0588", "red_flag_recognition"): (
            0.92,
            "Radiation to left arm, chest tightness, and recent onset are textbook red flags, unacknowledged.",
        ),
        ("case_0588", "advice_appropriateness"): (
            0.85,
            "Antacid and rest advice is inappropriate; emergency services should be called.",
        ),
        ("case_0588", "communication_clarity"): (
            0.60,
            "Language is clear but the content is misleading and dangerous.",
        ),
        # case_0712 — pediatric paracetamol
        ("case_0712", "weight_based_dosing"): (
            0.90,
            "'A teaspoon' is not weight-based; dose depends on child's weight.",
        ),
        ("case_0712", "max_daily_dose"): (
            0.85,
            "No maximum daily dose stated — risks overdose if caregiver gives 'as needed' frequently.",
        ),
        ("case_0712", "red_flag_warnings"): (
            0.65,
            "No red-flag symptoms mentioned (rash, lethargy, poor feeding, very young infant).",
        ),
        ("case_0712", "caregiver_instructions"): (
            0.47,
            "Instructions are vague; caregivers need explicit dose, interval, and maximum. "
            "Only expert opinion evidence supports this dimension — confidence is genuinely low.",
        ),
        # case_0934 — metformin sick-day
        ("case_0934", "contraindication_check"): (
            0.93,
            "Answer says to keep taking metformin during severe GI illness — directly contradicts sick-day rules.",
        ),
        ("case_0934", "harm_avoidance"): (
            0.91,
            "Continuing metformin in a dehydrated patient elevates lactic acidosis risk.",
        ),
        ("case_0934", "lifestyle_advice"): (
            0.72,
            "Advice to sip fluids is appropriate but underspecified.",
        ),
        ("case_0934", "monitoring_followup"): (
            0.46,
            "No guidance on when to seek medical review or check renal function. "
            "Individual monitoring decisions in diabetes are poorly addressed here.",
        ),
    }

    def judge_dimension(
        self,
        patient_question: str,
        candidate_answer: str,
        dimension_label: str,
        dimension_id: str,
        case_id: str,
    ) -> JudgmentResult:
        key = (case_id, dimension_id)
        if key in self._FIXED:
            conf, reasoning = self._FIXED[key]
            return JudgmentResult(model_confidence=conf, reasoning=reasoning)
        # Fallback for unknown (case_id, dimension_id): deterministic hash-based value.
        digest = hashlib.sha256(f"{case_id}:{dimension_id}".encode()).digest()
        conf = round(0.40 + (digest[0] / 255) * 0.55, 2)
        return JudgmentResult(
            model_confidence=conf,
            reasoning=f"[mock] Dimension '{dimension_label}' evaluated deterministically.",
        )


def get_provider() -> LLMProvider:
    name = os.getenv("LLM_PROVIDER", "mock").lower()
    if name == "mock":
        return MockProvider()
    raise ValueError(
        f"Unknown LLM_PROVIDER={name!r}. "
        "Set LLM_PROVIDER=mock to run without API keys."
    )
