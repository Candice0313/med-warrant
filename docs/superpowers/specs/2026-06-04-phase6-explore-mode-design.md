# Phase 6 — Explore Mode (TierSelector) Design

**Date:** 2026-06-04  
**Scope:** Global explore-mode toggle on the scorecard; per-row tier dropdown; live re-capping and escalation recomputation in pure TypeScript.  
**Deferred:** ProfileRadar (Phase 7). No new API calls.

---

## 1. The demo's "aha" moment

Explore mode lets a viewer ask "what would happen to this verdict if its evidence tier were weaker (or stronger)?" — and see the answer immediately. The key demo transitions:

- Drug-interaction safety grounded to `systematic_review` → safe green 88%. Change to `model_prior` → red DANGER 40%.  
- Monitoring & follow-up already escalated at 45%. Change to `systematic_review` → clears escalation, becomes amber 45% caution.

All computation is **pure frontend math** — no API calls. The TypeScript capping functions mirror `backend/capping.py` exactly so explore results match what a real re-judge would produce.

---

## 2. New & modified files

| File | Change |
|---|---|
| `frontend/src/constants.ts` | Add `capConfidence()` + `computeEscalation()` pure helper functions |
| `frontend/src/components/TierSelector.tsx` | NEW — dropdown with conditional ↩ reset |
| `frontend/src/components/DimensionRow.tsx` | Accept 3 new explore props; derive display values from explore tier when active |
| `frontend/src/components/ScoreCard.tsx` | Add `exploreMode` + `exploreTiers` state; toggle button; pass explore props to rows |

---

## 3. Pure helper functions — `constants.ts`

Add to the bottom of `frontend/src/constants.ts`:

```ts
// Must mirror backend/capping.py exactly.

export function capConfidence(
  modelConf: number,
  tier: string,
  claimScope: string,
): number {
  const ceiling = EVIDENCE_CEILINGS[tier] ?? 0.40;
  let capped = Math.min(modelConf, ceiling);
  if (claimScope === "individual") capped = Math.min(capped, 0.60);
  return Math.round(capped * 100) / 100;
}

export function computeEscalation(
  safetyCritical: boolean,
  tier: string,
  displayed: number,
): { flag: boolean; reason: string; severity: string } | null {
  if (safetyCritical && tier === "model_prior")
    return { flag: true, reason: "unverified_safety_claim", severity: "danger" };
  if (displayed < LOW_CONFIDENCE_THRESHOLD)
    return { flag: true, reason: "low_confidence", severity: "warning" };
  return null;
}
```

`LOW_CONFIDENCE_THRESHOLD` (0.50) and `EVIDENCE_CEILINGS` are already defined in the same file.

---

## 4. `TierSelector.tsx`

**Props:**
```ts
interface Props {
  currentTier: string;   // the tier currently shown (may differ from originalTier in explore)
  originalTier: string;  // the tier the backend actually grounded to
  onSelect: (tier: string) => void;
  onReset: () => void;
}
```

**Behaviour:**
- Renders a `<select>` with all 6 tiers as `<option>` elements.
- Option labels: `"T1 — Systematic review / meta-analysis"` etc, using `TIER_ORDER` and `TIER_META`.
- `value` = `currentTier`.
- When `currentTier === originalTier`: neutral styling (`border-gray-300`), no ↩ button.
- When `currentTier !== originalTier`: select styled `border-red-300 bg-red-50 text-red-800`, followed by a small `↩` button (`text-gray-400 hover:text-indigo-500`) that calls `onReset`.

---

## 5. `DimensionRow.tsx` — new props and derived display

**Three new props added (all optional to avoid breaking ScoreCard before it passes them):**
```ts
exploreMode?: boolean;
exploreTier?: string | null;
onTierChange?: (tier: string | null) => void;
```

**When `exploreMode` is falsy:** component renders exactly as today — no selectors, uses `verdict.displayed_confidence`, `verdict.escalation`, `verdict.grounded_tier`.

