"use client";

import { useState, useEffect } from "react";
import { Search, Bot, Sliders } from "lucide-react";
import AgentFilters, { FilterValue } from "@/components/agents/agent-filters";
import AgentCard, { AgentData } from "@/components/agents/agent-card";
import CreateAgentCard from "@/components/agents/create-agent-card";
import StatsBar from "@/components/agents/stats-bar";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import PageContainer from "@/components/common/page-container";

// Initial mock agents dataset with runs count and error rate statistics
const INITIAL_AGENTS: AgentData[] = [
  {
    id: "agent-1",
    name: "Grover Optimizer Bot",
    description: "Analyzing Grover search transpilations depth for NISQ devices. Optimizing phase diffusion gates.",
    status: "active",
    iconType: "code",
    metrics: {
      key1: "Complexity",
      val1: "O(sqrt(N))",
      key2: "Runs",
      val2: "14.2k jobs",
    },
    health: "healthy",
    runsCount: 14209,
    errorRate: "0.02%",
  },
  {
    id: "agent-2",
    name: "QAOA Solver Agent",
    description: "Graph maximum cut problem solver using QAOA variational layers optimization step methods.",
    status: "active",
    iconType: "analytics",
    metrics: {
      key1: "Optima",
      val1: "98.4% Acc",
      key2: "Cost Factor",
      val2: "0.002",
      val2Color: "green",
    },
    health: "healthy",
    runsCount: 8904,
    errorRate: "1.25%",
  },
  {
    id: "agent-3",
    name: "GuardRail Policy Gate",
    description: "Verifying relational datasets query filters conform with OWASP top 10 sanitizations.",
    status: "active",
    iconType: "shield",
    metrics: {
      key1: "Audit Level",
      val1: "High Threat",
      key2: "Anomalies",
      val2: "0",
      val2Color: "green",
    },
    health: "healthy",
    runsCount: 22490,
    errorRate: "0.0%",
  },
  {
    id: "agent-4",
    name: "Cloud FinOps Broker",
    description: "Monitoring APAC and US regional server load. Auto-routing workflows for optimal costing.",
    status: "draft",
    iconType: "cloud",
    metrics: {
      key1: "Cloud",
      val1: "AWS, Azure",
      key2: "Savings",
      val2: "24% MoM",
      val2Color: "green",
    },
    health: "healthy",
    runsCount: 3824,
    errorRate: "0.15%",
  },
];

