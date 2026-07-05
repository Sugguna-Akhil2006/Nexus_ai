"use client";

import { Shield, UserPlus, AlertTriangle, Cloud, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface AuditLogItem {
  id: string;
  title: string;
  description: string; // e.g. "Admin changed auth protocols for Vortex Systems."
  timestampText: string; // 12:44 PM • J. Miller
  iconType: "security" | "user" | "warning" | "cloud";
}

interface AuditLogProps {
  logs: AuditLogItem[];
  onViewAllLogs: () => void;
}

const ICON_MAP: Record<AuditLogItem["iconType"], { icon: LucideIcon; bgClass: string; borderClass: string; iconColorClass: string }> = {
  security: {
    icon: Shield,
    bgClass: "bg-primary/20",
    borderClass: "border-primary/40",
    iconColorClass: "text-primary",
  },
  user: {
    icon: UserPlus,
    bgClass: "bg-secondary-container/20",
    borderClass: "border-secondary/40",
    iconColorClass: "text-secondary",
  },
  warning: {
    icon: AlertTriangle,
    bgClass: "bg-red-500/20",
    borderClass: "border-red-500/40",
    iconColorClass: "text-red-400",
  },
  cloud: {
    icon: Cloud,
    bgClass: "bg-primary/20",
    borderClass: "border-primary/40",
    iconColorClass: "text-primary",
  },
};

export default function AuditLog({
  logs,
  onViewAllLogs,
}: AuditLogProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 flex flex-col justify-between h-full shadow-sm select-none">
      
      {/* Title Header */}
      <div className="p-1 border-b border-outline-variant/30 flex justify-between items-center shrink-0 mb-4 pb-2.5">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Audit Log
        </h3>
        <button
          onClick={onViewAllLogs}
          className="text-xs text-primary hover:underline bg-transparent border-none cursor-pointer p-0 font-bold"
        >
          View All
        </button>
      </div>

      {/* Timeline items list */}
      <div className="flex-grow space-y-6 select-text overflow-y-auto pr-1 max-h-[440px] custom-scrollbar">
        {logs.map((item, idx) => {
          const cfg = ICON_MAP[item.iconType];
          const Icon = cfg.icon;
          const isLast = idx === logs.length - 1;

          return (
            <div key={item.id} className="flex gap-4 relative">
              
              {/* Vertical connector line */}
              {!isLast && (
                <div className="absolute left-[11px] top-6 bottom-0 w-[1px] bg-outline-variant/30 pointer-events-none select-none" />
              )}
              
              {/* Icon Shield/User/Warning container */}
              <div className={cn(
                "w-6 h-6 rounded-full border flex items-center justify-center z-10 shrink-0 select-none shadow-sm",
                cfg.bgClass,
                cfg.borderClass
              )}>
                <Icon className={cn("size-3.5", cfg.iconColorClass)} />
              </div>

              {/* Text details */}
              <div className="min-w-0">
                <p className="text-xs md:text-sm font-bold text-on-surface leading-tight">
                  {item.title}
                </p>
                <p className="text-xs text-on-surface-variant font-medium mt-1 leading-relaxed">
                  {item.description}
                </p>
                <p className="text-[10px] md:text-xs text-on-surface-variant/50 font-mono font-semibold mt-1 select-none">
                  {item.timestampText}
                </p>
              </div>

            </div>
          );
        })}
      </div>

    </div>
  );
}
