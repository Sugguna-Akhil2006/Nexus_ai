"use client";

import { useEffect, useRef } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedCounterProps {
  /** Target value to count up to */
  value: number;
  /** Duration in seconds (default: 1.2) */
  duration?: number;
  /** Number of decimal places (default: 0) */
  decimals?: number;
  /** Prefix string (e.g., "$", "#") */
  prefix?: string;
  /** Suffix string (e.g., "%", "k", "ms") */
  suffix?: string;
  /** Optional className for the wrapper span */
  className?: string;
  /** Format with locale-aware commas (default: true) */
  formatted?: boolean;
}

/**
 * Animated number counter that smoothly counts from 0 to a target value on mount.
 * Uses framer-motion's spring animation for natural easing.
 *
 * @example
 * <AnimatedCounter value={1482} suffix=" commits" />
 * <AnimatedCounter value={94.2} suffix="%" decimals={1} />
 * <AnimatedCounter value={12400} prefix="$" formatted />
 */
export default function AnimatedCounter({
  value,
  duration = 1.2,
  decimals = 0,
  prefix = "",
  suffix = "",
  className,
  formatted = true,
}: AnimatedCounterProps) {
  const motionValue = useMotionValue(0);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration,
      ease: [0.25, 0.46, 0.45, 0.94], // Custom cubic-bezier for smooth deceleration
    });

    const unsubscribe = motionValue.on("change", (latest) => {
      if (ref.current) {
        let display: string;
        if (decimals > 0) {
          display = latest.toFixed(decimals);
        } else {
          display = Math.round(latest).toString();
        }

        if (formatted && decimals === 0) {
          display = Number(display).toLocaleString("en-US");
        }

        ref.current.textContent = `${prefix}${display}${suffix}`;
      }
    });

    return () => {
      controls.stop();
      unsubscribe();
    };
  }, [value, duration, decimals, prefix, suffix, formatted, motionValue]);

  return (
    <span
      ref={ref}
      className={cn("tabular-nums", className)}
      aria-label={`${prefix}${value}${suffix}`}
    >
      {prefix}0{suffix}
    </span>
  );
}
