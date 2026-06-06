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
            {TIER_META[tier]?.code}: {TIER_META[tier]?.label}
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
