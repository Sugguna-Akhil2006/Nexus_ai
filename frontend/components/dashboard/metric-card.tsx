"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  className?: string;
}

export default function MetricCard({
  title,
  value,
  icon: Icon,
  className,
}: MetricCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className={cn(
        "bg-surface-container-low border border-outline-variant p-4 rounded-xl flex items-center gap-4 shadow-sm hover:border-outline-variant/80 transition-shadow duration-200 group",
        className
      )}
    >
      {/* Icon frame */}
      <div className="w-12 h-12 bg-surface-container-highest border border-outline-variant/40 rounded-lg flex items-center justify-center text-primary transition-transform duration-300 group-hover:scale-105 shrink-0 select-none">
        <Icon className="size-6" />
      </div>

      {/* Texts */}
      <div className="flex flex-col">
        <span className="text-[10px] md:text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
          {title}
        </span>
        <span className="text-xl md:text-2xl font-bold font-mono text-on-surface tracking-tight mt-0.5 select-all">
          {value}
        </span>
      </div>
    </motion.div>
  );
}
