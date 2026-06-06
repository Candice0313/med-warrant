# Phase 7 — ProfileRadar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Profile" tab to the ScoreCard that shows a recharts RadarChart with dual series — outer dashed (model confidence) and inner solid (capped confidence) — with dots coloured by trust band.

**Architecture:** Pure frontend, zero backend changes. `ProfileRadar.tsx` is a stateless presentational component that receives `verdicts` and `dimensions` as props and renders a recharts `RadarChart`. `ScoreCard.tsx` gains a new `activeTab` state and a two-button tab bar (Scorecard / Profile) that conditionally renders either the existing dimension rows or the new radar.

**Tech Stack:** React 18 + TypeScript, recharts v3 (already installed), Tailwind CSS v3.

---

## File map

| File | Change |
|---|---|
| `frontend/src/components/ProfileRadar.tsx` | CREATE — radar chart component |
| `frontend/src/components/ScoreCard.tsx` | MODIFY — add `activeTab` state, tab bar, conditional render |

---

## Task 1: Create `ProfileRadar.tsx`

**Files:**
- Create: `frontend/src/components/ProfileRadar.tsx`

- [ ] **Step 1: Write the complete component**

Create `/Users/candice/Desktop/med-warrant/frontend/src/components/ProfileRadar.tsx` with this exact content:

```tsx
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { Dimension, Verdict } from "../types";

// ── types ───────────────────────────────────────────────────────────────────

interface DataEntry {
  label: string;
  modelConf: number;
  cappedConf: number;
  escalationSeverity: string | null;
}

// recharts clones this element with cx/cy/payload injected at runtime
interface BandDotProps {
  cx?: number;
  cy?: number;
  payload?: DataEntry;
  [key: string]: unknown;
}

// ── BandDot ─────────────────────────────────────────────────────────────────

function BandDot({ cx = 0, cy = 0, payload }: BandDotProps) {
  const sev = payload?.escalationSeverity;
  const conf = payload?.cappedConf ?? 0;
  const color =
    sev === "danger"
      ? "#e03131"
      : sev === "warning" || conf < 0.75
        ? "#f08c00"
        : "#2f9e44";
  return <circle cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={1.5} />;
}

// ── ProfileRadar ─────────────────────────────────────────────────────────────

interface Props {
  verdicts: Verdict[];
  dimensions: Dimension[];
}

export function ProfileRadar({ verdicts, dimensions }: Props) {
  const data: DataEntry[] = dimensions.map((dim) => {
    const verdict = verdicts.find((v) => v.dimension === dim.id);
    return {
      label: dim.label,
      modelConf: verdict?.model_confidence ?? 0,
      cappedConf: verdict?.displayed_confidence ?? 0,
      escalationSeverity: verdict?.escalation?.severity ?? null,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="label" tick={{ fontSize: 11, fill: "#495057" }} />
        <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
        <Radar
          name="Model confidence"
          dataKey="modelConf"
          stroke="#4dabf7"
          fill="#4dabf7"
          fillOpacity={0.1}
          strokeDasharray="5 3"
          dot={false}
        />
        <Radar
          name="Capped confidence"
          dataKey="cappedConf"
          stroke="#4263eb"
          fill="#4263eb"
          fillOpacity={0.2}
          dot={<BandDot />}
        />
        <Tooltip formatter={(v: number) => `${Math.round(v * 100)}%`} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 2: Update `ScoreCard.tsx`

**Files:**
- Modify: `frontend/src/components/ScoreCard.tsx`

Read the file before editing. Make 4 targeted changes:

- [ ] **Step 1: Add `activeTab` state and import**

At the top of the file, add `ProfileRadar` to imports:

```tsx
import { DimensionRow } from "./DimensionRow";
import { ProfileRadar } from "./ProfileRadar";
import type { Case, JudgeResponse, Verdict } from "../types";
```

After the two existing `useState` lines for `exploreMode` and `exploreTiers` (around line 32), add:

```tsx
  const [activeTab, setActiveTab] = useState<"scorecard" | "profile">("scorecard");
```

- [ ] **Step 2: Add tab reset to existing effect**

Find the existing `useEffect` that resets `exploreMode` and `exploreTiers` (around line 46). Add `setActiveTab("scorecard")` to it:

```tsx
  useEffect(() => {
    setExploreMode(false);
    setExploreTiers({});
    setActiveTab("scorecard");
  }, [selectedCase?.id]);
```

- [ ] **Step 3: Add tab bar UI**

Find the summary pill strip section. It starts with `{summary ? (` (around line 128). Directly after the closing `)}` of that entire block (after the `{error && ...}` block, before the closing `</div>` of the context card), add the tab bar. It should appear **after** the Evaluate/Explore button row and before the closing `</div>` of the inner `border-t` div:

Actually — place the tab bar **between the summary pills block and the Evaluate button row**. Find the `<div className="mt-3 flex items-center gap-2 flex-wrap">` that wraps the Evaluate + Explore buttons (around line 159). Insert this immediately before it:

```tsx
        {judgeResponse && (
          <div className="flex gap-0 border-b border-gray-100 mt-3 mb-1">
            <button
              onClick={() => setActiveTab("scorecard")}
              className={[
                "text-xs font-semibold px-3 py-1.5 border-b-2 transition-colors",
                activeTab === "scorecard"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-400 hover:text-gray-600",
              ].join(" ")}
            >
              Scorecard
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className={[
                "text-xs font-semibold px-3 py-1.5 border-b-2 transition-colors",
                activeTab === "profile"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-400 hover:text-gray-600",
              ].join(" ")}
            >
              ◉ Profile
            </button>
          </div>
        )}
