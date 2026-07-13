"use client";

import { useEffect, useState } from "react";
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
  modelA: number; // API requests count
  modelB: number; // API failures or scaled metric
}

export default function InferenceLoadsChart() {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch("/api/platform/metrics")
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((metrics) => {
        const timeline = metrics.usage_timeline || [];
        const formatted = timeline.map((slot: any) => ({
          time: slot.time,
          modelA: slot.requests,
          modelB: slot.failures,
          dataKb: slot.data_kb,
        }));
        if (formatted.length === 0) {
          setData([{ time: "Ready", modelA: 0, modelB: 0 }]);
        } else {
          setData(formatted);
        }
        setLoading(false);
      })
      .catch(() => {
        setError(true);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="col-span-12 lg:col-span-8 bg-surface-container-low border border-outline-variant p-6 rounded-xl flex items-center justify-center h-80">
        <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (error || data.length === 0) {
    return (
      <div className="col-span-12 lg:col-span-8 bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col items-center justify-center h-80 text-center select-none">
        <span className="text-on-surface-variant font-medium text-sm">No Analytics Available</span>
      </div>
    );
  }

  return (
    <div className="col-span-12 lg:col-span-8 bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col gap-6 group hover:border-outline-variant/80 transition-all duration-300">
      {/* Title & Legend Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h3 className="text-xl font-semibold text-on-surface tracking-tight">
          System API Loads
        </h3>
        
        {/* Custom Legend */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 select-none">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
            <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
              Requests Count
            </span>
          </div>
          <div className="flex items-center gap-2 select-none">
            <span className="w-2.5 h-2.5 rounded-full bg-[#adc6ff]" />
            <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
              System Failures
            </span>
          </div>
        </div>
      </div>

      {/* Chart container */}
      <div className="h-64 w-full relative select-none">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart 
            data={data} 
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
              name="Requests"
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
              name="Failures"
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
