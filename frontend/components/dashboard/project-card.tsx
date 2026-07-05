"use client";

import Image from "next/image";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ProjectMember {
  name: string;
  avatarUrl: string;
}

export interface ProjectCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "In Progress" | "Staging" | "Active";
  statusColorClass: string;
  progress: number;
  progressBarColorClass: string;
  members: ProjectMember[];
  extraMembers?: number;
  iconBgClass?: string;
}

export default function ProjectCard({
  title,
  description,
  icon: Icon,
  status,
  statusColorClass,
  progress,
  progressBarColorClass,
  members,
  extraMembers = 0,
  iconBgClass = "bg-primary/10 border-primary/20",
}: ProjectCardProps) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="bg-surface-container-low border border-outline-variant p-6 rounded-xl flex flex-col justify-between h-full group shadow-md hover:border-outline-variant/80 transition-shadow duration-200"
    >
      <div className="space-y-6">
        {/* Card Header Info */}
        <div className="flex justify-between items-start">
          <div className={cn(
            "w-12 h-12 rounded-lg border flex items-center justify-center text-primary transition-transform duration-300 group-hover:scale-105",
            iconBgClass
          )}>
            <Icon className="size-6" />
          </div>
          <span className={cn("text-xs font-semibold font-mono uppercase tracking-wider select-none", statusColorClass)}>
            {status}
          </span>
        </div>

        {/* Project Texts */}
        <div className="space-y-1">
          <h4 className="text-xl font-semibold text-on-surface tracking-tight leading-tight">
            {title}
          </h4>
          <p className="text-sm text-on-surface-variant font-normal leading-relaxed">
            {description}
          </p>
        </div>
      </div>

      {/* Progress & Team metrics */}
      <div className="space-y-4 mt-6">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-on-surface-variant">Progress</span>
            <span className="text-on-surface">{progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-surface-container-high rounded-full overflow-hidden select-none">
            <div 
              className={cn("h-full rounded-full transition-all duration-500 ease-out", progressBarColorClass)}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Team Avatars & Navigate arrow */}
        <div className="flex items-center justify-between pt-2 border-t border-outline-variant/30">
          <div className="flex items-center -space-x-2">
            {members.map((member, index) => (
              <div 
                key={member.name}
                className="w-8 h-8 rounded-full border-2 border-surface bg-surface-container-high overflow-hidden relative shadow-sm hover:translate-y-[-2px] hover:z-20 transition-all duration-150"
                title={member.name}
              >
                <Image
                  alt={member.name}
                  src={member.avatarUrl}
                  fill
                  sizes="32px"
                  className="object-cover"
                />
              </div>
            ))}
            
            {/* Excess count badge */}
            {extraMembers > 0 && (
              <div className="w-8 h-8 rounded-full border-2 border-surface bg-surface-container flex items-center justify-center text-[10px] font-bold text-on-surface-variant select-none shadow-sm">
                +{extraMembers}
              </div>
            )}
          </div>

          {/* Action icon */}
          <button 
            aria-label={`Open project ${title}`}
            className="text-on-surface-variant hover:text-primary transition-all p-1.5 rounded-lg hover:bg-surface-container-high/60 cursor-pointer"
          >
            <ArrowRight className="size-5 transition-transform duration-200 group-hover:translate-x-1" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
