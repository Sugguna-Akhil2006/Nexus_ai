"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { 
  ReactFlow, 
  MiniMap, 
  Controls, 
  Background, 
  BackgroundVariant,
  useNodesState, 
  useEdgesState, 
  addEdge, 
  Connection, 
  Edge,
  ReactFlowProvider,
  useReactFlow,
  Panel
} from "@xyflow/react";
import { Minus, Plus, Maximize, Search, Workflow, Undo2, Redo2, Terminal, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import EmptyState from "@/components/common/empty-state";

// Styles for React Flow
import "@xyflow/react/dist/style.css";

// Import custom node structures
import { nodeTypes, WorkflowNode, WorkflowNodeData } from "@/components/workflows/custom-nodes";
import NodeLibrary from "@/components/workflows/node-library";
import PropertiesPanel from "@/components/workflows/properties-panel";
import BottomActionBar from "@/components/workflows/bottom-action-bar";
import DashboardBreadcrumbs from "@/components/dashboard/breadcrumbs";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Initial nodes matching HTML layout coordinates
const INITIAL_NODES: WorkflowNode[] = [
  {
    id: "node-1",
    type: "webhookNode",
    position: { x: 450, y: 150 },
    data: { label: "API Ingest", type: "webhook", status: "idle" },
    selected: true,
    endpoint: "/v1/webhooks/ingest",
    auth: "Bearer Token",
    autoRetry: true,
    logPayloads: false,
    schema: '{\n  "type": "object",\n  "required": ["userId"],\n  "properties": {\n    "userId": { "type": "string" }\n  }\n}',
  } as any,
  {
    id: "node-2",
    type: "scriptNode",
    position: { x: 730, y: 280 },
    data: { label: "Transform Data", type: "script", status: "idle" },
    autoRetry: true,
    logPayloads: true,
    scriptCode: "def transform(payload):\n    # Transform input payload maps\n    payload['transformed'] = True\n    return payload",
  } as any,
  {
    id: "node-3",
    type: "dbNode",
    position: { x: 1050, y: 160 },
    data: { label: "Store Result", type: "db", status: "idle" },
    autoRetry: false,
    logPayloads: false,
    dbQuery: "INSERT INTO users_log (user_id, status) VALUES ($1, $2);",
  } as any,
];

// Initial connection edges
const INITIAL_EDGES: Edge[] = [
  {
    id: "edge-1-2",
    source: "node-1",
    sourceHandle: "output",
    target: "node-2",
    targetHandle: "input",
    style: { stroke: "#424754", strokeWidth: 2 },
  },
  {
    id: "edge-2-3",
    source: "node-2",
    sourceHandle: "output",
    target: "node-3",
    targetHandle: "input",
    style: { stroke: "#424754", strokeWidth: 2 },
  },
];

interface SimulationLog {
  timestamp: string;
  type: "info" | "success" | "error";
  message: string;
}

function WorkflowBuilderContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchQuery, setSearchQuery] = useState("");

  // Undo/Redo State History Stack
  const historyRef = useRef<{ nodes: WorkflowNode[]; edges: Edge[] }[]>([]);
  const historyIndexRef = useRef<number>(-1);
  const isUndoRedoAction = useRef<boolean>(false);

  // Simulation execution state
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationLogs, setSimulationLogs] = useState<SimulationLog[]>([]);

  const { screenToFlowPosition, zoomIn, zoomOut, fitView, getZoom } = useReactFlow();

  // Save state snapshot for history tracking
  const saveSnapshot = useCallback((currentNodes: WorkflowNode[], currentEdges: Edge[]) => {
    if (isUndoRedoAction.current) {
      isUndoRedoAction.current = false;
      return;
    }

    const snapshot = {
      nodes: JSON.parse(JSON.stringify(currentNodes)),
      edges: JSON.parse(JSON.stringify(currentEdges)),
    };

    // Slice off any redo states if we are inserting a new change
    const nextHistory = historyRef.current.slice(0, historyIndexRef.current + 1);
    nextHistory.push(snapshot);
    
    // Limit stack size to 50
    if (nextHistory.length > 50) {
      nextHistory.shift();
    }

    historyRef.current = nextHistory;
    historyIndexRef.current = nextHistory.length - 1;
  }, []);

  // Set initial snapshot on load
  useEffect(() => {
    if (historyRef.current.length === 0) {
      saveSnapshot(INITIAL_NODES, INITIAL_EDGES);
    }
  }, [saveSnapshot]);

  // Hook change events to trigger snapshot saves
  const handleNodesChange = useCallback((changes: any) => {
    onNodesChange(changes);
    // Push history snapshot for additions/deletions/position changes on dragEnd
    const hasPositionEnd = changes.some((c: any) => c.type === "position" && !c.dragging);
    const hasAddRemove = changes.some((c: any) => c.type === "add" || c.type === "remove");
    if (hasPositionEnd || hasAddRemove) {
      saveSnapshot(nodes, edges);
    }
  }, [onNodesChange, saveSnapshot, nodes, edges]);

  const handleEdgesChange = useCallback((changes: any) => {
    onEdgesChange(changes);
    saveSnapshot(nodes, edges);
  }, [onEdgesChange, saveSnapshot, nodes, edges]);

  // Connection created callback
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        style: { stroke: "#424754", strokeWidth: 2 },
      };
      setEdges((eds) => {
        const next = addEdge(newEdge, eds);
        saveSnapshot(nodes, next);
        return next;
      });
    },
    [setEdges, saveSnapshot, nodes]
  );

  const undo = useCallback(() => {
    if (historyIndexRef.current > 0) {
      isUndoRedoAction.current = true;
      historyIndexRef.current -= 1;
      const prev = historyRef.current[historyIndexRef.current];
      setNodes(prev.nodes);
      setEdges(prev.edges);
      toast.info("Undo operation performed");
    } else {
      toast.error("Nothing left to undo");
    }
  }, [setNodes, setEdges]);

  const redo = useCallback(() => {
    if (historyIndexRef.current < historyRef.current.length - 1) {
      isUndoRedoAction.current = true;
      historyIndexRef.current += 1;
      const next = historyRef.current[historyIndexRef.current];
      setNodes(next.nodes);
      setEdges(next.edges);
      toast.info("Redo operation performed");
    } else {
      toast.error("Nothing left to redo");
    }
  }, [setNodes, setEdges]);

  const activeNode = nodes.find((n) => n.selected);

  // Sync zoom value when canvas view shifts
  const handleViewportMove = useCallback(() => {
    setZoomLevel(Math.round(getZoom() * 100));
  }, [getZoom]);

  // Drop nodes from Palette onto Canvas
  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const dataStr = event.dataTransfer.getData("application/reactflow");
      if (!dataStr) return;

      const { nodeType, label } = JSON.parse(dataStr);

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNodeId = `node-${Date.now()}`;
      const newNode: WorkflowNode = {
        id: newNodeId,
        type: nodeType,
        position,
        data: { 
          label,
          type: nodeType.replace("Node", "") as any,
          status: "idle",
        },
        endpoint: nodeType === "webhookNode" ? "/v1/webhooks/custom" : undefined,
        auth: nodeType === "webhookNode" ? "None" : undefined,
        autoRetry: true,
        logPayloads: false,
        schema: "{\n  \"type\": \"object\"\n}",
        dbQuery: nodeType === "dbNode" ? "SELECT * FROM logs LIMIT 10;" : undefined,
        scriptCode: nodeType === "scriptNode" ? "def main(payload):\n    return payload" : undefined,
      } as any;

      setNodes((nds) => {
        const next = nds.concat(newNode);
        saveSnapshot(next, edges);
        return next;
      });
    },
    [screenToFlowPosition, setNodes, saveSnapshot, edges]
  );

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Keyboard shortcut listeners
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore key events if inside textareas or inputs
      if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") {
        return;
      }

      // Delete / Backspace to remove selected node
      if ((e.key === "Delete" || e.key === "Backspace") && activeNode) {
        e.preventDefault();
        handleDeleteNode(activeNode.id);
      }

      // Ctrl + Z to undo
      if ((e.ctrlKey || e.metaKey) && e.key === "z") {
        e.preventDefault();
        undo();
      }

      // Ctrl + Y to redo
      if ((e.ctrlKey || e.metaKey) && e.key === "y") {
        e.preventDefault();
        redo();
      }

      // + key to zoom in
      if (e.key === "+") {
        e.preventDefault();
        zoomIn();
      }

      // - key to zoom out
      if (e.key === "-") {
        e.preventDefault();
        zoomOut();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeNode, undo, redo, zoomIn, zoomOut]);

  // Update properties inputs inside Panel
  const handleUpdateNodeProperties = (id: string, updates: any) => {
    setNodes((nds) => {
      const next = nds.map((n) => {
        if (n.id === id) {
          return {
            ...n,
            data: {
              ...n.data,
              label: updates.label || n.data.label,
              subText: updates.subText || n.data.subText,
            },
            endpoint: updates.endpoint,
            auth: updates.auth,
            autoRetry: updates.autoRetry,
            logPayloads: updates.logPayloads,
            schema: updates.schema,
            dbQuery: updates.dbQuery,
            scriptCode: updates.scriptCode,
          } as any;
        }
        return n;
      });
      saveSnapshot(next, edges);
      return next;
    });
  };

  // Delete node
  const handleDeleteNode = (id: string) => {
    setNodes((nds) => {
      const nextNodes = nds.filter((n) => n.id !== id);
      setEdges((eds) => {
        const nextEdges = eds.filter((e) => e.source !== id && e.target !== id);
        saveSnapshot(nextNodes, nextEdges);
        return nextEdges;
      });
      return nextNodes;
    });
    toast.info("Node removed from canvas.");
  };

  // Convert selected node props to inspector panel schema format
  const getSelectedNodeInfo = () => {
    if (!activeNode) return null;
    return {
      id: activeNode.id,
      type: activeNode.type || "webhookNode",
      label: activeNode.data.label,
      subText: activeNode.data.subText,
      endpoint: (activeNode as any).endpoint,
      auth: (activeNode as any).auth,
      autoRetry: (activeNode as any).autoRetry,
      logPayloads: (activeNode as any).logPayloads,
      schema: (activeNode as any).schema,
      dbQuery: (activeNode as any).dbQuery,
      scriptCode: (activeNode as any).scriptCode,
    };
  };

  const handleNodeSearch = () => {
    if (!searchQuery.trim()) return;
    const matchedNode = nodes.find((n) =>
      n.data.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (matchedNode) {
      setNodes((nds) =>
        nds.map((n) => ({
          ...n,
          selected: n.id === matchedNode.id,
        }))
      );
      fitView({ nodes: [matchedNode], duration: 800 });
    } else {
      toast.error(`No node matched label: "${searchQuery}"`);
    }
  };

  // Run Debug execution trace simulation sequence
  const handleRunDebug = () => {
    if (isSimulating) return;
    
    setIsSimulating(true);
    setSimulationLogs([]);
    
    const timestampStr = () => new Date().toLocaleTimeString([], { hour12: false });
    
    const logs: SimulationLog[] = [];
    const addLog = (message: string, type: "info" | "success" | "error" = "info") => {
      logs.push({ timestamp: timestampStr(), type, message });
      setSimulationLogs([...logs]);
    };

    // Step 1: Webhook Node
    setTimeout(() => {
      addLog("Initializing debug execution trace...", "info");
      setNodes((nds) => nds.map(n => n.id === "node-1" ? { ...n, data: { ...n.data, status: "executing" } } : n));
      addLog("Node 'API Ingest' started executing.", "info");
    }, 100);

    setTimeout(() => {
      addLog("API Ingest webhook received mock payload: { userId: 'usr_8472' }", "info");
      addLog("Validating schema layout: PASSED.", "success");
      setNodes((nds) => nds.map(n => n.id === "node-1" ? { ...n, data: { ...n.data, status: "success" } } : n));
    }, 1200);

    // Step 2: Script Node
    setTimeout(() => {
      setNodes((nds) => nds.map(n => n.id === "node-2" ? { ...n, data: { ...n.data, status: "executing" } } : n));
      addLog("Node 'Transform Data' started executing.", "info");
      addLog("Compiling user Python script configuration...", "info");
    }, 2200);

    setTimeout(() => {
      addLog("Python script returned payload values map: { userId: 'usr_8472', transformed: true }", "success");
      setNodes((nds) => nds.map(n => n.id === "node-2" ? { ...n, data: { ...n.data, status: "success" } } : n));
    }, 3500);

    // Step 3: Database Node
    setTimeout(() => {
      setNodes((nds) => nds.map(n => n.id === "node-3" ? { ...n, data: { ...n.data, status: "executing" } } : n));
      addLog("Node 'Store Result' started executing.", "info");
      addLog("Writing payload map to PostgreSQL log tables...", "info");
    }, 4500);

    setTimeout(() => {
      addLog("DB Transaction committed successfully. Status: 201 Created.", "success");
      setNodes((nds) => nds.map(n => n.id === "node-3" ? { ...n, data: { ...n.data, status: "success" } } : n));
      addLog("Execution trace finished. All steps successfully processed.", "success");
      setIsSimulating(false);
      toast.success("Execution completed successfully!");
    }, 5800);
  };

  const handleClearStatus = () => {
    setNodes((nds) => nds.map(n => ({ ...n, data: { ...n.data, status: "idle" } })));
    setSimulationLogs([]);
  };

  return (
    <div className="flex-grow flex flex-col overflow-hidden relative h-full w-full">
      {/* Canvas + Inspector Row */}
      <div className="flex-grow flex flex-row overflow-hidden relative w-full h-full">
        {/* Floating search layer */}
        <div className="absolute top-6 left-[250px] z-30 hidden lg:flex items-center gap-2 bg-surface-container border border-outline-variant rounded-full px-3 py-1.5 shadow-xl">
          <Search className="size-4 text-on-surface-variant/70 shrink-0" />
          <input
            type="text"
            placeholder="Jump to node..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleNodeSearch()}
            className="bg-transparent border-none outline-none focus:ring-0 text-xs text-on-surface placeholder:text-on-surface-variant/40 py-1 px-1 w-44"
          />
        </div>

        {/* Undo/Redo Floater panel next to search */}
        <div className="absolute top-6 left-[500px] z-30 hidden lg:flex items-center gap-1 bg-surface-container border border-outline-variant rounded-full p-1 shadow-xl select-none">
          <Button
            variant="ghost"
            size="icon"
            onClick={undo}
            className="size-8 rounded-full hover:bg-surface-container-highest transition-colors cursor-pointer text-on-surface-variant hover:text-primary"
            title="Undo change (Ctrl+Z)"
          >
            <Undo2 className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={redo}
            className="size-8 rounded-full hover:bg-surface-container-highest transition-colors cursor-pointer text-on-surface-variant hover:text-primary"
            title="Redo change (Ctrl+Y)"
          >
            <Redo2 className="size-4" />
          </Button>
        </div>

        {/* Nodes Palette (Left Panel Overlay) */}
        <NodeLibrary />

        {/* Interactive React Flow Canvas (Center Panel) */}
        <div 
          className="flex-grow h-full relative" 
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onMove={handleViewportMove}
            onInit={(instance) => {
              setTimeout(() => {
                instance.fitView({ padding: 0.35 });
              }, 100);
            }}
            fitView
            fitViewOptions={{ padding: 0.35 }}
            className="custom-scrollbar"
          >
            <Background variant={BackgroundVariant.Dots} color="#262626" gap={24} size={1} />
            
            {/* Overlay Custom Zoom Toolbar */}
            <Panel position="bottom-center" className="!mb-6 !mr-10">
              <div className="bg-surface-container border border-outline-variant rounded-full p-1.5 flex items-center gap-1.5 shadow-xl select-none">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => zoomOut()}
                  className="size-8 text-on-surface hover:bg-surface-container-highest rounded-full transition-colors cursor-pointer"
                  title="Zoom Out (-)"
                >
                  <Minus className="size-4" />
                </Button>
                <span className="font-mono text-[10px] font-bold px-1.5 text-on-surface w-10 text-center">
                  {zoomLevel}%
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => zoomIn()}
                  className="size-8 text-on-surface hover:bg-surface-container-highest rounded-full transition-colors cursor-pointer"
                  title="Zoom In (+)"
                >
                  <Plus className="size-4" />
                </Button>
                <div className="w-[1px] h-4 bg-outline-variant mx-1" />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => fitView({ duration: 500 })}
                  className="size-8 text-on-surface hover:bg-surface-container-highest rounded-full transition-colors cursor-pointer"
                  title="Fit View Screen"
                >
                  <Maximize className="size-4" />
                </Button>
              </div>
            </Panel>

            {/* Minimap positioned lower-left corner */}
            <Panel position="bottom-left" className="!mb-6 !ml-6 hidden sm:block">
              <MiniMap 
                maskColor="rgba(19, 19, 21, 0.7)"
                nodeColor="#201f22"
                nodeStrokeColor="#424754"
                className="!bg-surface-container-low !border-outline-variant !m-0 rounded-lg shadow-xl"
              />
            </Panel>

            {/* Real-time terminal log console drawer */}
            {(isSimulating || simulationLogs.length > 0) && (
              <Panel position="bottom-left" className="!mb-[160px] !ml-6 z-30">
                <div className="w-[420px] bg-surface/95 backdrop-blur border border-outline-variant rounded-xl shadow-2xl p-4 flex flex-col gap-3 font-mono text-[10px]">
                  <div className="flex justify-between items-center border-b border-outline-variant/60 pb-2 select-none">
                    <span className="font-bold flex items-center gap-1.5 text-primary">
                      <Terminal className="size-4" />
                      SIMULATION LOG TRACE
                    </span>
                    <button 
                      onClick={handleClearStatus}
                      className="text-on-surface-variant hover:text-on-surface hover:underline bg-transparent border-none cursor-pointer"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="max-h-[140px] overflow-y-auto space-y-1.5 custom-scrollbar select-text">
                    {simulationLogs.map((log, idx) => (
                      <div key={idx} className={cn(
                        "leading-relaxed flex gap-2",
                        log.type === "success" ? "text-green-400" : log.type === "error" ? "text-red-400" : "text-on-surface-variant/80"
                      )}>
                        <span className="text-on-surface-variant/40 shrink-0">[{log.timestamp}]</span>
                        <span>{log.message}</span>
                      </div>
                    ))}
                    {isSimulating && (
                      <div className="flex gap-1.5 items-center pl-2 text-yellow-400 select-none animate-pulse">
                        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-ping" />
                        <span>Simulating trace...</span>
                      </div>
                    )}
                  </div>
                </div>
              </Panel>
            )}
          </ReactFlow>
        </div>

        {/* Properties Configuration Inspector */}
        <PropertiesPanel
          selectedNode={getSelectedNodeInfo()}
          onUpdate={handleUpdateNodeProperties}
          onDelete={handleDeleteNode}
        />
      </div>

      {/* Bottom actions triggers */}
      <BottomActionBar
        lastSaved="Just now"
        onRunDebug={handleRunDebug}
        onDeploy={() => toast.promise(
          new Promise((resolve) => setTimeout(resolve, 2000)),
          {
            loading: 'Serializing nodes, mapping validation schemas, and deploying triggers...',
            success: 'Workflow canvas successfully deployed to active production cluster.',
            error: 'Deployment failed.',
          }
        )}
      />
    </div>
  );
}

