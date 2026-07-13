"use client";

import { useState, useEffect } from "react";
import { Search, Bot } from "lucide-react";
import AgentFilters, { FilterValue } from "@/components/agents/agent-filters";
import AgentCard, { AgentData } from "@/components/agents/agent-card";
import CreateAgentCard from "@/components/agents/create-agent-card";
import StatsBar from "@/components/agents/stats-bar";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";

// Initial mock agents dataset
const INITIAL_AGENTS: AgentData[] = [
  {
    id: "agent-1",
    name: "Data Analyst Pro",
    description: "Autonomous data parsing, visualization generation, and complex trend forecasting using Python and SQL.",
    status: "active",
    iconType: "analytics",
    metrics: {
      key1: "Capabilities",
      val1: "Pandas, Matplotlib",
      key2: "Latency",
      val2: "~420ms",
    },
  },
  {
    id: "agent-2",
    name: "Refactor Sentinel",
    description: "Real-time code optimization and technical debt identification across multi-repo environments.",
    status: "draft",
    iconType: "code",
    metrics: {
      key1: "Capabilities",
      val1: "TS, Rust, Go",
      key2: "Memory",
      val2: "128GB Context",
    },
  },
  {
    id: "agent-3",
    name: "Audit Commander",
    description: "Compliance and security auditing for enterprise networks with automated patch suggestions.",
    status: "active",
    iconType: "shield",
    metrics: {
      key1: "Capabilities",
      val1: "SOC2, GDPR",
      key2: "Status",
      val2: "Secure",
      val2Color: "green",
    },
  },
  {
    id: "agent-4",
    name: "Polyglot Bridge",
    description: "Near-zero latency translation and localization agent for dynamic content streams.",
    status: "active",
    iconType: "translation",
    metrics: {
      key1: "Capabilities",
      val1: "92 Languages",
      key2: "Precision",
      val2: "99.8%",
    },
  },
  {
    id: "agent-5",
    name: "Cloud Optimizer",
    description: "Scales compute resources dynamically based on predicted demand and cost-efficiency curves.",
    status: "active",
    iconType: "cloud",
    metrics: {
      key1: "Cloud",
      val1: "AWS, Azure",
      key2: "Savings",
      val2: "24% MoM",
      val2Color: "green",
    },
  },
];

// Team avatars hosted on authorized domains
const TEAM_AVATARS = [
  "https://lh3.googleusercontent.com/aida-public/AB6AXuDTODzNl244d0kyeW9QZRzf7Ujg4rm4QUcS7DcAx3lEOeQ3M2vPx05cKAKYvoEUwQMpTv-Xzugk4zT5Ds9rLH9wb4nGkmDr6whsh7NwVoq621bw9NwdUnxT-MEtucb7vuJ4pUHB_kJuK3Z4GAA5DxJysqkB20HtwGN8WKb-OYtRxWOZUdI4CH73mNS7aayr0mm_jrROabs22-SNW04fuDIraa9k7joV7lmxXj9GFuYUV2nS1BAGu_PK8nfDL8JHhmpVTEPnrA6FPV5E",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuDFErOlpB5Iktkf3bCWYjOaykFqI7uliGnxmBUBvXdFolnJqEG0WAkOqPsUt3ou99AbgCPnsZD4zddcH7jrgpoyU8mWs4nVwkLn4nB5ZXDjec0Kc2eLfZLaP4UqJWAS0TU0_TluRqEhV1A73DkSt1JmZhG_RSsZSXGao8HYBVVv7uLmtMcxD9eCXM4_i-p1lRvfD0WDFmSeFcHg8IJXP0E7m9nwB8H3PppjSWiJ6YiJlchm-F9LN8u-HZ3FesREv1R3iqIzIWQUcX-s",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuAXMefxTWWcMpMEoW5ttZYChNbaq6ZXNWuxirg8SIrkmg7YFvX4lympAtQ2GaVE7FRkRJZTYWzx6EzdQDb3jjFIk6hvzMHOH3jj7Vjcy_C8Tq82ccHUAe_teKG7u1SwNAZRfufK6VNKxB0PX_rVQe9G2w3IEEH9JlIfviMQT-hP6amsiABELcT1xfrPeWIBus9oQhoEXiBEHnIuf3MWDAj8a_WhKrmpO9Dk-4SQYn-RYd4JRk03ELMeKdmYIY75knrXQZ5tA4wIV01K",
];

