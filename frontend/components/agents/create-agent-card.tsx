"use client";

import { Plus } from "lucide-react";

interface CreateAgentCardProps {
  onClick: () => void;
}

export default function CreateAgentCard({ onClick }: CreateAgentCardProps) {
  return (
    <div
      onClick={onClick}
      className="border-2 border-dashed border-outline-variant hover:border-primary/50 rounded-xl p-6 flex flex-col items-center justify-center text-center hover:bg-primary/5 transition-all duration-300 cursor-pointer group select-none min-h-[220px]"
    >
      <div className="w-14 h-14 rounded-full bg-surface-container flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary/10 group-hover:text-primary text-on-surface-variant transition-all duration-300 shadow-inner">
        <Plus className="size-6 transition-transform duration-300" />
      </div>
      <h3 className="text-base md:text-lg font-bold text-on-surface mb-2">
        Create New Agent
      </h3>
      <p className="text-xs md:text-sm text-on-surface-variant/70 px-6 leading-relaxed">
        Define custom behaviors and connect private data sources.
      </p>
    </div>
  );
}
