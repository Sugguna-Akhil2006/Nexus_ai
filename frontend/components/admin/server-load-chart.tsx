"use client";

import { useState, useEffect } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";
import { cn } from "@/lib/utils";

interface DataPoint {
  time: string;
  load: number;
}

export default function ServerLoadChart() {
  const [activeCluster, setActiveCluster] = useState<"A" | "B">("A");
  
  // Setup data points lists
  const [dataA, setDataA] = useState<DataPoint[]>([]);
  const [dataB, setDataB] = useState<DataPoint[]>([]);

  // Initialize data on mount
  useEffect(() => {
    const initData = (bias: number) => {
      return Array.from({ length: 15 }, (_, i) => {
        const timeVal = new Date(Date.now() - (15 - i) * 60000);
        return {
          time: timeVal.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          load: bias,
        };
      });
    };

    setDataA(initData(15));
    setDataB(initData(10));
  }, []);

  // Live ticking real data fetch pipeline
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("/admin/system");
        if (res.ok) {
          const body = await res.json();
          const cpu = body.data?.cpu_usage_pct ?? 15.0;
          const timeVal = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          
          setDataA((prev) => {
            const next = prev.length >= 15 ? [...prev.slice(1)] : [...prev];
            next.push({ time: timeVal, load: Math.round(cpu) });
            return next;
          });

          setDataB((prev) => {
            const next = prev.length >= 15 ? [...prev.slice(1)] : [...prev];
            next.push({ time: timeVal, load: Math.round(Math.max(2, cpu * 0.75)) });
            return next;
          });
        }
      } catch (e) {
        console.error("Failed to fetch server load metrics", e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  const activeData = activeCluster === "A" ? dataA : dataB;

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none h-[400px] flex flex-col justify-between shadow-sm overflow-hidden relative group">
      
      {/* Header Info */}
      <div className="flex justify-between items-start gap-4 mb-4 shrink-0 z-10">
        <div>
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Server Load
          </h3>
          <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
            Real-time compute cluster utilization
          </p>
        </div>

        {/* Cluster Tabs Selector */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveCluster("A")}
            className={cn(
              "px-3 py-1 text-[10px] font-bold rounded border transition-all cursor-pointer",
              activeCluster === "A"
                ? "bg-primary/10 border-primary/20 text-primary"
                : "bg-surface-container-high border-outline-variant text-on-surface-variant/80 hover:text-on-surface"
            )}
          >
            Cluster A
          </button>
          
          <button
            onClick={() => setActiveCluster("B")}
            className={cn(
              "px-3 py-1 text-[10px] font-bold rounded border transition-all cursor-pointer",
              activeCluster === "B"
                ? "bg-primary/10 border-primary/20 text-primary"
                : "bg-surface-container-high border-outline-variant text-on-surface-variant/80 hover:text-on-surface"
            )}
          >
            Cluster B
          </button>
        </div>
      </div>

      {/* Chart container */}
      <div className="flex-grow w-full relative pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={activeData} margin={{ top: 10, right: -5, left: -25, bottom: -10 }}>
            <defs>
              <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#adc6ff" stopOpacity={0.25}/>
                <stop offset="95%" stopColor="#adc6ff" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis
              dataKey="time"
              stroke="#8c909f"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              dy={8}
            />
            <YAxis
              stroke="#8c909f"
              fontSize={9}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
              tickFormatter={(tick) => `${tick}%`}
              dx={-8}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-surface-container border border-outline-variant p-2 rounded-xl text-[10px] space-y-0.5 shadow-2xl font-medium">
                      <p className="font-bold text-on-surface">{payload[0].payload.time}</p>
                      <p className="text-primary font-bold">Load: {payload[0].value}%</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="load"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorLoad)"
              className="transition-all duration-300"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Premium backdrop blur fade */}
      <div className="absolute inset-x-0 bottom-0 h-16 pointer-events-none bg-gradient-to-t from-background/20 to-transparent z-10" />

    </div>
  );
}
