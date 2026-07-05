"use client";

import { useState } from "react";
import { Bell, Shield, Users, CreditCard } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import ProfileSettings from "@/components/settings/profile-settings";
import ApiKeysManager, { ApiKeyItem } from "@/components/settings/api-keys-manager";
import PreferenceSwitch from "@/components/settings/preference-switch";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";

// Mock user profiles database
const INITIAL_PROFILE = {
  name: "Alex Sterling",
  email: "alex@nexus-ai.corp",
  bio: "Lead Infrastructure Architect specializing in LLM deployment and secure workspace scaling.",
  avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuBlhpoMt3jR2GI5_4dbQUe-h906NficthzrZBzLzhPP_Sk26XRjIeKEhdDe3XayRBKrDioV6YTYlejHmxj14-m4M7BI7BDR_1Z_zTUElpmcNFmlBOHXsLki-E6g2N2lZqzUO4JLJTvRLeKOsGA2mmU9VZ3MSoBuoRJiMRlQ1sg-DIfvbLOQ0Ychl0ZSeCXEtttsdSOl-Ubb3FPseUKTheJ7ZiTtUgq0lCTh001e-G5XTZ7xYxwGEye2lK7lN-f7yZuY8gkwNuTyXBQI",
};

// Mock credential keys database
const INITIAL_KEYS: ApiKeyItem[] = [
  {
    id: "key-1",
    name: "Production_Main_Vault",
    keyMasked: "nx_live_••••••••••••3a9d",
    fullValue: "nx_live_8321_xYk_p392_TfK_99183a9d",
    lastUsed: "2 hours ago",
    status: "Active",
  },
  {
    id: "key-2",
    name: "Development_Localhost",
    keyMasked: "nx_test_••••••••••••7f2b",
    fullValue: "nx_test_0428_lMp_a824_PzQ_88297f2b",
    lastUsed: "3 days ago",
    status: "Inactive",
  },
];

export default function SettingsPage() {
  const [profile, setProfile] = useState(INITIAL_PROFILE);
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>(INITIAL_KEYS);
  
  // Preference states
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [twoFactorAuth, setTwoFactorAuth] = useState(false);

  const handleSaveProfile = (updatedProfile: typeof INITIAL_PROFILE) => {
    setProfile(updatedProfile);
  };

  const handleKeysChange = (updatedKeys: ApiKeyItem[]) => {
    setApiKeys(updatedKeys);
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

        {/* API Credentials Card */}
        <ApiKeysManager 
          initialKeys={apiKeys} 
          onKeysChange={handleKeysChange} 
        />

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
