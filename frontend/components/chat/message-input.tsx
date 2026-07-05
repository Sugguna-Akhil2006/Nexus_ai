"use client";

import { useRef, useEffect, ChangeEvent } from "react";
import { Paperclip, ArrowUp, Sparkles, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileAttachments, { AttachedFile } from "./file-attachments";

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

  // Auto-grow textarea height on text length adjustments
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [text]);

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
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
    
    // Convert bytes to human readable format
    const sizeInKB = file.size / 1024;
    const sizeStr = sizeInKB > 1024 
      ? `${(sizeInKB / 1024).toFixed(1)} MB` 
      : `${sizeInKB.toFixed(1)} KB`;

    // Map file types
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

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

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

      <div className="relative border border-outline-variant rounded-lg bg-surface-container-low overflow-hidden focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all shadow-sm">
        {/* Attachment files listed inside the text area frame */}
        <FileAttachments files={files} onRemove={onRemoveFile} />

        <div className="relative flex items-end">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => onChangeText(e.target.value)}
            onKeyDown={handleKeyPress}
            rows={1}
            placeholder="Ask anything..."
            className="w-full bg-transparent border-none outline-none py-4 pl-4 pr-24 text-sm md:text-base text-on-surface placeholder:text-on-surface-variant/40 resize-none max-h-48 scrollbar-thin leading-relaxed"
            style={{ height: "auto" }}
          />

          {/* Action Button cluster in right corner */}
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
              disabled={!text.trim() && files.length === 0}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-all cursor-pointer shadow-md shadow-primary/5 border-none"
              title="Send message"
            >
              <ArrowUp className="size-4.5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Model descriptors */}
      <div className="flex justify-center mt-2.5 gap-6 text-[10px] md:text-xs font-medium text-on-surface-variant/50 select-none">
        <div className="flex items-center gap-1">
          <Sparkles className="size-3 text-primary/70" />
          <span>AI Model: Nexus-4 Turbo</span>
        </div>
        <div className="flex items-center gap-1">
          <Lock className="size-3 text-primary/70" />
          <span>Enterprise Secure</span>
        </div>
      </div>
    </footer>
  );
}
