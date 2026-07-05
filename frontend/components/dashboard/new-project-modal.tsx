"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import {
  Bot,
  BarChart3,
  CheckCircle2,
  ChevronLeft,
  Database,
  MessageSquare,
  ShieldAlert,
  Sparkles,
  Workflow,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNewProject } from "@/providers/new-project-provider";

// ─── Template Definitions ──────────────────────────────────────────────────

interface ProjectTemplate {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  category: string;
  accentClass: string;
  bgClass: string;
  defaultProjectName: string;
}

const TEMPLATES: ProjectTemplate[] = [
  {
    id: "chat-assistant",
    name: "AI Chat Assistant",
    icon: MessageSquare,
    description: "Customer-facing conversational AI with memory and personas.",
    category: "NLP",
    accentClass: "text-primary",
    bgClass: "bg-primary/10 border-primary/25",
    defaultProjectName: "Chat Assistant v1",
  },
  {
    id: "data-pipeline",
    name: "Data Pipeline",
    icon: Database,
    description: "Automated ETL routing, vector indexing, and embeddings.",
    category: "Data Ops",
    accentClass: "text-secondary",
    bgClass: "bg-secondary/10 border-secondary/25",
    defaultProjectName: "Data Processing Pipeline",
  },
  {
    id: "autonomous-agent",
    name: "Autonomous Agent",
    icon: Bot,
    description: "Self-directed task executor with tool use and planning.",
    category: "Agentic",
    accentClass: "text-violet-400",
    bgClass: "bg-violet-500/10 border-violet-500/25",
    defaultProjectName: "Autonomous Agent Runtime",
  },
  {
    id: "security-guardrail",
    name: "Security Guardrail",
    icon: ShieldAlert,
    description: "Prompt injection prevention and LLM safety layer.",
    category: "Security",
    accentClass: "text-orange-400",
    bgClass: "bg-orange-500/10 border-orange-500/25",
    defaultProjectName: "Vanguard Guardrail",
  },
  {
    id: "analytics-dashboard",
    name: "Analytics Dashboard",
    icon: BarChart3,
    description: "Real-time inference metrics, costs, and performance.",
    category: "Observability",
    accentClass: "text-cyan-400",
    bgClass: "bg-cyan-500/10 border-cyan-500/25",
    defaultProjectName: "Analytics Hub",
  },
  {
    id: "custom-workflow",
    name: "Custom Workflow",
    icon: Workflow,
    description: "Blank canvas for any automation — build from scratch.",
    category: "Builder",
    accentClass: "text-green-400",
    bgClass: "bg-green-500/10 border-green-500/25",
    defaultProjectName: "My Custom Workflow",
  },
];

// ─── Creation Progress Steps ────────────────────────────────────────────────

const CREATION_STEPS = [
  "Initializing workspace...",
  "Configuring AI agents...",
  "Wiring data pipelines...",
  "Almost ready...",
];

// ─── Step 1 — Template Picker ───────────────────────────────────────────────

function TemplateCard({
  template,
  isSelected,
  onSelect,
}: {
  template: ProjectTemplate;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const Icon = template.icon;
  return (
    <motion.button
      type="button"
      onClick={onSelect}
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.15 }}
      className={cn(
        "relative flex flex-col gap-3 p-4 rounded-xl border text-left cursor-pointer transition-all duration-200 w-full group",
        isSelected
          ? "border-primary bg-primary/5 ring-2 ring-primary/40 shadow-lg shadow-primary/10"
          : "border-outline-variant bg-surface-container-low hover:border-outline hover:bg-surface-container"
      )}
      aria-pressed={isSelected}
    >
      {/* Selected badge */}
      <AnimatePresence>
        {isSelected && (
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ duration: 0.15 }}
            className="absolute top-2.5 right-2.5"
          >
            <CheckCircle2 className="size-4 text-primary" />
          </motion.span>
        )}
      </AnimatePresence>

      {/* Icon */}
      <div className={cn("w-10 h-10 rounded-lg border flex items-center justify-center flex-shrink-0", template.bgClass)}>
        <Icon className={cn("size-5", template.accentClass)} />
      </div>

      {/* Text */}
      <div className="space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-on-surface leading-tight">{template.name}</span>
        </div>
        <span className={cn("text-[10px] font-semibold uppercase tracking-wider", template.accentClass)}>
          {template.category}
        </span>
        <p className="text-xs text-on-surface-variant leading-relaxed pt-1">{template.description}</p>
      </div>
    </motion.button>
  );
}

