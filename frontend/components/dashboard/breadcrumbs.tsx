"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const ROUTE_LABELS: Record<string, string> = {
  dashboard: "Workspace",
  chat: "Chat",
  documents: "Documents",
  agents: "Agents",
  workflows: "Workflows",
  marketplace: "Marketplace",
  analyzer: "Resume Analyzer",
  analytics: "Analytics",
  repository: "Repository Overview",
  admin: "Admin Panel",
  onboarding: "Onboarding",
  settings: "Settings",
  team: "Team Management",
  billing: "Billing & Subscription",
};

export default function DashboardBreadcrumbs() {
  const pathname = usePathname();

  // Split and filter empty segments
  const segments = pathname.split("/").filter(Boolean);

  // If we are at the root dashboard page (e.g. /dashboard) or home page, don't show breadcrumbs
  if (segments.length <= 1) {
    return null;
  }

  return (
    <nav className="flex items-center gap-1.5 text-[10px] md:text-xs text-on-surface-variant/80 select-none mb-6">
      {segments.map((segment, index) => {
        const isLast = index === segments.length - 1;
        const label = ROUTE_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
        
        // Construct absolute path for intermediate links
        const path = "/" + segments.slice(0, index + 1).join("/");

        if (isLast) {
          return (
            <span key={segment} className="text-primary font-bold">
              {label}
            </span>
          );
        }

        return (
          <div key={segment} className="flex items-center gap-1.5">
            <Link
              href={path}
              className="hover:text-on-surface transition-colors hover:no-underline"
            >
              {label}
            </Link>
            <ChevronRight className="size-3 shrink-0 text-on-surface-variant/40" />
          </div>
        );
      })}
    </nav>
  );
}
