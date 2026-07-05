"use client";

import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function DashboardHeader() {
  const handleExportReport = () => {
    toast.success("Preparing PDF report export. Your download will start shortly.");
  };

  const handleUpdateClusters = () => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: 'Connecting to cluster infrastructure...',
        success: 'All cluster nodes updated successfully.',
        error: 'Cluster connection timed out.',
      }
    );
  };

  return (
    <section className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div className="space-y-1">
        {/* System Online Badge */}
        <div className="flex items-center">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20 select-none">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
            System Online
          </span>
        </div>
        
        {/* Title */}
        <h2 className="text-3xl font-bold text-on-surface tracking-tight leading-none pt-1">
          Dashboard Overview
        </h2>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          onClick={handleExportReport}
          className="px-4 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm font-medium hover:bg-surface-container-highest transition-colors cursor-pointer"
        >
          Export Report
        </Button>
        <Button
          onClick={handleUpdateClusters}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-bold active:scale-95 transition-transform cursor-pointer border-none"
        >
          Update Clusters
        </Button>
      </div>
    </section>
  );
}
