"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseRealtimeSimulationOptions {
  /** Initial value */
  initialValue: number;
  /** Minimum value in the range */
  min: number;
  /** Maximum value in the range */
  max: number;
  /** Update interval in milliseconds (default: 3000) */
  intervalMs?: number;
  /** Maximum change per tick as a fraction of the range (default: 0.08) */
  volatility?: number;
  /** Number of decimal places (default: 0) */
  decimals?: number;
  /** Whether the simulation is active (default: true) */
  enabled?: boolean;
}

/**
 * Simulates a live data feed by periodically mutating a value within
 * a bounded range with configurable volatility.
 *
 * Useful for CPU usage, memory consumption, active users, token rates,
 * and other metrics that should feel "alive" in the UI.
 *
 * @example
 * const cpuUsage = useRealtimeSimulation({
 *   initialValue: 42,
 *   min: 10,
 *   max: 95,
 *   intervalMs: 3000,
 *   volatility: 0.1,
 * });
 *
 * return <span>{cpuUsage}%</span>;
 */
export function useRealtimeSimulation({
  initialValue,
  min,
  max,
  intervalMs = 3000,
  volatility = 0.08,
  decimals = 0,
  enabled = true,
}: UseRealtimeSimulationOptions): number {
  const [value, setValue] = useState(initialValue);
  const valueRef = useRef(initialValue);

  useEffect(() => {
    if (!enabled) return;

    const range = max - min;

    const tick = () => {
      // Random walk with mean-reversion toward center
      const center = (min + max) / 2;
      const current = valueRef.current;
      
      // Bias toward center to prevent sticking at extremes
      const meanReversionForce = (center - current) / range * 0.15;
      
      // Random component
      const randomDelta = (Math.random() - 0.5) * 2 * volatility * range;
      
      // Combined change
      let next = current + randomDelta + meanReversionForce * range;
      
      // Clamp to bounds
      next = Math.max(min, Math.min(max, next));
      
      // Round to decimals
      const factor = Math.pow(10, decimals);
      next = Math.round(next * factor) / factor;

      valueRef.current = next;
      setValue(next);
    };

    const interval = setInterval(tick, intervalMs);
    return () => clearInterval(interval);
  }, [min, max, intervalMs, volatility, decimals, enabled]);

  return value;
}
