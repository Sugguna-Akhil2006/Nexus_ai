"use client";

import { useState } from "react";
import Image from "next/image";
import { Play, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface AgentMarketplaceItem {
  id: string;
  name: string;
  price: string;
  description: string;
  rating: string;
  tag: "Verified" | "Open Source" | "Trending" | "Installed";
  category: "analytics" | "code" | "creative" | "security";
  coverUrl: string;
  initials: string[];
  plusCount?: number;
}

interface AgentCardProps {
  item: AgentMarketplaceItem;
  onInstall: (id: string) => Promise<void> | void;
}

export default function AgentCard({ item, onInstall }: AgentCardProps) {
  const [installState, setInstallState] = useState<"idle" | "installing" | "installed">("idle");

  const handleInstallClick = async () => {
    if (installState !== "idle") return;
    setInstallState("installing");
    
    // Simulate install latency
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    try {
      await onInstall(item.id);
      setInstallState("installed");
    } catch (err) {
      console.error(err);
      setInstallState("idle");
    }
  };



  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden group hover:shadow-xl hover:shadow-black/20 hover:border-primary/35 transition-all duration-300 flex flex-col justify-between select-none shadow-sm">
      
      {/* Cover Image Frame */}
      <div className="h-40 bg-surface-container relative overflow-hidden shrink-0 select-none">
        <Image
          alt={item.name}
          src={item.coverUrl}
          fill
          priority={false}
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className="object-cover group-hover:scale-105 transition-transform duration-700 ease-out brightness-90"
        />


      </div>

      {/* Info details */}
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Header row */}
          <div className="flex justify-between items-start gap-4 mb-2">
            <h5 className="text-base md:text-lg font-bold text-on-surface tracking-tight group-hover:text-primary transition-colors line-clamp-1">
              {item.name}
            </h5>
            <span className="font-mono text-xs font-semibold text-primary-fixed-dim shrink-0 bg-primary/5 px-2 py-1 rounded border border-primary/10">
              {item.price}
            </span>
          </div>
          
          <p className="text-xs md:text-sm text-on-surface-variant/80 leading-relaxed font-normal mb-6 line-clamp-2 min-h-[40px]">
            {item.description}
          </p>
        </div>

        {/* Bottom install section */}
        <div className="flex items-center justify-between border-t border-outline-variant/60 pt-4 mt-auto">
          <div />

          {/* Action Trigger */}
          <Button
            variant="ghost"
            size="xs"
            onClick={handleInstallClick}
            disabled={installState !== "idle"}
            className={cn(
              "font-bold text-xs cursor-pointer flex items-center gap-1 hover:bg-transparent h-auto py-1 pr-0 pl-2 group-hover:text-primary transition-all",
              installState === "idle" && "text-primary hover:translate-x-1 duration-200",
              installState === "installing" && "text-on-surface-variant animate-pulse cursor-default",
              installState === "installed" && "text-green-400 cursor-default"
            )}
          >
            {installState === "idle" && (
              <>
                Install Agent
                <Play className="size-3.5 fill-current shrink-0" />
              </>
            )}
            {installState === "installing" && (
              <>
                Installing...
              </>
            )}
            {installState === "installed" && (
              <>
                Installed
                <CheckCircle2 className="size-3.5 text-green-400 shrink-0" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
