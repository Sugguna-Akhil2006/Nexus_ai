"use client";

import { useState, useMemo } from "react";
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

// Candidate datasets structured for role-based weighing changes
const CANDIDATE_PROFILES: Record<string, any> = {
  "sarah-henderson": {
    id: "sarah-henderson",
    name: "Sarah K. Henderson",
    uploadTime: "2h ago",
    fileType: "PDF",
    status: "Interviewed",
    rolesWeightings: {
      "Senior Fullstack Engineer": {
        score: 62,
        desc: "Moderate match - lacks engineering background",
        badges: ["Design Focus", "Frontend Exposure"],
        skills: [
          { name: "Technical Proficiency", percentage: 55, isPrimary: false },
          { name: "Strategic Leadership", percentage: 80, isPrimary: true },
          { name: "Domain Knowledge", percentage: 65, isPrimary: false },
        ],
        strengths: ["Design Systems Integration", "Frontend Alignment", "CSS/HTML Architecture"],
        gaps: ["No backend exposure (Node/Rust)", "Distributed Systems", "Database Optimization"],
        insights: "Sarah is a lead designer. While she has frontend knowledge, she lacks the system engineering depth needed for a Senior Fullstack role.",
      },
      "Product Marketing Manager": {
        score: 92,
        desc: "High confidence match for Lead Level",
        badges: ["Top 3%", "Portfolio: Excellent", "UX Design Pro"],
        skills: [
          { name: "Technical Proficiency", percentage: 88, isPrimary: true },
          { name: "Strategic Leadership", percentage: 94, isPrimary: true },
          { name: "Domain Knowledge", percentage: 90, isPrimary: false },
        ],
        strengths: ["Product Vision Alignment", "Customer Persona Research", "Cross-functional Collaboration"],
        gaps: ["Data analytics toolkits (Tableau/SQL)", "Traditional growth advertising"],
        insights: "Sarah shows progressive responsibility growth. Experience aligns with creative product strategy and user-centric marketing campaigns.",
      },
      "AI Research Scientist": {
        score: 35,
        desc: "Low match - non-technical research focus",
        badges: ["Design Focus", "Qualitative Research"],
        skills: [
          { name: "Technical Proficiency", percentage: 30, isPrimary: false },
          { name: "Strategic Leadership", percentage: 68, isPrimary: false },
          { name: "Domain Knowledge", percentage: 40, isPrimary: false },
        ],
        strengths: ["User Behavior Analysis", "Experimental Testing"],
        gaps: ["No Machine Learning expertise", "Python/PyTorch coding", "Statistical Model Building"],
        insights: "Design background is useful for HCI design, but she lacks the mathematics and machine learning competencies required.",
      }
    },
    trajectory: [
      { year: "Year 1", candidateScore: 40, benchmarkScore: 45 },
      { year: "Year 2", candidateScore: 55, benchmarkScore: 52 },
      { year: "Year 3", candidateScore: 68, benchmarkScore: 60 },
      { year: "Year 4", candidateScore: 82, benchmarkScore: 68 },
      { year: "Year 5", candidateScore: 92, benchmarkScore: 75 },
    ],
  },
  "marcus-thorne": {
    id: "marcus-thorne",
    name: "Marcus Thorne",
    uploadTime: "5h ago",
    fileType: "DOCX",
    status: "Archived",
    rolesWeightings: {
      "Senior Fullstack Engineer": {
        score: 48,
        desc: "Low match - network/security specialization",
        badges: ["Security Focus", "Infrastructure Focus"],
        skills: [
          { name: "Technical Proficiency", percentage: 60, isPrimary: false },
          { name: "Strategic Leadership", percentage: 42, isPrimary: false },
          { name: "Domain Knowledge", percentage: 50, isPrimary: false },
        ],
        strengths: ["Infrastructure Scripting", "System Vulnerability Scans", "Network Routing"],
        gaps: ["React/Frontend Frameworks", "Database modeling", "Application architectures"],
        insights: "Marcus is a security analyst. He understands server components but lacks coding and application-building experience.",
      },
      "Product Marketing Manager": {
        score: 32,
        desc: "Low match - highly technical candidate",
        badges: ["Technical Focus", "No Marketing Exposure"],
        skills: [
          { name: "Technical Proficiency", percentage: 58, isPrimary: false },
          { name: "Strategic Leadership", percentage: 30, isPrimary: false },
          { name: "Domain Knowledge", percentage: 22, isPrimary: false },
        ],
        strengths: ["Detailed Technical Writing"],
        gaps: ["No sales copywriting", "No user acquisition campaigns", "No design/branding experience"],
        insights: "Marcus lacks commercial marketing and product launch experience.",
      },
      "AI Research Scientist": {
        score: 41,
        desc: "Low match - infrastructure security bias",
        badges: ["Threat Assessment", "No ML Exposure"],
        skills: [
          { name: "Technical Proficiency", percentage: 54, isPrimary: false },
          { name: "Strategic Leadership", percentage: 38, isPrimary: false },
          { name: "Domain Knowledge", percentage: 45, isPrimary: false },
        ],
        strengths: ["Vulnerability Auditing", "Infrastructure Compliance"],
        gaps: ["No scientific machine learning research", "PyTorch/Tensorflow frameworks", "Algorithmic publications"],
        insights: "Marcus has traditional pen-testing expertise but lacks scientific AI research methodology and coding practices.",
      }
    },
    trajectory: [
      { year: "Year 1", candidateScore: 30, benchmarkScore: 40 },
      { year: "Year 2", candidateScore: 35, benchmarkScore: 48 },
      { year: "Year 3", candidateScore: 38, benchmarkScore: 55 },
      { year: "Year 4", candidateScore: 42, benchmarkScore: 62 },
      { year: "Year 5", candidateScore: 45, benchmarkScore: 70 },
    ],
  },
  "alex-chen": {
    id: "alex-chen",
    name: "Alex Chen (Parsed)",
    uploadTime: "Just now",
    fileType: "PDF",
    status: "Shortlisted",
    rolesWeightings: {
      "Senior Fullstack Engineer": {
        score: 85,
        desc: "High confidence match for Sr. Level",
        badges: ["Top 5%", "Culture Fit: Strong", "Concurrency Pro"],
        skills: [
          { name: "Technical Proficiency", percentage: 92, isPrimary: true },
          { name: "Strategic Leadership", percentage: 68, isPrimary: false },
          { name: "Domain Knowledge", percentage: 88, isPrimary: true },
        ],
        strengths: ["Distributed Systems", "Rust Optimization", "Cloud-Native Architecture"],
        gaps: ["React Native mobile development", "ISO 27001 Certification"],
        insights: "Candidate shows progressive responsibility growth. Experience aligns with our recent pivot to high-concurrency architecture.",
      },
      "Product Marketing Manager": {
        score: 40,
        desc: "Low match - developer-centric candidate",
        badges: ["Tech Focus", "Low Commercial Strategy"],
        skills: [
          { name: "Technical Proficiency", percentage: 70, isPrimary: false },
          { name: "Strategic Leadership", percentage: 45, isPrimary: false },
          { name: "Domain Knowledge", percentage: 30, isPrimary: false },
        ],
        strengths: ["Technical Documentation", "Developer Relations API understanding"],
        gaps: ["Campaign management", "SEO & conversion analytics", "Creative direction"],
        insights: "Alex is heavily engineering-biased. Suitable for Developer Relations but not traditional Product Marketing.",
      },
      "AI Research Scientist": {
        score: 74,
        desc: "High match - strong cloud compute & systems engineering",
        badges: ["Compute Heavyweight", "Strong Systems background"],
        skills: [
          { name: "Technical Proficiency", percentage: 85, isPrimary: true },
          { name: "Strategic Leadership", percentage: 55, isPrimary: false },
          { name: "Domain Knowledge", percentage: 76, isPrimary: true },
        ],
        strengths: ["CUDA Parallel computing", "Cloud GPU scheduling", "Python automation"],
        gaps: ["Deep Learning mathematical publications", "No PhD credentials"],
        insights: "Alex has stellar cloud compute and automation experience. Capable of AI implementation, but lacks pure theoretical AI algorithm research history.",
      }
    },
    trajectory: [
      { year: "Year 1", candidateScore: 35, benchmarkScore: 42 },
      { year: "Year 2", candidateScore: 50, benchmarkScore: 50 },
      { year: "Year 3", candidateScore: 65, benchmarkScore: 58 },
      { year: "Year 4", candidateScore: 76, benchmarkScore: 65 },
      { year: "Year 5", candidateScore: 85, benchmarkScore: 72 },
    ],
  }
};

