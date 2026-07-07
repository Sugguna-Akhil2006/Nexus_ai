"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  alt?: boolean;
  shift?: boolean;
  action: () => void;
}

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const s of shortcuts) {
        const matchesKey = e.key.toLowerCase() === s.key.toLowerCase();
        const matchesCtrl = !!s.ctrl === (e.ctrlKey || e.metaKey);
        const matchesAlt = !!s.alt === e.altKey;
        const matchesShift = !!s.shift === e.shiftKey;

        if (matchesKey && matchesCtrl && matchesAlt && matchesShift) {
          e.preventDefault();
          s.action();
          break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts]);
}
