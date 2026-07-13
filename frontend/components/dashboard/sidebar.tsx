"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Boxes, 
  Plus, 
  LayoutDashboard, 
  MessageSquare, 
  FileText, 
  Bot, 
  Store, 
  BarChart3, 
  Settings, 
  User,
  FileSearch,
  FileCode,
  ShieldCheck,
  Workflow
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useNewProject } from "@/providers/new-project-provider";
import { useWorkspace } from "@/providers/workspace-provider";
import { useAuth } from "@/providers/auth-provider";

function WorkspaceSwitcher() {
  const { workspaces, activeWorkspace, switchWorkspace } = useWorkspace();

  return (
    <div className="w-full mb-6 relative">
      <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[9px] mb-1">
        Workspace
      </label>
      <div className="relative">
        <select
          value={activeWorkspace?.workspace_id || ""}
          onChange={(e) => switchWorkspace(e.target.value)}
          className="w-full bg-surface-container border border-outline-variant rounded-lg px-3 py-2 text-xs md:text-sm font-semibold focus:outline-none focus:border-primary text-on-surface appearance-none cursor-pointer"
        >
          {workspaces.map((ws) => (
            <option key={ws.workspace_id} value={ws.workspace_id}>
              {ws.name}
            </option>
          ))}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant/60">
          ▼
        </div>
      </div>
    </div>
  );
}

interface NavigationItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavigationItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Chat", href: "/dashboard/chat", icon: MessageSquare },
  { label: "Documents", href: "/dashboard/documents", icon: FileText },
  { label: "Agents", href: "/dashboard/agents", icon: Bot },
  { label: "Workflows", href: "/dashboard/workflows", icon: Workflow },
  { label: "Marketplace", href: "/dashboard/marketplace", icon: Store },
  { label: "Resume Analyzer", href: "/dashboard/analyzer", icon: FileSearch },
  { label: "GitHub Analyzer", href: "/dashboard/github-analyzer", icon: FileCode },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
  { label: "Admin", href: "/dashboard/admin", icon: ShieldCheck, adminOnly: true },
  { label: "Settings", href: "/dashboard/settings", icon: Settings },
];

interface DashboardSidebarProps {
  className?: string;
  isMobile?: boolean;
  onItemClick?: () => void;
}

export default function DashboardSidebar({ className, isMobile = false, onItemClick }: DashboardSidebarProps) {
  const pathname = usePathname();
  const { openNewProject } = useNewProject();
  const { user } = useAuth();

  const handleNewProject = () => {
    openNewProject();
    onItemClick?.();
  };

  const sidebarContent = (
    <>
      {/* Brand Logo */}
      <div className="flex items-center gap-2 mb-8 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary">
          <Boxes className="size-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-on-surface leading-none tracking-tight">Nexus AI</h1>
          <p className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest mt-1">
            Enterprise Workspace
          </p>
        </div>
      </div>

      {/* Workspace Switcher */}
      <WorkspaceSwitcher />

      {/* Action Button */}
      <Button
        variant="default"
        onClick={handleNewProject}
        className="w-full justify-center gap-2 bg-primary-container text-on-primary-container font-medium py-5 rounded-lg mb-8 hover:bg-primary-container/90 active:scale-[0.98] transition-all border-none cursor-pointer"
      >
        <Plus className="size-4" />
        New Project
      </Button>

      {/* Main Navigation */}
      <nav className="flex-grow space-y-1 overflow-y-auto pr-1">
        {NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === "Admin").map((item) => {
          const isActive = 
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.label}
              href={item.href}
              onClick={onItemClick}
              className={cn(
                "flex items-center gap-4 px-4 py-3 rounded-md transition-all group duration-200",
                isActive
                  ? "text-primary font-semibold border-r-2 border-primary bg-surface-container-high"
                  : "text-on-surface-variant font-medium hover:bg-surface-container-high/60 hover:text-on-surface"
              )}
            >
              <item.icon className={cn(
                "size-5 transition-transform group-hover:scale-105", 
                isActive ? "text-primary" : "text-on-surface-variant/70 group-hover:text-on-surface"
              )} />
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer / Account */}
      <div className="pt-4 border-t border-outline-variant mt-auto">
        <Link
          href="/dashboard/settings"
          onClick={onItemClick}
          className="flex items-center gap-4 px-4 py-3 text-on-surface-variant hover:text-on-surface font-medium rounded-md hover:bg-surface-container-high/60 transition-colors"
        >
          <User className="size-5 text-on-surface-variant/70" />
          <span className="text-sm">Account</span>
        </Link>
      </div>
    </>
  );

  if (isMobile) {
    return (
      <div className={cn("flex flex-col h-full py-6 px-4 bg-surface text-on-background", className)}>
        {sidebarContent}
      </div>
    );
  }

  return (
    <aside className={cn(
      "hidden lg:flex fixed left-0 top-0 h-full w-64 bg-surface border-r border-outline-variant flex-col py-6 px-4 z-50",
      className
    )}>
      {sidebarContent}
    </aside>
  );
}
