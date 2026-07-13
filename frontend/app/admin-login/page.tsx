"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Eye, EyeOff, ArrowRight, Mail, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useAuth } from "@/providers/auth-provider";
import AuthLayout from "@/components/auth/auth-layout";

export default function AdminLoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error("Please enter a valid email address.");
      return;
    }
    if (!password || password.length < 6) {
      toast.error("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: email, password })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid admin credentials.");
      }
      const data = await res.json();
      const mappedRole = data.role && data.role.toLowerCase() === "admin" ? "Admin" : "Member";

      if (mappedRole !== "Admin") {
        throw new Error("Access Denied. Only administrator accounts can login here.");
      }

      document.cookie = `Authorization=Bearer ${data.token}; path=/; max-age=3600; SameSite=Strict`;
      login({
        name: data.username.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
        email: data.username,
        role: "Admin",
        token: data.token
      } as any);
      toast.success(`Welcome Administrator! Signed in as ${data.username}`);
      router.push("/dashboard/admin");
    } catch (err: any) {
      toast.error(err.message || "Admin login error.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="bg-surface-container-low border border-outline-variant rounded-2xl p-6 md:p-8 flex flex-col gap-6 md:gap-8 shadow-2xl select-none animate-in fade-in zoom-in-95 duration-200 w-full max-w-md mx-auto">
        <header className="flex flex-col items-center gap-2 select-text">
          <div className="w-12 h-12 bg-secondary/10 border border-secondary/20 rounded-xl flex items-center justify-center shadow-md">
            <ShieldCheck className="size-6 text-secondary" />
          </div>
          <div className="text-center mt-1">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
              Secure Admin Portal
            </h1>
            <p className="text-xs md:text-sm text-on-surface-variant/80 font-medium mt-1 select-none">
              Authorized access only
            </p>
          </div>
        </header>

        <form onSubmit={handleFormSubmit} className="flex flex-col gap-4 text-xs md:text-sm select-none">
          <div className="flex flex-col gap-1.5">
            <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Admin Email
            </label>
            <div className="relative">
              <Mail className="size-4 text-outline absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@nexus-ai.corp"
                required
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-9 pr-4 py-2.5 text-on-surface focus:outline-none focus:border-secondary transition-all input-glow"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Password
            </label>
            <div className="relative">
              <Lock className="size-4 text-outline absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-9 pr-10 py-2.5 text-on-surface focus:outline-none focus:border-secondary transition-all input-glow"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-on-surface transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-secondary text-secondary-foreground hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold py-5 rounded-lg border-none flex items-center justify-center gap-1.5 cursor-pointer mt-2 shadow-sm disabled:opacity-50"
          >
            <span>
              {isLoading ? "Authenticating..." : "Authorized Sign In"}
            </span>
            {!isLoading && <ArrowRight className="size-4 shrink-0" />}
          </Button>
        </form>
      </div>
    </AuthLayout>
  );
}
