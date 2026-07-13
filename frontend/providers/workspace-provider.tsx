"use client";

import { createContext, useContext, useState, useEffect } from "react";
import { toast } from "sonner";

export interface WorkspaceSettings {
  industry: string;
  deployment: string;
  description: string;
}

export interface Workspace {
  workspace_id: string;
  name: string;
  owner_id: string;
  status: string;
  is_pinned: boolean;
  is_favorite: boolean;
  settings: WorkspaceSettings;
  metadata: Record<string, any>;
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  loading: boolean;
  switchWorkspace: (workspaceId: string) => Promise<void>;
  createWorkspace: (name: string, settings?: WorkspaceSettings) => Promise<Workspace | null>;
  updateWorkspace: (workspaceId: string, updates: Partial<Workspace>) => Promise<boolean>;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshWorkspaces = async () => {
    try {
      setLoading(true);
      const res = await fetch("/workspace");
      if (!res.ok) {
        // Fallback to old API path or mock
        const altRes = await fetch("/api/workspaces");
        if (altRes.ok) {
          const data = await altRes.json();
          // Map to standard WorkspaceDetail model format
          const mapped = (data.workspaces || []).map((w: any) => ({
            workspace_id: w.workspace_id,
            name: w.name,
            owner_id: w.owner_id,
            status: w.status || "active",
            is_pinned: false,
            is_favorite: false,
            settings: { industry: "Technology & SaaS", deployment: "private", description: "" },
            metadata: {}
          }));
          setWorkspaces(mapped);
          if (mapped.length > 0 && !activeWorkspace) {
            setActiveWorkspace(mapped[0]);
          }
          return;
        }
        throw new Error(`Fetch failed with HTTP status: ${res.status}`);
      }
      const data = await res.json();
      if (data.success && data.data) {
        setWorkspaces(data.data);
        if (data.data.length > 0) {
          // Keep active workspace sync or select first
          const currentActive = data.data.find(
            (w: Workspace) => w.workspace_id === activeWorkspace?.workspace_id
          ) || data.data[0];
          setActiveWorkspace(currentActive);
        }
      }
    } catch (e) {
      console.error("Failed to load workspaces, using simulator fallback", e);
      const fallback: Workspace[] = [
        {
          workspace_id: "ws-fallback",
          name: "Local Offline Workspace",
          owner_id: "admin",
          status: "active",
          is_pinned: true,
          is_favorite: true,
          settings: { industry: "Technology & SaaS", deployment: "private", description: "Default offline simulator workspace." },
          metadata: {}
        }
      ];
      setWorkspaces(fallback);
      if (!activeWorkspace) {
        setActiveWorkspace(fallback[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  const switchWorkspace = async (workspaceId: string) => {
    const ws = workspaces.find((w) => w.workspace_id === workspaceId);
    if (ws) {
      setActiveWorkspace(ws);
      toast.success(`Switched to workspace: ${ws.name}`);
      // In production, we might trigger page reload or state reset
      window.dispatchEvent(new CustomEvent("workspace-switched", { detail: ws }));
    }
  };

  const createWorkspace = async (name: string, settings?: WorkspaceSettings) => {
    try {
      const res = await fetch("/workspace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          owner_id: "admin",
          settings: settings || { industry: "Technology & SaaS", deployment: "private", description: "" }
        })
      });
      const data = await res.json();
      if (data.success && data.data) {
        toast.success(`Created workspace: ${name}`);
        await refreshWorkspaces();
        setActiveWorkspace(data.data);
        return data.data;
      }
      return null;
    } catch (e) {
      toast.error("Failed to create workspace");
      return null;
    }
  };

  const updateWorkspace = async (workspaceId: string, updates: Partial<Workspace>) => {
    try {
      const res = await fetch(`/workspace/${workspaceId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates)
      });
      const data = await res.json();
      if (data.success) {
        toast.success("Workspace settings updated");
        await refreshWorkspaces();
        return true;
      }
      return false;
    } catch (e) {
      toast.error("Failed to update workspace settings");
      return false;
    }
  };

  useEffect(() => {
    refreshWorkspaces();
  }, []);

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        loading,
        switchWorkspace,
        createWorkspace,
        updateWorkspace,
        refreshWorkspaces
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
