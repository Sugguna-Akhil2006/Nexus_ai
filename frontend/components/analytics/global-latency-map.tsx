"use client";

import { Globe } from "lucide-react";
import { cn } from "@/lib/utils";

export interface LatencyBar {
  id: number;
  heightClass: string;
  colorClass: string; // bg-[#10b981] etc
  opacityClass: string; // opacity-60 etc
}

interface GlobalLatencyMapProps {
  bars: LatencyBar[];
  globalAverage: string;
}

export default function GlobalLatencyMap({
  bars,
  globalAverage,
}: GlobalLatencyMapProps) {
  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl p-5 select-none shadow-sm overflow-hidden flex flex-col justify-between">
      
      {/* Header and Legend Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5 shrink-0">
        <div>
          <h2 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Global Latency Map
          </h2>
          <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
            Regional response times for Nexus Core v4
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 select-none">
          <div className="flex items-center gap-1.5 text-[10px] md:text-xs">
            <span className="w-2 h-2 rounded-full bg-[#10b981] shrink-0" />
            <span className="text-on-surface-variant font-semibold">Fast (&lt;200ms)</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] md:text-xs">
            <span className="w-2 h-2 rounded-full bg-[#f59e0b] shrink-0" />
            <span className="text-on-surface-variant font-semibold">Med (200-500ms)</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] md:text-xs">
            <span className="w-2 h-2 rounded-full bg-[#ef4444] shrink-0" />
            <span className="text-on-surface-variant font-semibold">Slow (&gt;500ms)</span>
          </div>
        </div>
      </div>

      {/* Map Waveform Frame */}
      <div className="w-full h-48 bg-surface-container-low rounded-lg border border-outline-variant/30 flex items-center justify-center relative overflow-hidden group select-none">
        
        {/* Background Pixel Grid Effect */}
        <div className="absolute inset-0 opacity-10 pixel-grid pointer-events-none" />

        {/* Latency Waveform Bars */}
        <div className="flex gap-1 h-32 items-end z-10 pointer-events-none select-none">
          {bars.map((bar) => (
            <div
              key={bar.id}
              className={cn(
                "w-2.5 sm:w-4 rounded-t-sm transition-all duration-300",
                bar.heightClass,
                bar.colorClass,
                bar.opacityClass,
                "group-hover:opacity-100 group-hover:scale-y-105"
              )}
            />
          ))}
        </div>

        {/* Center overlay details HUD */}
        <div className="absolute inset-0 flex items-center justify-center bg-background/20 backdrop-blur-[1px] group-hover:backdrop-blur-0 group-hover:bg-transparent transition-all z-20">
          <div className="bg-surface border border-outline-variant p-4 rounded-xl flex items-center gap-4 shadow-2xl animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0 shadow-inner">
              <Globe className="size-5" />
            </div>
            <div className="select-text">
              <div className="font-mono text-[10px] text-on-surface-variant font-bold uppercase tracking-wider pl-0.5 leading-none">
                Optimal Performance
              </div>
              <div className="text-sm md:text-base font-bold text-on-surface mt-1 leading-none">
                Global Average {globalAverage}
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
