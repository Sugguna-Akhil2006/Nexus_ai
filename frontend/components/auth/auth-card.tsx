"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bot, Eye, EyeOff, ArrowRight, Mail, Lock, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useAuth } from "@/providers/auth-provider";

export default function AuthCard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated } = useAuth();

  // Redirect away if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  // Modes: "login" | "signup" | "forgot"
  const [mode, setMode] = useState<"login" | "signup" | "forgot">("login");
  const [showPassword, setShowPassword] = useState(false);

  // Form states
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleToggleMode = () => {
    setName("");
    setEmail("");
    setPassword("");
    if (mode === "login") {
      setMode("signup");
    } else {
      setMode("login");
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validations
    if (mode === "signup" && !name.trim()) {
      toast.error("Please enter your Full Name.");
      return;
    }
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error("Please enter a valid email address.");
      return;
    }
    if (mode !== "forgot" && (!password || password.length < 6)) {
      toast.error("Password must be at least 6 characters.");
      return;
    }

    setIsLoading(true);
    try {
      if (mode === "forgot") {
        // Mock password reset endpoint or mock success
        await new Promise((resolve) => setTimeout(resolve, 1000));
        toast.success(`Password reset link sent to: ${email}`);
        setMode("login");
      } else if (mode === "login") {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, password })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Invalid username or password.");
        }
        const data = await res.json();
        const mappedRole: "Admin" | "Member" | "Viewer" = data.role && data.role.toLowerCase() === "admin" ? "Admin" : data.role && data.role.toLowerCase() === "viewer" ? "Viewer" : "Member";
        if (mappedRole === "Admin") {
          throw new Error("Admin login is restricted here. Please use the secure Admin Portal.");
        }
        document.cookie = `Authorization=Bearer ${data.token}; path=/; max-age=3600; SameSite=Strict`;
        login({
          name: data.username.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
          email: data.username,
          role: mappedRole,
          token: data.token
        } as any);
        toast.success(`Welcome back! Signed in as ${data.username}`);
        const returnTo = searchParams.get("returnTo");
        router.push(returnTo ? decodeURIComponent(returnTo) : "/dashboard");
      } else {
        // signup mode
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, password, email })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Registration failed. Username may already exist.");
        }
        // Auto-login
        const loginRes = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: email, password })
        });
        if (!loginRes.ok) {
          throw new Error("Registration succeeded but auto-login failed.");
        }
        const data = await loginRes.json();
        const mappedRole: "Admin" | "Member" | "Viewer" = data.role && data.role.toLowerCase() === "admin" ? "Admin" : data.role && data.role.toLowerCase() === "viewer" ? "Viewer" : "Member";
        document.cookie = `Authorization=Bearer ${data.token}; path=/; max-age=3600; SameSite=Strict`;
        login({
          name: name.trim() || data.username.split("@")[0],
          email: data.username,
          role: mappedRole,
          token: data.token
        } as any);
        toast.success(`Account created! Welcome, ${name.trim() || email}.`);
        router.push("/dashboard");
      }
    } catch (err: any) {
      toast.error(err.message || "Authentication error.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialAuth = (provider: "Google" | "GitHub") => {
    toast.info(`Connecting OAuth integration flow via: ${provider}...`);
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-2xl p-6 md:p-8 flex flex-col gap-6 md:gap-8 shadow-2xl select-none animate-in fade-in zoom-in-95 duration-200">
      
      {/* branding header info */}
      <header className="flex flex-col items-center gap-2 select-text">
        <div className="w-12 h-12 bg-primary-container rounded-xl flex items-center justify-center shadow-md">
          <Bot className="size-6 text-white" />
        </div>
        <div className="text-center mt-1">
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
            {mode === "login" && "Welcome back"}
            {mode === "signup" && "Create account"}
            {mode === "forgot" && "Reset password"}
          </h1>
          <p className="text-xs md:text-sm text-on-surface-variant/80 font-medium mt-1 select-none">
            {mode === "login" && "Access your Nexus AI workspace"}
            {mode === "signup" && "Start your high-performance journey"}
            {mode === "forgot" && "Provide your email to receive reset token"}
          </p>
        </div>
      </header>

      {/* Main input form */}
      <form onSubmit={handleFormSubmit} className="flex flex-col gap-4 text-xs md:text-sm select-none">
        
        {/* Name input (SignUp only) */}
        {mode === "signup" && (
          <div className="flex flex-col gap-1.5 animate-in fade-in duration-300">
            <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
              Full Name
            </label>
            <div className="relative">
              <User className="size-4 text-outline absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                required
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-9 pr-4 py-2.5 text-on-surface focus:outline-none focus:border-primary-container transition-all input-glow"
              />
            </div>
          </div>
        )}

        {/* Email input */}
        <div className="flex flex-col gap-1.5">
          <label className="font-bold text-on-surface-variant/80 pl-0.5 uppercase tracking-wider text-[10px] md:text-xs">
            Email Address
          </label>
          <div className="relative">
            <Mail className="size-4 text-outline absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-9 pr-4 py-2.5 text-on-surface focus:outline-none focus:border-primary-container transition-all input-glow"
            />
          </div>
        </div>

        {/* Password input (Sign In & Sign Up only) */}
        {mode !== "forgot" && (
          <div className="flex flex-col gap-1.5">
            <div className="flex justify-between items-center px-0.5">
              <label className="font-bold text-on-surface-variant/80 uppercase tracking-wider text-[10px] md:text-xs">
                Password
              </label>
              {mode === "login" && (
                <button
                  type="button"
                  onClick={() => setMode("forgot")}
                  className="text-primary-container font-bold hover:underline cursor-pointer text-[10px] md:text-xs"
                >
                  Forgot?
                </button>
              )}
            </div>
            <div className="relative">
              <Lock className="size-4 text-outline absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg pl-9 pr-10 py-2.5 text-on-surface focus:outline-none focus:border-primary-container transition-all input-glow"
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
        )}

        {/* Submit Action Button */}
        <Button
          type="submit"
          disabled={isLoading}
          className="w-full bg-primary-container text-white hover:opacity-90 active:scale-98 text-xs md:text-sm font-bold py-5 rounded-lg border-none flex items-center justify-center gap-1.5 cursor-pointer mt-2 shadow-sm disabled:opacity-50"
        >
          <span>
            {isLoading ? "Authenticating..." : mode === "login" ? "Sign In" : mode === "signup" ? "Create Account" : "Reset Password"}
          </span>
          {!isLoading && <ArrowRight className="size-4 shrink-0" />}
        </Button>
      </form>

      {/* Divider */}
      {mode !== "forgot" && (
        <>
          <div className="flex items-center gap-3 select-none">
            <div className="h-[1px] flex-1 bg-outline-variant/60" />
            <span className="font-mono text-[9px] text-outline uppercase tracking-widest leading-none">
              or continue with
            </span>
            <div className="h-[1px] flex-1 bg-outline-variant/60" />
          </div>

          {/* Social Sign-In buttons */}
          <div className="grid grid-cols-2 gap-4 select-none shrink-0">
            <button
              onClick={() => handleSocialAuth("Google")}
              className="flex items-center justify-center gap-2 border border-outline-variant hover:bg-surface-container-high hover:border-outline/50 py-2.5 rounded-lg transition-all group cursor-pointer"
            >
              <svg className="w-4 h-4 fill-on-surface-variant group-hover:fill-on-surface transition-colors shrink-0" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              <span className="font-semibold text-xs text-on-surface-variant group-hover:text-on-surface">Google</span>
            </button>

            <button
              onClick={() => handleSocialAuth("GitHub")}
              className="flex items-center justify-center gap-2 border border-outline-variant hover:bg-surface-container-high hover:border-outline/50 py-2.5 rounded-lg transition-all group cursor-pointer"
            >
              <svg className="w-4 h-4 fill-on-surface-variant group-hover:fill-on-surface transition-colors shrink-0" viewBox="0 0 24 24">
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
              <span className="font-semibold text-xs text-on-surface-variant group-hover:text-on-surface">GitHub</span>
            </button>
          </div>
        </>
      )}

      {/* Footer Toggle links */}
      <footer className="text-center text-xs md:text-sm select-none shrink-0">
        {mode === "forgot" ? (
          <button
            type="button"
            onClick={() => setMode("login")}
            className="text-primary-container font-bold hover:underline cursor-pointer"
          >
            Back to Sign in
          </button>
        ) : (
          <p className="text-on-surface-variant/90 font-medium">
            <span>
              {mode === "login" ? "Don't have an account?" : "Already have an account?"}
            </span>
            <button
              type="button"
              onClick={handleToggleMode}
              className="text-primary-container font-bold hover:underline ml-1.5 cursor-pointer bg-transparent border-none p-0"
            >
              {mode === "login" ? "Sign up" : "Sign in"}
            </button>
          </p>
        )}
      </footer>

    </div>
  );
}
