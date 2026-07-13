"use client";

import { useState } from "react";
import Image from "next/image";
import { MoreVertical, Edit2, ShieldAlert, UserX, Search, ChevronDown, ArrowUpDown } from "lucide-react";
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
import ConfirmationDialog from "@/components/common/confirmation-dialog";

export interface Member {
  id: string;
  name: string;
  email: string;
  avatarUrl: string;
  role: "Admin" | "Editor" | "Member";
  status: "Active" | "Inactive";
  lastActive: string;
}

interface MembersTableProps {
  initialMembers: Member[];
  onMembersChange: (members: Member[]) => void;
}

export default function MembersTable({
  initialMembers,
  onMembersChange,
}: MembersTableProps) {
  const [members, setMembers] = useState<Member[]>(initialMembers);
  
  // Search, filter, and sort states
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<"All" | "Admin" | "Editor" | "Member">("All");
  const [sortField, setSortField] = useState<"name" | "role" | "lastActive">("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 4;

  // Deletion Target
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  // Sync state modifications to parent coordinator
  const updateMembersList = (updated: Member[]) => {
    setMembers(updated);
    onMembersChange(updated);
  };

  const handleRemoveMemberConfirm = async () => {
    if (!deleteTarget) return;
    const target = members.find((m) => m.id === deleteTarget);
    if (!target) return;

    const updated = members.filter((m) => m.id !== deleteTarget);
    updateMembersList(updated);
    setDeleteTarget(null);
    toast.success(`Removed "${target.name}" from this workspace.`);
  };

  const handleChangeRole = (id: string, newRole: Member["role"]) => {
    const target = members.find((m) => m.id === id);
    if (!target) return;

    const updated = members.map((m) =>
      m.id === id ? { ...m, role: newRole } : m
    );
    updateMembersList(updated);
    toast.success(`Role for "${target.name}" changed to ${newRole}.`);
  };

  const handleSort = (field: "name" | "role" | "lastActive") => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const filteredMembers = members.filter((m) => {
    const matchesSearch = m.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          m.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "All" || m.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const sortedMembers = [...filteredMembers].sort((a, b) => {
    let comparison = 0;
    if (sortField === "name") {
      comparison = a.name.localeCompare(b.name);
    } else if (sortField === "role") {
      comparison = a.role.localeCompare(b.role);
    } else {
      comparison = a.lastActive.localeCompare(b.lastActive);
    }
    return sortDirection === "asc" ? comparison : -comparison;
  });

  const totalPages = Math.ceil(sortedMembers.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedMembers = sortedMembers.slice(startIndex, startIndex + itemsPerPage);

  const activeDeleteTargetName = deleteTarget ? members.find((m) => m.id === deleteTarget)?.name : "";

  return (
    <>
      <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden shadow-sm select-none">
        
        {/* Table Title and toolbar controls */}
        <div className="px-6 py-4 border-b border-outline-variant flex flex-col sm:flex-row gap-4 justify-between items-center bg-surface-container">
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Active Members
          </h3>
          
          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-grow sm:flex-grow-0">
              <Search className="size-4 absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
              <input
                type="text"
                placeholder="Search members..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-surface-container-low border border-outline-variant rounded-lg pl-9 pr-4 py-1.5 text-xs md:text-sm text-on-surface focus:outline-none focus:border-primary transition-all w-full sm:w-48"
              />
            </div>

            <div className="relative">
              <select
                value={roleFilter}
                onChange={(e) => {
                  setRoleFilter(e.target.value as typeof roleFilter);
                  setCurrentPage(1);
                }}
                className="bg-surface-container-low border border-outline-variant rounded-lg px-3 py-1.5 text-xs font-semibold text-on-surface-variant hover:text-on-surface focus:outline-none cursor-pointer appearance-none pr-8"
              >
                <option value="All">All Roles</option>
                <option value="Admin">Admin</option>
                <option value="Editor">Editor</option>
                <option value="Member">Member</option>
              </select>
              <ChevronDown className="size-3.5 absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Responsive Table Layout */}
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs md:text-sm border-collapse">
            <thead>
              <tr className="text-on-surface-variant/90 border-b border-outline-variant/60 uppercase text-[10px] md:text-[11px] tracking-wider font-bold bg-surface-container-lowest select-none">
                <th 
                  onClick={() => handleSort("name")}
                  className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none font-sans"
                >
                  <div className="flex items-center gap-1.5">
                    Member
                    <ArrowUpDown className="size-3 text-on-surface-variant" />
                  </div>
                </th>
                
                <th 
                  onClick={() => handleSort("role")}
                  className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none font-sans"
                >
                  <div className="flex items-center gap-1.5">
                    Role
                    <ArrowUpDown className="size-3 text-on-surface-variant" />
                  </div>
                </th>
                
                <th className="px-6 py-4 font-bold select-none font-sans">Status</th>
                
                <th 
                  onClick={() => handleSort("lastActive")}
                  className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none font-sans"
                >
                  <div className="flex items-center gap-1.5">
                    Last Active
                    <ArrowUpDown className="size-3 text-on-surface-variant" />
                  </div>
                </th>

                <th className="px-6 py-4 font-bold text-right select-none font-sans">Actions</th>
              </tr>
            </thead>
            
            <tbody className="divide-y divide-outline-variant/30 select-text">
              {paginatedMembers.map((m) => (
                <tr key={m.id} className="hover:bg-surface-container/20 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg overflow-hidden border border-outline-variant shrink-0 relative select-none">
                        <Image
                          alt={m.name}
                          src={m.avatarUrl}
                          fill
                          sizes="40px"
                          className="object-cover"
                        />
                      </div>
                      <div className="min-w-0">
                        <div className="font-bold text-on-surface truncate">{m.name}</div>
                        <div className="text-[10px] md:text-xs text-on-surface-variant/80 truncate">
                          {m.email}
                        </div>
                      </div>
                    </div>
                  </td>

                  <td className="px-6 py-4">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border leading-none",
                      m.role === "Admin"
                        ? "bg-primary-container/20 text-primary border-primary/20"
                        : m.role === "Editor"
                        ? "bg-surface-container-highest text-on-surface-variant border-outline-variant/35"
                        : "bg-surface-container text-on-surface-variant/80 border-outline-variant/20"
                    )}>
                      {m.role}
                    </span>
                  </td>

                  <td className="px-6 py-4 select-none">
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "w-2 h-2 rounded-full shrink-0",
                        m.status === "Active" ? "bg-green-500" : "bg-outline"
                      )} />
                      <span className="text-on-surface font-medium">{m.status}</span>
                    </div>
                  </td>

                  <td className="px-6 py-4 font-mono text-xs text-on-surface-variant select-none">
                    {m.lastActive}
                  </td>

                  <td className="px-6 py-4 text-right select-none">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="p-2 hover:bg-surface-container-highest rounded-lg text-on-surface-variant hover:text-on-surface transition-all cursor-pointer inline-flex items-center justify-center bg-transparent border-none">
                          <MoreVertical className="size-4 shrink-0" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-48 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                        <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.info("Permissions panel trigger")}>
                          <Edit2 className="size-3.5" />
                          Edit Permissions
                        </DropdownMenuItem>
                        
                        {/* Submenu for role changing */}
                        <DropdownMenuSub>
                          <DropdownMenuSubTrigger className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2">
                            <ShieldAlert className="size-3.5" />
                            Change Role
                          </DropdownMenuSubTrigger>
                          <DropdownMenuSubContent className="bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                            {["Admin", "Editor", "Member"].map((r) => (
                              <DropdownMenuItem
                                key={r}
                                className={cn(
                                  "cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded",
                                  m.role === r && "text-primary font-bold bg-primary/5"
                                )}
                                onClick={() => handleChangeRole(m.id, r as Member["role"])}
                              >
                                {r}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuSubContent>
                        </DropdownMenuSub>

                        <DropdownMenuSeparator className="bg-outline-variant" />
                        
                        <DropdownMenuItem
                          className="cursor-pointer hover:bg-red-500/10 text-red-400 px-2 py-1.5 text-xs rounded flex items-center gap-2"
                          onClick={() => setDeleteTarget(m.id)}
                        >
                          <UserX className="size-3.5 text-red-400" />
                          Remove Member
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))}

              {paginatedMembers.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-xs text-on-surface-variant/40 italic select-none">
                    No workspace members found matching filter requirements.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-6 py-4 border-t border-outline-variant/50 flex flex-col sm:flex-row gap-4 items-center justify-between text-on-surface-variant font-medium text-xs md:text-sm bg-surface-container-low select-none">
          <span>
            Showing {paginatedMembers.length} of {filteredMembers.length} members
          </span>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-outline-variant rounded hover:bg-surface-container-highest transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer font-semibold text-xs"
            >
              Previous
            </button>
            
            <div className="flex gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pNum) => (
                <button
                  key={pNum}
                  onClick={() => setCurrentPage(pNum)}
                  className={cn(
                    "w-8 h-8 flex items-center justify-center rounded font-bold transition-all cursor-pointer text-xs",
                    currentPage === pNum
                      ? "bg-primary text-primary-foreground font-black shadow-sm"
                      : "hover:bg-surface-container-highest text-on-surface-variant"
                  )}
                >
                  {pNum}
                </button>
              ))}
            </div>
            
            <button
              onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-outline-variant rounded hover:bg-surface-container-highest transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer font-semibold text-xs"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Remove Member Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Remove Member from Workspace?"
        description={`This will permanently remove ${activeDeleteTargetName} and revoke all credentials, workspace configurations, and logs access from this account. Click Confirm to remove.`}
        confirmLabel="Remove Member"
        variant="destructive"
        onConfirm={handleRemoveMemberConfirm}
      />
    </>
  );
}
