"use client";

import { useState } from "react";
import Link from "next/link";
import { CreditCard, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import CurrentPlanCard, { PlanDetails } from "@/components/billing/current-plan-card";
import UsageMetrics from "@/components/billing/usage-metrics";
import PricingPlans from "@/components/billing/pricing-plans";
import PaymentHistoryTable, { InvoiceItem } from "@/components/billing/payment-history-table";
import PaymentMethods, { CardDetails } from "@/components/billing/payment-methods";
import BillingAddress, { AddressDetails } from "@/components/billing/billing-address";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import PageContainer from "@/components/common/page-container";

// Complete pricing plans definitions database
const MOCK_PLANS: PlanDetails[] = [
  {
    id: "pro-developer",
    name: "Developer",
    price: "$29",
    periodText: "/mo",
    annualBillingText: "Billed annually ($348/yr)",
    features: [
      "100k Monthly Tokens",
      "Community Support",
      "5 Custom Agents",
    ],
  },
  {
    id: "pro-enterprise",
    name: "Enterprise",
    price: "$499",
    periodText: "/mo",
    annualBillingText: "Billed annually ($5,988/yr)",
    features: [
      "5M Monthly Tokens",
      "24/7 Dedicated Support",
      "Unlimited Agents",
      "SSO & Custom Auth",
    ],
  },
  {
    id: "pro-infra",
    name: "Infrastructure",
    price: "Custom",
    periodText: "",
    annualBillingText: "Billed annually (Custom contract)",
    features: [
      "Unlimited Tokens",
      "Air-gapped Deployment",
      "Custom Model Training",
    ],
  },
];

const INITIAL_INVOICES: InvoiceItem[] = [
  {
    id: "inv-1",
    invoiceCode: "#INV-88219-Nexus",
    date: "Oct 24, 2023",
    amount: "$499.00",
    status: "Paid",
  },
  {
    id: "inv-2",
    invoiceCode: "#INV-87402-Nexus",
    date: "Sep 24, 2023",
    amount: "$499.00",
    status: "Paid",
  },
];

const INITIAL_CARDS: CardDetails[] = [
  {
    id: "card-1",
    numberMasked: "•••• •••• •••• 4242",
    expiry: "12/25",
    isDefault: true,
  },
];

const INITIAL_ADDRESS: AddressDetails = {
  company: "Nexus Paradigm Labs Inc.",
  street: "888 Quantum Way, Suite 400",
  cityStateZip: "Palo Alto, CA 94301",
  country: "United States",
};

export default function BillingSettingsPage() {
  const [selectedPlanId, setSelectedPlanId] = useState("pro-enterprise");
  const [isEmpty, setIsEmpty] = useState(false);
  
  // Find current plan details from state
  const currentPlan = MOCK_PLANS.find((p) => p.id === selectedPlanId) || MOCK_PLANS[1];

  const handleUpgradeHeader = () => {
    toast.success("Connecting to Stripe billing portal... Redirecting you shortly.");
  };

  const handleManagePayment = () => {
    toast.info("Opening secure payment methods portal. Loading default credentials.");
  };

  const toolbarActions = (
    <>
      <Button 
        variant="ghost" 
        size="xs" 
        onClick={() => setIsEmpty(!isEmpty)} 
        className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors bg-transparent border-none mr-2"
      >
        {isEmpty ? "● Show Billing Profile" : "○ Simulate Empty State"}
      </Button>
      <Button
        variant="outline"
        disabled={isEmpty}
        onClick={handleManagePayment}
        className="bg-surface-container-low border border-outline-variant hover:bg-surface-container hover:border-primary px-4 py-2.5 rounded-lg text-xs font-bold text-on-surface cursor-pointer shadow-sm disabled:opacity-50"
      >
        Manage Payment Method
      </Button>
      
      <Button
        onClick={handleUpgradeHeader}
        className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
      >
        <Sparkles className="size-3.5 shrink-0" />
        Upgrade Plan
      </Button>
    </>
  );

  return (
    <PageContainer
      title="Billing & Subscription"
      description="Manage your organizational plan, track real-time usage across API nodes, and review historical invoices."
      icon={<CreditCard className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={CreditCard}
            title="No Billing Plan Configured"
            description="Configure your billing profile and select a developer or enterprise subscription tier to allocate GPU compute hours and deploy custom models."
            actionLabel="Configure Billing Profile"
            onAction={handleUpgradeHeader}
            accentColor="warning"
          />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Bento grid layout for Current Plan and metrics */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
            
            {/* Current Plan Summary Card */}
            <div className="md:col-span-4">
              <CurrentPlanCard 
                plan={currentPlan} 
                nextBillingDate="Oct 24, 2026" 
              />
            </div>

            {/* Quotas utilization details */}
            <div className="md:col-span-8">
              <UsageMetrics 
                tokensUsed={1.2} 
                tokensLimit={selectedPlanId === "pro-developer" ? 0.1 : 5.0} 
                storageUsed={412} 
                storageLimit={1000} 
                gpuEfficiency={82} 
              />
            </div>

          </div>

          {/* Plans selector comparative matrix */}
          <PricingPlans 
            plans={MOCK_PLANS} 
            selectedPlanId={selectedPlanId} 
            onSelectPlan={setSelectedPlanId} 
          />

          {/* Receipts list table */}
          <PaymentHistoryTable 
            initialInvoices={INITIAL_INVOICES} 
          />

          {/* Methods & Addresses Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 shrink-0">
            
            {/* Cards tracker */}
            <PaymentMethods 
              initialCards={INITIAL_CARDS} 
            />

            {/* Corporate Address */}
            <BillingAddress 
              initialAddress={INITIAL_ADDRESS} 
            />

          </div>
        </div>
      )}
    </PageContainer>
  );
}
