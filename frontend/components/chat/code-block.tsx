"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CodeBlockProps {
  filename: string;
  code: string;
  language?: string;
}

export default function CodeBlock({ filename, code, language = "python" }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy code: ", err);
    }
  };

  return (
    <div className="rounded-lg overflow-hidden border border-outline-variant bg-surface-container-lowest font-mono text-xs md:text-sm shadow-sm select-text">
      {/* File Header */}
      <div className="bg-surface-container flex items-center justify-between px-4 py-2 border-b border-outline-variant select-none">
        <span className="text-on-surface-variant font-medium text-xs">
          {filename}
        </span>
        <Button
          variant="ghost"
          size="xs"
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-green-400" />
              <span className="text-xs font-semibold text-green-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="size-3.5" />
              <span className="text-xs">Copy code</span>
            </>
          )}
        </Button>
      </div>

      {/* Code Text Area */}
      <div className="p-4 text-primary-fixed-dim leading-6 overflow-x-auto whitespace-pre scrollbar-thin select-all">
        <code className={language ? `language-${language}` : undefined}>{code}</code>
      </div>
    </div>
  );
}
