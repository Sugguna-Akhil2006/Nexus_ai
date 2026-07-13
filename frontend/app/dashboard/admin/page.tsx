"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Download, RefreshCw, Cpu, Globe, Database, Network, ShieldCheck, Play, Power, AlertTriangle, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import KpiCards from "@/components/admin/kpi-cards";
import dynamic from "next/dynamic";
const ServerLoadChart = dynamic(() => import("@/components/admin/server-load-chart"), { ssr: false });
import SystemHealthPanel, { HealthMetric } from "@/components/admin/system-health-panel";
import OrganizationsTable, { OrganizationItem } from "@/components/admin/organizations-table";
import AuditLog, { AuditLogItem } from "@/components/admin/audit-log";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useAuth } from "@/providers/auth-provider";
import PageContainer from "@/components/common/page-container";

interface ClusterInfo {
  id: string;
  name: string;
  region: string;
  activeAgents: number;
  health: string;
  load: string;
  status: "Online" | "Degraded" | "Offline";
}

const INITIAL_CLUSTERS: ClusterInfo[] = [
  { id: "c-1", name: "Cluster APAC-1", region: "Singapore (ap-southeast-1)", activeAgents: 28, health: "99.8%", load: "42%", status: "Online" },
  { id: "c-2", name: "Cluster US-East", region: "N. Virginia (us-east-1)", activeAgents: 142, health: "100%", load: "78%", status: "Online" },
  { id: "c-3", name: "Cluster EU-West", region: "Ireland (eu-west-1)", activeAgents: 64, health: "98.2%", load: "89%", status: "Degraded" },
];

const INITIAL_HEALTH_METRICS: HealthMetric[] = [
  { id: "h-1", name: "API Gateway", status: "Active", metricText: "12ms latency" },
  { id: "h-2", name: "Compute Nodes", status: "Active", metricText: "42% utilized" },
  { id: "h-3", name: "Vector Database", status: "Active", metricText: "Healthy" },
  { id: "h-4", name: "CDN Edge", status: "Warning", metricText: "Degraded" },
];

const INITIAL_ORGS: OrganizationItem[] = [
  { id: "org-1", name: "Vortex Systems", planType: "Enterprise", status: "Active", lastActivity: "2 mins ago", colorClass: "bg-indigo-500/20 text-indigo-400", letter: "V" },
  { id: "org-2", name: "Kinetix Bio", planType: "Scale", status: "Active", lastActivity: "14 mins ago", colorClass: "bg-orange-500/20 text-orange-400", letter: "K" },
  { id: "org-3", name: "Nebula Corp", planType: "Enterprise", status: "Suspended", lastActivity: "2 days ago", colorClass: "bg-red-500/20 text-red-400", letter: "N" },
  { id: "org-4", name: "Artemis AI", planType: "Scale", status: "Active", lastActivity: "45 mins ago", colorClass: "bg-emerald-500/20 text-emerald-400", letter: "A" },
];

const MOCK_AUDIT_LOGS: AuditLogItem[] = [
  { id: "audit-1", title: "Policy Update", description: "Admin changed auth protocols for Vortex Systems.", timestampText: "12:44 PM • J. Miller", iconType: "security" },
  { id: "audit-2", title: "User Provisioned", description: "3 new seats added to Artemis AI Enterprise plan.", timestampText: "11:30 AM • System", iconType: "user" },
  { id: "audit-3", title: "Access Denied", description: "Multiple failed login attempts detected on Root Admin.", timestampText: "10:05 AM • GuardRail", iconType: "warning" },
  { id: "audit-4", title: "Cluster Snapshot", description: "Manual backup initiated for US-EAST-1 cluster nodes.", timestampText: "09:15 AM • R. Chen", iconType: "cloud" },
];

