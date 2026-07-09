"use client";

import { useState, useRef, DragEvent } from "react";
import { Upload, Plus, FileText, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface ResumeUploadProps {
  onUploadStart: (filename: string) => Promise<void> | void;
  isAnalyzing: boolean;
  analyzingStep: string;
}

export default function ResumeUpload({
  onUploadStart,
  isAnalyzing,
  analyzingStep,
}: ResumeUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (isAnalyzing) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith(".pdf") || file.name.endsWith(".docx")) {
        await onUploadStart(file.name);
      } else {
        toast.error("Please drop a PDF or DOCX file.");
      }
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isAnalyzing) return;
    
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      await onUploadStart(file.name);
    }
  };

  const triggerFileInput = () => {
    if (isAnalyzing) return;
    fileInputRef.current?.click();
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Candidate Source
        </h3>
        <Upload className="size-4 text-on-surface-variant" />
      </div>

      {/* Drop Zone Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        className={cn(
          "flex-1 min-h-[160px] border-2 border-dashed border-outline-variant/60 hover:border-primary rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer group transition-all duration-300 select-none",
          isDragOver && "border-primary bg-primary/5",
          isAnalyzing && "cursor-default opacity-85 hover:border-outline-variant/60"
        )}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.docx"
          className="hidden"
        />

        {isAnalyzing ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="relative flex items-center justify-center">
              <Loader2 className="size-10 text-primary animate-spin" />
              <FileText className="size-4 text-primary absolute" />
            </div>
            <div className="space-y-1">
              <p className="text-xs md:text-sm font-semibold text-on-surface animate-pulse">
                ATS Neural Scanning...
              </p>
              <p className="text-[10px] md:text-xs text-on-surface-variant font-medium">
                {analyzingStep}
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Plus icon circle */}
            <div className="w-12 h-12 rounded-full bg-surface-container-highest flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-300 shadow-inner">
              <Plus className="size-5 text-primary" />
            </div>

            <p className="text-xs md:text-sm font-semibold text-on-surface mb-1 group-hover:text-primary transition-colors">
              Drop CV here or click to browse
            </p>
            <p className="text-[10px] md:text-xs text-on-surface-variant font-medium">
              PDF, DOCX up to 10MB
            </p>
          </>
        )}
      </div>
    </div>
  );
}
