"use client";

import { useState, useMemo } from "react";
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
    id: "creative",
    name: "Creative Arts",
    description: "Marketing copy, design feedback, and content.",
    iconType: "creative",
    iconColorClass: "text-primary-fixed-dim",
  },
  {
    id: "security",
    name: "Cybersecurity",
    description: "Vulnerability scanning and compliance auditing.",
    iconType: "security",
    iconColorClass: "text-error",
  },
];

// Mock agent items matching HTML cover URL links, ratings, prices, and user overlap bubble piles
const AGENT_MARKET_ITEMS: AgentMarketplaceItem[] = [
  {
    id: "agent-1",
    name: "Synthetix Architect",
    price: "$49/mo",
    description: "A high-fidelity system architect for building scalable microservices and infrastructure diagrams.",
    rating: "4.9",
    tag: "Verified",
    category: "code",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBhM5nUh4x4dHyG3S3Zs54mIWZxqaWUOGMn41tMDu-CFLpEJ5BQs2agVdma9r4LfpQSOLQyzpc_DfEIUZN3Y9K2h1QcBn9AhwQb5Ty9OiXANFbIHuePNPzJa5JOuLl9YeRkL5JeFhr8ek8mHrf5V8uDcyLqZ66UVVfvaltr65FczxkfuNd1566l9JAdZIpPL7mmbSgX1eWOyD3B2dSavffQkJ5Qw7eOQA2xku2B8TC3UtblGg3LD1LLCsxPOe_Eom0HPah8-ygrQxNw",
    initials: ["JD", "AS"],
  },
  {
    id: "agent-2",
    name: "AuditMaster Pro",
    price: "Free",
    description: "Autonomous security auditor specialized in Solidity smart contracts and DeFi protocol safety checks.",
    rating: "4.7",
    tag: "Open Source",
    category: "security",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuC2tyty80ysgb9eH_wz0r3eh8de6a4GcUqrIQ-j2MokABSqvvoeRCdeFAfLc6_i1KhTyjo7MwXvtOFlHA5YIZEMO-V6qzh-vhm-Y8chdadnFjhQQ2ugGkFugNqs56eKyDWDtapFnurtUorrvH_rlB8-0PCVB7lS8xeEb8whL1ZybQ2rr7RXMMOKkX6enJNY3xIpXHQXjzOorFFDqSx9iYKMDEDrvBANhreCdZMdwwF4OY3EuGIkjU8-VgcSkZah1XfcQhtNwzYLQr9P",
    initials: ["B"],
    plusCount: 4,
  },
  {
    id: "agent-3",
    name: "Lexicon Analyst",
    price: "$12/mo",
    description: "Linguistic agent for cross-market sentiment analysis and localized copywriting with high emotional IQ.",
    rating: "5.0",
    tag: "Trending",
    category: "creative",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCz82dpIxP16IqdFOcyT8-aFrPY9bcDnVly6cqBnKECoXgJF7EfhDhbY4ZKvS1vsJRdD3KUbhmYBkSUCVD-XJAno7wvcsXAI9zI_jO4-Qvnr8Q291J1ag6L33Uu6GFsikrj-mq0MkRGjzQukK9oGnyZztYXmgf71N7p_q5kwg0v5ZgSM9h20IWEcMRndmVuZ4HpFPdBbHJRvZzB3LMkHApC9nsWsk0MnMG3TFCl7S4dZmg3fGqTeAXt1Er_ZtvE9K-DnYLL0xZe68AD",
    initials: ["LX"],
  },
  {
    id: "agent-4",
    name: "QuerySQL Genius",
    price: "Free",
    description: "Translates natural language to complex SQL queries, optimizes executions, and builds live spreadsheets.",
    rating: "4.8",
    tag: "Verified",
    category: "analytics",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBhM5nUh4x4dHyG3S3Zs54mIWZxqaWUOGMn41tMDu-CFLpEJ5BQs2agVdma9r4LfpQSOLQyzpc_DfEIUZN3Y9K2h1QcBn9AhwQb5Ty9OiXANFbIHuePNPzJa5JOuLl9YeRkL5JeFhr8ek8mHrf5V8uDcyLqZ66UVVfvaltr65FczxkfuNd1566l9JAdZIpPL7mmbSgX1eWOyD3B2dSavffQkJ5Qw7eOQA2xku2B8TC3UtblGg3LD1LLCsxPOe_Eom0HPah8-ygrQxNw",
    initials: ["QL", "MK"],
  },
  {
    id: "agent-5",
    name: "PromptCraft AI",
    price: "$5/mo",
    description: "Deep research agent specialized in parsing prompt vulnerabilities and tuning system configurations.",
    rating: "4.6",
    tag: "Trending",
    category: "security",
    coverUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuC2tyty80ysgb9eH_wz0r3eh8de6a4GcUqrIQ-j2MokABSqvvoeRCdeFAfLc6_i1KhTyjo7MwXvtOFlHA5YIZEMO-V6qzh-vhm-Y8chdadnFjhQQ2ugGkFugNqs56eKyDWDtapFnurtUorrvH_rlB8-0PCVB7lS8xeEb8whL1ZybQ2rr7RXMMOKkX6enJNY3xIpXHQXjzOorFFDqSx9iYKMDEDrvBANhreCdZMdwwF4OY3EuGIkjU8-VgcSkZah1XfcQhtNwzYLQr9P",
    initials: ["TR"],
    plusCount: 2,
  },
];

