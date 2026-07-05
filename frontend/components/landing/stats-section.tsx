"use client";

import { motion, Variants } from "framer-motion";

interface StatItem {
  value: string;
  label: string;
}

const STATS: StatItem[] = [
  { value: "99.99%", label: "Uptime SLA" },
  { value: "250ms", label: "P95 Latency" },
  { value: "500k+", label: "Daily Ops" },
  { value: "Zero", label: "Cold Starts" },
];

export default function StatsSection() {
  const containerVariants: Variants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut",
      },
    },
  };

  return (
    <section className="border-y border-outline-variant bg-surface-container-lowest overflow-hidden">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        className="max-w-7xl mx-auto px-6 py-12 md:py-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center"
      >
        {STATS.map((stat) => (
          <motion.div
            key={stat.label}
            variants={itemVariants}
            className="space-y-1 group"
          >
            <div className="text-3xl md:text-4xl lg:text-5xl font-bold text-primary tracking-tight font-sans transition-transform duration-300 group-hover:scale-105 select-none">
              {stat.value}
            </div>
            <div className="text-[10px] md:text-xs font-semibold text-on-surface-variant uppercase tracking-widest">
              {stat.label}
            </div>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
