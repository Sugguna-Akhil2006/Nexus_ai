"use client";

import { User, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ScanItem {
  id: string;
  candidateName: string;
  uploadTime: string;
  fileType: string;
  role: string;
  score: number;
  status: "Interviewed" | "Shortlisted" | "Archived" | "New";
}

interface RecentScansProps {
  scans: ScanItem[];
  activeScanId?: string;
  onSelectScan: (id: string) => void;
}

export default function RecentScans({
  scans,
  activeScanId,
  onSelectScan,
}: RecentScansProps) {
  const getScoreColorClass = (val: number) => {
    if (val >= 80) return "text-primary";
    if (val >= 60) return "text-tertiary";
    return "text-error";
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case "Interviewed":
        return "bg-primary/10 text-primary border-primary/20";
      case "Shortlisted":
        return "bg-green-400/10 text-green-400 border-green-400/20";
      case "Archived":
        return "bg-surface-container-highest text-on-surface-variant border-outline-variant/30";
      default: // New
        return "bg-tertiary/10 text-tertiary border-tertiary/20";
    }
  };

  return (
    <section className="space-y-4 select-none">
      <h3 className="text-base md:text-lg font-bold text-on-surface uppercase tracking-wider pl-0.5">
        Recent Scans
      </h3>

      <div className="bg-surface-container-low border border-outline-variant rounded-xl divide-y divide-outline-variant/50 overflow-hidden shadow-sm">
        {scans.map((scan) => {
          const isActive = activeScanId === scan.id;
          const scoreColor = getScoreColorClass(scan.score);
          const statusBadge = getStatusBadgeClass(scan.status);

          return (
            <div
              key={scan.id}
              onClick={() => onSelectScan(scan.id)}
              className={cn(
                "p-4 flex flex-wrap md:flex-nowrap items-center gap-4 hover:bg-surface-container-high transition-colors group cursor-pointer select-none",
                isActive && "bg-surface-container-high border-l-2 border-primary pl-3.5"
              )}
            >
              {/* User avatar thumbnail */}
              <div className={cn(
                "w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center transition-colors group-hover:bg-primary/10 group-hover:text-primary",
                isActive ? "text-primary bg-primary/10" : "text-on-surface-variant"
              )}>
                <User className="size-5" />
              </div>

              {/* Name Details */}
              <div className="flex-grow min-w-[200px]">
                <p className="text-xs md:text-sm font-bold text-on-surface leading-tight group-hover:text-primary transition-colors">
                  {scan.candidateName}
                </p>
                <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
                  Uploaded {scan.uploadTime} &bull; {scan.fileType}
                </p>
              </div>

              {/* Role Title Column (Hidden on mobile) */}
              <div className="px-4 hidden lg:block w-48 truncate">
                <p className="text-[9px] uppercase tracking-widest text-on-surface-variant/60 font-bold mb-0.5">
                  Role
                </p>
                <p className="text-xs md:text-sm text-on-surface font-semibold truncate">
                  {scan.role}
                </p>
              </div>

              {/* Score Value Column */}
              <div className="px-4 w-20 shrink-0">
                <p className="text-[9px] uppercase tracking-widest text-on-surface-variant/60 font-bold mb-0.5">
                  Score
                </p>
                <p className={cn("font-mono text-xs md:text-sm font-bold", scoreColor)}>
                  {scan.score}/100
                </p>
              </div>

              {/* Status and Action arrow */}
              <div className="flex gap-4 items-center shrink-0 ml-auto md:ml-0">
                <span className={cn("px-2.5 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-full border leading-none", statusBadge)}>
                  {scan.status}
                </span>
                <ArrowRight className="size-4 text-on-surface-variant group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          );
        })}

        {scans.length === 0 && (
          <div className="p-8 text-center text-xs md:text-sm text-on-surface-variant/50 italic">
            No recent scans recorded. Upload a resume above to begin.
          </div>
        )}
      </div>
    </section>
  );
}
