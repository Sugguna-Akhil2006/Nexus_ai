"use client";

import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export interface HealthMetric {
  id: string;
  name: string;
  status: "Active" | "Warning" | "Error";
  metricText: string;
}

interface SystemHealthPanelProps {
  metrics: HealthMetric[];
  onViewLogs: () => void;
}

export default function SystemHealthPanel({
  metrics,
  onViewLogs,
}: SystemHealthPanelProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 shadow-sm flex flex-col justify-between h-full select-none">
      
      {/* Title */}
      <div className="shrink-0 mb-5">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          System Health
        </h3>
      </div>

      {/* Health metrics items list */}
      <div className="space-y-3 flex-grow">
        {metrics.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between p-3 bg-surface-container/60 hover:bg-surface-container/90 rounded-xl border border-outline-variant/20 hover:border-outline-variant/40 transition-all select-text"
          >
            {/* Status dot + Name */}
            <div className="flex items-center gap-3 select-none">
              <span className={cn(
                "w-2.5 h-2.5 rounded-full shrink-0 relative flex items-center justify-center",
                item.status === "Active" && "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]",
                item.status === "Warning" && "bg-amber-500 animate-pulse",
                item.status === "Error" && "bg-rose-500 animate-ping"
              )} />
              <span className="text-xs md:text-sm font-bold text-on-surface">
                {item.name}
              </span>
            </div>

            {/* Metric Value */}
            <span className={cn(
              "font-mono text-xs font-semibold leading-none",
              item.status === "Warning" ? "text-amber-500" : "text-on-surface-variant"
            )}>
              {item.metricText}
            </span>
          </div>
        ))}
      </div>

      {/* Logs trigger button */}
      <div className="mt-5 shrink-0 select-none">
        <button
          onClick={onViewLogs}
          className="w-full py-2 bg-transparent hover:bg-primary/10 text-primary font-bold text-xs md:text-sm rounded-lg transition-colors border border-primary/20 cursor-pointer"
        >
          View Detailed Logs
        </button>
      </div>

    </div>
  );
}
