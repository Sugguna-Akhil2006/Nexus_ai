"use client";

import Link from "next/link";
import { motion, Variants } from "framer-motion";
import { Button } from "@/components/ui/button";

export default function Hero() {
  // Stagger wrapper container variants
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.1,
      },
    },
  };

  // Individual element animation variants
  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 15,
      },
    },
  };

  return (
    <section className="relative flex flex-col items-center justify-center text-center px-6 py-16 md:py-24 lg:py-32 overflow-hidden border-b border-outline-variant/30">
      {/* Background soft ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[250px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-4xl mx-auto space-y-6 relative z-10"
      >
        {/* Status Badge */}
        <motion.div variants={itemVariants} className="inline-flex justify-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container-low border border-outline-variant select-none">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest">
              Enterprise Nexus v2.4 Now Live
            </span>
          </div>
        </motion.div>

        {/* Title */}
        <motion.h2 
          variants={itemVariants} 
          className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-on-surface leading-[1.1] max-w-3xl mx-auto"
        >
          Orchestrate Intelligence at <br />
          <span className="text-primary italic font-serif">Global Scale.</span>
        </motion.h2>

        {/* Subtitle / Description */}
        <motion.p 
          variants={itemVariants} 
          className="text-base sm:text-lg text-on-surface-variant max-w-2xl mx-auto font-normal leading-relaxed"
        >
          The autonomous workspace designed for high-performance engineering teams. Integrate, analyze, and automate your entire document lifecycle with a single API.
        </motion.p>

        {/* Action Buttons */}
        <motion.div 
          variants={itemVariants} 
          className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
        >
          <Link href="/dashboard" className="w-full sm:w-auto">
            <Button 
              className="w-full px-8 py-6 bg-primary text-primary-foreground text-base font-semibold rounded-lg shadow-lg hover:bg-primary/95 hover:shadow-primary/20 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer border-none"
            >
              Get Started
            </Button>
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
}
