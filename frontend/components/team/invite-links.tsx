"use client";

import { useState } from "react";
import { Rocket, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function InviteLinks() {
  const [inviteLink, setInviteLink] = useState("nexus-ai.io/join/f8a2-992z-xp01");
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(inviteLink);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateNewLink = () => {
    // Generate randomized suffix segments
    const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
    const randSeg = (len: number) => 
      Array.from({ length: len }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
    
    const newLink = `nexus-ai.io/join/${randSeg(4)}-${randSeg(4)}-${randSeg(4)}`;
    setInviteLink(newLink);
    setIsCopied(false);
    toast.success("New secure invitation link generated successfully!");
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col justify-between h-full select-none shadow-sm">
      
      {/* Top Category Badge */}
      <div className="flex items-center gap-2 mb-4 text-tertiary shrink-0">
        <Rocket className="size-4 text-tertiary shrink-0" />
        <h3 className="font-bold uppercase tracking-widest text-[10px] md:text-xs">
          Advanced Onboarding
        </h3>
      </div>

      {/* Title & Desc */}
      <div className="flex-grow select-text">
        <h4 className="text-sm md:text-base font-bold text-on-surface mb-1 select-none">
          Invitation Links
        </h4>
        <p className="text-xs md:text-sm text-on-surface-variant mb-4 leading-relaxed font-medium">
          Generate secure, multi-use invitation links for rapid team scaling.
        </p>

        {/* Generated Link Textbox */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3 font-mono text-xs text-primary flex items-center justify-between gap-4 mb-4 select-text">
          <span className="truncate font-semibold">{inviteLink}</span>
          <button
            onClick={handleCopyLink}
            className="text-on-surface-variant hover:text-white transition-colors cursor-pointer shrink-0"
            title="Copy invitation link"
          >
            {isCopied ? (
              <Check className="size-4 text-green-400" />
            ) : (
              <Copy className="size-4 text-on-surface-variant" />
            )}
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4 shrink-0 mt-2 select-none">
        <Button
          onClick={() => toast.info("Viewing all onboarding invitation links logs... Backend syncing coming soon.")}
          className="flex-1 py-2.5 bg-surface-container-highest border border-outline-variant text-on-surface text-xs font-bold rounded-lg cursor-pointer hover:bg-surface-container transition-colors"
        >
          View All Links
        </Button>
        
        <Button
          onClick={handleCreateNewLink}
          className="flex-1 py-2.5 bg-primary text-primary-foreground hover:opacity-90 active:scale-95 text-xs font-bold rounded-lg cursor-pointer border-none shadow-sm shadow-primary/15"
        >
          Create New
        </Button>
      </div>

    </div>
  );
}
