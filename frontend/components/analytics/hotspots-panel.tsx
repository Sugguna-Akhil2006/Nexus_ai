"use client";

import { Flame, AlertTriangle, AlertCircle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface HotspotItem {
  id: string;
  filePath: string;
  metricType: "commits" | "complexity" | "coverage";
  metricDesc: string;
  severity: "error" | "warning" | "info";
}

interface HotspotsPanelProps {
  hotspots: HotspotItem[];
  onHotspotClick: (id: string) => void;
}

export default function HotspotsPanel({
  hotspots,
  onHotspotClick,
}: HotspotsPanelProps) {
  const getIcon = (type: "commits" | "complexity" | "coverage", severity: "error" | "warning" | "info") => {
    switch (type) {
      case "commits":
        return <Flame className="size-4 text-error" />;
      case "complexity":
        return <AlertTriangle className="size-4 text-tertiary" />;
      default: // coverage
        return <AlertCircle className="size-4 text-primary" />;
    }
  };

  const getContainerBg = (severity: "error" | "warning" | "info") => {
    switch (severity) {
      case "error":
        return "bg-error-container/20";
      case "warning":
        return "bg-tertiary-container/20";
      default: // info
        return "bg-primary-container/20";
    }
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm h-full flex flex-col justify-between">
      
      {/* Header */}
      <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider mb-5">
        Hotspots &amp; Volatility
      </h3>

      {/* Hotspots feed */}
      <div className="space-y-3.5">
        {hotspots.map((spot) => (
          <div
            key={spot.id}
            onClick={() => onHotspotClick(spot.id)}
            className="p-4 bg-surface border border-outline-variant rounded-lg flex items-center justify-between hover:border-primary/50 hover:bg-primary/5 active:scale-98 transition-all cursor-pointer group shadow-sm select-none"
          >
            <div className="flex items-center gap-4 min-w-0">
              {/* Icon bounding frame */}
              <div className={cn("p-2 rounded-lg shrink-0 flex items-center justify-center", getContainerBg(spot.severity))}>
                {getIcon(spot.metricType, spot.severity)}
              </div>
              
              <div className="min-w-0">
                <p className="font-mono text-xs md:text-sm font-semibold text-on-surface truncate">
                  {spot.filePath}
                </p>
                <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
                  {spot.metricDesc}
                </p>
              </div>
            </div>
            
            {/* Navigation Chevron */}
            <ChevronRight className="size-4 text-on-surface-variant group-hover:translate-x-0.5 group-hover:text-primary transition-all shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}
