"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
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

// Load React Flow rendering style assets
import "@xyflow/react/dist/style.css";

// Custom node typings
interface ServiceNodeData extends Record<string, unknown> {
  label: string;
  type: "core" | "database" | "bottleneck";
  description: string;
  connections: number;
  risk: "Low" | "Medium" | "High";
}

type ServiceNode = Node<ServiceNodeData>;

// ─── 1. DEPENDENCY NODE GRAPH DATASET ──────────────────────────────────────────
const DEPENDENCY_NODES: ServiceNode[] = [
  {
    id: "gateway",
    position: { x: 40, y: 160 },
    data: {
      label: "API Gateway",
      type: "core",
      description: "Gateway proxy layer handling authentication, TLS termination, and request routing.",
      connections: 32,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "balancer",
    position: { x: 220, y: 160 },
    data: {
      label: "Load Balancer",
      type: "core",
      description: "Nginx traffic distributor balancing API requests across backend clusters.",
      connections: 28,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "auth",
    position: { x: 410, y: 50 },
    data: {
      label: "Auth Service",
      type: "core",
      description: "Service managing JWT token verifications, user sessions, and key storage.",
      connections: 12,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "ingest",
    position: { x: 410, y: 270 },
    data: {
      label: "Ingest Service",
      type: "bottleneck",
      description: "Heavy database writer ingestion API experiencing queue throttling under peak load.",
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
      width: 140,
    },
  },
  {
    id: "inference",
    position: { x: 410, y: 160 },
    data: {
      label: "Inference Engine",
      type: "core",
      description: "AI neural vector lookup pipeline connecting client Prompts with LLM models.",
      connections: 24,
      risk: "Medium",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "authDB",
    position: { x: 600, y: 50 },
    data: {
      label: "User Auth DB",
      type: "database",
      description: "PostgreSQL master DB hosting credentials profiles.",
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
      width: 140,
    },
  },
  {
    id: "redis",
    position: { x: 600, y: 160 },
    data: {
      label: "Redis Cache",
      type: "database",
      description: "In-memory cache caching frequent vector results.",
      connections: 18,
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
      width: 140,
    },
  },
  {
    id: "rabbitmq",
    position: { x: 600, y: 270 },
    data: {
      label: "RabbitMQ Queue",
      type: "core",
      description: "Message broker queuing asynchronous pipeline ingestion jobs.",
      connections: 15,
      risk: "Medium",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "worker",
    position: { x: 780, y: 270 },
    data: {
      label: "Pipeline Worker",
      type: "core",
      description: "Python worker consumer processing batch ingestion files.",
      connections: 8,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "timescaledb",
    position: { x: 960, y: 270 },
    data: {
      label: "TimescaleDB",
      type: "database",
      description: "Timeseries analytical database storage cluster.",
      connections: 10,
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
      width: 140,
    },
  },
];

const DEPENDENCY_EDGES: Edge[] = [
  { id: "de-gate-bal", source: "gateway", target: "balancer", animated: true, style: { stroke: "#3b82f6" } },
  { id: "de-bal-auth", source: "balancer", target: "auth", style: { stroke: "#424754" } },
  { id: "de-bal-inf", source: "balancer", target: "inference", style: { stroke: "#424754" } },
  { id: "de-bal-ing", source: "balancer", target: "ingest", animated: true, style: { stroke: "#ef4444" } },
  { id: "de-auth-db", source: "auth", target: "authDB", style: { stroke: "#424754" } },
  { id: "de-inf-redis", source: "inference", target: "redis", style: { stroke: "#424754" } },
  { id: "de-ing-rmq", source: "ingest", target: "rabbitmq", animated: true, style: { stroke: "#ef4444" } },
  { id: "de-rmq-wrk", source: "rabbitmq", target: "worker", style: { stroke: "#424754" } },
  { id: "de-wrk-ts", source: "worker", target: "timescaledb", style: { stroke: "#424754" } },
];

// ─── 2. FILE TREE GRAPH DATASET ────────────────────────────────────────────────
const TREE_NODES: ServiceNode[] = [
  {
    id: "root",
    position: { x: 50, y: 160 },
    data: {
      label: "repository-root/",
      type: "core",
      description: "Workspace repository root container.",
      connections: 3,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "src",
    position: { x: 230, y: 100 },
    data: {
      label: "src/",
      type: "core",
      description: "Source code directory containing backend implementations.",
      connections: 4,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "config",
    position: { x: 230, y: 220 },
    data: {
      label: "config/",
      type: "core",
      description: "Global properties definitions and service configurations.",
      connections: 2,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "main_py",
    position: { x: 410, y: 30 },
    data: {
      label: "main.py",
      type: "core",
      description: "Application runtime main entry point initiating server instances.",
      connections: 5,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "routers",
    position: { x: 410, y: 110 },
    data: {
      label: "routers/",
      type: "core",
      description: "FastAPI REST API controllers and routing namespaces.",
      connections: 3,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "services",
    position: { x: 410, y: 190 },
    data: {
      label: "services/",
      type: "bottleneck",
      description: "Heavy CPU pipelines where computational bottleneck risks exist.",
      connections: 6,
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
      width: 140,
    },
  },
  {
    id: "auth_py",
    position: { x: 590, y: 70 },
    data: {
      label: "routers/auth.py",
      type: "core",
      description: "Routing endpoints for JWT validation and user permissions verification.",
      connections: 2,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "vector_py",
    position: { x: 590, y: 150 },
    data: {
      label: "services/vector.py",
      type: "core",
      description: "Service script executing similarity matching on vector stores.",
      connections: 3,
      risk: "Medium",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "db_py",
    position: { x: 590, y: 230 },
    data: {
      label: "services/db.py",
      type: "database",
      description: "Database connectors pool initializing persistent sessions.",
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
      width: 140,
    },
  },
];

const TREE_EDGES: Edge[] = [
  { id: "te-root-src", source: "root", target: "src", style: { stroke: "#424754" } },
  { id: "te-root-cfg", source: "root", target: "config", style: { stroke: "#424754" } },
  { id: "te-src-main", source: "src", target: "main_py", style: { stroke: "#424754" } },
  { id: "te-src-rtr", source: "src", target: "routers", style: { stroke: "#424754" } },
  { id: "te-src-srv", source: "src", target: "services", animated: true, style: { stroke: "#ef4444" } },
  { id: "te-rtr-ath", source: "routers", target: "auth_py", style: { stroke: "#424754" } },
  { id: "te-srv-vec", source: "services", target: "vector_py", style: { stroke: "#424754" } },
  { id: "te-srv-db", source: "services", target: "db_py", style: { stroke: "#424754" } },
];

// ─── 3. DATA FLOW GRAPH DATASET ────────────────────────────────────────────────
const DATA_NODES: ServiceNode[] = [
  {
    id: "request",
    position: { x: 50, y: 160 },
    data: {
      label: "Client HTTP Request",
      type: "core",
      description: "HTTPS request carrying JWT authorizations and payload details.",
      connections: 1,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "parser",
    position: { x: 230, y: 160 },
    data: {
      label: "JSON Parser",
      type: "core",
      description: "Validation parser executing OpenAPI schema checks on requests.",
      connections: 2,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "auth_guard",
    position: { x: 410, y: 160 },
    data: {
      label: "Authentication Guard",
      type: "core",
      description: "Token audit gate checking user permissions and rate caps.",
      connections: 3,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
  {
    id: "llm_pipeline",
    position: { x: 590, y: 160 },
    data: {
      label: "LLM Pipeline Dispatch",
      type: "bottleneck",
      description: "Heavy NLP computation block containing vector indices matching.",
      connections: 5,
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
      width: 140,
    },
  },
  {
    id: "db_log",
    position: { x: 770, y: 100 },
    data: {
      label: "SQL Sync Logger",
      type: "database",
      description: "Asynchronous SQL transactional database write step.",
      connections: 2,
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
      width: 140,
    },
  },
  {
    id: "response",
    position: { x: 770, y: 220 },
    data: {
      label: "HTTP Response API",
      type: "core",
      description: "Response encoder serializing responses back to clients.",
      connections: 1,
      risk: "Low",
    },
    style: {
      background: "rgba(59, 130, 246, 0.15)",
      border: "1px solid rgba(59, 130, 246, 0.4)",
      borderRadius: "8px",
      color: "#3b82f6",
      fontWeight: "bold",
      fontSize: "11px",
      padding: "10px",
      width: 140,
    },
  },
];

const DATA_EDGES: Edge[] = [
  { id: "da-req-par", source: "request", target: "parser", animated: true, style: { stroke: "#3b82f6" } },
  { id: "da-par-grd", source: "parser", target: "auth_guard", animated: true, style: { stroke: "#3b82f6" } },
  { id: "da-grd-llm", source: "auth_guard", target: "llm_pipeline", animated: true, style: { stroke: "#ef4444" } },
  { id: "da-llm-log", source: "llm_pipeline", target: "db_log", style: { stroke: "#424754" } },
  { id: "da-llm-res", source: "llm_pipeline", target: "response", animated: true, style: { stroke: "#3b82f6" } },
];

function ExplorerContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState<ServiceNode>(DEPENDENCY_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(DEPENDENCY_EDGES);
  const [mode, setMode] = useState<"dependency" | "tree" | "data">("dependency");
  const [showInspector, setShowInspector] = useState(true);

  // Sync state nodes when mode changes
  useEffect(() => {
    if (mode === "dependency") {
      setNodes(DEPENDENCY_NODES);
      setEdges(DEPENDENCY_EDGES);
    } else if (mode === "tree") {
      setNodes(TREE_NODES);
      setEdges(TREE_EDGES);
    } else if (mode === "data") {
      setNodes(DATA_NODES);
      setEdges(DATA_EDGES);
    }
  }, [mode, setNodes, setEdges]);

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
              ? `2px solid ${n.id === "ingest" || n.id === "services" || n.id === "llm_pipeline" ? "#ef4444" : n.id === "authDB" || n.id === "analyticsDB" || n.id === "db_py" || n.id === "db_log" ? "#f59e0b" : "#3b82f6"}`
              : `1px solid ${n.id === "ingest" || n.id === "services" || n.id === "llm_pipeline" ? "rgba(239, 68, 68, 0.4)" : n.id === "authDB" || n.id === "analyticsDB" || n.id === "db_py" || n.id === "db_log" ? "rgba(245, 158, 11, 0.4)" : "rgba(59, 130, 246, 0.4)"}`,
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
          <div className="flex bg-surface-container-highest border border-outline-variant/60 rounded-lg p-1 select-none animate-fade-in">
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
