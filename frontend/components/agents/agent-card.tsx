"use client";

import { useState } from "react";
import { BarChart2, Code, Shield, Globe, Cloud, Sliders, Play, Square, FileText, Trash2, Copy, MoreVertical, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

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
  health?: "healthy" | "busy" | "stopped";
  runsCount?: number;
  errorRate?: string;
}

interface AgentCardProps {
  agent: AgentData;
  onConfigure: (id: string) => void;
  onStatusToggle?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export default function AgentCard({ agent, onConfigure, onStatusToggle, onDelete }: AgentCardProps) {
  const [health, setHealth] = useState<"healthy" | "busy" | "stopped">(agent.health || "healthy");
  const [status, setStatus] = useState<"active" | "draft">(agent.status);

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

  const getHealthColor = (hState: string) => {
    if (hState === "healthy") return "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]";
    if (hState === "busy") return "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]";
    return "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]";
  };

  const handleStartStop = () => {
    if (status === "active") {
      setStatus("draft");
      setHealth("stopped");
      onStatusToggle?.(agent.id);
      toast.info(`Agent "${agent.name}" stopped.`);
    } else {
      setStatus("active");
      setHealth("healthy");
      onStatusToggle?.(agent.id);
      toast.success(`Agent "${agent.name}" started successfully.`);
    }
  };

  return (
    <div className="agent-card bg-surface-container-low border border-outline-variant rounded-xl p-6 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5 transition-all duration-300 group relative select-none flex flex-col justify-between">
      
      <div>
        {/* Icon, Health Pulse & Context Menu row */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center shadow-sm", bgColor)}>
              <IconComp className="size-6" />
            </div>
            
            {/* Health Pulse Indicator */}
            <div className="flex items-center gap-1.5 bg-surface-container/60 px-2 py-0.5 rounded border border-outline-variant/50">
              <span className={cn("w-2 h-2 rounded-full animate-pulse", getHealthColor(health))} />
              <span className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider">{health}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            {status === "active" ? (
              <span className="px-2.5 py-0.5 rounded-full bg-primary/20 text-primary text-[9px] font-bold tracking-wider uppercase border border-primary/10 select-none">
                Active
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded-full bg-surface-container-highest text-on-surface-variant text-[9px] font-bold tracking-wider uppercase border border-outline-variant/50 select-none">
                Draft
              </span>
            )}

            {/* Actions Context Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="p-1.5 rounded hover:bg-surface-container-highest text-on-surface-variant/60 hover:text-on-surface transition-all cursor-pointer bg-transparent border-none">
                  <MoreVertical className="size-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={handleStartStop}>
                  {status === "active" ? (
                    <>
                      <Square className="size-3.5 text-red-400" />
                      Stop Agent
                    </>
                  ) : (
                    <>
                      <Play className="size-3.5 text-green-400" />
                      Start Agent
                    </>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => onConfigure(agent.id)}>
                  <Sliders className="size-3.5" />
                  Configure
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.success(`Viewing execution log trace for: ${agent.name}`)}>
                  <FileText className="size-3.5" />
                  View Logs
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.success(`Agent "${agent.name}" cloned.`)}>
                  <Copy className="size-3.5" />
                  Clone Agent
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-outline-variant" />
                <DropdownMenuItem className="cursor-pointer hover:bg-red-500/10 text-red-400 px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => {
                  onDelete?.(agent.id);
                  toast.success(`Agent "${agent.name}" deleted.`);
                }}>
                  <Trash2 className="size-3.5 text-red-400" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Info */}
        <h3 className="text-lg md:text-xl font-bold text-on-surface mb-2 tracking-tight group-hover:text-primary transition-colors">
          {agent.name}
        </h3>
        <p className="text-xs md:text-sm text-on-surface-variant/80 leading-relaxed mb-4 line-clamp-2 min-h-10">
          {agent.description}
        </p>

        {/* Telemetry telemetry bar (Runs, Errors) */}
        <div className="flex items-center justify-between bg-surface-container-lowest/60 border border-outline-variant/40 rounded-lg p-2.5 mb-4 text-[10px] select-none font-mono">
          <div className="flex items-center gap-1 text-on-surface-variant">
            <Activity className="size-3 text-primary" />
            <span>Runs: <span className="text-on-surface font-semibold">{agent.runsCount || 234}</span></span>
          </div>
          <span className="text-on-surface-variant/40">|</span>
          <span className="text-on-surface-variant">Errors: <span className="text-red-400 font-semibold">{agent.errorRate || "0.0%"}</span></span>
        </div>
      </div>

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
    </div>
  );
}
