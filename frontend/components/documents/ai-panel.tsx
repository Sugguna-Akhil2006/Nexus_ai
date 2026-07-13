"use client";

import { useState } from "react";
import { Sparkles, Info, HeartHandshake, Eye, AlertTriangle, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import EntityTags from "./entity-tags";
import AIChatBox from "./ai-chat-box";

export interface DocumentAnalysis {
  filename: string;
  takeaway: string;
  sentiment: string;
  sentimentColor: string; // e.g. "text-emerald-400" | "text-amber-400"
  confidence: string;
  entities: string[];
  dataPoints: { label: string; value: string }[];
  risks: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface AIPanelProps {
  analysis: DocumentAnalysis;
  chatMessages: ChatMessage[];
  onSendInquiry: (prompt: string) => void;
  isSending?: boolean;
}

type TabType = "summary" | "datapoints" | "risks";

export default function AIPanel({ analysis, chatMessages, onSendInquiry, isSending = false }: AIPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>("summary");

  const mapBgUrl = "https://lh3.googleusercontent.com/aida-public/AB6AXuCUYwaiQsVtVPi8DTkljyii-MXe2bF_FeWmBnsWHkXsIFHL-2E7s5A4C8XJvFxxUHo1u4naKYo7XDTXN2UzA2FAYwImHbVpRovdRtpwwvqZbK1HAODSsZq4vrvLjdBY0NZEVqnzd9FqY0JGxb2k_lFJYxzF5t_ohBP3Eb0I0M7sw_E-d2mZJjZf8bAG9X7jj95HpmvZKssiQNSqd0wGyCdjwE3Aerl3s2GzP6bHwDtVHdXxU-wfTOlP1-nF2FH6_X2ew3Js12hXqQzb";

  return (
    <section className="w-96 border-l border-outline-variant bg-surface-container-lowest flex flex-col overflow-hidden shrink-0 select-none">
      
      {/* Panel Header */}
      <div className="p-4 border-b border-outline-variant flex items-center gap-2 select-none">
        <Sparkles className="size-4 text-primary" />
        <h2 className="text-[10px] font-bold text-on-surface uppercase tracking-wider">
          Intelligence Panel
        </h2>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-6">
        
        {/* Navigation Tabs */}
        <div className="flex bg-surface-container rounded-lg p-1 select-none">
          {(["summary", "datapoints", "risks"] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "flex-1 py-1.5 text-xs rounded transition-all cursor-pointer font-semibold",
                activeTab === tab
                  ? "bg-surface-container-highest text-on-surface shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              )}
            >
              {tab === "summary" ? "Summary" : tab === "datapoints" ? "Data Points" : "Risks"}
            </button>
          ))}
        </div>

        {/* Tab Layout Renderings */}
        {activeTab === "summary" && (
          <div className="space-y-6">
            {/* Takeaway Card */}
            <div className="p-4 bg-surface-container rounded-lg border border-outline-variant hover:border-primary/40 transition-colors shadow-sm duration-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[9px] font-bold text-on-tertiary-container bg-tertiary-container/20 px-2 py-0.5 rounded uppercase tracking-wider">
                  Key Takeaway
                </span>
                <Info className="size-3.5 text-on-surface-variant/80" />
              </div>
              <p className="text-xs md:text-sm text-on-surface leading-relaxed">
                {analysis.takeaway}
              </p>
            </div>

            {/* Metrics cards grid */}
            <div className="grid grid-cols-2 gap-4">
              {/* Sentiment Card */}
              <div className="p-4 bg-surface-container rounded-lg border border-outline-variant shadow-sm">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant/70 tracking-wider">
                  Sentiment
                </span>
                <div className={cn("mt-1.5 text-lg font-bold leading-tight", analysis.sentimentColor)}>
                  {analysis.sentiment}
                </div>
              </div>

              {/* Confidence Card */}
              <div className="p-4 bg-surface-container rounded-lg border border-outline-variant shadow-sm">
                <span className="text-[9px] uppercase font-bold text-on-surface-variant/70 tracking-wider">
                  Confidence
                </span>
                <div className="mt-1.5 text-lg font-bold text-primary leading-tight">
                  {analysis.confidence}
                </div>
              </div>
            </div>

            {/* Extracted Entities */}
            <div className="p-4 bg-surface-container rounded-lg border border-outline-variant space-y-3 shadow-sm">
              <h3 className="text-[9px] font-bold text-on-surface uppercase tracking-wider">
                Detected Entities
              </h3>
              <EntityTags tags={analysis.entities} />
            </div>

            {/* Cover map visual portal */}
            <div className="relative group overflow-hidden rounded-lg h-32 border border-outline-variant shadow-sm select-none">
              <div 
                className="bg-cover bg-center w-full h-full brightness-50 group-hover:scale-105 transition-transform duration-700 ease-out" 
                style={{ backgroundImage: `url('${mapBgUrl}')` }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <button className="bg-surface/85 backdrop-blur-sm border border-outline-variant px-4 py-2 rounded-md text-xs font-bold flex items-center gap-2 hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all duration-200 cursor-pointer shadow-lg select-none">
                  <Layers className="size-3.5" />
                  Visual Map
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "datapoints" && (
          <div className="space-y-4">
            <div className="p-4 bg-surface-container rounded-lg border border-outline-variant shadow-sm space-y-3">
              <h3 className="text-[9px] font-bold text-on-surface uppercase tracking-wider mb-1">
                Extracted Data Points
              </h3>
              <div className="divide-y divide-outline-variant/30 text-xs">
                {analysis.dataPoints.map((dp) => (
                  <div key={dp.label} className="py-2.5 flex justify-between gap-4">
                    <span className="text-on-surface-variant font-medium">{dp.label}</span>
                    <span className="text-primary font-bold text-right">{dp.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "risks" && (
          <div className="space-y-4">
            <div className="p-4 bg-surface-container rounded-lg border border-outline-variant shadow-sm space-y-3">
              <div className="flex items-center gap-1.5 text-amber-400">
                <AlertTriangle className="size-4" />
                <h3 className="text-[9px] font-bold uppercase tracking-wider">
                  Compliance Risk Warnings
                </h3>
              </div>
              <ul className="space-y-2.5 text-xs text-on-surface leading-relaxed list-none">
                {analysis.risks.map((risk, idx) => (
                  <li key={idx} className="flex gap-2 items-start bg-surface-container-high/30 p-2 rounded border border-outline-variant/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Chat message bubbles history */}
        {chatMessages.length > 0 && (
          <div className="space-y-3.5 pt-4 border-t border-outline-variant">
            <h3 className="text-[10px] font-bold text-on-surface uppercase tracking-wider pl-0.5">
              Q&A History
            </h3>
            <div className="space-y-3 max-h-60 overflow-y-auto custom-scrollbar pr-1 select-text">
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "p-3 rounded-lg text-xs leading-relaxed max-w-[85%] font-medium",
                    msg.role === "user"
                      ? "bg-primary/10 border border-primary/20 text-on-surface ml-auto rounded-tr-none"
                      : "bg-surface-container border border-outline-variant text-on-surface rounded-tl-none"
                  )}
                >
                  {msg.content}
                </div>
              ))}
              {isSending && (
                <div className="p-3 rounded-lg text-xs leading-relaxed max-w-[85%] font-medium bg-surface-container border border-outline-variant text-on-surface rounded-tl-none animate-pulse">
                  AI is thinking...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat input box */}
        <div className="pt-4 border-t border-outline-variant">
          <AIChatBox onSubmit={onSendInquiry} />
        </div>

      </div>

      {/* Footer statistics */}
      <div className="p-4 border-t border-outline-variant bg-surface-container-lowest select-none">
        <div className="flex items-center justify-between text-[10px] font-mono font-code text-on-surface-variant/60">
          <span>AI MODEL: NEXUS-4B</span>
          <span>TOKENS: 4,102/32K</span>
        </div>
      </div>
    </section>
  );
}
