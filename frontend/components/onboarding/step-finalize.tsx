"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StepFinalizeProps {
  onEnterDashboard: () => void;
}

export default function StepFinalize({ onEnterDashboard }: StepFinalizeProps) {
  const [percent, setPercent] = useState(88);
  const [neuralEstablished, setNeuralEstablished] = useState(false);

  useEffect(() => {
    // Simulate progression of neural sharding establishing
    const interval = setTimeout(() => {
      setPercent(100);
      setNeuralEstablished(true);
    }, 2000);

    return () => clearTimeout(interval);
  }, []);

  return (
    <section className="w-full max-w-[640px] animate-in fade-in slide-in-from-left-4 duration-300 select-none">
      <div className="glass-panel p-6 md:p-8 rounded-2xl text-center space-y-6 flex flex-col justify-between items-center">
        
        {/* Pulsing Checked Icon Bounding Frame */}
        <div className="relative w-20 h-20 md:w-24 md:h-24 mx-auto mb-2 shrink-0 select-none">
          <div className="absolute inset-0 bg-primary/25 rounded-full blur-xl animate-pulse" />
          <div className="relative w-full h-full bg-surface-container rounded-full flex items-center justify-center border-2 border-primary shadow-inner">
            <CheckCircle2 className="size-10 md:size-12 text-primary" />
          </div>
        </div>

        {/* Headings */}
        <div className="space-y-1.5 select-text">
          <h2 className="text-lg md:text-xl font-bold tracking-tight text-on-surface">
            Workspace Ready
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium max-w-[340px] mx-auto leading-relaxed">
            Nexus AI is initializing your environment. You&apos;ll be redirected to your dashboard in a moment.
          </p>
        </div>

        {/* Provisioning log details */}
        <div className="w-full bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm shrink-0">
          {/* Header */}
          <div className="p-4 border-b border-outline-variant flex items-center justify-between font-mono text-[10px] md:text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-tertiary rounded-full animate-ping shrink-0" />
              <span className="text-tertiary font-bold">System Provisioning...</span>
            </div>
            <span className="text-on-surface-variant font-bold">{percent}%</span>
          </div>

          {/* Logs rows */}
          <div className="p-4 text-left space-y-2 select-text">
            <div className="flex justify-between text-[10px] md:text-xs font-mono">
              <span className="text-on-surface-variant/80">Database Sharding</span>
              <span className="text-primary font-bold">COMPLETE</span>
            </div>
            <div className="flex justify-between text-[10px] md:text-xs font-mono">
              <span className="text-on-surface-variant/80">Agent Memory Allocation</span>
              <span className="text-primary font-bold">COMPLETE</span>
            </div>
            <div className="flex justify-between text-[10px] md:text-xs font-mono">
              <span className="text-on-surface-variant/80">Neural Link Established</span>
              {neuralEstablished ? (
                <span className="text-primary font-bold animate-pulse">COMPLETE</span>
              ) : (
                <span className="text-tertiary font-bold animate-pulse">IN PROGRESS</span>
              )}
            </div>
          </div>
        </div>

        {/* CTA triggers */}
        <div className="w-full space-y-3.5 select-none shrink-0">
          <Link href="/dashboard" passHref className="w-full">
            <Button
              onClick={onEnterDashboard}
              className="w-full py-5 bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold rounded-lg border-none flex items-center justify-center gap-1.5 cursor-pointer shadow-md shadow-primary/15"
            >
              <span>Enter Dashboard</span>
              <ArrowRight className="size-4" />
            </Button>
          </Link>
          
          <p className="text-[10px] md:text-xs text-on-surface-variant/80 font-semibold select-text">
            Setting up for enterprise-grade performance.
          </p>
        </div>

      </div>
    </section>
  );
}
