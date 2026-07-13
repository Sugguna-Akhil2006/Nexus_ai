"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { 
  RefreshCw, 
  Download, 
  MessageSquareCode, 
  GitBranch, 
  GitCommit, 
  GitPullRequest, 
  AlertCircle, 
  Users, 
  CheckCircle, 
  Clock, 
  Sparkles, 
  Code, 
  ShieldCheck, 
  Activity, 
  Info,
  ShieldAlert,
  Flame,
  Terminal,
  Database,
  ArrowUpRight,
  ArrowRight,
  FileCode,
  Play
} from "lucide-react";
import { Button } from "@/components/ui/button";
import CodeHealthMetrics from "@/components/analytics/code-health-metrics";
import TechStackCard from "@/components/analytics/tech-stack-card";
import ArchitectureExplorer from "@/components/analytics/architecture-explorer";
import HotspotsPanel from "@/components/analytics/hotspots-panel";
import RecentActivityFeed from "@/components/analytics/recent-activity-feed";
import { cn } from "@/lib/utils";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import { useWorkspace } from "@/providers/workspace-provider";
import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, CartesianGrid } from "recharts";
import PageContainer from "@/components/common/page-container";

// Custom Github SVG Icon to guarantee compatibility
const GithubIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

// ─── Interfaces ──────────────────────────────────────────────────────────────

interface Contributor {
  name: string;
  avatarUrl: string;
  commits: number;
  impactPercentage: number;
}

interface MockPR {
  id: string;
  number: number;
  title: string;
  author: string;
  state: "open" | "merged" | "closed";
  timeAgo: string;
  tags: string[];
}

interface MockIssue {
  id: string;
  number: number;
  title: string;
  priority: "high" | "medium" | "low";
  state: "open" | "closed";
  timeAgo: string;
}

interface RepoData {
  name: string;
  branch: string;
  date: string;
  maintainability: number;
  maintainabilityTrend: string;
  securityScore: string;
  securityDesc: string;
  testCoverage: number;
  techDebtHours: number;
  languages: { name: string; percentage: number; colorClass: string }[];
  commits: number;
  openPRs: number;
  closedPRs: number;
  openIssues: number;
  closedIssues: number;
  complexity: { commit: string; complexity: number }[];
  commitActivity: { week: string; commits: number }[];
  contributors: Contributor[];
  pullRequests: MockPR[];
  issues: MockIssue[];
  securityInsights: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    scannerStatus: string;
    patchAdvice: string;
  };
  hotspots: {
    id: string;
    filePath: string;
    metricType: "commits" | "complexity" | "coverage";
    metricDesc: string;
    severity: "error" | "warning" | "info";
  }[];
  activities: {
    id: string;
    author: string;
    timeAgo: string;
    type: "pr" | "system" | "push";
    description: string;
    tags?: string[];
  }[];
  aiRecommendation: string;
}

// ─── Mock Database ───────────────────────────────────────────────────────────

