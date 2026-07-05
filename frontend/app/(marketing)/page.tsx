"use client";

import Hero from "@/components/landing/hero";
import DashboardPreview from "@/components/landing/dashboard-preview";
import FeatureGrid from "@/components/landing/feature-grid";
import StatsSection from "@/components/landing/stats-section";
import Footer from "@/components/landing/footer";

export default function MarketingPage() {
  return (
    <div className="flex flex-col w-full min-h-screen">
      {/* Hero Section */}
      <Hero />

      {/* Dashboard Preview Image Graphic */}
      <DashboardPreview />

      {/* Bento Grid Technical Features Section */}
      <FeatureGrid />

      {/* Operational Stats Section */}
      <StatsSection />

      {/* Page Footer */}
      <Footer />
    </div>
  );
}
