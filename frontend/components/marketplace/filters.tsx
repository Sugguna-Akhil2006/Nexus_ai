"use client";

import { cn } from "@/lib/utils";

export type TimeframeValue = "week" | "all";

interface FiltersProps {
  value: TimeframeValue;
  onChange: (value: TimeframeValue) => void;
}

export default function Filters({ value, onChange }: FiltersProps) {
  const options: { key: TimeframeValue; label: string }[] = [
    { key: "week", label: "This Week" },
    { key: "all", label: "All Time" },
  ];

  return (
    <div className="flex bg-surface-container-highest p-1 rounded-lg border border-outline-variant/60 w-fit select-none shrink-0">
      {options.map((opt) => {
        const isActive = value === opt.key;
        return (
          <button
            key={opt.key}
            onClick={() => onChange(opt.key)}
            className={cn(
              "px-3 py-1 text-xs md:text-sm font-semibold rounded-md transition-all duration-200 cursor-pointer select-none",
              isActive
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-on-surface-variant hover:text-on-surface"
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
