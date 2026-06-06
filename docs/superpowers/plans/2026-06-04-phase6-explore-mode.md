# Phase 6 — Explore Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global "Explore mode" toggle to the ScoreCard that reveals a per-row tier dropdown; changing the tier live-recomputes the capped confidence and escalation pill with no API calls.

**Architecture:** Pure frontend computation — `capConfidence()` and `computeEscalation()` are added to `constants.ts` as exact TypeScript mirrors of `backend/capping.py`. ScoreCard owns `exploreMode` + `exploreTiers` state; DimensionRow derives all display values from the active tier. When `exploreMode` is false the component is byte-for-byte identical to Phase 5.

**Tech Stack:** React 18 + TypeScript, Tailwind CSS v3. Zero new API calls.

---

## File map

| File | Change |
|---|---|
| `frontend/src/constants.ts` | Add `TIER_ORDER`, `capConfidence()`, `computeEscalation()` |
| `frontend/src/components/TierSelector.tsx` | NEW — tier `<select>` + ↩ reset |
| `frontend/src/components/DimensionRow.tsx` | Refactor `band()`, add 3 explore props, insert `<TierSelector>` |
| `frontend/src/components/ScoreCard.tsx` | Add explore state + toggle button + prop threading |

---

## Task 1: Add helpers to `constants.ts`

**Files:**
- Modify: `frontend/src/constants.ts`

- [ ] **Step 1: Append `TIER_ORDER` and the two pure helper functions**

The current file ends at line 21 (`export const TRUSTWORTHY_THRESHOLD = 0.75;`). Append after that line:

```ts
// Tiers ordered strongest → weakest by ceiling — used by TierSelector dropdown.
export const TIER_ORDER: string[] = [
  "systematic_review",
  "rct",
  "guideline",
  "cohort",
  "expert",
  "model_prior",
];

// ── Pure capping helpers (mirrors backend/capping.py exactly) ────────────────

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

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 2: Create `TierSelector.tsx`

**Files:**
- Create: `frontend/src/components/TierSelector.tsx`

- [ ] **Step 1: Write the component**

```tsx
import { TIER_META, TIER_ORDER } from "../constants";

interface Props {
  currentTier: string;   // tier currently shown (may differ in explore mode)
  originalTier: string;  // tier the backend actually grounded to
  onSelect: (tier: string) => void;
  onReset: () => void;
}

