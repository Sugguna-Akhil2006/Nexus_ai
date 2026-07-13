"use client";

import { useState, useMemo, useEffect } from "react";
import { ArrowRight, Store } from "lucide-react";
import HeroBanner from "@/components/marketplace/hero-banner";
import CategoryCard, { CategoryData } from "@/components/marketplace/category-card";
import AgentCard, { AgentMarketplaceItem } from "@/components/marketplace/agent-card";
import Filters, { TimeframeValue } from "@/components/marketplace/filters";
import DeveloperCTA from "@/components/marketplace/developer-cta";
import StatsSection from "@/components/marketplace/stats-section";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import PageContainer from "@/components/common/page-container";

// Mock categories dataset matching HTML icons and text descriptions
const CATEGORIES: CategoryData[] = [
  {
    id: "analytics",
    name: "Data Analysis",
    description: "SQL experts, Python notebooks, and visualizers.",
    iconType: "analytics",
    iconColorClass: "text-primary",
  },
  {
    id: "code",
    name: "Engineering",
    description: "Code review, refactoring, and test generators.",
    iconType: "code",
    iconColorClass: "text-tertiary",
  },
  {
    id: "security",
    name: "Security Auditing",
    description: "Vulnerability analysis and compliance scanners.",
    iconType: "security",
    iconColorClass: "text-red-400",
  },
];

// Initial mock marketplace agents database
const AGENT_MARKET_ITEMS: AgentMarketplaceItem[] = [
  {
    id: "git-agent",
    name: "GitHub Reviewer Pro",
    price: "Free",
    description: "Automated PR reviews, AST diff analyzer, code quality score metrics, and developer impact weightings.",
    rating: "4.9",
    tag: "Verified",
    category: "code",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBhM5nUh4x4dHyG3S3Zs54mIWZxqaWUOGMn41tMDu-CFLpEJ5BQs2agVdma9r4LfpQSOLQyzpc_DfEIUZN3Y9K2h1QcBn9AhwQb5Ty9OiXANFbIHuePNPzJa5JOuLl9YeRkL5JeFhr8ek8mHrf5V8uDcyLqZ66UVVfvaltr65FczxkfuNd1566l9JAdZIpPL7mmbSgX1eWOyD3B2dSavffQkJ5Qw7eOQA2xku2B8TC3UtblGg3LD1LLCsxPOe_Eom0HPah8-ygrQxNw",
    initials: ["GH", "PR"],
  },
  {
    id: "db-agent",
    name: "SQL Architect",
    price: "$12/mo",
    description: "Optimize database schemas, generate migrations, and audit slow-running queries.",
    rating: "4.8",
    tag: "Trending",
    category: "analytics",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuADTWQkJyCrcBfNzLgWua8xU-wSLoS4mBRmPJAOkXXNiI6psySgLavV1ddMecybd-7q9elRbTlwmWxlKjxr3FHHT5xYSlyrbidFLE16_NS6iaqQrVs70eGO2g95M6_PkS2khQZXIMjMIH70Oaj8Q08rqOzH0F8RmXifQLnBBLi0KiNCdfvzLcTaug8Nx4WKOWgxJmqKpcqTiD2huFl4At0iXjGJeXgJ8sCjRqtnJOVd3Ppku0_QYohGZpctB_esvM7LgXuueGefuPN0",
    initials: ["SQL", "DB"],
  },
  {
    id: "sec-agent",
    name: "GuardRail Auditor",
    price: "Free",
    description: "OWASP vulnerability scanner, credential leak detector, and package audit reporting.",
    rating: "4.7",
    tag: "Verified",
    category: "security",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCN4AjYH9VxqqekSZR46EWARGDW7GMXN34fjzzmPJY-B4sW93NZW3_bKE8rk8GH6Z7bRoipIGJbgqN0vtzn7xAgoHQTc6JtG3CQCfDiA9neEXuu28xGxc7wL6j9Kf9h9i4MR4U2WvxAjh9HSw6td40xcVWZ9XzdCZ2rtAJ9ktBeZegNm95Es4QadiRmjLDzYdu7-cEyX3PmeaeSC_AnC0mw4FYBiPbd4et2dqdo-rGQFmI6NeZ8QujR__Aq0aj-E6wcGGvHPbx8gVEE",
    initials: ["GR", "SEC"],
  },
  {
    id: "qaoa-agent",
    name: "Quantum QAOA Solver",
    price: "$45/mo",
    description: "Transpile combinatorial cut optimization layers to NISQ backend devices.",
    rating: "5.0",
    tag: "Verified",
    category: "analytics",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBhM5nUh4x4dHyG3S3Zs54mIWZxqaWUOGMn41tMDu-CFLpEJ5BQs2agVdma9r4LfpQSOLQyzpc_DfEIUZN3Y9K2h1QcBn9AhwQb5Ty9OiXANFbIHuePNPzJa5JOuLl9YeRkL5JeFhr8ek8mHrf5V8uDcyLqZ66UVVfvaltr65FczxkfuNd1566l9JAdZIpPL7mmbSgX1eWOyD3B2dSavffQkJ5Qw7eOQA2xku2B8TC3UtblGg3LD1LLCsxPOe_Eom0HPah8-ygrQxNw",
    initials: ["QL", "MK"],
  },
  {
    id: "promptcraft-agent",
    name: "PromptCraft AI",
    price: "$5/mo",
    description: "Deep research agent specialized in parsing prompt vulnerabilities and tuning system configurations.",
    rating: "4.6",
    tag: "Trending",
    category: "security",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuC2tyty80ysgb9eH_wz0r3eh8de6a4GcUqrIQ-j2MokABSqvvoeRCdeFAfLc6_i1KhTyjo7MwXvtOFlHA5YIZEMO-V6qzh-vhm-Y8chdadnFjhQQ2ugGkFugNqs56eKyDWDtapFnurtUorrvH_rlB8-0PCVB7lS8xeEb8whL1ZybQ2rr7RXMMOKkX6enJNY3xIpXHQXjzOorFFDqSx9iYKMDEDrvBANhreCdZMdwwF4OY3EuGIkjU8-VgcSkZah1XfcQhtNwzYLQr9P",
    initials: ["PC"],
  },
];

