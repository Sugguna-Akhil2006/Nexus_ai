"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Bot,
  CheckCircle2,
  Circle,
  Clock,
  ExternalLink,
  FileDown,
  Settings,
  Share2,
  Shield,
  Users,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ProjectData {
  id: string;
  name: string;
  templateId: string;
  templateName: string;
  category: string;
  createdAt: string;
}

// ─── Template-driven config ───────────────────────────────────────────────────

const TEMPLATE_CONFIGS: Record<string, {
  accentClass: string;
  gradientClass: string;
  statusLabel: string;
  agentsOnline: number;
  requestsProcessed: string;
  uptime: string;
  checklistItems: string[];
  recentEvents: { label: string; time: string; type: "success" | "info" | "warning" }[];
}> = {
  "chat-assistant": {
    accentClass: "text-primary",
    gradientClass: "from-primary/20 via-primary/5 to-transparent",
    statusLabel: "Provisioning",
    agentsOnline: 2,
    requestsProcessed: "0 / day",
    uptime: "100%",
    checklistItems: [
      "Configure system prompt & persona",
      "Connect knowledge base documents",
      "Set memory retention window",
      "Deploy to production endpoint",
    ],
    recentEvents: [
      { label: "Workspace provisioned", time: "just now", type: "success" },
      { label: "Default NLP model assigned", time: "just now", type: "info" },
      { label: "API endpoint generated", time: "just now", type: "info" },
    ],
  },
  "data-pipeline": {
    accentClass: "text-secondary",
    gradientClass: "from-secondary/20 via-secondary/5 to-transparent",
    statusLabel: "Initializing",
    agentsOnline: 1,
    requestsProcessed: "0 records",
    uptime: "99.9%",
    checklistItems: [
      "Define source data connectors",
      "Configure vector embedding model",
      "Set indexing schedule",
      "Link downstream consumers",
    ],
    recentEvents: [
      { label: "Pipeline schema created", time: "just now", type: "success" },
      { label: "Queue worker allocated", time: "just now", type: "info" },
      { label: "Storage bucket linked", time: "just now", type: "success" },
    ],
  },
  "autonomous-agent": {
    accentClass: "text-violet-400",
    gradientClass: "from-violet-500/20 via-violet-500/5 to-transparent",
    statusLabel: "Configuring",
    agentsOnline: 3,
    requestsProcessed: "0 tasks",
    uptime: "100%",
    checklistItems: [
      "Define agent goal & constraints",
      "Attach tools (search, code, file)",
      "Set planning strategy (ReAct / CoT)",
      "Run sandbox test task",
    ],
    recentEvents: [
      { label: "Agent runtime allocated", time: "just now", type: "success" },
      { label: "Tool registry connected", time: "just now", type: "info" },
      { label: "Sandbox environment ready", time: "just now", type: "success" },
    ],
  },
  "security-guardrail": {
    accentClass: "text-orange-400",
    gradientClass: "from-orange-500/20 via-orange-500/5 to-transparent",
    statusLabel: "Provisioning",
    agentsOnline: 1,
    requestsProcessed: "0 audits",
    uptime: "100%",
    checklistItems: [
      "Configure injection detection rules",
      "Set alert thresholds & severity",
      "Attach to upstream LLM endpoint",
      "Run baseline safety audit",
    ],
    recentEvents: [
      { label: "Guardrail ruleset initialized", time: "just now", type: "success" },
      { label: "Safety classifier loaded", time: "just now", type: "info" },
      { label: "Monitoring dashboard ready", time: "just now", type: "success" },
    ],
  },
  "analytics-dashboard": {
    accentClass: "text-cyan-400",
    gradientClass: "from-cyan-500/20 via-cyan-500/5 to-transparent",
    statusLabel: "Initializing",
    agentsOnline: 0,
    requestsProcessed: "0 events",
    uptime: "N/A",
    checklistItems: [
      "Connect inference endpoint for tracking",
      "Configure metric dimensions",
      "Set up alert thresholds",
      "Share dashboard with team",
    ],
    recentEvents: [
      { label: "Analytics schema created", time: "just now", type: "success" },
      { label: "Metrics engine online", time: "just now", type: "info" },
      { label: "Retention policy set to 90 days", time: "just now", type: "info" },
    ],
  },
  "custom-workflow": {
    accentClass: "text-green-400",
    gradientClass: "from-green-500/20 via-green-500/5 to-transparent",
    statusLabel: "Draft",
    agentsOnline: 0,
    requestsProcessed: "0 runs",
    uptime: "N/A",
    checklistItems: [
      "Open workflow canvas",
      "Add trigger node",
      "Connect agent & tool nodes",
      "Deploy workflow",
    ],
    recentEvents: [
      { label: "Blank canvas initialized", time: "just now", type: "success" },
      { label: "Workflow ID assigned", time: "just now", type: "info" },
    ],
  },
};

