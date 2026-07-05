"use client";

import { Suspense } from "react";
import AuthLayout from "@/components/auth/auth-layout";
import AuthCard from "@/components/auth/auth-card";

export default function LoginPage() {
  return (
    <AuthLayout>
      <Suspense fallback={
        <div className="bg-surface-container-low border border-outline-variant rounded-2xl p-8 flex items-center justify-center min-h-[320px]">
          <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
        </div>
      }>
        <AuthCard />
      </Suspense>
    </AuthLayout>
  );
}
