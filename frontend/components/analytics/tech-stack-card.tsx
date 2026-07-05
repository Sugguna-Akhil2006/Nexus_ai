"use client";

import { cn } from "@/lib/utils";

export interface LanguageItem {
  name: string;
  percentage: number;
  colorClass: string;
}

interface TechStackCardProps {
  languages: LanguageItem[];
  aiInsight: string;
  onUpgradeClick: () => void;
}

export default function TechStackCard({
  languages,
  aiInsight,
  onUpgradeClick,
}: TechStackCardProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm flex flex-col justify-between h-full">
      
      <div>
        {/* Header */}
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider mb-5">
          Tech Stack
        </h3>

        {/* Stack Progress Bar (GitHub style) */}
        <div className="w-full h-2.5 rounded-full overflow-hidden flex mb-5 select-none bg-surface-container-highest">
          {languages.map((lang) => (
            <div
              key={lang.name}
              style={{ width: `${lang.percentage}%` }}
              className={cn("h-full first:rounded-l-full last:rounded-r-full", lang.colorClass)}
              title={`${lang.name}: ${lang.percentage}%`}
            />
          ))}
        </div>

        {/* Language rows listing */}
        <div className="space-y-3.5">
          {languages.map((lang) => (
            <div key={lang.name} className="flex items-center justify-between font-mono text-xs md:text-sm select-text">
              <div className="flex items-center gap-2.5 font-medium">
                <span className={cn("w-2.5 h-2.5 rounded-full shrink-0", lang.colorClass)} />
                <span className="text-on-surface truncate">{lang.name}</span>
              </div>
              <span className="text-on-surface-variant/80 font-semibold shrink-0">
                {lang.percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insight Box */}
      <div className="mt-6 p-4 bg-surface rounded-xl border border-outline-variant border-dashed">
        <p className="text-[10px] uppercase tracking-wider font-bold text-primary mb-1">
          AI Insight
        </p>
        <p className="text-xs md:text-sm text-on-surface leading-relaxed font-normal select-text">
          Repository shows a strong modular structure. Recommended upgrade:{" "}
          <span 
            onClick={onUpgradeClick}
            className="text-primary font-bold hover:underline cursor-pointer select-none"
          >
            TS 5.4 features
          </span>{" "}
          could reduce bundle size by ~8%.
        </p>
      </div>
    </div>
  );
}
