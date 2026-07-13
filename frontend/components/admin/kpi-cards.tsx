"use client";

import { useEffect, useState } from "react";
import { FileText, Building2, Activity, Users } from "lucide-react";

interface KpiCardsProps {
  totalWorkspaces: number;
  totalUsers: number;
  uptimeSeconds?: number;
}

/** Format uptime seconds into human-readable string */
function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return `${hours}h ${remainMins}m`;
}

export default function KpiCards({ totalWorkspaces, totalUsers, uptimeSeconds }: KpiCardsProps) {
  const [totalDocs, setTotalDocs] = useState<number | null>(null);
  const [displayDocs, setDisplayDocs] = useState(0);
  const [displayWorkspaces, setDisplayWorkspaces] = useState(0);
  const [displayUsers, setDisplayUsers] = useState(0);

  // Fetch real document count
  useEffect(() => {
    fetch("/api/documents?workspace_id=default-ws")
      .then((r) => r.json())
      .then((data) => {
        const docs = Array.isArray(data?.documents) ? data.documents.length : 0;
        setTotalDocs(docs);
      })
      .catch(() => setTotalDocs(0));
  }, []);

  // Count-up animations triggered when data is ready
  useEffect(() => {
    if (totalDocs === null) return;
    const targets = { docs: totalDocs, workspaces: totalWorkspaces, users: totalUsers };
    const duration = 900;
    const steps = 25;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      const ease = 1 - Math.pow(1 - step / steps, 3);
      setDisplayDocs(Math.round(targets.docs * ease));
      setDisplayWorkspaces(Math.round(targets.workspaces * ease));
      setDisplayUsers(Math.round(targets.users * ease));
      if (step >= steps) clearInterval(interval);
    }, duration / steps);

    return () => clearInterval(interval);
  }, [totalDocs, totalWorkspaces, totalUsers]);

  const uptimeDisplay = uptimeSeconds != null ? formatUptime(uptimeSeconds) : "—";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 select-none text-xs md:text-sm">

      {/* Total Documents */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <FileText className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">Live</span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Total Documents
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {totalDocs === null ? "…" : displayDocs}
          </p>
        </div>
      </div>

      {/* Active Orgs */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Building2 className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">Live</span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Active Enterprise Orgs
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {displayWorkspaces}
          </p>
        </div>
      </div>

      {/* System Uptime — real value from /admin/health uptime_seconds */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Activity className="size-4.5" />
          </span>
          <span className="text-on-surface-variant font-mono font-semibold leading-none mt-1">
            Running
          </span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            System Uptime
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {uptimeDisplay}
          </p>
        </div>
      </div>

      {/* Registered Users */}
      <div className="bg-surface-container-low border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm hover:border-outline transition-colors">
        <div className="flex justify-between items-start">
          <span className="text-primary bg-primary/10 p-2 rounded-lg shrink-0">
            <Users className="size-4.5" />
          </span>
          <span className="text-emerald-400 font-mono font-bold leading-none mt-1">Live</span>
        </div>
        <div className="mt-4 select-text">
          <p className="text-on-surface-variant font-semibold text-[10px] md:text-xs uppercase tracking-wider">
            Registered Users
          </p>
          <p className="text-xl md:text-2xl font-bold text-on-surface mt-1 leading-none">
            {displayUsers}
          </p>
        </div>
      </div>

    </div>
  );
}
