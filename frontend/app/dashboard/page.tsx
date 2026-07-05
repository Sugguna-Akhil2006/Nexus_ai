"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Boxes, ShieldAlert, Cloud, Cpu, Database, Users } from "lucide-react";
import DashboardHeader from "@/components/dashboard/header";
import InferenceLoadsChart from "@/components/dashboard/chart";
import ActivityPanel from "@/components/dashboard/activity-panel";
import ProjectCard, { ProjectCardProps } from "@/components/dashboard/project-card";
import MetricCard from "@/components/dashboard/metric-card";
import { Button } from "@/components/ui/button";
import { useNewProject } from "@/providers/new-project-provider";
import EmptyState from "@/components/common/empty-state";

// Mock Active Projects Data
const PROJECTS: (Omit<ProjectCardProps, "icon"> & { id: string; icon: any })[] = [
  {
    id: "proj-1",
    title: "Data Processing Pipeline",
    description: "Autonomous data processing and routing workflow canvas.",
    status: "In Progress",
    statusColorClass: "text-primary",
    progress: 84,
    progressBarColorClass: "bg-primary",
    icon: Boxes,
    iconBgClass: "bg-primary/10 border-primary/20",
    members: [
      { 
        name: "Alex Chen", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAbr9guC61fiUJeD9Xl4Rj2K2COicq9oILTpOuLicDl0fZT-LW7zHHMa0DmF3nf0mx53QYwDf7QJAPBH0wLWmvTjyEs98DxiXtowyXhFnn8dwhIaaa_Ku72pQRHyMxSsk14lAq3sJwega8kIfJatmMGLgWHFdJ4fw6in1BJKEnusJgVr7mNLcBHbtix11PTjD4LIFc8F8WqkoQkssm3IWd7K4_euEesvkfi7mh7a4XNi_eTbGDkEtU6ZV4PaVM8gTjA2jXzgiSw7P0X" 
      },
      { 
        name: "Sarah Jenkins", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuA3MoYSYYxljBKeD1LPVnMlh1GRqzGT-0TPiEk3dCPcouz2FfLQuitJSbZKDvMjXQOq6ixjnsbx3l6hsfJPOLv7ciaUzn_PmDfvXonTcwEVmgTmLR9l6WxXgtyheASMa1QK2InnI3L65Q-hJ3D98-0uWyJcz3Jd5WgFn4Liy-Z9p6RG5ax7_p1wL6lvGKnoPQYRIOcpzEJlr9oV5R0yjunh8FVal9HJ8OFI8OFcGupCvATsxR0l_A2pPwP8DZPp-1sIRLeuZiI65wJh" 
      }
    ],
    extraMembers: 3,
  },
  {
    id: "proj-2",
    title: "Vanguard Guardrail",
    description: "Real-time prompt injection prevention and LLM safety layer.",
    status: "Staging",
    statusColorClass: "text-secondary",
    progress: 42,
    progressBarColorClass: "bg-secondary",
    icon: ShieldAlert,
    iconBgClass: "bg-secondary/15 border-secondary/20",
    members: [
      { 
        name: "Marcus Aurelius", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuCN4AjYH9VxqqekSZR46EWARGDW7GMXN34fjzzmPJY-B4sW93NZW3_bKE8rk8GH6Z7bRoipIGJbgqN0vtzn7xAgoHQTc6JtG3CQCfDiA9neEXuu28xGxc7wL6j9Kf9h9i4MR4U2WvxAjh9HSw6td40xcVWZ9XzdCZ2rtAJ9ktBeZegNm95Es4QadiRmjLDzYdu7-cEyX3PmeaeSC_AnC0mw4FYBiPbd4et2dqdo-rGQFmI6NeZ8QujR__Aq0aj-E6wcGGvHPbx8gVEE" 
      }
    ],
    extraMembers: 1,
  },
  {
    id: "proj-3",
    title: "Core-Sync 2.0",
    description: "Unified vector embedding pipeline for global agent clusters.",
    status: "Active",
    statusColorClass: "text-green-400",
    progress: 96,
    progressBarColorClass: "bg-primary",
    icon: Cloud,
    iconBgClass: "bg-primary-container/20 border-primary-container/30",
    members: [
      { 
        name: "Dina Prince", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuDvD0kvr7FE7QIJRQL9HZs04p8yaOCCyuEkJznFj0H2CiDuOh3ohnA9hKPU5n9MyCu5fVwuIsnK-pP7LCR-PvBdz3mAE2Qrmm1bX6Lwps43Uv4sL1JMbXRAf-DvOTTEiFmWPC0izk3h7-lQdyZ4GXU-s5YnVt-Uz1-AGJon-RJujjlCeVAEZvrDaqW1Q_x7poDkUXefQ_JgndojkCTwKAXQRIbCicPkaSffJNHeNnGYL0iilkCifS9fCc1VWcCXWtGa6fht0BuS6qKJ" 
      },
      { 
        name: "John Stewart", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuADTWQkJyCrcBfNzLgWua8xU-wSLoS4mBRmPJAOkXXNiI6psySgLavV1ddMecybd-7q9elRbTlwmWxlKjxr3FHHT5xYSlyrbidFLE16_NS6iaqQrVs70eGO2g95M6_PkS2khQZXIMjMIH70Oaj8Q08rqOzH0F8RmXifQLnBBLi0KiNCdfvzLcTaug8Nx4WKOWgxJmqKpcqTiD2huFl4At0iXjGJeXgJ8sCjRqtnJOVd3Ppku0_QYohGZpctB_esvM7LgXuueGefuPN0" 
      },
      { 
        name: "Wally West", 
        avatarUrl: "https://lh3.googleusercontent.com/aida-public/AB6AXuAEnZ2U0S7-nMI81nD33xTVKwg57UfvPrDUZUI5BNnA7MfYHooLqhTbejOGaSkmiGzN7wb9mV2lEhKtJ-48IPOno1WR8NuS5PZV7I2R226SZaCsHjXXS5vz9tbSBvyid-6MkDeFAE0kYYvXzSjNcWQf3DFGDqGz4ADbfSiaGDP3OsNkh0EmvpOqwVCf9v5BPx_MxrRGU1ncbF7JiovX7TgfKygx0a6jFTk5svBGlvAeg8ISiq3YR_i4uzjHEZVIsMyyHMHql5ESvtr5" 
      }
    ],
    extraMembers: 8,
  }
];