// ─── Step 2 — Name Input ────────────────────────────────────────────────────

function StepNameProject({
  template,
  projectName,
  setProjectName,
  onBack,
  onCreate,
}: {
  template: ProjectTemplate;
  projectName: string;
  setProjectName: (n: string) => void;
  onBack: () => void;
  onCreate: () => void;
}) {
  const Icon = template.icon;
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // focus with a brief delay so modal animation settles
    const t = setTimeout(() => inputRef.current?.focus(), 120);
    return () => clearTimeout(t);
  }, []);

  const isValid = projectName.trim().length >= 2;

  return (
    <motion.div
      key="step-name"
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -24 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col gap-6"
    >
      {/* Selected template preview chip */}
      <div className={cn("flex items-center gap-3 p-3 rounded-xl border", template.bgClass)}>
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", template.bgClass)}>
          <Icon className={cn("size-4", template.accentClass)} />
        </div>
        <div>
          <p className="text-xs font-medium text-on-surface-variant">Selected template</p>
          <p className="text-sm font-semibold text-on-surface">{template.name}</p>
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <label htmlFor="project-name-input" className="text-sm font-semibold text-on-surface">
          Project Name
        </label>
        <Input
          id="project-name-input"
          ref={inputRef}
          value={projectName}
          onChange={(e) => setProjectName(e.target.value.slice(0, 60))}
          placeholder="e.g. Production Chat Agent"
          className="h-11 text-sm bg-surface-container border-outline-variant focus-visible:border-primary focus-visible:ring-primary/20"
          onKeyDown={(e) => {
            if (e.key === "Enter" && isValid) onCreate();
          }}
        />
        <p className="text-xs text-on-surface-variant text-right">{projectName.length}/60</p>
      </div>

      {/* Buttons */}
      <div className="flex gap-3 pt-1">
        <Button
          variant="outline"
          onClick={onBack}
          className="flex-1 gap-1.5 border-outline-variant bg-surface-container text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface cursor-pointer"
        >
          <ChevronLeft className="size-4" />
          Back
        </Button>
        <Button
          disabled={!isValid}
          onClick={onCreate}
          className="flex-[2] gap-2 bg-primary text-primary-foreground font-semibold hover:bg-primary/90 active:scale-95 transition-transform cursor-pointer border-none disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Zap className="size-4" />
          Create Project
        </Button>
      </div>
    </motion.div>
  );
}

// ─── Step 3 — Creating Loader ───────────────────────────────────────────────

function StepCreating({ projectName }: { projectName: string }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((i) => Math.min(i + 1, CREATION_STEPS.length - 1));
      setProgress((p) => Math.min(p + 28, 100));
    }, 380);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      key="step-creating"
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col items-center gap-6 py-6 text-center"
    >
      {/* Animated icon */}
      <div className="relative">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
          className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/25 flex items-center justify-center"
        >
          <Sparkles className="size-7 text-primary" />
        </motion.div>
        {/* Pulse ring */}
        <span className="absolute inset-0 rounded-2xl border border-primary/30 animate-ping opacity-30" />
      </div>

      <div className="space-y-1">
        <h3 className="text-base font-bold text-on-surface">Building "{projectName}"</h3>
        <AnimatePresence mode="wait">
          <motion.p
            key={stepIndex}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="text-sm text-on-surface-variant"
          >
            {CREATION_STEPS[stepIndex]}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-xs space-y-1.5">
        <div className="h-1.5 w-full rounded-full bg-surface-container-high overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-primary"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          />
        </div>
        <p className="text-[11px] text-on-surface-variant text-right font-mono">{progress}%</p>
      </div>
    </motion.div>
  );
}

// ─── Main Modal ─────────────────────────────────────────────────────────────

type ModalStep = "template" | "name" | "creating";