export default function AgentDirectoryPage() {
  const [agents, setAgents] = useState<AgentData[]>(INITIAL_AGENTS);
  const [filter, setFilter] = useState<FilterValue>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isEmpty, setIsEmpty] = useState(false);

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
            }
          }));
          setAgents(apiAgents);
        }
      })
      .catch((err) => {
        console.error("Error loading agents:", err);
      });
  }, []);

  // Filter & search operations
  const filteredAgents = agents.filter((agent) => {
    // Status Filter Check
    if (filter === "production" && agent.status !== "active") return false;
    if (filter === "drafts" && agent.status !== "draft") return false;

    // Search query check
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      return (
        agent.name.toLowerCase().includes(query) ||
        agent.description.toLowerCase().includes(query) ||
        agent.metrics.val1.toLowerCase().includes(query)
      );
    }

    return true;
  });

  const activeAgentsCount = agents.filter(a => a.status === "active").length;

  // Configure trigger
  const handleConfigure = (id: string) => {
    const agentName = agents.find((a) => a.id === id)?.name || "Agent";
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: `Initializing configure pipeline for: ${agentName}...`,
        success: `${agentName} configurations loaded. Loaded hyperparameter weights and sandbox environments.`,
        error: 'Configuration build failed.',
      }
    );
  };

  // Create new agent modal prompt
  const handleCreateAgent = () => {
    const name = prompt("Enter a name for the new autonomous agent:");
    if (!name || !name.trim()) return;

    const description = prompt("Describe the agent's responsibilities:") || "Custom user-defined autonomous workflow agent.";

    const capabilities = prompt("Specify key capabilities (comma separated):") || "Python, REST APIs";

    const newAgent: AgentData = {
      id: `agent-${Date.now()}`,
      name: name.trim(),
      description: description.trim(),
      status: "draft",
      iconType: "code",
      metrics: {
        key1: "Capabilities",
        val1: capabilities,
        key2: "Memory",
        val2: "64GB Context",
      },
    };

    setAgents([...agents, newAgent]);
    toast.success(`Agent "${name.trim()}" successfully initialized as a draft in directory!`);
  };

  return (
    <section className="p-6 md:p-8 lg:p-12 overflow-y-auto h-[calc(100vh-64px)] custom-scrollbar select-none">
      <DashboardBreadcrumbs />
      
      {/* Directory Header & Filters wrapper */}
      <div className="flex flex-col xl:flex-row xl:items-end justify-between mb-8 gap-6">
        <div>
          <div className="flex items-center gap-4">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-on-surface mb-1">
              Agent Directory
            </h2>
            <Button 
              variant="ghost" 
              size="xs" 
              onClick={() => setIsEmpty(!isEmpty)} 
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
            >
              {isEmpty ? "● Show Agents" : "○ Simulate Empty State"}
            </Button>
          </div>
          <p className="text-xs md:text-sm text-on-surface-variant leading-relaxed">
            Manage and deploy specialized autonomous agents across your projects.
          </p>
        </div>

        {/* Inputs cluster: Search + Tabs */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          
          {/* Secondary Search box */}
          <div className="relative w-full sm:w-60">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60 size-4" />
            <input
              type="text"
              placeholder="Search capabilities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-2 text-xs md:text-sm focus:outline-none focus:border-primary transition-all text-on-surface placeholder:text-on-surface-variant/40"
            />
          </div>

          <AgentFilters value={filter} onChange={setFilter} />
        </div>
      </div>

      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={Bot}
            title="No Autonomous Agents"
            description="Start building your private directory of specialized AI workforce agents. Configure custom memory limits, tool endpoints, and system constraints."
            actionLabel="Initialize First Agent"
            onAction={handleCreateAgent}
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
            />
          ))}

          {/* Create placeholder card */}
          <CreateAgentCard onClick={handleCreateAgent} />
        </div>
      )}

      {/* Stats bar */}
      <StatsBar
        activeCount={`${activeAgentsCount} / ${agents.length + 5}`}
        totalOps="142,829"
        teamAvatars={TEAM_AVATARS}
        plusCount={4}
      />

    </section>
  );
}
