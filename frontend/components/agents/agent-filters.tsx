"use client";

import { cn } from "@/lib/utils";

export type FilterValue = "all" | "production" | "drafts";

interface AgentFiltersProps {
  value: FilterValue;
  onChange: (value: FilterValue) => void;
}

export default function AgentFilters({ value, onChange }: AgentFiltersProps) {
  const options: { key: FilterValue; label: string }[] = [
    { key: "all", label: "All Agents" },
    { key: "production", label: "Production" },
    { key: "drafts", label: "Drafts" },
  ];

  return (
    <div className="flex gap-1.5 p-1.5 bg-surface-container-low rounded-xl border border-outline-variant select-none w-fit">
      {options.map((opt) => {
        const isActive = value === opt.key;
        return (
          <button
            key={opt.key}
            onClick={() => onChange(opt.key)}
            className={cn(
              "px-4 py-2 rounded-lg font-semibold text-xs md:text-sm transition-all duration-200 cursor-pointer select-none",
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