const TEAM_AVATARS = [
  "https://lh3.googleusercontent.com/aida-public/AB6AXuCH8hs7VjzQp-v6XU8c99znid5XEHV4JB_-WEPJ49g6YQjyesZN0LwaaVHriJAWBmo-_9YJHekWtFSBSgBEaF85zp0swkRN1cx89tOPtzjKsrePMiWB1TSURPMNrxzYHgC5ZHzdmjkpJLteBt5dUqYSrFx0BSl-9rD66uDU2096SehL_rAjcu4sUCvD4uk7CRnwfVzE-nndk_pN3WwSnXC7kUtOIcRiNoHzdrx5WFDDlYpVE_dB8QeMlkCd_rOpi1i5laBB5HkrDtwC",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuCCOi1jGQaPkQLqV4ZhsQb7DInTmE1U9dJA5QocSEs35Dq340lq31HdjyZ9ZFYo7x71o41gR3A0Cs0F4XypUgIhbyLniuEHUQlnprscIT-Nt58CZO-yxecM1I8o1PAlngGCtG1WYEgI40zHc0RzoKelNzNdW0Dlc2UZ20nNOtDfPTx-3goVvZ9KDBM-BxOpwn4G03Zy6zfSF_34K_2_mjaOK37LaqH7q9RcQScdCtIwJW4S2l5FkjsJYgI-FSxPkMefOEzgK4NuywG3",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh",
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<FilterValue>("all");
  const [isEmpty, setIsEmpty] = useState(false);

  // Form states inside creation Dialog
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCaps, setNewCaps] = useState("");
  const [newIconType, setNewIconType] = useState<AgentData["iconType"]>("code");

  useEffect(() => {
    fetch("/api/agents")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch agents");
        return res.json();
      })
      .then((data) => {
        if (data && data.agents) {
          const apiAgents = data.agents.map((a: any) => ({
            id: a.id,
            name: a.name,
            description: a.description,
            status: a.status.toLowerCase() === "active" ? "active" : "draft",
            iconType: a.capabilities.includes("GITHUB_INTELLIGENCE") || a.capabilities.includes("CODE_ANALYSIS") ? "code" : a.capabilities.includes("SECURITY") ? "shield" : "analytics",
            metrics: {
              key1: "Capabilities",
              val1: a.capabilities.join(", "),
              key2: "Latency",
              val2: `~${a.response_time_ms}ms`,
            },
            health: "healthy",
            runsCount: 14209,
            errorRate: "0.02%",
          }));
          setAgents(apiAgents.length > 0 ? apiAgents : INITIAL_AGENTS);
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch live agents from registry, falling back to mock dataset.", err);
      });
  }, []);

  const handleStatusToggle = (id: string) => {
    setAgents((prev) =>
      prev.map((agent) => {
        if (agent.id === id) {
          const nextHealth = agent.health === "stopped" ? "healthy" : "stopped";
          toast.success(
            `Agent "${agent.name}" state toggled to: ${
              nextHealth === "healthy" ? "RUNNING" : "STOPPED"
            }`
          );
          return { ...agent, health: nextHealth };
        }
        return agent;
      })
    );
  };

  const handleConfigure = (id: string) => {
    const agent = agents.find((a) => a.id === id);
    if (agent) {
      toast.info(`Opening configuration panel for: ${agent.name}`);
    }
  };

  const handleDeleteAgent = (id: string) => {
    const agent = agents.find((a) => a.id === id);
    setAgents((prev) => prev.filter((a) => a.id !== id));
    if (agent) {
      toast.error(`Agent "${agent.name}" removed from platform directory.`);
    }
  };

  // Filter and search computation logic
  const filteredAgents = agents.filter((agent) => {
    const queryMatch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.metrics.val1.toLowerCase().includes(searchQuery.toLowerCase());

    if (filter === "all") return queryMatch;
    if (filter === "production") return queryMatch && agent.status === "active";
    if (filter === "drafts") return queryMatch && agent.status === "draft";
    return queryMatch;
  });

  const activeAgentsCount = agents.filter((a) => a.health !== "stopped").length;

  const handleCreateAgentSubmit = () => {
    if (!newName.trim()) {
      toast.error("Please enter a valid agent name.");
      return;
    }

    const newAgent: AgentData = {
      id: `agent-${Date.now()}`,
      name: newName.trim(),
      description: newDesc.trim() || "No description provided.",
      status: "draft",
      iconType: newIconType,
      metrics: {
        key1: "Capabilities",
        val1: newCaps.trim() || "Python, REST APIs",
        key2: "Memory",
        val2: "64GB Context",
      },
      health: "stopped",
      runsCount: 0,
      errorRate: "0.0%",
    };

    setAgents([...agents, newAgent]);
    toast.success(`Agent "${newName.trim()}" initialized in draft mode.`);
    
    // Clear & close modal
    setNewName("");
    setNewDesc("");
    setNewCaps("");
    setNewIconType("code");
    setShowCreateModal(false);
  };

  const toolbarActions = (
    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
      <Button 
        variant="ghost" 
        size="xs" 
        onClick={() => setIsEmpty(!isEmpty)} 
        className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors bg-transparent border-none mr-2"
      >
        {isEmpty ? "● Show Agents" : "○ Simulate Empty State"}
      </Button>
      <div className="relative w-full sm:w-48">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60 size-4" />
        <input
          type="text"
          placeholder="Search capabilities..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-1.5 text-xs focus:outline-none focus:border-primary transition-all text-on-surface placeholder:text-on-surface-variant/40"
        />
      </div>
      <AgentFilters value={filter} onChange={setFilter} />
    </div>
  );

  return (
    <PageContainer
      title="Agent Directory"
      description="Manage and deploy specialized autonomous agents across your projects."
      icon={<Bot className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={Bot}
            title="No Autonomous Agents"
            description="Start building your private directory of specialized AI workforce agents. Configure custom memory limits, tool endpoints, and system constraints."
            actionLabel="Initialize First Agent"
            onAction={() => setShowCreateModal(true)}
            accentColor="tertiary"
          />
        </div>
      ) : (
        /* Grid listing */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onConfigure={handleConfigure}
              onStatusToggle={handleStatusToggle}
              onDelete={handleDeleteAgent}
            />
          ))}

          {/* Create placeholder card */}
          <CreateAgentCard onClick={() => setShowCreateModal(true)} />
        </div>
      )}

      {/* Stats bar */}
      <StatsBar
        activeCount={`${activeAgentsCount} / ${agents.length}`}
        totalOps="142,829"
        teamAvatars={TEAM_AVATARS}
        plusCount={4}
      />

      {/* Reusable Create Agent Dialog Modal overlay */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-md bg-surface border border-outline-variant text-on-surface p-6 rounded-xl">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Bot className="size-5 text-primary" />
              Create Autonomous Agent
            </DialogTitle>
            <DialogDescription className="text-xs text-on-surface-variant">
              Provision a new agent workspace. Setup capabilities and system access controls.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 my-4 text-xs md:text-sm">
            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">Agent Name</label>
              <input
                type="text"
                placeholder="e.g. Code Reviewer Bot"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-xs"
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">Description</label>
              <textarea
                placeholder="Describe the agent's primary automated tasks..."
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={2}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-xs resize-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">Capabilities (comma separated)</label>
              <input
                type="text"
                placeholder="e.g. TS, Go, Rust, Git API"
                value={newCaps}
                onChange={(e) => setNewCaps(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-xs"
              />
            </div>

            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">Icon / Specialty Type</label>
              <select
                value={newIconType}
                onChange={(e) => setNewIconType(e.target.value as any)}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-xs cursor-pointer"
              >
                <option value="code">Engineering & Code</option>
                <option value="analytics">Data & Analytics</option>
                <option value="shield">Cybersecurity & Compliance</option>
                <option value="translation">Translation & Localization</option>
                <option value="cloud">Cloud & Infrastructure</option>
              </select>
            </div>
          </div>

          <DialogFooter className="flex justify-end gap-2.5 pt-2">
            <Button
              variant="outline"
              size="xs"
              onClick={() => setShowCreateModal(false)}
              className="text-xs cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateAgentSubmit}
              className="bg-primary text-primary-foreground font-semibold px-4 py-2 rounded-lg text-xs cursor-pointer border-none"
            >
              Initialize Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageContainer>
  );
}
