"use client";

import MarketingNavbar from "@/components/layout/marketing-navbar";

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen bg-background text-on-background">
      {/* Main Content Layout Wrapper */}
      <div className="flex flex-col min-h-screen">
        {/* Sticky Header Navbar */}
        <MarketingNavbar />

        {/* Main Content Area - Full Width */}
        <main className="flex-1 min-h-[calc(100vh-64px)] transition-all relative">
          {children}
        </main>
      </div>
    </div>
  );
}
