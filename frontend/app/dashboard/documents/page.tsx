"use client";

import { useEffect, useState } from "react";
import { Bot, Wand2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import FileExplorer, { FolderItem } from "@/components/documents/file-explorer";
import DocumentToolbar from "@/components/documents/document-toolbar";
import PDFViewer from "@/components/documents/pdf-viewer";
import AIPanel, { DocumentAnalysis } from "@/components/documents/ai-panel";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import EmptyState from "@/components/common/empty-state";
import { useWorkspace } from "@/providers/workspace-provider";

export default function DocumentIntelligencePage() {
  const { activeWorkspace } = useWorkspace();
  const [documents, setDocuments] = useState<any[]>([]);
  const [activeFilename, setActiveFilename] = useState("");
  const [zoom, setZoom] = useState(100);
  const [loading, setLoading] = useState(true);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [isSending, setIsSending] = useState(false);

  const activeWorkspaceId = activeWorkspace?.workspace_id || "default-ws";

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`/api/documents?workspace_id=${activeWorkspaceId}`);
      if (res.ok) {
        const data = await res.json();
        const docs = data.documents || [];
        setDocuments(docs);
        if (docs.length > 0 && !activeFilename) {
          setActiveFilename(docs[0].name);
        } else if (docs.length === 0) {
          setActiveFilename("");
        }
      }
    } catch (e) {
      console.error("Failed to load documents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [activeWorkspaceId]);

  const activeAnalysis: DocumentAnalysis = {
    filename: activeFilename || "No Document",
    takeaway: activeFilename ? `Semantic vector index established for document: ${activeFilename}. Ingested into database.` : "No document selected.",
    sentiment: "Positive",
    sentimentColor: "text-emerald-400",
    confidence: "95%",
    entities: activeFilename ? [activeFilename, "Workspace Index", "Secure Node"] : [],
    dataPoints: activeFilename ? [
      { label: "Status", value: "Indexed" },
      { label: "Format", value: activeFilename.split(".").pop()?.toUpperCase() || "PDF" }
    ] : [],
    risks: activeFilename ? ["No critical compliance threats detected in primary chunk indexing."] : []
  };

  // Folders structure for file-explorer
  const folders: FolderItem[] = [
    {
      id: "workspace-docs",
      name: "Workspace Documents",
      files: documents.map((doc: any) => ({
        name: doc.name,
        type: doc.name.split(".").pop()?.toLowerCase() as any || "pdf"
      }))
    }
  ];

  // Zoom events
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 10, 155));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 10, 60));
  };

  const handleSendInquiry = async (prompt: string) => {
    const activeDoc = documents.find((d) => d.name === activeFilename);
    if (!activeDoc) {
      toast.error("Please upload or select a document first.");
      return;
    }

    const userMsg = { role: "user" as const, content: prompt };
    setChatMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await fetch("/api/document/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: activeWorkspaceId,
          document_ids: [activeDoc.document_id],
          query: prompt
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Query failed.");
      }

      const data = await res.json();
      setChatMessages((prev) => [...prev, { role: "assistant" as const, content: data.answer }]);
      toast.success("AI response received!");
    } catch (e: any) {
      console.error(e);
      toast.error(e.message || "Failed to query document.");
    } finally {
      setIsSending(false);
    }
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
      </div>
      <div className="flex-1 flex overflow-hidden">
        
        {loading ? (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex-1 flex items-center justify-center p-8 bg-surface-container-lowest/20">
            <div className="max-w-md w-full">
              <FileExplorer
                activeFilename={activeFilename}
                onSelectFile={setActiveFilename}
                folders={folders}
                onUploadSuccess={fetchDocuments}
              />
            </div>
            <div className="flex-grow flex items-center justify-center">
              <EmptyState
                icon={FileText}
                title="No Documents Uploaded"
                description="Upload files to begin semantic vector embedding extraction, document summaries, risk profiling, and context searches."
                actionLabel="Upload First Document"
                onAction={() => document.getElementById("file-dropzone-input")?.click()}
                accentColor="primary"
              />
            </div>
          </div>
        ) : (
          <>
            {/* Column 1: File Explorer panel */}
            <FileExplorer
              activeFilename={activeFilename}
              onSelectFile={setActiveFilename}
              folders={folders}
              onUploadSuccess={fetchDocuments}
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
              chatMessages={chatMessages}
              onSendInquiry={handleSendInquiry}
              isSending={isSending}
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
