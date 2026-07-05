"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard — wraps protected routes (e.g. /dashboard/*).
 *
 * While the auth state is loading from localStorage it renders a full-screen
 * skeleton so there is no flash of unauthenticated content.
 * Once loaded:
 *  - Authenticated → renders children normally
 *  - Unauthenticated → redirects to /login
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Preserve the intended destination so login can redirect back
      const returnTo = encodeURIComponent(pathname);
      router.replace(`/login?returnTo=${returnTo}`);
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // While checking localStorage — show a subtle full-screen loader
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
          <p className="text-xs text-on-surface-variant font-medium tracking-wider uppercase animate-pulse">
            Loading workspace...
          </p>
        </div>
      </div>
    );
  }

  // Unauthenticated — render nothing while the redirect fires
  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
