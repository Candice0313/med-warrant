// Must match backend/capping.py — EVIDENCE_CEILINGS and EVIDENCE_META
export const EVIDENCE_CEILINGS: Record<string, number> = {
  systematic_review: 0.95,
  rct: 0.90,
  guideline: 0.80,
  cohort: 0.75,
  expert: 0.60,
  model_prior: 0.40,
};

export const TIER_META: Record<string, { label: string; code: string }> = {
  systematic_review: { label: "Systematic review / meta-analysis", code: "T1" },
  rct:               { label: "Randomized controlled trial",        code: "T2" },
  guideline:         { label: "Clinical guideline / consensus",     code: "T4" },
  cohort:            { label: "Cohort / observational study",       code: "T3" },
  expert:            { label: "Expert opinion / case report",       code: "T5" },
  model_prior:       { label: "Model prior (ungrounded)",           code: "T6" },
};

export const LOW_CONFIDENCE_THRESHOLD = 0.50;
export const TRUSTWORTHY_THRESHOLD = 0.75;

// Tiers ordered strongest → weakest by ceiling — used by TierSelector dropdown.
export const TIER_ORDER: string[] = [
  "systematic_review",
  "rct",
  "guideline",
  "cohort",
  "expert",
  "model_prior",
];

// ── Pure capping helpers (mirrors backend/capping.py exactly) ────────────────

export function capConfidence(
  modelConf: number,
  tier: string,
  claimScope: string,
): number {
  const ceiling = EVIDENCE_CEILINGS[tier] ?? 0.40;
  let capped = Math.min(modelConf, ceiling);
  if (claimScope === "individual") capped = Math.min(capped, 0.60);
  return Math.round(capped * 100) / 100;
}

export function computeEscalation(
  safetyCritical: boolean,
  tier: string,
  displayed: number,
): { flag: boolean; reason: string; severity: string } | null {
  if (safetyCritical && tier === "model_prior")
    return { flag: true, reason: "unverified_safety_claim", severity: "danger" };
  if (displayed < LOW_CONFIDENCE_THRESHOLD)
    return { flag: true, reason: "low_confidence", severity: "warning" };
  return null;
}
