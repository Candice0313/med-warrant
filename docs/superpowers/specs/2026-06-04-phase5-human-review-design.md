# Phase 5 — Human-in-the-Loop Design

**Date:** 2026-06-04  
**Scope:** Review Queue tab, EvidenceSnippets inline expansion, approve/override workflow.  
**Deferred:** TierSelector (Phase 6), ProfileRadar (Phase 7).

---

## 1. Layout change

The existing `<header>` gains a **second row** for tab navigation — banner text stays on row 1, tabs on row 2:

```
┌──────────────────────────────────────────────────────────┐
│  ⚠ Demo — not for clinical use. All cases synthetic.     │  ← row 1 (existing amber)
│  [ Cases ]    [ Review Queue  🔴3 ]                      │  ← row 2 (white bg, border-b)
└──────────────────────────────────────────────────────────┘
```

- `view: "cases" | "queue"` state in `App.tsx` (default `"cases"`).
- Red badge on the queue tab when `queueCount > 0`; badge hidden when 0.
- Main area renders `<ScoreCard>` for `"cases"` and `<ReviewQueue>` for `"queue"`.
- Sidebar (case list) is **only shown** in the `"cases"` view; hidden in queue view.

---

## 2. Component tree

```
App.tsx
├── TabNav (inline — not a separate file)   Cases | Review Queue [N]
├── [view === "cases"]
│   ├── CaseList.tsx        (sidebar — unchanged)
│   └── ScoreCard.tsx       (main — DimensionRow now includes EvidenceSnippets)
│       └── DimensionRow.tsx
│           └── EvidenceSnippets.tsx   ← NEW: chips + inline expansion
└── [view === "queue"]
    └── ReviewQueue.tsx     ← NEW: escalated verdict cards + approve/override
        └── EvidenceSnippets.tsx   (same component, reused)
```

---

## 3. New files

### `frontend/src/components/EvidenceSnippets.tsx`

**Props:** `{ grounding: GroundingSnippet[] }`  
**State:** `activeIdx: number | null`

- Renders nothing if `grounding` is empty.
- One chip per snippet: `[source_id · score N]` — small blue pill buttons.
- `activeIdx` tracks which chip is expanded; `null` = none.
- Clicking a chip: if it's the active one → collapse (`activeIdx = null`); otherwise → expand it (`activeIdx = i`). Only one open at a time.
- Expanded panel (rendered below the chips row):
  - Source ID as monospace label.
  - Tier badge using `TIER_META[snippet.tier].code` + label (from `constants.ts`).
  - Snippet text in a left-bordered quoted block (`border-l-2 border-blue-200 pl-3 italic text-gray-600`).
  - URL as a small grey `<a>` link (opens in new tab). If URL is a placeholder (`example.org`), still render it — this is a demo.
- No external fetch; all data is inside `GroundingSnippet`.

---

### `frontend/src/components/ReviewQueue.tsx`

**Props:** `{ onCountChange: (n: number) => void }`  
**State:**
- `verdicts: Verdict[]`
- `loading: boolean`
- `fetchError: string | null` — error from the initial queue fetch
- `actionErrors: Record<string, string>` — per-card error from approve/review call, keyed by `verdict_id`
- `overrideNotes: Record<string, string>` — note text keyed by `verdict_id`
- `overrideOpen: Record<string, boolean>` — whether the override textarea is shown

**Behaviour:**

- Fetches `api.getQueue()` on mount. Passes result length to `onCountChange`.
- Each verdict card renders:
  1. **Header line**: `case_id` · dimension ID (used as label until a case lookup is available — no extra fetch) · escalation pill (red DANGER or amber WARNING).
  2. **Model reasoning**: `verdict.model_reasoning` — full text, no truncation.
  3. **`<EvidenceSnippets grounding={verdict.grounding} />`**
  4. **Action row**: `[Approve]` button (green) · `[Override…]` button (amber).