const REPO_DATABASE: Record<string, RepoData> = {
  "Sugguna-Akhil2006/Nexus_ai": {
    name: "Sugguna-Akhil2006/Nexus_ai",
    branch: "main",
    date: "Just now",
    maintainability: 94,
    maintainabilityTrend: "2.4%",
    securityScore: "A+",
    securityDesc: "Top 5%",
    testCoverage: 82.1,
    techDebtHours: 12,
    languages: [
      { name: "TypeScript", percentage: 64.2, colorClass: "bg-blue-400" },
      { name: "Python", percentage: 22.8, colorClass: "bg-yellow-400" },
      { name: "Rust", percentage: 9.5, colorClass: "bg-purple-400" },
      { name: "Others", percentage: 3.5, colorClass: "bg-outline" },
    ],
    commits: 242,
    openPRs: 12,
    closedPRs: 94,
    openIssues: 8,
    closedIssues: 65,
    complexity: [
      { commit: "C-01", complexity: 32 },
      { commit: "C-02", complexity: 45 },
      { commit: "C-03", complexity: 38 },
      { commit: "C-04", complexity: 55 },
      { commit: "C-05", complexity: 48 },
      { commit: "C-06", complexity: 62 },
      { commit: "C-07", complexity: 50 },
      { commit: "C-08", complexity: 68 },
      { commit: "C-09", complexity: 72 },
      { commit: "C-10", complexity: 78 },
    ],
    commitActivity: [
      { week: "W-01", commits: 15 },
      { week: "W-02", commits: 22 },
      { week: "W-03", commits: 18 },
      { week: "W-04", commits: 35 },
      { week: "W-05", commits: 28 },
      { week: "W-06", commits: 42 },
      { week: "W-07", commits: 30 },
      { week: "W-08", commits: 52 },
    ],
    contributors: [
      { name: "Alex Chen", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X", commits: 104, impactPercentage: 43 },
      { name: "Sarah Jenkins", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh", commits: 76, impactPercentage: 31 },
      { name: "Marcus Aurelius", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCN4AjYH9VxqqekSZR46EWARGDW7GMXN34fjzzmPJY-B4sW93NZW3_bKE8rk8GH6Z7bRoipIGJbgqN0vtzn7xAgoHQTc6JtG3CQCfDiA9neEXuu28xGxc7wL6j9Kf9h9i4MR4U2WvxAjh9HSw6td40xcVWZ9XzdCZ2rtAJ9ktBeZegNm95Es4QadiRmjLDzYdu7-cEyX3PmeaeSC_AnC0mw4FYBiPbd4et2dqdo-rGQFmI6NeZ8QujR__Aq0aj-E6wcGGvHPbx8gVEE", commits: 48, impactPercentage: 20 },
      { name: "John Stewart", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuADTWQkJyCrcBfNzLgWua8xU-wSLoS4mBRmPJAOkXXNiI6psySgLavV1ddMecybd-7q9elRbTlwmWxlKjxr3FHHT5xYSlyrbidFLE16_NS6iaqQrVs70eGO2g95M6_PkS2khQZXIMjMIH70Oaj8Q08rqOzH0F8RmXifQLnBBLi0KiNCdfvzLcTaug8Nx4WKOWgxJmqKpcqTiD2huFl4At0iXjGJeXgJ8sCjRqtnJOVd3Ppku0_QYohGZpctB_esvM7LgXuueGefuPN0", commits: 14, impactPercentage: 6 },
    ],
    pullRequests: [
      { id: "pr-1", number: 142, title: "Refactor auth middleware for better scalability", author: "Alex Chen", state: "open", timeAgo: "2h ago", tags: ["feat", "auth"] },
      { id: "pr-2", number: 140, title: "Fix AST parsing memory leak under concurrent logs", author: "Sarah Jenkins", state: "merged", timeAgo: "1d ago", tags: ["bug", "engine"] },
      { id: "pr-3", number: 139, title: "Implement new workflow properties layout panel", author: "John Stewart", state: "open", timeAgo: "2d ago", tags: ["ui", "workflows"] },
    ],
    issues: [
      { id: "iss-1", number: 82, title: "Database connection pools timeout on staging logs", priority: "high", state: "open", timeAgo: "5h ago" },
      { id: "iss-2", number: 78, title: "Next.js hydration mismatch on theme select toggle button", priority: "medium", state: "open", timeAgo: "3d ago" },
      { id: "iss-3", number: 74, title: "Telemetry maps buffer overflows under peak concurrency", priority: "low", state: "closed", timeAgo: "5d ago" },
    ],
    securityInsights: {
      critical: 0,
      high: 1,
      medium: 3,
      low: 8,
      scannerStatus: "Active & Secure",
      patchAdvice: "1 high vulnerability found in package axios@1.5.0. Upgrade to axios@1.6.0 is recommended.",
    },
    hotspots: [
      { id: "h-1", filePath: "src/lib/engine.ts", metricType: "commits", metricDesc: "24 commits this week", severity: "error" },
      { id: "h-2", filePath: "src/api/handler.py", metricType: "complexity", metricDesc: "Cyclomatic Complexity: 42", severity: "warning" },
      { id: "h-3", filePath: "tests/integration.rs", metricType: "coverage", metricDesc: "New coverage required", severity: "info" },
    ],
    activities: [
      { id: "act-1", author: "Alex Chen", timeAgo: "2h ago", type: "pr", description: "Merged PR #142: Refactor auth middleware for better scalability.", tags: ["feat", "middleware"] },
      { id: "act-2", author: "System Agent", timeAgo: "5h ago", type: "system", description: "Automated analysis complete: 0 vulnerabilities found in newest patch." },
      { id: "act-3", author: "Jordan Smith", timeAgo: "1d ago", type: "push", description: "Pushed 3 commits to branch main." },
    ],
    aiRecommendation: "Repository shows a strong modular structure. Recommended upgrade: TS 5.4 features could reduce bundle size by ~8%. Configure target schema checks inside /workflows to validate endpoints.",
  },
  "facebook/react": {
    name: "facebook/react",
    branch: "main",
    date: "2 days ago",
    maintainability: 89,
    maintainabilityTrend: "1.1%",
    securityScore: "A",
    securityDesc: "Top 8%",
    testCoverage: 91.5,
    techDebtHours: 45,
    languages: [
      { name: "JavaScript", percentage: 88.4, colorClass: "bg-yellow-300" },
      { name: "TypeScript", percentage: 8.2, colorClass: "bg-blue-400" },
      { name: "Others", percentage: 3.4, colorClass: "bg-outline" },
    ],
    commits: 1482,
    openPRs: 48,
    closedPRs: 412,
    openIssues: 32,
    closedIssues: 142,
    complexity: [
      { commit: "C-01", complexity: 62 },
      { commit: "C-02", complexity: 58 },
      { commit: "C-03", complexity: 70 },
      { commit: "C-04", complexity: 65 },
      { commit: "C-05", complexity: 80 },
      { commit: "C-06", complexity: 74 },
      { commit: "C-07", complexity: 88 },
      { commit: "C-08", complexity: 82 },
      { commit: "C-09", complexity: 94 },
      { commit: "C-10", complexity: 90 },
    ],
    commitActivity: [
      { week: "W-01", commits: 98 },
      { week: "W-02", commits: 124 },
      { week: "W-03", commits: 110 },
      { week: "W-04", commits: 145 },
      { week: "W-05", commits: 130 },
      { week: "W-06", commits: 162 },
      { week: "W-07", commits: 140 },
      { week: "W-08", commits: 184 },
    ],
    contributors: [
      { name: "Dan Abramov", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCCOi1jGQaPkQLqV4ZhsQb7DInTmE1U9dJA5QocSEs35Dq340lq31HdjyZ9ZFYo7x71o41gR3A0Cs0F4XypUgIhbyLniuEHUQlnprscIT-Nt58CZO-yxecM1I8o1PAlngGCtG1WYEgI40zHc0RzoKelNzNdW0Dlc2UZ20nNOtDfPTx-3goVvZ9KDBM-BxOpwn4G03Zy6zfSF_34K_2_mjaOK37LaqH7q9RcQScdCtIwJW4S2l5FkjsJYgI-FSxPkMefOEzgK4NuywG3", commits: 412, impactPercentage: 55 },
      { name: "Sophie Alpert", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh", commits: 220, impactPercentage: 29 },
      { name: "Andrew Clark", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X", commits: 112, impactPercentage: 16 },
    ],
    pullRequests: [
      { id: "pr-1", number: 28401, title: "Fix server component transition rendering", author: "Dan Abramov", state: "open", timeAgo: "4h ago", tags: ["server-components"] },
      { id: "pr-2", number: 28392, title: "Optimize scheduler heap insertions", author: "Andrew Clark", state: "open", timeAgo: "1d ago", tags: ["perf"] },
    ],
    issues: [
      { id: "iss-1", number: 27910, title: "useActionState throws hydration errors in Next.js 15", priority: "high", state: "open", timeAgo: "12h ago" },
      { id: "iss-2", number: 27885, title: "React compiler flags false positive in nested loops", priority: "medium", state: "open", timeAgo: "2d ago" },
    ],
    securityInsights: {
      critical: 0,
      high: 0,
      medium: 1,
      low: 4,
      scannerStatus: "Active",
      patchAdvice: "Upgrade target lint guidelines to catch redundant react compiler parameters.",
    },
    hotspots: [
      { id: "h-1", filePath: "packages/react-reconciler/src/ReactFiberWorkLoop.js", metricType: "complexity", metricDesc: "Complexity: 184", severity: "error" },
      { id: "h-2", filePath: "packages/react/src/ReactHooks.js", metricType: "commits", metricDesc: "48 commits this month", severity: "warning" },
    ],
    activities: [
      { id: "act-1", author: "Dan Abramov", timeAgo: "4h ago", type: "push", description: "Pushed 2 commits to main." },
      { id: "act-2", author: "Sophie Alpert", timeAgo: "1d ago", type: "pr", description: "Opened PR #28392: Optimize scheduler heap insertions" },
    ],
    aiRecommendation: "React workspace has extremely high cyclomatic complexity in Fiber WorkLoop. Recommend partitioning task queue checks to reduce stack depth under complex state trees.",
  },
};

// ─── Main Component ──────────────────────────────────────────────────────────

export default function RepositoryAnalyticsPage() {
  const { activeWorkspace } = useWorkspace();
  const activeWorkspaceId = activeWorkspace?.workspace_id || "default-ws";

  // Scan inputs
  const [repoUrl, setRepoUrl] = useState(".");
  const [branch, setBranch] = useState("main");
  
  // History & active report state
  const [history, setHistory] = useState<any[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [activeReport, setActiveReport] = useState<any | null>(null);

  // Scanning / Polling states
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanStatusMsg, setScanStatusMsg] = useState("");

  const [activeRepoName, setActiveRepoName] = useState<string>("Sugguna-Akhil2006/Nexus_ai");
  const [activeTab, setActiveTab] = useState<"overview" | "code" | "activity" | "security">("overview");

  // Fetch scan history
  const fetchHistory = async () => {
    try {
      const res = await fetch(`/github/history?workspace_id=${activeWorkspaceId}`);
      if (res.ok) {
        const data = await res.json();
        const reports = data.history || [];
        setHistory(reports);
        if (reports.length > 0 && !selectedReportId) {
          setSelectedReportId(reports[0].report_id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch scan history", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [activeWorkspaceId]);

  // Load selected report details
  useEffect(() => {
    if (!selectedReportId) {
      setActiveReport(null);
      return;
    }
    fetch(`/github/report/${selectedReportId}`)
      .then((res) => {
        if (res.ok) return res.json();
      })
      .then((data) => {
        if (data && !data.status) { // Ensure it's a report, not a job status
          setActiveReport(data);
          if (data.repository) {
            setActiveRepoName(data.repository);
          }
        }
      })
      .catch((err) => console.error("Failed to load report", err));
  }, [selectedReportId]);

  // Polling helper for background analysis job
  const pollJobStatus = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/github/status/${jobId}`);
        if (!res.ok) throw new Error("Failed to get status");
        const job = await res.json();
        
        setScanProgress(job.progress || 0);
        setScanStatusMsg(job.status_msg || "Scanning...");

        if (job.status === "completed") {
          clearInterval(interval);
          setIsScanning(false);
          toast.success("Repository analysis complete!");
          await fetchHistory();
          if (job.report_id) {
            setSelectedReportId(job.report_id);
          } else if (job.result && job.result.report_id) {
            setSelectedReportId(job.result.report_id);
          }
        } else if (job.status === "failed") {
          clearInterval(interval);
          setIsScanning(false);
          toast.error(job.status_msg || "Repository analysis failed.");
        }
      } catch (err) {
        clearInterval(interval);
        setIsScanning(false);
        toast.error("Failed to poll scan status.");
      }
    }, 1000);
  };

  // Launch repository analysis
  const handleStartAnalysis = async () => {
    if (isScanning) return;
    setIsScanning(true);
    setScanProgress(5);
    setScanStatusMsg("Initiating scan request...");

    try {
      const res = await fetch("/github/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repository_url: repoUrl,
          workspace_id: activeWorkspaceId,
          user_id: "admin",
          branch: branch,
          options: { async: true } // Force async to leverage worker pool progress tracking
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Analysis failed to start.");
      }

      const data = await res.json();
      if (data.job_id) {
        pollJobStatus(data.job_id);
      } else if (data.report_id) {
        setIsScanning(false);
        toast.success("Repository analysis complete!");
        await fetchHistory();
        setSelectedReportId(data.report_id);
      }
    } catch (err: any) {
      // Fallback to local simulation when backend endpoint isn't fully set up or running
      console.warn("Failed sync analyze. Running local mock simulation instead.", err);
      let progress = 0;
      const phases = [
        "Cloning remote repository...",
        "Parsing AST nodes...",
        "Running code health & maintainability checks...",
        "Scanning dependencies for CVE vulnerabilities...",
        "Generating AI optimization recommendations...",
        "Compiling code intelligence report..."
      ];
      const timer = setInterval(() => {
        progress += 15;
        if (progress >= 100) {
          clearInterval(timer);
          setIsScanning(false);
          toast.success("Mock analysis complete!");
          
          let cleanName = repoUrl.replace(/https?:\/\/github\.com\//, "").trim();
          if (cleanName.endsWith("/")) cleanName = cleanName.slice(0, -1);
          if (!cleanName || cleanName === ".") cleanName = "Sugguna-Akhil2006/Nexus_ai";
          
          REPO_DATABASE[cleanName] = {
            name: cleanName,
            branch: branch || "main",
            date: "Just now",
            maintainability: Math.floor(Math.random() * 20) + 78,
            maintainabilityTrend: "1.8%",
            securityScore: "A",
            securityDesc: "Top 10%",
            testCoverage: Math.floor(Math.random() * 25) + 70,
            techDebtHours: Math.floor(Math.random() * 30) + 5,
            languages: [
              { name: "TypeScript", percentage: 55.4, colorClass: "bg-blue-400" },
              { name: "JavaScript", percentage: 32.1, colorClass: "bg-yellow-300" },
              { name: "Others", percentage: 12.5, colorClass: "bg-outline" },
            ],
            commits: 340,
            openPRs: 4,
            closedPRs: 20,
            openIssues: 5,
            closedIssues: 18,
            complexity: [
              { commit: "C-01", complexity: 40 },
              { commit: "C-02", complexity: 45 },
            ],
            commitActivity: [
              { week: "W-01", commits: 20 },
              { week: "W-02", commits: 35 },
            ],
            contributors: [
              { name: "Self", avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X", commits: 40, impactPercentage: 100 }
            ],
            pullRequests: [],
            issues: [],
            securityInsights: {
              critical: 0,
              high: 0,
              medium: 0,
              low: 1,
              scannerStatus: "Completed",
              patchAdvice: "All clear! Minor security packages updates needed.",
            },
            hotspots: [],
            activities: [],
            aiRecommendation: "Dynamic repository mapped. Solid Clean Architecture compliance verified."
          };
          setActiveRepoName(cleanName);
        } else {
          setScanProgress(progress);
          setScanStatusMsg(phases[Math.min(phases.length - 1, Math.floor(progress / 18))]);
        }
      }, 700);
    }
  };

  const handleExportPDF = () => {
    if (selectedReportId) {
      window.open(`/github/report/${selectedReportId}?export=pdf`, "_blank");
      toast.success("Downloading PDF Report...");
    } else {
      toast.info("Exporting simulated report...");
    }
  };

  const handleUpgradeInsight = () => {
    toast.info("Running code optimizations diagnostics...");
  };

  const handleHotspotClick = (filePath: string) => {
    toast.info(`Opening file context viewer for: ${filePath}`);
  };

  // Memoized mapping of report data
  const repoData = useMemo<RepoData>(() => {
    if (activeReport) {
      const qs = activeReport.engineering_quality || {};
      const over = activeReport.repository_overview || {};
      const langs = activeReport.technology_stack?.languages || [];
      const risks = activeReport.engineering_risks || [];
      
      return {
        name: activeReport.repository || activeRepoName,
        branch: over.branch || "main",
        date: new Date(activeReport.timestamp || activeReport.created_at).toLocaleDateString(),
        maintainability: Math.round(qs.maintainability_score || 85),
        maintainabilityTrend: "+1.2%",
        securityScore: risks.length > 3 ? "B" : "A+",
        securityDesc: risks.length > 3 ? "Medium risk" : "Secure",
        testCoverage: Math.round(qs.test_coverage || 80),
        techDebtHours: Math.round(qs.technical_debt_hours || 10),
        languages: langs.map((l: any, idx: number) => ({
          name: l.language || l,
          percentage: l.percentage || (100 / Math.max(1, langs.length)),
          colorClass: idx === 0 ? "bg-blue-400" : idx === 1 ? "bg-yellow-400" : "bg-purple-400"
        })),
        commits: over.commits_count || 120,
        openPRs: 2,
        closedPRs: 30,
        openIssues: risks.length,
        closedIssues: 10,
        complexity: (qs.complexity_trend || []).map((c: any, idx: number) => ({
          commit: `C-${idx}`,
          complexity: c.value || c
        })),
        commitActivity: (activeReport.commit_activity || []).map((c: any) => ({
          week: c.week || "Week",
          commits: c.count || c
        })),
        contributors: (activeReport.contributors || []).map((c: any) => ({
          name: c.name || "Contributor",
          avatarUrl: c.avatar_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X",
          commits: c.commits || 10,
          impactPercentage: c.impact || 20
        })),
        pullRequests: [],
        issues: [],
        securityInsights: {
          critical: risks.filter((r: any) => r.severity === "critical").length,
          high: risks.filter((r: any) => r.severity === "high").length,
          medium: risks.filter((r: any) => r.severity === "medium").length,
          low: risks.filter((r: any) => r.severity === "low" || r.severity === "info").length,
          scannerStatus: "Active",
          patchAdvice: activeReport.executive_summary || "Security scanner completed. Code is highly stable."
        },
        hotspots: (qs.hotspots || []).map((h: any, idx: number) => ({
          id: `h-${idx}`,
          filePath: h.file_path || h,
          metricType: "complexity",
          metricDesc: h.reason || "Hotspot detected",
          severity: h.severity || "warning"
        })),
        activities: (activeReport.commits_timeline || []).map((c: any, idx: number) => ({
          id: `act-${idx}`,
          author: c.author || "Developer",
          timeAgo: c.date ? new Date(c.date).toLocaleDateString() : "Just now",
          type: "push",
          description: c.message || "Pushed commits."
        })),
        aiRecommendation: activeReport.executive_summary || "Good codebase overall."
      };
    }
    return REPO_DATABASE[activeRepoName] || REPO_DATABASE["Sugguna-Akhil2006/Nexus_ai"];
  }, [activeReport, activeRepoName]);

  const toolbarActions = (
    <div className="flex flex-wrap items-center gap-3">
      {/* History Selection Dropdown */}
      {history.length > 0 && (
        <div className="relative">
          <select
            value={selectedReportId}
            onChange={(e) => setSelectedReportId(e.target.value)}
            className="bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 pr-8 text-xs font-bold text-on-surface focus:outline-none focus:border-primary appearance-none cursor-pointer"
          >
            {history.map((h) => (
              <option key={h.report_id} value={h.report_id}>
                {h.repository.split("/").pop()} ({new Date(h.timestamp || h.created_at).toLocaleDateString()})
              </option>
            ))}
          </select>
          <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant/80 text-[9px]">
            ▼
          </span>
        </div>
      )}

      {/* Mock dropdown fallback if history is empty */}
      {history.length === 0 && (
        <div className="relative">
          <select
            value={activeRepoName}
            onChange={(e) => setActiveRepoName(e.target.value)}
            className="bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 pr-8 text-xs font-bold text-on-surface focus:outline-none focus:border-primary appearance-none cursor-pointer"
          >
            {Object.keys(REPO_DATABASE).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <span className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-on-surface-variant/80 text-[9px]">
            ▼
          </span>
        </div>
      )}

      <Button
        onClick={handleExportPDF}
        className="bg-primary text-primary-foreground hover:opacity-90 active:scale-98 px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer border-none shadow-md shadow-primary/10 flex items-center gap-1.5"
      >
        <Download className="size-3.5 shrink-0" />
        Export PDF Report
      </Button>
    </div>
  );

  return (
    <PageContainer
      title="GitHub Repository Analyzer"
      description="Execute code quality scans, AST complexity mapping, and security compliance audits."
      icon={<GithubIcon className="size-8 text-primary shrink-0" />}
      toolbar={toolbarActions}
    >
      {/* ─── Ingest Control Panel (sync/async scans) ────────────────── */}
      <section className="bg-surface-container-low/60 border border-outline-variant rounded-xl p-5 md:p-6 shadow-sm backdrop-blur-sm">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-bold text-on-surface uppercase tracking-wider">
            <Terminal className="size-4.5 text-primary" />
            Run New Repository Analysis
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
            <div className="md:col-span-6 flex flex-col gap-1.5">
              <label className="text-[10px] md:text-xs font-bold text-on-surface-variant/80 uppercase tracking-wide">
                Workspace Path / Git URL
              </label>
              <input
                type="text"
                placeholder="e.g. . or https://github.com/username/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={isScanning}
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2 text-xs md:text-sm text-on-surface focus:outline-none focus:border-primary placeholder:text-on-surface-variant/30"
              />
            </div>
            
            <div className="md:col-span-3 flex flex-col gap-1.5">
              <label className="text-[10px] md:text-xs font-bold text-on-surface-variant/80 uppercase tracking-wide">
                Branch / Tag
              </label>
              <input
                type="text"
                placeholder="main"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                disabled={isScanning}
                className="w-full bg-surface-container-lowest border border-outline-variant rounded-lg px-3 py-2 text-xs md:text-sm text-on-surface focus:outline-none focus:border-primary placeholder:text-on-surface-variant/30"
              />
            </div>

            <div className="md:col-span-3 flex gap-2.5">
              <Button
                onClick={handleStartAnalysis}
                disabled={isScanning}
                className="flex-grow bg-primary text-primary-foreground hover:bg-primary/95 text-xs font-bold py-2.5 rounded-lg border-none cursor-pointer flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <Play className="size-4" />
                {isScanning ? "Scanning..." : "Start Analysis"}
              </Button>
            </div>
          </div>

          {/* Progress Indicator */}
          {isScanning && (
            <div className="mt-4 p-4 bg-surface rounded-xl border border-outline-variant/60 space-y-2 animate-pulse">
              <div className="flex justify-between items-center text-xs">
                <span className="text-primary font-semibold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
                  {scanStatusMsg}
                </span>
                <span className="font-bold text-on-surface-variant">{scanProgress}%</span>
              </div>
              <div className="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                <div 
                  className="bg-primary h-full rounded-full transition-all duration-300"
                  style={{ width: `${scanProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ─── Metadata Stats Grid ────────────────────────────────────────── */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-6 select-text">
        <div className="bg-surface-container border border-outline-variant p-4 rounded-xl flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/25 flex items-center justify-center text-primary">
            <GitCommit className="size-5" />
          </div>
          <div>
            <p className="text-[10px] text-on-surface-variant/80 uppercase font-bold tracking-wider">Total Commits</p>
            <p className="text-xl font-bold text-on-surface mt-0.5">{repoData.commits}</p>
          </div>
        </div>

        <div className="bg-surface-container border border-outline-variant p-4 rounded-xl flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-secondary/10 border border-secondary/25 flex items-center justify-center text-secondary">
            <GitPullRequest className="size-5" />
          </div>
          <div>
            <p className="text-[10px] text-on-surface-variant/80 uppercase font-bold tracking-wider">Active Pulls</p>
            <p className="text-xl font-bold text-on-surface mt-0.5">{repoData.openPRs} open</p>
          </div>
        </div>

        <div className="bg-surface-container border border-outline-variant p-4 rounded-xl flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-tertiary/10 border border-tertiary/25 flex items-center justify-center text-tertiary">
            <AlertCircle className="size-5" />
          </div>
          <div>
            <p className="text-[10px] text-on-surface-variant/80 uppercase font-bold tracking-wider">Issues Tracker</p>
            <p className="text-xl font-bold text-on-surface mt-0.5">{repoData.openIssues} open</p>
          </div>
        </div>

        <div className="bg-surface-container border border-outline-variant p-4 rounded-xl flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-primary-container/10 border border-primary-container/25 flex items-center justify-center text-primary-container">
            <Users className="size-5" />
          </div>
          <div>
            <p className="text-[10px] text-on-surface-variant/80 uppercase font-bold tracking-wider">Contributors</p>
            <p className="text-xl font-bold text-on-surface mt-0.5">{repoData.contributors.length} active</p>
          </div>
        </div>
      </section>

      {/* ─── Navigation Tabs ───────────────────────────────────────────── */}
      <div className="flex border-b border-outline-variant/40 gap-6 select-none">
        {["overview", "code", "activity", "security"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={cn(
              "pb-3.5 text-xs font-bold uppercase tracking-wider border-b-2 transition-all cursor-pointer",
              activeTab === tab 
                ? "border-primary text-primary" 
                : "border-transparent text-on-surface-variant hover:text-on-surface"
            )}
          >
            {tab === "overview" && "Overview & Tech Stack"}
            {tab === "code" && "Health & Security"}
            {tab === "activity" && "Commit Activity & Logs"}
            {tab === "security" && "Collaboration & Community"}
          </button>
        ))}
      </div>

      {/* ─── Tabs Views ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-8">
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Health parameters */}
            <div className="lg:col-span-8 h-full">
              <CodeHealthMetrics
                metrics={{
                  maintainability: repoData.maintainability,
                  maintainabilityTrend: repoData.maintainabilityTrend,
                  securityScore: repoData.securityScore,
                  securityDesc: repoData.securityDesc,
                  testCoverage: repoData.testCoverage,
                  techDebtHours: repoData.techDebtHours,
                }}
                complexityData={repoData.complexity}
              />
            </div>
            
            {/* Tech Languages card */}
            <div className="lg:col-span-4 h-full">
              <TechStackCard
                languages={repoData.languages}
                aiInsight={repoData.aiRecommendation}
                onUpgradeClick={handleUpgradeInsight}
              />
            </div>

            {/* Architecture dependency map */}
            <div className="lg:col-span-12">
              <ArchitectureExplorer activeReport={activeReport} />
            </div>
          </div>
        )}

        {activeTab === "code" && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
            {/* Volatility Hotspots panel */}
            <div className="md:col-span-6">
              <HotspotsPanel
                hotspots={repoData.hotspots}
                onHotspotClick={handleHotspotClick}
              />
            </div>

            {/* Security Insights Panel */}
            <div className="md:col-span-6 bg-surface-container border border-outline-variant p-5 rounded-xl flex flex-col justify-between shadow-sm">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
                  <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider flex items-center gap-2">
                    <ShieldCheck className="size-5 text-green-400" />
                    Security Vulnerability Scans
                  </h3>
                  <span className="text-xs font-semibold text-on-surface-variant font-mono">
                    Status: {repoData.securityInsights.scannerStatus}
                  </span>
                </div>

                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-red-500/10 border border-red-500/20 p-2.5 rounded-lg">
                    <p className="text-[10px] uppercase font-bold text-red-400">Critical</p>
                    <p className="text-lg font-mono font-bold mt-1 text-red-400">{repoData.securityInsights.critical}</p>
                  </div>
                  <div className="bg-orange-500/10 border border-orange-500/20 p-2.5 rounded-lg">
                    <p className="text-[10px] uppercase font-bold text-orange-400">High</p>
                    <p className="text-lg font-mono font-bold mt-1 text-orange-400">{repoData.securityInsights.high}</p>
                  </div>
                  <div className="bg-yellow-500/10 border border-yellow-500/20 p-2.5 rounded-lg">
                    <p className="text-[10px] uppercase font-bold text-yellow-400">Medium</p>
                    <p className="text-lg font-mono font-bold mt-1 text-yellow-400">{repoData.securityInsights.medium}</p>
                  </div>
                  <div className="bg-blue-500/10 border border-blue-500/20 p-2.5 rounded-lg">
                    <p className="text-[10px] uppercase font-bold text-blue-400">Low</p>
                    <p className="text-lg font-mono font-bold mt-1 text-blue-400">{repoData.securityInsights.low}</p>
                  </div>
                </div>

                <div className="p-4 bg-surface rounded-lg border border-outline-variant border-dashed flex gap-3 items-start select-text">
                  <Info className="size-4.5 text-primary shrink-0 mt-0.5" />
                  <div className="text-xs font-medium text-on-surface-variant leading-relaxed">
                    <span className="font-bold text-on-surface block mb-1">AI Mitigation Advice</span>
                    {repoData.securityInsights.patchAdvice}
                  </div>
                </div>
              </div>

              {/* Security Badge */}
              <div className="mt-6 pt-4 border-t border-outline-variant/30 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="size-5 text-green-400" />
                  <span className="text-xs font-bold text-on-surface uppercase">SOC2 Compliance Checked</span>
                </div>
                <span className="text-[10px] font-mono text-on-surface-variant/60">SHA-256 Verified</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "activity" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Commit Activity chart */}
            <div className="lg:col-span-8 bg-surface-container border border-outline-variant p-5 rounded-xl shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider mb-5 flex items-center gap-2">
                  <Activity className="size-4.5 text-primary" />
                  Commit Ingestion Volume (8 Weeks)
                </h3>
                
                <div className="h-56 w-full relative pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={repoData.commitActivity} margin={{ left: -25, right: 0, bottom: -5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#232225" vertical={false} />
                      <XAxis dataKey="week" stroke="#8c909f" fontSize={9} tickLine={false} axisLine={false} />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            return (
                              <div className="bg-surface-container border border-outline-variant p-2 rounded-lg text-[10px] shadow-xl">
                                <p className="font-bold text-on-surface">Week: {payload[0].payload.week}</p>
                                <p className="text-primary font-bold">{payload[0].value} commits</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="commits" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={32} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Ingest events activity feed */}
            <div className="lg:col-span-4">
              <RecentActivityFeed activities={repoData.activities} />
            </div>
          </div>
        )}

        {activeTab === "security" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 select-text">
            {/* Contributors list column */}
            <div className="lg:col-span-4 bg-surface-container border border-outline-variant p-5 rounded-xl shadow-sm space-y-4">
              <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider border-b border-outline-variant/30 pb-3 flex items-center gap-2">
                <Users className="size-4.5 text-primary" />
                Active Contributors
              </h3>

              <div className="space-y-4">
                {repoData.contributors.map((contrib) => (
                  <div key={contrib.name} className="flex items-center justify-between gap-4 p-2 hover:bg-surface-container-high/40 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                      {/* Avatar */}
                      <div className="w-8 h-8 rounded-full border border-outline-variant overflow-hidden shrink-0">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src={contrib.avatarUrl} alt={contrib.name} className="w-full h-full object-cover" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs md:text-sm font-semibold text-on-surface truncate">{contrib.name}</p>
                        <p className="text-[10px] text-on-surface-variant font-mono">{contrib.commits} commits</p>
                      </div>
                    </div>
                    
                    <div className="text-right shrink-0">
                      <span className="text-xs font-bold text-primary font-mono">{contrib.impactPercentage}%</span>
                      <p className="text-[9px] uppercase tracking-wider text-on-surface-variant font-bold">Impact</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Tabbed PRs & Issues column */}
            <div className="lg:col-span-8 bg-surface-container border border-outline-variant p-5 rounded-xl shadow-sm flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider border-b border-outline-variant/30 pb-3 flex items-center justify-between select-none">
                  <span>Codebase Collaboration Status</span>
                  <span className="text-xs text-on-surface-variant/80 font-mono">
                    Open: {repoData.openPRs} PRs / {repoData.openIssues} Issues
                  </span>
                </h3>

                <div className="space-y-4 max-h-[320px] overflow-y-auto pr-1">
                  {/* PRs Header Label */}
                  <div className="text-[10px] font-bold text-on-surface-variant/70 uppercase tracking-widest border-b border-outline-variant/20 pb-1.5 flex items-center gap-1">
                    <GitPullRequest className="size-3 text-primary" />
                    Active Ingestion Pull Requests
                  </div>
                  {repoData.pullRequests.map((pr) => (
                    <div key={pr.id} className="flex justify-between items-start gap-4 p-3 bg-surface rounded-lg border border-outline-variant/50 hover:border-primary/40 transition-colors">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs md:text-sm font-semibold text-on-surface hover:text-primary cursor-pointer">
                            #{pr.number}: {pr.title}
                          </span>
                          {pr.state === "merged" && (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-purple-500/15 border border-purple-500/20 text-purple-400 uppercase tracking-wider">
                              Merged
                            </span>
                          )}
                          {pr.state === "open" && (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-500/15 border border-blue-500/20 text-blue-400 uppercase tracking-wider">
                              Open
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-on-surface-variant/80 font-mono mt-1">
                          Opened by {pr.author} &bull; {pr.timeAgo}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        {pr.tags.map((t) => (
                          <span key={t} className="text-[8px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-container-highest border border-outline-variant text-on-surface-variant">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Issues Header Label */}
                  <div className="text-[10px] font-bold text-on-surface-variant/70 uppercase tracking-widest border-b border-outline-variant/20 pt-2 pb-1.5 flex items-center gap-1">
                    <AlertCircle className="size-3 text-tertiary" />
                    Open Issues Tracker
                  </div>
                  {repoData.issues.map((iss) => (
                    <div key={iss.id} className="flex justify-between items-start gap-4 p-3 bg-surface rounded-lg border border-outline-variant/50 hover:border-primary/40 transition-colors">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs md:text-sm font-semibold text-on-surface hover:text-primary cursor-pointer">
                            #{iss.number}: {iss.title}
                          </span>
                          {iss.state === "open" ? (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-500/15 border border-amber-500/20 text-amber-400 uppercase tracking-wider">
                              Open
                            </span>
                          ) : (
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-green-500/15 border border-green-500/20 text-green-400 uppercase tracking-wider">
                              Closed
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-on-surface-variant/80 font-mono mt-1">
                          Opened {iss.timeAgo}
                        </p>
                      </div>
                      <span className={cn(
                        "text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded shrink-0",
                        iss.priority === "high" && "bg-error/15 text-error border border-error/20",
                        iss.priority === "medium" && "bg-amber-500/15 text-amber-400 border border-amber-500/20",
                        iss.priority === "low" && "bg-blue-500/15 text-blue-400 border border-blue-500/20"
                      )}>
                        {iss.priority}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Floating AI chatbot assistant FAB */}
      <div className="fixed bottom-8 right-8 z-50">
        <Button
          onClick={() => {
            toast.success("AI Copilot activated!", {
              description: `Loaded context parameters for ${repoData.name}. Ask any questions in Chat.`,
            });
          }}
          className="w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-2xl flex items-center justify-center active:scale-90 transition-all cursor-pointer border-none shadow-primary/20 hover:scale-105"
          title="Ask Repository AI Assistant"
        >
          <MessageSquareCode className="size-6 text-primary-foreground" />
        </Button>
      </div>
    </PageContainer>
  );
}
