"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Cpu, Terminal, ArrowUpRight, ArrowRight, ShieldAlert, BarChart3, Database, Calendar, RefreshCw, FileDown, ToggleLeft, ToggleRight, Sparkles, AlertCircle, TrendingDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import dynamic from "next/dynamic";
import type { TokenUsagePoint } from "@/components/analytics/token-consumption-chart";
import type { LatencyBar } from "@/components/analytics/global-latency-map";

const TokenConsumptionChart = dynamic(() => import("@/components/analytics/token-consumption-chart"), { ssr: false });
const CostEfficiencyChart = dynamic(() => import("@/components/analytics/cost-efficiency-chart"), { ssr: false });
const GlobalLatencyMap = dynamic(() => import("@/components/analytics/global-latency-map"), { ssr: false });

import PerformanceLogTable, { LogItem } from "@/components/analytics/performance-log-table";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import PageContainer from "@/components/common/page-container";

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

const MOCK_TOKEN_USAGE_PREV: TokenUsagePoint[] = [
  { day: "Mon", tokens: 120, label: "Mon: 120M tokens" },
  { day: "Tue", tokens: 150, label: "Tue: 150M tokens" },
  { day: "Wed", tokens: 200, label: "Wed: 200M tokens" },
  { day: "Thu", tokens: 140, label: "Thu: 140M tokens" },
  { day: "Fri", tokens: 180, label: "Fri: 180M tokens" },
  { day: "Sat", tokens: 80, label: "Sat: 80M tokens" },
  { day: "Sun", tokens: 60, label: "Sun: 60M tokens" },
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
    statusCode: "500 FAIL",
    statusType: "error",
    clusterPath: "nexus-v4-prod / training",
    tokensText: "0 tokens",
    latencyText: "2490ms",
    timeAgo: "8m ago",
  },
];

