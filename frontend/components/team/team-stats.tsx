"use client";

import { Users, Mail, BarChart3 } from "lucide-react";

interface TeamStatsProps {
  totalMembers: number;
  pendingInvites: number;
  apiConsumption: number; // e.g. 82
}

export default function TeamStats({
  totalMembers,
  pendingInvites,
  apiConsumption,
}: TeamStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 select-none">
      
      {/* Total Members */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
        <div className="flex justify-between items-start mb-4">
          <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px] md:text-xs">
            Total Members
          </span>
          <Users className="size-5 text-primary shrink-0" />
        </div>
        <div className="text-xl md:text-2xl font-bold text-on-surface leading-none">
          {totalMembers}
        </div>
        <div className="text-[10px] md:text-xs text-on-surface-variant mt-2 flex items-center gap-1">
          <span className="text-green-400 font-bold leading-none">+3</span> this month
        </div>
      </div>

      {/* Pending Invites */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
        <div className="flex justify-between items-start mb-4">
          <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px] md:text-xs">
            Pending Invites
          </span>
          <Mail className="size-5 text-tertiary shrink-0" />
        </div>
        <div className="text-xl md:text-2xl font-bold text-on-surface leading-none">
          {pendingInvites}
        </div>
        <div className="text-[10px] md:text-xs text-on-surface-variant mt-2 leading-none">
          Expiring in &lt; 48h
        </div>
      </div>

      {/* API Consumption progress */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
        <div className="flex justify-between items-start mb-4">
          <span className="text-on-surface-variant/80 font-bold uppercase tracking-wider text-[10px] md:text-xs">
            API Consumption
          </span>
          <BarChart3 className="size-5 text-outline shrink-0" />
        </div>
        <div className="text-xl md:text-2xl font-bold text-on-surface leading-none">
          {apiConsumption}%
        </div>
        <div className="w-full bg-surface-container-highest h-1.5 rounded-full mt-3 overflow-hidden select-none">
          <div className="bg-primary h-full rounded-full" style={{ width: `${apiConsumption}%` }} />
        </div>
      </div>

    </div>
  );
}
