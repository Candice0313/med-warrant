import { useEffect, useState } from "react";
import { api } from "../api";
import { EvidenceSnippets } from "./EvidenceSnippets";
import type { Verdict } from "../types";

interface Props {
  onCountChange: (n: number) => void;
}

function toLabel(id: string): string {
  return id
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function ReviewQueue({ onCountChange }: Props) {
  const [verdicts, setVerdicts] = useState<Verdict[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [overrideOpen, setOverrideOpen] = useState<Record<string, boolean>>({});
  const [overrideNotes, setOverrideNotes] = useState<Record<string, string>>({});
  const [actionErrors, setActionErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    api
      .getQueue()
      .then((q) => {
        setVerdicts(q);
        onCountChange(q.length);
      })
      .catch((e: Error) => setFetchError(e.message))
      .finally(() => setLoading(false));
  }, [onCountChange]);

  function removeVerdict(verdict_id: string) {
    setVerdicts((prev) => {
      const next = prev.filter((v) => v.verdict_id !== verdict_id);
      onCountChange(next.length);
      return next;
    });
  }

  function setActionError(verdict_id: string, msg: string) {
    setActionErrors((prev) => ({ ...prev, [verdict_id]: msg }));
  }

  async function handleApprove(verdict_id: string) {
    try {
      await api.review({ verdict_id, decision: "approve", note: "" });
      removeVerdict(verdict_id);
    } catch (e) {
      setActionError(verdict_id, (e as Error).message);
    }
  }

  async function handleOverride(verdict_id: string) {
    const note = overrideNotes[verdict_id]?.trim();
    if (!note) return;
    try {
      await api.review({ verdict_id, decision: "override", note });
      removeVerdict(verdict_id);
    } catch (e) {
      setActionError(verdict_id, (e as Error).message);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto w-full">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-40 rounded-xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="p-6 max-w-3xl mx-auto w-full">
        <p className="text-xs text-red-600 bg-red-50 rounded px-4 py-3">{fetchError}</p>
      </div>
    );
  }

  if (verdicts.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        All caught up. No escalated verdicts awaiting review.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-6 max-w-3xl mx-auto w-full">
      <h2 className="text-sm font-semibold text-gray-700">
        {verdicts.length} verdict{verdicts.length !== 1 ? "s" : ""} awaiting review
      </h2>

      {verdicts.map((v) => (
        <div
          key={v.verdict_id}
          className={[
          "rounded-xl border-2 bg-white overflow-hidden",
          v.escalation?.severity === "danger" ? "border-red-400" : "border-amber-300",
        ].join(" ")}
        >
          {/* card header */}
          <div className={[
            "px-4 pt-3 pb-2",
            v.escalation?.severity === "danger" ? "bg-red-50" : "bg-amber-50",
          ].join(" ")}>
            <div className="flex items-start justify-between gap-2 flex-wrap">
              <div>
                <span className="text-[10px] font-mono text-gray-400">{v.case_id}</span>
                <h3 className="text-sm font-semibold text-gray-900">{toLabel(v.dimension)}</h3>
              </div>
              <div className="flex gap-1.5 items-center flex-wrap">
                {v.safety_critical && (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-600 text-white">
                    SAFETY
                  </span>
                )}
                {v.escalation && (
                  <span className={[
                    "text-[10px] font-bold px-1.5 py-0.5 rounded",
                    v.escalation.severity === "danger"
                      ? "bg-red-600 text-white"
                      : "bg-amber-500 text-white",
                  ].join(" ")}>
                    {v.escalation.reason === "unverified_safety_claim"
                      ? "UNVERIFIED SAFETY"
                      : "LOW CONFIDENCE"}
                  </span>
                )}
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 font-mono">
                  {Math.round(v.displayed_confidence * 100)}% capped
                </span>
              </div>
            </div>
          </div>

          {/* model reasoning */}
          <div className="px-4 py-3 border-b border-gray-100">
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Model reasoning
            </p>
            <p className="text-xs text-gray-700 leading-relaxed">{v.model_reasoning}</p>
          </div>

          {/* evidence snippets */}
          <EvidenceSnippets grounding={v.grounding} />

          {/* action error */}
          {actionErrors[v.verdict_id] && (
            <div className="px-4 pb-2">
              <p className="text-xs text-red-600 bg-red-50 rounded px-3 py-2">
                {actionErrors[v.verdict_id]}
              </p>
            </div>
          )}

          {/* actions */}
          <div className="px-4 pb-4 flex items-start gap-2 flex-wrap">
            <button
              onClick={() => handleApprove(v.verdict_id)}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
            >
              Approve
            </button>

            {!overrideOpen[v.verdict_id] ? (
              <button
                onClick={() =>
                  setOverrideOpen((prev) => ({ ...prev, [v.verdict_id]: true }))
                }
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-100 text-amber-800 hover:bg-amber-200 transition-colors"
              >
                Override…
              </button>
            ) : (
              <div className="flex flex-col gap-2 flex-1 min-w-[200px]">
                <textarea
                  value={overrideNotes[v.verdict_id] ?? ""}
                  onChange={(e) =>
                    setOverrideNotes((prev) => ({ ...prev, [v.verdict_id]: e.target.value }))
                  }
                  placeholder="Reason for override…"
                  className="text-xs border border-amber-300 rounded-lg px-3 py-2 resize-none h-16 focus:outline-none focus:ring-1 focus:ring-amber-400 w-full"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleOverride(v.verdict_id)}
                    disabled={!overrideNotes[v.verdict_id]?.trim()}
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    Confirm override
                  </button>
                  <button
                    onClick={() =>
                      setOverrideOpen((prev) => ({ ...prev, [v.verdict_id]: false }))
                    }
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
