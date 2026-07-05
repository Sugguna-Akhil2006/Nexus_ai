"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { RefreshCw, Download, MessageSquareCode } from "lucide-react";
import { Button } from "@/components/ui/button";
import CodeHealthMetrics from "@/components/analytics/code-health-metrics";
import TechStackCard from "@/components/analytics/tech-stack-card";
import ArchitectureExplorer from "@/components/analytics/architecture-explorer";
import HotspotsPanel from "@/components/analytics/hotspots-panel";
import RecentActivityFeed from "@/components/analytics/recent-activity-feed";
import { cn } from "@/lib/utils";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";

// Initial mock data structures
const INITIAL_METRICS = {
  maintainability: 94,
  maintainabilityTrend: "2.4%",
  securityScore: "A+",
  securityDesc: "Top 5%",
  testCoverage: 82.1,
  techDebtHours: 12,
};

const INITIAL_COMPLEXITY = [
  { commit: "C-01", complexity: 32 },
  { commit: "C-02", complexity: 45 },
  { commit: "C-03", complexity: 38 },
  { commit: "C-04", complexity: 55 },
  { commit: "C-05", complexity: 48 },
  { commit: "C-06", complexity: 62 },
  { commit: "C-07", complexity: 50 },
  { commit: "C-08", complexity: 68 },
  { commit: "C-09", complexity: 72 },
  { commit: "C-10", complexity: 78 },
];

const INITIAL_LANGUAGES = [
  { name: "TypeScript", percentage: 64.2, colorClass: "bg-blue-400" },
  { name: "Python", percentage: 22.8, colorClass: "bg-yellow-400" },
  { name: "Rust", percentage: 9.5, colorClass: "bg-purple-400" },
  { name: "Others", percentage: 3.5, colorClass: "bg-outline" },
];

const INITIAL_HOTSPOTS = [
  {
    id: "h-1",
    filePath: "src/lib/engine.ts",
    metricType: "commits" as const,
    metricDesc: "24 commits this week",
    severity: "error" as const,
  },
  {
    id: "h-2",
    filePath: "src/api/handler.py",
    metricType: "complexity" as const,
    metricDesc: "Cyclomatic Complexity: 42",
    severity: "warning" as const,
  },
  {
    id: "h-3",
    filePath: "tests/integration.rs",
    metricType: "coverage" as const,
    metricDesc: "New coverage required",
    severity: "info" as const,
  },
];

const INITIAL_ACTIVITIES = [
  {
    id: "act-1",
    author: "Alex Rivera",
    timeAgo: "2h ago",
    type: "pr" as const,
    description: "Merged PR #142: Refactor auth middleware for better scalability.",
    tags: ["feat", "middleware"],
  },
  {
    id: "act-2",
    author: "System Agent",
    timeAgo: "5h ago",
    type: "system" as const,
    description: "Automated analysis complete: 0 vulnerabilities found in newest patch.",
  },
  {
    id: "act-3",
    author: "Jordan Smith",
    timeAgo: "1d ago",
    type: "push" as const,
    description: "Pushed to branch dev-ui-updates.",
  },
];

export default function RepositoryAnalyticsPage() {
  const [metrics, setMetrics] = useState(INITIAL_METRICS);
  const [complexity, setComplexity] = useState(INITIAL_COMPLEXITY);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Simulate repository scans update refresh pipeline
  const handleRefreshAnalysis = useCallback(async () => {
    setIsRefreshing(true);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    
    // Generate slight shifts in data values to feel live
    setMetrics({
      maintainability: 95,
      maintainabilityTrend: "3.1%",
      securityScore: "A+",
      securityDesc: "Top 4%",
      testCoverage: 83.4,
      techDebtHours: 10,
    });
    
    setComplexity((prev) => 
      prev.map((pt, idx) => ({
        ...pt,
        complexity: pt.complexity + (idx % 2 === 0 ? 2 : -2),
      }))
    );

    setIsRefreshing(false);
    toast.success("Repository health analysis refreshed! Fetched latest branch commits.");
  }, []);

  const handleExportPDF = () => {
    toast.success("Exporting Repository Analysis Report PDF. Your download will start shortly.");
  };

  const handleUpgradeInsight = () => {
    toast.info("Running TS upgrade simulations... Scanning typescript compilerOptions parameters.");
  };

  const handleHotspotClick = (filePath: string) => {
    toast.info(`Inspecting hotspots parameters in file: ${filePath}`);
  };

  return (
    <div className="space-y-8 select-none">
      <DashboardBreadcrumbs />
      
      {/* Header title and trigger actions */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/30 pb-6 shrink-0">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface flex flex-wrap items-center gap-3">
            Repository Overview
            <span className="text-xs text-on-surface-variant bg-surface-container-low border border-outline-variant px-2.5 py-1 rounded-md font-normal leading-none">
              <Link href="/dashboard/analytics" className="hover:text-primary transition-colors">
                ← Switch to System Metrics
              </Link>
            </span>
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-none">
            Analyzing <span className="font-mono text-primary font-bold">v2.4.1-stable</span> branch
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={handleRefreshAnalysis}
            disabled={isRefreshing}
            className="bg-surface-container-low border border-outline-variant hover:bg-surface-container hover:border-primary px-4 py-2.5 rounded-lg text-xs font-bold text-on-surface flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={cn("size-3.5 shrink-0", isRefreshing && "animate-spin")} />
            {isRefreshing ? "Scanning Branch..." : "Refresh Analysis"}
          </Button>
          
          <Button
            onClick={handleExportPDF}
            className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
          >
            <Download className="size-3.5 shrink-0" />
            Export PDF
          </Button>
        </div>
      </section>

      {/* Grid layout section */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Code health wave metrics */}
        <div className="md:col-span-8">
          <CodeHealthMetrics
            metrics={metrics}
            complexityData={complexity}
          />
        </div>

        {/* Tech language allocations stack */}
        <div className="md:col-span-4">
          <TechStackCard
            languages={INITIAL_LANGUAGES}
            aiInsight="Repository shows a strong modular structure. Recommended upgrade: TS 5.4 features could reduce bundle size by ~8%."
            onUpgradeClick={handleUpgradeInsight}
          />
        </div>

        {/* React Flow Service Dependency graph explorer */}
        <div className="md:col-span-12">
          <ArchitectureExplorer />
        </div>

        {/* Hotspots files warning checks */}
        <div className="md:col-span-6">
          <HotspotsPanel
            hotspots={INITIAL_HOTSPOTS}
            onHotspotClick={handleHotspotClick}
          />
        </div>

        {/* Commit/PR Timeline logger */}
        <div className="md:col-span-6">
          <RecentActivityFeed
            activities={INITIAL_ACTIVITIES}
          />
        </div>

      </div>

      {/* Floating AI chatbot assistant FAB */}
      <div className="fixed bottom-8 right-8 z-50">
        <Button
          onClick={() => alert("Launching repository context chatbot. Ask questions about cyclomatic complexity thresholds.")}
          className="w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-2xl flex items-center justify-center active:scale-90 transition-all cursor-pointer border-none shadow-primary/20 hover:scale-105"
          title="Ask Repository AI Assistant"
        >
          <MessageSquareCode className="size-6 text-primary-foreground" />
        </Button>
      </div>
    </div>
  );
}
