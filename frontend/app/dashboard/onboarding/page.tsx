"use client";

import { useState } from "react";
import ProgressStepper from "@/components/onboarding/progress-stepper";
import StepWorkspace from "@/components/onboarding/step-workspace";
import StepTeam, { TeamMember } from "@/components/onboarding/step-team";
import StepFinalize from "@/components/onboarding/step-finalize";

// Initial mock teammates invite list
const INITIAL_INVITES: TeamMember[] = [
  { id: "mem-1", email: "sarah.j@enterprise.ai", role: "Admin" },
  { id: "mem-2", email: "mark.v@enterprise.ai", role: "Member" },
];

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [workspaceConfig, setWorkspaceConfig] = useState<{
    workspaceName: string;
    industry: string;
    deployment: "cloud" | "private";
  } | null>(null);
  const [invitedMembers, setInvitedMembers] = useState<TeamMember[]>(INITIAL_INVITES);

  const handleWorkspaceContinue = (data: { workspaceName: string; industry: string; deployment: "cloud" | "private" }) => {
    setWorkspaceConfig(data);
    setStep(2);
  };

  const handleTeamActivate = (members: TeamMember[]) => {
    setInvitedMembers(members);
    setStep(3);
  };

  const handleEnterDashboard = () => {
    // Future integration can hook up workspace creations API here
    console.log("Workspace Activated:", {
      config: workspaceConfig,
      invites: invitedMembers
    });
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center py-10 relative min-h-[calc(100vh-140px)] w-full">
      
      {/* Centered wizard container */}
      <div className="w-full max-w-[640px] z-10 flex flex-col items-center gap-6 px-4">
        
        {/* Progress Stepper lines */}
        <ProgressStepper currentStep={step} />

        {/* Dynamic step view */}
        {step === 1 && (
          <StepWorkspace onContinue={handleWorkspaceContinue} />
        )}

        {/* Step 2 invite list */}
        {step === 2 && (
          <StepTeam 
            initialMembers={invitedMembers}
            onBack={() => setStep(1)}
            onActivate={handleTeamActivate}
          />
        )}

        {/* Step 3 finalize loader */}
        {step === 3 && (
          <StepFinalize onEnterDashboard={handleEnterDashboard} />
        )}

      </div>

      {/* Visual Accents footer overlay (Stitch layout look) */}
      <footer className="absolute bottom-2 left-0 right-0 px-6 py-4 flex justify-between items-center opacity-30 pointer-events-none select-none text-[9px] md:text-[10px] font-mono tracking-widest uppercase">
        <div className="flex items-center gap-3">
          <div className="w-px h-6 bg-outline-variant/60" />
          <span>Encryption: AES-256</span>
        </div>
        <div className="text-right leading-relaxed">
          <span className="block">v2.4.0-Stable</span>
          <span className="block">Region: US-East-1</span>
        </div>
      </footer>

    </div>
  );
}
