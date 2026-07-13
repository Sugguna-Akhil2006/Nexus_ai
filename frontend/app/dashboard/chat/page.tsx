"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Bot, ChevronRight, Clock, Cpu, History, MessageSquare, RefreshCw, TerminalSquare, Wrench } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import ConversationList, { Conversation } from "@/components/chat/conversation-list";
import ChatMessages, { Message } from "@/components/chat/chat-messages";
import MessageInput from "@/components/chat/message-input";
import SuggestedPrompts from "@/components/chat/suggested-prompts";
import { AttachedFile } from "@/components/chat/file-attachments";
import EmptyState from "@/components/common/empty-state";
import { useWorkspace } from "@/providers/workspace-provider";
import { cn } from "@/lib/utils";

const SUGGESTED_QUESTIONS = [
  "Analyze this workspace context",
  "Summarize the uploaded documents",
  "Plan the next workflow step",
];

interface Agent {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  supported_tools: string[];
  supported_models: string[];
  status: string;
  state: string;
  provider: string;
  response_time_ms: number;
  runtime: string;
}

interface ConsoleEvent {
  timestamp: string;
  event: string;
}

interface ExecutionMetadata {
  active_agent?: string;
  agent_id?: string;
  agent_status?: string;
  selected_provider?: string;
  provider?: string;
  runtime?: string;
  response_time?: string;
  total_request_duration?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  workflow_trace?: Array<{ step: string; status: string; time: string; error?: string }>;
  event_logs?: ConsoleEvent[];
}

interface ConversationRow {
  conversation_id: string;
  title: string;
  created_at?: string;
}

interface MessageRow {
  message_id: string;
  role: string;
  content: string;
  provider?: string;
  execution_metadata?: unknown;
}

