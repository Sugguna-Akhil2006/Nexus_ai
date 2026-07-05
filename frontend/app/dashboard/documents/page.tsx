"use client";

import { useState } from "react";
import { Bot, Wand2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileExplorer, { FolderItem } from "@/components/documents/file-explorer";
import DocumentToolbar from "@/components/documents/document-toolbar";
import PDFViewer from "@/components/documents/pdf-viewer";
import AIPanel, { DocumentAnalysis } from "@/components/documents/ai-panel";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";

// Folders mock structure
const DOCUMENT_FOLDERS: FolderItem[] = [
  {
    id: "folder-1",
    name: "Project Alpha",
    files: [
      { name: "Q3_Financial_Review.pdf", type: "pdf" },
      { name: "Stakeholder_Analysis.docx", type: "docx" },
      { name: "Technical_Specs_v2.pdf", type: "pdf" },
    ],
  },
  {
    id: "folder-2",
    name: "Legal Archive",
    files: [
      { name: "NDA_Agreement_Draft.pdf", type: "pdf" },
      { name: "Compliance_Policy.xlsx", type: "xlsx" },
    ],
  },
  {
    id: "folder-3",
    name: "Training Data",
    files: [
      { name: "Model_Training_Logs.xlsx", type: "xlsx" },
    ],
  },
];

// Document AI insights database
const ANALYSIS_DB: Record<string, DocumentAnalysis> = {
  "Q3_Financial_Review.pdf": {
    filename: "Q3_Financial_Review.pdf",
    takeaway: "Revenue growth exceeded projections by 14.2% driven by aggressive expansion in APAC regions.",
    sentiment: "Positive",
    sentimentColor: "text-emerald-400",
    confidence: "98%",
    entities: ["Global Corp", "NASDAQ: GCRP", "Q3 FY24", "APAC Market"],
    dataPoints: [
      { label: "Revenue Growth (APAC)", value: "+14.2%" },
      { label: "Profit Margin", value: "22.4%" },
      { label: "Deviation from projected target", value: "14%" },
      { label: "Total APAC Revenue", value: "$12.4M" },
    ],
    risks: [
      "Currency exchange rate volatility in APAC markets might slightly squeeze Q4 margins.",
      "Deviations from target projection requires auditing APAC division expense logs.",
    ],
  },
  "Stakeholder_Analysis.docx": {
    filename: "Stakeholder_Analysis.docx",
    takeaway: "Key stakeholder sentiment is currently flagged as neutral-negative due to delayed Q4 product releases.",
    sentiment: "Neutral",
    sentimentColor: "text-amber-400",
    confidence: "92%",
    entities: ["Stakeholders", "Product Team", "Q4 Roadmap", "Executive Board"],
    dataPoints: [
      { label: "Net Promoter Score", value: "7.2 / 10" },
      { label: "Communication Frequency", value: "Bi-weekly" },
      { label: "Target satisfaction", value: "90%" },
      { label: "Current satisfaction", value: "78%" },
    ],
    risks: [
      "Stakeholder alignment risk if Q4 releases are pushed further.",
      "Direct executive board review required for delayed roadmap items.",
    ],
  },
  "Technical_Specs_v2.pdf": {
    filename: "Technical_Specs_v2.pdf",
    takeaway: "Grover search parameters must strictly map 2-qubit targets on US-East servers to satisfy security rules.",
    sentiment: "Positive",
    sentimentColor: "text-emerald-400",
    confidence: "96%",
    entities: ["Qiskit Simulation", "Aer Simulator", "US-East Cloud", "controlled-Z"],
    dataPoints: [
      { label: "Simulation backend", value: "qasm_simulator" },
      { label: "Qubit count", value: "2" },
      { label: "Base gate count", value: "18" },
      { label: "API Compliance", value: "100%" },
    ],
    risks: [
      "Security checks flag a warning if quantum circuits execute on overseas simulation clusters.",
      "Aer Simulator performance might experience throttle under peak concurrency logs.",
    ],
  },
  // Fallbacks for closed folders files
  "NDA_Agreement_Draft.pdf": {
    filename: "NDA_Agreement_Draft.pdf",
    takeaway: "Standard mutual nondisclosure agreement governing document sharing protocols.",
    sentiment: "Neutral",
    sentimentColor: "text-amber-400",
    confidence: "95%",
    entities: ["NDA", "Legal Dept", "Confidentiality"],
    dataPoints: [
      { label: "Term duration", value: "3 Years" },
      { label: "Jurisdiction", value: "Delaware" },
    ],
    risks: ["Indemnity caps need review from legal council."],
  },
  "Compliance_Policy.xlsx": {
    filename: "Compliance_Policy.xlsx",
    takeaway: "Compliance policy auditing sheet tracking operational and regulatory flags.",
    sentiment: "Positive",
    sentimentColor: "text-emerald-400",
    confidence: "99%",
    entities: ["Audit Logs", "Compliance", "SEC Rules"],
    dataPoints: [
      { label: "Audit status", value: "Passed" },
      { label: "Flagged nodes", value: "0" },
    ],
    risks: ["Requires manual re-evaluation on quarterly cycles."],
  },
  "Model_Training_Logs.xlsx": {
    filename: "Model_Training_Logs.xlsx",
    takeaway: "Deep learning training cycles metrics recording validation losses and accuracies.",
    sentiment: "Positive",
    sentimentColor: "text-emerald-400",
    confidence: "97%",
    entities: ["Epoch Logs", "Nexus-4B Model", "Loss curve"],
    dataPoints: [
      { label: "Final Accuracy", value: "98.4%" },
      { label: "Validation Loss", value: "0.012" },
    ],
    risks: ["Potential overfitting patterns detected on cluster nodes."],
  },
};

export default function DocumentIntelligencePage() {
  const [activeFilename, setActiveFilename] = useState("Q3_Financial_Review.pdf");
  const [zoom, setZoom] = useState(100);
  const [isEmpty, setIsEmpty] = useState(false);

  const activeAnalysis = ANALYSIS_DB[activeFilename] || ANALYSIS_DB["Q3_Financial_Review.pdf"];

  // Zoom events
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 10, 155));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 10, 60));
  };

  // Inquiry Submission simulation
  const handleSendInquiry = (prompt: string) => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 1500)),
      {
        loading: `Submitting inquiry: "${prompt}"...`,
        success: 'AI simulations calculated against document coordinates.',
        error: 'Simulation failed.',
      }
    );
  };

  const handleTriggerMagicInsight = () => {
    toast.promise(
      new Promise((resolve) => setTimeout(resolve, 2000)),
      {
        loading: 'Running magic document compliance audit...',
        success: 'AI audit complete. Re-indexed text layers successfully.',
        error: 'Audit failed.',
      }
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] w-full overflow-hidden bg-background text-on-background relative select-none">
      <div className="px-6 md:px-8 pt-4 flex items-center justify-between shrink-0">
        <DashboardBreadcrumbs />
        <Button 
          variant="ghost" 
          size="xs" 
          onClick={() => setIsEmpty(!isEmpty)} 
          className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
        >
          {isEmpty ? "● Show Documents" : "○ Simulate Empty State"}
        </Button>
      </div>
      <div className="flex-1 flex overflow-hidden">
        
        {isEmpty ? (
          <div className="flex-1 flex items-center justify-center p-8 bg-surface-container-lowest/20">
            <EmptyState
              icon={FileText}
              title="No Documents Uploaded"
              description="Upload files to begin semantic vector embedding extraction, document summaries, risk profiling, and context searches."
              actionLabel="Upload First Document"
              onAction={() => toast.success("Initiating secure file gateway upload protocol...")}
              accentColor="primary"
            />
          </div>
        ) : (
          <>
            {/* Column 1: File Explorer panel */}
            <FileExplorer
              activeFilename={activeFilename}
              onSelectFile={setActiveFilename}
              folders={DOCUMENT_FOLDERS}
            />

            {/* Column 2: Document Preview Canvas */}
            <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
              
              {/* Preview header toolbar */}
              <DocumentToolbar
                filename={activeFilename}
                isVerified={true}
                zoom={zoom}
                onZoomIn={handleZoomIn}
                onZoomOut={handleZoomOut}
                onDownload={() => toast.success(`Downloading file: ${activeFilename}`)}
                onShare={() => toast.success(`Shareable URL generated for: ${activeFilename}`)}
              />

              {/* Scalable PDF Mockup view */}
              <PDFViewer filename={activeFilename} zoom={zoom} />

            </div>

            {/* Column 3: AI Intelligence panel */}
            <AIPanel
              analysis={activeAnalysis}
              onSendInquiry={handleSendInquiry}
            />

            {/* Magic audit Floating Action Button (FAB) positioned just left of right panel */}
            <div className="fixed bottom-8 right-[400px] z-50 hidden lg:block">
              <Button
                onClick={handleTriggerMagicInsight}
                className="w-14 h-14 rounded-full bg-tertiary text-on-tertiary hover:scale-105 active:scale-95 transition-all shadow-xl hover:bg-tertiary/95 flex items-center justify-center border-none cursor-pointer"
                title="Run Magic AI Document Audit"
              >
                <Wand2 className="size-6 text-on-tertiary" />
              </Button>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
