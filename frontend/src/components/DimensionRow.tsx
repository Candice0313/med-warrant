import { EVIDENCE_CEILINGS, TIER_META, capConfidence, computeEscalation } from "../constants";
import { EvidenceSnippets } from "./EvidenceSnippets";
import { TierSelector } from "./TierSelector";
import type { Dimension, Verdict } from "../types";

// ── colour helpers ──────────────────────────────────────────────────────────

type Band = "trustworthy" | "caution" | "escalated-danger" | "escalated-warning";

function band(
  escalation: { severity: string } | null,
  displayedConf: number,
): Band {
  if (escalation?.severity === "danger")  return "escalated-danger";
  if (escalation?.severity === "warning") return "escalated-warning";
  if (displayedConf >= 0.75)             return "trustworthy";
  return "caution";
}

const BORDER: Record<Band, string> = {
  trustworthy:         "border-green-300 bg-green-50",
  caution:             "border-amber-300 bg-amber-50",
  "escalated-danger":  "border-red-400 bg-red-50",
  "escalated-warning": "border-amber-400 bg-amber-50",
};

const BAR_HEX: Record<Band, string> = {
  trustworthy:         "#2f9e44",
  caution:             "#f08c00",
  "escalated-danger":  "#e03131",
  "escalated-warning": "#f08c00",
};

const PCT_CLASS: Record<Band, string> = {
  trustworthy:         "text-green-700",
  caution:             "text-amber-700",
  "escalated-danger":  "text-red-700",
  "escalated-warning": "text-amber-700",
};

// ── component ───────────────────────────────────────────────────────────────

interface Props {
  verdict: Verdict;
  dimension: Dimension;
  exploreMode?: boolean;
  exploreTier?: string | null;
  onTierChange?: (tier: string | null) => void;
}

export function DimensionRow({
  verdict,
  dimension,
  exploreMode,
  exploreTier,
  onTierChange,
}: Props) {
  // In explore mode, derive display values from the chosen tier.
  // When exploreMode is false (or exploreTier is null), use backend values unchanged.
  const displayedTier = (exploreMode && exploreTier) ? exploreTier : verdict.grounded_tier;
  const displayedCap  = exploreMode
    ? capConfidence(verdict.model_confidence, displayedTier, verdict.claim_scope)
    : verdict.displayed_confidence;
  const displayedEsc  = exploreMode
    ? computeEscalation(verdict.safety_critical, displayedTier, displayedCap)
    : verdict.escalation;

  const b = band(displayedEsc, displayedCap);
  const barColour = BAR_HEX[b];
  const ceiling = EVIDENCE_CEILINGS[displayedTier] ?? 0.4;
  const tierCode = TIER_META[displayedTier]?.code ?? "??";

  return (
    <div
      className={[
        "rounded-lg border-2 overflow-hidden",
        BORDER[b],
      ].join(" ")}
    >
      {/* ── top line ── */}
      <div className="flex items-center gap-2 px-3 pt-2.5 pb-1 flex-wrap">
        <span className="font-semibold text-sm text-gray-900 flex-1 min-w-0 truncate">
          {dimension.label}
        </span>

        {dimension.safety_critical && (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-600 text-white shrink-0">
            SAFETY
          </span>
        )}

        {displayedEsc && (
          <span
            className={[
              "text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0",
              displayedEsc.severity === "danger"
                ? "bg-red-600 text-white"
                : "bg-amber-500 text-white",
            ].join(" ")}
          >
            {displayedEsc.reason === "unverified_safety_claim"
              ? "UNVERIFIED SAFETY"
              : "LOW CONFIDENCE"}
          </span>
        )}

        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 shrink-0 font-mono">
          {tierCode}
        </span>

        <span className={`text-sm font-bold shrink-0 ${PCT_CLASS[b]}`}>
          {Math.round(displayedCap * 100)}%
        </span>
      </div>

      {/* ── explore tier selector (only in explore mode) ── */}
      {exploreMode && (
        <div className="px-3 pb-1">
          <TierSelector
            currentTier={displayedTier}
            originalTier={verdict.grounded_tier}
            onSelect={(t) => onTierChange?.(t)}
            onReset={() => onTierChange?.(null)}
          />
        </div>
      )}

      {/* ── dual confidence bar ── */}
      <div className="px-3 pb-2.5">
        <div
          className="relative h-2.5 rounded-full bg-gray-200"
          title={`Model: ${Math.round(verdict.model_confidence * 100)}%  Capped: ${Math.round(displayedCap * 100)}%  Ceiling: ${Math.round(ceiling * 100)}%`}
        >
          {/* faded: model confidence — always real, never changes in explore */}
          <div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{
              width: `${verdict.model_confidence * 100}%`,
              backgroundColor: barColour,
              opacity: 0.30,
            }}
          />
          {/* solid: capped/displayed confidence */}
          <div
            className="absolute inset-y-0 left-0 rounded-full"
            style={{
              width: `${displayedCap * 100}%`,
              backgroundColor: barColour,
            }}
          />
          {/* ceiling tick */}
          <div
            className="absolute top-[-3px] bottom-[-3px] w-[2px] bg-gray-500 rounded-full"
            style={{ left: `${ceiling * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-0.5 text-[9px] text-gray-400">
          <span>model {Math.round(verdict.model_confidence * 100)}%</span>
          <span>ceiling {Math.round(ceiling * 100)}%</span>
        </div>
      </div>

      <EvidenceSnippets grounding={verdict.grounding} />
    </div>
  );
}
