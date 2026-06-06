# Phase 3 — Scorecard UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React scorecard UI that calls the live backend, shows a per-dimension dual confidence bar (faded = model, solid = capped, ceiling tick), colour-codes rows by trust band, and never displays a single aggregate score.

**Architecture:** Sidebar + Main layout rooted in App.tsx. App owns all network state (cases list, selected case, verdicts/summary) and passes data down as props. Every component below App is a pure display function. ScoreCard joins verdicts with Case.dimensions by ID so DimensionRow receives a fully-resolved (Verdict, Dimension) pair.

**Tech Stack:** Vite + React 18 + TypeScript (`react-ts` template), Tailwind CSS v3 (PostCSS), recharts (installed now, used Phase 7), backend on `http://localhost:8000` via `VITE_API_URL`.

---

## File map

| File | Responsibility |
|---|---|
| `frontend/src/types.ts` | All TypeScript interfaces mirroring backend Pydantic models |
| `frontend/src/constants.ts` | `EVIDENCE_CEILINGS`, `TIER_META` (label + code) |
| `frontend/src/api.ts` | Typed fetch wrappers for all 6 backend endpoints |
| `frontend/src/components/ComplexityTags.tsx` | Two complexity pill badges (reasoning × visual) |
| `frontend/src/components/CaseList.tsx` | Sidebar case list with selection state |
| `frontend/src/components/DimensionRow.tsx` | Two-line card: name/badges + dual confidence bar |
| `frontend/src/components/ScoreCard.tsx` | Summary pill strip + ordered DimensionRow list |
| `frontend/src/App.tsx` | Root: banner + sidebar + main; all useState/useEffect |
| `frontend/src/index.css` | Tailwind directives |
| `frontend/src/main.tsx` | React root mount |
| `frontend/.env.local` | `VITE_API_URL=http://localhost:8000` |

---

## Task 1: Scaffold Vite project and install dependencies

**Files:**
- Create: `frontend/` (entire directory via Vite scaffold)
- Create: `frontend/.env.local`

- [ ] **Step 1: Scaffold**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npm create vite@latest . -- --template react-ts --yes 2>/dev/null || \
  (npm create vite@5 . -- --template react-ts && echo done)
```

If the directory already has files, Vite will ask to overwrite — choose to ignore/merge existing files, or run in an empty temp dir and copy.

- [ ] **Step 2: Install runtime + dev dependencies**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npm install
npm install recharts
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: Configure Tailwind content paths**

Edit `frontend/tailwind.config.js` — replace the generated content array:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 4: Add Tailwind directives to CSS**

Replace all content in `frontend/src/index.css` with:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Create env file**

Create `frontend/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npm run dev -- --port 5173 &
```

Expected: Vite prints `http://localhost:5173`. Kill with `kill %1` once confirmed. TypeScript errors are expected at this point (we haven't written our files yet).

---

## Task 2: Types

**Files:**
- Create: `frontend/src/types.ts`

- [ ] **Step 1: Write types (mirrors backend Pydantic models exactly)**

Create `frontend/src/types.ts`:

```ts
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
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: errors only from App.tsx / main.tsx boilerplate (not from types.ts).

---

## Task 3: Constants

**Files:**
- Create: `frontend/src/constants.ts`

- [ ] **Step 1: Write constants (must match backend/capping.py exactly)**

Create `frontend/src/constants.ts`:

```ts
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
```

---

## Task 4: api.ts

**Files:**
- Create: `frontend/src/api.ts`

- [ ] **Step 1: Write typed fetch client**

Create `frontend/src/api.ts`:

```ts
import type { Case, CaseSummary, JudgeResponse, Verdict } from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listCases: () => request<CaseSummary[]>("/api/cases"),

  getCase: (id: string) => request<Case>(`/api/cases/${id}`),

  judge: (case_id: string) =>
    request<JudgeResponse>("/api/judge", {
      method: "POST",
      body: JSON.stringify({ case_id }),
    }),

  // Stubs — implemented in Phase 5
  searchEvidence: (_q: string): Promise<never> => {
    throw new Error("searchEvidence: not implemented until Phase 5");
  },
  getQueue: (): Promise<never> => {
    throw new Error("getQueue: not implemented until Phase 5");
  },
  review: (_body: unknown): Promise<never> => {
    throw new Error("review: not implemented until Phase 5");
  },
} as const;
```

---

## Task 5: ComplexityTags

**Files:**
- Create: `frontend/src/components/ComplexityTags.tsx`

- [ ] **Step 1: Write component**

Create `frontend/src/components/ComplexityTags.tsx`:

```tsx
interface Props {
  complexity: { reasoning: string; visual_dependency: string };
}

const REASONING_COLOUR: Record<string, string> = {
  low:    "bg-green-100 text-green-800",
  medium: "bg-amber-100 text-amber-800",
  high:   "bg-red-100 text-red-800",
};

const VISUAL_COLOUR: Record<string, string> = {
  low:    "bg-gray-100 text-gray-600",
  medium: "bg-amber-100 text-amber-800",
  high:   "bg-red-100 text-red-800",
};

