"use client";

import { useState, useEffect } from "react";
import { Copy, Check, Trash2, Play, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface SelectedNodeInfo {
  id: string;
  type: string;
  label: string;
  subText?: string;
  endpoint?: string;
  auth?: string;
  autoRetry?: boolean;
  logPayloads?: boolean;
  schema?: string;
  dbQuery?: string;
  scriptCode?: string;
}

interface PropertiesPanelProps {
  selectedNode: SelectedNodeInfo | null;
  onUpdate: (id: string, updates: Partial<SelectedNodeInfo>) => void;
  onDelete: (id: string) => void;
}

export default function PropertiesPanel({
  selectedNode,
  onUpdate,
  onDelete,
}: PropertiesPanelProps) {
  // Local state to manage buffer updates
  const [name, setName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [auth, setAuth] = useState("Bearer Token");
  const [autoRetry, setAutoRetry] = useState(true);
  const [logPayloads, setLogPayloads] = useState(false);
  const [schema, setSchema] = useState("");
  const [dbQuery, setDbQuery] = useState("");
  const [scriptCode, setScriptCode] = useState("");
  
  // Validation / Testing states
  const [copied, setCopied] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  // Sync buffer states when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setName(selectedNode.label || "");
      setEndpoint(selectedNode.endpoint || "/v1/webhooks/ingest");
      setAuth(selectedNode.auth || "Bearer Token");
      setAutoRetry(selectedNode.autoRetry !== false);
      setLogPayloads(!!selectedNode.logPayloads);
      setSchema(selectedNode.schema || '{\n  "type": "object",\n  "required": ["userId"],\n  "properties": {\n    "userId": { "type": "string" }\n  }\n}');
      setDbQuery(selectedNode.dbQuery || "SELECT * FROM users LIMIT 10;");
      setScriptCode(selectedNode.scriptCode || "def transform(payload):\n    # Transform input payload maps\n    payload['transformed'] = True\n    return payload");
      setJsonError(null);
    }
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <div className="w-[320px] bg-surface border-l border-outline-variant z-30 flex flex-col items-center justify-center p-8 text-center select-none shrink-0">
        <p className="text-sm text-on-surface-variant/50 font-normal">
          Select a node from the canvas to inspect and edit its properties.
        </p>
      </div>
    );
  }

  const handleCopyEndpoint = async () => {
    try {
      await navigator.clipboard.writeText(endpoint);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Endpoint URL copied");
    } catch (err) {
      console.error(err);
    }
  };

  const validateJson = (val: string): boolean => {
    if (!val.trim()) {
      setJsonError(null);
      return true;
    }
    try {
      JSON.parse(val);
      setJsonError(null);
      return true;
    } catch (e: any) {
      setJsonError(e.message || "Invalid JSON syntax");
      return false;
    }
  };

  const handleSchemaChange = (val: string) => {
    setSchema(val);
    validateJson(val);
  };

  const handleSaveChanges = () => {
    if (selectedNode.type === "webhookNode" && !validateJson(schema)) {
      toast.error("Cannot save: Invalid JSON validation schema.");
      return;
    }

    onUpdate(selectedNode.id, {
      label: name,
      endpoint,
      auth,
      autoRetry,
      logPayloads,
      schema,
      dbQuery,
      scriptCode,
    });
    toast.success("Node properties successfully saved!");
  };

  const handleTestNode = () => {
    setIsTesting(true);
    toast.promise(
      new Promise((resolve, reject) => {
        setTimeout(() => {
          if (selectedNode.type === "webhookNode" && !validateJson(schema)) {
            reject(new Error("Schema validation failure"));
          } else {
            resolve({ ok: true });
          }
        }, 1200);
      }),
      {
        loading: `Running test simulation for "${name}"...`,
        success: () => {
          setIsTesting(false);
          return `Test Successful! Node response: 200 OK.`;
        },
        error: (err) => {
          setIsTesting(false);
          return `Test Failed: ${err.message}`;
        }
      }
    );
  };

  const Toggle = ({ enabled, onChange }: { enabled: boolean; onChange: () => void }) => (
    <div 
      onClick={onChange}
      className={cn(
        "w-10 h-5 rounded-full relative cursor-pointer flex items-center px-1 transition-all duration-200 select-none border border-outline-variant/30",
        enabled ? "bg-primary" : "bg-surface-container-highest"
      )}
    >
      <div className={cn(
        "w-3.5 h-3.5 rounded-full shadow-sm transition-all duration-200",
        enabled ? "bg-white ml-auto" : "bg-outline mr-auto"
      )} />
    </div>
  );

  return (
    <div className="w-[320px] bg-surface border-l border-outline-variant z-30 flex flex-col select-none shrink-0 h-full">
      {/* Header */}
      <div className="p-6 border-b border-outline-variant shrink-0 flex justify-between items-start">
        <div className="min-w-0">
          <h2 className="text-lg md:text-xl font-bold tracking-tight text-on-surface mb-1">
            Properties
          </h2>
          <p className="text-xs text-on-surface-variant font-medium">
            Selected: <span className="text-primary font-bold">{name}</span>
          </p>
        </div>
        
        {/* Test Node Button */}
        <Button
          variant="outline"
          size="xs"
          disabled={isTesting}
          onClick={handleTestNode}
          className="flex items-center gap-1 hover:text-primary hover:border-primary text-[10px] cursor-pointer"
        >
          <Play className="size-3 text-primary fill-primary" />
          Test
        </Button>
      </div>

      {/* Scrollable Form */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5 custom-scrollbar text-xs md:text-sm">
        {/* Name input */}
        <div className="space-y-2">
          <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
            Node Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all text-xs md:text-sm"
          />
        </div>

        {/* Conditional inputs: Webhook Node */}
        {selectedNode.type === "webhookNode" && (
          <>
            {/* Endpoint */}
            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
                Endpoint URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={endpoint}
                  className="flex-1 bg-surface-container-low border border-outline-variant rounded-lg p-2.5 font-mono text-[11px] text-on-surface-variant/90 outline-none"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopyEndpoint}
                  className="p-2.5 border border-outline-variant rounded-lg hover:bg-surface-container-highest transition-colors cursor-pointer text-on-surface-variant hover:text-on-surface"
                >
                  {copied ? <Check className="size-4 text-green-400" /> : <Copy className="size-4" />}
                </Button>
              </div>
            </div>

            {/* Authentication */}
            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
                Authentication
              </label>
              <select
                value={auth}
                onChange={(e) => setAuth(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all cursor-pointer text-xs md:text-sm"
              >
                <option value="None">None</option>
                <option value="Bearer Token">Bearer Token</option>
                <option value="OAuth 2.0">OAuth 2.0</option>
              </select>
            </div>

            {/* JSON Validation Schema */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
                  Validation Schema (JSON)
                </label>
                {jsonError && (
                  <span className="text-[9px] text-red-400 font-bold flex items-center gap-0.5">
                    <AlertCircle className="size-2.5" />
                    Invalid JSON
                  </span>
                )}
              </div>
              <textarea
                value={schema}
                onChange={(e) => handleSchemaChange(e.target.value)}
                spellCheck={false}
                className={cn(
                  "w-full h-36 bg-surface-container border rounded-xl p-3 font-mono text-[11px] leading-relaxed focus:outline-none focus:ring-1 outline-none custom-scrollbar resize-none",
                  jsonError ? "border-red-500/50 focus:border-red-500 focus:ring-red-500 text-red-300" : "border-outline-variant focus:border-primary focus:ring-primary text-primary-fixed-dim"
                )}
              />
              {jsonError && (
                <p className="text-[10px] text-red-400/80 leading-normal pl-0.5">
                  {jsonError}
                </p>
              )}
            </div>
          </>
        )}

        {/* Conditional inputs: Script Node */}
        {selectedNode.type === "scriptNode" && (
          <div className="space-y-2">
            <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
              Script Execution Code
            </label>
            <textarea
              value={scriptCode}
              onChange={(e) => setScriptCode(e.target.value)}
              spellCheck={false}
              className="w-full h-48 bg-surface-container border border-outline-variant rounded-xl p-3 font-mono text-[11px] leading-relaxed text-primary-fixed-dim focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary outline-none custom-scrollbar resize-none"
            />
          </div>
        )}

        {/* Conditional inputs: Database Node */}
        {selectedNode.type === "dbNode" && (
          <div className="space-y-2">
            <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">
              SQL Database Query
            </label>
            <textarea
              value={dbQuery}
              onChange={(e) => setDbQuery(e.target.value)}
              spellCheck={false}
              className="w-full h-32 bg-surface-container border border-outline-variant rounded-xl p-3 font-mono text-[11px] leading-relaxed text-primary-fixed-dim focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary outline-none custom-scrollbar resize-none"
            />
          </div>
        )}

        {/* Retry/Log Toggles */}
        <div className="p-4 bg-surface-container-low border border-outline-variant rounded-xl space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold text-on-surface">Auto-retry</span>
            <Toggle enabled={autoRetry} onChange={() => setAutoRetry(!autoRetry)} />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs font-semibold text-on-surface">Log payloads</span>
            <Toggle enabled={logPayloads} onChange={() => setLogPayloads(!logPayloads)} />
          </div>
        </div>
      </div>

      {/* Save / Delete Footer */}
      <div className="p-6 border-t border-outline-variant flex gap-3 shrink-0">
        <Button
          onClick={handleSaveChanges}
          className="flex-grow bg-primary text-primary-foreground font-bold py-5 rounded-lg hover:opacity-90 active:scale-98 transition-all cursor-pointer border-none shadow-md shadow-primary/10 text-xs md:text-sm"
        >
          Save Changes
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={() => onDelete(selectedNode.id)}
          className="p-3 border border-error/50 hover:border-error text-error hover:bg-error/10 rounded-lg transition-colors cursor-pointer size-10 shrink-0"
          title="Delete node"
        >
          <Trash2 className="size-4 text-error" />
        </Button>
      </div>
    </div>
  );
}