const parseMaybeJson = (value: unknown) => {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

export default function ChatPage() {
  const { activeWorkspace } = useWorkspace();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [agentsError, setAgentsError] = useState("");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [pendingAgentId, setPendingAgentId] = useState("");

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [agentStatus, setAgentStatus] = useState("Idle");
  const [executionProgress, setExecutionProgress] = useState("Waiting for message");
  const [lastMetadata, setLastMetadata] = useState<ExecutionMetadata | null>(null);
  const [consoleEvents, setConsoleEvents] = useState<ConsoleEvent[]>([]);

  const socketRef = useRef<WebSocket | null>(null);
  const activeWorkspaceId = activeWorkspace?.workspace_id || "default-ws";
  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId) || null,
    [agents, selectedAgentId]
  );

  const fetchAgents = async () => {
    setAgentsLoading(true);
    setAgentsError("");
    try {
      const res = await fetch("/api/agents");
      if (!res.ok) throw new Error("Agent registry unavailable");
      const data = await res.json();
      const loadedAgents: Agent[] = data.agents || [];
      setAgents(loadedAgents);
      setSelectedAgentId((current) => current || loadedAgents[0]?.id || "");
    } catch (error) {
      setAgentsError(error instanceof Error ? error.message : "Failed to load agents");
      setAgents([]);
      setSelectedAgentId("");
    } finally {
      setAgentsLoading(false);
    }
  };

  const fetchConversations = async () => {
    const res = await fetch(`/api/chat/history?workspace_id=${activeWorkspaceId}`);
    if (!res.ok) return;
    const data = await res.json();
    const mapped: Conversation[] = ((data.conversations || []) as ConversationRow[]).map((conversation) => ({
      id: conversation.conversation_id,
      title: conversation.title,
      updatedAt: conversation.created_at ? new Date(conversation.created_at).toLocaleDateString() : "Just now",
      category: "Today",
    }));
    setConversations(mapped);
    if (mapped.length > 0 && !activeId) setActiveId(mapped[0].id);
    if (mapped.length === 0) {
      setActiveId("");
      setMessages([]);
    }
  };

  const fetchMessages = async (id: string) => {
    if (!id) {
      setMessages([]);
      return;
    }
    const res = await fetch(`/api/chat/history?session_id=${id}`);
    if (!res.ok) return;
    const data = await res.json();
    const mapped: Message[] = ((data.messages || []) as MessageRow[]).map((message) => {
      const metadata = parseMaybeJson(message.execution_metadata) as ExecutionMetadata | undefined;
      return {
        id: message.message_id,
        sender: message.role === "user" ? "user" : "ai",
        text: message.content,
        agentName: metadata?.active_agent,
        provider: metadata?.provider || message.provider,
        latencyMs: typeof metadata?.response_time === "string" ? Number.parseFloat(metadata.response_time) * 1000 : undefined,
      };
    });
    setMessages(mapped);
  };

  /* eslint-disable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */
  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [activeWorkspaceId]);

  useEffect(() => {
    fetchMessages(activeId);
  }, [activeId]);
  /* eslint-enable react-hooks/set-state-in-effect, react-hooks/exhaustive-deps */

  const handleSelectConversation = (id: string) => {
    setActiveId(id);
    setInputText("");
    setAttachedFiles([]);
  };

  const handleDeleteConversation = (id: string, event: React.MouseEvent) => {
    event.stopPropagation();
    const remaining = conversations.filter((conversation) => conversation.id !== id);
    setConversations(remaining);
    if (activeId === id) {
      setActiveId(remaining[0]?.id || "");
      if (remaining.length === 0) setMessages([]);
    }
  };

  const handleNewChat = () => {
    setActiveId("");
    setMessages([]);
    setInputText("");
    setAttachedFiles([]);
    setLastMetadata(null);
    setConsoleEvents([]);
  };

  const createSession = async (agentId: string, titleSeed: string) => {
    const res = await fetch("/api/chat/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_id: activeWorkspaceId,
        selected_agent: agentId,
        user_id: "admin",
        title: `${agents.find((agent) => agent.id === agentId)?.name || "Agent"}: ${titleSeed.slice(0, 24)}`,
        selected_project: activeWorkspace?.name || activeWorkspaceId,
        knowledge_context: { workspace_name: activeWorkspace?.name || "Default Workspace" },
        uploaded_documents: attachedFiles.map((file) => ({ name: file.name, size: file.size, type: file.type })),
      }),
    });
    if (!res.ok) throw new Error("Unable to create chat session");
    const data = await res.json();
    return data.session.conversation_id as string;
  };

  const handleAgentChange = (agentId: string) => {
    if (agentId === selectedAgentId) return;
    if (messages.length > 0) {
      setPendingAgentId(agentId);
      return;
    }
    setSelectedAgentId(agentId);
  };

  const confirmAgentSwitch = () => {
    setSelectedAgentId(pendingAgentId);
    setPendingAgentId("");
    setConsoleEvents((events) => [
      ...events,
      { timestamp: new Date().toISOString(), event: "Agent switched for subsequent messages" },
    ]);
  };

  const handleSendPrompt = async () => {
    if ((!inputText.trim() && attachedFiles.length === 0) || !selectedAgent) return;

    const userMsgText = inputText;
    const currentFiles = attachedFiles;
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: userMsgText,
      attachments: currentFiles.length > 0 ? currentFiles : undefined,
    };

    setMessages((previous) => [...previous, userMsg]);
    setInputText("");
    setAttachedFiles([]);
    setIsTyping(true);
    setAgentStatus("Routing");
    setExecutionProgress(`Sending to ${selectedAgent.name}`);

    try {
      const sessionId = activeId || await createSession(selectedAgent.id, userMsgText || "New Conversation");
      if (!activeId) {
        setActiveId(sessionId);
        fetchConversations();
      }

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost = window.location.hostname === "localhost" ? "localhost:8000" : window.location.host;
      const wsUrl = `${protocol}//${wsHost}/ws/chat/${sessionId}`;
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      const assistantMsgId = `ai-${Date.now()}`;
      let assistantText = "";
      const startedAt = performance.now();

      socket.onopen = () => {
        setAgentStatus("Executing");
        setExecutionProgress("Streaming response");
        socket.send(JSON.stringify({
          action: "send_message",
          session_id: sessionId,
          conversation_id: sessionId,
          workspace_id: activeWorkspaceId,
          selected_agent: selectedAgent.id,
          message: userMsgText,
          user_id: "admin",
          attachments: currentFiles,
          selected_project: activeWorkspace?.name || activeWorkspaceId,
          knowledge_context: {
            workspace_id: activeWorkspaceId,
            workspace_name: activeWorkspace?.name || "Default Workspace",
          },
          uploaded_documents: currentFiles.map((file) => ({ name: file.name, size: file.size, type: file.type })),
        }));
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
          setIsTyping(false);
          setAgentStatus("Error");
          setExecutionProgress(data.error);
          return;
        }

        if (data.token) {
          assistantText += data.token;
          setIsTyping(false);
          setMessages((previous) => {
            const filtered = previous.filter((message) => message.id !== assistantMsgId);
            return [
              ...filtered,
              {
                id: assistantMsgId,
                sender: "ai",
                text: assistantText,
                agentName: data.active_agent || selectedAgent.name,
                provider: data.provider || selectedAgent.provider,
                latencyMs: Math.round(performance.now() - startedAt),
              },
            ];
          });
        }

        if (data.metadata) {
          setLastMetadata(data.metadata);
          setConsoleEvents(data.metadata.event_logs || []);
          setAgentStatus(data.metadata.agent_status || "Completed");
          setExecutionProgress("Conversation saved");
          fetchConversations();
        }
      };

      socket.onerror = () => {
        setIsTyping(false);
        setAgentStatus("Error");
        setExecutionProgress("WebSocket connection failed");
      };

      socket.onclose = () => {
        setIsTyping(false);
        if (agentStatus !== "Error") setAgentStatus("Idle");
      };
    } catch (error) {
      setIsTyping(false);
      setAgentStatus("Error");
      setExecutionProgress(error instanceof Error ? error.message : "Message failed");
    }
  };

  const activeConversationTitle = conversations.find((conversation) => conversation.id === activeId)?.title || "AI Chat";
  const pendingAgent = agents.find((agent) => agent.id === pendingAgentId);

  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background text-on-background">
      <div className="hidden md:flex">
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNewChat={handleNewChat}
        />
      </div>

      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <div className="h-12 border-b border-outline-variant/50 px-6 flex items-center justify-between shrink-0 bg-surface/40 select-none">
          <div className="flex items-center gap-1 text-xs text-on-surface-variant font-medium min-w-0">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="md:hidden size-8 text-on-surface-variant hover:text-on-surface mr-1.5 cursor-pointer">
                  <History className="size-4.5" />
                  <span className="sr-only">Conversation History</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 w-64 border-r border-outline-variant bg-surface" showCloseButton={true}>
                <SheetTitle className="sr-only">Recent Conversations</SheetTitle>
                <SheetDescription className="sr-only">History panel of prior chat logs.</SheetDescription>
                <ConversationList
                  conversations={conversations}
                  activeId={activeId}
                  onSelect={handleSelectConversation}
                  onDelete={handleDeleteConversation}
                  onNewChat={handleNewChat}
                />
              </SheetContent>
            </Sheet>
            <span>Workspace</span>
            <ChevronRight className="size-3.5 text-on-surface-variant/40" />
            <span className="text-primary font-semibold truncate max-w-[160px] sm:max-w-xs">{activeConversationTitle}</span>
          </div>

          <div className="flex items-center gap-2 text-[10px] font-bold text-on-surface-variant/80 uppercase tracking-widest font-mono">
            <span className={cn("w-2 h-2 rounded-full", selectedAgent ? "bg-primary animate-pulse" : "bg-red-500")} />
            <span>{selectedAgent ? selectedAgent.name : "No Agent"}</span>
          </div>
        </div>

        <div className="flex-1 min-h-0 grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex flex-col min-h-0 overflow-hidden">
            <section className="border-b border-outline-variant/50 bg-surface-container-low/40 px-6 py-4">
              <div className="max-w-4xl mx-auto grid gap-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-on-surface">
                    <Bot className="size-4 text-primary" />
                    <span>AI Agent</span>
                  </div>
                  <Button variant="ghost" size="sm" onClick={fetchAgents} className="h-8 gap-2">
                    <RefreshCw className="size-3.5" />
                    Refresh
                  </Button>
                </div>

                {agentsLoading ? (
                  <div className="text-sm text-on-surface-variant">Loading agents from Runtime Agent Registry...</div>
                ) : agents.length === 0 ? (
                  <div className="rounded border border-outline-variant bg-surface px-4 py-3 text-sm text-on-surface">
                    No AI Agents Available
                    {agentsError && <span className="block text-xs text-red-400 mt-1">{agentsError}</span>}
                  </div>
                ) : (
                  <div className="grid gap-3 md:grid-cols-[240px_minmax(0,1fr)]">
                    <select
                      value={selectedAgentId}
                      onChange={(event) => handleAgentChange(event.target.value)}
                      className="h-10 rounded border border-outline-variant bg-surface px-3 text-sm text-on-surface outline-none focus:border-primary"
                    >
                      {agents.map((agent) => (
                        <option key={agent.id} value={agent.id}>{agent.name}</option>
                      ))}
                    </select>

                    {selectedAgent && (
                      <div className="rounded border border-outline-variant bg-surface px-4 py-3">
                        <div className="flex flex-wrap items-center gap-3 text-xs text-on-surface-variant">
                          <span className="font-semibold text-on-surface">{selectedAgent.description}</span>
                          <span className="inline-flex items-center gap-1"><Activity className="size-3.5" /> {selectedAgent.status}</span>
                          <span className="inline-flex items-center gap-1"><Clock className="size-3.5" /> {selectedAgent.response_time_ms}ms</span>
                          <span className="inline-flex items-center gap-1"><Cpu className="size-3.5" /> {selectedAgent.provider}</span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {selectedAgent.capabilities.map((capability) => (
                            <span key={capability} className="rounded bg-primary/10 px-2 py-1 text-[10px] font-semibold text-primary">{capability}</span>
                          ))}
                        </div>
                        <div className="mt-2 grid gap-1 text-[11px] text-on-surface-variant">
                          <span>Models: {selectedAgent.supported_models.join(", ") || "None reported"}</span>
                          <span>Tools: {selectedAgent.supported_tools.join(", ") || "None reported"}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </section>

            {agents.length === 0 && !agentsLoading ? (
              <div className="flex-1 flex items-center justify-center p-6 bg-surface-container-lowest/20">
                <EmptyState
                  icon={MessageSquare}
                  title="No AI Agents Available"
                  description="The Runtime Agent Registry did not return any agents for chat routing."
                  actionLabel="Refresh Agents"
                  onAction={fetchAgents}
                  accentColor="tertiary"
                />
              </div>
            ) : (
              <>
                <div className="flex-1 overflow-y-auto flex flex-col justify-between">
                  <ChatMessages messages={messages} />

                  {isTyping && (
                    <div className="px-6 py-2 flex items-center gap-2 text-xs text-on-surface-variant max-w-4xl mx-auto w-full select-none animate-pulse">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-75" />
                      <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-150" />
                      <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-300" />
                      <span className="ml-1 leading-none pt-0.5">{selectedAgent?.name || "Agent"} is typing...</span>
                    </div>
                  )}

                  {messages.length < 5 && (
                    <div className="max-w-4xl mx-auto w-full px-6 pb-4">
                      <SuggestedPrompts prompts={SUGGESTED_QUESTIONS} onClick={setInputText} />
                    </div>
                  )}
                </div>

                <MessageInput
                  text={inputText}
                  onChangeText={setInputText}
                  files={attachedFiles}
                  onAddFile={(file) => setAttachedFiles((files) => [...files, file])}
                  onRemoveFile={(id) => setAttachedFiles((files) => files.filter((file) => file.id !== id))}
                  onSend={handleSendPrompt}
                />
              </>
            )}
          </div>

          <aside className="hidden xl:flex flex-col border-l border-outline-variant/50 bg-surface-container-low/30 min-h-0">
            <div className="p-4 border-b border-outline-variant/50">
              <div className="flex items-center gap-2 text-sm font-semibold text-on-surface">
                <TerminalSquare className="size-4 text-primary" />
                <span>Developer Console</span>
              </div>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto custom-scrollbar text-xs">
              <div className="grid gap-2 rounded border border-outline-variant bg-surface p-3">
                <span>Active Agent: <strong>{lastMetadata?.active_agent || selectedAgent?.name || "None"}</strong></span>
                <span>Provider: <strong>{lastMetadata?.selected_provider || selectedAgent?.provider || "Unknown"}</strong></span>
                <span>Runtime: <strong>{lastMetadata?.runtime || selectedAgent?.runtime || "nexus-runtime"}</strong></span>
                <span>Status: <strong>{agentStatus}</strong></span>
                <span>Progress: <strong>{executionProgress}</strong></span>
                <span>Token Usage: <strong>{lastMetadata?.total_tokens ?? 0}</strong></span>
                <span>Latency: <strong>{lastMetadata?.total_request_duration || lastMetadata?.response_time || "0s"}</strong></span>
              </div>

              <div className="rounded border border-outline-variant bg-surface p-3">
                <div className="mb-2 flex items-center gap-2 font-semibold text-on-surface">
                  <Wrench className="size-3.5 text-primary" />
                  Execution Logs
                </div>
                <div className="space-y-2">
                  {(lastMetadata?.workflow_trace || []).map((step) => (
                    <div key={`${step.step}-${step.time}`} className="flex items-center justify-between gap-2 text-on-surface-variant">
                      <span className="truncate">{step.step}</span>
                      <span className="shrink-0 font-mono">{step.status} / {step.time}</span>
                    </div>
                  ))}
                  {!lastMetadata?.workflow_trace?.length && <span className="text-on-surface-variant">No execution trace yet.</span>}
                </div>
              </div>

              <div className="rounded border border-outline-variant bg-surface p-3">
                <div className="mb-2 font-semibold text-on-surface">Agent Events</div>
                <div className="space-y-2">
                  {consoleEvents.map((event, index) => (
                    <div key={`${event.timestamp}-${index}`} className="text-on-surface-variant">
                      <span className="font-mono text-[10px]">{new Date(event.timestamp).toLocaleTimeString()}</span>
                      <span className="block">{event.event}</span>
                    </div>
                  ))}
                  {consoleEvents.length === 0 && <span className="text-on-surface-variant">No agent events yet.</span>}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>

      {pendingAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-lg border border-outline-variant bg-surface p-5 shadow-xl">
            <h3 className="text-base font-semibold text-on-surface">Switch active agent?</h3>
            <p className="mt-2 text-sm text-on-surface-variant">
              Future messages in this conversation will be routed to {pendingAgent.name}. Conversation history will remain attached to this session.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setPendingAgentId("")}>Cancel</Button>
              <Button onClick={confirmAgentSwitch}>Switch Agent</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
