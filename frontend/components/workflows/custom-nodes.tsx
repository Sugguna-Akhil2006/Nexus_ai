"use client";

import { Handle, Position, NodeProps, Node } from "@xyflow/react";
import { Webhook, Timer, Split, FileCode, Database, MoreVertical } from "lucide-react";
import { cn } from "@/lib/utils";

// Custom node data typing
export type WorkflowNodeData = {
  label: string;
  subText?: string;
  type: "webhook" | "cron" | "condition" | "script" | "db";
};

export type WorkflowNode = Node<WorkflowNodeData>;

export function WebhookNode({ data, selected }: NodeProps<WorkflowNode>) {
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border border-outline-variant rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      selected && "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Webhook className="size-4 text-primary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer shrink-0" />
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
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border border-outline-variant rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      selected && "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]"
    )}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Timer className="size-4 text-primary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer shrink-0" />
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
  return (
    <div className={cn(
      "w-56 bg-surface-container-highest border border-outline-variant rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      selected && "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]"
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Split className="size-4 text-tertiary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer shrink-0" />
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
  return (
    <div className={cn(
      "w-56 bg-surface-container-highest border border-outline-variant rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      selected && "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]"
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileCode className="size-4 text-tertiary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer shrink-0" />
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
  return (
    <div className={cn(
      "w-48 bg-surface-container-highest border border-outline-variant rounded-xl p-4 shadow-lg flex flex-col gap-3 group transition-all relative select-none",
      selected && "outline-2 outline-primary shadow-[0_0_15px_rgba(59,130,246,0.2)]"
    )}>
      {/* Input handle on the Left */}
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="w-3 h-3 !bg-outline !border-2 !border-surface hover:!bg-primary transition-colors cursor-pointer !-ml-1.5"
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="size-4 text-secondary shrink-0" />
          <span className="text-xs font-bold text-on-surface truncate">{data.label}</span>
        </div>
        <MoreVertical className="size-4 text-on-surface-variant/60 cursor-pointer shrink-0" />
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
