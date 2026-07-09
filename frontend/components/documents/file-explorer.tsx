"use client";

import { useState } from "react";
import { Folder, FolderOpen, FileText, ChevronDown, ChevronRight, FolderPlus, Filter, MoreVertical, Pencil, Trash2, Copy, Download, Eye, FileSpreadsheet, FileImage } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import DragDropUpload from "@/components/common/drag-drop-upload";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

export interface FileItem {
  name: string;
  type: "pdf" | "docx" | "xlsx";
  size?: string;
  modifiedAt?: string;
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
}

const FILE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  pdf: FileText,
  docx: FileText,
  xlsx: FileSpreadsheet,
};

const FILE_SIZES: Record<string, string> = {
  "Q3_Financial_Review.pdf": "2.4 MB",
  "Stakeholder_Analysis.docx": "842 KB",
  "Technical_Specs_v2.pdf": "1.8 MB",
  "NDA_Agreement_Draft.pdf": "534 KB",
  "Compliance_Policy.xlsx": "1.1 MB",
  "Model_Training_Logs.xlsx": "4.7 MB",
};

const FILE_DATES: Record<string, string> = {
  "Q3_Financial_Review.pdf": "Jul 5",
  "Stakeholder_Analysis.docx": "Jul 3",
  "Technical_Specs_v2.pdf": "Jul 1",
  "NDA_Agreement_Draft.pdf": "Jun 28",
  "Compliance_Policy.xlsx": "Jun 25",
  "Model_Training_Logs.xlsx": "Jun 20",
};

const TYPE_COLORS: Record<string, string> = {
  pdf: "text-red-400 bg-red-500/10 border-red-500/20",
  docx: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  xlsx: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

export default function FileExplorer({
  activeFilename,
  onSelectFile,
  folders,
}: FileExplorerProps) {
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({
    "folder-1": true,
  });
  const [filterType, setFilterType] = useState<string | null>(null);

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [folderId]: !prev[folderId],
    }));
  };

  const totalFiles = folders.reduce((sum, f) => sum + f.files.length, 0);

  return (
    <section className="w-72 border-r border-outline-variant flex flex-col bg-surface-container-low overflow-hidden shrink-0 select-none">
      {/* Explorer Header */}
      <div className="p-4 border-b border-outline-variant flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-[10px] font-bold text-on-surface uppercase tracking-wider">
            Explorer
          </h2>
          <span className="text-[9px] font-mono text-on-surface-variant/40 bg-surface-container px-1.5 py-0.5 rounded">
            {totalFiles} files
          </span>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-7 text-on-surface-variant hover:text-on-surface hover:bg-surface-container cursor-pointer"
            title="Create new folder"
            onClick={() => toast.success("New folder created: Untitled")}
          >
            <FolderPlus className="size-4" />
          </Button>
          
          {/* Filter dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "size-7 text-on-surface-variant hover:text-on-surface hover:bg-surface-container cursor-pointer",
                  filterType && "text-primary"
                )}
                title="Filter files"
              >
                <Filter className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => setFilterType(null)}>
                All Files
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => setFilterType("pdf")}>
                PDF Only
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => setFilterType("docx")}>
                DOCX Only
              </DropdownMenuItem>
              <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded" onClick={() => setFilterType("xlsx")}>
                XLSX Only
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Directory Hierarchy */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-4">
        {/* Upload Zone */}
        <DragDropUpload />

        <div className="space-y-1">
          {folders.map((folder) => {
            const isExpanded = !!expandedFolders[folder.id];
            const filteredFiles = filterType ? folder.files.filter(f => f.type === filterType) : folder.files;
            
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
                <span className="text-xs font-semibold text-on-surface truncate flex-1">
                  {folder.name}
                </span>
                <span className="text-[9px] text-on-surface-variant/40 font-mono shrink-0">
                  {filteredFiles.length}
                </span>
              </div>

              {/* Sub-Files */}
              {isExpanded && (
                <div className="pl-6 space-y-0.5">
                  {filteredFiles.map((file) => {
                    const isActive = file.name === activeFilename;
                    const FileIcon = FILE_ICONS[file.type] || FileText;
                    const fileSize = FILE_SIZES[file.name] || "—";
                    const fileDate = FILE_DATES[file.name] || "—";

                    return (
                      <div
                        key={file.name}
                        className={cn(
                          "flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors duration-150 group/file relative",
                          isActive
                            ? "bg-primary/10 border-l-2 border-primary text-primary font-medium"
                            : "hover:bg-surface-container/60 text-on-surface-variant hover:text-on-surface"
                        )}
                        onClick={() => onSelectFile(file.name)}
                      >
                        <FileIcon className={cn("size-3.5 shrink-0", isActive ? "text-primary" : "text-on-surface-variant/60")} />
                        <div className="flex-1 min-w-0">
                          <span className="text-xs truncate leading-none block">
                            {file.name}
                          </span>
                          <span className="text-[9px] text-on-surface-variant/40 font-mono mt-0.5 block">
                            {fileSize} · {fileDate}
                          </span>
                        </div>
                        
                        {/* Type badge */}
                        <span className={cn(
                          "text-[8px] font-bold uppercase px-1 py-0.5 rounded border shrink-0 hidden group-hover/file:inline-block",
                          TYPE_COLORS[file.type] || "text-on-surface-variant/40 bg-surface-container border-outline-variant"
                        )}>
                          {file.type}
                        </span>

                        {/* Context menu */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button
                              onClick={(e) => e.stopPropagation()}
                              className="opacity-0 group-hover/file:opacity-100 p-1 rounded hover:bg-surface-container-highest text-on-surface-variant/60 hover:text-on-surface transition-all cursor-pointer bg-transparent border-none shrink-0"
                            >
                              <MoreVertical className="size-3" />
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-44 bg-surface border border-outline-variant p-1 shadow-lg text-on-surface z-50">
                            <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => onSelectFile(file.name)}>
                              <Eye className="size-3" /> Preview
                            </DropdownMenuItem>
                            <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.success(`Downloading ${file.name}`)}>
                              <Download className="size-3" /> Download
                            </DropdownMenuItem>
                            <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.success(`Link copied for ${file.name}`)}>
                              <Copy className="size-3" /> Copy link
                            </DropdownMenuItem>
                            <DropdownMenuItem className="cursor-pointer hover:bg-surface-container-high px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.info("Rename functionality placeholder")}>
                              <Pencil className="size-3" /> Rename
                            </DropdownMenuItem>
                            <DropdownMenuSeparator className="bg-outline-variant" />
                            <DropdownMenuItem className="cursor-pointer hover:bg-red-500/10 text-red-400 px-2 py-1.5 text-xs rounded flex items-center gap-2" onClick={() => toast.success(`Deleted: ${file.name}`)}>
                              <Trash2 className="size-3" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    );
                  })}
                  {filteredFiles.length === 0 && (
                    <div className="text-[10px] text-on-surface-variant/40 italic py-1 pl-6">
                      {filterType ? `No ${filterType.toUpperCase()} files` : "Folder is empty"}
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
            <p className="text-[10px] text-on-surface-variant/70 leading-none mt-1.5">84.2 GB of 100 GB used</p>
            <div className="w-full bg-surface-container h-1 rounded-full overflow-hidden mt-2">
              <div className="bg-primary h-full rounded-full" style={{ width: "84.2%" }} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
