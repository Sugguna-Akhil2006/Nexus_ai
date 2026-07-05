"use client";

import { ThemeProvider } from "next-themes";
import {
    QueryClient,
    QueryClientProvider,
} from "@tanstack/react-query";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { ReactNode, useState } from "react";
import { AuthProvider } from "@/providers/auth-provider";

export default function Providers({
    children,
}: {
    children: ReactNode;
}) {
    const [queryClient] = useState(
        () => new QueryClient()
    );

    return (
        <ThemeProvider
            attribute="class"
            defaultTheme="dark"
            enableSystem
            disableTransitionOnChange
        >
            <QueryClientProvider client={queryClient}>
                <AuthProvider>
                    <TooltipProvider>
                        {children}
                        <Toaster richColors position="top-right" />
                    </TooltipProvider>
                </AuthProvider>
            </QueryClientProvider>
        </ThemeProvider>
    );
}