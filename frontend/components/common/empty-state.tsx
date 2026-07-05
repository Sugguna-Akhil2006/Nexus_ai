"use client";

import React from "react";
import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
  accentColor?: "primary" | "secondary" | "tertiary" | "success" | "warning";
}

const ACCENT_STYLES = {
  primary: {
    iconBg: "bg-primary/10 border-primary/20 text-primary",
    glow: "bg-primary/10",
    ring: "focus-visible:ring-primary/20 focus-visible:border-primary/40",
  },
  secondary: {
    iconBg: "bg-secondary/15 border-secondary/20 text-secondary",
    glow: "bg-secondary/15",
    ring: "focus-visible:ring-secondary/20 focus-visible:border-secondary/40",
  },
  tertiary: {
    iconBg: "bg-violet-500/10 border-violet-500/20 text-violet-400",
    glow: "bg-violet-500/5",
    ring: "focus-visible:ring-violet-500/20 focus-visible:border-violet-500/40",
  },
  success: {
    iconBg: "bg-green-500/10 border-green-500/20 text-green-400",
    glow: "bg-green-500/5",
    ring: "focus-visible:ring-green-500/20 focus-visible:border-green-500/40",
  },
  warning: {
    iconBg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    glow: "bg-amber-500/5",
    ring: "focus-visible:ring-amber-500/20 focus-visible:border-amber-500/40",
  },
};

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className,
  accentColor = "primary",
}: EmptyStateProps) {
  const styles = ACCENT_STYLES[accentColor];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn(
        "relative overflow-hidden w-full max-w-2xl mx-auto rounded-2xl border border-outline-variant bg-surface-container-low/40 p-8 md:p-12 text-center backdrop-blur-sm select-none group shadow-lg",
        className
      )}
    >
      {/* Decorative background glow */}
      <div
        className={cn(
          "absolute -top-12 left-1/2 -translate-x-1/2 w-48 h-48 rounded-full filter blur-[60px] opacity-60 pointer-events-none transition-all duration-500 group-hover:scale-110",
          styles.glow
        )}
      />

      <div className="relative flex flex-col items-center gap-6 z-10">
        {/* Icon container with hover animation */}
        <motion.div
          whileHover={{ scale: 1.05, rotate: [0, -5, 5, 0] }}
          transition={{ duration: 0.4 }}
          className={cn(
            "w-16 h-16 rounded-2xl border flex items-center justify-center shadow-inner relative overflow-hidden",
            styles.iconBg
          )}
        >
          <Icon className="size-8 relative z-10" />
          <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </motion.div>

        {/* Message */}
        <div className="space-y-2 max-w-md">
          <h3 className="text-xl font-bold tracking-tight text-on-surface">
            {title}
          </h3>
          <p className="text-sm text-on-surface-variant leading-relaxed">
            {description}
          </p>
        </div>

        {/* Actions */}
        {(actionLabel || secondaryActionLabel) && (
          <div className="flex flex-col sm:flex-row items-center gap-3 mt-2">
            {secondaryActionLabel && onSecondaryAction && (
              <Button
                variant="outline"
                onClick={onSecondaryAction}
                className="w-full sm:w-auto px-5 py-2 hover:bg-surface-container-high hover:text-on-surface border-outline-variant cursor-pointer text-xs font-semibold"
              >
                {secondaryActionLabel}
              </Button>
            )}
            
            {actionLabel && onAction && (
              <Button
                onClick={onAction}
                className="w-full sm:w-auto px-6 py-2 bg-primary text-primary-foreground font-semibold hover:bg-primary/95 active:scale-95 transition-transform cursor-pointer border-none text-xs flex items-center justify-center gap-2"
              >
                {actionLabel}
              </Button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
