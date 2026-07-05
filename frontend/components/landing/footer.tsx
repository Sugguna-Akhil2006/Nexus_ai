"use client";

import Link from "next/link";
import { Boxes, Globe, MessageSquare, AtSign } from "lucide-react";

export default function Footer() {
  return (
    <footer className="max-w-7xl mx-auto px-6 py-12 mt-12 border-t border-outline-variant/30">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
        {/* Brand Information */}
        <div className="col-span-1 md:col-span-2 space-y-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary">
              <Boxes className="size-5" />
            </div>
            <span className="text-xl font-bold text-on-surface tracking-tight">Nexus AI</span>
          </div>
          <p className="text-sm text-on-surface-variant max-w-sm leading-relaxed font-normal">
            Building the intelligence layer for the modern enterprise. Secure, scalable, and developer-first.
          </p>
        </div>

        {/* Product Links */}
        <div className="space-y-4">
          <h5 className="text-xs font-semibold text-on-surface uppercase tracking-widest">
            Product
          </h5>
          <ul className="space-y-2 text-sm text-on-surface-variant">
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Agents
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Marketplace
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Integrations
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Changelog
              </Link>
            </li>
          </ul>
        </div>

        {/* Company Links */}
        <div className="space-y-4">
          <h5 className="text-xs font-semibold text-on-surface uppercase tracking-widest">
            Company
          </h5>
          <ul className="space-y-2 text-sm text-on-surface-variant">
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                About
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Security
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Terms
              </Link>
            </li>
            <li>
              <Link href="#" className="hover:text-primary transition-colors duration-150">
                Privacy
              </Link>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Copyright & Social Row */}
      <div className="mt-12 pt-6 border-t border-outline-variant/40 flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-medium text-on-surface-variant">
        <p>© 2024 Nexus AI Enterprise. All rights reserved.</p>
        <div className="flex items-center gap-6">
          <Link href="#" aria-label="Website" className="text-on-surface-variant hover:text-primary transition-colors duration-150">
            <Globe className="size-5" />
          </Link>
          <Link href="#" aria-label="Community" className="text-on-surface-variant hover:text-primary transition-colors duration-150">
            <MessageSquare className="size-5" />
          </Link>
          <Link href="#" aria-label="Contact" className="text-on-surface-variant hover:text-primary transition-colors duration-150">
            <AtSign className="size-5" />
          </Link>
        </div>
      </div>
    </footer>
  );
}
