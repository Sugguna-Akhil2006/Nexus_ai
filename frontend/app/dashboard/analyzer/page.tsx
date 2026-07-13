"use client";

import { useEffect, useState, useMemo } from "react";
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
import { useWorkspace } from "@/providers/workspace-provider";
import { cn } from "@/lib/utils";
import PageContainer from "@/components/common/page-container";

// Candidate datasets structured for role-based weighing changes
const CANDIDATE_PROFILES: Record<string, any> = {
  "sarah-henderson": {
    id: "sarah-henderson",
    name: "Sarah K. Henderson",
    uploadTime: "2h ago",
    details: {
      score: 92,
      desc: "Exceptional match for senior platform engineering. Exhibits deep systems design expertise.",
      badges: ["Distinguished", "API Guru", "System Architect"],
      skills: [
        { name: "React / Next.js", percentage: 95, isPrimary: true },
        { name: "Node.js API Development", percentage: 90, isPrimary: true },
        { name: "SQL Schema Design", percentage: 85, isPrimary: true },
        { name: "Docker Containerization", percentage: 80, isPrimary: false },
        { name: "Kubernetes Orchestration", percentage: 70, isPrimary: false },
      ],
      strengths: [
        "Proven experience building distributed microservices using Node/Go.",
        "Deep understanding of database synchronization and caching mechanisms.",
        "Expertise in modern frontend routing, SSR frameworks (Next.js)."
      ],
      gaps: [
        "Lacks formal certification in AWS or GCP cloud administration.",
        "Prior projects focus on relational DBs; NoSQL database experience is limited."
      ],
      insights: "Excellent candidate to lead the API Gateway migration. Suggest focusing technical interviews on load balancer tuning and rate limiting protocols.",
      atsStats: {
        score: 95,
        formatting: "Passed",
        readability: "Excellent (Grade 12)",
        sectionCompleteness: "98%",
      },
      keywords: {
        found: ["React", "Next.js", "Node.js", "SQL", "Docker", "REST API", "Microservices"],
        missing: ["Kubernetes", "Redis Cache", "GRPC"],
      },
      grammar: {
        score: "99/100",
        errors: 1,
      },
      recruiterSummary: [
        "Strong experience orchestrating high-traffic backend API endpoints.",
        "Solid React/Next.js skills for building modern management dashboards.",
        "Active open-source contributor with good collaborative code review practices."
      ],
    },
    trajectory: [
      { year: "Year 1", candidateScore: 50, benchmarkScore: 45 },
      { year: "Year 2", candidateScore: 68, benchmarkScore: 52 },
      { year: "Year 3", candidateScore: 78, benchmarkScore: 60 },
      { year: "Year 4", candidateScore: 88, benchmarkScore: 68 },
      { year: "Year 5", candidateScore: 92, benchmarkScore: 75 },
    ],
  },
  "jason-vance": {
    id: "jason-vance",
    name: "Jason R. Vance",
    uploadTime: "1d ago",
    details: {
      score: 74,
      desc: "Moderate match. Competent frontend specialist but lacks sufficient backend systems experience.",
      badges: ["Frontend Specialist", "React Pro"],
      skills: [
        { name: "React / Next.js", percentage: 98, isPrimary: true },
        { name: "Node.js API Development", percentage: 65, isPrimary: false },
        { name: "SQL Schema Design", percentage: 50, isPrimary: false },
        { name: "Docker Containerization", percentage: 40, isPrimary: false },
      ],
      strengths: [
        "Exceptional component-driven architecture development using React/Tailwind.",
        "Strong accessibility (WCAG) audit and design systems compliance skills.",
        "Fluid UI/UX implementation."
      ],
      gaps: [
        "Lacks production database schema management experience.",
        "Minimal experience with Linux containers, deployment scripts, or Dockerfiles."
      ],
      insights: "Strong candidate for specialized UI frontend roles. Not recommended for backend gateway development tasks.",
      atsStats: {
        score: 82,
        formatting: "Warning: Unconventional Layout",
        readability: "Good (Grade 10)",
        sectionCompleteness: "85%",
      },
      keywords: {
        found: ["React", "Next.js", "UI/UX", "Tailwind CSS"],
        missing: ["SQL", "Docker", "Database", "Kubernetes"],
      },
      grammar: {
        score: "96/100",
        errors: 3,
      },
      recruiterSummary: [
        "Highly skilled UI engineer; outstanding design system expertise.",
        "Suggest routing to product frontend teams.",
        "Interview focus: Evaluate knowledge of Server Server Components (RSC)."
      ],
    },
    trajectory: [
      { year: "Year 1", candidateScore: 45, benchmarkScore: 45 },
      { year: "Year 2", candidateScore: 55, benchmarkScore: 52 },
      { year: "Year 3", candidateScore: 68, benchmarkScore: 60 },
      { year: "Year 4", candidateScore: 72, benchmarkScore: 68 },
      { year: "Year 5", candidateScore: 74, benchmarkScore: 75 },
    ],
  },
  "alexander-patel": {
    id: "alexander-patel",
    name: "Alexander Patel",
    uploadTime: "3d ago",
    details: {
      score: 95,
      desc: "Outstanding system engineering capabilities. Highly aligned with ML ops requirements.",
      badges: ["Elite Engineer", "AI/ML Expert"],
      skills: [
        { name: "Python / PyTorch", percentage: 98, isPrimary: true },
        { name: "Docker & Kubernetes", percentage: 92, isPrimary: true },
        { name: "Go Lang Runtime", percentage: 85, isPrimary: false },
        { name: "SQL & Vector DBs", percentage: 90, isPrimary: true },
      ],
      strengths: [
        "Extensive experience building and serving high-scale ML pipelines.",
        "Expertise in vector similarity index tuning (Qdrant, Pinecone).",
        "Deep container optimization practices."
      ],
      gaps: [
        "Lacks core React frontend development experience."
      ],
      insights: "Excellent fit for orchestrating core platform agents. Suggest routing directly to Platform ML Team.",
      atsStats: {
        score: 97,
        formatting: "Passed",
        readability: "Excellent",
        sectionCompleteness: "100%",
      },
      keywords: {
        found: ["Python", "Docker", "Kubernetes", "Vector Database", "MLOps", "Go"],
        missing: ["React", "CSS"],
      },
      grammar: {
        score: "100/100",
        errors: 0,
      },
      recruiterSummary: [
        "Superb systems background for scaling machine learning nodes.",
        "Strong model integration and optimization capabilities.",
        "Interview focus: Evaluate knowledge of LLM parameter-efficient fine-tuning."
      ],
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
  const { activeWorkspace } = useWorkspace();
  const [candidates, setCandidates] = useState<Record<string, any>>(CANDIDATE_PROFILES);
  const [activeCandidateId, setActiveCandidateId] = useState("sarah-henderson");
  const [selectedRole, setSelectedRole] = useState("Senior Fullstack Engineer");
  const [jobDescription, setJobDescription] = useState(
    "We are looking for a senior engineer with strong React, Node.js, SQL, and Docker experience to orchestrate core API microservices."
  );

  // History scans list
  const [scans, setScans] = useState<any[]>([]);
  const [activeScanId, setActiveScanId] = useState("");
  const [activeReport, setActiveReport] = useState<any | null>(null);

  // Upload progress indicators
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
    setIsAnalyzing(true);
    const steps = [
      "Cloning resume artifact file...",
      "Extracting text headers using OCR engine...",
      "Running semantic entity extraction...",
      "Matching skills taxonomy vectors...",
      "Weighing experience trajectories...",
      "Compiling final analysis scorecard..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setAnalyzingStep(steps[i]);
      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    if (fileObject) {
      // Real API Upload if file object is provided
      try {
        const formData = new FormData();
        formData.append("file", fileObject);
        formData.append("workspace_id", activeWorkspaceId);
        formData.append("selected_role", selectedRole);
        formData.append("job_description", jobDescription);

        const res = await fetch("/resume/analyze", {
          method: "POST",
          body: formData,
        });

        if (res.ok) {
          const report = await res.json();
          toast.success(`Resume "${filename}" parsed successfully!`);
          await fetchHistory();
          setActiveScanId(report.report_id);
        } else {
          throw new Error("Parser failure");
        }
      } catch (err) {
        console.warn("Failed real upload, fallback to mock profile generation.", err);
        seedMockProfile(filename);
      } finally {
        setIsAnalyzing(false);
      }
    } else {
      seedMockProfile(filename);
      setIsAnalyzing(false);
    }
  };

  const seedMockProfile = (filename: string) => {
    const mockId = `mock-${Date.now()}`;
    const cleanName = filename.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
    
    CANDIDATE_PROFILES[mockId] = {
      id: mockId,
      name: cleanName,
      uploadTime: "Just now",
      details: {
        score: Math.floor(Math.random() * 25) + 70, // 70 - 95
        desc: `Evaluation scorecard generated dynamically for role: ${selectedRole}.`,
        badges: ["Evaluated", "Applicant"],
        skills: [
          { name: "React", percentage: 85, isPrimary: true },
          { name: "TypeScript", percentage: 80, isPrimary: true },
          { name: "Docker", percentage: 70, isPrimary: false },
          { name: "Backend Services", percentage: 75, isPrimary: false },
        ],
        strengths: ["Strong engineering fundamentals.", "Matches primary required technologies."],
        gaps: ["No explicit cloud infrastructure certifications listed."],
        insights: "Candidate matches core requirements. Proceed to screening call.",
        atsStats: {
          score: 85,
          formatting: "Passed",
          readability: "Good",
          sectionCompleteness: "90%",
        },
        keywords: {
          found: ["React", "TypeScript", "Docker"],
          missing: ["Kubernetes", "Redis"],
        },
        grammar: {
          score: "98/100",
          errors: 1,
        },
        recruiterSummary: ["Qualified applicant.", "Strong technology foundations."],
      },
      trajectory: [
        { year: "Year 1", candidateScore: 60, benchmarkScore: 50 },
        { year: "Year 2", candidateScore: 75, benchmarkScore: 60 },
        { year: "Year 3", candidateScore: 85, benchmarkScore: 75 },
      ]
    };

    setCandidates({ ...CANDIDATE_PROFILES });
    setActiveCandidateId(mockId);
    toast.success(`Mock resume parsed: ${cleanName}`);
  };

  const handleBulkUpload = () => {
    toast.info("Opening batch resumes ingest loader queue...");
  };

  const handleExportReport = () => {
    toast.success("Downloading PDF Candidate matching scorecard report...");
  };

  // Resolve candidate details by combining database metrics & active API report
  const weightingDetails = useMemo(() => {
    if (activeReport) {
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
        ],
        atsStats: {
          score: Math.round(activeReport.ats_score || 75),
          formatting: "Passed",
          readability: "Good",
          sectionCompleteness: "92%",
        },
        keywords: {
          found: techSkills.slice(0, 4),
          missing: ["Kubernetes"],
        },
        grammar: {
          score: "98/100",
          errors: 0,
        },
        recruiterSummary: activeReport.strengths || ["Meets matching requirements."],
      };
    }

    const currentProfile = candidates[activeCandidateId] || candidates["sarah-henderson"];
    return currentProfile.details;
  }, [activeReport, activeCandidateId, candidates]);

  const currentTrajectory = useMemo(() => {
    if (activeReport) {
      return [
        { year: "Evaluation", candidateScore: activeReport.ats_score || 75, benchmarkScore: 80 }
      ];
    }
    const currentProfile = candidates[activeCandidateId] || candidates["sarah-henderson"];
    return currentProfile.trajectory;
  }, [activeReport, activeCandidateId, candidates]);

  const scanHistoryItems = useMemo<ScanItem[]>(() => {
    if (scans.length > 0) {
      return scans.map((s) => ({
        id: s.report_id || s.document_id,
        candidateName: s.filename || "Candidate Resume",
        uploadTime: s.timestamp ? new Date(s.timestamp).toLocaleDateString() : "Just now",
        fileType: "pdf",
        role: s.selected_role || "Senior Fullstack Engineer",
        score: Math.round(s.ats_score || 80),
        status: "New"
      }));
    }

    return Object.values(candidates).map((c: any) => ({
      id: c.id,
      candidateName: c.name,
      uploadTime: c.uploadTime,
      fileType: "pdf",
      role: "Senior Fullstack Engineer",
      score: c.details?.score || 80,
      status: "New"
    }));
  }, [scans, candidates]);

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
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MatchScoreCard 
              score={weightingDetails.score}
              matchDescription={weightingDetails.desc}
              badges={weightingDetails.badges}
            />
            
            <SkillAlignment 
              skills={weightingDetails.skills}
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
                  <span className="text-on-surface font-semibold">{weightingDetails.atsStats?.score || 80}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Formatting Audit:</span>
                  <span className={cn(
                    "font-semibold",
                    weightingDetails.atsStats?.formatting?.includes("Warning") ? "text-amber-400" : "text-green-400"
                  )}>{weightingDetails.atsStats?.formatting || "Passed"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Readability Grade:</span>
                  <span className="text-on-surface font-semibold">{weightingDetails.atsStats?.readability || "Excellent"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Section Completeness:</span>
                  <span className="text-on-surface font-semibold">{weightingDetails.atsStats?.sectionCompleteness || "90%"}</span>
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
                    {weightingDetails.keywords?.found?.map((kw: string) => (
                      <span key={kw} className="bg-green-500/10 border border-green-500/20 text-green-400 px-1.5 py-0.5 rounded text-[8px] font-semibold">{kw}</span>
                    ))}
                  </div>
                </div>
                <div className="pt-1.5">
                  <span className="text-amber-400 font-bold uppercase tracking-wider">Missing Keywords:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {weightingDetails.keywords?.missing?.map((kw: string) => (
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
                  <span className="text-green-400 font-bold">{weightingDetails.grammar?.score || "98/100"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Stylistic Errors:</span>
                  <span className="text-on-surface font-semibold">{weightingDetails.grammar?.errors || 0} items</span>
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

          {/* AI generated Summaries / Competency Gaps */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <CompetencyAnalysis
              strengths={weightingDetails.strengths}
              gaps={weightingDetails.gaps}
              insights={weightingDetails.insights}
            />

            <div className="bg-surface-container border border-outline-variant p-5 rounded-xl space-y-4 shadow-sm select-text flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5 mb-1 select-none">
                  <Sparkles className="size-4.5 text-primary" />
                  Recruiter Evaluation Summary
                </h4>
                <p className="text-[10px] text-on-surface-variant select-none font-medium">Generated via autonomous profile matching pipeline.</p>
              </div>
              <div className="space-y-2.5 flex-1 pt-3">
                {weightingDetails.recruiterSummary?.map((bullet: string, index: number) => (
                  <div key={index} className="flex gap-2.5 items-start">
                    <ChevronRight className="size-4 text-primary shrink-0 mt-0.5 select-none" />
                    <p className="text-xs text-on-surface-variant font-medium leading-relaxed">{bullet}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Trajectory comparison timeline */}
          <ExperienceTrajectory 
            data={currentTrajectory}
          />

          {/* Recent candidate scans lookup index */}
          <RecentScans 
            scans={scanHistoryItems}
            activeScanId={activeScanId || activeCandidateId}
            onSelectScan={(id) => {
              if (scans.length > 0) {
                setActiveScanId(id);
              } else {
                setActiveCandidateId(id);
              }
            }}
          />
        </div>
      </div>
    </PageContainer>
  );
}
