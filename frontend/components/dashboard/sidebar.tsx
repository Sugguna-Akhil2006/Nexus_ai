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
  ShieldCheck,
  Workflow,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useNewProject } from "@/providers/new-project-provider";
import { useWorkspace } from "@/providers/workspace-provider";
import { useSidebar } from "@/providers/sidebar-provider";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";

function WorkspaceSwitcher({ isCollapsed }: { isCollapsed: boolean }) {
  const { workspaces, activeWorkspace, switchWorkspace } = useWorkspace();

  if (isCollapsed) {
    return (
      <div className="w-full mb-6 flex flex-col items-center">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="relative cursor-pointer group">
              <div className="w-10 h-10 rounded-lg bg-surface-container-lowest border border-outline-variant flex items-center justify-center text-xs font-bold text-primary group-hover:border-primary transition-all">
                {activeWorkspace?.name.substring(0, 2).toUpperCase() || "NX"}
              </div>
              <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-green-400 border border-surface" />
            </div>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-surface border border-outline-variant p-2 text-on-surface">
            <p className="font-semibold text-xs">{activeWorkspace?.name}</p>
            <p className="text-[10px] text-on-surface-variant">Active Workspace</p>
          </TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="w-full mb-6 relative">
      <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[9px] mb-1">
        Active Workspace
      </label>
      <div className="relative">
        <select
          value={activeWorkspace?.workspace_id || ""}
          onChange={(e) => switchWorkspace(e.target.value)}
          className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-2.5 pr-8 text-on-surface focus:outline-none focus:border-primary transition-all text-xs font-semibold appearance-none cursor-pointer"
        >
          {workspaces.map((ws) => (
            <option key={ws.workspace_id} value={ws.workspace_id}>
              {ws.name} {ws.is_favorite ? "⭐" : ""}
            </option>
          ))}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant/80 text-[10px]">
          ▼
        </div>
      </div>
    </div>
  );
}

// Custom Github SVG Icon to guarantee compatibility
const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

interface NavigationItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  badge?: string | number;
  badgeType?: "info" | "warning";
}

