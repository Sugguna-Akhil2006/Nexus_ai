"use client";

import { LineChart, Code, Palette, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CategoryData {
  id: string;
  name: string;
  description: string;
  iconType: "analytics" | "code" | "creative" | "security";
  iconColorClass: string;
}

interface CategoryCardProps {
  category: CategoryData;
  isActive?: boolean;
  onClick: () => void;
}

export default function CategoryCard({ category, isActive = false, onClick }: CategoryCardProps) {
  const getIcon = (type: string) => {
    switch (type) {
      case "analytics":
        return LineChart;
      case "code":
        return Code;
      case "creative":
        return Palette;
      default: // security
        return ShieldAlert;
    }
  };

  const IconComp = getIcon(category.iconType);

  return (
    <div
      onClick={onClick}
      className={cn(
        "group bg-surface-container-low border border-outline-variant p-5 rounded-xl hover:bg-surface-container transition-all cursor-pointer select-none shadow-sm flex flex-col justify-between h-full hover:border-primary/30",
        isActive && "bg-surface-container border-primary/50 ring-1 ring-primary/20"
      )}
    >
      <div>
        {/* Icon wrapper (scales on hover) */}
        <div className="w-11 h-11 bg-surface-container-highest rounded-lg flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-300 shadow-inner">
          <IconComp className={cn("size-5", category.iconColorClass)} />
        </div>
        
        <h4 className="text-sm md:text-base font-bold text-on-surface mb-2 tracking-tight group-hover:text-primary transition-colors">
          {category.name}
        </h4>
        <p className="text-xs md:text-sm text-on-surface-variant/80 leading-relaxed font-normal">
          {category.description}
        </p>
      </div>
    </div>
  );
}
