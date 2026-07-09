"use client";

import { useState } from "react";
import { ZoomIn, ZoomOut, Download, Share2, History, Eye, ScanText, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface VersionEntry {
  version: string;
  date: string;
  author: string;
  isCurrent?: boolean;
}

const VERSION_HISTORY: VersionEntry[] = [
  { version: "v3.1", date: "Jul 7, 2024", author: "Alex Sterling", isCurrent: true },
  { version: "v3.0", date: "Jul 3, 2024", author: "Sarah Jenkins" },
  { version: "v2.4", date: "Jun 28, 2024", author: "Marcus Aurelius" },
  { version: "v2.0", date: "Jun 15, 2024", author: "Alex Sterling" },
  { version: "v1.0", date: "May 22, 2024", author: "Dina Prince" },
];

interface DocumentToolbarProps {
  filename: string;
  isVerified?: boolean;
  zoom: number;
  totalPages?: number;
  currentPage?: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onDownload?: () => void;
  onShare?: () => void;
  onPageChange?: (page: number) => void;
}

export default function DocumentToolbar({
  filename,
  isVerified = true,
  zoom,
  totalPages = 12,
  currentPage = 1,
  onZoomIn,
  onZoomOut,
  onDownload,
  onShare,
  onPageChange,
}: DocumentToolbarProps) {
  const [page, setPage] = useState(currentPage);

  const handlePageChange = (newPage: number) => {
    const clamped = Math.max(1, Math.min(newPage, totalPages));
    setPage(clamped);
    onPageChange?.(clamped);
  };

  const isOCR = filename.endsWith(".pdf");

  return (
    <div className="h-12 border-b border-outline-variant flex items-center justify-between px-4 bg-surface-container-lowest select-none shrink-0">
      {/* File Info + Badges */}
      <div className="flex items-center gap-2.5 min-w-0">
        <span className="text-sm font-semibold text-on-surface truncate max-w-[180px]">
          {filename}
        </span>
        {isVerified && (
          <div className="flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px] uppercase font-bold text-emerald-400 border border-emerald-500/20 shrink-0">
            <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
            Verified
          </div>
        )}
        {isOCR && (
          <div className="flex items-center gap-1 bg-blue-500/10 px-2 py-0.5 rounded text-[9px] uppercase font-bold text-blue-400 border border-blue-500/20 shrink-0">
            <ScanText className="size-2.5" />
            OCR
          </div>
        )}
      </div>

      {/* Center: Page Navigation */}
      <div className="hidden sm:flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => handlePageChange(page - 1)}
          disabled={page <= 1}
          className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer disabled:opacity-30"
        >
          <ChevronLeft className="size-3.5" />
        </Button>
        <span className="text-xs font-mono text-on-surface tabular-nums">
          <input
            type="number"
            value={page}
            onChange={(e) => handlePageChange(Number(e.target.value))}
            className="w-8 bg-surface-container border border-outline-variant rounded px-1 py-0.5 text-center text-xs text-on-surface outline-none focus:ring-1 focus:ring-primary [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            min={1}
            max={totalPages}
          />
          <span className="text-on-surface-variant/50 mx-1">/</span>
          <span className="text-on-surface-variant/70">{totalPages}</span>
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => handlePageChange(page + 1)}
          disabled={page >= totalPages}
          className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer disabled:opacity-30"
        >
          <ChevronRight className="size-3.5" />
        </Button>
      </div>

      {/* Right: Zoom, Version History & Actions */}
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* Zoom */}
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={onZoomOut} className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer" title="Zoom Out">
            <ZoomOut className="size-4" />
          </Button>
          <span className="text-xs font-mono text-on-surface w-10 text-center tabular-nums">{zoom}%</span>
          <Button variant="ghost" size="icon" onClick={onZoomIn} className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer" title="Zoom In">
            <ZoomIn className="size-4" />
          </Button>
        </div>

        <div className="w-px h-4 bg-outline-variant hidden sm:block" />

        {/* Version History Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer" title="Version History">
              <History className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64 bg-surface border border-outline-variant p-1.5 shadow-lg text-on-surface z-50">
            <DropdownMenuLabel className="px-2 py-1.5 text-xs font-semibold text-on-surface-variant">Version History</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-outline-variant" />
            {VERSION_HISTORY.map((v) => (
              <DropdownMenuItem
                key={v.version}
                className={cn(
                  "cursor-pointer hover:bg-surface-container-high px-3 py-2 text-xs rounded flex items-center justify-between",
                  v.isCurrent && "bg-primary/5"
                )}
                onClick={() => toast.success(`Loaded version ${v.version} — ${v.date}`)}
              >
                <div>
                  <span className="font-semibold block">{v.version}{v.isCurrent ? " (Current)" : ""}</span>
                  <span className="text-[10px] text-on-surface-variant/60">{v.author} · {v.date}</span>
                </div>
                <Button variant="ghost" size="icon" className="size-6 text-on-surface-variant hover:text-primary cursor-pointer" onClick={(e) => { e.stopPropagation(); toast.info(`Preview ${v.version}`); }}>
                  <Eye className="size-3" />
                </Button>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Download & Share */}
        <Button variant="ghost" size="icon" onClick={onDownload} className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer" title="Download">
          <Download className="size-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={onShare} className="size-7 text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors cursor-pointer" title="Share">
          <Share2 className="size-4" />
        </Button>
      </div>
    </div>
  );
}
