"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseSimulatedLoadingOptions<T> {
  /** The data to return after loading completes */
  data: T;
  /** Delay in milliseconds before data is revealed (default: 600) */
  delayMs?: number;
  /** Whether to re-trigger loading when data reference changes (default: false) */
  reloadOnChange?: boolean;
}

interface UseSimulatedLoadingResult<T> {
  /** Whether the simulated loading is in progress */
  isLoading: boolean;
  /** The data (null while loading, then the provided data) */
  data: T | null;
  /** Manually trigger a reload */
  reload: () => void;
}

/**
 * Simulates a network fetch delay before revealing data.
 * Returns isLoading and data, with data being null during the loading phase.
 * Used to show skeleton states on initial page mount.
 *
 * @example
 * const { isLoading, data } = useSimulatedLoading({ data: PROJECTS, delayMs: 500 });
 *
 * if (isLoading) return <SkeletonProjectCard />;
 * return <ProjectCard data={data} />;
 */
export function useSimulatedLoading<T>({
  data,
  delayMs = 600,
  reloadOnChange = false,
}: UseSimulatedLoadingOptions<T>): UseSimulatedLoadingResult<T> {
  const [isLoading, setIsLoading] = useState(true);
  const [resolved, setResolved] = useState<T | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const startLoading = useCallback(() => {
    setIsLoading(true);
    setResolved(null);

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Add slight randomness to feel more natural (±15%)
    const jitter = delayMs * (0.85 + Math.random() * 0.3);

    timerRef.current = setTimeout(() => {
      if (mountedRef.current) {
        setResolved(data);
        setIsLoading(false);
      }
    }, jitter);
  }, [data, delayMs]);

  // Initial load
  useEffect(() => {
    mountedRef.current = true;
    startLoading();

    return () => {
      mountedRef.current = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
    // Only re-run on mount or when reloadOnChange triggers
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadOnChange ? data : undefined]);

  const reload = useCallback(() => {
    startLoading();
  }, [startLoading]);

  return { isLoading, data: resolved, reload };
}
