"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { cn } from "@/lib/utils";

export interface TrajectoryPoint {
  year: string;
  candidateScore: number;
  benchmarkScore: number;
}

interface ExperienceTrajectoryProps {
  data: TrajectoryPoint[];
}

export default function ExperienceTrajectory({ data }: ExperienceTrajectoryProps) {
  return (
    <div className="col-span-1 md:col-span-2 h-64 bg-surface-container-low border border-outline-variant rounded-xl relative overflow-hidden flex flex-col p-5 shadow-sm select-none">
      
      {/* Background Dots Overlay */}
      <div 
        className="absolute inset-0 opacity-5 pointer-events-none select-none" 
        style={{
          backgroundImage: "radial-gradient(#3b82f6 1px, transparent 1px)",
          backgroundSize: "24px 24px"
        }} 
      />

      {/* Header Info */}
      <div className="relative z-10 flex justify-between items-start mb-3">
        <div>
          <h4 className="text-xs md:text-sm font-bold text-on-surface">
            Experience Trajectory
          </h4>
          <p className="text-[10px] text-on-surface-variant font-medium">
            Career level progression vs. Industry Benchmarks
          </p>
        </div>

        {/* Custom Legend */}
        <div className="flex gap-4 text-[9px] font-bold uppercase tracking-wider">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded bg-primary shrink-0" />
            Candidate
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded bg-outline shrink-0" />
            Benchmark
          </div>
        </div>
      </div>

      {/* Recharts Area Chart Viewport */}
      <div className="flex-1 w-full relative z-10 select-none">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCandidate" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2c" vertical={false} />
            <XAxis
              dataKey="year"
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
              domain={[0, 100]}
              tickCount={5}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-surface-container border border-outline-variant p-2.5 rounded-lg text-[10px] space-y-1 shadow-xl font-medium">
                      <p className="font-bold text-on-surface mb-1">
                        Timeline: {payload[0].payload.year}
                      </p>
                      <p className="text-primary flex justify-between gap-4">
                        <span>Candidate Score:</span>
                        <span className="font-mono font-bold">{payload[0].value}%</span>
                      </p>
                      <p className="text-on-surface-variant flex justify-between gap-4">
                        <span>Industry Benchmark:</span>
                        <span className="font-mono font-bold">{payload[1].value}%</span>
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="candidateScore"
              stroke="#3b82f6"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCandidate)"
            />
            <Area
              type="monotone"
              dataKey="benchmarkScore"
              stroke="#8c909f"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              fill="none"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
