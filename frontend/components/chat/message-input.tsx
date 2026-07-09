"use client";

import { useRef, useEffect, useState, ChangeEvent } from "react";
import { Paperclip, ArrowUp, Sparkles, Lock, Hash, Zap, Code, FileSearch, Bot, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import FileAttachments, { AttachedFile } from "./file-attachments";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

const MAX_CHARS = 4000;

interface SlashCommand {
  command: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const SLASH_COMMANDS: SlashCommand[] = [
  { command: "/code", label: "Code", description: "Generate or review code", icon: Code },
  { command: "/analyze", label: "Analyze", description: "Analyze data or documents", icon: FileSearch },
  { command: "/summarize", label: "Summarize", description: "Summarize text or conversation", icon: Hash },
  { command: "/optimize", label: "Optimize", description: "Optimize code performance", icon: Zap },
  { command: "/agent", label: "Agent", description: "Invoke autonomous agent", icon: Bot },
];

const AI_MODELS = [
  { id: "nexus-4-turbo", name: "Nexus-4 Turbo", description: "Fastest, best for chat", badge: "Default" },
  { id: "nexus-4-pro", name: "Nexus-4 Pro", description: "Best quality reasoning", badge: "Pro" },
  { id: "nexus-4-vision", name: "Nexus-4 Vision", description: "Image + text analysis", badge: "Vision" },
];

interface MessageInputProps {
  text: string;
  onChangeText: (text: string) => void;
  files: AttachedFile[];
  onAddFile: (file: AttachedFile) => void;
  onRemoveFile: (id: string) => void;
  onSend: () => void;
}

export default function MessageInput({
  text,
  onChangeText,
  files,
  onAddFile,
  onRemoveFile,
  onSend,
}: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [selectedModel, setSelectedModel] = useState(AI_MODELS[0]);

  // Auto-grow textarea height
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [text]);

  // Detect slash command trigger
  useEffect(() => {
    if (text === "/") {
      setShowSlashMenu(true);
    } else if (!text.startsWith("/") || text.includes(" ")) {
      setShowSlashMenu(false);
    }
  }, [text]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (showSlashMenu) {
        // Select first matching command
        const filtered = SLASH_COMMANDS.filter(c => c.command.startsWith(text));
        if (filtered.length > 0) {
          handleSlashSelect(filtered[0]);
          return;
        }
      }
      onSend();
    }
    if (e.key === "Escape") {
      setShowSlashMenu(false);
    }
  };

  const handleSlashSelect = (cmd: SlashCommand) => {
    onChangeText(cmd.command + " ");
    setShowSlashMenu(false);
    textareaRef.current?.focus();
  };

  const triggerFileBrowser = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    const file = fileList[0];
    
    const sizeInKB = file.size / 1024;
    const sizeStr = sizeInKB > 1024 
      ? `${(sizeInKB / 1024).toFixed(1)} MB` 
      : `${sizeInKB.toFixed(1)} KB`;

    let mappedType = "file";
    if (file.type.startsWith("image/")) mappedType = "image";
    else if (file.type.includes("pdf") || file.type.includes("word") || file.type.includes("text")) {
      mappedType = "document";
    }

    onAddFile({
      id: `file-${Date.now()}`,
      name: file.name,
      size: sizeStr,
      type: mappedType,
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const charCount = text.length;
  const isOverLimit = charCount > MAX_CHARS;
  const charPercent = Math.min((charCount / MAX_CHARS) * 100, 100);

  // Filter slash commands based on current text
  const filteredSlashCommands = text.startsWith("/")
    ? SLASH_COMMANDS.filter(c => c.command.startsWith(text.split(" ")[0]))
    : SLASH_COMMANDS;

  return (
    <footer className="p-4 md:p-6 pt-0 w-full max-w-4xl mx-auto z-40 bg-background/80 backdrop-blur-sm select-none">
      
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept="image/*,application/pdf,text/*,.py,.js,.json"
      />

      <div className="relative border border-outline-variant rounded-lg bg-surface-container-low overflow-visible focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all shadow-sm">
        
        {/* Slash Command Dropdown */}
        {showSlashMenu && (
          <div className="absolute bottom-full left-0 right-0 mb-2 bg-surface/95 backdrop-blur-md border border-outline-variant rounded-xl shadow-2xl z-50 p-2 max-h-[260px] overflow-y-auto">
            <div className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant/50 px-3 py-1.5">
              Slash Commands
            </div>
            {filteredSlashCommands.map((cmd) => (
              <button
                key={cmd.command}
                onClick={() => handleSlashSelect(cmd)}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer hover:bg-primary/10 hover:text-primary transition-all text-left bg-transparent border-none"
              >
                <div className="w-7 h-7 rounded-md bg-surface-container flex items-center justify-center shrink-0">
                  <cmd.icon className="size-3.5 text-on-surface-variant" />
                </div>
                <div>
                  <span className="text-xs font-semibold text-on-surface block">{cmd.command}</span>
                  <span className="text-[10px] text-on-surface-variant/60">{cmd.description}</span>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Attachment files listed inside the text area frame */}
        <FileAttachments files={files} onRemove={onRemoveFile} />

        <div className="relative flex items-end">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => onChangeText(e.target.value)}
            onKeyDown={handleKeyPress}
            rows={1}
            placeholder="Ask anything... (Type / for commands)"
            className="w-full bg-transparent border-none outline-none py-4 pl-4 pr-28 text-sm md:text-base text-on-surface placeholder:text-on-surface-variant/40 resize-none max-h-48 scrollbar-thin leading-relaxed"
            style={{ height: "auto" }}
          />

          {/* Action Button cluster */}
          <div className="absolute right-3 bottom-3 flex items-center gap-1.5 z-10">
            <Button
              variant="ghost"
              size="icon"
              onClick={triggerFileBrowser}
              className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-surface-container-highest text-on-surface-variant transition-all cursor-pointer"
              title="Attach files"
            >
              <Paperclip className="size-4.5" />
            </Button>
            <Button
              onClick={onSend}
              disabled={(!text.trim() && files.length === 0) || isOverLimit}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-all cursor-pointer shadow-md shadow-primary/5 border-none"
              title="Send message"
            >
              <ArrowUp className="size-4.5" />
            </Button>
          </div>
        </div>

        {/* Character count bar */}
        {charCount > 0 && (
          <div className="px-4 pb-2 flex items-center justify-between">
            <div className="flex-1 h-0.5 bg-surface-container-highest rounded-full max-w-[120px] overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-300",
                  isOverLimit ? "bg-red-500" : charPercent > 80 ? "bg-amber-400" : "bg-primary/50"
                )}
                style={{ width: `${charPercent}%` }}
              />
            </div>
            <span className={cn(
              "text-[10px] font-mono ml-2",
              isOverLimit ? "text-red-400 font-bold" : "text-on-surface-variant/40"
            )}>
              {charCount.toLocaleString()}/{MAX_CHARS.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Model descriptors + Model Selector */}
      <div className="flex justify-center mt-2.5 gap-6 text-[10px] md:text-xs font-medium text-on-surface-variant/50 select-none">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-1 cursor-pointer hover:text-primary transition-colors bg-transparent border-none">
              <Sparkles className="size-3 text-primary/70" />
              <span>AI Model: {selectedModel.name}</span>
              <ChevronDown className="size-2.5 ml-0.5" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="center" className="w-56 bg-surface border border-outline-variant p-1.5 shadow-lg text-on-surface z-50">
            {AI_MODELS.map((model) => (
              <DropdownMenuItem
                key={model.id}
                className={cn(
                  "cursor-pointer hover:bg-surface-container-high px-3 py-2 text-xs rounded flex items-center justify-between",
                  selectedModel.id === model.id && "bg-primary/5 text-primary"
                )}
                onClick={() => setSelectedModel(model)}
              >
                <div>
                  <span className="font-semibold block">{model.name}</span>
                  <span className="text-[10px] text-on-surface-variant/60">{model.description}</span>
                </div>
                <span className={cn(
                  "text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border",
                  model.badge === "Default" ? "bg-primary/10 text-primary border-primary/20" :
                  model.badge === "Pro" ? "bg-secondary/10 text-secondary border-secondary/20" :
                  "bg-amber-500/10 text-amber-400 border-amber-500/20"
                )}>
                  {model.badge}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="flex items-center gap-1">
          <Lock className="size-3 text-primary/70" />
          <span>Enterprise Secure</span>
        </div>
      </div>
    </footer>
  );
}
