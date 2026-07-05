"use client";

import Link from "next/link";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full flex flex-col justify-between items-center p-6 bg-surface relative overflow-y-auto select-none">
      
      {/* Spacer to push card to visual center */}
      <div className="flex-grow shrink-0" />

      {/* Main card container */}
      <div className="w-full max-w-[440px] z-10 my-8">
        {children}
      </div>

      {/* Spacer */}
      <div className="flex-grow shrink-0" />

      {/* System Status Bar at the bottom */}
      <footer className="w-full max-w-[440px] flex justify-between items-center px-1 shrink-0 select-none text-[10px] md:text-[11px] font-mono tracking-wider opacity-60">
        <div className="flex items-center gap-2">
          {/* Pulsing indicator */}
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="uppercase text-on-surface-variant font-semibold">
            Nexus Grid: Operational
          </span>
        </div>

        <div className="flex gap-4">
          <Link href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-medium">
            Privacy
          </Link>
          <Link href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-medium">
            Terms
          </Link>
        </div>
      </footer>

    </div>
  );
}