export default function WorkflowBuilderPage() {
  const [isEmpty, setIsEmpty] = useState(false);

  return (
    <ReactFlowProvider>
      <div className="flex-1 flex flex-col h-[calc(100vh-64px)] overflow-hidden relative">
        <div className="px-6 md:px-8 pt-4 flex items-center justify-between shrink-0">
          <DashboardBreadcrumbs />
          <Button 
            variant="ghost" 
            size="xs" 
            onClick={() => setIsEmpty(!isEmpty)} 
            className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
          >
            {isEmpty ? "● Show Flow Canvas" : "○ Simulate Empty State"}
          </Button>
        </div>

        {isEmpty ? (
          <div className="flex-grow flex items-center justify-center p-8 bg-surface-container-lowest/20 mb-16">
            <EmptyState
              icon={Workflow}
              title="No Workflow Canvas Created"
              description="Orchestrate automated triggers, code execution scripts, and database sync pipelines on an interactive grid canvas."
              actionLabel="Initialize Default Pipeline"
              onAction={() => {
                setIsEmpty(false);
                toast.success("Default ingest pipeline canvas provisioned!");
              }}
              accentColor="success"
            />
          </div>
        ) : (
          <WorkflowBuilderContent />
        )}
      </div>
    </ReactFlowProvider>
  );
}