// Mock Performance Metrics Data
const METRICS = [
  {
    title: "Compute Usage",
    value: "84.2 TFlops",
    icon: Cpu,
  },
  {
    title: "Storage Index",
    value: "1.2 PB",
    icon: Database,
  },
  {
    title: "Active Agents",
    value: (
      <span className="flex items-baseline">
        12 
        <span className="text-green-400 text-xs font-normal ml-1.5 lowercase">
          online
        </span>
      </span>
    ),
    icon: Users,
  }
];

export default function DashboardPage() {
  const { openNewProject } = useNewProject();
  const [isEmpty, setIsEmpty] = useState(false);

  return (
    <div className="p-6 md:p-8 space-y-6 md:space-y-8 flex flex-col justify-between min-h-[calc(100vh-64px)] relative">
      
      <div className="space-y-6 md:space-y-8">
        {/* Dashboard Header */}
        <DashboardHeader />

        {/* Inference Load Chart & Live Activity Feed Grid */}
        <div className="grid grid-cols-12 gap-6">
          <InferenceLoadsChart />
          <ActivityPanel />
        </div>

        {/* Active Projects Grid */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-on-surface tracking-tight">
              Active Projects
            </h3>
            <Button 
              variant="ghost" 
              size="xs" 
              onClick={() => setIsEmpty(!isEmpty)} 
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
            >
              {isEmpty ? "● Show Mock Projects" : "○ Simulate Empty State"}
            </Button>
          </div>

          {isEmpty ? (
            <div className="py-6">
              <EmptyState
                icon={Boxes}
                title="No Active Projects"
                description="Create your first workspace pipeline container to start running inference jobs, deploying autonomous agents, and orchestrating models."
                actionLabel="Create New Project"
                onAction={openNewProject}
                accentColor="primary"
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {PROJECTS.map((project) => (
                <Link
                  key={project.id}
                  href={project.id === "proj-1" ? "/dashboard/workflows" : "#"}
                  className="block h-full cursor-pointer hover:no-underline"
                >
                  <ProjectCard
                    title={project.title}
                    description={project.description}
                    status={project.status}
                    statusColorClass={project.statusColorClass}
                    progress={project.progress}
                    progressBarColorClass={project.progressBarColorClass}
                    icon={project.icon}
                    iconBgClass={project.iconBgClass}
                    members={project.members}
                    extraMembers={project.extraMembers}
                  />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Bottom Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          {METRICS.map((metric) => (
            <MetricCard
              key={metric.title}
              title={metric.title}
              value={metric.value}
              icon={metric.icon}
            />
          ))}
        </div>
      </div>

      {/* Footer Branding */}
      <footer className="py-6 mt-8 border-t border-outline-variant/30 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-medium text-on-surface-variant">
        <span>© 2024 Nexus AI Enterprise</span>
        <div className="flex gap-6">
          <Link href="#" className="hover:text-on-surface transition-colors">
            API Docs
          </Link>
          <Link href="#" className="hover:text-on-surface transition-colors">
            System Status
          </Link>
          <Link href="#" className="hover:text-on-surface transition-colors">
            Support
          </Link>
        </div>
      </footer>

      {/* Floating Action Button (FAB) on Mobile */}
      <Button
        aria-label="Create New Project"
        onClick={openNewProject}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-primary text-primary-foreground shadow-2xl flex items-center justify-center active:scale-90 transition-all z-50 md:hidden cursor-pointer border-none shadow-primary/20 hover:scale-105"
      >
        <Plus className="size-6" />
      </Button>

    </div>
  );
}
