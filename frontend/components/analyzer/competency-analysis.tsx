"use client";

import { ShieldCheck, AlertTriangle, Lightbulb } from "lucide-react";

interface CompetencyAnalysisProps {
  strengths: string[];
  gaps: string[];
  insights: string;
}

export default function CompetencyAnalysis({
  strengths,
  gaps,
  insights,
}: CompetencyAnalysisProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden shadow-sm h-full flex flex-col select-none">
      {/* Header Panel */}
      <div className="p-4 border-b border-outline-variant bg-surface-container-highest/20 flex items-center justify-between shrink-0">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Competency Analysis
        </h3>
        <div className="flex gap-2 text-[8px] uppercase tracking-wider font-bold">
          <span className="bg-surface-container-highest text-on-surface-variant px-1.5 py-0.5 rounded border border-outline-variant/30">
            Neural Scan
          </span>
          <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded border border-primary/20">
            V.4.2
          </span>
        </div>
      </div>

      {/* Lists sections */}
      <div className="p-5 flex-grow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Strengths */}
          <div className="space-y-3">
            <h5 className="text-[10px] font-bold text-on-surface-variant flex items-center gap-1.5 uppercase tracking-widest pl-0.5 shrink-0">
              <ShieldCheck className="size-3.5 text-primary shrink-0" />
              Strengths
            </h5>
            <ul className="text-xs md:text-sm text-on-surface space-y-1.5">
              {strengths.map((str, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-primary font-bold">•</span>
                  <span className="truncate">{str}</span>
                </li>
              ))}
              {strengths.length === 0 && (
                <li className="text-on-surface-variant/40 italic">No prominent strengths identified.</li>
              )}
            </ul>
          </div>

          {/* Gaps */}
          <div className="space-y-3">
            <h5 className="text-[10px] font-bold text-on-surface-variant flex items-center gap-1.5 uppercase tracking-widest pl-0.5 shrink-0">
              <AlertTriangle className="size-3.5 text-tertiary shrink-0" />
              Gaps
            </h5>
            <ul className="text-xs md:text-sm text-on-surface space-y-1.5">
              {gaps.map((gap, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-tertiary font-bold">•</span>
                  <span className="truncate">{gap}</span>
                </li>
              ))}
              {gaps.length === 0 && (
                <li className="text-green-400/80 italic flex items-center gap-1">
                  ✓ Ready for role requirements
                </li>
              )}
            </ul>
          </div>

          {/* Insights */}
          <div className="space-y-3">
            <h5 className="text-[10px] font-bold text-on-surface-variant flex items-center gap-1.5 uppercase tracking-widest pl-0.5 shrink-0">
              <Lightbulb className="size-3.5 text-on-surface-variant shrink-0" />
              Insights
            </h5>
            <p className="text-xs md:text-sm text-on-surface-variant leading-relaxed italic border-l-2 border-outline-variant/40 pl-3">
              &ldquo;{insights}&rdquo;
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
