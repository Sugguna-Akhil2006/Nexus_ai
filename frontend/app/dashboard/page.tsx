"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Plus, Boxes, ShieldAlert, Cloud, Cpu, Database, Users, MessageSquare, FileText, GitBranch, Bot, Zap, ArrowRight, Activity, CheckCircle2 } from "lucide-react";
import InferenceLoadsChart from "@/components/dashboard/chart";
import ActivityPanel from "@/components/dashboard/activity-panel";
import ProjectCard from "@/components/dashboard/project-card";
import MetricCard from "@/components/dashboard/metric-card";
import { Button } from "@/components/ui/button";
import { useNewProject } from "@/providers/new-project-provider";
import EmptyState from "@/components/common/empty-state";
import { useWorkspace } from "@/providers/workspace-provider";
import AnimatedCounter from "@/components/common/animated-counter";
import { SkeletonStatCard, SkeletonProjectCard, SkeletonChart, SkeletonListItem } from "@/components/common/skeleton-variants";
import { useSimulatedLoading } from "@/hooks/use-simulated-loading";
import { useRealtimeSimulation } from "@/hooks/use-realtime-simulation";
import { toast } from "sonner";
import { motion, Variants } from "framer-motion";
import { cn } from "@/lib/utils";
import PageContainer from "@/components/common/page-container";

interface ProjectItem {
  project_id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
  tags: string[];
}

