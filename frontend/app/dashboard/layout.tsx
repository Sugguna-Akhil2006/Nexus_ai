"use client";

import DashboardSidebar from "@/components/dashboard/sidebar";
import DashboardNavbar from "@/components/dashboard/navbar";
import { NewProjectProvider } from "@/providers/new-project-provider";
import NewProjectModal from "@/components/dashboard/new-project-modal";
import AuthGuard from "@/components/auth/auth-guard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <NewProjectProvider>
        <div className="relative min-h-screen bg-background text-on-background">
          {/* Sidebar - Visible on Desktop, Hidden on Mobile */}
          <DashboardSidebar />

          {/* Main Container */}
          <div className="flex flex-col min-h-screen">
            {/* Sticky Header Navbar */}
            <DashboardNavbar />

            {/* Content Viewport Offset by Sidebar on large screens */}
            <main className="flex-1 min-h-[calc(100vh-64px)] lg:pl-64 transition-all relative">
              {children}
            </main>
          </div>

          {/* Global New Project Modal (rendered once, controlled via context) */}
          <NewProjectModal />
        </div>
      </NewProjectProvider>
    </AuthGuard>
  );
}

