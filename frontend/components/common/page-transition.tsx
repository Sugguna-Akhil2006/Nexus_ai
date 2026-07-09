"use client";

import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";

interface PageTransitionProps {
  children: React.ReactNode;
}

/**
 * Wraps page content with a subtle fade + slide-up animation on route change.
 * Uses AnimatePresence with pathname as the key to trigger exit/enter transitions.
 *
 * Place this inside the dashboard layout around {children}.
 */
export default function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }}
        transition={{
          duration: 0.2,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
        className="flex-1"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