export default function AgentMarketplacePage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [timeframe, setTimeframe] = useState<TimeframeValue>("week");
  const [isEmpty, setIsEmpty] = useState(false);

  // Handle Category click toggles
  const handleCategoryClick = (categoryId: string) => {
    setSelectedCategory((prev) => (prev === categoryId ? null : categoryId));
  };

  // Perform install action trigger callback
  const handleInstallAgent = (agentId: string) => {
    const item = AGENT_MARKET_ITEMS.find((a) => a.id === agentId);
    if (item) {
      toast.promise(
        new Promise((resolve) => setTimeout(resolve, 1500)),
        {
          loading: `Adding ${item.name} to workspace pipelines...`,
          success: `Agent "${item.name}" has been successfully added to your workspace.`,
          error: 'Failed to install agent.',
        }
      );
    }
  };

  // Handle developer program signup trigger callback
  const handleDeveloperSignup = () => {
    toast.success("Signing up for the developer program... You will be redirected to the developer documentation panel shortly.");
  };

  const handleScrollToCategories = () => {
    const categoriesSection = document.getElementById("categories-section");
    if (categoriesSection) {
      categoriesSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Filter items based on active search input values and category filters
  const filteredAgents = useMemo(() => {
    return AGENT_MARKET_ITEMS.filter((agent) => {
      const matchesCategory = selectedCategory ? agent.category === selectedCategory : true;
      const matchesSearch = searchQuery
        ? agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          agent.description.toLowerCase().includes(searchQuery.toLowerCase())
        : true;
      return matchesCategory && matchesSearch;
    });
  }, [selectedCategory, searchQuery]);

  return (
    <div className="space-y-8 md:space-y-12 relative">
      <div className="absolute top-0 right-0 z-10">
        <Button 
          variant="ghost" 
          size="xs" 
          onClick={() => setIsEmpty(!isEmpty)} 
          className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
        >
          {isEmpty ? "● Show Marketplace" : "○ Simulate Empty State"}
        </Button>
      </div>
      
      {/* Hero section banner */}
      <HeroBanner 
        onExplore={handleScrollToCategories}
        onDeveloperClick={handleDeveloperSignup}
      />

      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={Store}
            title="No Extensions Available"
            description="Explore and install community-contributed agents, custom prompt security classifiers, and specialized datasets."
            actionLabel="Refresh Directory"
            onAction={() => {
              setIsEmpty(false);
              toast.success("Successfully synchronized marketplace repository!");
            }}
            accentColor="primary"
          />
        </div>
      ) : (
        <>
          {/* Categories Bento (Section IDs mapped for smooth scrolling) */}
          <section id="categories-section" className="space-y-6 scroll-mt-6 select-none">
            <div className="flex items-center justify-between">
              <h3 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
                Browse Categories
              </h3>
              <Button
                variant="link"
                onClick={() => setSelectedCategory(null)}
                className="text-primary hover:text-primary/80 font-semibold p-0 h-auto cursor-pointer text-xs md:text-sm flex items-center gap-1"
              >
                Clear Filters 
                <ArrowRight className="size-4" />
              </Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
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

          {/* Dynamic Search / Search Indicators */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-t border-outline-variant/30 pt-8">
            <div className="relative w-full sm:w-80 group shrink-0">
              <input
                type="text"
                placeholder="Filter active cards list..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg px-4 py-2 text-xs md:text-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
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
                  onInstall={handleInstallAgent}
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
        </>
      )}

      {/* Bottom statistics indicators */}
      <StatsSection />
    </div>
  );
}
