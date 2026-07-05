"use client";

import { motion } from "framer-motion";

interface StatItem {
  value: string;
  label: string;
}

const STATS: StatItem[] = [
  { value: "1,240+", label: "Verified Agents" },
  { value: "2.4M", label: "Agent Executions" },
  { value: "99.9%", label: "Uptime SLA" },
];

export default function StatsSection() {
  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-6 select-none shrink-0">
      {STATS.map((stat, idx) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: idx * 0.1 }}
          className="bg-surface-container p-6 border border-outline-variant/50 rounded-xl text-center shadow-sm select-none hover:border-primary/20 transition-colors"
        >
          <span className="text-3xl md:text-4xl font-bold tracking-tight text-primary block mb-1">
            {stat.value}
          </span>
          <span className="text-[10px] md:text-xs font-bold uppercase tracking-widest text-on-surface-variant/70 block">
            {stat.label}
          </span>
        </motion.div>
      ))}
    </section>
  );
}
