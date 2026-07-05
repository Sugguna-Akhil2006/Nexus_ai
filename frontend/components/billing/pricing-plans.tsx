"use client";

import { Check, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { PlanDetails } from "./current-plan-card";
import { toast } from "sonner";

interface PricingPlansProps {
  plans: PlanDetails[];
  selectedPlanId: string;
  onSelectPlan: (planId: string) => void;
}

export default function PricingPlans({
  plans,
  selectedPlanId,
  onSelectPlan,
}: PricingPlansProps) {
  return (
    <section className="space-y-8 select-none">
      
      {/* Header Info */}
      <div className="text-center">
        <h3 className="text-base md:text-lg font-bold text-on-surface uppercase tracking-wider">
          Choose the right path for your scale
        </h3>
        <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-none">
          Flexible options designed for startups to global infrastructure.
        </p>
      </div>

      {/* Plans columns mapping */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {plans.map((p) => {
          const isSelected = p.id === selectedPlanId;
          const isEnterprise = p.id === "pro-enterprise"; // Enterprise plan is highlighted
          
          return (
            <div
              key={p.id}
              className={cn(
                "bg-surface-container-low border rounded-xl p-6 flex flex-col justify-between transition-all duration-300 relative",
                isEnterprise
                  ? "border-primary shadow-xl bg-surface-container shadow-primary/5"
                  : "border-outline-variant hover:border-outline shadow-sm",
                isSelected && !isEnterprise && "border-primary/50"
              )}
            >
              {/* Popular badge for enterprise */}
              {isEnterprise && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[8px] md:text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-widest leading-none select-none">
                  Most Popular
                </div>
              )}

              {/* Title & info */}
              <div>
                <h4 className="text-base md:text-lg font-bold text-on-surface leading-tight">
                  {p.name}
                </h4>
                <p className="text-xs text-on-surface-variant/80 font-medium mt-1.5 leading-normal mb-5 select-text">
                  {p.id === "pro-developer"
                    ? "For individuals and small experiments."
                    : p.id === "pro-enterprise"
                    ? "Advanced capabilities for scaling teams."
                    : "Custom hardware and isolation for high security."}
                </p>

                {/* Price */}
                <div className="mb-6 select-text">
                  <span className="text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">
                    {p.price}
                  </span>
                  {p.periodText && (
                    <span className="text-on-surface-variant font-semibold text-xs md:text-sm pl-0.5">
                      {p.periodText}
                    </span>
                  )}
                </div>

                {/* Features list */}
                <ul className="space-y-3 mb-8 select-text">
                  {p.features.map((feature, fIdx) => (
                    <li key={fIdx} className="flex gap-2 text-xs md:text-sm font-medium leading-tight">
                      <Check className={cn(
                        "size-4 shrink-0 mt-0.5",
                        isEnterprise ? "text-primary" : "text-on-surface-variant/80"
                      )} />
                      <span className={cn(
                        isEnterprise ? "text-on-surface" : "text-on-surface-variant"
                      )}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Plan selector Button */}
              <div>
                {p.id === "pro-infra" ? (
                  <button
                    onClick={() => toast.info("Connecting you to infrastructure sales support...")}
                    className="w-full py-2.5 bg-surface-container-highest hover:bg-surface-variant border border-outline-variant text-on-surface text-xs font-bold rounded-lg cursor-pointer transition-colors"
                  >
                    Contact Sales
                  </button>
                ) : (
                  <button
                    onClick={() => onSelectPlan(p.id)}
                    className={cn(
                      "w-full py-2.5 text-xs font-bold rounded-lg cursor-pointer transition-all border-none",
                      isSelected
                        ? "bg-primary text-primary-foreground cursor-default"
                        : "bg-surface-container-highest hover:bg-surface-variant border border-outline-variant text-on-surface"
                    )}
                  >
                    {isSelected ? "Selected" : "Select Plan"}
                  </button>
                )}
              </div>

            </div>
          );
        })}
      </div>

    </section>
  );
}
