"use client";

import { Play, UploadCloud, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";

interface BottomActionBarProps {
  lastSaved?: string;
  onRunDebug: () => void;
  onDeploy: () => void;
}

export default function BottomActionBar({
  lastSaved = "2m ago",
  onRunDebug,
  onDeploy,
}: BottomActionBarProps) {
  return (
    <footer className="h-10 bg-surface-container border-t border-outline-variant flex items-center justify-between px-6 z-40 shrink-0 select-none">
      {/* Status Details */}
      <div className="flex items-center gap-4 text-[10px] md:text-xs text-on-surface-variant font-medium">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse"></span>
          System Live
        </div>
        <div className="flex items-center gap-1.5 text-on-surface-variant/80">
          <Clock className="size-3.5" />
          Last saved: {lastSaved}
        </div>
      </div>

      {/* Button controls */}
      <div className="flex items-center gap-4 sm:gap-6 text-[10px] md:text-xs font-bold">
        <Button
          variant="ghost"
          size="xs"
          onClick={onRunDebug}
          className="flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors cursor-pointer bg-transparent border-none py-1 h-auto"
        >
          <Play className="size-3.5" />
          RUN DEBUG
        </Button>
        <Button
          variant="ghost"
          size="xs"
          onClick={onDeploy}
          className="flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors cursor-pointer bg-transparent border-none py-1 h-auto"
        >
          <UploadCloud className="size-3.5" />
          DEPLOY WORKFLOW
        </Button>
      </div>
    </footer>
  );
}
