"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Cpu, Terminal, ArrowUpRight, ArrowRight, ShieldAlert, BarChart3, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import TokenConsumptionChart, { TokenUsagePoint } from "@/components/analytics/token-consumption-chart";
import CostEfficiencyChart from "@/components/analytics/cost-efficiency-chart";
import GlobalLatencyMap, { LatencyBar } from "@/components/analytics/global-latency-map";
import PerformanceLogTable, { LogItem } from "@/components/analytics/performance-log-table";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";

// Mock Weekly Token Usage data
const MOCK_TOKEN_USAGE: TokenUsagePoint[] = [
  { day: "Mon", tokens: 142, label: "Mon: 142M tokens" },
  { day: "Tue", tokens: 184, label: "Tue: 184M tokens" },
  { day: "Wed", tokens: 290, label: "Wed: 290M tokens" },
  { day: "Thu", tokens: 156, label: "Thu: 156M tokens" },
  { day: "Fri", tokens: 212, label: "Fri: 212M tokens" },
  { day: "Sat", tokens: 98, label: "Sat: 98M tokens" },
  { day: "Sun", tokens: 72, label: "Sun: 72M tokens" },
];

// Mock Latency Bars heights and opacity sequence matching HTML visual layout
const MOCK_LATENCY_BARS: LatencyBar[] = [
  { id: 1, heightClass: "h-24", colorClass: "bg-[#10b981]", opacityClass: "opacity-60" },
  { id: 2, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-70" },
  { id: 3, heightClass: "h-28", colorClass: "bg-[#f59e0b]", opacityClass: "opacity-80" },
  { id: 4, heightClass: "h-20", colorClass: "bg-[#10b981]", opacityClass: "opacity-60" },
  { id: 5, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-90" },
  { id: 6, heightClass: "h-16", colorClass: "bg-[#ef4444]", opacityClass: "opacity-70" },
  { id: 7, heightClass: "h-28", colorClass: "bg-[#10b981]", opacityClass: "opacity-50" },
  { id: 8, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-80" },
  { id: 9, heightClass: "h-24", colorClass: "bg-[#f59e0b]", opacityClass: "opacity-60" },
  { id: 10, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-70" },
  { id: 11, heightClass: "h-20", colorClass: "bg-[#10b981]", opacityClass: "opacity-60" },
  { id: 12, heightClass: "h-12", colorClass: "bg-[#ef4444]", opacityClass: "opacity-50" },
  { id: 13, heightClass: "h-24", colorClass: "bg-[#10b981]", opacityClass: "opacity-60" },
  { id: 14, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-70" },
  { id: 15, heightClass: "h-28", colorClass: "bg-[#f59e0b]", opacityClass: "opacity-80" },
  { id: 16, heightClass: "h-20", colorClass: "bg-[#10b981]", opacityClass: "opacity-60" },
  { id: 17, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-90" },
  { id: 18, heightClass: "h-16", colorClass: "bg-[#ef4444]", opacityClass: "opacity-70" },
  { id: 19, heightClass: "h-28", colorClass: "bg-[#10b981]", opacityClass: "opacity-50" },
  { id: 20, heightClass: "h-32", colorClass: "bg-[#10b981]", opacityClass: "opacity-80" },
];

// Mock logs rows
const MOCK_LOGS: LogItem[] = [
  {
    id: "log-1",
    statusCode: "200 OK",
    statusType: "success",
    clusterPath: "nexus-v4-prod / completion",
    tokensText: "4.2k tokens",
    latencyText: "142ms",
    timeAgo: "2m ago",
  },
  {
    id: "log-2",
    statusCode: "200 OK",
    statusType: "success",
    clusterPath: "nexus-v4-prod / embedding",
    tokensText: "512 tokens",
    latencyText: "88ms",
    timeAgo: "4m ago",
  },
  {
    id: "log-3",
    statusCode: "429 RATE",
    statusType: "warning",
    clusterPath: "internal-dev-cluster / completion",
    tokensText: "0 tokens",
    latencyText: "--ms",
    timeAgo: "5m ago",
  },
  {
    id: "log-4",
    statusCode: "200 OK",
    statusType: "success",
    clusterPath: "nexus-v4-prod / completion",
    tokensText: "8.1k tokens",
    latencyText: "312ms",
    timeAgo: "7m ago",
  },
];

export default function AdvancedAnalyticsPage() {
  const [isEmpty, setIsEmpty] = useState(false);
  
  // Counters states to run on-mount ticking animation
  const [tokensCount, setTokensCount] = useState(0);
  const [costCount, setCostCount] = useState(0);
  const [latencyCount, setLatencyCount] = useState(0);
  const [agentsCount, setAgentsCount] = useState(0);

  useEffect(() => {
    if (isEmpty) {
      setTokensCount(0);
      setCostCount(0);
      setLatencyCount(0);
      setAgentsCount(0);
      return;
    }
    // Tick animations
    const duration = 1200;
    const steps = 30;
    const intervalTime = duration / steps;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      const progress = step / steps;
      const easeOut = 1 - Math.pow(1 - progress, 3); // cubic ease-out

      setTokensCount(parseFloat((1.24 * easeOut).toFixed(2)));
      setCostCount(Math.floor(14203 * easeOut));
      setLatencyCount(Math.floor(242 * easeOut));
      setAgentsCount(Math.floor(84 * easeOut));

      if (step >= steps) {
        clearInterval(interval);
      }
    }, intervalTime);

    return () => clearInterval(interval);
  }, [isEmpty]);

  const handleViewLogs = () => {
    toast.info("Opening full performance latency pipeline logs viewer...");
  };

  return (
    <div className="space-y-8 select-none relative">
      <DashboardBreadcrumbs />
      
      {/* Header Info */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/30 pb-6 shrink-0 select-none">
        <div>
          <div className="flex items-center gap-4">
            <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
              Performance Analytics
            </h2>
            <Button 
              variant="ghost" 
              size="xs" 
              onClick={() => setIsEmpty(!isEmpty)} 
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
            >
              {isEmpty ? "● Show Metrics" : "○ Simulate Empty State"}
            </Button>
          </div>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-none">
            Infrastructure analytics metrics for Nexus Core cluster deployments
          </p>
        </div>

        {/* Link back/forth to repository Health Analyzer */}
        <div className="flex select-none">
          <Link href="/dashboard/analytics/repository" passHref>
            <Button
              className="bg-transparent border border-outline hover:bg-surface-container hover:border-primary text-on-surface text-xs font-bold px-4 py-2.5 rounded-lg cursor-pointer flex items-center gap-1.5"
            >
              <Database className="size-3.5" />
              <span>View Repository Health</span>
              <ArrowUpRight className="size-3.5 shrink-0" />
            </Button>
          </Link>
        </div>
      </section>

      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={BarChart3}
            title="No Metric Clusters Available"
            description="Trigger workflow execution queries, query active agents, or stream API datasets to accumulate latency heatmaps, validation loss, and cost curves."
            actionLabel="Generate Simulated Logs"
            onAction={() => {
              setIsEmpty(false);
              toast.success("Accumulating simulated model performance metrics logs...");
            }}
            accentColor="primary"
          />
        </div>
      ) : (
        <>
          {/* KPI Stats Grid Row */}
          <section className="grid grid-cols-2 md:grid-cols-4 gap-6 select-none text-xs md:text-sm">
            
            {/* Total Usage */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Total Usage
                </span>
                <span className="text-primary font-mono font-bold leading-none">
                  +12.4%
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  {tokensCount}B
                </span>
                <span className="text-on-surface-variant/80 text-[10px] md:text-xs font-semibold leading-none">
                  tokens
                </span>
              </div>
            </div>

            {/* Estimated Cost */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Estimated Cost
                </span>
                <span className="text-error font-mono font-bold leading-none">
                  +4.2%
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  ${costCount.toLocaleString()}
                </span>
                <span className="text-on-surface-variant/80 text-[10px] md:text-xs font-semibold leading-none">
                  USD
                </span>
              </div>
            </div>

            {/* Avg Latency */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Avg Latency
                </span>
                <span className="text-primary font-mono font-bold leading-none">
                  -18ms
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  {latencyCount}ms
                </span>
                <span className="text-on-surface-variant/80 text-[10px] md:text-xs font-semibold leading-none">
                  P95
                </span>
              </div>
            </div>

            {/* Active Agents */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Active Agents
                </span>
                <span className="text-primary font-mono font-bold leading-none">
                  Live
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  {agentsCount}
                </span>
                <span className="text-on-surface-variant/80 text-[10px] md:text-xs font-semibold leading-none">
                  instances
                </span>
              </div>
            </div>

          </section>

          {/* Main Analytics Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            
            {/* Token Consumption Recharts Bar */}
            <div className="md:col-span-8">
              <TokenConsumptionChart 
                initialData={MOCK_TOKEN_USAGE} 
              />
            </div>

            {/* Cost Efficiency circular gauge */}
            <div className="md:col-span-4">
              <CostEfficiencyChart 
                percentage={75} 
                allocated={20000} 
                remaining={5797} 
              />
            </div>

            {/* Latency heatmap wave grids */}
            <div className="md:col-span-12">
              <GlobalLatencyMap 
                bars={MOCK_LATENCY_BARS} 
                globalAverage="186ms" 
              />
            </div>

            {/* Real-time queries performance log tables */}
            <div className="md:col-span-12">
              <PerformanceLogTable 
                logs={MOCK_LOGS} 
                onViewAllClick={handleViewLogs} 
              />
            </div>

          </div>
        </>
      )}

    </div>
  );
}
