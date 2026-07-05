"use client";

import { File, FileText, Image as ImageIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface AttachedFile {
  id: string;
  name: string;
  size: string;
  type: string; // e.g. "image", "document", "code"
}

interface FileAttachmentsProps {
  files: AttachedFile[];
  onRemove: (id: string) => void;
}

export default function FileAttachments({ files, onRemove }: FileAttachmentsProps) {
  if (files.length === 0) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case "image":
        return ImageIcon;
      case "document":
        return FileText;
      default:
        return File;
    }
  };

  return (
    <div className="flex flex-wrap gap-2.5 px-4 py-2 border-t border-outline-variant/20 bg-surface-container-lowest/60 select-none">
      {files.map((file) => {
        const FileIcon = getIcon(file.type);
        return (
          <div
            key={file.id}
            className="flex items-center gap-2 pl-2 pr-1 py-1 rounded-lg bg-surface-container border border-outline-variant/60 text-on-surface shadow-sm group hover:border-primary/30 transition-all duration-200"
          >
            <div className="flex items-center justify-center p-1.5 rounded-md bg-primary/10 text-primary">
              <FileIcon className="size-4" />
            </div>
            
            <div className="flex flex-col max-w-[120px] sm:max-w-[180px]">
              <span className="text-xs font-semibold truncate leading-none">
                {file.name}
              </span>
              <span className="text-[10px] text-on-surface-variant/70 leading-none mt-1">
                {file.size}
              </span>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => onRemove(file.id)}
              className="size-6 text-on-surface-variant hover:text-destructive hover:bg-destructive/10 rounded-md cursor-pointer ml-1"
            >
              <X className="size-3.5" />
              <span className="sr-only">Remove attachment</span>
            </Button>
          </div>
        );
      })}
    </div>
  );
}
