import { useEffect, useRef, useState } from "react";
import { DimensionRow } from "./DimensionRow";
import { ProfileRadar } from "./ProfileRadar";
import type { Case, JudgeResponse, Verdict } from "../types";

interface Props {
  selectedCase: Case | null;
  judgeResponse: JudgeResponse | null;
  loading: boolean;
  error: string | null;
  onEvaluate: () => void;
}

function trustBand(v: Verdict): "escalated" | "caution" | "trustworthy" {
  if (v.escalation) return "escalated";
  if (v.displayed_confidence >= 0.75) return "trustworthy";
  return "caution";
}

const BAND_ORDER = { escalated: 0, caution: 1, trustworthy: 2 } as const;

export function ScoreCard({
  selectedCase,
  judgeResponse,
  loading,
  error,
  onEvaluate,
}: Props) {
  const [answerExpanded, setAnswerExpanded] = useState(false);
  const [answerOverflows, setAnswerOverflows] = useState(false);
  const answerRef = useRef<HTMLParagraphElement>(null);
  const [exploreMode, setExploreMode] = useState(false);
  const [exploreTiers, setExploreTiers] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<"scorecard" | "profile">("scorecard");

  // Reset expansion and re-measure overflow whenever the case changes.
  useEffect(() => {
    setAnswerExpanded(false);
    setAnswerOverflows(false);
    // Measure after the DOM has updated with the new answer text.
    const frame = requestAnimationFrame(() => {
      const el = answerRef.current;
      if (el) setAnswerOverflows(el.scrollHeight > el.clientHeight + 1);
    });
    return () => cancelAnimationFrame(frame);
  }, [selectedCase?.id]);

  useEffect(() => {
    setExploreMode(false);
    setExploreTiers({});
    setActiveTab("scorecard");
  }, [selectedCase?.id]);

  function toggleExploreMode() {
    setExploreMode((prev) => {
      if (prev) setExploreTiers({});
      return !prev;
    });
  }

  function handleTierChange(verdict_id: string, tier: string | null) {
    setExploreTiers((prev) => {
      const next = { ...prev };
      if (tier === null) delete next[verdict_id];
      else next[verdict_id] = tier;
      return next;
    });
  }

  if (!selectedCase) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Select a case from the sidebar to evaluate it.
      </div>
    );
  }

  const answer = selectedCase.candidate_answer;

  // Join verdicts with dimension metadata, sorted by trust band
  const rows =
    judgeResponse?.verdicts
      .map((v) => ({
        verdict: v,
        dimension: selectedCase.dimensions.find((d) => d.id === v.dimension)!,
      }))
      .filter((r) => r.dimension)
      .sort((a, b) => BAND_ORDER[trustBand(a.verdict)] - BAND_ORDER[trustBand(b.verdict)]) ?? [];

  const { summary } = judgeResponse ?? {};

  return (
    <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto w-full">
      {/* ── context card: question + candidate answer ── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4 flex flex-col gap-3">

        {/* patient question */}
        <p className="text-xs text-gray-400 italic border-l-2 border-gray-200 pl-3 leading-relaxed">
          "{selectedCase.patient_question}"
        </p>

        {/* candidate answer */}
        <div className="border-t border-gray-100 pt-3">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
            AI Candidate Answer
          </p>
          <div className="pl-3">
            <p
              ref={answerRef}
              className={[
                "text-sm text-gray-700 leading-relaxed whitespace-pre-wrap",
                !answerExpanded ? "line-clamp-4" : "",
              ].join(" ")}
            >
              {answer}
            </p>
            {answerOverflows && (
              <button
                onClick={() => setAnswerExpanded((e) => !e)}
                className="mt-1 text-xs text-blue-500 hover:text-blue-700 transition-colors"
              >
                {answerExpanded ? "Collapse ↑" : "Show full answer ↓"}
              </button>
            )}
          </div>
        </div>

        {/* divider before evaluation controls */}
        <div className="border-t border-gray-100 pt-1">
          {/* summary pill strip */}
          {summary ? (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-green-100 text-green-800">
                {summary.trustworthy} trustworthy
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                {summary.caution} caution
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-red-100 text-red-800">
                {summary.escalated} escalated
              </span>
              <span className="ml-auto text-[11px] text-gray-300 line-through">
                avg {summary.mixed_average_suppressed}%
              </span>
            </div>
          ) : (
            !loading && (
              <p className="text-xs text-gray-400">
                {selectedCase.dimensions.length} dimensions. Click Evaluate to run the judge.
              </p>
            )
          )}

          {loading && (
            <div className="flex gap-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-7 w-24 rounded-full bg-gray-100 animate-pulse" />
              ))}
            </div>
          )}

        {judgeResponse && (
          <div className="flex gap-0 border-b border-gray-100 mt-3 mb-1">
            <button
              onClick={() => setActiveTab("scorecard")}
              className={[
                "text-xs font-semibold px-3 py-1.5 border-b-2 transition-colors",
                activeTab === "scorecard"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-400 hover:text-gray-600",
              ].join(" ")}
            >
              Scorecard
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className={[
                "text-xs font-semibold px-3 py-1.5 border-b-2 transition-colors",
                activeTab === "profile"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-400 hover:text-gray-600",
              ].join(" ")}
            >
              Profile
            </button>
          </div>
        )}

        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <button
            onClick={onEvaluate}
            disabled={loading}
            className={[
              "text-xs font-semibold px-4 py-1.5 rounded-lg transition-colors",
              loading
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700",
            ].join(" ")}
          >
            {loading ? "Evaluating…" : "Evaluate"}
          </button>
          {judgeResponse && (
            <button
              onClick={toggleExploreMode}
              className={[
                "text-xs font-semibold px-3 py-1.5 rounded-full border transition-colors",
                exploreMode
                  ? "bg-indigo-600 border-indigo-600 text-white"
                  : "bg-white border-gray-300 text-gray-500 hover:border-indigo-300 hover:text-indigo-500",
              ].join(" ")}
            >
              {exploreMode ? "Explore ON" : "Explore"}
            </button>
          )}
        </div>

          {error && (
            <p className="mt-2 text-xs text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}
        </div>
      </div>

      {/* ── dimension rows (loading skeletons) ── */}
      {activeTab === "scorecard" && loading && rows.length === 0 && (
        <div className="flex flex-col gap-3">
          {selectedCase.dimensions.map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {/* ── dimension rows (results) ── */}
      {activeTab === "scorecard" && rows.length > 0 && (
        <div className="flex flex-col gap-3">
          {rows.map(({ verdict, dimension }) => (
            <DimensionRow
              key={verdict.verdict_id}
              verdict={verdict}
              dimension={dimension}
              exploreMode={exploreMode}
              exploreTier={exploreTiers[verdict.verdict_id] ?? null}
              onTierChange={(tier) => handleTierChange(verdict.verdict_id, tier)}
            />
          ))}
        </div>
      )}

      {/* ── profile radar ── */}
      {activeTab === "profile" && judgeResponse && (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4">
          <ProfileRadar
            verdicts={judgeResponse.verdicts}
            dimensions={selectedCase.dimensions}
          />
        </div>
      )}
    </div>
  );
}
