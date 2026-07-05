"use client";

import { Webhook, Timer, Split, FileCode, Database, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LibraryItem {
  type: string; // React Flow custom node name, e.g. "webhookNode"
  label: string;
  category: "Input" | "Logic" | "Actions";
  icon: React.ComponentType<{ className?: string }>;
  iconColorClass: string;
}

const PALETTE_ITEMS: LibraryItem[] = [
  {
    type: "webhookNode",
    label: "Webhook",
    category: "Input",
    icon: Webhook,
    iconColorClass: "text-primary",
  },
  {
    type: "cronNode",
    label: "Cron Job",
    category: "Input",
    icon: Timer,
    iconColorClass: "text-primary",
  },
  {
    type: "conditionNode",
    label: "Condition",
    category: "Logic",
    icon: Split,
    iconColorClass: "text-tertiary",
  },
  {
    type: "scriptNode",
    label: "JS Script",
    category: "Logic",
    icon: FileCode,
    iconColorClass: "text-tertiary",
  },
  {
    type: "dbNode",
    label: "DB Query",
    category: "Actions",
    icon: Database,
    iconColorClass: "text-secondary",
  },
];

export default function NodeLibrary() {
  const handleDragStart = (event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData("application/reactflow", JSON.stringify({ nodeType, label }));
    event.dataTransfer.effectAllowed = "move";
  };

  const categories: ("Input" | "Logic" | "Actions")[] = ["Input", "Logic", "Actions"];

  return (
    <div className="absolute left-6 top-6 bottom-6 w-56 bg-surface-container border border-outline-variant rounded-xl z-30 flex flex-col overflow-hidden shadow-2xl select-none">
      {/* Header */}
      <div className="p-4 border-b border-outline-variant flex justify-between items-center shrink-0">
        <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface">
          Node Library
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-on-surface-variant hover:text-primary rounded cursor-pointer"
          title="Filter library"
        >
          <Filter className="size-4" />
        </Button>
      </div>

      {/* Palette listing */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-4">
        {categories.map((cat) => {
          const items = PALETTE_ITEMS.filter((item) => item.category === cat);
          return (
            <div key={cat} className="space-y-2">
              <span className="text-[10px] uppercase tracking-widest text-on-surface-variant/60 font-bold block pl-0.5">
                {cat}
              </span>
              <div className="space-y-1.5">
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.type}
                      draggable
                      onDragStart={(e) => handleDragStart(e, item.type, item.label)}
                      className="p-3 bg-surface-container-high border border-outline-variant rounded-lg flex items-center gap-3 cursor-grab hover:border-primary/50 hover:bg-primary/5 active:scale-98 active:cursor-grabbing transition-all group shadow-sm select-none"
                    >
                      <Icon className={`${item.iconColorClass} size-4`} />
                      <span className="text-xs md:text-sm font-medium text-on-surface group-hover:text-primary transition-colors truncate">
                        {item.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
