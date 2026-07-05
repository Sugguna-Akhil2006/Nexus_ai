"use client";

import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from "recharts";

interface ChartDataPoint {
  time: string;
  modelA: number; // GPT-X load
  modelB: number; // Nexus-7 load
}

const DATA: ChartDataPoint[] = [
  { time: "00:00", modelA: 150, modelB: 180 },
  { time: "02:00", modelA: 110, modelB: 160 },
  { time: "04:00", modelA: 80,  modelB: 140 },
  { time: "06:00", modelA: 100, modelB: 150 },
  { time: "08:00", modelA: 120, modelB: 165 },
  { time: "10:00", modelA: 95,  modelB: 145 },
  { time: "12:00", modelA: 60,  modelB: 120 },
  { time: "14:00", modelA: 85,  modelB: 135 },
  { time: "16:00", modelA: 100, modelB: 125 },
  { time: "18:00", modelA: 75,  modelB: 140 },
  { time: "20:00", modelA: 40,  modelB: 150 },
  { time: "22:00", modelA: 90,  modelB: 165 },
];

export default function InferenceLoadsChart() {
  return (
    <div className="col-span-12 lg:col-span-8 bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col gap-6 group hover:border-outline-variant/80 transition-all duration-300">
      {/* Title & Legend Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h3 className="text-xl font-semibold text-on-surface tracking-tight">
          Inference Loads
        </h3>
        
        {/* Custom Legend */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 select-none">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
            <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
              Model-A (GPT-X)
            </span>
          </div>
          <div className="flex items-center gap-2 select-none">
            <span className="w-2.5 h-2.5 rounded-full bg-[#adc6ff]" />
            <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
              Model-B (Nexus-7)
            </span>
          </div>
        </div>
      </div>

      {/* Chart container */}
      <div className="h-64 w-full relative select-none">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart 
            data={DATA} 
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            {/* Ambient gradients */}
            <defs>
              <linearGradient id="colorModelA" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.01}/>
              </linearGradient>
            </defs>

            {/* Background grids matching zinc-800 (#27272a) outline colors */}
            <CartesianGrid 
              stroke="#27272a" 
              strokeDasharray="0" 
              vertical={false} 
            />

            {/* Axes settings */}
            <XAxis 
              dataKey="time" 
              stroke="#8c909f" 
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="#8c909f" 
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dx={-5}
            />

            {/* Custom Tooltip */}
            <Tooltip
              contentStyle={{
                backgroundColor: "#1c1b1d",
                border: "1px solid #424754",
                borderRadius: "8px",
                fontFamily: "var(--font-sans)",
                fontSize: "12px",
                color: "#e5e1e4",
              }}
              labelStyle={{ fontWeight: 600, color: "#e5e1e4", marginBottom: "4px" }}
              itemStyle={{ padding: 0 }}
            />

            {/* Model-A Area: Solid blue with shadow fill */}
            <Area
              type="monotone"
              dataKey="modelA"
              name="Model-A Load"
              stroke="#3b82f6"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorModelA)"
              activeDot={{ r: 5, stroke: "#3b82f6", strokeWidth: 2, fill: "#131315" }}
            />

            {/* Model-B Area: Dashed light blue line, no fill */}
            <Area
              type="monotone"
              dataKey="modelB"
              name="Model-B Load"
              stroke="#adc6ff"
              strokeWidth={2}
              strokeDasharray="5 5"
              fill="none"
              activeDot={{ r: 4, stroke: "#adc6ff", strokeWidth: 2, fill: "#131315" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
