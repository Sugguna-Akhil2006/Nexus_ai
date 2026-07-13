"use client";

import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { Webhook, Timer, Split, FileCode, Database, MoreVertical, Play, CheckCircle2, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

// Custom node data typing
export type WorkflowNodeData = {
  label: string;
  subText?: string;
  type: "webhook" | "cron" | "condition" | "script" | "db";
  status?: "idle" | "executing" | "success" | "error";
};

export type WorkflowNode = Node<WorkflowNodeData>;

// Helper to get status-specific classes
function getStatusClasses(status?: string, selected?: boolean) {
  if (status === "executing") {
    return "border-yellow-400 shadow-[0_0_15px_rgba(251,191,36,0.3)] animate-pulse ring-1 ring-yellow-400";
  }
  if (status === "success") {
    return "border-green-400 shadow-[0_0_15px_rgba(74,222,128,0.25)] ring-1 ring-green-400";
  }
  if (status === "error") {
    return "border-red-400 shadow-[0_0_15px_rgba(248,113,113,0.25)] ring-1 ring-red-400";
  }
  return selected ? "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]" : "border-outline-variant";
}

// Status Indicator Icon Overlay
function StatusBadge({ status }: { status?: string }) {
  if (status === "executing") {
    return <Play className="size-3 text-yellow-400 animate-spin shrink-0" />;
  }
  if (status === "success") {
    return <CheckCircle2 className="size-3 text-green-400 shrink-0" />;
  }
  if (status === "error") {
    return <AlertTriangle className="size-3 text-red-400 shrink-0" />;
  }
  return null;
}

export function WebhookNode({ data, selected }: NodeProps<WorkflowNode>) {
  const statusClasses = getStatusClasses(data.status, selected);
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      statusClasses
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Webhook className="size-4 text-primary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={data.status} />
          <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer" />
        </div>
      </div>

      {/* Connection Output handle on the Right */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-mr-1.5"
      />
    </div>
  );
}

export function CronNode({ data, selected }: NodeProps<WorkflowNode>) {
  const statusClasses = getStatusClasses(data.status, selected);
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      statusClasses
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Timer className="size-4 text-primary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={data.status} />
          <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer" />
        </div>
      </div>

      {/* Connection Output handle on the Right */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-mr-1.5"
      />
    </div>
  );
}

export function ConditionNode({ data, selected }: NodeProps<WorkflowNode>) {
  const statusClasses = getStatusClasses(data.status, selected);
  return (
    <div className={cn(
      "w-56 bg-surface-container-highest border rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      statusClasses
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Split className="size-4 text-tertiary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={data.status} />
          <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer" />
        </div>
      </div>

      {/* Two outputs for Condition checks on the Right */}
      <div className="flex flex-col gap-2 text-[9px] text-on-surface-variant/70 uppercase font-bold text-right pr-1 select-none">
        <span className="leading-none mt-1">True</span>
        <span className="leading-none mt-3.5">False</span>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        id="true"
        style={{ top: "42px" }}
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-mr-1.5"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="false"
        style={{ top: "66px" }}
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-mr-1.5"
      />
    </div>
  );
}

export function ScriptNode({ data, selected }: NodeProps<WorkflowNode>) {
  const statusClasses = getStatusClasses(data.status, selected);
  return (
    <div className={cn(
      "w-56 bg-surface-container-highest border rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      statusClasses
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <FileCode className="size-4 text-tertiary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={data.status} />
          <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer" />
        </div>
      </div>

      <div className="flex justify-between items-center mt-1 select-none">
        <div className="text-[10px] text-outline-variant font-mono uppercase tracking-wider">
          {data.subText || "mapping v1.2"}
        </div>
      </div>

      {/* Output handle on the Right */}
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-mr-1.5"
      />
    </div>
  );
}

export function DBNode({ data, selected }: NodeProps<WorkflowNode>) {
  const statusClasses = getStatusClasses(data.status, selected);
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      statusClasses
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Database className="size-4 text-secondary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <StatusBadge status={data.status} />
          <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer" />
        </div>
      </div>
    </div>
  );
}

// Node types mapping dictionary for React Flow
export const nodeTypes = {
  webhookNode: WebhookNode,
  cronNode: CronNode,
  conditionNode: ConditionNode,
  scriptNode: ScriptNode,
  dbNode: DBNode,
};
