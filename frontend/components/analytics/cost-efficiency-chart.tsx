"use client";

import { cn } from "@/lib/utils";

interface CostEfficiencyChartProps {
  percentage: number; // 75
  allocated: number; // 20000
  remaining: number; // 5797
}

export default function CostEfficiencyChart({
  percentage,
  allocated,
  remaining,
}: CostEfficiencyChartProps) {
  // SVG circular properties
  const radius = 88;
  const strokeWidth = 12;
  const circumference = 2 * Math.PI * radius; // ~552.92
  const strokeDashoffset = circumference - (circumference * percentage) / 100;

  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl p-5 select-none flex flex-col justify-between overflow-hidden shadow-sm h-full">
      
      {/* Header */}
      <div className="shrink-0">
        <h2 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Cost Efficiency
        </h2>
        <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
          Budget vs. Actual
        </p>
      </div>

      {/* SVG Ring Dial */}
      <div className="relative w-44 h-44 md:w-48 md:h-48 mx-auto my-6 shrink-0 flex items-center justify-center select-none">
        <svg className="w-full h-full transform -rotate-90">
          {/* Background circle */}
          <circle
            className="text-outline-variant/40"
            cx="96"
            cy="96"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
          />
          {/* Foreground progress circle */}
          <circle
            className="text-primary transition-all duration-1000 ease-out"
            cx="96"
            cy="96"
            fill="transparent"
            r={radius}
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Text label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none">
          <span className="text-xl md:text-2xl font-bold text-on-surface leading-none">
            {percentage}%
          </span>
          <span className="text-[9px] md:text-[10px] text-on-surface-variant/80 uppercase font-bold tracking-widest mt-1">
            Utilized
          </span>
        </div>
      </div>

      {/* Budget Summary Rows */}
      <div className="space-y-2 border-t border-outline-variant/30 pt-4 shrink-0 text-xs md:text-sm select-text">
        <div className="flex justify-between font-medium">
          <span className="text-on-surface-variant/80">Allocated Monthly</span>
          <span className="text-on-surface font-semibold">
            ${allocated.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex justify-between font-medium">
          <span className="text-on-surface-variant/80">Remaining</span>
          <span className="text-primary font-bold">
            ${remaining.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

    </div>
  );
}
