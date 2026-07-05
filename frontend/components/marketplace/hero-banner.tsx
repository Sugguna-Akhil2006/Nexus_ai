"use client";

import { Sparkles, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeroBannerProps {
  onExplore: () => void;
  onDeveloperClick: () => void;
}

export default function HeroBanner({ onExplore, onDeveloperClick }: HeroBannerProps) {
  return (
    <section className="relative overflow-hidden rounded-xl bg-surface-container p-6 md:p-8 lg:p-12 border border-outline-variant/30 select-none shadow-sm">
      {/* Background glow highlights */}
      <div className="absolute top-1/2 right-12 -translate-y-1/2 w-[350px] h-[180px] bg-primary/5 rounded-full blur-[80px] pointer-events-none" />

      <div className="relative z-10 max-w-2xl">
        {/* Banner Tagline & Badge */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <span className="px-2.5 py-1 bg-primary/15 text-primary text-[10px] font-bold tracking-widest uppercase rounded border border-primary/20 flex items-center gap-1.5 leading-none">
            <Sparkles className="size-3 animate-pulse" />
            v4.2 Update
          </span>
          <span className="text-xs text-on-surface-variant font-medium">
            Discover the next generation of LLM workflow agents.
          </span>
        </div>

        {/* Header Texts */}
        <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-on-surface mb-6 leading-tight select-text">
          Elevate your workspace with <br />
          <span className="text-primary italic font-serif">expert agents.</span>
        </h2>
        <p className="text-sm sm:text-base md:text-lg text-on-surface-variant leading-relaxed mb-8 select-text">
          Deploy pre-configured autonomous agents for engineering, research, and data analysis in seconds. Verified for enterprise security and performance.
        </p>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <Button
            onClick={onExplore}
            className="w-full sm:w-auto px-6 py-5 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 active:scale-98 transition-all cursor-pointer border-none text-xs md:text-sm shadow-md shadow-primary/10"
          >
            Explore Categories
          </Button>
          <Button
            variant="outline"
            onClick={onDeveloperClick}
            className="w-full sm:w-auto px-6 py-5 bg-surface-container-highest border border-outline-variant text-on-surface rounded-xl font-bold hover:bg-surface-variant transition-all cursor-pointer text-xs md:text-sm shadow-sm"
          >
            Become a Developer
          </Button>
        </div>
      </div>
    </section>
  );
}
