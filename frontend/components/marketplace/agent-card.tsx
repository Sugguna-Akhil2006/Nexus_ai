"use client";

import { useState } from "react";
import Image from "next/image";
import { Star, Play, CheckCircle2, ShieldCheck, Heart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export interface AgentMarketplaceItem {
  id: string;
  name: string;
  price: string;
  description: string;
  rating: string;
  reviewsCount?: number;
  tag: "Verified" | "Open Source" | "Trending" | "Installed";
  category: "analytics" | "code" | "creative" | "security";
  coverUrl: string;
  initials: string[];
  plusCount?: number;
  liked?: boolean;
  isInstalled?: boolean;
}

interface AgentCardProps {
  item: AgentMarketplaceItem;
  onInstall: (id: string) => Promise<void> | void;
}

export default function AgentCard({ item, onInstall }: AgentCardProps) {
  const [installState, setInstallState] = useState<"idle" | "installing" | "installed">("idle");
  const [liked, setLiked] = useState(!!item.liked);

  const handleInstallClick = async () => {
    if (installState !== "idle") return;
    setInstallState("installing");
    
    // Simulate install latency
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    try {
      await onInstall(item.id);
      setInstallState("installed");
      toast.success(`Agent "${item.name}" installed successfully!`);
    } catch (err) {
      console.error(err);
      setInstallState("idle");
      toast.error(`Installation failed for: ${item.name}`);
    }
  };

  const getTagStyle = (tag: string) => {
    switch (tag) {
      case "Verified":
        return "text-green-400 border-green-500/20 bg-surface/85 backdrop-blur-md";
      case "Trending":
        return "text-tertiary border-tertiary/20 bg-surface/85 backdrop-blur-md";
      case "Installed":
        return "text-green-400 border-green-500/20 bg-surface/85 backdrop-blur-md";
      default: // Open Source
        return "text-on-surface-variant border-outline-variant bg-surface/85 backdrop-blur-md";
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case "code": return "text-tertiary bg-tertiary/10";
      case "security": return "text-red-400 bg-red-500/10";
      case "analytics": return "text-primary bg-primary/10";
      default: return "text-blue-400 bg-blue-500/10";
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

        {/* Floating tags */}
        <div className="absolute top-3 left-3 flex gap-2">
          <span className={cn("text-[9px] px-2.5 py-1 rounded font-bold uppercase tracking-wider border leading-none flex items-center gap-1", getTagStyle(item.tag))}>
            {item.tag === "Verified" && <ShieldCheck className="size-3" />}
            {item.tag}
          </span>
        </div>

        {/* Favorite action overlay button */}
        <button
          onClick={() => {
            setLiked(!liked);
            toast.success(liked ? "Removed from favorites" : "Added to favorites");
          }}
          className="absolute top-3 right-3 w-8 h-8 rounded-full bg-surface/80 backdrop-blur-md flex items-center justify-center border border-outline-variant/30 text-on-surface-variant hover:text-red-400 hover:scale-105 active:scale-95 transition-all cursor-pointer"
        >
          <Heart className={cn("size-4", liked && "text-red-500 fill-red-500")} />
        </button>

        {/* Floating rating details */}
        <div className="absolute bottom-3 right-3">
          <div className="bg-surface/80 backdrop-blur-md px-2.5 py-1 rounded text-xs font-semibold text-on-surface flex items-center gap-1 leading-none shadow-sm border border-outline-variant/30">
            <Star className="size-3.5 text-tertiary fill-tertiary shrink-0" />
            <span className="pt-0.5">{item.rating}</span>
            <span className="text-[10px] text-on-surface-variant/50">({item.reviewsCount || 42})</span>
          </div>
        </div>
      </div>

      {/* Info details */}
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Header row */}
          <div className="flex justify-between items-start gap-4 mb-2">
            <div className="min-w-0">
              <h5 className="text-base md:text-lg font-bold text-on-surface tracking-tight group-hover:text-primary transition-colors line-clamp-1">
                {item.name}
              </h5>
              <span className={cn("text-[8px] font-mono font-bold uppercase px-1.5 py-0.5 rounded-sm border border-outline-variant/30 mt-1 inline-block", getCategoryColor(item.category))}>
                {item.category}
              </span>
            </div>
            <span className="font-mono text-xs font-semibold text-primary-fixed-dim shrink-0 bg-primary/5 px-2.5 py-1 rounded border border-primary/10">
              {item.price}
            </span>
          </div>
          
          <p className="text-xs md:text-sm text-on-surface-variant/80 leading-relaxed font-normal mb-6 line-clamp-2 min-h-[40px]">
            {item.description}
          </p>
        </div>

        {/* Bottom install section */}
        <div className="flex items-center justify-between border-t border-outline-variant/60 pt-4 mt-auto">
          {/* Users Pile */}
          <div className="flex -space-x-1.5 overflow-hidden">
            {item.initials.map((init, idx) => (
              <div
                key={idx}
                className="w-6 h-6 rounded-full bg-surface-container-highest border border-surface flex items-center justify-center text-[9px] font-bold text-on-surface-variant"
                title="Active User"
              >
                {init}
              </div>
            ))}
            {item.plusCount && item.plusCount > 0 && (
              <div className="w-6 h-6 rounded-full bg-surface-container-highest border border-surface flex items-center justify-center text-[9px] font-bold text-on-surface-variant">
                +{item.plusCount}
              </div>
            )}
          </div>

          {/* Action Trigger */}
          <Button
            variant="ghost"
            size="xs"
            onClick={handleInstallClick}
            disabled={installState !== "idle"}
            className={cn(
              "font-bold text-xs cursor-pointer flex items-center gap-1 hover:bg-transparent h-auto py-1 pr-0 pl-2 group-hover:text-primary transition-all border-none",
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
