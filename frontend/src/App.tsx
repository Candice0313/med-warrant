import { useEffect, useState } from "react";
import { api } from "./api";
import { CaseList } from "./components/CaseList";
import { ReviewQueue } from "./components/ReviewQueue";
import { ScoreCard } from "./components/ScoreCard";
import type { Case, CaseSummary, JudgeResponse } from "./types";

export default function App() {
  // ── navigation ──────────────────────────────────────────────────────────
  const [view, setView] = useState<"cases" | "queue">("cases");
  const [queueCount, setQueueCount] = useState(0);

  // ── cases view state ────────────────────────────────────────────────────
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [casesLoading, setCasesLoading] = useState(true);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [caseLoading, setCaseLoading] = useState(false);

  const [judgeResponse, setJudgeResponse] = useState<JudgeResponse | null>(null);
  const [judgeLoading, setJudgeLoading] = useState(false);
  const [judgeError, setJudgeError] = useState<string | null>(null);

  function refreshQueueCount() {
    api.getQueue().then((q) => setQueueCount(q.length)).catch(() => {});
  }

  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .catch((e: Error) => console.error("listCases:", e.message))
      .finally(() => setCasesLoading(false));

    refreshQueueCount();
  }, []);

  function handleSelectCase(id: string) {
    setSelectedId(id);
    setSelectedCase(null);
    setJudgeResponse(null);
    setJudgeError(null);
    setCaseLoading(true);
    api
      .getCase(id)
      .then(setSelectedCase)
      .catch((e: Error) => console.error("getCase:", e.message))
      .finally(() => setCaseLoading(false));
  }

  function handleEvaluate() {
    if (!selectedCase) return;
    setJudgeResponse(null);
    setJudgeError(null);
    setJudgeLoading(true);
    api
      .judge(selectedCase.id)
      .then((resp) => {
        setJudgeResponse(resp);
        refreshQueueCount(); // new verdicts may be escalated
      })
      .catch((e: Error) => setJudgeError(e.message))
      .finally(() => setJudgeLoading(false));
  }

  void caseLoading;

  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans">
      {/* ── two-row header ── */}
      <header className="shrink-0 flex flex-col">
        {/* row 1: clinical safety banner */}
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800 font-medium">
          Demo: not for clinical use. All cases are synthetic. Results must not guide medical decisions.
        </div>
        {/* row 2: tab nav */}
        <div className="bg-white border-b border-gray-200 flex">
          <button
            onClick={() => setView("cases")}
            className={[
              "px-4 py-2 text-xs font-semibold transition-colors",
              view === "cases"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700",
            ].join(" ")}
          >
            Cases
          </button>
          <button
            onClick={() => setView("queue")}
            className={[
              "px-4 py-2 text-xs font-semibold transition-colors flex items-center gap-1.5",
              view === "queue"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-500 hover:text-gray-700",
            ].join(" ")}
          >
            Review Queue
            {queueCount > 0 && (
              <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                {queueCount}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* ── main content ── */}
      {view === "cases" ? (
        <div className="flex flex-1 overflow-hidden">
          {/* sidebar */}
          <aside className="w-64 shrink-0 border-r border-gray-200 bg-white overflow-y-auto">
            <div className="px-4 pt-4 pb-2">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Cases
              </h2>
            </div>
            <CaseList
              cases={cases}
              selectedId={selectedId}
              loading={casesLoading}
              onSelect={handleSelectCase}
            />
          </aside>

          {/* scorecard */}
          <main className="flex-1 overflow-y-auto">
            <ScoreCard
              selectedCase={selectedCase}
              judgeResponse={judgeResponse}
              loading={judgeLoading}
              error={judgeError}
              onEvaluate={handleEvaluate}
            />
          </main>
        </div>
      ) : (
        <main className="flex-1 overflow-y-auto">
          <ReviewQueue onCountChange={setQueueCount} />
        </main>
      )}
    </div>
  );
}