export default function NewProjectModal() {
  const { isOpen, closeNewProject } = useNewProject();
  const router = useRouter();

  const [step, setStep] = useState<ModalStep>("template");
  const [selectedTemplate, setSelectedTemplate] = useState<ProjectTemplate | null>(null);
  const [projectName, setProjectName] = useState("");

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep("template");
      setSelectedTemplate(null);
      setProjectName("");
    }
  }, [isOpen]);

  const handleSelectTemplate = (template: ProjectTemplate) => {
    setSelectedTemplate(template);
    setProjectName(template.defaultProjectName);
  };

  const handleNext = () => {
    if (!selectedTemplate) return;
    setStep("name");
  };

  const handleCreate = () => {
    setStep("creating");

    // Mock async creation — 1.6s total
    setTimeout(() => {
      const projectId = `proj-${Date.now()}`;

      // Persist mock project data into sessionStorage so the detail page can read it
      const projectData = {
        id: projectId,
        name: projectName.trim(),
        templateId: selectedTemplate!.id,
        templateName: selectedTemplate!.name,
        category: selectedTemplate!.category,
        createdAt: new Date().toISOString(),
      };
      sessionStorage.setItem(`nexus_project_${projectId}`, JSON.stringify(projectData));

      closeNewProject();
      toast.success(`"${projectName.trim()}" created successfully!`, {
        description: "Your new project workspace is ready.",
        duration: 4000,
      });
      router.push(`/dashboard/projects/${projectId}`);
    }, 1600);
  };

  if (!isOpen) return null;

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget && step !== "creating") closeNewProject();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Create New Project"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.94, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94, y: 16 }}
        transition={{ duration: 0.22, ease: "easeOut" }}
        className="relative w-full max-w-2xl bg-surface-container rounded-2xl border border-outline-variant shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-outline-variant/50">
          <div className="space-y-0.5">
            <h2 className="text-lg font-bold text-on-surface tracking-tight">
              {step === "template" && "Choose a Template"}
              {step === "name" && "Name Your Project"}
              {step === "creating" && "Creating Project..."}
            </h2>
            <p className="text-xs text-on-surface-variant">
              {step === "template" && "Select a starting point for your new project."}
              {step === "name" && "Give your project a descriptive name."}
              {step === "creating" && "Hang tight while we provision your workspace."}
            </p>
          </div>

          {/* Step indicator dots */}
          <div className="flex items-center gap-2">
            {(["template", "name", "creating"] as ModalStep[]).map((s, i) => (
              <span
                key={s}
                className={cn(
                  "h-1.5 rounded-full transition-all duration-300",
                  step === s ? "w-5 bg-primary" : "w-1.5 bg-outline-variant"
                )}
              />
            ))}
          </div>

          {step !== "creating" && (
            <button
              type="button"
              onClick={closeNewProject}
              aria-label="Close modal"
              className="ml-4 flex items-center justify-center w-8 h-8 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer"
            >
              <X className="size-4" />
            </button>
          )}
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          <AnimatePresence mode="wait">
            {/* STEP 1 — Template grid */}
            {step === "template" && (
              <motion.div
                key="step-template"
                initial={{ opacity: 0, x: -24 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -24 }}
                transition={{ duration: 0.2 }}
                className="flex flex-col gap-5"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[340px] overflow-y-auto pr-1 scroll-smooth">
                  {TEMPLATES.map((template) => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      isSelected={selectedTemplate?.id === template.id}
                      onSelect={() => handleSelectTemplate(template)}
                    />
                  ))}
                </div>

                {/* Footer CTA */}
                <div className="flex items-center justify-between pt-1 border-t border-outline-variant/40">
                  <p className="text-xs text-on-surface-variant">
                    {selectedTemplate
                      ? `Selected: ${selectedTemplate.name}`
                      : "Select a template to continue"}
                  </p>
                  <Button
                    disabled={!selectedTemplate}
                    onClick={handleNext}
                    className="gap-2 bg-primary text-primary-foreground font-semibold hover:bg-primary/90 active:scale-95 transition-transform cursor-pointer border-none disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Continue
                    <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                      <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </Button>
                </div>
              </motion.div>
            )}

            {/* STEP 2 — Name input */}
            {step === "name" && selectedTemplate && (
              <StepNameProject
                template={selectedTemplate}
                projectName={projectName}
                setProjectName={setProjectName}
                onBack={() => setStep("template")}
                onCreate={handleCreate}
              />
            )}

            {/* STEP 3 — Creating */}
            {step === "creating" && (
              <StepCreating projectName={projectName} />
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
