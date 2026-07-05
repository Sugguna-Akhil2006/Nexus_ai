"use client";

import { Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DeveloperCTAProps {
  onSubmit: () => void;
}

export default function DeveloperCTA({ onSubmit }: DeveloperCTAProps) {
  return (
    <div className="bg-surface-container-lowest border border-dashed border-outline-variant rounded-xl p-6 flex flex-col items-center justify-center text-center hover:border-primary/50 hover:bg-primary/5 transition-all duration-300 group opacity-75 hover:opacity-100 select-none min-h-[240px] shadow-sm">
      
      {/* Icon */}
      <div className="w-12 h-12 rounded-full bg-surface-container border border-outline-variant flex items-center justify-center mb-4 group-hover:scale-105 group-hover:bg-primary/10 group-hover:text-primary transition-all duration-300 shadow-inner">
        <Rocket className="size-5 text-on-surface-variant transition-transform duration-300" />
      </div>

      {/* Info details */}
      <h5 className="text-base md:text-lg font-bold text-on-surface mb-2">
        Build Your Own
      </h5>
      <p className="text-xs md:text-sm text-on-surface-variant/85 px-6 leading-relaxed mb-6">
        Want to earn from your custom agent? Join the developer program.
      </p>

      {/* Submit button trigger */}
      <Button
        onClick={onSubmit}
        variant="outline"
        className="px-4 py-2 border border-outline-variant hover:border-primary hover:bg-primary hover:text-primary-foreground rounded-lg text-xs md:text-sm font-semibold transition-all duration-200 cursor-pointer shadow-sm"
      >
        Submit Agent
      </Button>
    </div>
  );
}