export default function AdminDashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && (!user || user.role !== "Admin")) {
      router.replace("/dashboard");
    }
  }, [user, authLoading, router]);

  const [healthMetrics, setHealthMetrics] = useState<HealthMetric[]>(INITIAL_HEALTH_METRICS);
  const [organizations, setOrganizations] = useState<OrganizationItem[]>(INITIAL_ORGS);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>(MOCK_AUDIT_LOGS);
  const [clusters, setClusters] = useState<ClusterInfo[]>(INITIAL_CLUSTERS);
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
        setOrganizations(mappedOrgs.length > 0 ? mappedOrgs : INITIAL_ORGS);
      }
    } catch (e) {
      console.warn("Failed to load live admin statistics, using mock datasets instead.", e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (user && user.role === "Admin") {
      loadAdminData();
    }
  }, [user]);

  const handleExportReport = () => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: "Compiling global administration system logs audit report...",
        success: "Platform security audit reports downloaded successfully.",
        error: "Failed to assemble logs."
      }
    );
  };

  const handleViewHealthLogs = () => {
    toast.info("Navigating to platform orchestration systems metrics registry...");
  };

  const handleViewAllLogs = () => {
    toast.info("Opening raw system transaction audit records log streams...");
  };

  const handleViewAllOrgs = () => {
    toast.info("Displaying full active/suspended corporate directories indices...");
  };

  const handleRestartCluster = (name: string) => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 2000)),
      {
        loading: `Initiating rolling reboot sequence for ${name}...`,
        success: `${name} back online. All node processes hot-swapped successfully.`,
        error: "Reboot failed."
      }
    );
  };

  const toolbarActions = (
    <>
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
    </>
  );

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
    <PageContainer
      title="Global Administration"
      description="Platform-wide health, organizational metrics, and live agent cluster logs control."
      icon={<Globe className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
      {/* KPI stats display */}
      <KpiCards totalWorkspaces={totalWorkspaces} totalUsers={totalUsers} uptimeSeconds={uptimeSeconds} />

      {/* Bento Visualization row layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
        {/* Recharts Server Compute utilization chart */}
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

      {/* Agent Cluster Status section */}
      <section className="bg-surface-container border border-outline-variant rounded-xl p-6 space-y-4 shadow-sm select-none">
        <div>
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
            <Globe className="size-4.5 text-primary" />
            Regional Agent Cluster Status
          </h3>
          <p className="text-xs text-on-surface-variant mt-1.5">
            Monitor active deployment agents, regional resource utilization loads, and hot-swap compute nodes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {clusters.map((c) => (
            <div key={c.id} className="bg-surface-container-low border border-outline-variant rounded-xl p-4 flex flex-col justify-between gap-4">
              <div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-on-surface">{c.name}</span>
                  <span className={cn(
                    "text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border flex items-center gap-1",
                    c.status === "Online" ? "bg-green-500/10 text-green-400 border-green-500/20" :
                    c.status === "Degraded" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                    "bg-red-500/10 text-red-400 border-red-500/20"
                  )}>
                    <span className={cn("w-1 h-1 rounded-full", c.status === "Online" ? "bg-green-400 animate-pulse" : "bg-amber-400")} />
                    {c.status}
                  </span>
                </div>
                <span className="text-[10px] text-on-surface-variant/60 block mt-1">{c.region}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 border-t border-b border-outline-variant/30 py-2.5 my-1.5 text-[10px] font-mono">
                <div>
                  <span className="text-on-surface-variant block text-[8px] font-bold uppercase">Agents</span>
                  <span className="text-on-surface font-semibold">{c.activeAgents}</span>
                </div>
                <div>
                  <span className="text-on-surface-variant block text-[8px] font-bold uppercase">Health</span>
                  <span className="text-on-surface font-semibold">{c.health}</span>
                </div>
                <div>
                  <span className="text-on-surface-variant block text-[8px] font-bold uppercase">Load</span>
                  <span className="text-on-surface font-semibold">{c.load}</span>
                </div>
              </div>

              <Button
                variant="outline"
                size="xs"
                onClick={() => handleRestartCluster(c.name)}
                className="w-full flex items-center gap-1 text-[10px] hover:text-red-400 hover:border-red-500/40 cursor-pointer"
              >
                <Power className="size-3 text-red-400" />
                Rolling Reboot
              </Button>
            </div>
          ))}
        </div>
      </section>

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
    </PageContainer>
  );
}