// Mock Active Projects Data
const PROJECTS = [
  {
    id: "proj-1",
    title: "Data Processing Pipeline",
    description: "Autonomous data processing and routing workflow canvas.",
    status: "In Progress",
    statusColorClass: "text-primary",
    progress: 84,
    progressBarColorClass: "bg-primary",
    icon: Boxes,
    iconBgClass: "bg-primary/10 border-primary/20",
    members: [
      { name: "Alex Chen", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X" },
      { name: "Sarah Jenkins", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh" }
    ],
    extraMembers: 3,
  },
  {
    id: "proj-2",
    title: "Vanguard Guardrail",
    description: "Real-time prompt injection prevention and LLM safety layer.",
    status: "Staging",
    statusColorClass: "text-secondary",
    progress: 42,
    progressBarColorClass: "bg-secondary",
    icon: ShieldAlert,
    iconBgClass: "bg-secondary/15 border-secondary/20",
    members: [
      { name: "Marcus Aurelius", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCN4AjYH9VxqqekSZR46EWARGDW7GMXN34fjzzmPJY-B4sW93NZW3_bKE8rk8GH6Z7bRoipIGJbgqN0vtzn7xAgoHQTc6JtG3CQCfDiA9neEXuu28xGxc7wL6j9Kf9h9i4MR4U2WvxAjh9HSw6td40xcVWZ9XzdCZ2rtAJ9ktBeZegNm95Es4QadiRmjLDzYdu7-cEyX3PmeaeSC_AnC0mw4FYBiPbd4et2dqdo-rGQFmI6NeZ8QujR__Aq0aj-E6wcGGvHPbx8gVEE" }
    ],
    extraMembers: 1,
  },
  {
    id: "proj-3",
    title: "Core-Sync 2.0",
    description: "Unified vector embedding pipeline for global agent clusters.",
    status: "Active",
    statusColorClass: "text-green-400",
    progress: 96,
    progressBarColorClass: "bg-primary",
    icon: Cloud,
    iconBgClass: "bg-primary-container/20 border-primary-container/30",
    members: [
      { name: "Dina Prince", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuDvD0kvr7FE7QIJRQL9HZs04p8yaOCCyuEkJznFj0H2CiDuOh3ohnA9hKPU5n9MyCu5fVwuIsnK-pP7LCR-PvBdz3mAE2Qrmm1bX6Lwps43Uv4sL1JMbXRAf-DvOTTEiFmWPC0izk3h7-lQdyZ4GXU-s5YnVt-Uz1-AGJon-RJujjlCeVAEZvrDaqW1Q_x7poDkUXefQ_JgndojkCTwKAXQRIbCicPkaSffJNHeNnGYL0iilkCifS9fCc1VWcCXWtGa6fht0BuS6qKJ" },
      { name: "John Stewart", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuADTWQkJyCrcBfNzLgWua8xU-wSLoS4mBRmPJAOkXXNiI6psySgLavV1ddMecybd-7q9elRbTlwmWxlKjxr3FHHT5xYSlyrbidFLE16_NS6iaqQrVs70eGO2g95M6_PkS2khQZXIMjMIH70Oaj8Q08rqOzH0F8RmXifQLnBBLi0KiNCdfvzLcTaug8Nx4WKOWgxJmqKpcqTiD2huFl4At0iXjGJeXgJ8sCjRqtnJOVd3Ppku0_QYohGZpctB_esvM7LgXuueGefuPN0" },
      { name: "Wally West", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAEnZ2U0S7-nMI81nD33xTVKwg57UfvPrDUZUI5BNnA7MfYHooLqhTbejOGaSkmiGzN7wb9mV2lEhKtJ-48IPOno1WR8NuS5PZV7I2R226SZaCsHjXXS5vz9tbSBvyid-6MkDeFAE0kYYvXzSjNcWQf3DFGDqGz4ADbfSiaGDP3OsNkh0EmvpOqwVCf9v5BPx_MxrRGU1ncbF7JiovX7TgfKygx0a6jFTk5svBGlvAeg8ISiq3YR_i4uzjHEZVIsMyyHMHql5ESvtr5" }
    ],
    extraMembers: 8,
  }
];

// Quick action buttons configuration
const QUICK_ACTIONS = [
  { label: "New Chat", icon: MessageSquare, href: "/dashboard/chat", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  { label: "Upload Doc", icon: FileText, href: "/dashboard/documents", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { label: "Build Workflow", icon: GitBranch, href: "/dashboard/workflows", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  { label: "Deploy Agent", icon: Bot, href: "/dashboard/agents", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
];

const AGENT_STATUSES = [
  { name: "Parser_Agent_Core", latency: "14ms", tasks: 82440, status: "active" },
  { name: "Evaluator_Node_APAC", latency: "28ms", tasks: 42109, status: "active" },
  { name: "GitHub_Sync_Agent", latency: "112ms", tasks: 8122, status: "warning" },
];

export default function DashboardPage() {
  const { activeWorkspace } = useWorkspace();
  const { openNewProject } = useNewProject();
  
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [computeUsage, setComputeUsage] = useState("84.2 TFlops");
  const [activeAgents, setActiveAgents] = useState(3);
  const [apiCalls, setApiCalls] = useState(1482);
  const [loading, setLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);

  const { isLoading } = useSimulatedLoading({ data: true, delayMs: 500 });

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
      .catch((err) => console.warn("Workspace projects endpoint unavailable, using mock projects instead.", err))
      .finally(() => setLoading(false));

    // 2. Fetch Metrics & Health
    fetch("/api/platform/metrics")
      .then((res) => res.json())
      .then((metrics) => {
        const reqs = metrics.api_requests_total || 1482;
        setApiCalls(reqs);
        const agentsCount = metrics.active_agents || 3;
        setActiveAgents(agentsCount);
        if (metrics.compute_tflops) {
          setComputeUsage(`${metrics.compute_tflops} TFlops`);
        }
      })
      .catch((err) => console.warn("Platform metrics endpoint unavailable, using mock telemetry indicators.", err));
  }, [activeWorkspaceId]);

  // Real-time animation simulator
  const simulatedApiCalls = useRealtimeSimulation({
    initialValue: 1482,
    min: 1400,
    max: 1650,
    intervalMs: 3000
  });

  const displayApiCalls = apiCalls === 1482 ? simulatedApiCalls : apiCalls;

  const handleCreateProjectMock = () => {
    openNewProject();
  };

  // Framer Motion staggered animations
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } },
  };

  const toolbarActions = (
    <Button
      onClick={handleCreateProjectMock}
      className="bg-primary hover:opacity-90 active:scale-98 text-primary-foreground font-bold px-4 py-2.5 rounded-lg text-xs cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
    >
      <Plus className="size-4 shrink-0" />
      Create Project
    </Button>
  );

  return (
    <PageContainer
      title={activeWorkspace ? `${activeWorkspace.name} Platform` : "Platform Control Console"}
      description="Orchestrate and supervise automated workflows, document analysis parsers, and regional agent nodes."
      toolbar={toolbarActions}
    >
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-8 min-h-0 flex-grow"
      >
        {/* Quick action buttons row */}
        <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {QUICK_ACTIONS.map((action) => (
            <Link key={action.label} href={action.href} className="no-underline block">
              <div className={cn(
                "rounded-xl border p-4 hover:border-primary/40 hover:bg-surface-container transition-all hover:translate-y-[-2px] cursor-pointer flex items-center gap-4.5 group select-none shadow-sm",
                action.bg
              )}>
                <div className={cn("p-2 rounded-lg bg-surface/50 border border-outline-variant/30 shrink-0 group-hover:scale-105 transition-transform", action.color)}>
                  <action.icon className="size-4.5" />
                </div>
                <div className="min-w-0">
                  <span className="text-xs md:text-sm font-bold text-on-surface truncate block">{action.label}</span>
                  <span className="text-[10px] text-on-surface-variant/70 font-medium">Quick Start</span>
                </div>
              </div>
            </Link>
          ))}
        </motion.div>

        {/* Inference Load Chart & Live Activity Feed Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-12 gap-6">
          {isLoading ? (
            <>
              <div className="col-span-12 lg:col-span-8"><SkeletonChart height="h-56" /></div>
              <div className="col-span-12 lg:col-span-4 space-y-3">
                {[1,2,3,4].map(i => <SkeletonListItem key={i} />)}
              </div>
            </>
          ) : (
            <>
              <InferenceLoadsChart />
              <ActivityPanel />
            </>
          )}
        </motion.div>

        {/* Active Projects Grid */}
        <motion.div variants={itemVariants} className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-on-surface tracking-tight">
              Active Projects
            </h3>
            <Button 
              variant="ghost" 
              size="xs" 
              onClick={() => setIsEmpty(!isEmpty)} 
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors bg-transparent border-none"
            >
              {isEmpty ? "● Show Mock Projects" : "○ Simulate Empty State"}
            </Button>
          </div>

          {loading && projects.length === 0 ? (
            <div className="py-12 flex justify-center">
              <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            </div>
          ) : (isEmpty || (projects.length === 0 && !loading)) ? (
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
          ) : isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1,2,3].map(i => <SkeletonProjectCard key={i} />)}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.length > 0 ? (
                projects.map((project) => (
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
                ))
              ) : (
                PROJECTS.map((project) => (
                  <Link
                    key={project.id}
                    href="/dashboard/workflows"
                    className="block h-full cursor-pointer hover:no-underline"
                  >
                    <ProjectCard
                      title={project.title}
                      description={project.description}
                      status={project.status as any}
                      statusColorClass={project.statusColorClass}
                      progress={project.progress}
                      progressBarColorClass={project.progressBarColorClass}
                      icon={project.icon}
                      iconBgClass={project.iconBgClass}
                      members={project.members}
                      extraMembers={project.extraMembers}
                    />
                  </Link>
                ))
              )}
            </div>
          )}
        </motion.div>

        {/* Bottom Metrics + AI Agent Status Row */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-4">
          {/* Metrics Cards */}
          <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            {isLoading ? (
              [1,2,3].map(i => <SkeletonStatCard key={i} />)
            ) : (
              <>
                <MetricCard
                  title="Compute Usage"
                  value={<AnimatedCounter value={84.2} suffix=" TFlops" decimals={1} />}
                  icon={Cpu}
                />
                <MetricCard
                  title="API Calls / min"
                  value={<AnimatedCounter value={displayApiCalls} formatted />}
                  icon={Zap}
                />
                <MetricCard
                  title="Active Agents"
                  value={
                    <span className="flex items-baseline">
                      <AnimatedCounter value={activeAgents} />
                      <span className="text-green-400 text-xs font-normal ml-1.5 lowercase">
                        online
                      </span>
                    </span>
                  }
                  icon={Users}
                />
              </>
            )}
          </div>

          {/* AI Agent Status Widget */}
          <div className="lg:col-span-4 bg-surface-container-low border border-outline-variant rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-bold text-on-surface flex items-center gap-2">
                <Activity className="size-4 text-primary" />
                Agent Health
              </h4>
              <Link href="/dashboard/agents" className="text-[10px] font-semibold text-primary hover:text-primary/80 transition-colors">
                View All →
              </Link>
            </div>
            <div className="space-y-3">
              {AGENT_STATUSES.map((agent) => (
                <div key={agent.name} className="flex items-center gap-3 p-2.5 rounded-lg bg-surface-container/50 hover:bg-surface-container transition-colors">
                  {/* Health dot */}
                  <div className={cn(
                    "w-2 h-2 rounded-full shrink-0",
                    agent.status === "active" ? "bg-green-400" : "bg-amber-400",
                    agent.status === "active" ? "shadow-[0_0_6px_rgba(74,222,128,0.4)]" : "shadow-[0_0_6px_rgba(251,191,36,0.4)]"
                  )} />
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-semibold text-on-surface truncate block">{agent.name}</span>
                    <span className="text-[10px] text-on-surface-variant font-mono">{agent.latency} · {agent.tasks.toLocaleString()} tasks</span>
                  </div>
                  <CheckCircle2 className={cn(
                    "size-3.5 shrink-0",
                    agent.status === "active" ? "text-green-400" : "text-amber-400"
                  )} />
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Footer Branding */}
      <footer className="py-6 mt-8 border-t border-outline-variant/30 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-medium text-on-surface-variant">
        <span>© 2026 Nexus AI Enterprise</span>
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
    </PageContainer>
  );
}