// ─── Metric Card ──────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  accentClass,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  accentClass: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-surface-container-low border border-outline-variant rounded-xl p-5 flex items-center gap-4"
    >
      <div className="w-10 h-10 rounded-lg bg-surface-container flex items-center justify-center flex-shrink-0">
        <Icon className={cn("size-5", accentClass)} />
      </div>
      <div>
        <p className="text-xs text-on-surface-variant font-medium">{label}</p>
        <p className="text-xl font-bold text-on-surface tracking-tight">{value}</p>
      </div>
    </motion.div>
  );
}

// ─── Checklist Item ───────────────────────────────────────────────────────────

function ChecklistItem({ label, index }: { label: string; index: number }) {
  const [done, setDone] = useState(false);
  return (
    <motion.li
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.05 * index, duration: 0.25 }}
      className="flex items-center gap-3 group cursor-pointer"
      onClick={() => setDone((d) => !d)}
    >
      {done ? (
        <CheckCircle2 className="size-4 text-green-400 flex-shrink-0" />
      ) : (
        <Circle className="size-4 text-outline-variant group-hover:text-on-surface-variant flex-shrink-0 transition-colors" />
      )}
      <span className={cn("text-sm transition-colors", done ? "line-through text-on-surface-variant/50" : "text-on-surface-variant group-hover:text-on-surface")}>
        {label}
      </span>
    </motion.li>
  );
}

// ─── Event Badge ──────────────────────────────────────────────────────────────

