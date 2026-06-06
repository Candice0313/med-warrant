# Phase 5 — Human-in-the-Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Review Queue tab (escalated verdicts with approve/override), evidence snippet chips with inline expansion on every DimensionRow, and the queue count badge that refreshes after each judge call.

**Architecture:** `EvidenceSnippets` is a pure display component shared by both `DimensionRow` and `ReviewQueue`. `App` owns `view` + `queueCount` state; `ReviewQueue` owns its own verdict list and calls `onCountChange` after each review action. The queue API stubs in `api.ts` are replaced with real `fetch` calls.

**Tech Stack:** React 18 + TypeScript, Tailwind CSS v3, existing FastAPI backend at `http://localhost:8000`.

---

## File map

| File | Change |
|---|---|
| `frontend/src/api.ts` | Replace `getQueue` + `review` stubs with real fetch calls |
| `frontend/src/components/EvidenceSnippets.tsx` | NEW — chips + inline snippet expansion |
| `frontend/src/components/DimensionRow.tsx` | Add `<EvidenceSnippets>` below the confidence bar |
| `frontend/src/components/ReviewQueue.tsx` | NEW — queue view with approve/override cards |
| `frontend/src/App.tsx` | Add `view`/`queueCount` state, two-row header with tabs, view switcher |

---

## Task 1: Implement real `getQueue` and `review` in api.ts

**Files:**
- Modify: `frontend/src/api.ts`

- [ ] **Step 1: Replace stubs with real implementations**

Open `frontend/src/api.ts` and replace the entire `api` object with:

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

  searchEvidence: (_q: string): Promise<never> => {
    throw new Error("searchEvidence: not implemented until Phase 6");
  },

  getQueue: () => request<Verdict[]>("/api/queue"),

  review: (body: { verdict_id: string; decision: string; note: string }) =>
    request<Verdict>("/api/review", {
      method: "POST",
      body: JSON.stringify(body),
    }),
} as const;
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

- [ ] **Step 3: Smoke-test the queue endpoint**

```bash
curl -s http://localhost:8000/api/queue | python3 -m json.tool | head -20
```

Expected: JSON array (may be empty if no cases judged yet, or contain escalated verdicts if judged earlier).

---

## Task 2: Create `EvidenceSnippets.tsx`

**Files:**
- Create: `frontend/src/components/EvidenceSnippets.tsx`

- [ ] **Step 1: Write the component**

Create `frontend/src/components/EvidenceSnippets.tsx`:

