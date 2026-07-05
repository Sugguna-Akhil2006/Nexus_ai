"use client";

import { CheckCircle2 } from "lucide-react";

export interface PlanDetails {
  id: string;
  name: string;
  price: string;
  periodText: string;
  annualBillingText: string;
  features: string[];
}

interface CurrentPlanCardProps {
  plan: PlanDetails;
  nextBillingDate: string;
}

export default function CurrentPlanCard({
  plan,
  nextBillingDate,
}: CurrentPlanCardProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6 flex flex-col justify-between shadow-sm select-none h-full">
      
      {/* Plan Header */}
      <div>
        <div className="flex flex-wrap justify-between items-start gap-2 mb-6">
          <span className="bg-primary/10 text-primary text-[10px] md:text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">
            {plan.name} Plan
          </span>
          <span className="text-[10px] md:text-xs text-on-surface-variant font-semibold select-text">
            Next billing: {nextBillingDate}
          </span>
        </div>

        {/* Pricing tag */}
        <div className="mb-6">
          <div className="flex items-baseline gap-1 select-text">
            <span className="text-3xl md:text-4xl font-extrabold text-on-surface tracking-tight">
              {plan.price}
            </span>
            <span className="text-on-surface-variant font-semibold text-xs md:text-sm">
              {plan.periodText}
            </span>
          </div>
          <p className="text-[10px] md:text-xs text-on-surface-variant/90 font-medium mt-1 select-text">
            {plan.annualBillingText}
          </p>
        </div>
      </div>

      {/* Plan features checkmarks */}
      <div className="space-y-3 pt-4 border-t border-outline-variant/30 select-text">
        {plan.features.map((feature, idx) => (
          <div key={idx} className="flex items-start gap-2.5">
            <CheckCircle2 className="size-4.5 text-primary shrink-0 mt-0.5" />
            <span className="text-xs md:text-sm text-on-surface font-medium leading-tight">
              {feature}
            </span>
          </div>
        ))}
      </div>

    </div>
  );
}
