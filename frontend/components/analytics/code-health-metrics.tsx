"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, Tooltip, CartesianGrid } from "recharts";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ComplexityPoint {
  commit: string;
  complexity: number;
}

interface CodeHealthMetricsProps {
  metrics: {
    maintainability: number;
    maintainabilityTrend: string;
    securityScore: string;
    securityDesc: string;
    testCoverage: number;
    techDebtHours: number;
  };
  complexityData: ComplexityPoint[];
}

export default function CodeHealthMetrics({
  metrics,
  complexityData,
}: CodeHealthMetricsProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Code Health Metrics
        </h3>
        <span className="px-2 py-0.5 bg-green-900/30 text-green-400 border border-green-500/20 rounded text-[9px] font-bold uppercase tracking-widest leading-none">
          Stable
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
        {/* Maintainability */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] md:text-xs text-on-surface-variant/80 font-bold uppercase tracking-wider">
            Maintainability
          </span>
          <div className="flex items-baseline gap-1.5 select-text">
            <span className="text-xl md:text-2xl font-bold text-primary">
              {metrics.maintainability}%
            </span>
            <span className="text-green-400 text-[10px] md:text-xs font-bold flex items-center leading-none">
              <ArrowUp className="size-3 shrink-0" />
              {metrics.maintainabilityTrend}
            </span>
          </div>
          <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden select-none">
            <div className="bg-primary h-full rounded-full" style={{ width: `${metrics.maintainability}%` }} />
          </div>
        </div>

        {/* Security Score */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] md:text-xs text-on-surface-variant/80 font-bold uppercase tracking-wider">
            Security Score
          </span>
          <div className="flex items-baseline gap-2 select-text">
            <span className="text-xl md:text-2xl font-bold text-on-surface">
              {metrics.securityScore}
            </span>
            <span className="text-on-surface-variant text-[10px] md:text-xs font-semibold leading-none">
              {metrics.securityDesc}
            </span>
          </div>
          <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden select-none">
            <div className="bg-green-500 h-full rounded-full" style={{ width: "98%" }} />
          </div>
        </div>

        {/* Test Coverage */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] md:text-xs text-on-surface-variant/80 font-bold uppercase tracking-wider">
            Test Coverage
          </span>
          <div className="flex items-baseline select-text">
            <span className="text-xl md:text-2xl font-bold text-on-surface">
              {metrics.testCoverage}%
            </span>
          </div>
          <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden select-none">
            <div className="bg-tertiary h-full rounded-full" style={{ width: `${metrics.testCoverage}%` }} />
          </div>
        </div>

        {/* Tech Debt */}
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] md:text-xs text-on-surface-variant/80 font-bold uppercase tracking-wider">
            Tech Debt
          </span>
          <div className="flex items-baseline select-text">
            <span className="text-xl md:text-2xl font-bold text-on-surface">
              {metrics.techDebtHours}h
            </span>
          </div>
          <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden select-none">
            <div className="bg-error h-full rounded-full" style={{ width: "12%" }} />
          </div>
        </div>
      </div>

      {/* Recharts Waveform Graph */}
      <div className="h-44 rounded-lg bg-surface border border-outline-variant/30 relative flex flex-col p-4 overflow-hidden select-none">
        
        {/* Absolute header overlay */}
        <div className="absolute top-3 left-4 z-10 flex flex-col pointer-events-none select-none">
          <span className="font-mono text-[10px] text-on-surface-variant/70 tracking-wider">
            Complexity Trajectory Waveform
          </span>
          <div className="flex items-center gap-1.5 mt-1.5">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.6)]"></div>
            <span className="text-[9px] font-bold text-primary uppercase tracking-widest leading-none">
              Active Analysis
            </span>
          </div>
        </div>

        <div className="w-full h-full pt-10 relative select-none">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={complexityData} margin={{ top: 5, right: 0, left: -28, bottom: -10 }}>
              <defs>
                <linearGradient id="colorComplexity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c1b1d" vertical={false} />
              <XAxis
                dataKey="commit"
                stroke="#8c909f"
                fontSize={9}
                tickLine={false}
                axisLine={false}
                dy={5}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-surface-container border border-outline-variant p-2 rounded-lg text-[10px] space-y-0.5 shadow-xl font-medium">
                        <p className="font-bold text-on-surface">Commit: {payload[0].payload.commit}</p>
                        <p className="text-primary font-bold">Complexity score: {payload[0].value}</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="complexity"
                stroke="#3b82f6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorComplexity)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