```tsx
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
            📄 {g.source_id} · {g.score}
          </button>
        ))}
      </div>

      {/* inline expansion */}
      {active && (
        <div className="rounded-lg border border-blue-100 bg-blue-50/40 p-3 flex flex-col gap-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[10px] text-gray-600">{active.source_id}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
              {TIER_META[active.tier]?.code ?? active.tier} — {TIER_META[active.tier]?.label ?? active.tier}
            </span>
          </div>
          <p className="text-xs text-gray-600 leading-relaxed border-l-2 border-blue-200 pl-3 italic">
            "{active.snippet}"
          </p>
          <a
            href={active.source_id.startsWith("http") ? active.source_id : "#"}
            target="_blank"
            rel="noreferrer"
            className="text-[10px] text-gray-400 hover:text-blue-500 transition-colors truncate"
          >
            🔗 source: {active.source_id}
          </a>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 3: Wire `EvidenceSnippets` into `DimensionRow`

**Files:**
- Modify: `frontend/src/components/DimensionRow.tsx`

The current file ends at line 128. Add one import at the top and one JSX element after the bar annotation `<div>`.

- [ ] **Step 1: Add the import**

In `frontend/src/components/DimensionRow.tsx`, add to the imports at the top (after the existing imports on lines 1-2):

```tsx
import { EvidenceSnippets } from "./EvidenceSnippets";
```

The first three lines of the file should now read:
```tsx
import { EVIDENCE_CEILINGS, TIER_META } from "../constants";
import { EvidenceSnippets } from "./EvidenceSnippets";
import type { Dimension, Verdict } from "../types";
```

- [ ] **Step 2: Add `<EvidenceSnippets>` after the bar annotation row**

The bar section ends with:
```tsx
        <div className="flex justify-between mt-0.5 text-[9px] text-gray-400">
          <span>model {Math.round(verdict.model_confidence * 100)}%</span>
          <span>ceiling {Math.round(ceiling * 100)}%</span>
        </div>
      </div>
    </div>
  );
}
```

Replace that closing sequence with:
```tsx
        <div className="flex justify-between mt-0.5 text-[9px] text-gray-400">
          <span>model {Math.round(verdict.model_confidence * 100)}%</span>
          <span>ceiling {Math.round(ceiling * 100)}%</span>
        </div>
      </div>
      <EvidenceSnippets grounding={verdict.grounding} />
    </div>
  );
}
```

- [ ] **Step 3: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 4: Create `ReviewQueue.tsx`

**Files:**
- Create: `frontend/src/components/ReviewQueue.tsx`

- [ ] **Step 1: Write the component**

Create `frontend/src/components/ReviewQueue.tsx`:

```tsx
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
        All caught up — no escalated verdicts awaiting review. ✓
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
          className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden"
        >
          {/* card header */}
          <div className={[
            "px-4 pt-3 pb-2 border-l-4",
            v.escalation?.severity === "danger" ? "border-l-red-500 bg-red-50" : "border-l-amber-400 bg-amber-50",
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
                      ? "⚠ UNVERIFIED SAFETY"
                      : "↓ LOW CONFIDENCE"}
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
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 5: Update `App.tsx` — tabs, queue count, view switcher

**Files:**
- Modify: `frontend/src/App.tsx`

Replace the entire file with:

- [ ] **Step 1: Write the new App.tsx**

```tsx
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
          ⚠ Demo — not for clinical use. All cases are synthetic. Results must not guide medical decisions.
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
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 6: Browser verification

**Files:** none — verification only.

- [ ] **Step 1: Confirm both servers are running**

```bash
curl -s http://localhost:8000/api/cases | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} cases')"
curl -s http://localhost:5173 | head -3
```

Expected: `4 cases` and HTML from Vite.

If either is down:
```bash
# backend
cd /Users/candice/Desktop/med-warrant/backend && python -m uvicorn main:app --port 8000 &
# frontend
cd /Users/candice/Desktop/med-warrant/frontend && npm run dev -- --port 5173 &
```

- [ ] **Step 2: Verify via Playwright**

```bash
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
import os

SHOTS = "/tmp/phase5_verify"
os.makedirs(SHOTS, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:5173", wait_until="networkidle")

    # 1. Two-row header: banner + tab nav
    banner = page.locator("text=Demo — not for clinical use").is_visible()
    cases_tab = page.locator("button", has_text="Cases").is_visible()
    queue_tab = page.locator("button", has_text="Review Queue").is_visible()
    print(f"Banner: {banner} | Cases tab: {cases_tab} | Queue tab: {queue_tab}")
    page.screenshot(path=f"{SHOTS}/01_tabs.png")

    # 2. Judge a case to populate the queue
    page.locator("nav button").first.click()
    page.wait_for_timeout(500)
    page.locator("button", has_text="Evaluate").click()
    page.wait_for_selector("text=LOW CONFIDENCE", timeout=12000)
    page.screenshot(path=f"{SHOTS}/02_after_judge.png")

    # 3. Evidence chips appear on DimensionRow
    chips = page.locator("button", has_text="📄").all()
    print(f"Evidence chips visible: {len(chips)}")

    # 4. Click a chip — inline expansion appears
    if chips:
        chips[0].click()
        page.wait_for_timeout(300)
        expanded = page.locator("text=systematic review").is_visible() or \
                   page.locator("text=guideline").is_visible() or \
                   page.locator("text=rct").is_visible()
        print(f"Inline expansion appeared: {expanded}")
        page.screenshot(path=f"{SHOTS}/03_chip_expanded.png")
        # Click again to collapse
        chips[0].click()
        page.wait_for_timeout(200)

    # 5. Queue badge count updated after judge
    badge = page.locator(".bg-red-500").first
    badge_text = badge.inner_text() if badge.is_visible() else "no badge"
    print(f"Queue badge: {badge_text!r}")

    # 6. Switch to Review Queue tab
    page.locator("button", has_text="Review Queue").click()
    page.wait_for_timeout(600)
    page.screenshot(path=f"{SHOTS}/04_queue_view.png")
    queue_cards = page.locator(".rounded-xl.border.border-gray-200.bg-white.shadow-sm").all()
    print(f"Queue cards: {len(queue_cards)}")

    # 7. Evidence chips in queue card
    queue_chips = page.locator("button", has_text="📄").all()
    print(f"Queue evidence chips: {len(queue_chips)}")

    # 8. Approve the first card
    approve_btn = page.locator("button", has_text="Approve").first
    if approve_btn.is_visible():
        verdict_count_before = len(page.locator(".rounded-xl.border.border-gray-200.bg-white.shadow-sm").all())
        approve_btn.click()
        page.wait_for_timeout(600)
        verdict_count_after = len(page.locator(".rounded-xl.border.border-gray-200.bg-white.shadow-sm").all())
        print(f"Cards before approve: {verdict_count_before}, after: {verdict_count_after}")
        page.screenshot(path=f"{SHOTS}/05_after_approve.png")

    # 9. Override flow
    override_btn = page.locator("button", has_text="Override…").first
    if override_btn.is_visible():
        override_btn.click()
        page.wait_for_timeout(200)
        textarea = page.locator("textarea").first
        textarea.fill("Overriding — low evidence but clinical context justifies this verdict.")
        page.wait_for_timeout(100)
        confirm_btn = page.locator("button", has_text="Confirm override").first
        print(f"Confirm override enabled: {not confirm_btn.is_disabled()}")
        page.screenshot(path=f"{SHOTS}/06_override_form.png")

    browser.close()
    print(f"\nScreenshots: {SHOTS}/")
EOF
```

Expected output:
```
Banner: True | Cases tab: True | Queue tab: True
Evidence chips visible: > 0
Inline expansion appeared: True
Queue badge: '1'  (or more)
Queue cards: >= 1
Approve removes card: before > after
Confirm override enabled: True
```

- [ ] **Step 3: Inspect screenshots**

Read `/tmp/phase5_verify/04_queue_view.png` to confirm queue cards render with SAFETY/WARNING pills, model reasoning, evidence chips, and action buttons.
