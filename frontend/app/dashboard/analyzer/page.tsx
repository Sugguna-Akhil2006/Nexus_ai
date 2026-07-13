"use client";

import { useEffect, useState, useMemo } from "react";
import { Download, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import ResumeUpload from "@/components/analyzer/resume-upload";
import RoleSelector from "@/components/analyzer/role-selector";
import MatchScoreCard from "@/components/analyzer/match-score-card";
import SkillAlignment from "@/components/analyzer/skill-alignment";
import CompetencyAnalysis from "@/components/analyzer/competency-analysis";
import ExperienceTrajectory from "@/components/analyzer/experience-trajectory";
import RecentScans, { ScanItem } from "@/components/analyzer/recent-scans";
import { useWorkspace } from "@/providers/workspace-provider";

export default function ResumeAnalyzerPage() {
  const { activeWorkspace } = useWorkspace();
  const [selectedRole, setSelectedRole] = useState("Senior Fullstack Engineer");
  const [jobDescription, setJobDescription] = useState("");
  
  // History scans list
  const [scans, setScans] = useState<any[]>([]);
  const [activeScanId, setActiveScanId] = useState("");
  const [activeReport, setActiveReport] = useState<any | null>(null);

  // File analyzing states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingStep, setAnalyzingStep] = useState("");

  const activeWorkspaceId = activeWorkspace?.workspace_id || "default-ws";

  // Fetch History
  const fetchHistory = async () => {
    try {
      const res = await fetch(`/resume/history?workspace_id=${activeWorkspaceId}`);
      if (res.ok) {
        const data = await res.json();
        const history = data.history || [];
        setScans(history);
        if (history.length > 0 && !activeScanId) {
          setActiveScanId(history[0].report_id || history[0].document_id);
        }
      }
    } catch (e) {
      console.error("Failed to load history", e);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [activeWorkspaceId]);

  // Load Active Report details
  useEffect(() => {
    if (!activeScanId) return;
    fetch(`/resume/report/${activeScanId}`)
      .then((res) => {
        if (res.ok) return res.json();
      })
      .then((data) => {
        if (data) {
          setActiveReport(data);
        }
      })
      .catch((err) => console.error("Failed to load report", err));
  }, [activeScanId]);

  // Handle file upload drag-and-drop
  const handleUploadStart = async (filename: string, fileObject?: File) => {
    if (!fileObject) {
      toast.error("Invalid file object.");
      return;
    }
    setIsAnalyzing(true);
    setAnalyzingStep("Uploading file to security sandbox...");

    const formData = new FormData();
    formData.append("file", fileObject);

    try {
      const res = await fetch(`/resume/upload?workspace_id=${activeWorkspaceId}`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Upload to security sandbox failed.");
      }
      const uploadData = await res.json();
      const docId = uploadData.document_id;

      setAnalyzingStep("Running semantic text extraction & parsing...");
      const analyzeRes = await fetch("/resume/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: docId,
          workspace_id: activeWorkspaceId,
          user_id: "admin"
        })
      });

      if (!analyzeRes.ok) {
        const err = await analyzeRes.json().catch(() => ({}));
        throw new Error(err.detail || "ATS Resume scanning engine failed.");
      }
      const report = await analyzeRes.json();
      const reportId = report.report_id || docId;

      toast.success("ATS Resume Scan Completed!");
      await fetchHistory();
      setActiveScanId(reportId);
    } catch (e: any) {
      console.error(e);
      toast.error(e.message || "Failed to analyze resume.");
    } finally {
      setIsAnalyzing(false);
      setAnalyzingStep("");
    }
  };

  const handleBulkUpload = () => {
    toast.info("Bulk upload folder processor initialized.");
  };

  const handleExportReport = () => {
    if (!activeScanId) return;
    window.open(`/resume/report/${activeScanId}?export=pdf`, "_blank");
  };

  // Compile scans list for the table
  const scansList = useMemo<ScanItem[]>(() => {
    return scans.map((s) => ({
      id: s.report_id || s.document_id,
      candidateName: s.report_data?.parser?.name || s.filename || "Candidate",
      uploadTime: s.created_at ? new Date(s.created_at).toLocaleDateString() : "Just now",
      fileType: "PDF",
      role: selectedRole,
      score: s.ats_score || s.report_data?.ats?.ats_score || 75,
      status: "Shortlisted",
    }));
  }, [scans, selectedRole]);

  // Compile weighting/details structure
  const weightingDetails = useMemo(() => {
    if (!activeReport) {
      return {
        score: 0,
        desc: "Upload a resume to begin analysis",
        badges: [],
        skills: [],
        strengths: [],
        gaps: [],
        insights: "No resume active.",
        trajectory: []
      };
    }

    const techSkills = activeReport.skill_analysis?.technical_skills || [];
    const softSkills = activeReport.skill_analysis?.soft_skills || [];
    const skillsMapped = [...techSkills, ...softSkills].map((name, idx) => ({
      name,
      percentage: Math.max(50, 100 - idx * 8),
      isPrimary: idx < 3
    }));

    return {
      score: Math.round(activeReport.ats_score || 75),
      desc: activeReport.executive_summary || "Evaluation completed.",
      badges: activeReport.strengths || ["Analyzed"],
      skills: skillsMapped,
      strengths: activeReport.strengths || [],
      gaps: activeReport.weaknesses || [],
      insights: activeReport.executive_summary || "",
      trajectory: [
        { year: "Score", candidateScore: activeReport.ats_score || 75, benchmarkScore: 80 }
      ]
    };
  }, [activeReport]);

  return (
    <div className="space-y-6 md:space-y-8 select-none">
      <DashboardBreadcrumbs />
      
      {/* Header section triggers */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-4 select-none shrink-0 border-b border-outline-variant/30 pb-6">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-on-surface">
            ATS Intelligence Engine
          </h2>
          <p className="text-xs md:text-sm text-on-surface-variant font-medium max-w-2xl mt-1 leading-relaxed">
            Leverage neural parsing to extract, score, and analyze resumes against complex enterprise job descriptions with high precision.
          </p>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            disabled={!activeScanId}
            onClick={handleExportReport}
            className="bg-surface-container-low border border-outline-variant hover:bg-surface-container hover:border-primary px-4 py-2.5 rounded-lg text-xs font-bold text-on-surface cursor-pointer shadow-sm flex items-center gap-1.5"
          >
            <Download className="size-4" />
            Export Report
          </Button>
          <Button
            onClick={handleBulkUpload}
            className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
          >
            <UploadCloud className="size-4" />
            Bulk Upload
          </Button>
        </div>
      </section>

      {/* Workspace split grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left config side panel */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <ResumeUpload 
            onUploadStart={handleUploadStart} 
            isAnalyzing={isAnalyzing}
            analyzingStep={analyzingStep}
          />
          <RoleSelector 
            selectedRole={selectedRole}
            onChangeRole={setSelectedRole}
            jobDescription={jobDescription}
            onChangeJD={setJobDescription}
          />
        </div>

        {/* Right dashboard report metrics */}
        <div className="col-span-12 lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <MatchScoreCard 
            score={weightingDetails.score}
            matchDescription={weightingDetails.desc}
            badges={weightingDetails.badges}
          />
          
          <SkillAlignment 
            skills={weightingDetails.skills}
          />

          <div className="col-span-1 md:col-span-2">
            <CompetencyAnalysis
              strengths={weightingDetails.strengths}
              gaps={weightingDetails.gaps}
              insights={weightingDetails.insights}
            />
          </div>

          <ExperienceTrajectory 
            data={weightingDetails.trajectory}
          />
        </div>
      </div>

      {/* Recent scans table */}
      {scansList.length > 0 && (
        <RecentScans
          scans={scansList}
          activeScanId={activeScanId}
          onSelectScan={setActiveScanId}
        />
      )}
    </div>
  );
}