export default function ResumeAnalyzerPage() {
  const [selectedRole, setSelectedRole] = useState("Senior Fullstack Engineer");
  const [jobDescription, setJobDescription] = useState("");
  const [activeCandidateId, setActiveCandidateId] = useState("sarah-henderson");
  const [candidates, setCandidates] = useState<Record<string, any>>(CANDIDATE_PROFILES);

  // File analyzing states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingStep, setAnalyzingStep] = useState("");

  // Handle file upload drag-and-drop mock scan triggers
  const handleUploadStart = async (filename: string) => {
    setIsAnalyzing(true);
    
    // Step 1
    setAnalyzingStep("Running OCR text extraction...");
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    // Step 2
    setAnalyzingStep("Parsing skill vectors...");
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Step 3
    setAnalyzingStep("Calculating ATS match weightings...");
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Finish load and select the newly parsed Alex Chen profile
    setIsAnalyzing(false);
    setActiveCandidateId("alex-chen");
    toast.success("ATS Scan Completed! Parsed resume files for candidate Alex Chen into listings.");
  };

  const handleBulkUpload = () => {
    toast.info("Running Bulk Upload: Select a folder of resumes to process in queue pipeline.");
  };

  const handleExportReport = () => {
    const candidate = candidates[activeCandidateId];
    toast.success(`Exporting ATS Analysis Report for candidate: ${candidate.name} (${selectedRole}) in PDF format. Download starting shortly.`);
  };

  // Compile scans directory table schema
  const scansList = useMemo<ScanItem[]>(() => {
    return Object.values(candidates).map((c) => {
      const activeWeight = c.rolesWeightings[selectedRole] || c.rolesWeightings["Senior Fullstack Engineer"];
      return {
        id: c.id,
        candidateName: c.name,
        uploadTime: c.uploadTime,
        fileType: c.fileType,
        role: selectedRole,
        score: activeWeight.score,
        status: c.status,
      };
    });
  }, [candidates, selectedRole]);

  // Extract selected active candidate reports data
  const currentCandidate = candidates[activeCandidateId] || candidates["sarah-henderson"];
  const currentWeightingDetails = currentCandidate.rolesWeightings[selectedRole] || currentCandidate.rolesWeightings["Senior Fullstack Engineer"];

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
          {/* File drop zone uploader */}
          <ResumeUpload 
            onUploadStart={handleUploadStart} 
            isAnalyzing={isAnalyzing}
            analyzingStep={analyzingStep}
          />
          {/* Role selector dropdown weights */}
          <RoleSelector 
            selectedRole={selectedRole}
            onChangeRole={setSelectedRole}
            jobDescription={jobDescription}
            onChangeJD={setJobDescription}
          />
        </div>

        {/* Right dashboard report metrics */}
        <div className="col-span-12 lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* SVG Score progression rings */}
          <MatchScoreCard 
            score={currentWeightingDetails.score}
            matchDescription={currentWeightingDetails.desc}
            badges={currentWeightingDetails.badges}
          />
          
          {/* Skills alignment percentage bars */}
          <SkillAlignment 
            skills={currentWeightingDetails.skills}
          />

          {/* Strengths, Gaps, and Insights bullet grids */}
          <div className="col-span-1 md:col-span-2">
            <CompetencyAnalysis
              strengths={currentWeightingDetails.strengths}
              gaps={currentWeightingDetails.gaps}
              insights={currentWeightingDetails.insights}
            />
          </div>

          {/* Recharts Career Experience Trajectory line/area charts */}
          <ExperienceTrajectory 
            data={currentCandidate.trajectory}
          />
        </div>
      </div>

      {/* Recent scans table */}
      <RecentScans
        scans={scansList}
        activeScanId={activeCandidateId}
        onSelectScan={setActiveCandidateId}
      />
    </div>
  );
}
