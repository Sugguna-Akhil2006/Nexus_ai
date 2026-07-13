"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Trash2, Info, ShieldAlert, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type ConfirmVariant = "destructive" | "warning" | "info";

interface ConfirmationDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback to close the dialog */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Description body text */
  description: string;
  /** Visual variant controlling colors and default icon */
  variant?: ConfirmVariant;
  /** Custom icon override */
  icon?: LucideIcon;
  /** Confirm button label (default: "Confirm") */
  confirmLabel?: string;
  /** Cancel button label (default: "Cancel") */
  cancelLabel?: string;
  /** Async handler called on confirm — button shows loading spinner while pending */
  onConfirm: () => void | Promise<void>;
}

const VARIANT_CONFIG: Record<ConfirmVariant, {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  confirmClass: string;
}> = {
  destructive: {
    icon: Trash2,
    iconBg: "bg-red-500/10 border-red-500/20",
    iconColor: "text-red-400",
    confirmClass: "bg-red-500 hover:bg-red-600 text-white border-none",
  },
  warning: {
    icon: AlertTriangle,
    iconBg: "bg-amber-500/10 border-amber-500/20",
    iconColor: "text-amber-400",
    confirmClass: "bg-amber-500 hover:bg-amber-600 text-white border-none",
  },
  info: {
    icon: Info,
    iconBg: "bg-primary/10 border-primary/20",
    iconColor: "text-primary",
    confirmClass: "bg-primary hover:bg-primary/90 text-primary-foreground border-none",
  },
};

/**
 * Reusable confirmation dialog for destructive or important actions.
 * Built on top of the existing Dialog primitive.
 *
 * @example
 * <ConfirmationDialog
 *   open={showDelete}
 *   onOpenChange={setShowDelete}
 *   title="Delete Agent"
 *   description="This will permanently remove the agent and all associated data."
 *   variant="destructive"
 *   confirmLabel="Delete Agent"
 *   onConfirm={handleDelete}
 * />
 */
export default function ConfirmationDialog({
  open,
  onOpenChange,
  title,
  description,
  variant = "destructive",
  icon,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
}: ConfirmationDialogProps) {
  const [isLoading, setIsLoading] = useState(false);
  const config = VARIANT_CONFIG[variant];
  const IconComponent = icon || config.icon;

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm();
    } finally {
      setIsLoading(false);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="bg-surface-container border border-outline-variant rounded-2xl max-w-md shadow-2xl"
        showCloseButton={false}
      >
        <DialogHeader className="flex flex-col items-center text-center gap-4 pt-2">
          {/* Icon */}
          <div className={cn(
            "w-14 h-14 rounded-xl border flex items-center justify-center",
            config.iconBg
          )}>
            <IconComponent className={cn("size-7", config.iconColor)} />
          </div>

          <div className="space-y-2">
            <DialogTitle className="text-lg font-bold text-on-surface">
              {title}
            </DialogTitle>
            <DialogDescription className="text-sm text-on-surface-variant leading-relaxed max-w-sm mx-auto">
              {description}
            </DialogDescription>
          </div>
        </DialogHeader>

        <DialogFooter className="flex gap-3 pt-4 sm:justify-center">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
            className="flex-1 bg-surface-container-low border border-outline-variant hover:bg-surface-container text-on-surface font-bold text-xs rounded-lg py-2.5 cursor-pointer"
          >
            {cancelLabel}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            className={cn(
              "flex-1 font-bold text-xs rounded-lg py-2.5 cursor-pointer flex items-center justify-center gap-2",
              config.confirmClass,
              isLoading && "opacity-80"
            )}
          >
            {isLoading && (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
