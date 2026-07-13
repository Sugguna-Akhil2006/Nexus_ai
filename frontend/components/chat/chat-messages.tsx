"use client";

import { useRef, useEffect } from "react";
import { Bot, FileText, Image as ImageIcon, File } from "lucide-react";
import { cn } from "@/lib/utils";
import CodeBlock from "./code-block";
import { AttachedFile } from "./file-attachments";

export interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  agentName?: string;
  provider?: string;
  latencyMs?: number;
  codeBlock?: {
    filename: string;
    code: string;
    language?: string;
  };
  showVisualization?: boolean; // Renders Grover's Simulation score widgets
  attachments?: AttachedFile[];
}

interface ChatMessagesProps {
  messages: Message[];
}

export default function ChatMessages({ messages }: ChatMessagesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Automatically scroll to bottom on new message load
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
              "flex flex-col gap-2 select-text",
              isAI ? "items-start" : "items-end text-right"
            )}
          >
            {/* Header / Sender Profile */}
            <div className="flex items-center gap-2 mb-1 select-none">
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
            </div>

            {/* Bubble Contents */}
            {isAI ? (
              // AI bubble container (renders full width/spacing blocks)
              <div className="space-y-4 max-w-3xl w-full text-left">
                <p className="text-sm md:text-base text-on-surface leading-relaxed font-normal whitespace-pre-line">
                  {message.text}
                </p>

                {/* Render code block if present */}
                {message.codeBlock && (
                  <CodeBlock
                    filename={message.codeBlock.filename}
                    code={message.codeBlock.code}
                    language={message.codeBlock.language}
                  />
                )}

                {/* Render confidence widgets if set */}
                {message.showVisualization && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full pt-2">
                    {/* Confidence card */}
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

                    {/* Latent Vector graph */}
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
              // User Bubble Container
              <div className="flex flex-col items-end gap-2 max-w-[85%] text-left">
                {/* Render Text Bubble */}
                {message.text && (
                  <div className="bg-surface-container-high px-4 py-3 rounded-xl border border-outline-variant/30 text-sm md:text-base text-on-surface leading-relaxed font-normal shadow-sm">
                    {message.text}
                  </div>
                )}

                {/* Render attachments previews under user bubble */}
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
          </div>
        );
      })}

      {messages.length === 0 && (
        <div className="flex-grow flex flex-col items-center justify-center text-center p-8 select-none">
          <Bot className="size-12 text-primary opacity-30 animate-pulse mb-4" />
          <h4 className="text-lg font-semibold text-on-surface mb-1">Quantum Simulate Session</h4>
          <p className="text-sm text-on-surface-variant max-w-sm">
            Ask any question to initialize calculations, structure Qiskit code scripts, or analyze metrics.
          </p>
        </div>
      )}
    </div>
  );
}
