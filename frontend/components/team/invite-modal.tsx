"use client";

import { useState } from "react";
import { X, Mail, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface InviteModalProps {
  onClose: () => void;
  onInvite: (email: string, role: "Admin" | "Editor" | "Member") => void;
}

export default function InviteModal({ onClose, onInvite }: InviteModalProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"Admin" | "Editor" | "Member">("Member");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      toast.error("Please enter a valid email address.");
      return;
    }

    onInvite(trimmed, role);
    setEmail("");
    toast.success(`Invitation sent successfully to ${trimmed} as ${role}!`);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-[60] flex items-center justify-center p-4 select-none">
      <div className="bg-surface border border-outline-variant rounded-2xl p-6 md:p-8 max-w-md w-full shadow-2xl relative select-none animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header close trigger */}
        <div className="flex justify-between items-start mb-5">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary shadow-inner">
            <Mail className="size-5" />
          </div>
          <button
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface cursor-pointer rounded hover:bg-surface-container-high p-1"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Headings */}
        <h3 className="text-base md:text-lg font-bold text-on-surface mb-1">
          Invite Member
        </h3>
        <p className="text-xs md:text-sm text-on-surface-variant/90 font-medium mb-6 leading-relaxed select-text">
          Send a workspace invitation email. Collaborators will automatically join this organization upon validation.
        </p>

        {/* Inputs form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs md:text-sm">
          
          {/* Email input */}
          <div className="space-y-1.5">
            <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="collaborator@enterprise.ai"
              required
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-3 text-on-surface focus:outline-none focus:border-primary-container transition-all"
            />
          </div>

          {/* Role select */}
          <div className="space-y-1.5">
            <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Workspace Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as any)}
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg p-3 text-on-surface focus:outline-none focus:border-primary-container transition-all cursor-pointer"
            >
              <option value="Admin">Admin (Full permissions)</option>
              <option value="Editor">Editor (Can create &amp; publish)</option>
              <option value="Member">Member (Standard discovery)</option>
            </select>
          </div>

          {/* Action Row */}
          <div className="flex gap-4 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1 border border-outline-variant bg-transparent text-on-surface hover:bg-surface-container-high hover:border-outline text-xs md:text-sm font-bold py-5 rounded-lg cursor-pointer"
            >
              Cancel
            </Button>
            
            <Button
              type="submit"
              className="flex-1 bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold py-5 rounded-lg border-none cursor-pointer shadow-md shadow-primary/15"
            >
              Send Invitation
            </Button>
          </div>

        </form>

      </div>
    </div>
  );
}
