"use client";

import { useState, useMemo } from "react";
import { Download, UploadCloud, Search, ShieldCheck, AlertTriangle, Sparkles, CheckCircle2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import ResumeUpload from "@/components/analyzer/resume-upload";
import RoleSelector from "@/components/analyzer/role-selector";
import MatchScoreCard from "@/components/analyzer/match-score-card";
import SkillAlignment from "@/components/analyzer/skill-alignment";
import CompetencyAnalysis from "@/components/analyzer/competency-analysis";
import ExperienceTrajectory from "@/components/analyzer/experience-trajectory";
import RecentScans, { ScanItem } from "@/components/analyzer/recent-scans";
import { cn } from "@/lib/utils";
import PageContainer from "@/components/common/page-container";

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
        atsStats: { score: 72, formatting: "Passed", sectionCompleteness: "90%", readability: "Excellent" },
        keywords: { found: ["CSS", "HTML", "UI/UX", "Figma", "React"], missing: ["Node.js", "SQL", "Docker", "Distributed Systems"] },
        grammar: { score: "96/100", errors: 2 },
        recruiterSummary: [
          "Strong creative direction and design background.",
          "Good React design-system mapping knowledge.",
          "Interview focus: Ask how she approaches backend API designs and data schema optimization."
        ],
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
        atsStats: { score: 95, formatting: "Optimal", sectionCompleteness: "100%", readability: "Outstanding" },
        keywords: { found: ["Product Strategy", "Market Research", "SEO", "Collaboration", "UX Design"], missing: ["Tableau", "SQL Data Analysis"] },
        grammar: { score: "99/100", errors: 0 },
        recruiterSummary: [
          "Outstanding product strategy alignment with proven high NPS scores.",
          "Highly collaborative candidate who bridges designers and marketing suites.",
          "Interview focus: Evaluate experience with high-budget growth advertising campaigns."
        ],
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
        atsStats: { score: 58, formatting: "Passed", sectionCompleteness: "80%", readability: "Excellent" },
        keywords: { found: ["Research", "Supervised Testing", "Figma"], missing: ["Python", "PyTorch", "CUDA", "TensorFlow"] },
        grammar: { score: "94/100", errors: 4 },
        recruiterSummary: [
          "Strong qualitative user-testing skills but lacks core scientific credentials.",
          "Not recommended for pure algorithm engineering or deep learning roles.",
          "Interview focus: Assess feasibility of transitioning towards HCI design roles instead."
        ],
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
    uploadTime: "1d ago",
    fileType: "DOCX",
    status: "Shortlisted",
    rolesWeightings: {
      "Senior Fullstack Engineer": {
        score: 95,
        desc: "Highly qualified fullstack match",
        badges: ["Highly Recommended", "Algorithms Master", "Distributed Systems Expert"],
        skills: [
          { name: "Technical Proficiency", percentage: 98, isPrimary: true },
          { name: "Strategic Leadership", percentage: 88, isPrimary: true },
          { name: "Domain Knowledge", percentage: 92, isPrimary: false },
        ],
        strengths: ["Rust/C++ Low-level runtime optimization", "PostgreSQL database clustering", "Next.js routing patterns"],
        gaps: ["UI micro-animations styling", "Product design heuristics"],
        insights: "Marcus shows outstanding engineering foundations. Built highly responsive systems with clean modular structures.",
        atsStats: { score: 98, formatting: "Optimal", sectionCompleteness: "100%", readability: "Outstanding" },
        keywords: { found: ["Rust", "Node.js", "Docker", "SQL", "Distributed Systems", "Next.js"], missing: ["Figma", "Product Design Heuristics"] },
        grammar: { score: "98/100", errors: 1 },
        recruiterSummary: [
          "Superb systems builder with extreme low-level expertise.",
          "Highly analytical problem solver with clean code patterns.",
          "Interview focus: Explore his approaches to database horizontal scalability."
        ],
      },
      "Product Marketing Manager": {
        score: 42,
        desc: "Low match - engineering background fits poorly",
        badges: ["Technical Background", "Developer Advocate Potential"],
        skills: [
          { name: "Technical Proficiency", percentage: 90, isPrimary: true },
          { name: "Strategic Leadership", percentage: 48, isPrimary: false },
          { name: "Domain Knowledge", percentage: 38, isPrimary: false },
        ],
        strengths: ["Developer documentation parsing", "Technical feature alignment"],
        gaps: ["Customer acquisition metrics", "Campaign visual planning", "SEO analytics suites"],
        insights: "Strong engineering background. Would fit better in a Developer Relations or Solution Engineering track.",
        atsStats: { score: 65, formatting: "Passed", sectionCompleteness: "85%", readability: "Excellent" },
        keywords: { found: ["Collaboration", "Documentation"], missing: ["Marketing", "Campaigns", "NPS", "SEO"] },
        grammar: { score: "96/100", errors: 2 },
        recruiterSummary: [
          "Extremely technical background. Could bridge developer communities well.",
          "Not recommended for standard product marketing pipelines.",
          "Interview focus: Assess willingness to pivot towards technical product management."
        ],
      },
      "AI Research Scientist": {
        score: 84,
        desc: "High match - strong math & low-level competencies",
        badges: ["Low Level Expert", "Algorithms Focus"],
        skills: [
          { name: "Technical Proficiency", percentage: 92, isPrimary: true },
          { name: "Strategic Leadership", percentage: 70, isPrimary: false },
          { name: "Domain Knowledge", percentage: 88, isPrimary: true },
        ],
        strengths: ["CUDA kernel programming", "Vector database clustering", "Large-scale embeddings processing"],
        gaps: ["Pure mathematical proofs research", "Academic journal citation lists"],
        insights: "Very solid technical base. Marcus can implement model optimizations and handle cluster integrations with high autonomy.",
        atsStats: { score: 90, formatting: "Optimal", sectionCompleteness: "98%", readability: "Outstanding" },
        keywords: { found: ["Rust", "CUDA", "Vector Search", "Clustering", "Distributed Systems"], missing: ["PyTorch", "TensorFlow", "Math Thesis"] },
        grammar: { score: "98/100", errors: 1 },
        recruiterSummary: [
          "Superb systems background for scaling machine learning nodes.",
          "Strong model integration and optimization capabilities.",
          "Interview focus: Evaluate knowledge of LLM parameter-efficient fine-tuning."
        ],
      }
    },
    trajectory: [
      { year: "Year 1", candidateScore: 50, benchmarkScore: 45 },
      { year: "Year 2", candidateScore: 68, benchmarkScore: 52 },
      { year: "Year 3", candidateScore: 78, benchmarkScore: 60 },
      { year: "Year 4", candidateScore: 88, benchmarkScore: 68 },
      { year: "Year 5", candidateScore: 95, benchmarkScore: 75 },
    ],
  }
};

