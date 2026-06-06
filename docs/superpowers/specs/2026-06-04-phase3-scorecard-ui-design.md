# Phase 3 — Scorecard UI Design

**Date:** 2026-06-04  
**Scope:** Vite + React + TypeScript frontend, Phase 3 only (Scorecard UI reading the real API).  
**Deferred:** TierSelector (Phase 6), EvidenceDrawer / ReviewQueue (Phase 5), ProfileRadar (Phase 7).

---

## 1. Layout

**Sidebar + Main** split at the application root.

```
┌─────────────────────────────────────────────────────────┐
│  ⚠ Demo — not for clinical use                 [banner] │
├──────────────────┬──────────────────────────────────────┤
│  Cases           │  ScoreCard                           │
│  ─────────────   │  ─────────────────────────────────── │
│  [case item]  ◄  │  [summary pill strip]                │
│  [case item]     │  [DimensionRow]                      │
│  [case item]     │  [DimensionRow]                      │
│  [case item]     │  [DimensionRow]                      │
│                  │  [DimensionRow]                      │
└──────────────────┴──────────────────────────────────────┘
```

- Sidebar: fixed width (~260 px), scrollable, lists all cases.
- Main: remaining space, scrollable, shows the selected case's scorecard.
- Banner: full-width persistent strip above both panels; amber background, non-dismissible.
- On first load, no case is selected; main shows a prompt ("Select a case to evaluate").

---

## 2. Component tree

```
App.tsx
├── Banner (inline — no separate file needed)
├── CaseList.tsx        (sidebar)
│   └── ComplexityTags.tsx  (per case item)
└── ScoreCard.tsx       (main)
    └── DimensionRow.tsx × N
```

`api.ts` is a typed client module, not a component.

---

## 3. Component specs

### `api.ts`

Typed wrappers for the backend. Base URL from `import.meta.env.VITE_API_URL` (defaults to `http://localhost:8000`). Phase 3 calls only three endpoints:

| Function | Method + path | Returns |
|---|---|---|
| `listCases()` | GET `/api/cases` | `CaseSummary[]` |
| `getCase(id)` | GET `/api/cases/{id}` | `Case` |
| `judge(case_id)` | POST `/api/judge` | `JudgeResponse` |

Remaining endpoints (`searchEvidence`, `getQueue`, `review`) stubbed as typed functions that throw `"not implemented"` — they will be filled in Phase 5.

All functions return typed promises; errors propagate as thrown `Error` objects with a human-readable message.

---

### `CaseList.tsx`

Props: `{ cases: CaseSummary[], selectedId: string | null, onSelect: (id: string) => void }`

- Renders one clickable item per case.
- Selected item has a blue left border highlight.
- Each item shows: patient question (truncated to ~2 lines) + `<ComplexityTags>`.
- Loading state: 4 skeleton placeholder divs.

---

### `ComplexityTags.tsx`

Props: `{ complexity: { reasoning: string, visual_dependency: string } }`

- Renders two small pill badges: `reasoning: high` and `visual: low`.
- Reasoning: green (low) → amber (medium) → red (high).
- Visual dependency: grey (low) → amber (medium) → red (high).

---

### `ScoreCard.tsx`

Props: `{ case: Case | null, verdicts: Verdict[], summary: Summary | null, loading: boolean, error: string | null }`

**Summary header** (pill strip style):

```
"<patient question>" (italic, left-bordered)
✓ N trustworthy   ◐ N caution   ⚠ N escalated       ~~avg N%~~
```

- Three colour pills (green / amber / red).
- Suppressed average: `<s>` element, grey, right-aligned. No tooltip or label — the strikethrough is the statement.
- When `loading`: pulsing skeleton in place of pills.
- When `error`: red inline banner.

**Dimension list**: one `<DimensionRow>` per verdict, ordered — escalated first, then caution, then trustworthy.

**Run Judge button**: "Evaluate" button in the case header triggers `api.judge()`. Disabled while loading.

---

### `DimensionRow.tsx`

Props: `{ verdict: Verdict, dimension: Dimension }`

