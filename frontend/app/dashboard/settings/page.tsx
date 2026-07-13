"use client";

import { useState, useEffect } from "react";
import { Bell, Shield, Users, CreditCard, Key, Settings, AlertTriangle, ShieldCheck, Mail, MessageSquare } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import ProfileSettings from "@/components/settings/profile-settings";
import PreferenceSwitch from "@/components/settings/preference-switch";
import WorkspaceSettingsPanel from "@/components/settings/workspace-settings";
import ApiKeysManager, { ApiKeyItem } from "@/components/settings/api-keys-manager";
import ConfirmationDialog from "@/components/common/confirmation-dialog";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import PageContainer from "@/components/common/page-container";
import { useAuth } from "@/providers/auth-provider";

type SettingsTab = "general" | "workspace" | "security" | "notifications";

const INITIAL_KEYS: ApiKeyItem[] = [
  { id: "key-1", name: "Production Gateway Token", keyMasked: "nx_live_••••••••••••••••3a8c", lastUsed: "Just now", status: "Active" },
  { id: "key-2", name: "Staging CLI Auth Key", keyMasked: "nx_test_••••••••••••••••f982", lastUsed: "3 days ago", status: "Active" },
];

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>(INITIAL_KEYS);
  
  // Granular preference states
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [securityPush, setSecurityPush] = useState(true);
  const [slackLogs, setSlackLogs] = useState(false);
  const [billingNotif, setBillingNotif] = useState(true);
  
  // Security states
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);
  const [showDeleteWorkspaceDialog, setShowDeleteWorkspaceDialog] = useState(false);

  // Derived profile from useAuth
  const profile = {
    name: user?.name || "Admin",
    email: user?.email || "admin@nexus-ai.corp",
    bio: `Workspace administrator with role: ${user?.role || "Admin"}.`,
    avatarUrl: user?.avatarUrl || "https://lh3.googleusercontent.com/aida-public/AB6AXuBlhpoMt3jR2GI5_4dbQUe-h906NficthzrZBzLzhPP_Sk26XRjIeKEhdDe3XayRBKrDioV6YTYlejHmxj14-m4M7BI7BDR_1Z_zTUElpmcNFmlBOHXsLki-E6g2N2lZqzUO4JLJTvRLeKOsGA2mmU9VZ3MSoBuoRJiMRlQ1sg-DIfvbLOQ0Ychl0ZSeCXEtttsdSOl-Ubb3FPseUKTheJ7ZiTtUgq0lCTh001e-G5XTZ7xYxwGEye2lK7lN-f7yZuY8gkwNuTyXBQI",
  };

  const handleSaveProfile = (updated: typeof profile) => {
    if (updateUser) {
      updateUser({
        name: updated.name,
        email: updated.email,
        avatarUrl: updated.avatarUrl,
      });
    }
    toast.success("Profile updates saved successfully.");
  };

  const handleKeysChange = (updated: ApiKeyItem[]) => {
    setApiKeys(updated);
  };

  const handleTriggerPasswordReset = () => {
    toast.success("MFA Reset token dispatched successfully. Please check your inbox at: " + profile.email);
  };

  const handlePurgeWorkspace = async () => {
    toast.error("Executing secure workspace wipe sequence...", {
      description: "Database indexes purged. Disassociating DNS zones.",
    });
    setShowDeleteWorkspaceDialog(false);
  };

  const toolbarActions = (
    <>
      <Link href="/dashboard/settings/team" passHref>
        <Button className="bg-transparent border border-outline hover:bg-surface-container hover:border-primary text-on-surface text-xs font-bold px-4 py-2.5 rounded-lg cursor-pointer flex items-center gap-1.5 shadow-sm">
          <Users className="size-3.5" />
          <span>Manage Team Permissions</span>
        </Button>
      </Link>

      <Link href="/dashboard/settings/billing" passHref>
        <Button className="bg-transparent border border-outline hover:bg-surface-container hover:border-primary text-on-surface text-xs font-bold px-4 py-2.5 rounded-lg cursor-pointer flex items-center gap-1.5 shadow-sm">
          <CreditCard className="size-3.5" />
          <span>Billing &amp; Subscription</span>
        </Button>
      </Link>
    </>
  );

  return (
    <PageContainer
      title="Workspace Settings"
      description="Configure your enterprise workspace environment, team preferences, and developer credentials."
      icon={<Settings className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
      {/* Structured Tab Switcher Navigation */}
      <div className="flex gap-1.5 border-b border-outline-variant/35 pb-px select-none overflow-x-auto scrollbar-none">
        {(["general", "workspace", "security", "notifications"] as SettingsTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-5 py-3 text-xs md:text-sm font-semibold capitalize border-b-2 transition-all cursor-pointer bg-transparent outline-none",
              activeTab === tab
                ? "border-primary text-primary font-bold"
                : "border-transparent text-on-surface-variant/75 hover:text-on-surface"
            )}
          >
            {tab === "security" ? "Security & API Keys" : tab}
          </button>
        ))}
      </div>

      {/* Grid Layout settings blocks based on active tab state */}
      <div className="grid grid-cols-1 gap-8">
        
        {/* Tab 1: General & Profile */}
        {activeTab === "general" && (
          <ProfileSettings 
            initialProfile={profile} 
            onSave={handleSaveProfile} 
          />
        )}

        {/* Tab 2: Workspace Config */}
        {activeTab === "workspace" && (
          <WorkspaceSettingsPanel />
        )}

        {/* Tab 3: Security & Credentials */}
        {activeTab === "security" && (
          <>
            <ApiKeysManager 
              initialKeys={apiKeys} 
              onKeysChange={handleKeysChange} 
            />

            {/* Password and 2FA card */}
            <div className="bg-surface-container border border-outline-variant rounded-xl p-6 space-y-6 shadow-sm select-none">
              <div>
                <h3 className="text-lg font-bold text-on-surface tracking-tight mb-1">
                  Credential Security &amp; Access Logs
                </h3>
                <p className="text-xs text-on-surface-variant">
                  Update passwords, configure Multi-factor logins, and review active developer terminal logs.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                {/* Reset Form */}
                <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 space-y-4">
                  <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider block">Password Updates</span>
                  <p className="text-xs text-on-surface-variant/90 leading-relaxed">
                    To reset your account password, we require authentication checks via email. Click the button to trigger a secure reset payload.
                  </p>
                  <Button
                    onClick={handleTriggerPasswordReset}
                    className="bg-primary text-primary-foreground font-semibold px-4 py-2.5 rounded-lg text-xs cursor-pointer border-none"
                  >
                    Send Reset Email
                  </Button>
                </div>

                {/* 2FA preference */}
                <PreferenceSwitch
                  title="Two-Factor Auth (2FA)"
                  description="Force authentication validation challenge using TOTP algorithms on mobile apps."
                  icon={ShieldCheck}
                  enabled={twoFactorAuth}
                  onChange={setTwoFactorAuth}
                />
              </div>

              {/* Active Sessions Logs list */}
              <div className="border-t border-outline-variant/60 pt-5 space-y-4">
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider block">Active Workspace Sessions</span>
                <div className="space-y-3 font-mono text-[10px] md:text-xs">
                  <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      <div>
                        <span className="font-semibold text-on-surface">Chrome on Windows (Current)</span>
                        <p className="text-[9px] text-on-surface-variant/50 mt-1">IP: 198.51.100.42 · Location: Dublin, IE</p>
                      </div>
                    </div>
                    <span className="text-on-surface-variant/60 font-semibold">Active</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-on-surface-variant/30" />
                      <div>
                        <span className="font-semibold text-on-surface">VS Code Antigravity Extension</span>
                        <p className="text-[9px] text-on-surface-variant/50 mt-1">IP: 203.0.113.11 · Location: New York, US</p>
                      </div>
                    </div>
                    <button
                      onClick={() => toast.success("VS Code extension token revoked successfully.")}
                      className="text-[10px] text-error hover:underline cursor-pointer bg-transparent border-none font-semibold"
                    >
                      Revoke Session
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Danger Zone Purge */}
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6 space-y-4 shadow-sm select-none">
              <div>
                <h3 className="text-lg font-bold text-red-400 tracking-tight flex items-center gap-2">
                  <AlertTriangle className="size-5 shrink-0" />
                  Danger Zone
                </h3>
                <p className="text-xs text-on-surface-variant">
                  Irreversible actions that completely purge this workspace, deleting all models, tokens configurations, and analytics logs.
                </p>
              </div>
              <div className="border-t border-red-500/15 pt-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <span className="text-xs font-bold text-on-surface block">Delete Workspace container</span>
                  <p className="text-[11px] text-on-surface-variant leading-relaxed mt-0.5 max-w-xl">
                    Once clicked, all database indexes matching this workspace ID will be permanently destroyed. External API routes will break immediately.
                  </p>
                </div>
                <Button
                  onClick={() => setShowDeleteWorkspaceDialog(true)}
                  className="bg-red-500 hover:bg-red-600 text-white font-bold px-4 py-2.5 rounded-lg text-xs cursor-pointer border-none shrink-0"
                >
                  Delete Workspace
                </Button>
              </div>
            </div>

            {/* Delete Workspace Dialog */}
            <ConfirmationDialog
              open={showDeleteWorkspaceDialog}
              onOpenChange={setShowDeleteWorkspaceDialog}
              title="Irreversibly Delete Workspace?"
              description="This action is permanent and cannot be undone. All models, workflows history, files logs, and team permissions records under this workspace container will be wiped forever from the cluster databases."
              confirmLabel="Purge Workspace"
              variant="destructive"
              onConfirm={handlePurgeWorkspace}
            />
          </>
        )}

        {/* Tab 4: Notifications settings switches */}
        {activeTab === "notifications" && (
          <div className="bg-surface-container border border-outline-variant rounded-xl p-6 space-y-6 shadow-sm select-none">
            <div>
              <h3 className="text-lg font-bold text-on-surface tracking-tight mb-1">
                Notification Preferences
              </h3>
              <p className="text-xs text-on-surface-variant">
                Configure your inbound channels for developer actions, cost thresholds warnings, and deployment alerts.
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <PreferenceSwitch
                title="Email Weekly Summaries"
                description="Receive weekly roundups of API tokens usage stats, and model billing metrics reports."
                icon={Mail}
                enabled={emailAlerts}
                onChange={setEmailAlerts}
              />
              <PreferenceSwitch
                title="Security Push Alerts"
                description="Receive instant alerts for key creation, policy modifications, and foreign IP logins."
                icon={Shield}
                enabled={securityPush}
                onChange={setSecurityPush}
              />
              <PreferenceSwitch
                title="Slack Log Hook Stream"
                description="Post live workspace execution events, compile successes, and runtime failures direct to Slack channels."
                icon={MessageSquare}
                enabled={slackLogs}
                onChange={setSlackLogs}
              />
              <PreferenceSwitch
                title="Billing Threshold Alerts"
                description="Receive priority alerts when billing limits hit 80% or 100% of defined quotas."
                icon={CreditCard}
                enabled={billingNotif}
                onChange={setBillingNotif}
              />
            </div>
          </div>
        )}

      </div>
    </PageContainer>
  );
}