**When `exploreMode` is true:**

Derive display values at the top of the component:
```ts
const displayedTier = exploreTier ?? verdict.grounded_tier;
const displayedCap  = capConfidence(verdict.model_confidence, displayedTier, verdict.claim_scope);
const displayedEsc  = computeEscalation(verdict.safety_critical, displayedTier, displayedCap);
```

Then use:
- `displayedTier` for the tier code chip and `TierSelector`'s `currentTier`
- `displayedCap` for the `%` label and the bar's solid-layer width
- `displayedEsc` for the escalation pill (the row colour `band()` function takes the escalation result)
- Ceiling tick: `EVIDENCE_CEILINGS[displayedTier]`
- Faded bar (model confidence) is unchanged — it's always `verdict.model_confidence`

**Insertion point:** `<TierSelector>` is rendered as a new row between the top-line badges and the confidence bar, only when `exploreMode` is true:
```tsx
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
```

**`band()` must be refactored** to accept `(escalation, displayedConf)` instead of the full `Verdict`, so explore mode can pass computed values:

```ts
// before (reads from verdict directly)
function band(verdict: Verdict): Band { … }

// after (takes the two fields it actually needs)
function band(
  escalation: { severity: string } | null,
  displayedConf: number,
): Band {
  if (escalation?.severity === "danger")  return "escalated-danger";
  if (escalation?.severity === "warning") return "escalated-warning";
  if (displayedConf >= 0.75)             return "trustworthy";
  return "caution";
}
```

The existing call site in `DimensionRow` (before explore props exist) becomes:
```ts
const b = band(verdict.escalation, verdict.displayed_confidence);
```
In explore mode, it becomes:
```ts
const b = band(displayedEsc, displayedCap);
```
This is the only change to `band()`'s call site — both paths are in the same component.

---

## 6. `ScoreCard.tsx` — state + toggle + prop threading

**New state:**
```ts
const [exploreMode, setExploreMode] = useState(false);
const [exploreTiers, setExploreTiers] = useState<Record<string, string>>({});
```

**Toggle handler:**
```ts
function toggleExploreMode() {
  setExploreMode((prev) => {
    if (prev) setExploreTiers({});   // reset all on exit
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
```

**Toggle button** — inserted in the case header between the patient question and the summary pills:
```tsx
<button
  onClick={toggleExploreMode}
  className={[
    "text-xs font-semibold px-3 py-1 rounded-full border transition-colors",
    exploreMode
      ? "bg-indigo-600 border-indigo-600 text-white"
      : "bg-white border-gray-300 text-gray-500 hover:border-indigo-300 hover:text-indigo-500",
  ].join(" ")}
>
  {exploreMode ? "⬡ Explore ON" : "⬡ Explore"}
</button>
```

**Prop threading** in `rows.map(...)`:
```tsx
<DimensionRow
  key={verdict.verdict_id}
  verdict={verdict}
  dimension={dimension}
  exploreMode={exploreMode}
  exploreTier={exploreTiers[verdict.verdict_id] ?? null}
  onTierChange={(tier) => handleTierChange(verdict.verdict_id, tier)}
/>
```

**Reset on case switch:** `exploreMode` and `exploreTiers` reset to defaults naturally — they are local to `ScoreCard`, which remounts when the selected case changes (because `selectedCase` prop changes).

---

## 7. Key invariants

- `exploreMode === false` → DimensionRow is byte-for-byte identical in output to Phase 5. No regression.
- `capConfidence` and `computeEscalation` produce results identical to the backend for all valid tier + claimScope combinations.
- Toggling explore OFF resets `exploreTiers` to `{}`, so all rows snap back to real backend values.
- `verdict.displayed_confidence` and `verdict.escalation` (the backend values) are never mutated — only the derived display vars change.

---

## 8. Out of scope

- ProfileRadar (Phase 7)
- Persisting explore selections across page refreshes
- Showing explore results in the Review Queue