export default function PerformanceAnalyticsPage() {
  const [dateRange, setDateRange] = useState("Last 7 Days");
  const [compareMode, setCompareMode] = useState(false);
  const [isEmpty, setIsEmpty] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [logs, setLogs] = useState<LogItem[]>(MOCK_LOGS);

  // Live telemetry update simulation loops
  const [tokensCount, setTokensCount] = useState(48.2);
  const [p95Latency, setP95Latency] = useState(182);
  const [avgCost, setAvgCost] = useState(1420);

  useEffect(() => {
    if (isEmpty) return;
    const interval = setInterval(() => {
      setTokensCount((prev) => +(prev + (Math.random() * 0.4 - 0.2)).toFixed(1));
      setP95Latency((prev) => Math.max(120, prev + Math.floor(Math.random() * 6 - 3)));
      setAvgCost((prev) => Math.max(1000, prev + Math.floor(Math.random() * 10 - 5)));
      
      // Randomly append new live log row
      if (Math.random() > 0.6) {
        const nextId = `log-${Date.now()}`;
        const newLog: LogItem = {
          id: nextId,
          statusCode: "200 OK",
          statusType: "success",
          clusterPath: "nexus-v4-prod / completion",
          tokensText: `${Math.floor(Math.random() * 5 + 1)}.${Math.floor(Math.random() * 9)}k tokens`,
          latencyText: `${Math.floor(Math.random() * 50 + 100)}ms`,
          timeAgo: "Just now",
        };
        setLogs((prev) => [newLog, ...prev.slice(0, 7)]);
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [isEmpty]);

  const handleExport = (format: string) => {
    setIsExporting(true);
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: `Compressing performance analytics logs to ${format.toUpperCase()} format...`,
        success: `Analytics telemetry successfully exported! Download started.`,
        error: "Failed to compile logs database.",
      }
    );
    setTimeout(() => setIsExporting(false), 1600);
  };

  const toolbarActions = (
    <>
      <Button 
        variant="ghost" 
        size="xs" 
        onClick={() => setIsEmpty(!isEmpty)} 
        className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors bg-transparent border-none mr-2"
      >
        {isEmpty ? "● Show Analytics" : "○ Simulate Empty State"}
      </Button>

      {!isEmpty && (
        <div className="flex flex-wrap items-center gap-3">
          {/* Date Range Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="flex items-center gap-2 border-outline-variant text-xs cursor-pointer">
                <Calendar className="size-3.5" />
                {dateRange}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50 w-40">
              {["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Current Quarter"].map((d) => (
                <DropdownMenuItem
                  key={d}
                  className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded"
                  onClick={() => {
                    setDateRange(d);
                    toast.success(`Analytics filter adjusted: ${d}`);
                  }}
                >
                  {d}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Comparison Mode Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setCompareMode(!compareMode);
              toast.info(compareMode ? "Comparison overlay disabled" : "Overlaying metrics from previous period");
            }}
            className={cn(
              "flex items-center gap-2 border-outline-variant text-xs cursor-pointer transition-all",
              compareMode && "border-primary text-primary bg-primary/5"
            )}
          >
            {compareMode ? <ToggleRight className="size-4" /> : <ToggleLeft className="size-4" />}
            Compare Period
          </Button>

          {/* Export Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" disabled={isExporting} className="flex items-center gap-2 border-outline-variant text-xs cursor-pointer">
                <FileDown className="size-3.5" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="bg-surface border border-outline-variant p-1.5 shadow-lg text-on-surface z-50 w-44">
              <DropdownMenuLabel className="text-[10px] uppercase font-bold text-on-surface-variant">Select Format</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-outline-variant" />
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => handleExport("csv")}>
                CSV Spreadsheet
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => handleExport("pdf")}>
                PDF Document Report
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => handleExport("json")}>
                JSON Raw Telemetry
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Link to repository Health Analyzer */}
          <Link href="/dashboard/analytics/repository" passHref>
            <Button
              size="sm"
              className="bg-primary text-primary-foreground hover:bg-primary/95 text-xs font-semibold rounded-lg cursor-pointer flex items-center gap-1.5 border-none"
            >
              <Database className="size-3.5" />
              Repository Health
              <ArrowRight className="size-3.5 shrink-0" />
            </Button>
          </Link>
        </div>
      )}
    </>
  );

  return (
    <PageContainer
      title="Performance Analytics"
      description="Infrastructure analytics metrics for Nexus Core cluster deployments."
      icon={<BarChart3 className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
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
        <div className="space-y-8">
          {/* AI Insights & Recommendation Board Banner */}
          <section className="bg-surface-container-low border border-outline-variant/65 rounded-xl p-5 select-none relative overflow-hidden">
            <div className="absolute top-0 right-0 w-48 h-48 bg-primary/5 rounded-full blur-3xl" />
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                <Sparkles className="size-5 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-bold text-on-surface flex items-center gap-1.5">
                  AI Optimization Insights
                  <span className="text-[9px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20 px-1.5 py-0.5 rounded">Recommending</span>
                </h4>
                <p className="text-xs text-on-surface-variant/90 leading-relaxed mt-1.5 max-w-3xl">
                  Average APAC latency has spiked by <span className="text-red-400 font-semibold">18%</span> over the last 2 hours. We recommend routing concurrent vector database searches to <span className="text-green-400 font-semibold">US-East regional clusters</span> to reduce overall API costs by approximately <span className="text-green-400 font-semibold">$340/month</span> while lowering P95 time metrics.
                </p>
                <div className="flex items-center gap-4 mt-3 text-[10px] text-on-surface-variant font-mono">
                  <span className="flex items-center gap-1">
                    <TrendingDown className="size-3.5 text-green-400" />
                    Projected Cost Drop: -14.2%
                  </span>
                  <span>·</span>
                  <span className="flex items-center gap-1">
                    <RefreshCw className="size-3 text-primary animate-spin" />
                    Auto-routing: Active
                  </span>
                </div>
              </div>
            </div>
          </section>

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
                <span className="text-[10px] text-on-surface-variant/60 font-medium">tokens</span>
              </div>
            </div>

            {/* P95 Latency */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  P95 Latency
                </span>
                <span className="text-red-400 font-mono font-bold leading-none">
                  +3.1%
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  {p95Latency}
                </span>
                <span className="text-[10px] text-on-surface-variant/60 font-medium">ms</span>
              </div>
            </div>

            {/* Ingestion load */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Active Load
                </span>
                <span className="text-green-400 font-mono font-bold leading-none">
                  Stable
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  42.8%
                </span>
                <span className="text-[10px] text-on-surface-variant/60 font-medium">capacity</span>
              </div>
            </div>

            {/* Estimated cost */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-2.5 shadow-sm">
              <div className="flex justify-between items-start">
                <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px]">
                  Estimated Cost
                </span>
                <span className="text-primary font-mono font-bold leading-none">
                  +1.8%
                </span>
              </div>
              <div className="flex items-baseline gap-1.5 select-text">
                <span className="text-xl md:text-2xl font-bold text-on-surface">
                  ${avgCost.toLocaleString()}
                </span>
                <span className="text-[10px] text-on-surface-variant/60 font-medium">/mo</span>
              </div>
            </div>

          </section>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch select-none">
            
            {/* Token Consumption Volume charts */}
            <div className="lg:col-span-8">
              <TokenConsumptionChart 
                initialData={compareMode ? MOCK_TOKEN_USAGE_PREV : MOCK_TOKEN_USAGE}
              />
            </div>

            {/* Cost efficiency indicator */}
            <div className="lg:col-span-4">
              <CostEfficiencyChart 
                percentage={75}
                allocated={20000}
                remaining={5797}
              />
            </div>

          </div>

          {/* Latency heatmaps and execution log lists */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            
            {/* Latency Map */}
            <div className="lg:col-span-4">
              <GlobalLatencyMap 
                bars={MOCK_LATENCY_BARS}
                globalAverage="182ms"
              />
            </div>

            {/* Performance log details table */}
            <div className="lg:col-span-8">
              <PerformanceLogTable 
                logs={logs}
                onViewAllClick={() => toast.info("Opening all real-time logs...")}
              />
            </div>

          </div>
        </div>
      )}
    </PageContainer>
  );
}
