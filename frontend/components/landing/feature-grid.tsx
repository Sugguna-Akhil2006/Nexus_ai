"use client";

import Image from "next/image";
import { Terminal, ShieldCheck, Network } from "lucide-react";
import { motion } from "framer-motion";
import FeatureCard from "./feature-card";

export default function FeatureGrid() {
  const analyticsImageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuBjMq-LhDZ5GXloRq_1Kr9dtiplzZMh-kvd3gSuz7S2Er1Tt9EHoSmf7aQ_11YIYHkQfWYIe3F_rdT_hWGufB1HsHQYSheD05EcmiBwr2OcJ0ICjT7jc5vNpu9goQ-o395k5rZR-zo_wCVN0EPCGSDhE93YOa7MLBlIW6Zki1d4Q2pJBstLvjC2J1j_wa3n86oF_Xf7Mb7i-WCcQlrajatMkFEQ92ACHKOZmGBHxEEyvhsLflM2n4q6B7ShLcS42SFHRtBXuetO4xfR";

  return (
    <section className="max-w-7xl mx-auto px-6 py-16 md:py-24">
      {/* Section Header */}
      <div className="mb-12 md:mb-16 space-y-2">
        <motion.h3 
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-2xl md:text-3xl font-bold text-on-surface tracking-tight"
        >
          Technical Foundations
        </motion.h3>
        <motion.p 
          initial={{ opacity: 0, x: -20 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-sm md:text-base text-on-surface-variant font-medium"
        >
          Built for the demands of modern infrastructure.
        </motion.p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-12 gap-6">
        
        {/* Card 1: Command-Line Intelligence (col-span-12 md:col-span-8, 400px height) */}
        <FeatureCard
          title="Command-Line Intelligence"
          description="Nexus provides a robust CLI and SDK suite, allowing developers to script AI operations directly into existing CI/CD pipelines."
          icon={Terminal}
          className="col-span-12 md:col-span-8 min-h-[380px] md:h-[400px]"
        >
          <div className="p-4 bg-surface-container-lowest rounded-lg border border-outline-variant font-mono text-xs md:text-sm text-primary relative overflow-hidden group select-all">
            <code className="relative z-10 block select-all">$ nexus deploy --agent="analytical-ops" --region="us-east"</code>
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
          </div>
        </FeatureCard>

        {/* Card 2: SOC-2 Compliant (col-span-12 md:col-span-4, 400px height, centered text and icon) */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.1 }}
          className="col-span-12 md:col-span-4 min-h-[380px] md:h-[400px] bg-surface-container-low border border-outline-variant rounded-2xl p-6 md:p-8 flex flex-col items-center justify-center text-center group shadow-md transition-all duration-300 hover:border-primary/30 hover:shadow-primary/5"
        >
          <div className="w-24 h-24 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-6 text-primary group-hover:scale-105 transition-transform duration-300 shadow-inner">
            <ShieldCheck className="size-12" />
          </div>
          <h4 className="text-xl md:text-2xl font-semibold text-on-surface tracking-tight leading-tight">
            SOC-2 Compliant
          </h4>
          <p className="text-sm md:text-base text-on-surface-variant leading-relaxed max-w-[280px] mt-2 font-normal">
            Enterprise-grade encryption and regional data residency by default.
          </p>
        </motion.div>

        {/* Card 3: Real-time Analytics (col-span-12 md:col-span-6, 350px height) */}
        <FeatureCard
          title="Real-time Analytics"
          description="Monitor agent health and token consumption with millisecond precision."
          className="col-span-12 md:col-span-6 min-h-[330px] md:h-[350px]"
        >
          <div className="w-full h-32 md:h-36 bg-surface-container-highest rounded-lg overflow-hidden border border-outline-variant relative group/image mt-4">
            <Image
              alt="Analytics View"
              src={analyticsImageUrl}
              fill
              sizes="(max-w-768px) 100vw, 40vw"
              className="w-full h-full object-cover grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-500"
            />
          </div>
        </FeatureCard>

        {/* Card 4: Vector Memory (col-span-12 md:col-span-6, 350px height) */}
        <FeatureCard
          title="Vector Memory"
          description="Semantic search that understands the context of your entire document corpus."
          className="col-span-12 md:col-span-6 min-h-[330px] md:h-[350px]"
        >
          <div className="relative flex-grow h-32 md:h-36 mt-4 flex items-center justify-center overflow-hidden">
            {/* Background vector hub icon */}
            <Network className="text-outline size-24 md:size-28 opacity-10 absolute pointer-events-none" />
            
            {/* Pulsing ring animation */}
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div
                animate={{
                  scale: [1, 1.8, 1],
                  opacity: [0.15, 0.4, 0.15],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="w-24 h-24 border border-primary/30 rounded-full"
              />
              <motion.div
                animate={{
                  scale: [1.2, 2.2, 1.2],
                  opacity: [0.1, 0.3, 0.1],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 1.5,
                }}
                className="w-24 h-24 border border-primary/20 rounded-full"
              />
            </div>
            
            {/* Central glowing hub dot */}
            <div className="w-3 h-3 rounded-full bg-primary relative z-10 shadow-[0_0_15px_rgba(59,130,246,0.8)]" />
          </div>
        </FeatureCard>

      </div>
    </section>
  );
}
