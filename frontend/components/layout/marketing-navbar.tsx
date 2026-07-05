"use client";

import Link from "next/link";
import Image from "next/image";
import { Boxes, Bell, HelpCircle, Menu } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";

export default function MarketingNavbar() {
  const profileImageUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuAQPWQApcT52DE-3vQdZRRCoKniiP3TrN2d0bhsPn6NiQzY-0nrV_bNt2qYfeq6tPIplH4q5K6Vh7Ob-E1alQEMRiUUxEGlevIxrpeCDXGgph3_yqC1v63qVcTwDBblsZq1fG5xjsxnyxUjrYjvII392MblRFeyUknfePTonIS1DvB5kY1bmujaQ6ft5-lBHRpH3pfsRAff-FMnSoOF1RNZAkshyDM1yjk1ow5_RLXX6TziFiDQIglB78U4_DQSXiGHr3MoQI98gviJ";

  const navLinks = (
    <>
      <Link href="#" className="text-sm font-semibold text-primary transition-colors">
        Solutions
      </Link>
      <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
        Framework
      </Link>
      <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
        Resources
      </Link>
      <Link href="#" className="text-sm font-medium text-on-surface-variant hover:text-primary transition-colors">
        Pricing
      </Link>
    </>
  );

  return (
    <header className="sticky top-0 z-40 w-full bg-surface/85 backdrop-blur-md border-b border-outline-variant flex justify-between items-center h-16 px-6 md:px-8 lg:px-12 transition-all">
      {/* Brand Logo & Mobile Trigger Group */}
      <div className="flex items-center gap-4">
        {/* Mobile menu trigger */}
        <Sheet>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden shrink-0 text-on-surface-variant hover:text-on-surface cursor-pointer"
            >
              <Menu className="size-5" />
              <span className="sr-only">Toggle navigation menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-6 w-64 border-r border-outline-variant bg-surface" showCloseButton={true}>
            <SheetTitle className="text-left font-bold text-on-surface flex items-center gap-2 mb-8">
              <Boxes className="size-5 text-primary" />
              Nexus AI
            </SheetTitle>
            <SheetDescription className="sr-only">
              Landing page solutions, framework, resources, and pricing navigation menu.
            </SheetDescription>
            <nav className="flex flex-col gap-4">
              {navLinks}
            </nav>
          </SheetContent>
        </Sheet>

        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2 select-none">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary">
            <Boxes className="size-5" />
          </div>
          <span className="text-lg font-bold text-on-surface tracking-tight leading-none">
            Nexus AI
          </span>
        </Link>
      </div>

      {/* Nav links and actions */}
      <div className="flex items-center gap-6">
        {/* Desktop Solutions, Framework, etc. */}
        <nav className="hidden lg:flex items-center gap-6">
          {navLinks}
        </nav>

        {/* Right side icons */}
        <div className="flex items-center gap-4">
          <Bell className="size-5 text-on-surface-variant cursor-pointer hover:text-primary opacity-80 hover:opacity-100 transition-all" />
          <HelpCircle className="size-5 text-on-surface-variant cursor-pointer hover:text-primary opacity-80 hover:opacity-100 transition-all" />
          
          {/* User profile avatar */}
          <div className="h-8 w-8 rounded-full bg-surface-container-highest overflow-hidden border border-outline-variant relative">
            <Image
              alt="User Profile"
              src={profileImageUrl}
              fill
              className="object-cover"
              sizes="32px"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
