"use client";

import { useState } from "react";
import { Cloud, Shield, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface StepWorkspaceProps {
  onContinue: (data: { workspaceName: string; industry: string; deployment: "cloud" | "private" }) => void;
}

export default function StepWorkspace({ onContinue }: StepWorkspaceProps) {
  const [workspaceName, setWorkspaceName] = useState("");
  const [industry, setIndustry] = useState("Technology & SaaS");
  const [deployment, setDeployment] = useState<"cloud" | "private">("private"); // Matches HTML where Private is default selected

  const handleContinue = () => {
    if (!workspaceName.trim()) {
      toast.error("Please enter a Workspace Name before continuing.");
      return;
    }
    onContinue({ workspaceName, industry, deployment });
  };

  return (
    <section className="w-full max-w-[640px] animate-in fade-in slide-in-from-left-4 duration-300 select-none">
      <div className="glass-panel p-6 md:p-8 rounded-2xl space-y-6">
        
        {/* Step Headings */}
        <div className="space-y-1.5 select-text">
          <h2 className="text-lg md:text-xl font-bold tracking-tight text-on-surface">
            Configure your workspace
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium leading-relaxed">
            This will be the central hub for your team&apos;s documents and AI agents.
          </p>
        </div>

        {/* Inputs */}
        <div className="space-y-4">
          
          {/* Name input */}
          <div className="space-y-1.5">
            <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Workspace Name
            </label>
            <input
              type="text"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder="e.g. Acme Corp Research"
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm"
            />
          </div>

          {/* Industry dropdown */}
          <div className="space-y-1.5">
            <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Industry Vertical
            </label>
            <div className="relative">
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-3 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm appearance-none cursor-pointer"
              >
                <option value="Technology & SaaS">Technology &amp; SaaS</option>
                <option value="Financial Services">Financial Services</option>
                <option value="Healthcare">Healthcare</option>
                <option value="Legal & Compliance">Legal &amp; Compliance</option>
                <option value="Manufacturing">Manufacturing</option>
              </select>
              {/* Caret arrow decoration */}
              <div className="absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant/80 font-bold select-none text-[10px]">
                ▼
              </div>
            </div>
          </div>

          {/* Deployment options columns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {/* Option Cloud */}
            <div
              onClick={() => setDeployment("cloud")}
              className={cn(
                "bg-surface-container-low border rounded-xl p-4 cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all group relative select-none",
                deployment === "cloud" ? "border-primary" : "border-outline-variant"
              )}
            >
              {deployment === "cloud" && (
                <div className="absolute top-2.5 right-2.5 h-2 w-2 bg-primary rounded-full" />
              )}
              <Cloud className={cn(
                "size-5 mb-2 transition-transform group-hover:scale-115 duration-200 shrink-0",
                deployment === "cloud" ? "text-primary" : "text-on-surface-variant"
              )} />
              <h3 className="text-xs md:text-sm font-bold text-on-surface mb-1">
                Cloud Managed
              </h3>
              <p className="text-[10px] md:text-xs text-on-surface-variant/80 leading-normal font-medium">
                We handle the infrastructure and scaling.
              </p>
            </div>

            {/* Option Private */}
            <div
              onClick={() => setDeployment("private")}
              className={cn(
                "bg-surface-container-low border rounded-xl p-4 cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all group relative select-none",
                deployment === "private" ? "border-primary" : "border-outline-variant"
              )}
            >
              {deployment === "private" && (
                <div className="absolute top-2.5 right-2.5 h-2 w-2 bg-primary rounded-full" />
              )}
              <Shield className={cn(
                "size-5 mb-2 transition-transform group-hover:scale-115 duration-200 shrink-0",
                deployment === "private" ? "text-primary" : "text-on-surface-variant"
              )} />
              <h3 className="text-xs md:text-sm font-bold text-on-surface mb-1">
                Private Cluster
              </h3>
              <p className="text-[10px] md:text-xs text-on-surface-variant/80 leading-normal font-medium">
                Dedicated compute for high security.
              </p>
            </div>
          </div>

        </div>

        {/* Action Button */}
        <Button
          onClick={handleContinue}
          className="w-full bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold py-5 rounded-lg border-none flex items-center justify-center gap-1.5 cursor-pointer shadow-md shadow-primary/15"
        >
          <span>Continue</span>
          <ArrowRight className="size-4 shrink-0" />
        </Button>

      </div>
    </section>
  );
}
