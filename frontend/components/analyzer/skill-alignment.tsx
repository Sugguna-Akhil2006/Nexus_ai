"use client";

import { Brain } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SkillItem {
  name: string;
  percentage: number;
  isPrimary?: boolean;
}

interface SkillAlignmentProps {
  skills: SkillItem[];
}

export default function SkillAlignment({ skills }: SkillAlignmentProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm h-full flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 shrink-0">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Skill Alignment
        </h3>
        <Brain className="size-4 text-primary shrink-0" />
      </div>

      {/* Progress Bars list */}
      <div className="space-y-4 flex-grow flex flex-col justify-center">
        {skills.map((skill) => (
          <div key={skill.name} className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-on-surface">{skill.name}</span>
              <span className={cn(skill.isPrimary ? "text-primary font-bold" : "text-on-surface-variant")}>
                {skill.percentage}%
              </span>
            </div>
            {/* Custom progress rail */}
            <div className="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden select-none">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-1000 ease-out",
                  skill.isPrimary ? "bg-primary" : "bg-outline"
                )}
                style={{ width: `${skill.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