export default function ResumeAnalyzerPage() {
  const [candidates, setCandidates] = useState<Record<string, any>>(CANDIDATE_PROFILES);
  const [activeCandidateId, setActiveCandidateId] = useState("sarah-henderson");
  const [selectedRole, setSelectedRole] = useState("Senior Fullstack Engineer");
  const [jobDescription, setJobDescription] = useState(
    "We are looking for a senior engineer with strong React, Node.js, SQL, and Docker experience to orchestrate core API microservices."
  );

  // Upload progress indicators
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzingStep, setAnalyzingStep] = useState("");

  const handleUploadStart = (filename: string) => {
    setIsAnalyzing(true);
    setAnalyzingStep("Ingesting PDF layout structure...");
    
    setTimeout(() => {
      setAnalyzingStep("Executing OCR text matching...");
      setTimeout(() => {
        setAnalyzingStep("Running neural parsing alignment weights...");
        setTimeout(() => {
          setIsAnalyzing(false);
          toast.success(`Candidate ${filename} successfully analyzed!`);
        }, 1500);
      }, 1200);
    }, 1000);
  };

  const handleBulkUpload = () => {
    toast.info("Opening bulk ingestion interface... Supports zip/tar uploads up to 100MB.");
  };

  const handleExportReport = () => {
    toast.success(`Exporting full candidate matching matrix evaluation report for: ${currentCandidate.name}`);
  };

  // Memoize scan history listings
  const scanHistoryItems: ScanItem[] = useMemo(() => {
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

  const toolbarActions = (
    <>
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
    </>
  );

  return (
    <PageContainer
      title="ATS Intelligence Engine"
      description="Leverage neural parsing to extract, score, and analyze resumes against complex enterprise job descriptions with high precision."
      icon={<Sparkles className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
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
        <div className="col-span-12 lg:col-span-8 space-y-6">
          
          {/* Main Scoring Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
          </div>

          {/* Bento Stats: ATS formatting, keywords, grammar, recruiter summaries */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* ATS Format & Readability Audit */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-3 shadow-sm select-none">
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="size-4 text-green-400" />
                ATS Parser Audit
              </h4>
              <div className="space-y-2.5 pt-1 text-[11px] font-medium text-on-surface-variant">
                <div className="flex justify-between items-center">
                  <span>ATS Score:</span>
                  <span className="text-on-surface font-semibold">{currentWeightingDetails.atsStats?.score || 80}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Formatting Audit:</span>
                  <span className={cn(
                    "font-semibold",
                    currentWeightingDetails.atsStats?.formatting?.includes("Warning") ? "text-amber-400" : "text-green-400"
                  )}>{currentWeightingDetails.atsStats?.formatting || "Passed"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Readability Grade:</span>
                  <span className="text-on-surface font-semibold">{currentWeightingDetails.atsStats?.readability || "Excellent"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Section Completeness:</span>
                  <span className="text-on-surface font-semibold">{currentWeightingDetails.atsStats?.sectionCompleteness || "90%"}</span>
                </div>
              </div>
            </div>

            {/* Keyword Density Checks */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-3 shadow-sm select-none">
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                <Search className="size-4 text-primary" />
                Keyword Matcher
              </h4>
              <div className="space-y-2 pt-1 text-[10px]">
                <div>
                  <span className="text-green-400 font-bold uppercase tracking-wider">Keywords Found:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {currentWeightingDetails.keywords?.found?.map((kw: string) => (
                      <span key={kw} className="bg-green-500/10 border border-green-500/20 text-green-400 px-1.5 py-0.5 rounded text-[8px] font-semibold">{kw}</span>
                    ))}
                  </div>
                </div>
                <div className="pt-1.5">
                  <span className="text-amber-400 font-bold uppercase tracking-wider">Missing Keywords:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {currentWeightingDetails.keywords?.missing?.map((kw: string) => (
                      <span key={kw} className="bg-amber-500/10 border border-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[8px] font-semibold">{kw}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Readability & Grammar Audit */}
            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-3 shadow-sm select-none">
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="size-4 text-tertiary" />
                Quality Audit
              </h4>
              <div className="space-y-2.5 pt-1 text-[11px] font-medium text-on-surface-variant">
                <div className="flex justify-between items-center">
                  <span>Grammar Quality Index:</span>
                  <span className="text-green-400 font-bold">{currentWeightingDetails.grammar?.score || "98/100"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Stylistic Errors:</span>
                  <span className="text-on-surface font-semibold">{currentWeightingDetails.grammar?.errors || 0} items</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Plagiarism Index:</span>
                  <span className="text-green-400 font-bold">1% (Safe)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Tone / Sentiment:</span>
                  <span className="text-on-surface font-semibold">Professional</span>
                </div>
              </div>
            </div>

          </div>

          {/* AI generated Summaries */}
          <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-4 shadow-sm select-text">
            <div>
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5 mb-1 select-none">
                <Sparkles className="size-4.5 text-primary" />
                Recruiter Evaluation Summary
              </h4>
              <p className="text-[10px] text-on-surface-variant select-none">Generated via autonomous profile matching pipeline.</p>
            </div>
            <div className="space-y-2.5">
              {currentWeightingDetails.recruiterSummary?.map((bullet: string, index: number) => (
                <div key={index} className="flex gap-2.5 items-start">
                  <ChevronRight className="size-4 text-primary shrink-0 mt-0.5 select-none" />
                  <p className="text-xs text-on-surface-variant font-medium leading-relaxed">{bullet}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Trajectory comparison timeline */}
          <ExperienceTrajectory 
            data={currentCandidate.trajectory}
          />

          {/* Recent candidate scans lookup index */}
          <RecentScans 
            scans={scanHistoryItems}
            activeScanId={activeCandidateId}
            onSelectScan={setActiveCandidateId}
          />

        </div>
      </div>
    </PageContainer>
  );
}
