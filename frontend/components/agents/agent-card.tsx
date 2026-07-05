"use client";

import { BarChart2, Code, Shield, Globe, Cloud, Sliders } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface AgentData {
  id: string;
  name: string;
  description: string;
  status: "active" | "draft";
  iconType: "analytics" | "code" | "shield" | "translation" | "cloud";
  metrics: {
    key1: string;
    val1: string;
    key2: string;
    val2: string;
    val2Color?: "green" | "default";
  };
}

interface AgentCardProps {
  agent: AgentData;
  onConfigure: (id: string) => void;
}

export default function AgentCard({ agent, onConfigure }: AgentCardProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case "analytics":
        return {
          icon: BarChart2,
          bgColor: "bg-primary/10 text-primary",
        };
      case "shield":
        return {
          icon: Shield,
          bgColor: "bg-error/10 text-error",
        };
      case "translation":
        return {
          icon: Globe,
          bgColor: "bg-secondary-container text-on-secondary-container",
        };
      case "cloud":
        return {
          icon: Cloud,
          bgColor: "bg-tertiary-container/20 text-tertiary",
        };
      default: // code
        return {
          icon: Code,
          bgColor: "bg-tertiary/10 text-tertiary",
        };
    }
  };

  const { icon: IconComp, bgColor } = getIcon(agent.iconType);

  return (
    <div className="agent-card bg-surface-container-low border border-outline-variant rounded-xl p-6 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 group relative select-none">
      
      {/* Icon & Status row */}
      <div className="flex items-start justify-between mb-4">
        <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center shadow-sm", bgColor)}>
          <IconComp className="size-6" />
        </div>
        
        {agent.status === "active" ? (
          <span className="px-3 py-1 rounded-full bg-primary/20 text-primary text-[10px] font-bold tracking-wider uppercase border border-primary/10 animate-pulse">
            Active
          </span>
        ) : (
          <span className="px-3 py-1 rounded-full bg-surface-container-highest text-on-surface-variant text-[10px] font-bold tracking-wider uppercase border border-outline-variant/50">
            Draft
          </span>
        )}
      </div>

      {/* Info */}
      <h3 className="text-lg md:text-xl font-bold text-on-surface mb-2 tracking-tight group-hover:text-primary transition-colors">
        {agent.name}
      </h3>
      <p className="text-xs md:text-sm text-on-surface-variant/80 leading-relaxed mb-6 line-clamp-2 min-h-10">
        {agent.description}
      </p>

      {/* Capabilities and metrics */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-outline-variant/60">
        <div className="min-w-0">
          <p className="text-[9px] uppercase tracking-widest text-on-surface-variant mb-1 font-bold">
            {agent.metrics.key1}
          </p>
          <p className="font-mono text-xs text-on-surface truncate">
            {agent.metrics.val1}
          </p>
        </div>
        <div className="min-w-0">
          <p className="text-[9px] uppercase tracking-widest text-on-surface-variant mb-1 font-bold">
            {agent.metrics.key2}
          </p>
          <p className={cn(
            "font-mono text-xs truncate",
            agent.metrics.val2Color === "green" 
              ? "text-green-400 font-semibold" 
              : "text-on-surface"
          )}>
            {agent.metrics.val2}
          </p>
        </div>
      </div>

      {/* Hover action configuration trigger */}
      <Button
        onClick={() => onConfigure(agent.id)}
        className="absolute inset-x-6 bottom-6 opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 bg-primary text-primary-foreground py-5 rounded-lg font-bold transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer shadow-md hover:bg-primary/95 border-none"
      >
        <Sliders className="size-4" />
        Configure
      </Button>
    </div>
  );
}