export default function AgentMarketplacePage() {
  const [plugins, setPlugins] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [timeframe, setTimeframe] = useState<TimeframeValue>("all");
  const [isEmpty, setIsEmpty] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchPlugins = async () => {
    try {
      const res = await fetch("/api/registry/plugins");
      if (res.ok) {
        const data = await res.json();
        setPlugins(data.plugins || []);
      }
    } catch (e) {
      console.warn("Failed to load live plugins registry. Falling back to mock marketplace catalog.", e);
      setPlugins([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  const marketItems = useMemo<AgentMarketplaceItem[]>(() => {
    if (plugins.length === 0) {
      return AGENT_MARKET_ITEMS;
    }
    return plugins.map(p => {
      const mockMeta = AGENT_MARKET_ITEMS.find(item => item.id === p.plugin_id) || {
        id: p.plugin_id,
        name: p.name,
        price: "Free",
        rating: "5.0",
        tag: "Verified",
        category: "code",
        coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBhM5nUh4x4dHyG3S3Zs54mIWZxqaWUOGMn41tMDu-CFLpEJ5BQs2agVdma9r4LfpQSOLQyzpc_DfEIUZN3Y9K2h1QcBn9AhwQb5Ty9OiXANFbIHuePNPzJa5JOuLl9YeRkL5JeFhr8ek8mHrf5V8uDcyLqZ66UVVfvaltr65FczxkfuNd1566l9JAdZIpPL7mmbSgX1eWOyD3B2dSavffQkJ5Qw7eOQA2xku2B8TC3UtblGg3LD1LLCsxPOe_Eom0HPah8-ygrQxNw",
        initials: ["MX"],
      };

      return {
        id: p.plugin_id,
        name: p.name,
        price: mockMeta.price,
        description: p.description,
        rating: mockMeta.rating,
        tag: (p.is_enabled ? "Installed" : mockMeta.tag) as any,
        category: mockMeta.category as any,
        coverUrl: mockMeta.coverUrl,
        initials: mockMeta.initials,
        isInstalled: p.is_enabled
      };
    });
  }, [plugins]);

  const handleCategoryClick = (id: string) => {
    setSelectedCategory(selectedCategory === id ? null : id);
  };

  const handleInstallAgent = async (agentId: string) => {
    const item = marketItems.find((a) => a.id === agentId);
    if (!item) return;

    if (plugins.length === 0) {
      // Offline fallback toggle
      toast.success(item.isInstalled ? `Uninstalling "${item.name}"...` : `Installing "${item.name}"...`);
      AGENT_MARKET_ITEMS.forEach(m => {
        if (m.id === agentId) {
          m.isInstalled = !m.isInstalled;
        }
      });
      fetchPlugins();
      return;
    }

    toast.promise(
      (async () => {
        const res = await fetch(`/api/registry/plugins/${agentId}/toggle?enabled=${!item.isInstalled}`, {
          method: "POST"
        });
        if (!res.ok) throw new Error("Operation failed");
        await fetchPlugins();
      })(),
      {
        loading: item.isInstalled ? `Uninstalling ${item.name}...` : `Installing ${item.name}...`,
        success: item.isInstalled ? `Plugin "${item.name}" uninstalled successfully.` : `Plugin "${item.name}" installed and active!`,
        error: 'Failed to update plugin status.',
      }
    );
  };

  const handleDeveloperSignup = () => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: "Opening Developer Registration Portal...",
        success: "Developer documentation and API keys generated successfully.",
        error: "Verification failed."
      }
    );
  };

  const filteredAgents = useMemo(() => {
    return marketItems.filter((agent) => {
      const matchCategory = !selectedCategory || agent.category === selectedCategory;
      const matchSearch =
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCategory && matchSearch;
    });
  }, [marketItems, selectedCategory, searchQuery]);

  return (
    <PageContainer
      title="Agent Marketplace"
      description="Discover, install, and custom-route pre-trained micro-agents to automate your workflows."
      icon={<Store className="size-8 text-primary shrink-0" />}
    >
      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={Store}
            title="Marketplace Offline"
            description="The central agent registry is currently undergoing maintenance. Check back shortly to download verified runtime plug-ins."
            actionLabel="Retry Connection"
            onAction={fetchPlugins}
            accentColor="primary"
          />
        </div>
      ) : (
        <div className="space-y-10">
          {/* Top Hero Banner */}
          <HeroBanner
            onExplore={() => {
              const el = document.getElementById("search-marketplace");
              if (el) el.focus();
            }}
            onDeveloperClick={handleDeveloperSignup}
          />

          {/* Categories Grid Row layout */}
          <section className="space-y-6">
            <div className="flex justify-between items-center select-none">
              <h3 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
                Browse Categories
              </h3>
              <Button 
                variant="ghost" 
                size="xs" 
                onClick={() => setIsEmpty(!isEmpty)} 
                className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors bg-transparent border-none"
              >
                {isEmpty ? "● Show Content" : "○ Simulate Offline"}
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {CATEGORIES.map((cat) => (
                <CategoryCard
                  key={cat.id}
                  category={cat}
                  isActive={selectedCategory === cat.id}
                  onClick={() => handleCategoryClick(cat.id)}
                />
              ))}
            </div>
          </section>

          {/* Search bar and options row layout */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between items-stretch sm:items-center border-t border-outline-variant/30 pt-6">
            <div className="relative flex-1 max-w-md">
              <SearchQueryIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/50 size-4" />
              <input
                id="search-marketplace"
                type="text"
                placeholder="Search marketplace agents by title or capabilities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-2 text-xs focus:outline-none focus:border-primary transition-all text-on-surface placeholder:text-on-surface-variant/40"
              />
            </div>

            {/* Filters and Reset selectors */}
            <Filters 
              value={timeframe} 
              onChange={setTimeframe} 
            />
          </div>

          {/* Trending Agents Grid */}
          <section className="space-y-6">
            <h3 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface select-none">
              Trending Agents
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  item={agent}
                  onInstall={() => handleInstallAgent(agent.id)}
                />
              ))}

              {/* Add Developer submission placeholder */}
              <DeveloperCTA onSubmit={handleDeveloperSignup} />
            </div>

            {/* Empty state overlay indicator if filtering matches no cards */}
            {filteredAgents.length === 0 && (
              <div className="py-12 text-center select-none bg-surface-container-lowest rounded-xl border border-dashed border-outline-variant/60">
                <p className="text-sm text-on-surface-variant font-medium">
                  No matching agents found in this category matching your search.
                </p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* Bottom statistics indicators */}
      <StatsSection />
    </PageContainer>
  );
}

// Search helper icon
function SearchQueryIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}
