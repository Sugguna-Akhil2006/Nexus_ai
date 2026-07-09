"use client";

import React from "react";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";

interface PageContainerProps {
  children: React.ReactNode;
  title: string;
  description: string;
  icon?: React.ReactNode;
  toolbar?: React.ReactNode;
}

export default function PageContainer({
  children,
  title,
  description,
  icon,
  toolbar,
}: PageContainerProps) {
  return (
    <div className="p-6 md:p-8 space-y-8 select-none overflow-y-auto h-[calc(100vh-64px)] custom-scrollbar flex flex-col justify-start">
      <DashboardBreadcrumbs />
      
      {/* Page Title Header */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-outline-variant/30 pb-6 shrink-0">
        <div>
          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-on-surface flex items-center gap-3">
            {icon}
            {title}
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-relaxed max-w-2xl">
            {description}
          </p>
        </div>

        {toolbar && (
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            {toolbar}
          </div>
        )}
      </section>

      {/* Main Content Area */}
      <div className="space-y-6 flex-grow">
        {children}
      </div>
    </div>
  );
}
