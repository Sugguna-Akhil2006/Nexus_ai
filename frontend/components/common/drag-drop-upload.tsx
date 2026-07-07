"use client";

import { useState, DragEvent } from "react";
import { UploadCloud, FileText, CheckCircle, AlertCircle, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface UploadedFile {
  name: string;
  size: number;
  progress: number;
  status: "uploading" | "completed" | "failed";
}

export default function DragDropUpload() {
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadedFile[]>([]);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const processFiles = (files: FileList) => {
    const list = Array.from(files).map((f) => {
      const item: UploadedFile = {
        name: f.name,
        size: f.size,
        progress: 0,
        status: "uploading"
      };

      // Simulate file upload progress
      const interval = setInterval(() => {
        setUploadingFiles((prev) =>
          prev.map((uf) => {
            if (uf.name === f.name) {
              const nextProgress = uf.progress + 20;
              if (nextProgress >= 100) {
                clearInterval(interval);
                toast.success(`File uploaded successfully: ${f.name}`);
                return { ...uf, progress: 100, status: "completed" };
              }
              return { ...uf, progress: nextProgress };
            }
            return uf;
          })
        );
      }, 300);

      return item;
    });

    setUploadingFiles((prev) => [...prev, ...list]);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const removeFile = (name: string) => {
    setUploadingFiles((prev) => prev.filter((f) => f.name !== name));
    toast.success(`Removed file reference: ${name}`);
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-3 transition-colors select-none ${
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-outline-variant hover:border-primary/50 bg-surface-container-low"
        }`}
      >
        <UploadCloud className="size-8 text-on-surface-variant/80" />
        <div className="text-center">
          <p className="text-sm font-semibold text-on-surface">
            Drag and drop files here or click to upload
          </p>
          <p className="text-xs text-on-surface-variant mt-1">
            Supports PDF, DOCX, XLSX (Max 50MB)
          </p>
        </div>
        <input
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
          id="file-dropzone-input"
        />
        <label htmlFor="file-dropzone-input">
          <Button
            variant="outline"
            className="cursor-pointer text-xs font-bold px-4 py-2 border-outline-variant bg-surface-container-lowest"
            asChild
          >
            <span>Select Files</span>
          </Button>
        </label>
      </div>

      {/* Uploading Files Progress */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[10px] font-bold text-on-surface uppercase tracking-wider">
            Uploading Files
          </h4>
          <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
            {uploadingFiles.map((file) => (
              <div
                key={file.name}
                className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant rounded-lg"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <FileText className="size-4 text-on-surface-variant shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-on-surface truncate leading-none">
                      {file.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <div className="flex-1 bg-surface-container h-1 rounded-full overflow-hidden">
                        <div
                          className="bg-primary h-full transition-all duration-300"
                          style={{ width: `${file.progress}%` }}
                        />
                      </div>
                      <span className="font-mono text-[9px] text-on-surface-variant font-semibold">
                        {file.progress}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 ml-3">
                  {file.status === "completed" && (
                    <CheckCircle className="size-4 text-emerald-400" />
                  )}
                  {file.status === "failed" && (
                    <AlertCircle className="size-4 text-rose-500" />
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(file.name)}
                    className="size-7 hover:bg-surface-container hover:text-rose-500 text-on-surface-variant/70 cursor-pointer"
                  >
                    <Trash2 className="size-4.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
