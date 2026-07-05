"use client";

import { cn } from "@/lib/utils";

interface ProgressStepperProps {
  currentStep: number; // 1, 2, or 3
}

export default function ProgressStepper({ currentStep }: ProgressStepperProps) {
  // Calculate progress percentage
  const getWidth = () => {
    switch (currentStep) {
      case 1:
        return "w-[33.33%]";
      case 2:
        return "w-[66.66%]";
      default:
        return "w-[100%]";
    }
  };

  const steps = [
    { number: 1, label: "Workspace" },
    { number: 2, label: "Team Access" },
    { number: 3, label: "Finalize" },
  ];

  return (
    <header className="mb-8 space-y-4 text-center select-none w-full max-w-[640px]">
      {/* Progress rail */}
      <div className="relative w-full h-1 bg-surface-container-highest rounded-full overflow-hidden select-none">
        <div 
          className={cn(
            "absolute top-0 left-0 h-full bg-primary transition-all duration-700 ease-in-out",
            getWidth()
          )} 
        />
      </div>

      {/* Progress labels */}
      <div className="flex justify-between px-1 select-none">
        {steps.map((st) => {
          const isActiveOrPassed = currentStep >= st.number;
          return (
            <span
              key={st.number}
              className={cn(
                "text-xs md:text-sm font-semibold tracking-wide transition-colors duration-300",
                isActiveOrPassed ? "text-primary font-bold" : "text-on-surface-variant/80"
              )}
            >
              {st.label}
            </span>
          );
        })}
      </div>
    </header>
  );
}
