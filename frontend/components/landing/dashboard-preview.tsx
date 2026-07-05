"use client";

import Image from "next/image";
import { motion } from "framer-motion";

export default function DashboardPreview() {
  const dashboardImageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuCgSL3vy-m7j5TkbcKXwcZzANkF4RO_JIQhccwyECk5Qtn37FVVcvRpTkg80nYZ4kWTb2DZVj48vT1Cbn9TSAe8DL21-SB2EBhkjvDwok0l_GwlfeAgkozCayecriD86SipybT-FTNzOGbJEvWjJ7u9ac0x8qpnzSza7M4nDwWjDFaWseZihUT9n8P4UJ3hU-86mqW_nzJd6486QxKsQzFMT7zS_iLUREuwmCivfHAw8UBhHT5R4u-FE2XEUXznOLcsiUDIbarMtSf3";

  return (
    <section className="px-6 pb-20 md:pb-28">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-5xl mx-auto rounded-2xl border border-outline-variant bg-surface-container-low p-2 shadow-2xl overflow-hidden custom-glow transition-shadow duration-300 hover:shadow-primary/10"
      >
        <div className="aspect-[16/9] md:aspect-[16/10] lg:aspect-[16/9] w-full relative rounded-xl overflow-hidden border border-outline-variant group">
          <Image
            alt="A high-fidelity software dashboard interface showing complex data visualizations, AI agent task flows, and collaborative document editing."
            src={dashboardImageUrl}
            fill
            priority
            sizes="(max-w-768px) 100vw, (max-w-1200px) 90vw, 1024px"
            className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.01]"
          />
          {/* Subtle dark overlay at the bottom matching Stitch style */}
          <div className="absolute inset-0 bg-gradient-to-t from-surface-container-low/90 via-transparent to-transparent opacity-80 pointer-events-none" />
        </div>
      </motion.div>
    </section>
  );
}
