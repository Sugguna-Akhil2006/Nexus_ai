"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Search, 
  Bell, 
  HelpCircle, 
  Menu, 
  Sun, 
  Moon, 
  Laptop, 
  User, 
  Users, 
  CreditCard, 
  LogOut, 
  BookOpen, 
  Keyboard, 
  Activity, 
  LifeBuoy,
  Command
} from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { 
  DropdownMenu, 
  DropdownMenuTrigger, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator 
} from "@/components/ui/dropdown-menu";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription 
} from "@/components/ui/dialog";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import DashboardSidebar from "./sidebar";
import { useAuth } from "@/providers/auth-provider";
import { useSidebar } from "@/providers/sidebar-provider";


// Search Index Mock Data for command bar
const SEARCH_INDEX = [
  { category: "Pages", name: "Dashboard Overview", href: "/dashboard" },
  { category: "Pages", name: "Chat Interface", href: "/dashboard/chat" },
  { category: "Pages", name: "Documents Vault", href: "/dashboard/documents" },
  { category: "Pages", name: "Agent Clusters", href: "/dashboard/agents" },
  { category: "Pages", name: "Workflows Canvas", href: "/dashboard/workflows" },
  { category: "Pages", name: "Integrations Marketplace", href: "/dashboard/marketplace" },
  { category: "Pages", name: "Resume Analyzer", href: "/dashboard/analyzer" },
  { category: "Pages", name: "GitHub Analyzer", href: "/dashboard/analytics/repository" },
  { category: "Pages", name: "Advanced Analytics", href: "/dashboard/analytics" },
  { category: "Pages", name: "Admin Dashboard Panel", href: "/dashboard/admin" },
  { category: "Pages", name: "Workspace Settings", href: "/dashboard/settings" },
  { category: "Pages", name: "Team Management", href: "/dashboard/settings/team" },
  { category: "Pages", name: "Billing & Subscription", href: "/dashboard/settings/billing" },
  { category: "Projects", name: "Data Processing Pipeline", href: "/dashboard/workflows" },
  { category: "Projects", name: "Vanguard Guardrail (LLM Safety)", href: "#" },
  { category: "Projects", name: "Core-Sync 2.0 (Vector Pipeline)", href: "#" },
  { category: "Settings", name: "Profile Configuration", href: "/dashboard/settings" },
  { category: "Settings", name: "API Credentials Main Vault", href: "/dashboard/settings" },
];

