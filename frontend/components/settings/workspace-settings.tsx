"use client";

import { useState } from "react";
import { useWorkspace } from "@/providers/workspace-provider";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function WorkspaceSettingsPanel() {
  const { activeWorkspace, updateWorkspace } = useWorkspace();
  const [name, setName] = useState(activeWorkspace?.name || "");
  const [industry, setIndustry] = useState(activeWorkspace?.settings.industry || "Technology & SaaS");
  const [deployment, setDeployment] = useState(activeWorkspace?.settings.deployment || "private");
  const [description, setDescription] = useState(activeWorkspace?.settings.description || "");

  const handleSave = async () => {
    if (!activeWorkspace) return;
    const success = await updateWorkspace(activeWorkspace.workspace_id, {
      name,
      settings: {
        industry,
        deployment,
        description
      }
    });
    if (success) {
      toast.success("Workspace configurations updated successfully!");
    }
  };

  return (
    <section className="bg-surface-container-low border border-outline-variant rounded-2xl overflow-hidden shadow-sm select-none">
      {/* Header */}
      <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container shrink-0">
        <div>
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Workspace Configuration
          </h3>
          <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
            Configure settings for the active workspace.
          </p>
        </div>
        <Button
          onClick={handleSave}
          className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs font-bold rounded-lg px-4 py-2 cursor-pointer border-none shadow shadow-primary/15"
        >
          Save Workspace Settings
        </Button>
      </div>

      {/* Grid Inputs */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-xs md:text-sm">
        {/* Name */}
        <div className="space-y-1.5 col-span-2">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Workspace Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm"
          />
        </div>

        {/* Industry dropdown */}
        <div className="space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Industry Vertical
          </label>
          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm cursor-pointer"
          >
            <option value="Technology & SaaS">Technology &amp; SaaS</option>
            <option value="Financial Services">Financial Services</option>
            <option value="Healthcare">Healthcare</option>
            <option value="Legal & Compliance">Legal &amp; Compliance</option>
            <option value="Manufacturing">Manufacturing</option>
          </select>
        </div>

        {/* Deployment dropdown */}
        <div className="space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Deployment Strategy
          </label>
          <select
            value={deployment}
            onChange={(e) => setDeployment(e.target.value)}
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm cursor-pointer"
          >
            <option value="private">Private Infrastructure</option>
            <option value="cloud">Managed Cloud</option>
          </select>
        </div>

        {/* Description */}
        <div className="md:col-span-2 space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Workspace Description
          </label>
          <textarea
            value={description}
            rows={3}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm"
          />
        </div>
      </div>
    </section>
  );
}
