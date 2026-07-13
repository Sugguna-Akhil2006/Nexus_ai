"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Bot, User, FileText, Image as ImageIcon, File, Copy, Check, RefreshCw, Pencil, MoreHorizontal, ThumbsUp, ThumbsDown } from "lucide-react";
import { cn } from "@/lib/utils";
import CodeBlock from "./code-block";
import { AttachedFile } from "./file-attachments";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";

export interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  agentName?: string;
  provider?: string;
  latencyMs?: number;
  timestamp?: string;
  codeBlock?: {
    filename: string;
    code: string;
    language?: string;
  };
  showVisualization?: boolean;
  attachments?: AttachedFile[];
  isStreaming?: boolean;
}

interface ChatMessagesProps {
  messages: Message[];
  onRegenerate?: (messageId: string) => void;
  onEditUserMessage?: (messageId: string, newText: string) => void;
}

function MessageActions({ message, onRegenerate, onEditUserMessage }: {
  message: Message;
  onRegenerate?: (messageId: string) => void;
  onEditUserMessage?: (messageId: string, newText: string) => void;
}) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.text);
  const editRef = useRef<HTMLTextAreaElement>(null);
  const isAI = message.sender === "ai";

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopiedId(message.id);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error("Failed to copy");
    }
  }, [message.id, message.text]);

  const handleEditSubmit = useCallback(() => {
    if (editText.trim() && editText !== message.text) {
      onEditUserMessage?.(message.id, editText);
    }
    setIsEditing(false);
  }, [editText, message.id, message.text, onEditUserMessage]);

  useEffect(() => {
    if (isEditing && editRef.current) {
      editRef.current.focus();
      editRef.current.selectionStart = editRef.current.value.length;
    }
  }, [isEditing]);

  if (message.isStreaming) return null;

  if (isEditing && !isAI) {
    return (
      <div className="w-full max-w-[85%] ml-auto mt-1">
        <textarea
          ref={editRef}
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleEditSubmit(); }
            if (e.key === "Escape") setIsEditing(false);
          }}
          className="w-full bg-surface-container-low border border-primary/30 rounded-lg px-3 py-2 text-sm text-on-surface resize-none outline-none focus:ring-1 focus:ring-primary"
          rows={2}
        />
        <div className="flex justify-end gap-2 mt-1.5">
          <button onClick={() => setIsEditing(false)} className="text-[10px] font-semibold text-on-surface-variant hover:text-on-surface cursor-pointer bg-transparent border-none">Cancel</button>
          <button onClick={handleEditSubmit} className="text-[10px] font-semibold text-primary hover:text-primary/80 cursor-pointer bg-transparent border-none">Save & Resend</button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "flex items-center gap-1 mt-1 opacity-0 group-hover/msg:opacity-100 transition-opacity duration-150",
      isAI ? "justify-start" : "justify-end"
    )}>
      {/* Copy */}
      <button
        onClick={handleCopy}
        className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-on-surface transition-colors cursor-pointer bg-transparent border-none"
        title="Copy message"
      >
        {copiedId === message.id ? <Check className="size-3 text-green-400" /> : <Copy className="size-3" />}
      </button>

      {/* AI-specific: Regenerate, Thumbs Up/Down */}
      {isAI && (
        <>
          <button
            onClick={() => onRegenerate?.(message.id)}
            className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-on-surface transition-colors cursor-pointer bg-transparent border-none"
            title="Regenerate response"
          >
            <RefreshCw className="size-3" />
          </button>
          <button
            onClick={() => toast.success("Feedback recorded: positive")}
            className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-green-400 transition-colors cursor-pointer bg-transparent border-none"
            title="Good response"
          >
            <ThumbsUp className="size-3" />
          </button>
          <button
            onClick={() => toast.success("Feedback recorded: needs improvement")}
            className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-amber-400 transition-colors cursor-pointer bg-transparent border-none"
            title="Poor response"
          >
            <ThumbsDown className="size-3" />
          </button>
        </>
      )}

      {/* User-specific: Edit */}
      {!isAI && onEditUserMessage && (
        <button
          onClick={() => { setEditText(message.text); setIsEditing(true); }}
          className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-on-surface transition-colors cursor-pointer bg-transparent border-none"
          title="Edit message"
        >
          <Pencil className="size-3" />
        </button>
      )}

      {/* More actions */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant/60 hover:text-on-surface transition-colors cursor-pointer bg-transparent border-none">
            <MoreHorizontal className="size-3" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align={isAI ? "start" : "end"} className="w-40 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
          <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={handleCopy}>
            Copy text
          </DropdownMenuItem>
          {isAI && (
            <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => onRegenerate?.(message.id)}>
              Regenerate
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

/** Streaming cursor dot animation */
function StreamingCursor() {
  return (
    <span className="inline-block w-2 h-4 bg-primary/80 rounded-sm animate-pulse ml-0.5 align-middle" />
  );
}

export default function ChatMessages({ messages, onRegenerate, onEditUserMessage }: ChatMessagesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const getAttachmentIcon = (type: string) => {
    if (type === "image") return ImageIcon;
    if (type === "document") return FileText;
    return File;
  };

  const formatTimestamp = (ts?: string) => {
    if (!ts) return null;
    return ts;
  };

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto px-6 py-8 custom-scrollbar flex flex-col gap-8 max-w-4xl mx-auto w-full"
    >
      {messages.map((message) => {
        const isAI = message.sender === "ai";
        
        return (
          <div
            key={message.id}
            className={cn(
              "flex flex-col gap-1 select-text group/msg",
              isAI ? "items-start" : "items-end text-right"
            )}
          >
            {/* Header / Sender Profile + Timestamp */}
            <div className={cn("flex items-center gap-2 mb-0.5 select-none", isAI ? "" : "flex-row-reverse")}>
              {isAI ? (
                <>
                  <div className="w-6 h-6 bg-primary/20 text-primary rounded flex items-center justify-center shrink-0">
                    <Bot className="size-4" />
                  </div>
                  <span className="text-[10px] font-bold text-primary uppercase tracking-wider font-sans mt-0.5">
                    {message.agentName || "Nexus AI"}
                  </span>
                  {message.provider && (
                    <span className="text-[10px] text-on-surface-variant font-mono">
                      {message.provider}{message.latencyMs ? ` / ${message.latencyMs}ms` : ""}
                    </span>
                  )}
                </>
              ) : (
                <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider font-sans mt-0.5">
                  You
                </span>
              )}
              {message.timestamp && (
                <span className="text-[9px] text-on-surface-variant/40 font-mono">
                  {formatTimestamp(message.timestamp)}
                </span>
              )}
            </div>

            {/* Bubble Contents */}
            {isAI ? (
              <div className="space-y-4 max-w-3xl w-full text-left">
                <p className="text-sm md:text-base text-on-surface leading-relaxed font-normal whitespace-pre-line">
                  {message.text}
                  {message.isStreaming && <StreamingCursor />}
                </p>

                {message.codeBlock && (
                  <CodeBlock
                    filename={message.codeBlock.filename}
                    code={message.codeBlock.code}
                    language={message.codeBlock.language}
                  />
                )}

                {message.showVisualization && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full pt-2">
                    <div className="p-4 rounded-lg border border-outline-variant bg-surface-container-low flex flex-col gap-2 shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                        Confidence Score
                      </span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-primary">99.4%</span>
                        <span className="text-[10px] text-green-400 font-semibold uppercase tracking-wider bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/20">
                          Optimal
                        </span>
                      </div>
                      <div className="w-full bg-surface-container-highest h-1 rounded-full overflow-hidden mt-1 select-none">
                        <div className="bg-primary h-full rounded-full" style={{ width: "99.4%" }} />
                      </div>
                    </div>

                    <div className="p-4 rounded-lg border border-outline-variant bg-surface-container-low flex flex-col gap-2 shadow-sm">
                      <span className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                        Latent Vectors
                      </span>
                      <div className="flex gap-1.5 h-10 items-end mt-1 select-none">
                        <div className="flex-1 bg-primary/20 h-full rounded-sm" />
                        <div className="flex-1 bg-primary/40 h-[75%] rounded-sm" />
                        <div className="flex-1 bg-primary/60 h-[50%] rounded-sm" />
                        <div className="flex-1 bg-primary h-full rounded-sm" />
                        <div className="flex-1 bg-primary/30 h-[25%] rounded-sm" />
                        <div className="flex-1 bg-primary/50 h-[75%] rounded-sm" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-end gap-2 max-w-[85%] text-left">
                {message.text && (
                  <div className="bg-surface-container-high px-4 py-3 rounded-xl border border-outline-variant/30 text-sm md:text-base text-on-surface leading-relaxed font-normal shadow-sm">
                    {message.text}
                  </div>
                )}

                {message.attachments && message.attachments.length > 0 && (
                  <div className="flex flex-col gap-1.5 mt-1 select-none">
                    {message.attachments.map((file) => {
                      const FileIcon = getAttachmentIcon(file.type);
                      return (
                        <div
                          key={file.id}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-container border border-outline-variant/50 text-xs text-on-surface max-w-[240px]"
                        >
                          <FileIcon className="size-4 text-primary shrink-0" />
                          <span className="truncate flex-1 font-medium">{file.name}</span>
                          <span className="text-[9px] text-on-surface-variant/70 shrink-0">{file.size}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Message Actions (Copy/Regenerate/Edit/Feedback) */}
            <MessageActions
              message={message}
              onRegenerate={onRegenerate}
              onEditUserMessage={onEditUserMessage}
            />
          </div>
        );
      })}

      {messages.length === 0 && (
        <div className="flex-grow flex flex-col items-center justify-center text-center p-8 select-none">
          <Bot className="size-12 text-primary opacity-30 animate-pulse mb-4" />
          <h4 className="text-lg font-semibold text-on-surface mb-1">Nexus AI Session</h4>
          <p className="text-sm text-on-surface-variant max-w-sm">
            Ask any question to initialize calculations, structure code scripts, or analyze metrics.
          </p>
        </div>
      )}
    </div>
  );
}
