"use client";

import { Bot, BarChart2, Users, FileText, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface PDFViewerProps {
  filename: string;
  zoom: number;
}

export default function PDFViewer({ filename, zoom }: PDFViewerProps) {
  const scale = zoom / 100;

  // Render different page layout contents depending on the selected file
  const renderPDFContent = () => {
    switch (filename) {
      case "Stakeholder_Analysis.docx":
        return (
          <div className="space-y-6">
            <div className="flex justify-between border-b border-zinc-200 pb-4">
              <div className="font-bold text-base md:text-lg text-zinc-800">Stakeholder Map & Analysis</div>
              <div className="text-xs text-zinc-400 font-mono">Page 1 of 12</div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="space-y-4">
                <div className="h-4 w-4/5 bg-zinc-100 rounded" />
                <div className="h-4 w-full bg-zinc-100 rounded" />
                <div className="h-4 w-11/12 bg-zinc-100 rounded" />
                <div className="h-32 w-full bg-zinc-50 border border-zinc-100 flex flex-col items-center justify-center rounded-lg gap-2 text-zinc-400">
                  <Users className="size-8 text-zinc-300" />
                  <span className="text-xs font-medium">Influence Matrix</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="h-4 w-full bg-zinc-100 rounded" />
                <div className="h-4 w-3/4 bg-zinc-100 rounded" />
                <div className="p-3 bg-zinc-50 border border-zinc-100 rounded-lg space-y-2">
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-4/5 bg-zinc-200 rounded" />
                </div>
              </div>
            </div>

            {/* AI Highlights & Context Overlays */}
            <div className="absolute top-[280px] left-12 w-64 h-6 bg-primary/20 border-l-4 border-primary pointer-events-none" />
            <div className="absolute top-[305px] left-12 group z-30">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-white cursor-pointer shadow-lg animate-pulse hover:scale-110 transition-transform duration-200">
                <Bot className="size-3.5" />
              </div>
              <div className="hidden group-hover:block absolute left-8 top-0 w-64 bg-surface-container-highest text-on-surface p-3 rounded-lg border border-outline-variant shadow-xl text-xs leading-relaxed">
                <span className="font-bold block mb-1 text-primary">AI Context Insight</span>
                Key stakeholder sentiment is currently flagged as neutral-negative. Recommendation is to prioritize Q4 communication drafts.
              </div>
            </div>
          </div>
        );

      case "Technical_Specs_v2.pdf":
        return (
          <div className="space-y-6">
            <div className="flex justify-between border-b border-zinc-200 pb-4">
              <div className="font-bold text-base md:text-lg text-zinc-800">Qiskit Simulation Engine Specifications</div>
              <div className="text-xs text-zinc-400 font-mono">Page 1 of 48</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div className="space-y-4">
                <div className="h-4 w-full bg-zinc-100 rounded" />
                <div className="h-4 w-5/6 bg-zinc-100 rounded" />
                <div className="p-3 bg-zinc-50 border border-zinc-100 rounded-lg space-y-2">
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-2/3 bg-zinc-200 rounded" />
                </div>
              </div>
              <div className="space-y-4">
                <div className="h-4 w-3/4 bg-zinc-100 rounded" />
                <div className="h-32 w-full bg-zinc-50 border border-zinc-100 flex flex-col items-center justify-center rounded-lg gap-2 text-zinc-400">
                  <FileText className="size-8 text-zinc-300" />
                  <span className="text-xs font-medium">Architecture Topology</span>
                </div>
              </div>
            </div>

            {/* AI Highlights & Context Overlays */}
            <div className="absolute top-[180px] left-12 w-56 h-6 bg-primary/20 border-l-4 border-primary pointer-events-none" />
            <div className="absolute top-[205px] left-12 group z-30">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-white cursor-pointer shadow-lg animate-pulse hover:scale-110 transition-transform duration-200">
                <Bot className="size-3.5" />
              </div>
              <div className="hidden group-hover:block absolute left-8 top-0 w-64 bg-surface-container-highest text-on-surface p-3 rounded-lg border border-outline-variant shadow-xl text-xs leading-relaxed">
                <span className="font-bold block mb-1 text-primary">AI Context Insight</span>
                Grover search parameters must strictly map 2-qubit targets on US-East cloud servers for compliance rules.
              </div>
            </div>
          </div>
        );

      default: // Q3_Financial_Review.pdf
        return (
          <div className="space-y-6">
            <div className="flex justify-between border-b border-zinc-200 pb-4">
              <div className="font-bold text-base md:text-lg text-zinc-800">Financial Performance Analysis</div>
              <div className="text-xs text-zinc-400 font-mono">Page 1 of 24</div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2">
              <div className="space-y-4">
                <div className="h-4 w-3/4 bg-zinc-100 rounded" />
                <div className="h-4 w-full bg-zinc-100 rounded" />
                <div className="h-4 w-5/6 bg-zinc-100 rounded" />
                <div className="h-32 w-full bg-zinc-50 border border-zinc-100 flex flex-col items-center justify-center rounded-lg gap-2 text-zinc-400">
                  <BarChart2 className="size-8 text-zinc-300" />
                  <span className="text-xs font-medium">Revenue Growth APAC</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="h-4 w-full bg-zinc-100 rounded" />
                <div className="h-4 w-2/3 bg-zinc-100 rounded" />
                <div className="p-3 bg-zinc-50 border border-zinc-100 rounded-lg space-y-2">
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-full bg-zinc-200 rounded" />
                  <div className="h-2 w-2/3 bg-zinc-200 rounded" />
                </div>
              </div>
            </div>

            {/* AI Highlights & Context Overlays */}
            <div className="absolute top-48 left-12 w-48 h-6 bg-primary/20 border-l-4 border-primary pointer-events-none" />
            <div className="absolute top-[210px] left-12 group z-30">
              <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center text-white cursor-pointer shadow-lg animate-pulse hover:scale-110 transition-transform duration-200">
                <Bot className="size-3.5" />
              </div>
              <div className="hidden group-hover:block absolute left-8 top-0 w-64 bg-surface-container-highest text-on-surface p-3 rounded-lg border border-outline-variant shadow-xl text-xs leading-relaxed">
                <span className="font-bold block mb-1 text-primary">AI Context Insight</span>
                This metric represents a 14% deviation from the projected fiscal target mentioned on page 12.
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex-1 overflow-auto custom-scrollbar bg-surface-container p-6 md:p-12 flex justify-center items-start">
      <div 
        className="w-full max-w-[800px] bg-white min-h-[1050px] shadow-2xl p-6 md:p-8 text-zinc-900 relative rounded-lg origin-top transition-transform duration-200 ease-out select-none border border-zinc-200"
        style={{ transform: `scale(${scale})` }}
      >
        {renderPDFContent()}
      </div>
    </div>
  );
}
