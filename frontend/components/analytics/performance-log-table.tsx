"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface LogItem {
  id: string;
  statusCode: string; // 200 OK or 429 RATE
  statusType: "success" | "warning" | "error";
  clusterPath: string; // nexus-v4-prod / completion
  tokensText: string; // 4.2k tokens
  latencyText: string; // 142ms
  timeAgo: string; // 2m ago
}

interface PerformanceLogTableProps {
  logs: LogItem[];
  onViewAllClick: () => void;
}

export default function PerformanceLogTable({
  logs,
  onViewAllClick,
}: PerformanceLogTableProps) {
  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden shadow-sm select-none">
      
      {/* Table Header */}
      <div className="p-5 border-b border-outline-variant flex justify-between items-center bg-surface-container-high/40 shrink-0">
        <h2 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Real-time Performance Log
        </h2>
        <button
          onClick={onViewAllClick}
          className="text-primary font-bold text-xs md:text-sm flex items-center gap-1 hover:underline cursor-pointer bg-transparent border-none p-0"
        >
          View all logs
          <ArrowRight className="size-3.5" />
        </button>
      </div>

      {/* Logs rows */}
      <div className="divide-y divide-outline-variant/30 select-text">
        {logs.map((log) => (
          <div
            key={log.id}
            className="p-4 grid grid-cols-5 sm:grid-cols-6 items-center gap-4 hover:bg-surface-container-high/40 transition-colors text-xs md:text-sm"
          >
            {/* Status */}
            <div className="col-span-1 flex items-center gap-2 select-none">
              <span className={cn(
                "w-2 h-2 rounded-full shrink-0",
                log.statusType === "success" && "bg-emerald-500",
                log.statusType === "warning" && "bg-amber-500",
                log.statusType === "error" && "bg-rose-500"
              )} />
              <span className="font-mono font-bold text-on-surface">
                {log.statusCode}
              </span>
            </div>

            {/* Path */}
            <div className="col-span-2 font-medium text-on-surface-variant truncate">
              {log.clusterPath}
            </div>

            {/* Tokens */}
            <div className="col-span-1 font-mono font-bold text-on-surface-variant text-right hidden sm:block">
              {log.tokensText}
            </div>

            {/* Latency */}
            <div className="col-span-1 font-mono font-semibold text-on-surface-variant text-right">
              {log.latencyText}
            </div>

            {/* Timestamp */}
            <div className="col-span-1 flex justify-end select-none">
              <span className="font-semibold text-on-surface-variant/50 text-[10px] md:text-xs">
                {log.timeAgo}
              </span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