export function TierSelector({ currentTier, originalTier, onSelect, onReset }: Props) {
  const changed = currentTier !== originalTier;

  return (
    <div className="flex items-center gap-1.5">
      <select
        value={currentTier}
        onChange={(e) => onSelect(e.target.value)}
        className={[
          "text-[10px] border rounded px-1.5 py-0.5 transition-colors cursor-pointer",
          changed
            ? "border-red-300 bg-red-50 text-red-800 font-semibold"
            : "border-gray-200 bg-white text-gray-600 hover:border-gray-300",
        ].join(" ")}
      >
        {TIER_ORDER.map((tier) => (
          <option key={tier} value={tier}>
            {TIER_META[tier]?.code} — {TIER_META[tier]?.label}
          </option>
        ))}
      </select>
      {changed && (
        <button
          onClick={onReset}
          title="Reset to actual grounded tier"
          className="text-gray-400 hover:text-indigo-500 transition-colors text-xs leading-none"
        >
          ↩
        </button>
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

## Task 3: Update `DimensionRow.tsx`

**Files:**
- Modify: `frontend/src/components/DimensionRow.tsx`

Replace the **entire file** with the version below. Changes from Phase 5:
1. `band()` refactored to accept `(escalation, displayedConf)` instead of `verdict`
2. Three new optional props: `exploreMode`, `exploreTier`, `onTierChange`
3. Display values derived from explore tier when `exploreMode` is true
4. `<TierSelector>` inserted between top line and bar when `exploreMode` is true
5. All bar widths, tier chip, percentage, and escalation pill use the derived values

- [ ] **Step 1: Replace `DimensionRow.tsx`**

```tsx
import { EVIDENCE_CEILINGS, TIER_META, capConfidence, computeEscalation } from "../constants";
import { EvidenceSnippets } from "./EvidenceSnippets";
import { TierSelector } from "./TierSelector";
import type { Dimension, Verdict } from "../types";

// ── colour helpers ──────────────────────────────────────────────────────────

type Band = "trustworthy" | "caution" | "escalated-danger" | "escalated-warning";

function band(
  escalation: { severity: string } | null,
  displayedConf: number,
): Band {
  if (escalation?.severity === "danger")  return "escalated-danger";
  if (escalation?.severity === "warning") return "escalated-warning";
  if (displayedConf >= 0.75)             return "trustworthy";
  return "caution";
}

const BORDER: Record<Band, string> = {
  trustworthy:         "border-l-green-500 bg-green-50",
  caution:             "border-l-amber-400 bg-amber-50",
  "escalated-danger":  "border-l-red-500 bg-red-50",
  "escalated-warning": "border-l-amber-500 bg-amber-50",
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
  exploreMode?: boolean;
  exploreTier?: string | null;
  onTierChange?: (tier: string | null) => void;
}

export function DimensionRow({
  verdict,
  dimension,
  exploreMode,
  exploreTier,
  onTierChange,
}: Props) {
  // In explore mode, derive display values from the chosen tier.
  // When exploreMode is false (or exploreTier is null), use backend values unchanged.
  const displayedTier = (exploreMode && exploreTier) ? exploreTier : verdict.grounded_tier;
  const displayedCap  = exploreMode
    ? capConfidence(verdict.model_confidence, displayedTier, verdict.claim_scope)
    : verdict.displayed_confidence;
  const displayedEsc  = exploreMode
    ? computeEscalation(verdict.safety_critical, displayedTier, displayedCap)
    : verdict.escalation;

  const b = band(displayedEsc, displayedCap);
  const barColour = BAR_HEX[b];
  const ceiling = EVIDENCE_CEILINGS[displayedTier] ?? 0.4;
  const tierCode = TIER_META[displayedTier]?.code ?? "??";

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

        {displayedEsc && (
          <span
            className={[
              "text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0",
              displayedEsc.severity === "danger"
                ? "bg-red-600 text-white"
                : "bg-amber-500 text-white",
            ].join(" ")}
          >
            {displayedEsc.reason === "unverified_safety_claim"
              ? "⚠ UNVERIFIED SAFETY"
              : "↓ LOW CONFIDENCE"}
          </span>
        )}

        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 shrink-0 font-mono">
          {tierCode}
        </span>

        <span className={`text-sm font-bold shrink-0 ${PCT_CLASS[b]}`}>
          {Math.round(displayedCap * 100)}%
        </span>
      </div>

      {/* ── explore tier selector (only in explore mode) ── */}
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

      {/* ── dual confidence bar ── */}
      <div className="px-3 pb-2.5">
        <div
          className="relative h-2.5 rounded-full bg-gray-200"
          title={`Model: ${Math.round(verdict.model_confidence * 100)}%  Capped: ${Math.round(displayedCap * 100)}%  Ceiling: ${Math.round(ceiling * 100)}%`}
        >
          {/* faded: model confidence — always real, never changes in explore */}
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
              width: `${displayedCap * 100}%`,
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

      <EvidenceSnippets grounding={verdict.grounding} />
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

## Task 4: Update `ScoreCard.tsx` — explore state + toggle + prop threading

**Files:**
- Modify: `frontend/src/components/ScoreCard.tsx`

Four targeted changes to the existing file. Read the current file before editing.

- [ ] **Step 1: Add explore state and reset effect**

After the existing state declarations (line ~30, after `answerRef`), add:

```tsx
  const [exploreMode, setExploreMode] = useState(false);
  const [exploreTiers, setExploreTiers] = useState<Record<string, string>>({});
```

After the existing `useEffect` for answer overflow (ends around line 42), add a new effect that resets explore state when the selected case changes:

```tsx
  useEffect(() => {
    setExploreMode(false);
    setExploreTiers({});
  }, [selectedCase?.id]);
```

- [ ] **Step 2: Add handler functions**

After the `useEffect` blocks and before the early `if (!selectedCase)` return, add:

```tsx
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
```

- [ ] **Step 3: Add Explore toggle button in the case header**

Find the existing `<button onClick={onEvaluate} ...>` button (around line 136). Wrap it and add the Explore button so both appear on the same row:

Replace:
```tsx
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
```

With:
```tsx
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
              {exploreMode ? "⬡ Explore ON" : "⬡ Explore"}
            </button>
          )}
        </div>
```

- [ ] **Step 4: Thread explore props into DimensionRow**

Find the existing `<DimensionRow ... />` in `rows.map()` (near the bottom of the file). It currently reads:

```tsx
            <DimensionRow
              key={verdict.verdict_id}
              verdict={verdict}
              dimension={dimension}
            />
```

Replace with:

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

- [ ] **Step 5: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 5: Browser verification

**Files:** none — verification only.

- [ ] **Step 1: Confirm both servers are running**

```bash
curl -s http://localhost:8000/api/cases | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'cases')"
curl -s http://localhost:5173 | head -2
```

Expected: `4 cases` and `<!doctype html>`.

- [ ] **Step 2: Playwright smoke test — the three demo transitions**

```bash
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
import os

SHOTS = "/tmp/phase6_verify"
os.makedirs(SHOTS, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:5173", wait_until="networkidle")

    # Setup: judge the warfarin case
    page.locator("nav button").first.click()
    page.wait_for_timeout(500)
    page.locator("button", has_text="Evaluate").click()
    page.wait_for_selector("text=LOW CONFIDENCE", timeout=12000)
    page.screenshot(path=f"{SHOTS}/01_before_explore.png")
    print("Phase 5 state confirmed")

    # 1. Explore button appears after judge
    explore_btn = page.locator("button", has_text="Explore")
    print(f"Explore button visible: {explore_btn.is_visible()}")

    # 2. Click Explore ON
    explore_btn.click()
    page.wait_for_timeout(300)
    page.screenshot(path=f"{SHOTS}/02_explore_on.png")
    explore_on = page.locator("button", has_text="Explore ON").is_visible()
    print(f"Explore ON label shows: {explore_on}")

    # TierSelector dropdowns should appear
    selects = page.locator("select").all()
    print(f"Tier selects visible: {len(selects)}")

    # 3. Key demo: change Drug-interaction safety to model_prior → must flip red+DANGER
    # Drug-interaction safety is the 3rd row (after sorting: escalated first, then trustworthy)
    # Find the row containing "Drug-interaction safety" and change its select
    drug_row = page.locator("text=Drug-interaction safety").locator("..")
    drug_select = page.locator("select").nth(2)  # third dropdown (rows sorted: monitoring, dosing, drug-interaction, completeness)
    # Change to model_prior
    drug_select.select_option("model_prior")
    page.wait_for_timeout(400)
    page.screenshot(path=f"{SHOTS}/03_drug_flipped_to_model_prior.png")

    # Check for DANGER pill
    danger_count = page.locator("text=UNVERIFIED SAFETY").count()
    print(f"DANGER pills after flipping to model_prior: {danger_count}")

    # Check the ↩ reset button appears
    reset_btn = page.locator("button", has_text="↩").first
    print(f"Reset ↩ button visible: {reset_btn.is_visible()}")

    # 4. Click ↩ to reset — row snaps back to original tier
    reset_btn.click()
    page.wait_for_timeout(300)
    page.screenshot(path=f"{SHOTS}/04_reset_to_original.png")
    danger_after_reset = page.locator("text=UNVERIFIED SAFETY").count()
    print(f"DANGER pills after reset: {danger_after_reset}")

    # 5. Toggle Explore OFF — all selects disappear, all rows restore real data
    page.locator("button", has_text="Explore ON").click()
    page.wait_for_timeout(300)
    page.screenshot(path=f"{SHOTS}/05_explore_off.png")
    selects_after = page.locator("select").count()
    print(f"Selects after Explore OFF: {selects_after}  (expected: 0)")

    browser.close()
    print(f"\nScreenshots: {SHOTS}/")
EOF
```

Expected output:
```
Phase 5 state confirmed
Explore button visible: True
Explore ON label shows: True
Tier selects visible: 4
DANGER pills after flipping to model_prior: >= 1
Reset ↩ button visible: True
DANGER pills after reset: 0
Selects after Explore OFF: 0
```

- [ ] **Step 3: Read screenshot `03_drug_flipped_to_model_prior.png`**

Confirm visually: the drug-interaction safety row is now red with "⚠ UNVERIFIED SAFETY" pill and shows 40% — the demo's "aha" moment.
