import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  iconOnly?: boolean;
  className?: string;
  href?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = {
  sm: { iconPx: 20, textCls: "text-[13px]", gap: "gap-2" },
  md: { iconPx: 24, textCls: "text-[15px]", gap: "gap-2.5" },
  lg: { iconPx: 32, textCls: "text-xl",     gap: "gap-3" },
};

export default function Logo({
  iconOnly = false,
  className,
  href = "/",
  size = "md",
}: LogoProps) {
  const { iconPx, textCls, gap } = sizeMap[size];

  return (
    <Link
      href={href}
      aria-label="Nexus AI Home"
      className={cn(
        "group inline-flex items-center select-none outline-none",
        "focus-visible:ring-2 focus-visible:ring-ring/50 rounded-md",
        gap,
        className
      )}
    >
      <span
        className="relative shrink-0 rounded-md flex items-center justify-center bg-foreground"
        style={{ width: iconPx, height: iconPx }}
        aria-hidden="true"
      >
        <svg
          width={Math.round(iconPx * 0.55)}
          height={Math.round(iconPx * 0.55)}
          viewBox="0 0 12 12"
          fill="none"
          className="relative"
        >
          <path
            d="M2 10V2L10 10V2"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-background"
          />
        </svg>
      </span>

      {!iconOnly && (
        <span
          className={cn(
            "font-semibold leading-none tracking-[-0.02em] text-foreground",
            textCls
          )}
        >
          Nexus
        </span>
      )}
    </Link>
  );
}
