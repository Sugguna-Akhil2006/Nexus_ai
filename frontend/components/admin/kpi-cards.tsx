"use client";

import { useEffect, useState } from "react";
import { DollarSign, Building2, Activity, Users } from "lucide-react";

export default function KpiCards() {
  const [revenue, setRevenue] = useState(0);
  const [orgs, setOrgs] = useState(0);
  const [uptime, setUptime] = useState(0);
  const [sessions, setSessions] = useState(0);

  useEffect(() => {
    // Mounting count ticking animations
    const duration = 1000;
    const steps = 30;
    const intervalTime = duration / steps;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      const progress = step / steps;
      const easeOut = 1 - Math.pow(1 - progress, 3); // cubic ease-out

      setRevenue(parseFloat((1.2 * easeOut).toFixed(1)));
      setOrgs(Math.floor(482 * easeOut));
      setUptime(parseFloat((99.99 * easeOut).toFixed(2)));
      setSessions(Math.floor(14202 * easeOut));

      if (step >= steps) {
        clearInterval(interval);
      }
    }, intervalTime);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 select-none text-xs md:text-sm">
      
      {/* Total Revenue */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <DollarSign className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">
            +12.5% ↑
          </span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Total Revenue
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            ${revenue}M
          </p>
        </div>
      </div>

      {/* Active Orgs */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Building2 className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">
            +48 new
          </span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Active Enterprise Orgs
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {orgs}
          </p>
        </div>
      </div>

      {/* System Uptime */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Activity className="size-4.5" />
          </span>
          <span className="text-on-surface-variant font-mono font-semibold leading-none mt-1">
            Perfect
          </span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            System Uptime
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {uptime}%
          </p>
        </div>
      </div>

      {/* Active Sessions */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Users className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">
            +2.1k ↑
          </span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Active Sessions
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {sessions.toLocaleString()}
          </p>
        </div>
      </div>

    </div>
  );
}
