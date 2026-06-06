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
        <Tooltip formatter={(v) => typeof v === "number" ? `${Math.round(v * 100)}%` : v} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
}