export function ComplexityTags({ complexity }: Props) {
  return (
    <div className="flex gap-1 mt-1 flex-wrap">
      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${REASONING_COLOUR[complexity.reasoning] ?? "bg-gray-100 text-gray-600"}`}>
        reasoning: {complexity.reasoning}
      </span>
      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${VISUAL_COLOUR[complexity.visual_dependency] ?? "bg-gray-100 text-gray-600"}`}>
        visual: {complexity.visual_dependency}
      </span>
    </div>
  );
}
```

---

## Task 6: CaseList

**Files:**
- Create: `frontend/src/components/CaseList.tsx`

- [ ] **Step 1: Write component**

Create `frontend/src/components/CaseList.tsx`:

```tsx
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
```

---

## Task 7: DimensionRow

**Files:**
- Create: `frontend/src/components/DimensionRow.tsx`

This is the most important component. The dual bar uses inline `style` for widths because Tailwind can't generate arbitrary dynamic percentage classes at runtime.

- [ ] **Step 1: Write colour-derivation helper (at top of file)**

Create `frontend/src/components/DimensionRow.tsx`:

```tsx
import { EVIDENCE_CEILINGS, TIER_META } from "../constants";
import type { Dimension, Verdict } from "../types";

// ── colour helpers ──────────────────────────────────────────────────────────

type Band = "trustworthy" | "caution" | "escalated-danger" | "escalated-warning";

function band(verdict: Verdict): Band {
  if (verdict.escalation?.severity === "danger")   return "escalated-danger";
  if (verdict.escalation?.severity === "warning")  return "escalated-warning";
  if (verdict.displayed_confidence >= 0.75)        return "trustworthy";
  return "caution";
}

const BORDER: Record<Band, string> = {
  trustworthy:         "border-l-green-500  bg-green-50",
  caution:             "border-l-amber-400  bg-amber-50",
  "escalated-danger":  "border-l-red-500    bg-red-50",
  "escalated-warning": "border-l-amber-500  bg-amber-50",
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
}

