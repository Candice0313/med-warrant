import { ComplexityTags } from "./ComplexityTags";
import type { CaseSummary } from "../types";

interface Props {
  cases: CaseSummary[];
  selectedId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
}

export function CaseList({ cases, selectedId, loading, onSelect }: Props) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2 p-3">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-16 rounded-lg bg-gray-100 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <nav className="flex flex-col gap-1 p-3">
      {cases.map((c) => {
        const selected = c.id === selectedId;
        return (
          <button
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={[
              "text-left rounded-lg px-3 py-2.5 transition-colors",
              "border",
              selected
                ? "border-blue-400 bg-blue-50"
                : "border-transparent hover:bg-gray-50",
            ].join(" ")}
          >
            <p
              className={[
                "text-xs leading-snug line-clamp-2",
                selected ? "text-blue-900 font-medium" : "text-gray-700",
              ].join(" ")}
            >
              {c.patient_question}
            </p>
            <ComplexityTags complexity={c.complexity} />
          </button>
        );
      })}
    </nav>
  );
}