const EVENT_COLORS = {
  success: "bg-green-500/15 text-green-400 border-green-500/20",
  info: "bg-primary/10 text-primary border-primary/20",
  warning: "bg-orange-500/15 text-orange-400 border-orange-500/20",
};

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params?.projectId) return;
    const stored = sessionStorage.getItem(`nexus_project_${params.projectId}`);
    if (stored) {
      setProject(JSON.parse(stored));
    }
    setLoading(false);
  }, [params?.projectId]);

  const config = project ? (TEMPLATE_CONFIGS[project.templateId] ?? TEMPLATE_CONFIGS["custom-workflow"]) : null;

  const handleOpenWorkflow = () => {
    router.push("/dashboard/workflows");
  };

  const handleViewAgents = () => {
    router.push("/dashboard/agents");
  };

  const handleExport = () => {
    toast.promise(new Promise((res) => setTimeout(res, 1200)), {
      loading: "Preparing project export...",
      success: `"${project?.name}" exported as PDF.`,
      error: "Export failed. Try again.",
    });
  };

  const handleInvite = () => {
    toast.success("Invite link copied to clipboard!", { description: "Share it with your teammates." });
  };

  const handleSettings = () => {
    router.push("/dashboard/settings");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-64px)]">
        <div className="w-8 h-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!project || !config) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] gap-4 p-8 text-center">
        <Shield className="size-12 text-on-surface-variant/30" />
        <h2 className="text-xl font-bold text-on-surface">Project not found</h2>
        <p className="text-sm text-on-surface-variant max-w-xs">
          This project may have expired from your session. Create a new one to continue.
        </p>
        <Button onClick={() => router.push("/dashboard")} className="gap-2 bg-primary text-primary-foreground border-none cursor-pointer">
          <ArrowLeft className="size-4" /> Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-8 min-h-[calc(100vh-64px)]">

      {/* Hero Banner */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={cn(
          "relative rounded-2xl border border-outline-variant overflow-hidden",
          "bg-gradient-to-br", config.gradientClass
        )}
      >
        <div className="p-6 md:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-5">
          <div className="space-y-2">
            {/* Breadcrumb back */}
            <button
              onClick={() => router.push("/dashboard")}
              className="inline-flex items-center gap-1.5 text-xs text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer mb-1"
            >
              <ArrowLeft className="size-3" />
              Back to Dashboard
            </button>

            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl md:text-3xl font-bold text-on-surface tracking-tight leading-none">
                {project.name}
              </h1>
              <span className={cn(
                "text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border",
                "bg-surface-container/60 border-outline-variant text-on-surface-variant"
              )}>
                {project.category}
              </span>
            </div>

            <p className="text-sm text-on-surface-variant">
              Template: <span className="font-medium text-on-surface">{project.templateName}</span>
              {" · "}
              Created{" "}
              <span className="font-medium text-on-surface">
                {new Date(project.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
              </span>
            </p>

            {/* Status pill */}
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-on-surface-variant bg-surface-container/70 border border-outline-variant/50 px-3 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
              {config.statusLabel}
            </span>
          </div>

          {/* Action row */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={handleOpenWorkflow}
              className="gap-2 bg-primary text-primary-foreground font-semibold hover:bg-primary/90 active:scale-95 transition-transform cursor-pointer border-none text-sm"
            >
              <Zap className="size-4" />
              Open Workflow
            </Button>
            <Button
              variant="outline"
              onClick={handleInvite}
              className="gap-2 border-outline-variant bg-surface-container/60 hover:bg-surface-container-high text-on-surface cursor-pointer text-sm"
            >
              <Share2 className="size-4" />
              Invite
            </Button>
            <Button
              variant="outline"
              onClick={handleExport}
              className="gap-2 border-outline-variant bg-surface-container/60 hover:bg-surface-container-high text-on-surface cursor-pointer text-sm"
            >
              <FileDown className="size-4" />
              Export
            </Button>
            <Button
              variant="outline"
              onClick={handleSettings}
              className="gap-2 border-outline-variant bg-surface-container/60 hover:bg-surface-container-high text-on-surface cursor-pointer text-sm"
            >
              <Settings className="size-4" />
              Settings
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard icon={Bot} label="Agents Online" value={config.agentsOnline} accentClass={config.accentClass} />
        <StatCard icon={BarChart3} label="Requests Processed" value={config.requestsProcessed} accentClass={config.accentClass} />
        <StatCard icon={Activity} label="Uptime" value={config.uptime} accentClass={config.accentClass} />
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Getting Started Checklist */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="bg-surface-container-low border border-outline-variant rounded-xl p-6 space-y-5"
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="size-5 text-primary" />
            <h3 className="text-base font-bold text-on-surface">Getting Started</h3>
          </div>
          <ul className="space-y-3.5">
            {config.checklistItems.map((item, i) => (
              <ChecklistItem key={item} label={item} index={i} />
            ))}
          </ul>
          <Button
            onClick={handleOpenWorkflow}
            variant="outline"
            className="w-full gap-2 border-outline-variant bg-surface-container hover:bg-surface-container-high text-on-surface cursor-pointer text-sm mt-2"
          >
            <ExternalLink className="size-4" />
            Open in Workflow Builder
          </Button>
        </motion.div>

        {/* Live Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15 }}
          className="bg-surface-container-low border border-outline-variant rounded-xl p-6 space-y-5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="size-5 text-primary" />
              <h3 className="text-base font-bold text-on-surface">Activity Feed</h3>
            </div>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Live
            </span>
          </div>

          <ul className="space-y-3">
            {config.recentEvents.map((evt, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 * i + 0.2, duration: 0.2 }}
                className="flex items-center gap-3"
              >
                <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full border", EVENT_COLORS[evt.type])}>
                  {evt.type === "success" ? "OK" : evt.type === "warning" ? "WARN" : "INFO"}
                </span>
                <span className="text-sm text-on-surface-variant flex-1">{evt.label}</span>
                <span className="text-[11px] text-on-surface-variant/50 font-mono flex items-center gap-1 flex-shrink-0">
                  <Clock className="size-3" />
                  {evt.time}
                </span>
              </motion.li>
            ))}
          </ul>

          <div className="pt-2 border-t border-outline-variant/40">
            <Button
              onClick={handleViewAgents}
              variant="outline"
              className="w-full gap-2 border-outline-variant bg-surface-container hover:bg-surface-container-high text-on-surface cursor-pointer text-sm"
            >
              <Users className="size-4" />
              View Agents Dashboard
            </Button>
          </div>
        </motion.div>
      </div>

    </div>
  );
}
