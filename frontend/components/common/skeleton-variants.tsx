"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * Pre-built skeleton variants matching common UI patterns across the application.
 * Each variant mirrors the exact layout of its corresponding populated component
 * so transitions from loading → loaded feel seamless.
 */

// ─── Stat / Metric Card ──────────────────────────────────────────────────────
export function SkeletonStatCard({ className }: { className?: string }) {
  return (
    <div className={cn("bg-surface-container border border-outline-variant p-5 rounded-xl flex items-center gap-4", className)}>
      <Skeleton className="w-10 h-10 rounded-lg shrink-0 bg-surface-container-highest" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-2.5 w-20 rounded bg-surface-container-highest" />
        <Skeleton className="h-5 w-16 rounded bg-surface-container-highest" />
      </div>
    </div>
  );
}

// ─── Project / Feature Card ──────────────────────────────────────────────────
export function SkeletonProjectCard({ className }: { className?: string }) {
  return (
    <div className={cn("bg-surface-container-low border border-outline-variant rounded-xl p-5 space-y-4", className)}>
      <div className="flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded-lg shrink-0 bg-surface-container-highest" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4 rounded bg-surface-container-highest" />
          <Skeleton className="h-2.5 w-1/2 rounded bg-surface-container-highest" />
        </div>
      </div>
      <Skeleton className="h-2 w-full rounded-full bg-surface-container-highest" />
      <div className="flex items-center justify-between">
        <div className="flex -space-x-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="w-7 h-7 rounded-full border-2 border-surface-container-low bg-surface-container-highest" />
          ))}
        </div>
        <Skeleton className="h-3 w-12 rounded bg-surface-container-highest" />
      </div>
    </div>
  );
}

// ─── Table Row ───────────────────────────────────────────────────────────────
export function SkeletonTableRow({ columns = 4, className }: { columns?: number; className?: string }) {
  return (
    <div className={cn("flex items-center gap-4 px-4 py-3.5 border-b border-outline-variant/20", className)}>
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-3 rounded bg-surface-container-highest",
            i === 0 ? "w-1/4" : i === columns - 1 ? "w-16" : "flex-1"
          )}
        />
      ))}
    </div>
  );
}

// ─── Chart Placeholder ───────────────────────────────────────────────────────
export function SkeletonChart({ className, height = "h-44" }: { className?: string; height?: string }) {
  return (
    <div className={cn("bg-surface-container-low border border-outline-variant rounded-xl p-5 space-y-4", className)}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32 rounded bg-surface-container-highest" />
        <Skeleton className="h-3 w-16 rounded bg-surface-container-highest" />
      </div>
      <div className={cn("w-full rounded-lg bg-surface-container flex items-end gap-1.5 px-4 pb-2 pt-6", height)}>
        {Array.from({ length: 10 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t bg-surface-container-highest"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))}
      </div>
    </div>
  );
}

// ─── List Item ───────────────────────────────────────────────────────────────
export function SkeletonListItem({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-3 p-3 rounded-lg", className)}>
      <Skeleton className="w-8 h-8 rounded-full shrink-0 bg-surface-container-highest" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-3 w-3/5 rounded bg-surface-container-highest" />
        <Skeleton className="h-2 w-2/5 rounded bg-surface-container-highest" />
      </div>
      <Skeleton className="h-3 w-10 rounded bg-surface-container-highest shrink-0" />
    </div>
  );
}

// ─── Avatar Group ────────────────────────────────────────────────────────────
export function SkeletonAvatarGroup({ count = 4, className }: { count?: number; className?: string }) {
  return (
    <div className={cn("flex -space-x-2", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton
          key={i}
          className="w-8 h-8 rounded-full border-2 border-surface bg-surface-container-highest"
        />
      ))}
    </div>
  );
}

// ─── Full Page Skeleton ──────────────────────────────────────────────────────
export function SkeletonPage({ className }: { className?: string }) {
  return (
    <div className={cn("p-6 md:p-8 space-y-8 animate-in fade-in-0 duration-300", className)}>
      {/* Header */}
      <div className="flex items-end justify-between border-b border-outline-variant/30 pb-6">
        <div className="space-y-2">
          <Skeleton className="h-6 w-48 rounded bg-surface-container-highest" />
          <Skeleton className="h-3 w-72 rounded bg-surface-container-highest" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-9 w-28 rounded-lg bg-surface-container-highest" />
          <Skeleton className="h-9 w-28 rounded-lg bg-surface-container-highest" />
        </div>
      </div>
      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <SkeletonStatCard key={i} />
        ))}
      </div>
      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <SkeletonChart height="h-56" />
        </div>
        <div className="lg:col-span-4 space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonListItem key={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
