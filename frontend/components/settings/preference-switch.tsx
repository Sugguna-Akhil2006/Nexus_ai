"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface PreferenceSwitchProps {
  title: string;
  description: string;
  icon: LucideIcon;
  enabled: boolean;
  onChange: (val: boolean) => void;
}

export default function PreferenceSwitch({
  title,
  description,
  icon: Icon,
  enabled,
  onChange,
}: PreferenceSwitchProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-2xl p-5 space-y-4 shadow-sm select-none h-full flex flex-col justify-between hover:border-primary/20 transition-colors">
      
      {/* Header block */}
      <div className="flex items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <Icon className="size-5 text-primary shrink-0" />
          <h4 className="text-xs md:text-sm font-bold text-on-surface truncate">
            {title}
          </h4>
        </div>

        {/* Custom switch slider */}
        <div
          onClick={() => onChange(!enabled)}
          className={cn(
            "w-10 h-5 rounded-full relative cursor-pointer flex items-center px-1 transition-all duration-200 select-none border border-outline-variant/30 shrink-0",
            enabled ? "bg-primary" : "bg-surface-container-highest"
          )}
        >
          <div
            className={cn(
              "w-3.5 h-3.5 rounded-full shadow-sm transition-all duration-200",
              enabled ? "bg-white ml-auto" : "bg-outline mr-auto"
            )}
          />
        </div>
      </div>

      {/* Description */}
      <p className="text-[10px] md:text-xs text-on-surface-variant/80 leading-relaxed font-medium">
        {description}
      </p>
    </div>
  );
}
