"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Boxes, ShieldAlert, Cloud, Cpu, Database, Users } from "lucide-react";
import DashboardHeader from "@/components/dashboard/header";
import InferenceLoadsChart from "@/components/dashboard/chart";
import ActivityPanel from "@/components/dashboard/activity-panel";
import ProjectCard from "@/components/dashboard/project-card";
import MetricCard from "@/components/dashboard/metric-card";
import { Button } from "@/components/ui/button";
import { useNewProject } from "@/providers/new-project-provider";
import EmptyState from "@/components/common/empty-state";
import { useWorkspace } from "@/providers/workspace-provider";

interface ProjectItem {
  project_id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
  tags: string[];
}

export default function DashboardPage() {
  const { activeWorkspace } = useWorkspace();
  const { openNewProject } = useNewProject();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [computeUsage, setComputeUsage] = useState("0 TFlops");
  const [storageUsed, setStorageUsed] = useState("0 KB");
  const [activeAgents, setActiveAgents] = useState(0);
  const [loading, setLoading] = useState(true);

  const activeWorkspaceId = activeWorkspace?.workspace_id || "default-ws";

  useEffect(() => {
    if (!activeWorkspaceId) return;

    setLoading(true);
    // 1. Fetch Projects
    fetch(`/workspaces/projects?workspace_id=${activeWorkspaceId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data) {
          setProjects(data.data);
        }
      })
      .catch((err) => console.error("Error fetching workspace projects", err))
      .finally(() => setLoading(false));

    // 2. Fetch Metrics & Health
    fetch("/api/platform/metrics")
      .then((res) => res.json())
      .then((metrics) => {
        const reqs = metrics.api_requests_total || 0;
        setComputeUsage(`${(reqs * 0.12).toFixed(1)} GFlops`);
      })
      .catch((err) => console.error("Error fetching metrics", err));

    fetch(`/product/workspace/${activeWorkspaceId}/dashboard`)
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data && data.data.stats) {
          const stats = data.data.stats;
          const kb = (stats.storage_used_bytes / 1024).toFixed(1);
          setStorageUsed(`${kb} KB`);
        }
      })
      .catch((err) => console.error("Error fetching workspace dashboard stats", err));

    fetch("/api/health")
      .then((res) => res.json())
      .then((health) => {
        if (health.agents) {
          const count = Object.values(health.agents).filter(v => v === "healthy").length;
          setActiveAgents(count);
        }
      })
      .catch((err) => console.error("Error fetching system health", err));

  }, [activeWorkspaceId]);

  const metrics = [
    {
      title: "Compute Usage",
      value: computeUsage,
      icon: Cpu,
    },
    {
      title: "Storage Index",
      value: storageUsed,
      icon: Database,
    },
    {
      title: "Active Agents",
      value: (
        <span className="flex items-baseline">
          {activeAgents} 
          <span className="text-green-400 text-xs font-normal ml-1.5 lowercase">
            online
          </span>
        </span>
      ),
      icon: Users,
    }
  ];

  return (
    <div className="p-6 md:p-8 space-y-6 md:space-y-8 flex flex-col justify-between min-h-[calc(100vh-64px)] relative">
      
      <div className="space-y-6 md:space-y-8">
        {/* Dashboard Header */}
        <DashboardHeader />

        {/* Inference Load Chart & Live Activity Feed Grid */}
        <div className="grid grid-cols-12 gap-6">
          <InferenceLoadsChart />
          <ActivityPanel />
        </div>

        {/* Active Projects Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-on-surface tracking-tight">
              Active Projects
            </h3>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center">
              <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            </div>
          ) : projects.length === 0 ? (
            <div className="py-6">
              <EmptyState
                icon={Boxes}
                title="No Active Projects"
                description="Create your first workspace pipeline container to start running inference jobs, deploying autonomous agents, and orchestrating models."
                actionLabel="Create New Project"
                onAction={openNewProject}
                accentColor="primary"
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <Link
                  key={project.project_id}
                  href="/dashboard/workflows"
                  className="block h-full cursor-pointer hover:no-underline"
                >
                  <ProjectCard
                    title={project.name}
                    description={project.description || "Active collaboration project"}
                    status="Active"
                    statusColorClass="text-green-400"
                    progress={100}
                    progressBarColorClass="bg-primary"
                    icon={Boxes}
                    iconBgClass="bg-primary/10 border-primary/20"
                    members={[]}
                    extraMembers={0}
                  />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Bottom Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          {metrics.map((metric) => (
            <MetricCard
              key={metric.title}
              title={metric.title}
              value={metric.value}
              icon={metric.icon}
            />
          ))}
        </div>
      </div>

      {/* Footer Branding */}
      <footer className="py-6 mt-8 border-t border-outline-variant/30 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-medium text-on-surface-variant">
        <span>© 2024 Nexus AI Enterprise</span>
        <div className="flex gap-6">
          <Link href="#" className="hover:text-on-surface transition-colors">
            API Docs
          </Link>
          <Link href="#" className="hover:text-on-surface transition-colors">
            System Status
          </Link>
          <Link href="#" className="hover:text-on-surface transition-colors">
            Support
          </Link>
        </div>
      </footer>

      {/* Floating Action Button (FAB) on Mobile */}
      <Button
        aria-label="Create New Project"
        onClick={openNewProject}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-2xl flex items-center justify-center active:scale-90 transition-all z-50 md:hidden cursor-pointer border-none shadow-primary/20 hover:scale-105"
      >
        <Plus className="size-6" />
      </Button>

    </div>
  );
}