```

- [ ] **Step 4: Conditional render — dimension rows vs ProfileRadar**

Find the dimension rows results section (around line 203):

```tsx
      {/* ── dimension rows (results) ── */}
      {rows.length > 0 && (
        <div className="flex flex-col gap-3">
          {rows.map(({ verdict, dimension }) => (
            <DimensionRow
              key={verdict.verdict_id}
              verdict={verdict}
              dimension={dimension}
              exploreMode={exploreMode}
              exploreTier={exploreTiers[verdict.verdict_id] ?? null}
              onTierChange={(tier) => handleTierChange(verdict.verdict_id, tier)}
            />
          ))}
        </div>
      )}
```

Replace with:

```tsx
      {/* ── dimension rows (results) ── */}
      {activeTab === "scorecard" && rows.length > 0 && (
        <div className="flex flex-col gap-3">
          {rows.map(({ verdict, dimension }) => (
            <DimensionRow
              key={verdict.verdict_id}
              verdict={verdict}
              dimension={dimension}
              exploreMode={exploreMode}
              exploreTier={exploreTiers[verdict.verdict_id] ?? null}
              onTierChange={(tier) => handleTierChange(verdict.verdict_id, tier)}
            />
          ))}
        </div>
      )}

      {/* ── profile radar ── */}
      {activeTab === "profile" && judgeResponse && (
        <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4">
          <ProfileRadar
            verdicts={judgeResponse.verdicts}
            dimensions={selectedCase.dimensions}
          />
        </div>
      )}
```

Also update the loading skeletons condition (around line 194) to only show on scorecard tab:

Find:
```tsx
      {/* ── dimension rows (loading skeletons) ── */}
      {loading && rows.length === 0 && (
```

Replace with:
```tsx
      {/* ── dimension rows (loading skeletons) ── */}
      {activeTab === "scorecard" && loading && rows.length === 0 && (
```

- [ ] **Step 5: TypeScript check**

```bash
cd /Users/candice/Desktop/med-warrant/frontend && npx tsc --noEmit 2>&1
```

Expected: zero errors.

---

## Task 3: Browser verification

**Files:** none — verification only.

- [ ] **Step 1: Confirm both servers are running**

```bash
curl -s http://localhost:8000/api/cases | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'cases')"
curl -s http://localhost:5173 | head -1
```

Expected: `4 cases` and `<!doctype html>`.

- [ ] **Step 2: Playwright smoke test**

```bash
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
import os

SHOTS = "/tmp/phase7_verify"
os.makedirs(SHOTS, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://localhost:5173", wait_until="networkidle")

    # Select warfarin case and judge
    page.locator("nav button").first.click()
    page.wait_for_timeout(500)
    page.locator("button", has_text="Evaluate").click()
    page.wait_for_selector("text=LOW CONFIDENCE", timeout=12000)
    page.screenshot(path=f"{SHOTS}/01_scorecard_tab.png")
    print("✅ Scorecard tab populated")

    # Profile tab must not be visible before judging (we already judged, check it's there)
    profile_tab = page.locator("button", has_text="Profile")
    print(f"✅ Profile tab visible: {profile_tab.is_visible()}")

    # Click Profile tab
    profile_tab.click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SHOTS}/02_profile_tab.png")
    print("✅ Profile tab clicked")

    # Radar chart must be rendered (recharts renders SVG)
    svg_count = page.locator("svg.recharts-surface").count()
    print(f"✅ Recharts SVG rendered: {svg_count > 0} (count={svg_count})")

    # Dimension rows must NOT be visible on profile tab
    dim_rows_visible = page.locator("text=Drug-interaction safety").is_visible()
    print(f"✅ Dimension rows hidden on profile tab: {not dim_rows_visible}")

    # Switch back to Scorecard tab
    page.locator("button", has_text="Scorecard").click()
    page.wait_for_timeout(300)
    page.screenshot(path=f"{SHOTS}/03_back_to_scorecard.png")
    dim_rows_back = page.locator("text=Drug-interaction safety").is_visible()
    print(f"✅ Dimension rows visible on scorecard tab: {dim_rows_back}")

    # Switch to a different case — Profile tab should disappear (no judgeResponse)
    page.locator("nav button").nth(1).click()
    page.wait_for_timeout(400)
    profile_after_switch = page.locator("button", has_text="Profile").is_visible()
    print(f"✅ Profile tab hidden after case switch: {not profile_after_switch}")
    page.screenshot(path=f"{SHOTS}/04_new_case_no_profile_tab.png")

    browser.close()
    print(f"\n📸 Screenshots: {SHOTS}/")
EOF
```

Expected output:
```
✅ Scorecard tab populated
✅ Profile tab visible: True
✅ Profile tab clicked
✅ Recharts SVG rendered: True (count=1)
✅ Dimension rows hidden on profile tab: True
✅ Dimension rows visible on scorecard tab: True
✅ Profile tab hidden after case switch: True
```

- [ ] **Step 3: Read screenshot `02_profile_tab.png`**

Read the image at `/tmp/phase7_verify/02_profile_tab.png`. Confirm visually: radar chart is rendered with at least 2 overlapping polygon shapes (the dual series), axis labels show dimension names, dots are visible and coloured.
