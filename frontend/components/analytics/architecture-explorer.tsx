"use client";

import { useState, useCallback, useMemo } from "react";
import { 
  ReactFlow, 
  Background, 
  BackgroundVariant,
  useNodesState, 
  useEdgesState, 
  Edge,
  Node,
  ReactFlowProvider,
  useReactFlow,
  Panel
} from "@xyflow/react";
import { X, Network, Share2, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Custom node typings
interface ServiceNodeData extends Record<string, unknown> {
  label: string;
  type: "core" | "database" | "bottleneck";
  description: string;
  connections: number;
  risk: "Low" | "Medium" | "High";
}

type ServiceNode = Node<ServiceNodeData>;

// Nodes data listing
const INITIAL_NODES: ServiceNode[] = [
  {
    id: "gateway",
    position: { x: 80, y: 150 },
    data: {
      label: "API Gateway",
      type: "core",
      description: "Gateway load balancer proxying incoming developer requests.",
      connections: 28,
      risk: "Low",
    },
    // Styling matching core service node (blue)
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 130,
    },
  },
  {
    id: "auth",
    position: { x: 280, y: 70 },
    data: {
      label: "/api/v1/auth",
      type: "core",
      description: "High-traffic node handling session validation and JWT issuance.",
      connections: 14,
      risk: "Low",
    },
    selected: true, // Default selected to match HTML
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "2px solid #3b82f6", // selected look
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 130,
    },
  },
  {
    id: "ingest",
    position: { x: 280, y: 230 },
    data: {
      label: "/api/v1/ingest",
      type: "bottleneck",
      description: "Data ingestion endpoint throttling under payload peaks. Refactoring recommended.",
      connections: 26,
      risk: "High",
    },
    style: {
      background: "rgba(239, 68, 68, 0.15)",
      border: "1px solid rgba(239, 68, 68, 0.4)",
      borderRadius: "8px",
      color: "#ef4444",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 130,
    },
  },
  {
    id: "authDB",
    position: { x: 480, y: 70 },
    data: {
      label: "User Auth DB",
      type: "database",
      description: "Encrypted credential database holding persistent user profiles.",
      connections: 4,
      risk: "Low",
    },
    style: {
      background: "rgba(245, 158, 11, 0.15)",
      border: "1px solid rgba(245, 158, 11, 0.4)",
      borderRadius: "8px",
      color: "#f59e0b",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 130,
    },
  },
  {
    id: "analyticsDB",
    position: { x: 480, y: 230 },
    data: {
      label: "Analytics DB",
      type: "database",
      description: "Throttled Redis cluster storing real-time tracking events.",
      connections: 18,
      risk: "Medium",
    },
    style: {
      background: "rgba(245, 158, 11, 0.15)",
      border: "1px solid rgba(245, 158, 11, 0.4)",
      borderRadius: "8px",
      color: "#f59e0b",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 130,
    },
  },
];

const INITIAL_EDGES: Edge[] = [
  { id: "e-gate-auth", source: "gateway", target: "auth", animated: true, style: { stroke: "#424754" } },
  { id: "e-gate-ing", source: "gateway", target: "ingest", animated: true, style: { stroke: "#ef4444" } }, // red edge for bottleneck path
  { id: "e-auth-db", source: "auth", target: "authDB", style: { stroke: "#424754" } },
  { id: "e-ing-db", source: "ingest", target: "analyticsDB", style: { stroke: "#424754" } },
];

function ExplorerContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState<ServiceNode>(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [mode, setMode] = useState<"dependency" | "tree" | "data">("dependency");
  const [showInspector, setShowInspector] = useState(true);

  // Sync selected border details on click
  const activeNode = useMemo(() => {
    return nodes.find((n) => n.selected);
  }, [nodes]);

  const handleNodeClick = useCallback(
    (event: any, node: Node) => {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          selected: n.id === node.id,
          style: {
            ...n.style,
            border: n.id === node.id 
              ? `2px solid ${n.id === "ingest" ? "#ef4444" : n.id === "authDB" || n.id === "analyticsDB" ? "#f59e0b" : "#3b82f6"}`
              : `1px solid ${n.id === "ingest" ? "rgba(239, 68, 68, 0.4)" : n.id === "authDB" || n.id === "analyticsDB" ? "rgba(245, 158, 11, 0.4)" : "rgba(59, 130, 246, 0.4)"}`,
          },
        }))
      );
      setShowInspector(true);
    },
    [setNodes]
  );

  return (
    <div className="flex-1 bg-surface-container-lowest rounded-lg border border-outline-variant relative overflow-hidden h-[380px] w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        className="custom-scrollbar"
      >
        <Background variant={BackgroundVariant.Dots} color="#1c1b1d" gap={18} size={1} />

        {/* Mode controls Panel */}
        <Panel position="top-right">
          <div className="flex bg-surface-container-highest border border-outline-variant/60 rounded-lg p-1 select-none">
            <button
              onClick={() => setMode("dependency")}
              className={cn(
                "px-3 py-1 rounded text-[10px] font-bold transition-all cursor-pointer",
                mode === "dependency" ? "bg-primary text-primary-foreground" : "text-on-surface-variant hover:text-on-surface"
              )}
            >
              Dependency Graph
            </button>
            <button
              onClick={() => setMode("tree")}
              className={cn(
                "px-3 py-1 rounded text-[10px] font-bold transition-all cursor-pointer",
                mode === "tree" ? "bg-primary text-primary-foreground" : "text-on-surface-variant hover:text-on-surface"
              )}
            >
              File Tree
            </button>
            <button
              onClick={() => setMode("data")}
              className={cn(
                "px-3 py-1 rounded text-[10px] font-bold transition-all cursor-pointer",
                mode === "data" ? "bg-primary text-primary-foreground" : "text-on-surface-variant hover:text-on-surface"
              )}
            >
              Data Flow
            </button>
          </div>
        </Panel>

        {/* Legend Overlay HUD on the Left */}
        <Panel position="top-left">
          <div className="bg-surface/90 border border-outline-variant p-4 rounded-xl backdrop-blur-md shadow-xl select-none text-[10px] md:text-xs font-medium space-y-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-primary shrink-0 animate-pulse" />
              <span>Core Services</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-tertiary shrink-0" />
              <span>Database Nodes</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-error shrink-0" />
              <span>Bottlenecks</span>
            </div>
          </div>
        </Panel>

        {/* Inspect Details Info card Overlay on the Right */}
        {showInspector && activeNode && (
          <Panel position="bottom-right">
            <div className="w-72 bg-surface/95 border border-outline-variant p-4 rounded-xl backdrop-blur-md shadow-2xl relative select-none">
              <div className="flex items-center justify-between mb-2">
                <span className={cn(
                  "font-mono text-xs font-bold",
                  activeNode.data.type === "core" && "text-primary",
                  activeNode.data.type === "database" && "text-tertiary",
                  activeNode.data.type === "bottleneck" && "text-error"
                )}>
                  {activeNode.data.label}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowInspector(false)}
                  className="size-5 hover:bg-surface-container-highest rounded text-on-surface-variant hover:text-on-surface cursor-pointer"
                >
                  <X className="size-3.5" />
                </Button>
              </div>

              <p className="text-[11px] leading-relaxed text-on-surface-variant/90 font-medium mb-3 select-text">
                {activeNode.data.description}
              </p>

              <div className="flex flex-col gap-1.5 border-t border-outline-variant/40 pt-2 text-[10px] md:text-xs font-semibold">
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Incoming Connections:</span>
                  <span className="text-on-surface font-bold font-mono">{activeNode.data.connections}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-on-surface-variant">Risk Profile:</span>
                  <span className={cn(
                    "font-bold",
                    activeNode.data.risk === "Low" && "text-green-400",
                    activeNode.data.risk === "Medium" && "text-tertiary",
                    activeNode.data.risk === "High" && "text-error"
                  )}>
                    {activeNode.data.risk}
                  </span>
                </div>
              </div>
            </div>
          </Panel>
        )}
      </ReactFlow>
    </div>
  );
}

export default function ArchitectureExplorer() {
  return (
    <ReactFlowProvider>
      <div className="md:col-span-12 bg-surface-container-low border border-outline-variant rounded-xl p-5 select-none shadow-sm flex flex-col justify-between">
        
        {/* Title and Descriptions */}
        <div className="mb-5 select-none">
          <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
            AI Architecture Explorer
          </h3>
          <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
            Dynamic relationship mapping of services and data flows
          </p>
        </div>

        {/* React Flow viewport frame */}
        <ExplorerContent />
      </div>
    </ReactFlowProvider>
  );
}
