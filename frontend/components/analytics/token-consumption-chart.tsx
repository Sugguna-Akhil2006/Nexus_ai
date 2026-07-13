"use client";

import { useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { cn } from "@/lib/utils";

export interface TokenUsagePoint {
  day: string;
  tokens: number; // in Millions
  label: string;
}

interface TokenConsumptionChartProps {
  initialData: TokenUsagePoint[];
}

export default function TokenConsumptionChart({
  initialData,
}: TokenConsumptionChartProps) {
  const [range, setRange] = useState<"7d" | "30d">("7d");

  // Format values on Y axis
  const formatYAxis = (tick: number) => {
    if (tick >= 1000000) return `${(tick / 1000000).toFixed(1)}M`;
    if (tick >= 1000) return `${(tick / 1000).toFixed(1)}k`;
    return `${tick}`;
  };

  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl p-5 select-none h-[420px] flex flex-col justify-between shadow-sm">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-4 shrink-0">
        <div>
          <h2 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Token Consumption
          </h2>
          <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
            Daily breakdown across all clusters
          </p>
        </div>

        {/* Filters */}
        <div className="flex gap-2 bg-surface-container-low border border-outline-variant/60 rounded-lg p-1">
          <button
            onClick={() => setRange("7d")}
            className={cn(
              "px-3 py-1 rounded text-[10px] font-bold transition-all cursor-pointer",
              range === "7d" ? "bg-secondary-container text-on-surface" : "text-on-surface-variant/80 hover:text-on-surface"
            )}
          >
            7D
          </button>
          <button
            onClick={() => setRange("30d")}
            className={cn(
              "px-3 py-1 rounded text-[10px] font-bold transition-all cursor-pointer",
              range === "30d" ? "bg-secondary-container text-on-surface" : "text-on-surface-variant/80 hover:text-on-surface"
            )}
          >
            30D
          </button>
        </div>
      </div>

      {/* Recharts Bar Chart */}
      <div className="flex-grow w-full relative pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={initialData} margin={{ top: 20, right: 0, left: -22, bottom: -10 }}>
            <XAxis
              dataKey="day"
              stroke="#8c909f"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dy={8}
            />
            <YAxis
              stroke="#8c909f"
              fontSize={9}
              tickFormatter={formatYAxis}
              tickLine={false}
              axisLine={false}
              dx={-8}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-surface-container border border-outline-variant p-2.5 rounded-xl text-[10px] space-y-0.5 shadow-2xl font-medium">
                      <p className="font-bold text-on-surface">{payload[0].payload.label}</p>
                      <p className="text-primary font-bold">Usage: {payload[0].value} tokens</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar
              dataKey="tokens"
              radius={[4, 4, 0, 0]}
              className="cursor-help"
            >
              {initialData.map((entry, index) => {
                // Return different opacities to match look (highest Wed gets bold opacity)
                const opacity = entry.tokens > 250 ? 0.7 : entry.tokens > 180 ? 0.5 : 0.3;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill="#3b82f6"
                    fillOpacity={opacity}
                    className="hover:fill-opacity-80 transition-all duration-200"
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
