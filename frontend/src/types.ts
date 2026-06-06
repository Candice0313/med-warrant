// Mirror of backend Pydantic models — keep in sync with backend/models.py

export interface CaseSummary {
  id: string;
  patient_question: string;
  complexity: { reasoning: string; visual_dependency: string };
}

export interface Dimension {
  id: string;
  label: string;
  safety_critical: boolean;
  claim_scope: string;
  topics: string[];
}

export interface Case extends CaseSummary {
  candidate_answer: string;
  dimensions: Dimension[];
}

export interface GroundingSnippet {
  source_id: string;
  tier: string;
  snippet: string;
  score: number;
}

export interface EscalationFlag {
  flag: boolean;
  reason: string;           // "unverified_safety_claim" | "low_confidence"
  severity: string;         // "danger" | "warning"
}

export interface Verdict {
  verdict_id: string;
  case_id: string;
  dimension: string;        // dimension ID — join with Case.dimensions by id
  safety_critical: boolean;
  claim_scope: string;
  model_confidence: number;
  model_reasoning: string;
  grounded_tier: string;
  grounding: GroundingSnippet[];
  displayed_confidence: number;
  escalation: EscalationFlag | null;
  human_review: Record<string, string> | null;
}

export interface Summary {
  trustworthy: number;
  caution: number;
  escalated: number;
  mixed_average_suppressed: number;
}

export interface JudgeResponse {
  verdicts: Verdict[];
  summary: Summary;
}