`ScoreCard` joins verdict ↔ dimension by `verdict.dimension === dimension.id` before rendering each row; the join result is passed as two explicit props so `DimensionRow` remains a pure display component.

Two-line card, colour-coded by trust band:

```
┌─ [border colour] ──────────────────────────────────────────┐
│  Dimension name    [SAFETY]  [DANGER/WARNING pill]  T2  88%│
│  ░░░░░░░░░░████████████████████|░░░░░░░░░░░░░░░░░░░░░░░░░  │
└────────────────────────────────────────────────────────────┘
```

**Top line:**
- Dimension label (bold).
- `[SAFETY]` badge (red, solid) if `verdict.safety_critical === true`.
- Escalation pill: `⚠ UNVERIFIED SAFETY` (red) or `↓ LOW CONFIDENCE` (amber) if `verdict.escalation !== null`; absent otherwise.
- Evidence tier code (e.g., `T2`, `T4`) — grey chip, right side.
- `displayed_confidence` as bold percentage, coloured to trust band.

**Bottom line — dual confidence bar:**
- Track: full width, light grey background.
- Faded layer (model confidence): coloured at 40% opacity, width = `model_confidence × 100%`.
- Solid layer (capped confidence): full opacity, width = `displayed_confidence × 100%`. Always ≤ faded layer.
- Ceiling tick: a 2 px dark vertical line at `EVIDENCE_CEILINGS[grounded_tier] × 100%`. Extends slightly above/below the track. Represents the evidence ceiling; the solid bar can never cross it.

**Colour mapping** (left border + background tint + bar colour):

| Condition | Colour |
|---|---|
| `escalation.severity === "danger"` | red |
| `escalation.severity === "warning"` | amber |
| `displayed_confidence >= 0.75` | green |
| otherwise | amber |

---

## 4. Data flow

```
mount
  → api.listCases()
  → CaseList populated

user clicks case
  → App: selectedCaseId = id
  → api.getCase(id)  → Case stored in state (provides dimension labels)
  → ScoreCard renders the case header + empty scorecard; "Evaluate" button active

user clicks "Evaluate"
  → api.judge(id)  →  { verdicts, summary }
  → App joins verdicts ↔ Case.dimensions by dimension ID
  → ScoreCard re-renders with full data

DimensionRow receives (verdict, dimension) — pure, no internal data fetching.
No shared mutable state below App.tsx.
```

---

## 5. Tech stack

| Concern | Choice |
|---|---|
| Bundler | Vite |
| Framework | React 18 + TypeScript (`react-ts` template) |
| Styling | Tailwind CSS v3 via PostCSS |
| Charts | recharts (installed now, used Phase 7) |
| State | `useState` + `useEffect` in `App.tsx` — no library |
| API base URL | `VITE_API_URL` env var, default `http://localhost:8000` |

---

## 6. Error and loading states

| State | Behaviour |
|---|---|
| Cases loading | 4 skeleton cards in sidebar |
| Judge loading | Pulsing skeleton rows in scorecard; "Evaluate" button disabled |
| Judge error | Red inline banner inside ScoreCard; sidebar unchanged |
| No case selected | Main panel: grey prompt text |

---

## 7. Evidence ceilings on the frontend

The ceiling tick positions require knowing `EVIDENCE_CEILINGS` on the client. These are duplicated as a small const in `api.ts` (or a shared `constants.ts`) — they are configurable constants in the spec and unlikely to change at runtime, so a second source-of-truth is acceptable for a demo.

```ts
export const EVIDENCE_CEILINGS: Record<string, number> = {
  systematic_review: 0.95,
  rct: 0.90,
  guideline: 0.80,
  cohort: 0.75,
  expert: 0.60,
  model_prior: 0.40,
};
```

---

## 8. Out of scope for Phase 3

- `TierSelector` (live re-grounding — Phase 6)
- `EvidenceDrawer` (grounding snippet inspect — Phase 5)
- `ReviewQueue` (human review queue — Phase 5)
- `ProfileRadar` (radar chart — Phase 7)
- Authentication, persistence across page reload, dark mode.
