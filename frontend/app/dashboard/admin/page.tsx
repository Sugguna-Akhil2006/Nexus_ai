"use client";

import { useState } from "react";
import Link from "next/link";
import { Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import KpiCards from "@/components/admin/kpi-cards";
import ServerLoadChart from "@/components/admin/server-load-chart";
import SystemHealthPanel, { HealthMetric } from "@/components/admin/system-health-panel";
import OrganizationsTable, { OrganizationItem } from "@/components/admin/organizations-table";
import AuditLog, { AuditLogItem } from "@/components/admin/audit-log";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";

// Mock health stats
const INITIAL_HEALTH_METRICS: HealthMetric[] = [
  {
    id: "h-1",
    name: "API Gateway",
    status: "Active",
    metricText: "12ms latency",
  },
  {
    id: "h-2",
    name: "Compute Nodes",
    status: "Active",
    metricText: "42% utilized",
  },
  {
    id: "h-3",
    name: "Vector Database",
    status: "Active",
    metricText: "Healthy",
  },
  {
    id: "h-4",
    name: "CDN Edge",
    status: "Warning",
    metricText: "Degraded",
  },
];

// Mock enterprises database
const INITIAL_ORGS: OrganizationItem[] = [
  {
    id: "org-1",
    name: "Vortex Systems",
    planType: "Enterprise",
    status: "Active",
    lastActivity: "2 mins ago",
    colorClass: "bg-indigo-500/20 text-indigo-400",
    letter: "V",
  },
  {
    id: "org-2",
    name: "Kinetix Bio",
    planType: "Scale",
    status: "Active",
    lastActivity: "14 mins ago",
    colorClass: "bg-orange-500/20 text-orange-400",
    letter: "K",
  },
  {
    id: "org-3",
    name: "Nebula Corp",
    planType: "Enterprise",
    status: "Suspended",
    lastActivity: "2 days ago",
    colorClass: "bg-red-500/20 text-red-400",
    letter: "N",
  },
  {
    id: "org-4",
    name: "Artemis AI",
    planType: "Scale",
    status: "Active",
    lastActivity: "45 mins ago",
    colorClass: "bg-emerald-500/20 text-emerald-400",
    letter: "A",
  },
];

// Mock timelines audit history
const MOCK_AUDIT_LOGS: AuditLogItem[] = [
  {
    id: "audit-1",
    title: "Policy Update",
    description: "Admin changed auth protocols for Vortex Systems.",
    timestampText: "12:44 PM • J. Miller",
    iconType: "security",
  },
  {
    id: "audit-2",
    title: "User Provisioned",
    description: "3 new seats added to Artemis AI Enterprise plan.",
    timestampText: "11:30 AM • System",
    iconType: "user",
  },
  {
    id: "audit-3",
    title: "Access Denied",
    description: "Multiple failed login attempts detected on Root Admin.",
    timestampText: "10:05 AM • GuardRail",
    iconType: "warning",
  },
  {
    id: "audit-4",
    title: "Cluster Snapshot",
    description: "Manual backup initiated for US-EAST-1 cluster nodes.",
    timestampText: "09:15 AM • R. Chen",
    iconType: "cloud",
  },
];

export default function AdminDashboardPage() {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetric[]>(INITIAL_HEALTH_METRICS);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefreshSync = async () => {
    setIsRefreshing(true);
    try {
      const res = await fetch("/admin/health");
      const data = await res.json();
      if (data.success && data.data && data.data.services) {
        const services = data.data.services;
        const metrics: HealthMetric[] = [
          {
            id: "h-1",
            name: "API Gateway",
            status: services.api_gateway.status === "healthy" ? "Active" : "Warning",
            metricText: `${services.api_gateway.routes_registered} routes`,
          },
          {
            id: "h-2",
            name: "Database Status",
            status: services.database.status === "healthy" ? "Active" : "Error",
            metricText: `${services.database.latency_ms}ms`,
          },
          {
            id: "h-3",
            name: "WebSocket Channels",
            status: services.websocket.status === "healthy" ? "Active" : "Warning",
            metricText: `${services.websocket.active_channels} active`,
          }
        ];
        setHealthMetrics(metrics);
        toast.success("Enterprise health metrics synchronized successfully!");
      }
    } catch (e) {
      toast.error("Failed to sync live gateway metrics. Using simulator fallback.");
      // Fallback
      setHealthMetrics([
        {
          id: "h-1",
          name: "API Gateway",
          status: "Active",
          metricText: `${Math.floor(Math.random() * 5 + 10)}ms latency`,
        },
        {
          id: "h-2",
          name: "Compute Nodes",
          status: "Active",
          metricText: `${Math.floor(Math.random() * 10 + 38)}% utilized`,
        },
        {
          id: "h-3",
          name: "Vector Database",
          status: "Active",
          metricText: "Healthy",
        }
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExportReport = () => {
    toast.success("Exporting platform-wide Global Administration audit report PDF. Download will start shortly.");
  };

  const handleViewHealthLogs = () => {
    toast.info("Loading infrastructure gateway system metrics logs viewer...");
  };

  const handleViewAllLogs = () => {
    toast.info("Opening full administrative policies audits history ledger viewer...");
  };

  const handleViewAllOrgs = () => {
    toast.info("Displaying full active/suspended corporate directories indices...");
  };

  return (
    <div className="space-y-8 select-none">
      <DashboardBreadcrumbs />

      {/* Header Info */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/30 pb-6 shrink-0 select-none">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
            Global Administration
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-relaxed max-w-2xl">
            Platform-wide health and organizational metrics
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            onClick={handleExportReport}
            className="bg-surface-container-low border border-outline-variant hover:bg-surface-container hover:border-primary px-4 py-2.5 rounded-lg text-xs font-bold text-on-surface flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Download className="size-3.5 shrink-0" />
            Export Report
          </Button>
          
          <Button
            onClick={handleRefreshSync}
            disabled={isRefreshing}
            className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={cn("size-3.5 shrink-0", isRefreshing && "animate-spin")} />
            {isRefreshing ? "Syncing..." : "Refresh Sync"}
          </Button>
        </div>
      </section>

      {/* KPI stats display */}
      <KpiCards />

      {/* Bento Visualization row layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
        
        {/* Recharts Server Compute utilization chart (Col span 2) */}
        <div className="lg:col-span-2">
          <ServerLoadChart />
        </div>

        {/* System gateway and nodes statuses details panel */}
        <div className="lg:col-span-1">
          <SystemHealthPanel 
            metrics={healthMetrics} 
            onViewLogs={handleViewHealthLogs} 
          />
        </div>

      </div>

      {/* Organization Indices and Audit History layout grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch shrink-0">
        
        {/* Active Recent Enterprise organizations */}
        <div className="lg:col-span-8">
          <OrganizationsTable 
            initialOrgs={INITIAL_ORGS} 
            onViewAllClick={handleViewAllOrgs} 
          />
        </div>

        {/* System audit log vertical timelines */}
        <div className="lg:col-span-4">
          <AuditLog 
            logs={MOCK_AUDIT_LOGS} 
            onViewAllLogs={handleViewAllLogs} 
          />
        </div>

      </div>

    </div>
  );
}