const NAV_ITEMS: NavigationItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, shortcut: "⌘1" },
  { label: "Chat", href: "/dashboard/chat", icon: MessageSquare, shortcut: "⌘2", badge: 2, badgeType: "info" },
  { label: "Documents", href: "/dashboard/documents", icon: FileText, shortcut: "⌘3" },
  { label: "Agents", href: "/dashboard/agents", icon: Bot, shortcut: "⌘4", badge: 1, badgeType: "warning" },
  { label: "Workflows", href: "/dashboard/workflows", icon: Workflow, shortcut: "⌘5" },
  { label: "Marketplace", href: "/dashboard/marketplace", icon: Store, shortcut: "⌘6" },
  { label: "Resume Analyzer", href: "/dashboard/analyzer", icon: FileSearch, shortcut: "⌘7" },
  { label: "GitHub Analyzer", href: "/dashboard/analytics/repository", icon: GithubIcon, shortcut: "⌘8" },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3, shortcut: "⌘9" },
  { label: "Admin", href: "/dashboard/admin", icon: ShieldCheck, shortcut: "⌘0" },
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
  const { isCollapsed, toggleCollapse } = useSidebar();

  const handleNewProject = () => {
    openNewProject();
    onItemClick?.();
  };

  const actualCollapsed = isMobile ? false : isCollapsed;

  const sidebarContent = (
    <>
      {/* Brand Logo */}
      <div className={cn("flex items-center gap-2 mb-8 px-2 justify-start", actualCollapsed && "justify-center px-0")}>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary shrink-0">
          <Boxes className="size-6" />
        </div>
        {!actualCollapsed && (
          <div className="animate-in fade-in duration-200">
            <h1 className="text-xl font-bold text-on-surface leading-none tracking-tight">Nexus AI</h1>
            <p className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-widest mt-1">
              Enterprise Workspace
            </p>
          </div>
        )}
      </div>

      {/* Workspace Switcher */}
      <WorkspaceSwitcher isCollapsed={actualCollapsed} />

      {/* Action Button */}
      {actualCollapsed ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="default"
              onClick={handleNewProject}
              className="w-10 h-10 shrink-0 p-0 justify-center bg-primary-container text-on-primary-container font-medium rounded-lg mb-8 hover:bg-primary-container/90 active:scale-[0.98] transition-all border-none cursor-pointer"
            >
              <Plus className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-surface border border-outline-variant p-2 text-on-surface text-xs font-semibold">
            New Project
          </TooltipContent>
        </Tooltip>
      ) : (
        <Button
          variant="default"
          onClick={handleNewProject}
          className="w-full justify-center gap-2 bg-primary-container text-on-primary-container font-medium py-5 rounded-lg mb-8 hover:bg-primary-container/90 active:scale-[0.98] transition-all border-none cursor-pointer animate-in fade-in duration-100"
        >
          <Plus className="size-4" />
          New Project
        </Button>
      )}

      {/* Main Navigation */}
      <nav className="flex-grow space-y-1 overflow-y-auto pr-1 custom-scrollbar">
        {NAV_ITEMS.map((item) => {
          const isActive = 
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === item.href || pathname.startsWith(item.href + "/");

          const navButton = (
            <Link
              href={item.href}
              onClick={onItemClick}
              className={cn(
                "flex items-center gap-4 py-3 rounded-md transition-all group duration-200 relative",
                isActive
                  ? "text-primary font-semibold border-r-2 border-primary bg-surface-container-high"
                  : "text-on-surface-variant font-medium hover:bg-surface-container-high/60 hover:text-on-surface",
                actualCollapsed ? "justify-center px-0 w-10 h-10 mx-auto" : "px-4"
              )}
            >
              <item.icon className={cn(
                "size-5 transition-transform group-hover:scale-105 shrink-0", 
                isActive ? "text-primary" : "text-on-surface-variant/70 group-hover:text-on-surface"
              )} />
              
              {!actualCollapsed && (
                <span className="text-sm truncate animate-in fade-in duration-100 flex-1">
                  {item.label}
                </span>
              )}

              {/* Badges */}
              {item.badge !== undefined && (
                actualCollapsed ? (
                  <span className={cn(
                    "absolute top-1 right-1 w-2.5 h-2.5 rounded-full shrink-0 border-2 border-surface",
                    item.badgeType === "warning" ? "bg-amber-500" : "bg-primary"
                  )} />
                ) : (
                  <span className={cn(
                    "text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0",
                    item.badgeType === "warning" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-primary/10 text-primary border border-primary/20"
                  )}>
                    {item.badge}
                  </span>
                )
              )}
            </Link>
          );

          if (actualCollapsed) {
            return (
              <Tooltip key={item.label}>
                <TooltipTrigger asChild>
                  {navButton}
                </TooltipTrigger>
                <TooltipContent side="right" className="bg-surface border border-outline-variant p-2 text-on-surface flex items-center justify-between gap-4">
                  <span className="text-xs font-semibold">{item.label}</span>
                  {item.shortcut && (
                    <kbd className="px-1 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold text-on-surface-variant">
                      {item.shortcut}
                    </kbd>
                  )}
                </TooltipContent>
              </Tooltip>
            );
          }

          return <div key={item.label}>{navButton}</div>;
        })}
      </nav>

      {/* Footer / Account */}
      <div className="pt-4 border-t border-outline-variant mt-auto space-y-1">
        {actualCollapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Link
                href="/dashboard/settings"
                onClick={onItemClick}
                className="flex items-center justify-center w-10 h-10 mx-auto text-on-surface-variant hover:text-on-surface font-medium rounded-md hover:bg-surface-container-high/60 transition-colors"
              >
                <User className="size-5 text-on-surface-variant/70" />
              </Link>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-surface border border-outline-variant p-2 text-on-surface text-xs font-semibold">
              Account Settings
            </TooltipContent>
          </Tooltip>
        ) : (
          <Link
            href="/dashboard/settings"
            onClick={onItemClick}
            className="flex items-center gap-4 px-4 py-3 text-on-surface-variant hover:text-on-surface font-medium rounded-md hover:bg-surface-container-high/60 transition-colors animate-in fade-in duration-100"
          >
            <User className="size-5 text-on-surface-variant/70" />
            <span className="text-sm">Account</span>
          </Link>
        )}

        {/* Collapsible toggle button on desktop */}
        {!isMobile && (
          <button
            onClick={toggleCollapse}
            className={cn(
              "hidden lg:flex w-full items-center justify-center p-2 rounded-md hover:bg-surface-container-high/60 text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer border-none",
              actualCollapsed ? "h-10 w-10 mx-auto" : "h-10 px-4 gap-4 justify-start"
            )}
          >
            {actualCollapsed ? (
              <ChevronRight className="size-5 shrink-0" />
            ) : (
              <>
                <ChevronLeft className="size-5 shrink-0" />
                <span className="text-xs font-medium truncate">Collapse Menu</span>
              </>
            )}
          </button>
        )}
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
      "hidden lg:flex fixed left-0 top-0 h-full bg-surface border-r border-outline-variant flex-col py-6 px-4 z-50 transition-all duration-300",
      actualCollapsed ? "w-20" : "w-64",
      className
    )}>
      {sidebarContent}
    </aside>
  );
}
