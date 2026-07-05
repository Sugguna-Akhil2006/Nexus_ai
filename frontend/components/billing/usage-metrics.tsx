"use client";

import { Activity, Database, Cpu, Settings } from "lucide-react";
import { toast } from "sonner";

interface UsageMetricsProps {
  tokensUsed: number; // in Millions, e.g. 1.2
  tokensLimit: number; // in Millions, e.g. 5.0
  storageUsed: number; // in GB, e.g. 412
  storageLimit: number; // in GB, e.g. 1000 (1 TB)
  gpuEfficiency: number; // e.g. 82
}

export default function UsageMetrics({
  tokensUsed,
  tokensLimit,
  storageUsed,
  storageLimit,
  gpuEfficiency,
}: UsageMetricsProps) {
  const tokenPercentage = Math.round((tokensUsed / tokensLimit) * 100);
  const storagePercentage = Math.round((storageUsed / storageLimit) * 100);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 select-none h-full">
      
      {/* Token Usage Card */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xs md:text-sm font-bold text-on-surface uppercase tracking-wider">
            Token Usage
          </h3>
          <Activity className="size-4.5 text-on-surface-variant shrink-0" />
        </div>

        <div className="mb-2">
          <div className="flex justify-between text-xs font-semibold mb-2 select-text">
            <span className="text-on-surface">
              {tokensUsed.toFixed(1)}M / {tokensLimit.toFixed(1)}M
            </span>
            <span className="text-on-surface-variant">
              {tokenPercentage}% of quota
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
            <div
              className="bg-primary h-full rounded-full transition-all duration-1000"
              style={{ width: `${tokenPercentage}%` }}
            />
          </div>
        </div>

        <p className="text-[10px] md:text-xs text-on-surface-variant font-semibold select-text">
          Resetting in 12 days
        </p>
      </div>

      {/* Storage Quota Card */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xs md:text-sm font-bold text-on-surface uppercase tracking-wider">
            Vector Storage
          </h3>
          <Database className="size-4.5 text-on-surface-variant shrink-0" />
        </div>

        <div className="mb-2">
          <div className="flex justify-between text-xs font-semibold mb-2 select-text">
            <span className="text-on-surface">
              {storageUsed} GB / {storageLimit === 1000 ? "1 TB" : `${storageLimit} GB`}
            </span>
            <span className="text-on-surface-variant">
              {storagePercentage}% utilized
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-surface-container-highest h-2 rounded-full overflow-hidden">
            <div
              className="bg-tertiary h-full rounded-full transition-all duration-1000"
              style={{ width: `${storagePercentage}%` }}
            />
          </div>
        </div>

        <p className="text-[10px] md:text-xs text-on-surface-variant font-semibold select-text">
          Includes indexed vector databases
        </p>
      </div>

      {/* GPU Acceleration Full Card (Span 2) */}
      <div className="md:col-span-2 bg-surface-container-low border border-outline-variant rounded-xl p-5 flex flex-col sm:flex-row gap-4 items-center justify-between relative overflow-hidden group shadow-sm">
        
        {/* Info */}
        <div className="relative z-10 text-center sm:text-left select-text">
          <h3 className="text-xs md:text-sm font-bold text-on-surface uppercase tracking-wider mb-1.5 select-none">
            GPU Acceleration
          </h3>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium max-w-md leading-relaxed">
            Your workspace is currently utilizing H100 high-memory nodes for reasoning and training tasks.
          </p>
        </div>

        {/* Counter and Config button */}
        <div className="flex items-center gap-6 relative z-10 shrink-0">
          <div className="text-center select-text">
            <div className="font-mono text-2xl md:text-3xl font-extrabold text-primary leading-none">
              {gpuEfficiency}%
            </div>
            <div className="text-[9px] md:text-[10px] text-on-surface-variant/80 font-bold uppercase tracking-widest mt-1 select-none">
              Efficiency
            </div>
          </div>

          <button
            onClick={() => toast.info("Launching GPU Clusters Settings. Adjusting node parameters...")}
            className="bg-surface-container-highest hover:bg-surface-variant p-2 rounded-lg transition-all border border-outline-variant cursor-pointer inline-flex items-center justify-center"
            title="Adjust reasoning hardware"
          >
            <Settings className="size-4.5 text-on-surface-variant hover:text-white" />
          </button>
        </div>

        {/* Glow glow background */}
        <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors pointer-events-none" />

      </div>

    </div>
  );
}
