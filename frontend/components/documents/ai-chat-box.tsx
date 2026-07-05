"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Paperclip, Mic, Send } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AIChatBoxProps {
  onSubmit: (prompt: string) => void;
  placeholder?: string;
  tokenCount?: string;
}

export default function AIChatBox({
  onSubmit,
  placeholder = "e.g. Compare expenses with Q2...",
  tokenCount = "4,102/32K",
}: AIChatBoxProps) {
  const [query, setQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!query.trim()) return;
    onSubmit(query.trim());
    setQuery("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-3.5 select-none">
      <h3 className="text-[10px] font-bold text-on-surface uppercase tracking-wider pl-0.5">
        Ask AI about this file
      </h3>
      
      <div className="bg-surface-container-low rounded-lg border border-outline-variant p-3 focus-within:border-primary/80 focus-within:ring-1 focus-within:ring-primary/80 transition-all shadow-sm">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full bg-transparent border-none outline-none focus:ring-0 text-xs md:text-sm text-on-surface placeholder:text-on-surface-variant/40 resize-none h-16 md:h-20 leading-relaxed font-sans"
        />
        
        <div className="flex justify-between items-center mt-2.5">
          {/* Add-on actions */}
          <div className="flex gap-2 text-on-surface-variant">
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-on-surface-variant hover:text-primary rounded hover:bg-surface-container transition-colors cursor-pointer"
              title="Attach context file"
            >
              <Paperclip className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-on-surface-variant hover:text-primary rounded hover:bg-surface-container transition-colors cursor-pointer"
              title="Voice transcription"
            >
              <Mic className="size-4" />
            </Button>
          </div>

          {/* Send */}
          <Button
            onClick={handleSend}
            disabled={!query.trim()}
            className="bg-primary text-primary-foreground w-8 h-8 rounded-md flex items-center justify-center hover:opacity-90 disabled:opacity-55 transition-all shadow-md shadow-primary/10 border-none cursor-pointer"
            title="Send inquiry"
          >
            <Send className="size-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