export function DimensionRow({ verdict, dimension }: Props) {
  const b = band(verdict);
  const barColour = BAR_HEX[b];
  const ceiling = EVIDENCE_CEILINGS[verdict.grounded_tier] ?? 0.4;
  const tierCode = TIER_META[verdict.grounded_tier]?.code ?? "??";

  return (
    <div
      className={[
        "rounded-lg border border-gray-200 border-l-4 overflow-hidden",
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

        {verdict.escalation && (
          <span
            className={[
              "text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0",
              verdict.escalation.severity === "danger"
                ? "bg-red-600 text-white"
                : "bg-amber-500 text-white",
            ].join(" ")}
          >
            {verdict.escalation.reason === "unverified_safety_claim"
              ? "⚠ UNVERIFIED SAFETY"
              : "↓ LOW CONFIDENCE"}
          </span>
        )}

        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 shrink-0 font-mono">
          {tierCode}
        </span>

        <span className={`text-sm font-bold shrink-0 ${PCT_CLASS[b]}`}>
          {Math.round(verdict.displayed_confidence * 100)}%
        </span>
      </div>

      {/* ── bottom line: dual bar ── */}
      <div className="px-3 pb-2.5">
        <div
          className="relative h-2.5 rounded-full bg-gray-200"
          title={`Model: ${Math.round(verdict.model_confidence * 100)}%  Capped: ${Math.round(verdict.displayed_confidence * 100)}%  Ceiling: ${Math.round(ceiling * 100)}%`}
        >
          {/* faded: model confidence */}
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
              width: `${verdict.displayed_confidence * 100}%`,
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
    </div>
  );
}
```

---

## Task 8: ScoreCard

**Files:**
- Create: `frontend/src/components/ScoreCard.tsx`

- [ ] **Step 1: Write component**

Create `frontend/src/components/ScoreCard.tsx`:

```tsx
import { DimensionRow } from "./DimensionRow";
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
  if (!selectedCase) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Select a case from the sidebar to evaluate it.
      </div>
    );
  }

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
      {/* ── case header ── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4">
        <p className="text-xs text-gray-500 italic border-l-2 border-gray-200 pl-3 mb-3 leading-relaxed">
          "{selectedCase.patient_question}"
        </p>

        {/* summary pill strip */}
        {summary ? (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-green-100 text-green-800">
              ✓ {summary.trustworthy} trustworthy
            </span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
              ◐ {summary.caution} caution
            </span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-red-100 text-red-800">
              ⚠ {summary.escalated} escalated
            </span>
            <span className="ml-auto text-[11px] text-gray-300 line-through">
              avg {summary.mixed_average_suppressed}%
            </span>
          </div>
        ) : (
          !loading && (
            <p className="text-xs text-gray-400">
              {selectedCase.dimensions.length} dimensions — click Evaluate to run the judge.
            </p>
          )
        )}

        {loading && (
          <div className="flex gap-2 mt-1">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-7 w-24 rounded-full bg-gray-100 animate-pulse" />
            ))}
          </div>
        )}

        <button
          onClick={onEvaluate}
          disabled={loading}
          className={[
            "mt-3 text-xs font-semibold px-4 py-1.5 rounded-lg transition-colors",
            loading
              ? "bg-gray-100 text-gray-400 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700",
          ].join(" ")}
        >
          {loading ? "Evaluating…" : "Evaluate"}
        </button>

        {error && (
          <p className="mt-2 text-xs text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
        )}
      </div>

      {/* ── dimension rows ── */}
      {loading && rows.length === 0 && (
        <div className="flex flex-col gap-3">
          {selectedCase.dimensions.map((_, i) => (
            <div key={i} className="h-20 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {rows.length > 0 && (
        <div className="flex flex-col gap-3">
          {rows.map(({ verdict, dimension }) => (
            <DimensionRow
              key={verdict.verdict_id}
              verdict={verdict}
              dimension={dimension}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Task 9: App.tsx

**Files:**
- Modify: `frontend/src/App.tsx` (replace entire file)
- Modify: `frontend/src/main.tsx` (ensure CSS import and React 18 root)

- [ ] **Step 1: Write App.tsx**

Replace `frontend/src/App.tsx` with:

```tsx
import { useEffect, useState } from "react";
import { api } from "./api";
import { CaseList } from "./components/CaseList";
import { ScoreCard } from "./components/ScoreCard";
import type { Case, CaseSummary, JudgeResponse } from "./types";

export default function App() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [casesLoading, setCasesLoading] = useState(true);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [caseLoading, setCaseLoading] = useState(false);

  const [judgeResponse, setJudgeResponse] = useState<JudgeResponse | null>(null);
  const [judgeLoading, setJudgeLoading] = useState(false);
  const [judgeError, setJudgeError] = useState<string | null>(null);

  // Load case list on mount
  useEffect(() => {
    api
      .listCases()
      .then(setCases)
      .catch((e: Error) => console.error("listCases:", e.message))
      .finally(() => setCasesLoading(false));
  }, []);

  function handleSelectCase(id: string) {
    setSelectedId(id);          // highlight immediately, before fetch resolves
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
      .then(setJudgeResponse)
      .catch((e: Error) => setJudgeError(e.message))
      .finally(() => setJudgeLoading(false));
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans">
      {/* ── persistent banner ── */}
      <header className="shrink-0 bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800 font-medium">
        ⚠ Demo — not for clinical use. All cases are synthetic. Results must not guide medical decisions.
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* ── sidebar ── */}
        <aside className="w-64 shrink-0 border-r border-gray-200 bg-white overflow-y-auto">
          <div className="px-4 pt-4 pb-2">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Cases</h2>
          </div>
          <CaseList
            cases={cases}
            selectedId={selectedId}
            loading={casesLoading}
            onSelect={handleSelectCase}
          />
        </aside>

        {/* ── main ── */}
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
    </div>
  );
}
```

- [ ] **Step 2: Fix main.tsx**

Replace `frontend/src/main.tsx` with:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

---

## Task 10: TypeScript check + start backend + verify in browser

**Files:** none — verification only.

- [ ] **Step 1: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npx tsc --noEmit 2>&1
```

Expected: zero errors. Fix any that appear (usually a missing `!` on a non-null assertion or a missing import).

- [ ] **Step 2: Start the backend (if not running)**

```bash
cd /Users/candice/Desktop/med-warrant/backend
python -m uvicorn main:app --reload --port 8000 &
```

Wait 2 seconds, then confirm:

```bash
curl -s http://localhost:8000/api/cases | python3 -m json.tool | head -10
```

Expected: JSON array of 4 cases.

- [ ] **Step 3: Start the frontend dev server**

```bash
cd /Users/candice/Desktop/med-warrant/frontend
npm run dev -- --port 5173
```

Expected: Vite prints `Local: http://localhost:5173`.

- [ ] **Step 4: Browser smoke test** (golden paths)

Open `http://localhost:5173` and verify:

1. Amber banner "Demo — not for clinical use" spans the top.
2. Sidebar shows 4 case items with complexity tags.
3. Main shows "Select a case from the sidebar".
4. Click **"I'm on warfarin…"** case → main shows the patient question + Evaluate button.
5. Click **Evaluate** → loading skeletons appear, then 4 DimensionRows.
6. Check `drug_interaction_safety` row: SAFETY badge visible, grounded to `T1`/`T2`, displayed% < 100%.
7. Check `monitoring_followup` row: ↓ LOW CONFIDENCE pill, amber colour.
8. Summary pill strip shows trustworthy / caution / escalated counts; struck-through avg% right-aligned.
9. Repeat for at least one other case.

- [ ] **Step 5: Edge case check**

10. Click a second case without refreshing — scorecard resets cleanly.
11. Open browser DevTools → Network tab → confirm no request to `/api/overall_score` or any aggregate endpoint.
12. Console: zero errors (React warnings about keys are acceptable if any; fix them).
