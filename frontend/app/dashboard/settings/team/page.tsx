"use client";

import { useState } from "react";
import Link from "next/link";
import { Download, UserPlus, ShieldAlert, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import TeamStats from "@/components/team/team-stats";
import MembersTable, { Member } from "@/components/team/members-table";
import InviteModal from "@/components/team/invite-modal";
import InviteLinks from "@/components/team/invite-links";
import { cn } from "@/lib/utils";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";

// Mock Team Members Database
const INITIAL_MEMBERS: Member[] = [
  {
    id: "mem-1",
    name: "Alex Rivera",
    email: "alex.rivera@nexus-ai.io",
    avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCH8hs7VjzQp-v6XU8c99znid5XEHV4JB_-WEPJ49g6YQjyesZN0LwaaVHriJAWBmo-_9YJHekWtFSBSgBEaF85zp0swkRN1cx89tOPtzjKsrePMiWB1TSURPMNrxzYHgC5ZHzdmjkpJLteBt5dUqYSrFx0BSl-9rD66uDU2096SehL_rAjcu4sUCvD4uk7CRnwfVzE-nndk_pN3WwSnXC7kUtOIcRiNoHzdrx5WFDDlYpVE_dB8QeMlkCd_rOpi1i5laBB5HkrDtwC",
    role: "Admin",
    status: "Active",
    lastActive: "2 mins ago",
  },
  {
    id: "mem-2",
    name: "Jordan Smith",
    email: "j.smith@nexus-ai.io",
    avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCCOi1jGQaPkQLqV4ZhsQb7DInTmE1U9dJA5QocSEs35Dq340lq31HdjyZ9ZFYo7x71o41gR3A0Cs0F4XypUgIhbyLniuEHUQlnprscIT-Nt58CZO-yxecM1I8o1PAlngGCtG1WYEgI40zHc0RzoKelNzNdW0Dlc2UZ20nNOtDfPTx-3goVvZ9KDBM-BxOpwn4G03Zy6zfSF_34K_2_mjaOK37LaqH7q9RcQScdCtIwJW4S2l5FkjsJYgI-FSxPkMefOEzgK4NuywG3",
    role: "Editor",
    status: "Active",
    lastActive: "4h ago",
  },
  {
    id: "mem-3",
    name: "Sarah Jenkins",
    email: "sarah.j@nexus-ai.io",
    avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh",
    role: "Member",
    status: "Active",
    lastActive: "1d ago",
  },
  {
    id: "mem-4",
    name: "Alex Chen",
    email: "alex.chen@nexus-ai.io",
    avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X",
    role: "Member",
    status: "Inactive",
    lastActive: "3 days ago",
  },
];

export default function TeamManagementPage() {
  const [members, setMembers] = useState<Member[]>(INITIAL_MEMBERS);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [isEmpty, setIsEmpty] = useState(false);

  // Global Permissions States
  const [allowInvitations, setAllowInvitations] = useState(false);
  const [publicDiscovery, setPublicDiscovery] = useState(true);

  const handleInviteSubmit = (email: string, role: "Admin" | "Editor" | "Member") => {
    // Generate a secure mock name from email prefix
    const prefix = email.split("@")[0];
    const name = prefix
      .split(".")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");

    const nextId = `mem-${Date.now()}`;
    const newMember: Member = {
      id: nextId,
      name,
      email,
      avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCH8hs7VjzQp-v6XU8c99znid5XEHV4JB_-WEPJ49g6YQjyesZN0LwaaVHriJAWBmo-_9YJHekWtFSBSgBEaF85zp0swkRN1cx89tOPtzjKsrePMiWB1TSURPMNrxzYHgC5ZHzdmjkpJLteBt5dUqYSrFx0BSl-9rD66uDU2096SehL_rAjcu4sUCvD4uk7CRnwfVzE-nndk_pN3WwSnXC7kUtOIcRiNoHzdrx5WFDDlYpVE_dB8QeMlkCd_rOpi1i5laBB5HkrDtwC",
      role,
      status: "Active",
      lastActive: "Just now",
    };

    setMembers((prev) => [newMember, ...prev]);
  };

  const handleExportList = () => {
    toast.success("Exporting workspace team members list in CSV format. Your download will start shortly.");
  };

  return (
    <div className="space-y-8 select-none">
      
      <DashboardBreadcrumbs />

      {/* Page Header Actions */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/30 pb-6 shrink-0 select-none">
        <div>
          <div className="flex items-center gap-4">
            <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
              Team Management
            </h2>
            <Button 
              variant="ghost" 
              size="xs" 
              onClick={() => setIsEmpty(!isEmpty)} 
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
            >
              {isEmpty ? "● Show Team Members" : "○ Simulate Empty State"}
            </Button>
          </div>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium mt-1 leading-relaxed max-w-2xl">
            Manage workspace permissions, invite collaborators, and define member roles.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            disabled={isEmpty}
            onClick={handleExportList}
            className="bg-surface-container-low border border-outline-variant hover:bg-surface-container hover:border-primary px-4 py-2.5 rounded-lg text-xs font-bold text-on-surface flex items-center gap-1.5 cursor-pointer shadow-sm disabled:opacity-50"
          >
            <Download className="size-3.5 shrink-0" />
            Export List
          </Button>
          
          <Button
            onClick={() => setShowInviteModal(true)}
            className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
          >
            <UserPlus className="size-3.5 shrink-0" />
            Invite Member
          </Button>
        </div>
      </section>

      {isEmpty ? (
        <div className="py-12">
          <EmptyState
            icon={Users}
            title="No Collaborators Added"
            description="Invite developers, system managers, and prompt engineers to collaborate on resources, build workflow pipelines, and manage API keys."
            actionLabel="Invite Team Member"
            onAction={() => setShowInviteModal(true)}
            accentColor="secondary"
          />
        </div>
      ) : (
        <>
          {/* Stats Summary overview widget */}
          <TeamStats 
            totalMembers={members.length} 
            pendingInvites={7} 
            apiConsumption={82} 
          />

          {/* Members Directory Grid */}
          <div className="grid grid-cols-1 gap-8">
            
            {/* Members Table */}
            <MembersTable 
              initialMembers={members} 
              onMembersChange={setMembers} 
            />

        {/* Global Permissions & Invite links */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 shrink-0">
          
          {/* Permissions switches column */}
          <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider border-b border-outline-variant/40 pb-2.5 select-none">
              Global Permissions
            </h3>

            <div className="space-y-4">
              
              {/* Toggle 1 */}
              <div className="flex items-start justify-between gap-4 p-2 hover:bg-surface-container/20 rounded-xl transition-all">
                <div className="max-w-[78%] text-xs md:text-sm select-text">
                  <div className="font-bold text-on-surface leading-tight">
                    Allow Member Invitations
                  </div>
                  <p className="text-[10px] md:text-xs text-on-surface-variant/80 font-medium leading-relaxed mt-1.5">
                    Non-admin members can invite new users to the workspace.
                  </p>
                </div>
                
                {/* Switch slider */}
                <div
                  onClick={() => setAllowInvitations(!allowInvitations)}
                  className={cn(
                    "w-10 h-5 rounded-full relative cursor-pointer flex items-center px-1 transition-all duration-200 select-none border border-outline-variant/30 shrink-0 mt-1",
                    allowInvitations ? "bg-primary" : "bg-surface-container-highest"
                  )}
                >
                  <div className={cn(
                    "w-3.5 h-3.5 rounded-full shadow-sm transition-all duration-200",
                    allowInvitations ? "bg-white ml-auto" : "bg-outline mr-auto"
                  )} />
                </div>
              </div>

              {/* Toggle 2 */}
              <div className="flex items-start justify-between gap-4 p-2 hover:bg-surface-container/20 rounded-xl transition-all">
                <div className="max-w-[78%] text-xs md:text-sm select-text">
                  <div className="font-bold text-on-surface leading-tight">
                    Public Project Discovery
                  </div>
                  <p className="text-[10px] md:text-xs text-on-surface-variant/80 font-medium leading-relaxed mt-1.5">
                    Enable team members to browse and join open projects.
                  </p>
                </div>
                
                {/* Switch slider */}
                <div
                  onClick={() => setPublicDiscovery(!publicDiscovery)}
                  className={cn(
                    "w-10 h-5 rounded-full relative cursor-pointer flex items-center px-1 transition-all duration-200 select-none border border-outline-variant/30 shrink-0 mt-1",
                    publicDiscovery ? "bg-primary" : "bg-surface-container-highest"
                  )}
                >
                  <div className={cn(
                    "w-3.5 h-3.5 rounded-full shadow-sm transition-all duration-200",
                    publicDiscovery ? "bg-white ml-auto" : "bg-outline mr-auto"
                  )} />
                </div>
              </div>

            </div>
          </div>

          {/* Invitation links card */}
          <InviteLinks />

        </div>

      </div>
        </>
      )}

      {/* Invite Member modal popups */}
      {showInviteModal && (
        <InviteModal 
          onClose={() => setShowInviteModal(false)} 
          onInvite={handleInviteSubmit} 
        />
      )}

    </div>
  );
}
