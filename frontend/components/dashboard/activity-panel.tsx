"use client";

import { 
  MoreHorizontal, 
  RefreshCw, 
  ShieldCheck, 
  Terminal, 
  AlertTriangle 
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ActivityItem {
  id: string;
  title: string;
  subtitle: string;
  time: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBgClass: string;
  iconColorClass: string;
}

const ACTIVITIES: ActivityItem[] = [
  {
    id: "act-1",
    title: "Dataset synchronized",
    subtitle: "Shard-11 (Quantum-Link) verified",
    time: "Just now",
    icon: RefreshCw,
    iconBgClass: "bg-primary/10",
    iconColorClass: "text-primary",
  },
  {
    id: "act-2",
    title: "Security audit completed",
    subtitle: "All 14 endpoints secure",
    time: "12m ago",
    icon: ShieldCheck,
    iconBgClass: "bg-green-500/10 border border-green-500/20",
    iconColorClass: "text-green-400",
  },
  {
    id: "act-3",
    title: "Deployment successful",
    subtitle: "Core-Sync 2.0 v1.4.2 production",
    time: "45m ago",
    icon: Terminal,
    iconBgClass: "bg-secondary/15",
    iconColorClass: "text-primary",
  },
  {
    id: "act-4",
    title: "High latency detected",
    subtitle: "Node US-West-2 spike (+230ms)",
    time: "1h ago",
    icon: AlertTriangle,
    iconBgClass: "bg-destructive/15 border border-destructive/20",
    iconColorClass: "text-destructive",
  },
];

export default function ActivityPanel() {
  return (
    <div className="col-span-12 lg:col-span-4 bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col gap-4 group hover:border-outline-variant/80 transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-xl font-semibold text-on-surface tracking-tight">
          Live Activity
        </h3>
        <Button variant="ghost" size="icon" className="text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/60 cursor-pointer">
          <MoreHorizontal className="size-5" />
          <span className="sr-only">More options</span>
        </Button>
      </div>

      {/* Activity List */}
      <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1 scrollbar-thin">
        {ACTIVITIES.map((activity) => (
          <div
            key={activity.id}
            className="flex gap-4 p-3 rounded-lg bg-transparent hover:bg-surface-container-high/30 border border-transparent hover:border-outline-variant transition-all duration-200"
          >
            {/* Action Icon */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${activity.iconBgClass} ${activity.iconColorClass}`}>
              <activity.icon className="size-5" />
            </div>
            
            {/* Description */}
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-on-surface leading-tight">
                {activity.title}
              </span>
              <span className="text-xs text-on-surface-variant leading-relaxed">
                {activity.subtitle}
              </span>
              <span className="text-[10px] uppercase font-mono tracking-wider text-on-surface-variant mt-1.5 select-none">
                {activity.time}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Log Action */}
      <Button
        variant="ghost"
        className="w-full py-2 text-sm text-primary font-bold hover:bg-primary/5 rounded-lg transition-colors mt-2 cursor-pointer border-none"
      >
        View System Logs
      </Button>
    </div>
  );
}
