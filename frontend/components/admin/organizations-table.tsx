"use client";

import { useState } from "react";
import { Search, ChevronDown, ListFilter, ArrowUpDown, MoreVertical, ShieldAlert, Ban, RefreshCw, Key } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from "@/components/ui/dropdown-menu";

export interface OrganizationItem {
  id: string;
  name: string;
  planType: string;
  status: "Active" | "Suspended";
  lastActivity: string;
  colorClass: string;
  letter: string;
}

interface OrganizationsTableProps {
  initialOrgs: OrganizationItem[];
  onViewAllClick: () => void;
}

export default function OrganizationsTable({
  initialOrgs,
  onViewAllClick,
}: OrganizationsTableProps) {
  const [orgs, setOrgs] = useState<OrganizationItem[]>(initialOrgs);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<"name" | "planType" | "status">("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const handleSort = (field: "name" | "planType" | "status") => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleToggleStatus = (id: string) => {
    setOrgs((prev) =>
      prev.map((o) => {
        if (o.id === id) {
          const nextStatus = o.status === "Active" ? "Suspended" : "Active";
          toast.info(`Status for organization "${o.name}" updated to ${nextStatus}.`);
          return { ...o, status: nextStatus };
        }
        return o;
      })
    );
  };

  const handleChangePlan = (id: string, newPlan: string) => {
    setOrgs((prev) =>
      prev.map((o) => {
        if (o.id === id) {
          toast.success(`Plan for "${o.name}" changed to ${newPlan}.`);
          return { ...o, planType: newPlan };
        }
        return o;
      })
    );
  };

  // Filter orgs
  const filteredOrgs = orgs.filter((o) =>
    o.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    o.planType.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Sort orgs
  const sortedOrgs = [...filteredOrgs].sort((a, b) => {
    let comparison = 0;
    if (sortField === "name") {
      comparison = a.name.localeCompare(b.name);
    } else if (sortField === "planType") {
      comparison = a.planType.localeCompare(b.planType);
    } else {
      comparison = a.status.localeCompare(b.status);
    }
    return sortDirection === "asc" ? comparison : -comparison;
  });

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden shadow-sm select-none">
      
      {/* Table Header toolbar */}
      <div className="p-5 border-b border-outline-variant/30 flex flex-col sm:flex-row gap-4 justify-between items-center bg-surface-container/50">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Recent Organizations
        </h3>
        
        {/* Search tool */}
        <div className="relative w-full sm:w-48">
          <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
          <input
            type="text"
            placeholder="Search orgs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-1.5 text-xs md:text-sm text-on-surface focus:outline-none focus:border-primary transition-all w-full"
          />
        </div>
      </div>

      {/* Table Layout */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs md:text-sm border-collapse">
          <thead>
            <tr className="bg-surface-container/30 text-on-surface-variant/90 border-b border-outline-variant/30 uppercase text-[10px] md:text-[11px] tracking-wider font-bold select-none">
              
              <th
                onClick={() => handleSort("name")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors font-sans"
              >
                <div className="flex items-center gap-1.5 font-sans">
                  Org Name
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>
              
              <th
                onClick={() => handleSort("planType")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors font-sans"
              >
                <div className="flex items-center gap-1.5 font-sans">
                  Plan Type
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>

              <th
                onClick={() => handleSort("status")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors font-sans"
              >
                <div className="flex items-center gap-1.5 font-sans">
                  Status
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>

              <th className="px-6 py-4 font-bold font-sans">Last Activity</th>
              <th className="px-6 py-4 font-bold text-right font-sans">Actions</th>
            </tr>
          </thead>
          
          <tbody className="divide-y divide-outline-variant/10 select-text font-medium">
            {sortedOrgs.map((org) => (
              <tr key={org.id} className="hover:bg-surface-container-high/35 transition-colors group">
                
                {/* Org Avatar Letter & Name */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 select-none shadow-sm",
                      org.colorClass
                    )}>
                      {org.letter}
                    </div>
                    <span className="font-bold text-on-surface">{org.name}</span>
                  </div>
                </td>

                {/* Plan Type */}
                <td className="px-6 py-4 select-none">
                  <span className="px-2 py-0.5 rounded-full bg-zinc-800/80 text-on-surface-variant text-[10px] md:text-xs border border-outline-variant/60 font-semibold uppercase tracking-wider">
                    {org.planType}
                  </span>
                </td>

                {/* Status Dot */}
                <td className="px-6 py-4 select-none">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "w-1.5 h-1.5 rounded-full shrink-0",
                      org.status === "Active" ? "bg-emerald-400" : "bg-outline-variant"
                    )} />
                    <span className={cn(
                      org.status === "Active" ? "text-emerald-400 font-bold" : "text-on-surface-variant"
                    )}>
                      {org.status}
                    </span>
                  </div>
                </td>

                {/* Last Active */}
                <td className="px-6 py-4 font-mono text-[10px] md:text-xs text-on-surface-variant select-none">
                  {org.lastActivity}
                </td>

                {/* Actions Dropdown */}
                <td className="px-6 py-4 text-right select-none">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className="p-1.5 rounded hover:bg-surface-container-highest text-on-surface-variant/60 hover:text-on-surface transition-all cursor-pointer bg-transparent border-none">
                        <MoreVertical className="size-4 shrink-0" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                      <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => handleToggleStatus(org.id)}>
                        <Ban className="size-3.5" />
                        {org.status === "Active" ? "Suspend Org" : "Activate Org"}
                      </DropdownMenuItem>

                      {/* Sub-menu to switch plans */}
                      <DropdownMenuSub>
                        <DropdownMenuSubTrigger className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2">
                          <RefreshCw className="size-3.5" />
                          Change Plan
                        </DropdownMenuSubTrigger>
                        <DropdownMenuSubContent className="bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                          {["Enterprise", "Scale", "Developer"].map((p) => (
                            <DropdownMenuItem
                              key={p}
                              className={cn(
                                "cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded",
                                org.planType === p && "text-primary font-bold bg-primary/5"
                              )}
                              onClick={() => handleChangePlan(org.id, p)}
                            >
                              {p}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuSubContent>
                      </DropdownMenuSub>

                      <DropdownMenuSeparator className="bg-outline-variant" />
                      <DropdownMenuItem
                        className="cursor-pointer hover:bg-red-500/10 text-red-400 px-2 py-1.5 text-xs rounded flex items-center gap-2"
                        onClick={() => {
                          setOrgs((prev) => prev.filter((o) => o.id !== org.id));
                          toast.success(`Organization "${org.name}" deleted.`);
                        }}
                      >
                        Delete Org
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}

            {sortedOrgs.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center py-6 text-xs text-on-surface-variant/40 italic select-none">
                  No organizations found matching queries.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer view all link */}
      <div className="p-4 border-t border-outline-variant/30 flex justify-center bg-surface-container-low/20">
        <button
          onClick={onViewAllClick}
          className="text-on-surface-variant hover:text-primary transition-colors font-bold text-xs md:text-sm cursor-pointer bg-transparent border-none"
        >
          View all 482 organizations
        </button>
      </div>

    </div>
  );
}
