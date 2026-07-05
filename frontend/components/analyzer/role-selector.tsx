"use client";

import { Target, ChevronDown } from "lucide-react";

interface RoleSelectorProps {
  selectedRole: string;
  onChangeRole: (role: string) => void;
  jobDescription: string;
  onChangeJD: (jd: string) => void;
}

const ROLES = [
  "Senior Fullstack Engineer",
  "Product Marketing Manager",
  "AI Research Scientist"
];

export default function RoleSelector({
  selectedRole,
  onChangeRole,
  jobDescription,
  onChangeJD,
}: RoleSelectorProps) {
  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm h-full flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Target Role
        </h3>
        <Target className="size-4 text-on-surface-variant" />
      </div>

      {/* Select Role and Job Description inputs */}
      <div className="space-y-4">
        {/* Dropdown */}
        <div className="relative">
          <select
            value={selectedRole}
            onChange={(e) => onChangeRole(e.target.value)}
            className="w-full bg-surface border border-outline-variant rounded-lg pl-3 pr-10 py-2.5 text-xs md:text-sm font-semibold text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary appearance-none cursor-pointer"
          >
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <ChevronDown className="size-4 text-on-surface-variant absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        {/* Details Textarea */}
        <textarea
          value={jobDescription}
          onChange={(e) => onChangeJD(e.target.value)}
          placeholder="Paste job description details for specific weighting..."
          className="w-full h-28 bg-surface border border-outline-variant rounded-lg p-3 text-xs md:text-sm text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary resize-none custom-scrollbar"
        />
      </div>
    </div>
  );
}
