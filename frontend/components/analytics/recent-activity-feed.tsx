"use client";

import { cn } from "@/lib/utils";

export interface ActivityItem {
  id: string;
  author: string;
  timeAgo: string;
  type: "pr" | "system" | "push";
  description: string;
  tags?: string[];
}

interface RecentActivityFeedProps {
  activities: ActivityItem[];
}

export default function RecentActivityFeed({ activities }: RecentActivityFeedProps) {
  const getCircleStyle = (type: "pr" | "system" | "push") => {
    switch (type) {
      case "pr":
        return "bg-primary ring-primary/20";
      case "system":
        return "bg-tertiary ring-tertiary/20";
      default: // push
        return "bg-outline ring-outline/20";
    }
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm h-full flex flex-col justify-between">
      
      {/* Header */}
      <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider mb-5">
        Recent Activity
      </h3>

      {/* Timeline flow */}
      <div className="relative pl-6 flex flex-col gap-6 before:content-[''] before:absolute before:left-[5px] before:top-2 before:bottom-2 before:w-[1px] before:bg-outline-variant/60 flex-grow justify-center">
        {activities.map((act) => (
          <div key={act.id} className="relative text-xs md:text-sm select-text">
            
            {/* Timeline bullet overlap ring */}
            <div className={cn(
              "absolute -left-[26px] top-1 w-2.5 h-2.5 rounded-full border-2 border-surface ring-2 shrink-0 select-none",
              getCircleStyle(act.type)
            )} />

            {/* Author details */}
            <div className="flex items-center gap-1.5 mb-1 select-none">
              <span className="font-bold text-on-surface text-xs md:text-sm">
                {act.author}
              </span>
              <span className="text-on-surface-variant/80 text-[10px] md:text-xs font-medium">
                &bull; {act.timeAgo}
              </span>
            </div>

            {/* Paragraph details */}
            <p className="text-xs md:text-sm text-on-surface-variant font-normal leading-relaxed">
              {act.description}
            </p>

            {/* Tags row */}
            {act.tags && act.tags.length > 0 && (
              <div className="mt-2.5 flex flex-wrap gap-1.5 select-none">
                {act.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 bg-surface-container-highest rounded text-[10px] font-mono border border-outline-variant text-on-surface-variant"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
