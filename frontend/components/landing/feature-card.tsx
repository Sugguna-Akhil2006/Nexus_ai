"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FeatureCardProps {
  title: string;
  description: string;
  className?: string;
  icon?: React.ComponentType<{ className?: string }>;
  children?: React.ReactNode;
}

export default function FeatureCard({
  title,
  description,
  className,
  icon: Icon,
  children,
}: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn(
        "bg-surface-container-low border border-outline-variant rounded-2xl p-6 md:p-8 flex flex-col justify-between overflow-hidden group shadow-md transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5",
        className
      )}
    >
      <div className="space-y-4">
        {/* Optional Icon Header */}
        {Icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20 text-primary group-hover:scale-105 transition-transform duration-300">
            <Icon className="size-6" />
          </div>
        )}

        {/* Text Area */}
        <div className="space-y-2">
          <h4 className="text-xl md:text-2xl font-semibold text-on-surface tracking-tight leading-tight">
            {title}
          </h4>
          <p className="text-sm md:text-base text-on-surface-variant leading-relaxed max-w-lg font-normal">
            {description}
          </p>
        </div>
      </div>

      {/* Card Custom Children Content (CLI script, graphics, images, animations) */}
      {children && (
        <div className="mt-6 w-full flex-grow flex flex-col justify-end">
          {children}
        </div>
      )}
    </motion.div>
  );
}
