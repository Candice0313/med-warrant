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
