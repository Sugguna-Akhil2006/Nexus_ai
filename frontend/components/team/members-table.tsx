"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { MoreVertical, Edit2, ShieldAlert, UserX, Search, ChevronDown, ListFilter, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

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

  // Context Menu state
  const [menuMemberId, setMenuMemberId] = useState<string | null>(null);
  const [menuPos, setMenuPos] = useState({ top: 0, left: 0 });
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Close context menu on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuMemberId(null);
      }
    };
    document.addEventListener("click", handleOutsideClick);
    return () => document.removeEventListener("click", handleOutsideClick);
  }, []);

  // Sync state modifications to parent coordinator
  const updateMembersList = (updated: Member[]) => {
    setMembers(updated);
    onMembersChange(updated);
  };

  const handleOpenMenu = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    
    // Position menu slightly below the trigger button
    setMenuPos({
      top: rect.bottom + window.scrollY + 6,
      left: rect.right + window.scrollX - 192,
    });
    setMenuMemberId((prev) => (prev === id ? null : id));
  };

  const handleRemoveMember = (id: string) => {
    const target = members.find((m) => m.id === id);
    if (!target) return;
    
    const confirmRemove = confirm(`Are you sure you want to remove "${target.name}" from this workspace?`);
    if (confirmRemove) {
      const updated = members.filter((m) => m.id !== id);
      updateMembersList(updated);
      setMenuMemberId(null);
    }
  };

  const handleChangeRole = (id: string) => {
    const target = members.find((m) => m.id === id);
    if (!target) return;

    const nextRole = prompt(`Change role for "${target.name}" to (Admin, Editor, Member):`, target.role);
    if (nextRole === null) return;
    
    const formatted = nextRole.trim();
    if (formatted === "Admin" || formatted === "Editor" || formatted === "Member") {
      const updated = members.map((m) =>
        m.id === id ? { ...m, role: formatted as Member["role"] } : m
      );
      updateMembersList(updated);
      setMenuMemberId(null);
      toast.success(`Role for "${target.name}" changed to ${formatted}.`);
    } else {
      toast.error("Invalid role. Please specify Admin, Editor, or Member.");
    }
  };

  const handleEditPermissions = (id: string) => {
    toast.info("Permissions modifications dashboard coming soon with backend policies synchronization.");
    setMenuMemberId(null);
  };

  const handleSort = (field: "name" | "role" | "lastActive") => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Filter members list based on query and selections
  const filteredMembers = members.filter((m) => {
    const matchesSearch = m.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          m.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === "All" || m.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  // Sort list
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

  // Paginate list
  const totalPages = Math.ceil(sortedMembers.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedMembers = sortedMembers.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden shadow-sm select-none">
      
      {/* Table Title and toolbar controls */}
      <div className="px-6 py-4 border-b border-outline-variant flex flex-col sm:flex-row gap-4 justify-between items-center bg-surface-container">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Active Members
        </h3>
        
        {/* Search & Filter tools */}
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          {/* Inner Search Box */}
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

          {/* Role Filters dropdown */}
          <div className="relative">
            <select
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value as any);
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
              
              {/* Sortable headers */}
              <th 
                onClick={() => handleSort("name")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none"
              >
                <div className="flex items-center gap-1.5">
                  Member
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>
              
              <th 
                onClick={() => handleSort("role")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none"
              >
                <div className="flex items-center gap-1.5">
                  Role
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>
              
              <th className="px-6 py-4 font-bold select-none">Status</th>
              
              <th 
                onClick={() => handleSort("lastActive")}
                className="px-6 py-4 font-bold cursor-pointer hover:text-on-surface transition-colors select-none"
              >
                <div className="flex items-center gap-1.5">
                  Last Active
                  <ArrowUpDown className="size-3 text-on-surface-variant" />
                </div>
              </th>

              <th className="px-6 py-4 font-bold text-right select-none">Actions</th>
            </tr>
          </thead>
          
          <tbody className="divide-y divide-outline-variant/30 select-text">
            {paginatedMembers.map((m) => (
              <tr key={m.id} className="hover:bg-surface-container/20 transition-colors group">
                {/* Member avatar, name */}
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

                {/* Role badge */}
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

                {/* Status dot */}
                <td className="px-6 py-4 select-none">
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "w-2 h-2 rounded-full shrink-0",
                      m.status === "Active" ? "bg-green-500" : "bg-outline"
                    )} />
                    <span className="text-on-surface font-medium">{m.status}</span>
                  </div>
                </td>

                {/* Last Active */}
                <td className="px-6 py-4 font-mono text-xs text-on-surface-variant select-none">
                  {m.lastActive}
                </td>

                {/* row menu actions */}
                <td className="px-6 py-4 text-right select-none">
                  <button
                    onClick={(e) => handleOpenMenu(e, m.id)}
                    className="p-2 hover:bg-surface-container-highest rounded-lg text-on-surface-variant hover:text-on-surface transition-all cursor-pointer inline-flex items-center justify-center"
                  >
                    <MoreVertical className="size-4 shrink-0" />
                  </button>
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

      {/* Absolute Context Menu portal overlay */}
      {menuMemberId && (
        <div
          ref={menuRef}
          style={{ top: menuPos.top, left: menuPos.left }}
          className="fixed z-[100] bg-surface-container-high border border-outline-variant rounded-xl shadow-2xl py-2 w-48 font-semibold animate-in fade-in zoom-in-95 duration-150 select-none"
        >
          <button
            onClick={() => handleEditPermissions(menuMemberId)}
            className="w-full text-left px-4 py-2 hover:bg-surface-container-highest flex items-center gap-2 text-xs md:text-sm text-on-surface transition-colors cursor-pointer"
          >
            <Edit2 className="size-3.5 text-on-surface-variant" />
            Edit Permissions
          </button>
          
          <button
            onClick={() => handleChangeRole(menuMemberId)}
            className="w-full text-left px-4 py-2 hover:bg-surface-container-highest flex items-center gap-2 text-xs md:text-sm text-on-surface transition-colors cursor-pointer"
          >
            <ShieldAlert className="size-3.5 text-on-surface-variant" />
            Change Role
          </button>
          
          <div className="h-[1px] bg-outline-variant/60 my-2 mx-4" />
          
          <button
            onClick={() => handleRemoveMember(menuMemberId)}
            className="w-full text-left px-4 py-2 text-error hover:bg-error-container/20 flex items-center gap-2 text-xs md:text-sm transition-colors cursor-pointer"
          >
            <UserX className="size-3.5 text-error" />
            Remove Member
          </button>
        </div>
      )}

    </div>
  );
}
