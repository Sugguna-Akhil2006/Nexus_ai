"use client";

import { Sparkles } from "lucide-react";

interface SuggestedPromptsProps {
  prompts: string[];
  onClick: (prompt: string) => void;
}

export default function SuggestedPrompts({ prompts, onClick }: SuggestedPromptsProps) {
  if (prompts.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 px-1 select-none">
      <div className="flex items-center gap-1.5 text-[10px] uppercase font-semibold text-primary tracking-widest pl-1 mb-1">
        <Sparkles className="size-3 text-primary" />
        Suggested Actions
      </div>
      <div className="flex flex-wrap gap-2.5">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onClick(prompt)}
            className="text-left text-xs font-medium text-on-surface-variant hover:text-primary px-3.5 py-2.5 rounded-lg border border-outline-variant/60 hover:border-primary/30 bg-surface-container-low hover:bg-primary/5 active:scale-[0.98] transition-all cursor-pointer shadow-sm hover:shadow-primary/5"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
