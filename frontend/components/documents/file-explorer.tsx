"use client";

import { useState } from "react";
import { Folder, FolderOpen, FileText, ChevronDown, ChevronRight, FolderPlus, Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import DragDropUpload from "@/components/common/drag-drop-upload";

export interface FileItem {
  name: string;
  type: "pdf" | "docx" | "xlsx";
}

export interface FolderItem {
  id: string;
  name: string;
  files: FileItem[];
}

interface FileExplorerProps {
  activeFilename: string;
  onSelectFile: (filename: string) => void;
  folders: FolderItem[];
  onUploadSuccess?: () => void;
}

export default function FileExplorer({
  activeFilename,
  onSelectFile,
  folders,
  onUploadSuccess,
}: FileExplorerProps) {
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = { "folder-1": true, "workspace-docs": true };
    folders.forEach((f) => {
      init[f.id] = true;
    });
    return init;
  });

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [folderId]: !prev[folderId],
    }));
  };

  return (
    <section className="w-72 border-r border-outline-variant flex flex-col bg-surface-container-low overflow-hidden shrink-0 select-none">
      {/* Explorer Header */}
      <div className="p-4 border-b border-outline-variant flex items-center justify-between">
        <h2 className="text-[10px] font-bold text-on-surface uppercase tracking-wider">
          Explorer
        </h2>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-on-surface-variant hover:text-on-surface hover:bg-surface-container cursor-pointer"
            title="Create new folder"
          >
            <FolderPlus className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-on-surface-variant hover:text-on-surface hover:bg-surface-container cursor-pointer"
            title="Filter files"
          >
            <Filter className="size-4" />
          </Button>
        </div>
      </div>

      {/* Directory Hierarchy */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-4">
        {/* Upload Zone */}
        <DragDropUpload onUploadSuccess={onUploadSuccess} />

        <div className="space-y-1">
          {folders.map((folder) => {
            const isExpanded = !!expandedFolders[folder.id];
            return (
              <div key={folder.id} className="space-y-0.5">
              {/* Folder Line */}
              <div
                onClick={() => toggleFolder(folder.id)}
                className="flex items-center gap-2 px-2.5 py-2 hover:bg-surface-container rounded-lg cursor-pointer group transition-colors duration-150"
              >
                {isExpanded ? (
                  <ChevronDown className="size-3.5 text-on-surface-variant shrink-0" />
                ) : (
                  <ChevronRight className="size-3.5 text-on-surface-variant shrink-0" />
                )}
                {isExpanded ? (
                  <FolderOpen className="size-4 text-tertiary shrink-0" />
                ) : (
                  <Folder className="size-4 text-on-surface-variant/80 shrink-0" />
                )}
                <span className="text-xs font-semibold text-on-surface truncate">
                  {folder.name}
                </span>
              </div>

              {/* Sub-Files */}
              {isExpanded && (
                <div className="pl-6 space-y-0.5">
                  {folder.files.map((file) => {
                    const isActive = file.name === activeFilename;
                    return (
                      <div
                        key={file.name}
                        onClick={() => onSelectFile(file.name)}
                        className={cn(
                          "flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors duration-150",
                          isActive
                            ? "bg-primary/10 border-l-2 border-primary text-primary font-medium"
                            : "hover:bg-surface-container/60 text-on-surface-variant hover:text-on-surface"
                        )}
                      >
                        <FileText className={cn("size-3.5 shrink-0", isActive ? "text-primary" : "text-on-surface-variant/60")} />
                        <span className="text-xs truncate leading-none pt-0.5">
                          {file.name}
                        </span>
                      </div>
                    );
                  })}
                  {folder.files.length === 0 && (
                    <div className="text-[10px] text-on-surface-variant/40 italic py-1 pl-6">
                      Folder is empty
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        </div>
      </div>

      {/* Storage Capacity Gauge */}
      <div className="p-4 bg-surface-container-lowest border-t border-outline-variant">
        <div className="flex items-center gap-3">
          <div className="w-1.5 h-8 bg-primary rounded-full animate-pulse" />
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold text-on-surface leading-none">Storage Capacity</p>
            {(() => {
              const fileCount = folders.reduce((acc, f) => acc + (f.files ? f.files.length : 0), 0);
              const usedMB = (fileCount * 1.5).toFixed(1);
              const percentage = Math.min(100, Math.max(1, (fileCount * 1.5)));
              return (
                <>
                  <p className="text-[10px] text-on-surface-variant/70 leading-none mt-1.5">{usedMB} MB of 100 MB used</p>
                  <div className="w-full bg-surface-container h-1 rounded-full overflow-hidden mt-2">
                    <div className="bg-primary h-full rounded-full transition-all duration-300" style={{ width: `${percentage}%` }} />
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      </div>
    </section>
  );
}
