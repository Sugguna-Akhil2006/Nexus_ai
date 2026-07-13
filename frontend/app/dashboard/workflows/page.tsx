"use client";

import { useState, useCallback, DragEvent } from "react";
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
import { Minus, Plus, Maximize, Search, Workflow } from "lucide-react";
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

// Initial nodes matching HTML layout coordinates
const INITIAL_NODES: WorkflowNode[] = [];

// Initial connection edges
const INITIAL_EDGES: Edge[] = [];

function WorkflowBuilderContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchQuery, setSearchQuery] = useState("");

  const { screenToFlowPosition, zoomIn, zoomOut, fitView, getZoom } = useReactFlow();

  // Find currently active selected node
  const activeNode = nodes.find((n) => n.selected);

  // Connection created callback
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        style: { stroke: "#424754", strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // Sync zoom value when canvas view shifts
  const handleViewportMove = useCallback(() => {
    setZoomLevel(Math.round(getZoom() * 100));
  }, [getZoom]);

  // Drop nodes from Palette onto Canvas coordinates
  const handleDrop = useCallback(
    (event: DragEvent) => {
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
          type: nodeType.replace("Node", "") as any
        },
        // setup default configuration based on node type
        endpoint: nodeType === "webhookNode" ? "/v1/webhooks/custom" : undefined,
        auth: nodeType === "webhookNode" ? "None" : undefined,
        autoRetry: true,
        logPayloads: false,
        schema: "{\n  \"type\": \"object\"\n}",
      } as any;

      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  const handleDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Update properties inputs inside Panel
  const handleUpdateNodeProperties = (id: string, updates: any) => {
    setNodes((nds) =>
      nds.map((n) => {
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
          } as any;
        }
        return n;
      })
    );
  };

  // Delete node
  const handleDeleteNode = (id: string) => {
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
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
    };
  };

  // Inline Search capability filtering matching nodes labels on key query
  const handleNodeSearch = () => {
    if (!searchQuery.trim()) return;
    const matchedNode = nodes.find((n) =>
      n.data.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (matchedNode) {
      // Highlight selection focus
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

  const handleDeploy = async () => {
    const steps = nodes.map(n => ({
      step_id: n.id,
      name: n.data.label,
      step_type: n.type || "webhookNode",
      config: {
        endpoint: (n as any).endpoint || "",
        auth: (n as any).auth || "",
        autoRetry: (n as any).autoRetry || false,
        logPayloads: (n as any).logPayloads || false,
        schema: (n as any).schema || ""
      },
      dependencies: edges.filter(e => e.target === n.id).map(e => e.source)
    }));

    toast.promise(
      (async () => {
        const res = await fetch("/workflows", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: "Visual Pipeline canvas",
            description: "Interactive canvas workflow definition",
            steps
          })
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Deployment failed.");
        }
        const data = await res.json();
        sessionStorage.setItem("active_workflow_definition_id", data.definition_id);
        return data;
      })(),
      {
        loading: 'Serializing nodes, mapping validation schemas, and deploying triggers...',
        success: (data: any) => `Workflow canvas successfully deployed. ID: ${data.definition_id}`,
        error: (err: any) => err.message || 'Deployment failed.',
      }
    );
  };

  const handleRunDebug = async () => {
    const definitionId = sessionStorage.getItem("active_workflow_definition_id");
    if (!definitionId) {
      toast.error("Please deploy the workflow first before running execution.");
      return;
    }

    toast.promise(
      (async () => {
        const res = await fetch(`/workflows/${definitionId}/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Debug run execution failed.");
        }
        return await res.json();
      })(),
      {
        loading: 'Starting debug session and checking node endpoints...',
        success: (data: any) => `Debug trace completed. Instance ID: ${data.instance_id}`,
        error: (err: any) => err.message || 'Debug run failed.',
      }
    );
  };

  return (
    <div className="flex-1 flex overflow-hidden relative h-full w-full">
      {/* Floating search layer */}
      <div className="absolute top-6 left-[250px] z-30 hidden lg:flex items-center gap-2 bg-surface-container border border-outline-variant rounded-full px-3 py-1 shadow-xl">
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
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          onMove={handleViewportMove}
          fitView
          fitViewOptions={{ padding: 0.3 }}
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
                title="Zoom Out"
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
                title="Zoom In"
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
        </ReactFlow>
      </div>

      {/* Properties Configuration Inspector (Right Panel) */}
      <PropertiesPanel
        selectedNode={getSelectedNodeInfo()}
        onUpdate={handleUpdateNodeProperties}
        onDelete={handleDeleteNode}
      />

      {/* Floating Bottom Action Bar inside content */}
      <div className="absolute bottom-0 inset-x-0">
        <BottomActionBar
          lastSaved="Just now"
          onRunDebug={handleRunDebug}
          onDeploy={handleDeploy}
        />
      </div>
    </div>
  );
}

export default function WorkflowBuilderPage() {
  const [isEmpty, setIsEmpty] = useState(true);

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
