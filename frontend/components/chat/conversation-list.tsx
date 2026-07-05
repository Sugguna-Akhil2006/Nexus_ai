"use client";

import { MessageSquarePlus, MessageSquare, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  category: "Today" | "Yesterday" | "Older";
}

interface ConversationListProps {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onNewChat: () => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
}: ConversationListProps) {
  
  // Group conversations by category
  const categories: { key: string; label: string; items: Conversation[] }[] = [
    { key: "Today", label: "Today", items: conversations.filter(c => c.category === "Today") },
    { key: "Yesterday", label: "Yesterday", items: conversations.filter(c => c.category === "Yesterday") },
    { key: "Older", label: "Previous 7 Days", items: conversations.filter(c => c.category === "Older") },
  ];

  return (
    <div className="w-full md:w-64 border-r border-outline-variant bg-surface flex flex-col h-full shrink-0 select-none">
      {/* Header / New Chat action */}
      <div className="p-4 border-b border-outline-variant/60">
        <Button
          onClick={onNewChat}
          className="w-full justify-center gap-2 bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/80 text-on-surface hover:text-on-surface rounded-lg font-bold py-5 cursor-pointer shadow-sm"
        >
          <MessageSquarePlus className="size-4 text-primary" />
          New Chat
        </Button>
      </div>

      {/* History Items list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4 custom-scrollbar">
        {categories.map((cat) => {
          if (cat.items.length === 0) return null;
          return (
            <div key={cat.key} className="space-y-1.5">
              <h5 className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest pl-2">
                {cat.label}
              </h5>
              <div className="space-y-0.5">
                {cat.items.map((item) => {
                  const isActive = item.id === activeId;
                  return (
                    <div
                      key={item.id}
                      onClick={() => onSelect(item.id)}
                      className={cn(
                        "flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer group/item transition-all duration-150",
                        isActive
                          ? "bg-surface-container-high text-primary font-medium"
                          : "text-on-surface-variant hover:bg-surface-container-high/40 hover:text-on-surface"
                      )}
                    >
                      <div className="flex items-center gap-2.5 min-w-0 flex-1">
                        <MessageSquare className={cn("size-4 shrink-0", isActive ? "text-primary" : "text-on-surface-variant/60 group-hover/item:text-on-surface")} />
                        <span className="text-xs truncate leading-none pt-0.5">
                          {item.title}
                        </span>
                      </div>
                      
                      {/* Delete icon */}
                      <button
                        onClick={(e) => onDelete(item.id, e)}
                        className="opacity-0 group-hover/item:opacity-100 hover:text-destructive text-on-surface-variant/60 p-1 rounded hover:bg-destructive/15 transition-all cursor-pointer shrink-0 ml-1.5"
                        title="Delete chat log"
                      >
                        <Trash2 className="size-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {conversations.length === 0 && (
          <div className="text-center py-8 text-xs text-on-surface-variant/50 font-normal select-none">
            No history recorded
          </div>
        )}
      </div>
    </div>
  );
}
