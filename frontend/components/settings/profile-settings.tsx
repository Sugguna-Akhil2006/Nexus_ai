"use client";

import { useState } from "react";
import Image from "next/image";
import { Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface UserProfile {
  name: string;
  email: string;
  bio: string;
  avatarUrl: string;
}

interface ProfileSettingsProps {
  initialProfile: UserProfile;
  onSave: (updatedProfile: UserProfile) => void;
}

export default function ProfileSettings({
  initialProfile,
  onSave,
}: ProfileSettingsProps) {
  const [profile, setProfile] = useState<UserProfile>(initialProfile);

  const handleChange = (key: keyof UserProfile, val: string) => {
    setProfile((prev) => ({ ...prev, [key]: val }));
  };

  const handleAvatarChange = () => {
    // Simulate image uploading
    const demoAvatars = [
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCxxelS1cuHPXaiKjDhWXpETNJ2ygm-voJo29CYmfhCBlYM6vUdbhiMHXQx5iRntD7iHBpsz2tai7M4fgE3b4COMstUZhFeR8GVLhH6q6XChgRRunodNhyEJ6ZW86mH-UbDROm-FCAYFuEFi3_vby215djAcm9aj-PDAb2csgMzti08LLfwzMLlUdRZrbwrlEysPqoxttrDxu22TH86sXE76xA4_ft5N9uDzjoAMp8kxoItzwl3ysAaOaS_LNYRcM0u9GhB2-PLL0mO",
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAFwF085WuVUaEX4ze7lw-_5uUoG_aOcRT1jW-6I4DvTjxsVT2CbqWviixl9W7R2SfhlRJz_OL3IsC7DTBan_KRfvJPR-x-blcgtQo00i3KhmDM5SrKXCK5g6seVx_XFxRIKJ3RA_ONDwOq-EPbCc1nngFI_msy9Qwi9XVbWJfXiDBH2zQGh2rlJ_WgYROafV8fucH6sdoZJz8eGzIgdOQWP0P6Eto1YhZlJABSehz1YMtpzEdPB-1zuUPzvLqXuF03ILF5agwYOpwb",
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBlhpoMt3jR2GI5_4dbQUe-h906NficthzrZBzLzhPP_Sk26XRjIeKEhdDe3XayRBKrDioV6YTYlejHmxj14-m4M7BI7BDR_1Z_zTUElpmcNFmlBOHXsLki-E6g2N2lZqzUO4JLJTvRLeKOsGA2mmU9VZ3MSoBuoRJiMRlQ1sg-DIfvbLOQ0Ychl0ZSeCXEtttsdSOl-Ubb3FPseUKTheJ7ZiTtUgq0lCTh001e-G5XTZ7xYxwGEye2lK7lN-f7yZuY8gkwNuTyXBQI"
    ];
    // Select a random profile avatar URL
    const nextIdx = Math.floor(Math.random() * demoAvatars.length);
    handleChange("avatarUrl", demoAvatars[nextIdx]);
    toast.success("New profile avatar uploaded successfully!");
  };

  const handleSave = () => {
    onSave(profile);
    toast.success("Profile configurations saved successfully!");
  };

  return (
    <section className="bg-surface-container-low border border-outline-variant rounded-2xl overflow-hidden shadow-sm select-none">
      {/* Header */}
      <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container shrink-0">
        <div>
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            Profile Configuration
          </h3>
          <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
            Personal details and public representation.
          </p>
        </div>
        <Button
          onClick={handleSave}
          className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 text-xs font-bold rounded-lg px-4 py-2 cursor-pointer border-none shadow shadow-primary/15"
        >
          Save Changes
        </Button>
      </div>

      {/* Grid Inputs */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-xs md:text-sm">
        {/* Name */}
        <div className="space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Full Name
          </label>
          <input
            type="text"
            value={profile.name}
            onChange={(e) => handleChange("name", e.target.value)}
            placeholder="Alex Sterling"
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm"
          />
        </div>

        {/* Email */}
        <div className="space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Work Email
          </label>
          <input
            type="email"
            value={profile.email}
            onChange={(e) => handleChange("email", e.target.value)}
            placeholder="alex@nexus-ai.corp"
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all text-xs md:text-sm"
          />
        </div>

        {/* Bio */}
        <div className="md:col-span-2 space-y-1.5">
          <label className="font-bold text-on-surface-variant/80 block pl-0.5 uppercase tracking-wider text-[10px]">
            Bio / Role Description
          </label>
          <textarea
            value={profile.bio}
            onChange={(e) => handleChange("bio", e.target.value)}
            placeholder="Lead Infrastructure Architect specializing in LLM deployment and secure workspace scaling."
            rows={3}
            className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-4 py-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all resize-none text-xs md:text-sm custom-scrollbar"
          />
        </div>

        {/* Avatar Upload */}
        <div className="md:col-span-2 flex items-center gap-6 pt-2 select-none">
          <div 
            onClick={handleAvatarChange}
            className="w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-surface-container-highest border border-outline-variant flex items-center justify-center relative overflow-hidden group cursor-pointer shadow-inner shrink-0"
          >
            <Image
              alt="Avatar Profile"
              src={profile.avatarUrl}
              fill
              sizes="(max-width: 768px) 64px, 80px"
              className="object-cover"
            />
            {/* Edit overlay */}
            <div className="absolute inset-0 bg-surface/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Camera className="size-5 text-on-surface" />
            </div>
          </div>

          <div className="space-y-1 shrink-0">
            <p className="text-xs md:text-sm font-bold text-on-surface leading-none">Avatar Image</p>
            <p className="text-[10px] md:text-xs text-on-surface-variant/80 font-medium">Recommended: 400x400px. Max 2MB.</p>
            <button
              onClick={handleAvatarChange}
              className="text-primary font-bold text-xs hover:underline cursor-pointer bg-transparent border-none p-0"
            >
              Upload New
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
