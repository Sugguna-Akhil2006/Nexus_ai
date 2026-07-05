"use client";

import Image from "next/image";

interface StatsBarProps {
  activeCount: string; // e.g. "12 / 20"
  totalOps: string;    // e.g. "142,829"
  teamAvatars: string[];
  plusCount: number;   // e.g. 4
}

export default function StatsBar({
  activeCount,
  totalOps,
  teamAvatars,
  plusCount,
}: StatsBarProps) {
  return (
    <div className="mt-8 p-6 bg-surface-container-low rounded-xl border border-outline-variant flex flex-col md:flex-row items-center justify-between gap-6 select-none shadow-sm">
      {/* Left Metric Group */}
      <div className="flex items-center gap-6">
        <div className="flex flex-col">
          <span className="text-[9px] uppercase tracking-widest text-on-surface-variant font-bold">
            Active Agents
          </span>
          <span className="font-mono text-xl md:text-2xl font-bold text-primary mt-1 leading-none">
            {activeCount}
          </span>
        </div>
        
        <div className="h-8 w-px bg-outline-variant/60" />
        
        <div className="flex flex-col">
          <span className="text-[9px] uppercase tracking-widest text-on-surface-variant font-bold">
            Total Operations
          </span>
          <span className="font-mono text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {totalOps}
          </span>
        </div>
      </div>

      {/* Right Team Pile */}
      <div className="flex -space-x-2.5 overflow-hidden">
        {teamAvatars.map((url, index) => (
          <div 
            key={url} 
            className="relative h-9 w-9 rounded-full overflow-hidden ring-2 ring-surface bg-surface-container-highest"
          >
            <Image
              alt={`Team member ${index + 1}`}
              src={url}
              fill
              className="object-cover"
              sizes="36px"
            />
          </div>
        ))}
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-high text-xs font-semibold text-on-surface-variant ring-2 ring-surface select-none">
          +{plusCount}
        </div>
      </div>
    </div>
  );
}
