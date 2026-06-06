import { useState } from "react";
import { TIER_META } from "../constants";
import type { GroundingSnippet } from "../types";

interface Props {
  grounding: GroundingSnippet[];
}

export function EvidenceSnippets({ grounding }: Props) {
  const [activeIdx, setActiveIdx] = useState<number | null>(null);

  if (grounding.length === 0) return null;

  function toggle(i: number) {
    setActiveIdx((prev) => (prev === i ? null : i));
  }

  const active = activeIdx !== null ? grounding[activeIdx] : null;

  return (
    <div className="px-3 pb-2.5 flex flex-col gap-1.5">
      {/* chip row */}
      <div className="flex flex-wrap gap-1.5">
        {grounding.map((g, i) => (
          <button
            key={g.source_id}
            onClick={() => toggle(i)}
            className={[
              "text-[10px] font-medium px-2 py-0.5 rounded-full border transition-colors",
              activeIdx === i
                ? "bg-blue-600 border-blue-600 text-white"
                : "bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100",
            ].join(" ")}
          >
            {g.source_id} · {g.score}
          </button>
        ))}
      </div>

      {/* inline expansion */}
      {active && (
        <div className="rounded-lg border border-blue-100 bg-blue-50/40 p-3 flex flex-col gap-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[10px] text-gray-600">{active.source_id}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
              {TIER_META[active.tier]?.code ?? active.tier}: {TIER_META[active.tier]?.label ?? active.tier}
            </span>
          </div>
          <p className="text-xs text-gray-600 leading-relaxed italic">
            "{active.snippet}"
          </p>
          <a
            href={active.source_id.startsWith("http") ? active.source_id : "#"}
            target="_blank"
            rel="noreferrer"
            className="text-[10px] text-gray-400 hover:text-blue-500 transition-colors truncate"
          >
            source: {active.source_id}
          </a>
        </div>
      )}
    </div>
  );
}
