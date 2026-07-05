"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MatchScoreCardProps {
  score: number;
  matchDescription?: string;
  badges?: string[];
}

export default function MatchScoreCard({
  score,
  matchDescription = "High confidence match for Sr. Level",
  badges = ["Top 5%", "Culture Fit: Strong"],
}: MatchScoreCardProps) {
  // SVG Circle stroke calculation: radius = 46, circumference = 2 * Math.PI * 46 = ~289
  const circumference = 289;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Determine color matching score range
  const getScoreColorClass = (val: number) => {
    if (val >= 80) return "text-primary stroke-primary";
    if (val >= 60) return "text-tertiary stroke-tertiary";
    return "text-error stroke-error";
  };

  const getScoreGlowClass = (val: number) => {
    if (val >= 80) return "from-primary/10";
    if (val >= 60) return "from-tertiary/10";
    return "from-error/10";
  };

  const colorClass = getScoreColorClass(score);

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 flex flex-col items-center justify-center text-center relative overflow-hidden group shadow-sm select-none min-h-[220px]">
      
      {/* Dynamic gradient hover overlay */}
      <div className={cn(
        "absolute inset-0 bg-gradient-to-br to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none",
        getScoreGlowClass(score)
      )} />

      <div className="relative z-10 flex flex-col items-center justify-center">
        {/* Radial SVG Dial */}
        <div className="w-24 h-24 rounded-full border-4 border-surface-container-highest flex items-center justify-center mb-4 relative shadow-inner">
          <svg className="absolute inset-0 -rotate-90 w-full h-full" viewBox="0 0 100 100">
            <motion.circle
              cx="50"
              cy="50"
              r="46"
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              className={cn("transition-all duration-1000 ease-out", colorClass)}
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.2, ease: "easeOut" }}
            />
          </svg>
          <span className={cn("text-3xl font-bold tracking-tight", colorClass)}>
            {score}
          </span>
        </div>

        {/* Labels */}
        <h4 className="text-sm md:text-base font-bold text-on-surface mb-1">
          Match Probability
        </h4>
        <p className="text-[11px] md:text-xs text-on-surface-variant font-medium max-w-[200px]">
          {matchDescription}
        </p>
      </div>

      {/* Badges footer */}
      <div className="mt-4 flex flex-wrap justify-center gap-1.5 z-10">
        {badges.map((badge, idx) => (
          <span
            key={idx}
            className="px-2.5 py-0.5 bg-surface-container-highest text-on-surface-variant font-bold text-[9px] uppercase tracking-wider rounded-full border border-outline-variant/30 leading-none"
          >
            {badge}
          </span>
        ))}
      </div>
    </div>
  );
}
