"use client";

import { useState } from "react";
import { Bell, Shield, Users, CreditCard } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import ProfileSettings from "@/components/settings/profile-settings";

import PreferenceSwitch from "@/components/settings/preference-switch";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import WorkspaceSettingsPanel from "@/components/settings/workspace-settings";

import { useAuth } from "@/providers/auth-provider";



export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  
  const profile = {
    name: user?.name || "Admin",
    email: user?.email || "admin@nexus-ai.corp",
    bio: `Workspace administrator with role: ${user?.role || "Admin"}.`,
    avatarUrl: user?.avatarUrl || "https://lh3.googleusercontent.com/aida-public/AB6AXuBlhpoMt3jR2GI5_4dbQUe-h906NficthzrZBzLzhPP_Sk26XRjIeKEhdDe3XayRBKrDioV6YTYlejHmxj14-m4M7BI7BDR_1Z_zTUElpmcNFmlBOHXsLki-E6g2N2lZqzUO4JLJTvRLeKOsGA2mmU9VZ3MSoBuoRJiMRlQ1sg-DIfvbLOQ0Ychl0ZSeCXEtttsdSOl-Ubb3FPseUKTheJ7ZiTtUgq0lCTh001e-G5XTZ7xYxwGEye2lK7lN-f7yZuY8gkwNuTyXBQI",
  };

  // Preference states
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);

  const handleSaveProfile = (updatedProfile: any) => {
    updateUser({
      name: updatedProfile.name,
      email: updatedProfile.email,
      avatarUrl: updatedProfile.avatarUrl,
    });
  };

  return (
    <div className="space-y-8 md:space-y-12 select-none">
      <DashboardBreadcrumbs />
      
      {/* Header Info */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/30 pb-6 shrink-0 select-none">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
            Workspace Settings
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium max-w-2xl mt-1 leading-relaxed">
            Configure your enterprise workspace environment, team preferences, and developer credentials.
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3 select-none">
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
        </div>
      </section>

      {/* Grid Layout settings blocks */}
      <div className="grid grid-cols-1 gap-8">
        
        {/* Profile Configuration Card */}
        <ProfileSettings 
          initialProfile={profile} 
          onSave={handleSaveProfile} 
        />

        <WorkspaceSettingsPanel />



        {/* System Preferences toggles */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6 select-none shrink-0">
          {/* Email preferences */}
          <PreferenceSwitch
            title="Email Notifications"
            description="Receive weekly activity summaries and security alerts via your registered work email."
            icon={Bell}
            enabled={emailNotifications}
            onChange={setEmailNotifications}
          />

          {/* 2FA preferences */}
          <PreferenceSwitch
            title="Two-Factor Auth"
            description="Add an extra layer of security to your account by requiring more than just a password."
            icon={Shield}
            enabled={twoFactorAuth}
            onChange={setTwoFactorAuth}
          />
        </section>

      </div>
    </div>
  );
}
