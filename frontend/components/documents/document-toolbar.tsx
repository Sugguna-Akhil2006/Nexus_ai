"use client";

import { ZoomIn, ZoomOut, Download, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentToolbarProps {
  filename: string;
  isVerified?: boolean;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onDownload?: () => void;
  onShare?: () => void;
}

export default function DocumentToolbar({
  filename,
  isVerified = true,
  zoom,
  onZoomIn,
  onZoomOut,
  onDownload,
  onShare,
}: DocumentToolbarProps) {
  return (
    <div className="h-12 border-b border-outline-variant flex items-center justify-between px-4 bg-surface-container-lowest select-none shrink-0">
      {/* File Info */}
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-sm font-semibold text-on-surface truncate">
          {filename}
        </span>
        {isVerified && (
          <div className="flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px] uppercase font-bold text-emerald-400 border border-emerald-500/20">
            <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse"></span>
            Verified
          </div>
        )}
      </div>

      {/* Zoom & Action Controls */}
      <div className="flex items-center gap-1.5 sm:gap-3">
        {/* Zoom */}
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon"
            onClick={onZoomOut}
            className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="size-4" />
          </Button>
          <span className="text-xs font-mono font-code text-on-surface w-10 text-center">
            {zoom}%
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={onZoomIn}
            className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="size-4" />
          </Button>
        </div>

        {/* Separator */}
        <div className="w-px h-4 bg-outline-variant mx-0.5 hidden sm:block" />

        {/* Actions */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onDownload}
            className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer"
            title="Download document"
          >
            <Download className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onShare}
            className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer"
            title="Share document"
          >
            <Share2 className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
