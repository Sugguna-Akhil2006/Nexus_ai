"use client";

import { useState } from "react";
import { User, X, Info, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export interface TeamMember {
  id: string;
  email: string;
  role: "Admin" | "Member";
}

interface StepTeamProps {
  initialMembers: TeamMember[];
  onBack: () => void;
  onActivate: (members: TeamMember[]) => void;
}

export default function StepTeam({
  initialMembers,
  onBack,
  onActivate,
}: StepTeamProps) {
  const [members, setMembers] = useState<TeamMember[]>(initialMembers);
  const [emailInput, setEmailInput] = useState("");

  const handleAddMember = () => {
    const trimmed = emailInput.trim();
    if (!trimmed) return;
    
    // Quick regex email check
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      toast.error("Please enter a valid email address.");
      return;
    }

    // Check duplication
    if (members.some((m) => m.email.toLowerCase() === trimmed.toLowerCase())) {
      toast.error("This email is already in the invitation list.");
      return;
    }

    const nextId = `mem-${Date.now()}`;
    const newMember: TeamMember = {
      id: nextId,
      email: trimmed,
      role: "Member", // default is member
    };

    setMembers((prev) => [...prev, newMember]);
    setEmailInput("");
  };

  const handleRemoveMember = (id: string) => {
    setMembers((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <section className="w-full max-w-[640px] animate-in fade-in slide-in-from-left-4 duration-300 select-none">
      <div className="glass-panel p-6 md:p-8 rounded-2xl space-y-6">
        
        {/* Step Headings */}
        <div className="space-y-1.5 select-text">
          <h2 className="text-lg md:text-xl font-bold tracking-tight text-on-surface">
            Invite your team
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium leading-relaxed">
            Nexus AI is more powerful when your experts collaborate.
          </p>
        </div>

        <div className="space-y-4">
          
          {/* Email input field */}
          <div className="flex items-center bg-surface-container-lowest border border-outline-variant rounded-lg p-1.5 pr-2 gap-2">
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddMember();
                }
              }}
              placeholder="colleague@company.com"
              className="flex-grow bg-transparent border-none focus:outline-none focus:ring-0 text-on-surface px-3 py-2 text-xs md:text-sm font-medium"
            />
            <Button
              onClick={handleAddMember}
              className="bg-secondary-container text-on-secondary-container hover:bg-outline-variant/50 transition-colors text-xs font-bold px-4 py-2.5 rounded-md h-auto cursor-pointer border-none shadow-sm shrink-0"
            >
              Add
            </Button>
          </div>

          {/* Members Invitation List */}
          <div className="space-y-2.5 max-h-44 overflow-y-auto pr-1.5 custom-scrollbar select-none">
            {members.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-3.5 bg-surface-container-low border border-outline-variant/35 rounded-xl transition-all"
              >
                <div className="flex items-center gap-3 min-w-0 select-text">
                  <div className="w-8 h-8 rounded-full bg-surface-container-highest border border-outline-variant/30 flex items-center justify-center shrink-0">
                    <User className="size-4 text-on-surface-variant" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs md:text-sm font-semibold text-on-surface truncate">
                      {member.email}
                    </p>
                    <p className="text-[9px] font-bold text-on-surface-variant uppercase tracking-wider mt-0.5 select-none leading-none">
                      {member.role}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleRemoveMember(member.id)}
                  className="text-on-surface-variant hover:text-error transition-colors cursor-pointer shrink-0"
                  title="Remove invitation"
                >
                  <X className="size-4 hover:scale-110 transition-transform" />
                </button>
              </div>
            ))}

            {members.length === 0 && (
              <div className="text-center py-6 text-xs text-on-surface-variant/40 italic select-none">
                No invitations added yet. Add teammate emails above.
              </div>
            )}
          </div>

          {/* Info note */}
          <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl flex items-start gap-3 select-text">
            <Info className="size-5 text-primary shrink-0 mt-0.5" />
            <p className="text-[11px] md:text-xs leading-relaxed text-on-surface-variant font-medium">
              Invitations will be sent immediately upon workspace activation. Admins can manage roles later in the dashboard.
            </p>
          </div>

        </div>

        {/* Action Buttons rows */}
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={onBack}
            className="flex-1 border border-outline-variant bg-transparent text-on-surface hover:bg-surface-container-high hover:border-outline text-xs md:text-sm font-bold py-5 rounded-lg cursor-pointer"
          >
            Back
          </Button>
          
          <Button
            onClick={() => onActivate(members)}
            className="flex-[2] bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold py-5 rounded-lg border-none flex items-center justify-center gap-1.5 cursor-pointer shadow-md shadow-primary/15"
          >
            <span>Activate Workspace</span>
            <Zap className="size-4 shrink-0 fill-current" />
          </Button>
        </div>

      </div>
    </section>
  );
}
