# Phase 7 — ProfileRadar Design Spec

## Goal

Add a "Profile" tab to the ScoreCard that shows a radar chart of evidence profile across all dimensions — dual series (model confidence vs. capped confidence), coloured dots by trust band. Pure frontend, no backend changes.

## Design decisions

| Question | Decision |
|---|---|
| Placement | Separate "Profile" tab next to "Scorecard" in ScoreCard header |
| Content | Radar chart only — no callout, no table |
| Axes | Dual series: outer dashed = model confidence, inner solid = capped confidence |
| Dot colour | Green / amber / red per trust band (matches existing DimensionRow colours) |
| Tab visibility | Only when `judgeResponse` exists (same gate as Explore button) |
| Tab reset | Resets to "scorecard" when selected case changes |
| Backend changes | None — uses existing `judgeResponse.verdicts` data |
| New dependency | `recharts` (listed in spec tech stack; not yet installed) |

---

## Components

### New: `frontend/src/components/ProfileRadar.tsx`

**Props:**
```ts
interface Props {
  verdicts: Verdict[];
  dimensions: Dimension[];
}
```

**Behaviour:**
- Joins verdicts with dimensions by `verdict.dimension === dimension.id`
- Builds one `RadarChart` data entry per dimension:
  ```ts
  {
    label: dimension.label,
    modelConf: verdict.model_confidence,
    cappedConf: verdict.displayed_confidence,
    escalationSeverity: verdict.escalation?.severity ?? null,  // "danger" | "warning" | null
  }
  ```
- Renders a recharts `RadarChart` (responsive, `width="100%" height={320}`):
  - `<PolarGrid />` — background grid rings
  - `<PolarAngleAxis dataKey="label" />` — axis labels (dimension names)
  - `<PolarRadiusAxis domain={[0, 1]} tick={false} />` — 0–1 scale, no tick labels
  - `<Radar name="Model" dataKey="modelConf" stroke="#4dabf7" fill="#4dabf7" fillOpacity={0.1} strokeDasharray="5 3" />` — outer dashed
  - `<Radar name="Capped" dataKey="cappedConf" stroke="#4263eb" fill="#4263eb" fillOpacity={0.2} dot={<BandDot />} />` — inner solid with coloured dots
  - `<Tooltip formatter={(v) => \`${Math.round(+v * 100)}%\`} />` — hover values
  - `<Legend />` — "Model confidence" / "Capped confidence" labels

**`BandDot` helper** (defined in same file):
- A custom recharts dot component; recharts passes the full data entry as `payload` prop
- Reads `payload.cappedConf` and `payload.escalationSeverity` to determine colour:
  - `#e03131` if `escalationSeverity === "danger"`
  - `#f08c00` if `escalationSeverity === "warning"` or `cappedConf < 0.75`
  - `#2f9e44` otherwise (trustworthy)
- Renders a `<circle>` with `r={5}`, white stroke `strokeWidth={1.5}`

**No state** — pure presentational component.

---

### Modified: `frontend/src/components/ScoreCard.tsx`

**New state:**
```ts
const [activeTab, setActiveTab] = useState<"scorecard" | "profile">("scorecard");
```

**Reset effect** — add `setActiveTab("scorecard")` to the existing explore-mode reset effect (the one that calls `setExploreMode(false)` and `setExploreTiers({})`):
```ts
useEffect(() => {
  setExploreMode(false);
  setExploreTiers({});
  setActiveTab("scorecard");   // ← add this line
}, [selectedCase?.id]);
```

**Tab bar UI** — inserted between the summary pill strip and the Evaluate button row, only when `judgeResponse` exists:
```tsx
{judgeResponse && (
  <div className="flex gap-1 border-b border-gray-100 mt-2 mb-1">
    <button
      onClick={() => setActiveTab("scorecard")}
      className={activeTab === "scorecard" ? "tab-active" : "tab-inactive"}
    >
      Scorecard
    </button>
    <button
      onClick={() => setActiveTab("profile")}
      className={activeTab === "profile" ? "tab-active" : "tab-inactive"}
    >
      ◉ Profile
    </button>
  </div>
)}
```

Tab styling (Tailwind):
- Active: `text-xs font-semibold px-3 py-1.5 border-b-2 border-indigo-500 text-indigo-600`
- Inactive: `text-xs font-semibold px-3 py-1.5 border-b-2 border-transparent text-gray-400 hover:text-gray-600`

**Conditional render** — replace the dimension rows section with:
```tsx
{activeTab === "scorecard" && rows.length > 0 && (
  <div className="flex flex-col gap-3">
    {rows.map(...DimensionRow...)}
  </div>
)}

{activeTab === "profile" && judgeResponse && (
  <div className="rounded-xl border border-gray-200 bg-white shadow-sm p-4">
    <ProfileRadar
      verdicts={judgeResponse.verdicts}
      dimensions={selectedCase.dimensions}
    />
  </div>
)}
```

Loading skeletons only render when `activeTab === "scorecard"`.

---

## Data flow

```
ScoreCard
  judgeResponse.verdicts ──→ ProfileRadar
  selectedCase.dimensions ─→ ProfileRadar
                              └─ joins by dimension id
                              └─ builds RadarChart data
                              └─ renders dual-series RadarChart
```

---

## Dependency

Install recharts:
```bash
cd frontend && npm install recharts
```

recharts ships its own TypeScript types — no `@types/recharts` needed.

---

## What this is NOT

- No aggregate/average score — the chart shows per-dimension values only. The suppressed average (`mixed_average_suppressed`) remains struck-through in the summary strip and is not visualised in the radar.
- No interactivity beyond recharts built-in tooltip on hover.
- No explore mode integration — the Profile tab shows real backend values only. (Explore mode selectors remain on the Scorecard tab.)

---

## File map

| File | Change |
|---|---|
| `frontend/src/components/ProfileRadar.tsx` | CREATE — radar chart component |
| `frontend/src/components/ScoreCard.tsx` | MODIFY — add `activeTab` state, tab bar UI, conditional render |
| `frontend/package.json` | MODIFY — add `recharts` dependency |