- **Approve flow**: `api.review({ verdict_id, decision: "approve", note: "" })` → on success, remove verdict from local list → call `onCountChange(newLength)`.
- **Override flow**: clicking `[Override…]` toggles `overrideOpen[id]` to show a `<textarea>` + `[Confirm override]` button. Confirm calls `api.review({ verdict_id, decision: "override", note })` → same removal + recount. `[Cancel]` hides the textarea.
- **Loading state**: skeleton cards (3 × pulsing placeholder).
- **Error state**: red inline banner.
- **Empty state**: centred grey text "All caught up — no escalated verdicts awaiting review. ✓"

**Note on dimension labels:** `verdict.dimension` is the dimension ID string (e.g. `"drug_interaction_safety"`). ReviewQueue renders it directly (converting underscores to spaces + title-casing) rather than fetching the full Case object. This keeps the queue self-contained.

---

## 4. Modified files

### `frontend/src/api.ts`

Replace the two stub throws with real implementations:

```ts
getQueue: () => request<Verdict[]>("/api/queue"),

review: (body: { verdict_id: string; decision: string; note: string }) =>
  request<Verdict>("/api/review", {
    method: "POST",
    body: JSON.stringify(body),
  }),
```

`Verdict` is already imported from `./types`.

---

### `frontend/src/components/DimensionRow.tsx`

Add one import and one JSX line below the confidence bar's label row:

```tsx
import { EvidenceSnippets } from "./EvidenceSnippets";
// ...inside the component, after the bar annotation row:
<EvidenceSnippets grounding={verdict.grounding} />
```

No other changes to `DimensionRow`.

---

### `frontend/src/App.tsx`

Add state:
```ts
const [view, setView] = useState<"cases" | "queue">("cases");
const [queueCount, setQueueCount] = useState(0);
```

Fetch queue count on mount (after `listCases`):
```ts
api.getQueue().then((q) => setQueueCount(q.length)).catch(() => {});
```

Also re-fetch after each `judge()` call resolves (new verdicts may be escalated).

Tab nav added as a **second row** inside the existing `<header>` element:

```tsx
<header className="shrink-0 flex flex-col">
  {/* row 1: existing banner */}
  <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-xs text-amber-800 font-medium">
    ⚠ Demo — not for clinical use. All cases are synthetic. Results must not guide medical decisions.
  </div>
  {/* row 2: tab nav */}
  <div className="bg-white border-b border-gray-200 flex">
    <button onClick={() => setView("cases")} className={view === "cases" ? "tab-active" : "tab"}>Cases</button>
    <button onClick={() => setView("queue")} className={view === "queue" ? "tab-active" : "tab"}>
      Review Queue
      {queueCount > 0 && <span className="ml-1.5 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">{queueCount}</span>}
    </button>
  </div>
</header>
```

Main area:
```tsx
{view === "cases" ? (
  <div className="flex flex-1 overflow-hidden">
    <aside>…<CaseList /></aside>
    <main>…<ScoreCard /></main>
  </div>
) : (
  <main className="flex-1 overflow-y-auto">
    <ReviewQueue onCountChange={(n) => setQueueCount(n)} />
  </main>
)}
```

---

## 5. Data flow

```
mount
  → api.listCases()       → cases list
  → api.getQueue()        → queueCount (badge)

user clicks Evaluate
  → api.judge(id)         → verdicts/summary
  → api.getQueue()        → refresh queueCount (new escalations may have appeared)

user switches to queue tab
  → ReviewQueue mounts    → api.getQueue() → full verdict list

user clicks Approve/Override
  → api.review(…)         → success
  → remove card from local list
  → onCountChange(newLength) → App updates badge
```

---

## 6. Error and loading states

| State | Behaviour |
|---|---|
| Queue loading | 3 skeleton cards |
| Queue fetch error | Red inline banner in `ReviewQueue` |
| Review action error | Red inline banner below the action row of that card |
| Empty queue | Centred "All caught up…" message |

---

## 7. Out of scope for Phase 5

- Case lookup for full dimension labels in queue cards (use ID → readable string conversion instead)
- Pagination of the queue
- Bulk approve/reject
- `TierSelector` (Phase 6), `ProfileRadar` (Phase 7)
