"use client";

import { useState } from "react";
import { MessageSquarePlus, MessageSquare, Trash2, Search, Pin, PinOff, Pencil, Download, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import ConfirmationDialog from "@/components/common/confirmation-dialog";

export interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  category: "Today" | "Yesterday" | "Older";
  isPinned?: boolean;
  messageCount?: number;
}

interface ConversationListProps {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onNewChat: () => void;
  onRename?: (id: string, newTitle: string) => void;
  onTogglePin?: (id: string) => void;
}

export default function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
  onRename,
  onTogglePin,
}: ConversationListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameText, setRenameText] = useState("");

  const filteredConversations = conversations.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Pinned conversations always float to top
  const pinnedConversations = filteredConversations.filter(c => c.isPinned);
  const unpinnedConversations = filteredConversations.filter(c => !c.isPinned);

  // Group unpinned conversations by category
  const categories: { key: string; label: string; items: Conversation[] }[] = [
    { key: "Today", label: "Today", items: unpinnedConversations.filter(c => c.category === "Today") },
    { key: "Yesterday", label: "Yesterday", items: unpinnedConversations.filter(c => c.category === "Yesterday") },
    { key: "Older", label: "Previous 7 Days", items: unpinnedConversations.filter(c => c.category === "Older") },
  ];

  const handleRenameSubmit = (id: string) => {
    if (renameText.trim()) {
      onRename?.(id, renameText.trim());
      toast.success("Conversation renamed");
    }
    setRenamingId(null);
  };

  const handleExport = (conv: Conversation) => {
    const blob = new Blob([`# ${conv.title}\nExported: ${new Date().toISOString()}\n\n[Chat messages would be exported here]`], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${conv.title.replace(/\s+/g, "_").toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Chat exported as Markdown");
  };

  const renderConversationItem = (item: Conversation) => {
    const isActive = item.id === activeId;
    const isRenaming = renamingId === item.id;

    return (
      <div
        key={item.id}
        onClick={() => !isRenaming && onSelect(item.id)}
        className={cn(
          "flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer group/item transition-all duration-150 relative",
          isActive
            ? "bg-surface-container-high text-primary font-medium"
            : "text-on-surface-variant hover:bg-surface-container-high/40 hover:text-on-surface"
        )}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <MessageSquare className={cn("size-4 shrink-0", isActive ? "text-primary" : "text-on-surface-variant/60 group-hover/item:text-on-surface")} />
          
          {isRenaming ? (
            <input
              autoFocus
              value={renameText}
              onChange={(e) => setRenameText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRenameSubmit(item.id);
                if (e.key === "Escape") setRenamingId(null);
              }}
              onBlur={() => handleRenameSubmit(item.id)}
              onClick={(e) => e.stopPropagation()}
              className="text-xs bg-surface-container-low border border-primary/30 rounded px-1.5 py-0.5 text-on-surface outline-none focus:ring-1 focus:ring-primary w-full"
            />
          ) : (
            <div className="flex flex-col min-w-0">
              <span className="text-xs truncate leading-none pt-0.5">
                {item.title}
              </span>
              {item.messageCount !== undefined && (
                <span className="text-[9px] text-on-surface-variant/40 font-mono mt-0.5">
                  {item.messageCount} messages · {item.updatedAt}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Pin indicator */}
        {item.isPinned && !isRenaming && (
          <Pin className="size-2.5 text-primary/50 shrink-0 mr-1" />
        )}
        
        {/* Context Menu */}
        {!isRenaming && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                onClick={(e) => e.stopPropagation()}
                className="opacity-0 group-hover/item:opacity-100 text-on-surface-variant/60 p-1 rounded hover:bg-surface-container-highest transition-all cursor-pointer shrink-0 ml-1 bg-transparent border-none"
              >
                <MoreVertical className="size-3" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
              <DropdownMenuItem
                className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  setRenameText(item.title);
                  setRenamingId(item.id);
                }}
              >
                <Pencil className="size-3" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  onTogglePin?.(item.id);
                }}
              >
                {item.isPinned ? <PinOff className="size-3" /> : <Pin className="size-3" />}
                {item.isPinned ? "Unpin" : "Pin to top"}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExport(item);
                }}
              >
                <Download className="size-3" />
                Export as Markdown
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-outline-variant" />
              <DropdownMenuItem
                className="cursor-pointer hover:bg-red-500/10 text-red-400 px-2 py-1.5 text-xs rounded flex items-center gap-2"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteTarget(item.id);
                }}
              >
                <Trash2 className="size-3" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    );
  };

  return (
    <>
      <div className="w-full md:w-64 border-r border-outline-variant bg-surface flex flex-col h-full shrink-0 select-none">
        {/* Header / New Chat action */}
        <div className="p-4 pb-3 border-b border-outline-variant/60 space-y-3">
          <Button
            onClick={onNewChat}
            className="w-full justify-center gap-2 bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/80 text-on-surface hover:text-on-surface rounded-lg font-bold py-5 cursor-pointer shadow-sm"
          >
            <MessageSquarePlus className="size-4 text-primary" />
            New Chat
          </Button>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-on-surface-variant/50 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full bg-surface-container-low border-none rounded-lg pl-8 pr-3 py-2 text-xs text-on-surface placeholder:text-on-surface-variant/40 outline-none focus:ring-1 focus:ring-primary transition-all"
            />
          </div>
        </div>

        {/* History Items list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4 custom-scrollbar">
          {/* Pinned section */}
          {pinnedConversations.length > 0 && (
            <div className="space-y-1.5">
              <h5 className="text-[10px] font-bold text-primary/60 uppercase tracking-widest pl-2 flex items-center gap-1">
                <Pin className="size-2.5" />
                Pinned
              </h5>
              <div className="space-y-0.5">
                {pinnedConversations.map(renderConversationItem)}
              </div>
            </div>
          )}

          {/* Categorized sections */}
          {categories.map((cat) => {
            if (cat.items.length === 0) return null;
            return (
              <div key={cat.key} className="space-y-1.5">
                <h5 className="text-[10px] font-bold text-on-surface-variant/60 uppercase tracking-widest pl-2">
                  {cat.label}
                </h5>
                <div className="space-y-0.5">
                  {cat.items.map(renderConversationItem)}
                </div>
              </div>
            );
          })}

          {filteredConversations.length === 0 && (
            <div className="text-center py-8 text-xs text-on-surface-variant/50 font-normal select-none">
              {searchQuery ? `No results for "${searchQuery}"` : "No history recorded"}
            </div>
          )}
        </div>

        {/* Conversation count */}
        <div className="px-4 py-2.5 border-t border-outline-variant/50 text-[10px] text-on-surface-variant/40 font-mono text-center">
          {conversations.length} conversation{conversations.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        title="Delete Conversation"
        description="This conversation and all its messages will be permanently deleted. This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={async () => {
          if (deleteTarget) {
            const fakeEvent = { stopPropagation: () => {} } as React.MouseEvent;
            onDelete(deleteTarget, fakeEvent);
            toast.success("Conversation deleted");
          }
        }}
      />
    </>
  );
}
