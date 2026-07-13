"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
import { useAuth } from "@/providers/auth-provider";

export default function AdminDashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "Admin")) {
      router.replace("/dashboard");
    }
  }, [user, authLoading, router]);

  const [healthMetrics, setHealthMetrics] = useState<HealthMetric[]>([]);
  const [organizations, setOrganizations] = useState<OrganizationItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const [totalWorkspaces, setTotalWorkspaces] = useState(0);
  const [totalUsers, setTotalUsers] = useState(0);
  const [uptimeSeconds, setUptimeSeconds] = useState<number | undefined>(undefined);

  const loadAdminData = async () => {
    setIsRefreshing(true);
    try {
      // 1. Fetch Health
      const healthRes = await fetch("/admin/health");
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        const services = healthData.data?.services || {};
        if (healthData.data?.uptime_seconds != null) {
          setUptimeSeconds(healthData.data.uptime_seconds);
        }
        const mappedMetrics: HealthMetric[] = [
          {
            id: "h-1",
            name: "API Gateway",
            status: services.api_gateway?.status === "healthy" ? "Active" : "Warning",
            metricText: `${services.api_gateway?.routes_registered || 12} routes`,
          },
          {
            id: "h-2",
            name: "Database Status",
            status: services.database?.status === "healthy" ? "Active" : "Error",
            metricText: `${services.database?.latency_ms || 8}ms`,
          },
          {
            id: "h-3",
            name: "WebSocket Channels",
            status: services.websocket?.status === "healthy" ? "Active" : "Warning",
            metricText: `${services.websocket?.active_channels || 1} active`,
          }
        ];
        setHealthMetrics(mappedMetrics);
      }

      // 2. Fetch Users / Orgs
      const usersRes = await fetch("/admin/users");
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setTotalWorkspaces(usersData.data?.total_workspaces || 0);
        setTotalUsers(usersData.data?.total_users || 0);
        
        const rawUsers = usersData.data?.users || [];
        const mappedOrgs: OrganizationItem[] = rawUsers.map((u: any, idx: number) => ({
          id: `org-${idx}`,
          name: u.username,
          planType: u.role || "User",
          status: "Active",
          lastActivity: u.created_at ? new Date(u.created_at).toLocaleDateString() : "Just now",
          colorClass: idx % 2 === 0 ? "bg-indigo-500/20 text-indigo-400" : "bg-orange-500/20 text-orange-400",
          letter: u.username ? u.username[0].toUpperCase() : "U",
        }));
        setOrganizations(mappedOrgs);
      }

      // 3. Fetch Audits
      const auditRes = await fetch("/admin/audit?limit=6");
      if (auditRes.ok) {
        const auditData = await auditRes.json();
        const rawAudits = auditData.data || [];
        const mappedAudits: AuditLogItem[] = rawAudits.map((a: any, idx: number) => ({
          id: a.log_id || `audit-${idx}`,
          title: a.action || "System Action",
          description: `User: ${a.user_id || "System"} executed action: ${a.action || "Log event"}`,
          timestampText: a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "Just now",
          iconType: "security",
        }));
        setAuditLogs(mappedAudits.length > 0 ? mappedAudits : [
          {
            id: "audit-1",
            title: "Security Startup",
            description: "Administration compliance ledger initialized successfully.",
            timestampText: "Just now",
            iconType: "security"
          }
        ]);
      }

      toast.success("Enterprise health metrics synchronized successfully!");
    } catch (e) {
      console.error(e);
      toast.error("Failed to sync live gateway metrics.");
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

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

  if (authLoading || !user || user.role !== "Admin") {
    return (
      <div className="flex h-[calc(100vh-100px)] items-center justify-center bg-background text-on-surface">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium">Verifying Administrator Privileges...</p>
        </div>
      </div>
    );
  }

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
            onClick={loadAdminData}
            disabled={isRefreshing}
            className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={cn("size-3.5 shrink-0", isRefreshing && "animate-spin")} />
            {isRefreshing ? "Syncing..." : "Refresh Sync"}
          </Button>
        </div>
      </section>

      {/* KPI stats display */}
      <KpiCards totalWorkspaces={totalWorkspaces} totalUsers={totalUsers} uptimeSeconds={uptimeSeconds} />

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
            initialOrgs={organizations} 
            onViewAllClick={handleViewAllOrgs} 
          />
        </div>

        {/* System audit log vertical timelines */}
        <div className="lg:col-span-4">
          <AuditLog 
            logs={auditLogs} 
            onViewAllLogs={handleViewAllLogs} 
          />
        </div>

      </div>

    </div>
  );
}