export default function DashboardNavbar() {
  const router = useRouter();
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  
  // Theme logic
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { isCollapsed } = useSidebar();

  // Notifications State
  const [notifications, setNotifications] = useState([
    { id: 1, text: "Inference load spiked above 85% in nexus-v4-prod.", time: "2m ago", unread: true },
    { id: 2, text: "Data Processing Pipeline build completed successfully.", time: "15m ago", unread: true },
    { id: 3, text: "New agent 'Customer Support Bot' registered by Sarah Jenkins.", time: "1h ago", unread: false },
    { id: 4, text: "Billing quota exceeded 80% limit for active workspace.", time: "3h ago", unread: false },
    { id: 5, text: "Security anomaly: Unrecognized token access from IP 198.51.100.42.", time: "1d ago", unread: false },
  ]);

  // Keyboard Shortcuts listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
        setIsSearchFocused(true);
      }
      // Cmd/Ctrl + H to open shortcuts dialog
      if ((e.metaKey || e.ctrlKey) && e.key === "h") {
        e.preventDefault();
        setShowShortcuts(true);
      }
      // Escape to blur search
      if (e.key === "Escape") {
        searchInputRef.current?.blur();
        setIsSearchFocused(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Handler for navigation clicking
  const handleResultClick = (href: string) => {
    setIsSearchFocused(false);
    setSearchQuery("");
    if (href !== "#") {
      router.push(href);
    } else {
      toast.info("This is a mock project page link.");
    }
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, unread: false })));
    toast.success("All notifications marked as read.");
  };

  const clearNotifications = () => {
    setNotifications([]);
    toast.success("Notifications cleared.");
  };

  const handleSupportRequest = () => {
    toast.success("Support request registered! Our engineering team will contact you shortly.");
  };

  // Filter search results
  const filteredResults = searchQuery.trim() === ""
    ? SEARCH_INDEX.slice(0, 5) // Show popular/recent searches when input is empty
    : SEARCH_INDEX.filter(item => 
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        item.category.toLowerCase().includes(searchQuery.toLowerCase())
      );

  const profileImageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuAQPWQApcT52DE-3vQdZRRCoKniiP3TrN2d0bhsPn6NiQzY-0nrV_bNt2qYfeq6tPIplH4q5K6Vh7Ob-E1alQEMRiUUxEGlevIxrpeCDXGgph3_yqC1v63qVcTwDBblsZq1fG5xjsxnyxUjrYjvII392MblRFeyUknfePTonIS1DvB5kY1bmujaQ6ft5-lBHRpH3pfsRAff-FMnSoOF1RNZAkshyDM1yjk1ow5_RLXX6TziFiDQIglB78U4_DQSXiGHr3MoQI98gviJ";

  return (
    <>
      <header className={cn(
        "sticky top-0 z-40 w-full bg-surface/85 backdrop-blur-md border-b border-outline-variant flex justify-between items-center h-16 px-4 md:px-8 transition-all duration-300",
        isCollapsed ? "lg:pl-28" : "lg:pl-72"
      )}>
        {/* Search Bar / Menu button */}
        <div className="flex items-center gap-3 flex-1 max-w-xl relative">
          {/* Mobile menu trigger */}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden shrink-0 text-on-surface-variant hover:text-on-surface cursor-pointer"
              >
                <Menu className="size-5" />
                <span className="sr-only">Toggle navigation menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-64 border-r border-outline-variant bg-surface" showCloseButton={true}>
              <SheetTitle className="sr-only">Nexus AI Workspace Menu</SheetTitle>
              <SheetDescription className="sr-only">
                Navigation menu for project files, chat, documents, marketplace, analytics, and settings.
              </SheetDescription>
              <DashboardSidebar isMobile={true} onItemClick={() => setOpen(false)} />
            </SheetContent>
          </Sheet>

          {/* Interactive Command Search */}
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/70 size-4 pointer-events-none" />
            <input
              ref={searchInputRef}
              className="w-full bg-surface-container-low border-none rounded-lg pl-10 pr-12 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-on-surface-variant/40 text-on-surface transition-all"
              placeholder="Search (Press ⌘K)..."
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => {
                // Delay slightly to let clicks on dropdown register
                setTimeout(() => setIsSearchFocused(false), 200);
              }}
            />
            {/* Command shortcut badge */}
            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none hidden sm:flex items-center gap-0.5 text-[10px] font-mono font-bold text-on-surface-variant/40 bg-surface-container-high px-1.5 py-0.5 rounded border border-outline-variant">
              <span>⌘K</span>
            </div>

            {/* Dropdown panel for search results */}
            {isSearchFocused && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-surface/95 backdrop-blur-md border border-outline-variant rounded-xl shadow-2xl z-50 p-2 text-on-surface max-h-[380px] overflow-y-auto">
                <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant/50 px-3 py-1.5 flex items-center justify-between">
                  <span>{searchQuery ? "Search Results" : "Recent & Popular"}</span>
                  <span className="font-mono bg-surface-container-high px-1.5 py-0.5 rounded text-[8px]">ESC to close</span>
                </div>
                
                {filteredResults.length === 0 ? (
                  <div className="text-center py-8 text-xs text-on-surface-variant/60">
                    No results found for &ldquo;<span className="font-semibold">{searchQuery}</span>&rdquo;
                  </div>
                ) : (
                  <div className="space-y-1 mt-1">
                    {filteredResults.map((result, idx) => (
                      <div
                        key={idx}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          handleResultClick(result.href);
                        }}
                        className="flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer hover:bg-primary/10 hover:text-primary transition-all text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <Command className="size-3.5 opacity-60" />
                          <span>{result.name}</span>
                        </div>
                        <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-surface-container-highest text-on-surface-variant/80">
                          {result.category}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Nav links and actions */}
        <div className="flex items-center gap-6 ml-4">
          {/* Solutions, Framework, etc. (Desktop only) */}
          <nav className="hidden xl:flex items-center gap-6">
            <Link href="#" className="text-sm font-semibold text-primary transition-colors">
              Solutions
            </Link>
            <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
              Framework
            </Link>
            <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
              Resources
            </Link>
            <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
              Pricing
            </Link>
          </nav>

          {/* Right side icons */}
          <div className="flex items-center gap-4">
            
            {/* Theme Toggle Switcher */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="text-on-surface-variant hover:text-primary cursor-pointer size-9 rounded-full transition-colors">
                  {mounted && theme === "dark" && <Moon className="size-5" />}
                  {mounted && theme === "light" && <Sun className="size-5" />}
                  {mounted && theme === "system" && <Laptop className="size-5" />}
                  {!mounted && <Sun className="size-5" />}
                  <span className="sr-only">Toggle theme</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-36 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center" onClick={() => setTheme("light")}>
                  <Sun className="size-3.5 mr-2" />
                  <span>Light Mode</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center" onClick={() => setTheme("dark")}>
                  <Moon className="size-3.5 mr-2" />
                  <span>Dark Mode</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center" onClick={() => setTheme("system")}>
                  <Laptop className="size-3.5 mr-2" />
                  <span>System Default</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Notifications Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button aria-label="Notifications" className="relative cursor-pointer bg-transparent border-none p-1 text-on-surface-variant hover:text-primary transition-colors">
                  <Bell className="size-5" />
                  {notifications.some(n => n.unread) && (
                    <span className="absolute top-0 right-0 flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                    </span>
                  )}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80 bg-surface border border-outline-variant p-2 shadow-lg text-on-surface z-50">
                <div className="flex items-center justify-between px-2 py-1.5">
                  <span className="text-sm font-semibold">Notifications</span>
                  <div className="flex gap-2">
                    {notifications.some(n => n.unread) && (
                      <button 
                        onClick={markAllAsRead}
                        className="text-[10px] text-primary hover:underline bg-transparent border-none cursor-pointer font-medium"
                      >
                        Mark all read
                      </button>
                    )}
                    {notifications.length > 0 && (
                      <button 
                        onClick={clearNotifications}
                        className="text-[10px] text-on-surface-variant/60 hover:text-error hover:underline bg-transparent border-none cursor-pointer font-medium"
                      >
                        Clear all
                      </button>
                    )}
                  </div>
                </div>
                <DropdownMenuSeparator className="bg-outline-variant" />
                <div className="max-h-64 overflow-y-auto py-1 space-y-1">
                  {notifications.length === 0 ? (
                    <div className="text-center py-8 text-xs text-on-surface-variant/40">No alerts or notifications</div>
                  ) : (
                    notifications.map(n => (
                      <div 
                        key={n.id} 
                        onClick={() => {
                          setNotifications(notifications.map(notif => notif.id === n.id ? { ...notif, unread: false } : notif));
                        }}
                        className={cn(
                          "px-3 py-2 rounded-md text-xs cursor-pointer hover:bg-surface-container-high transition-colors text-left",
                          n.unread ? "bg-surface-container-low font-semibold text-on-surface border-l-2 border-primary" : "text-on-surface-variant"
                        )}
                      >
                        <p className="line-clamp-2 leading-relaxed">{n.text}</p>
                        <span className="text-[10px] text-on-surface-variant/40 mt-1 block">{n.time}</span>
                      </div>
                    ))
                  )}
                </div>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Help Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button aria-label="Help Options" className="relative cursor-pointer bg-transparent border-none p-1 text-on-surface-variant hover:text-primary transition-colors">
                  <HelpCircle className="size-5" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                <DropdownMenuLabel className="px-2 py-1.5 text-xs font-semibold text-on-surface-variant">Support & Help</DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-outline-variant" />
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center">
                  <BookOpen className="size-3.5 mr-2" />
                  <span>API & Documentation</span>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center justify-between" onClick={() => setShowShortcuts(true)}>
                  <div className="flex items-center">
                    <Keyboard className="size-3.5 mr-2" />
                    <span>Keyboard Shortcuts</span>
                  </div>
                  <kbd className="text-[9px] bg-muted px-1.5 py-0.5 rounded font-mono text-on-surface-variant/60 border border-outline-variant">⌘H</kbd>
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center">
                  <Activity className="size-3.5 mr-2" />
                  <span>System Status</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-outline-variant" />
                <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center" onClick={handleSupportRequest}>
                  <LifeBuoy className="size-3.5 mr-2" />
                  <span>Contact Support</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* User profile avatar with Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger className="focus:outline-none cursor-pointer group" asChild>
                <button
                  aria-label="User account menu"
                  className="relative flex items-center gap-2 rounded-full p-0.5 hover:ring-2 hover:ring-primary/25 transition-all focus:outline-none focus:ring-2 focus:ring-primary/25"
                >
                  <Avatar className="size-8 border border-outline-variant transition-all">
                    <AvatarImage src={profileImageUrl} alt="User Profile" />
                    <AvatarFallback className="bg-primary/10 text-primary font-bold text-xs">AS</AvatarFallback>
                  </Avatar>
                  {/* Online presence dot */}
                  <span className="absolute bottom-0.5 right-0.5 w-2 h-2 rounded-full bg-green-400 border-2 border-surface" />
                </button>
              </DropdownMenuTrigger>

              <DropdownMenuContent
                align="end"
                sideOffset={8}
                className="w-64 bg-surface border border-outline-variant shadow-xl shadow-black/20 text-on-surface z-50 p-0 rounded-xl overflow-hidden"
              >
                {/* ── Profile Card Header ─────────────────────────────── */}
                <div className="px-4 py-3.5 bg-surface-container-low border-b border-outline-variant/60">
                  <div className="flex items-center gap-3">
                    <div className="relative flex-shrink-0">
                      <Avatar className="size-10 border-2 border-outline-variant">
                        <AvatarImage src={profileImageUrl} alt="User Profile" />
                        <AvatarFallback className="bg-primary/10 text-primary font-bold">AS</AvatarFallback>
                      </Avatar>
                      <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-surface-container-low" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-on-surface truncate leading-tight">Alex Sterling</p>
                      <p className="text-[11px] text-on-surface-variant truncate">alex.s@enterprise.ai</p>
                      <span className="inline-flex items-center mt-1 px-1.5 py-0.5 rounded-sm text-[9px] font-bold uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
                        Admin
                      </span>
                    </div>
                  </div>
                </div>

                {/* ── Account Actions ──────────────────────────────────── */}
                <div className="p-1.5 space-y-0.5">
                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 text-on-surface hover:bg-surface-container-high focus:bg-surface-container-high transition-colors"
                    onClick={() => router.push("/dashboard/settings")}
                  >
                    <div className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center flex-shrink-0">
                      <User className="size-3.5 text-on-surface-variant" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-on-surface">Profile</p>
                      <p className="text-[10px] text-on-surface-variant/70 leading-tight">Manage your identity</p>
                    </div>
                  </DropdownMenuItem>

                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 text-on-surface hover:bg-surface-container-high focus:bg-surface-container-high transition-colors"
                    onClick={() => router.push("/dashboard/settings")}
                  >
                    <div className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center flex-shrink-0">
                      <svg className="size-3.5 text-on-surface-variant" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.07 4.93A10 10 0 0 0 5.07 19M4.93 19.07A10 10 0 0 0 19.07 5" />
                        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-on-surface">Settings</p>
                      <p className="text-[10px] text-on-surface-variant/70 leading-tight">Workspace preferences</p>
                    </div>
                  </DropdownMenuItem>

                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 text-on-surface hover:bg-surface-container-high focus:bg-surface-container-high transition-colors"
                    onClick={() => router.push("/dashboard/settings/billing")}
                  >
                    <div className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center flex-shrink-0">
                      <CreditCard className="size-3.5 text-on-surface-variant" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-on-surface">Billing</p>
                      <p className="text-[10px] text-on-surface-variant/70 leading-tight">Plans & subscription</p>
                    </div>
                  </DropdownMenuItem>

                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 text-on-surface hover:bg-surface-container-high focus:bg-surface-container-high transition-colors"
                    onClick={() => router.push("/dashboard/settings/team")}
                  >
                    <div className="w-6 h-6 rounded-md bg-surface-container flex items-center justify-center flex-shrink-0">
                      <Users className="size-3.5 text-on-surface-variant" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-on-surface">Team Management</p>
                      <p className="text-[10px] text-on-surface-variant/70 leading-tight">Members & permissions</p>
                    </div>
                  </DropdownMenuItem>
                </div>

                {/* ── Admin Section ─────────────────────────────────────── */}
                <div className="mx-1.5 border-t border-outline-variant/50" />
                <div className="p-1.5">
                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 text-on-surface hover:bg-secondary/10 focus:bg-secondary/10 transition-colors group/admin"
                    onClick={() => router.push("/dashboard/admin")}
                  >
                    <div className="w-6 h-6 rounded-md bg-secondary/10 border border-secondary/20 flex items-center justify-center flex-shrink-0 group-hover/admin:bg-secondary/20 transition-colors">
                      <svg className="size-3.5 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <p className="font-semibold text-on-surface">Admin Dashboard</p>
                        <span className="text-[8px] font-bold uppercase tracking-wider px-1 py-0.5 rounded bg-secondary/15 text-secondary border border-secondary/20">
                          Admin
                        </span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant/70 leading-tight">System & access controls</p>
                    </div>
                  </DropdownMenuItem>
                </div>

                {/* ── Logout ───────────────────────────────────────────── */}
                <div className="mx-1.5 border-t border-outline-variant/50" />
                <div className="p-1.5">
                  <DropdownMenuItem
                    className="cursor-pointer rounded-lg px-3 py-2 text-xs flex items-center gap-2.5 hover:bg-red-500/10 focus:bg-red-500/10 transition-colors group/logout"
                    onClick={() => {
                      logout();
                      toast.success("You've been signed out.", {
                        description: "See you next time, Alex.",
                        duration: 3000,
                      });
                      router.push("/login");
                    }}
                  >
                    <div className="w-6 h-6 rounded-md bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0 group-hover/logout:bg-red-500/20 transition-colors">
                      <LogOut className="size-3.5 text-red-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-red-400">Log out</p>
                      <p className="text-[10px] text-on-surface-variant/60 leading-tight">End current session</p>
                    </div>
                  </DropdownMenuItem>
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Keyboard Shortcuts Dialog Modal */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent className="max-w-sm bg-surface border border-outline-variant text-on-surface p-6 rounded-xl">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Keyboard className="size-5 text-primary" />
              Keyboard Shortcuts
            </DialogTitle>
            <DialogDescription className="text-xs text-on-surface-variant">
              Quickly trigger actions across the Nexus AI workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 my-4">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-on-surface-variant">Focus Search Input</span>
              <div className="flex gap-1 items-center">
                <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold">⌘</kbd>
                <span className="text-xs text-on-surface-variant/40">+</span>
                <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold">K</kbd>
              </div>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-on-surface-variant">Show Keyboard Shortcuts Dialog</span>
              <div className="flex gap-1 items-center">
                <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold">⌘</kbd>
                <span className="text-xs text-on-surface-variant/40">+</span>
                <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold">H</kbd>
              </div>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-on-surface-variant">Dismiss Search / Dropdowns / Modal</span>
              <kbd className="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant font-mono text-[9px] font-bold">ESC</kbd>
            </div>
          </div>
          <div className="flex justify-end pt-2">
            <Button 
              onClick={() => setShowShortcuts(false)}
              className="bg-primary text-primary-foreground font-semibold px-4 py-2 rounded-lg text-xs cursor-pointer border-none"
            >
              Got it
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
