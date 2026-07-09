"use client";

import { useState, useCallback, useRef } from "react";
import { History, ChevronRight, MessageSquare, Download } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import ConversationList, { Conversation } from "@/components/chat/conversation-list";
import ChatMessages, { Message } from "@/components/chat/chat-messages";
import MessageInput from "@/components/chat/message-input";
import SuggestedPrompts from "@/components/chat/suggested-prompts";
import { AttachedFile } from "@/components/chat/file-attachments";
import EmptyState from "@/components/common/empty-state";
import { toast } from "sonner";

function getTimestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Initial Mock Conversations List
const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: "chat-1",
    title: "Quantum Simulation Project",
    updatedAt: "Just now",
    category: "Today",
    messageCount: 4,
  },
  {
    id: "chat-2",
    title: "Grover's Search Oracle",
    updatedAt: "2h ago",
    category: "Today",
    messageCount: 1,
  },
  {
    id: "chat-3",
    title: "CI/CD Pipeline Fix",
    updatedAt: "Yesterday",
    category: "Yesterday",
    messageCount: 1,
  },
  {
    id: "chat-4",
    title: "AWS Cluster Configs",
    updatedAt: "4 days ago",
    category: "Older",
    isPinned: true,
    messageCount: 1,
  },
];

// Initial Messages Map for conversations
const INITIAL_MESSAGES_MAP: Record<string, Message[]> = {
  "chat-1": [
    {
      id: "msg-1-1",
      sender: "ai",
      text: "Hello. I've initialized the workspace for the **Quantum Simulation Project**. I can assist with data analysis, code refactoring, or architectural review. What would you like to start with?",
      timestamp: "10:23 AM",
    },
    {
      id: "msg-1-2",
      sender: "user",
      text: "Can you show me a Python snippet for a basic Grover's Algorithm implementation using Qiskit?",
      timestamp: "10:24 AM",
    },
    {
      id: "msg-1-3",
      sender: "ai",
      text: "Certainly. Here is a streamlined implementation of Grover's Algorithm for a 2-qubit system searching for the $|11\\rangle$ state.",
      timestamp: "10:24 AM",
      codeBlock: {
        filename: "grover_search.py",
        code: `from qiskit import QuantumCircuit, assemble, Aer
from qiskit.visualization import plot_histogram

def grover_circuit():
    # Initialize a 2-qubit circuit
    qc = QuantumCircuit(2)
    
    # 1. Oracle for |11> state
    qc.cz(0, 1) 
    
    #  diffusion operator (Hadamard + X + CZ)
    qc.h([0, 1])
    qc.z([0, 1])
    qc.cz(0, 1)
    qc.h([0, 1])
    
    return qc

circuit = grover_circuit()
print(circuit.draw())`,
        language: "python",
      },
    },
    {
      id: "msg-1-4",
      sender: "ai",
      text: "This specific circuit applies a controlled-Z gate as the oracle for the target state. The diffusion operator then amplifies the probability of measuring $|11\\rangle$.",
      timestamp: "10:25 AM",
      showVisualization: true,
    },
  ],
  "chat-2": [
    {
      id: "msg-2-1",
      sender: "ai",
      text: "Welcome back. I have loaded the Oracle matrices for state searching. We can test standard phase flips or define a multi-target oracle. What is your preference?",
      timestamp: "8:12 AM",
    },
  ],
  "chat-3": [
    {
      id: "msg-3-1",
      sender: "ai",
      text: "Grover build pipeline checks failed on stage 3 (Docker push). It appears that authorization tokens expired in the AWS registry. Let's renew tokens.",
      timestamp: "Yesterday",
    },
  ],
  "chat-4": [
    {
      id: "msg-4-1",
      sender: "ai",
      text: "Initialized AWS clusters logs. Ready to inspect US-West node latencies.",
      timestamp: "Jul 3",
    },
  ],
};

const SUGGESTED_QUESTIONS = [
  "Optimize Qiskit circuit",
  "Explain diffusion operator",
  "Add measurement gates",
  "Compare QAOA vs Grover",
];

// Simulated streaming — reveals text word by word
function useStreamingResponse() {
  const streamRef = useRef<NodeJS.Timeout | null>(null);

  const streamResponse = useCallback((
    fullText: string,
    messageId: string,
    activeId: string,
    codeBlock: Message["codeBlock"],
    showVisualization: boolean,
    updateMessages: React.Dispatch<React.SetStateAction<Record<string, Message[]>>>,
    onComplete: () => void,
  ) => {
    const words = fullText.split(" ");
    let currentIndex = 0;

    // Insert placeholder streaming message
    updateMessages(prev => ({
      ...prev,
      [activeId]: [...(prev[activeId] || []), {
        id: messageId,
        sender: "ai" as const,
        text: "",
        timestamp: getTimestamp(),
        isStreaming: true,
      }],
    }));

    streamRef.current = setInterval(() => {
      currentIndex++;
      const partialText = words.slice(0, currentIndex).join(" ");
      const isDone = currentIndex >= words.length;

      updateMessages(prev => ({
        ...prev,
        [activeId]: (prev[activeId] || []).map(msg =>
          msg.id === messageId
            ? { ...msg, text: partialText, isStreaming: !isDone, codeBlock: isDone ? codeBlock : undefined, showVisualization: isDone ? showVisualization : false }
            : msg
        ),
      }));

      if (isDone) {
        if (streamRef.current) clearInterval(streamRef.current);
        onComplete();
      }
    }, 40); // ~25 words/second
  }, []);

  const cancelStream = useCallback(() => {
    if (streamRef.current) clearInterval(streamRef.current);
  }, []);

  return { streamResponse, cancelStream };
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [activeId, setActiveId] = useState<string>("chat-1");
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>(INITIAL_MESSAGES_MAP);
  const [isEmpty, setIsEmpty] = useState(false);
  
  // Input states
  const [inputText, setInputText] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const { streamResponse, cancelStream } = useStreamingResponse();

  const activeMessages = messagesMap[activeId] || [];
  const activeConversationTitle = conversations.find(c => c.id === activeId)?.title || "AI Chat";

  // Handle Switch Conversation
  const handleSelectConversation = (id: string) => {
    cancelStream();
    setIsTyping(false);
    setActiveId(id);
    setInputText("");
    setAttachedFiles([]);
  };

  // Handle Delete Conversation
  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    cancelStream();
    const newConversations = conversations.filter(c => c.id !== id);
    setConversations(newConversations);
    
    const newMap = { ...messagesMap };
    delete newMap[id];
    setMessagesMap(newMap);

    if (activeId === id && newConversations.length > 0) {
      setActiveId(newConversations[0].id);
    }
  };

  // Handle Rename
  const handleRename = (id: string, newTitle: string) => {
    setConversations(conversations.map(c =>
      c.id === id ? { ...c, title: newTitle } : c
    ));
  };

  // Handle Pin Toggle
  const handleTogglePin = (id: string) => {
    setConversations(conversations.map(c =>
      c.id === id ? { ...c, isPinned: !c.isPinned } : c
    ));
    const conv = conversations.find(c => c.id === id);
    toast.success(conv?.isPinned ? "Conversation unpinned" : "Conversation pinned");
  };

  // Create New Chat Session
  const handleNewChat = () => {
    cancelStream();
    const newId = `chat-${Date.now()}`;
    const newChat: Conversation = {
      id: newId,
      title: "New AI Session",
      updatedAt: "Just now",
      category: "Today",
      messageCount: 1,
    };
    
    setConversations([newChat, ...conversations]);
    setMessagesMap({
      ...messagesMap,
      [newId]: [
        {
          id: `msg-${Date.now()}-greet`,
          sender: "ai",
          text: "I've opened a new session. Ask any questions about quantum search amplitude amplification, Qiskit circuits, or cluster latency analysis.",
          timestamp: getTimestamp(),
        }
      ]
    });
    setActiveId(newId);
    setInputText("");
    setAttachedFiles([]);
    setIsTyping(false);
  };

  // File management
  const handleAddFile = (file: AttachedFile) => {
    setAttachedFiles([...attachedFiles, file]);
  };

  const handleRemoveFile = (id: string) => {
    setAttachedFiles(attachedFiles.filter(f => f.id !== id));
  };

  // Suggested Prompts
  const handleSuggestedPromptClick = (prompt: string) => {
    setInputText(prompt);
  };

  // Generate AI response text based on keywords
  const generateAIResponse = (sentText: string, sentFiles: AttachedFile[]) => {
    let aiResponseText = "";
    let codeSnippet: Message["codeBlock"] = undefined;
    let showWidgets = false;

    if (sentText.toLowerCase().includes("optimize")) {
      aiResponseText = "To optimize your Grover's Qiskit circuit, we can replace the standard multi-controlled-Z diffusion gates with an optimized phase oracle. This reduces gate count and depth, improving error mitigation on noisy quantum devices (NISQ). I've prepared an optimized implementation below.";
      codeSnippet = {
        filename: "optimized_diffusion.py",
        code: `from qiskit.circuit.library import GroverOperator
# Qiskit's built-in GroverOperator optimizes transpilations automatically
grover_op = GroverOperator(oracle_circuit)
transpiled_circuit = transpile(grover_op, basis_gates=['u', 'cx'], optimization_level=3)`,
        language: "python",
      };
    } else if (sentText.toLowerCase().includes("diffusion") || sentText.toLowerCase().includes("explain")) {
      aiResponseText = "The diffusion operator performs amplitude amplification. Geometrically, it reflects the state vectors around the average amplitude. If the target state had its phase flipped by the oracle, this reflection increases the amplitude of the target state while shrinking all other states. The mathematical representation is: D = 2|ψ⟩⟨ψ| - I, where |ψ⟩ is the uniform superposition state.";
    } else if (sentText.toLowerCase().includes("gate") || sentText.toLowerCase().includes("measure")) {
      aiResponseText = "I have appended measurement gates to both qubits. This maps quantum state collapses onto classical register channels. Here is how to run measurement transpilations with the Aer simulator backend.";
      codeSnippet = {
        filename: "measurements.py",
        code: `qc.measure_all()
# Execute on qasm simulator
simulator = Aer.get_backend('qasm_simulator')
job = execute(qc, simulator, shots=1024)
result = job.result()
counts = result.get_counts()
print("Measurement outcomes:", counts)`,
        language: "python",
      };
      showWidgets = true;
    } else if (sentText.toLowerCase().includes("compare") || sentText.toLowerCase().includes("qaoa")) {
      aiResponseText = "QAOA (Quantum Approximate Optimization Algorithm) and Grover's algorithm serve different purposes. Grover's provides a quadratic speedup for unstructured search problems with O(√N) complexity. QAOA is a variational hybrid algorithm designed for combinatorial optimization. For exact search, Grover's is optimal. For approximate optimization of cost functions, QAOA offers parameterized flexibility that can be trained classically.";
    } else {
      aiResponseText = `I have received your prompt${sentFiles.length > 0 ? ` with the attached files (${sentFiles.map(f => f.name).join(", ")})` : ""}. I'm initiating quantum state vector calculations using the Aer simulator backend. Let me know if you would like me to optimize gate transpilations, write unit tests, or analyze circuit depths.`;
    }

    return { aiResponseText, codeSnippet, showWidgets };
  };

  // Send Prompt Message (with streaming)
  const handleSendPrompt = () => {
    if (!inputText.trim() && attachedFiles.length === 0) return;

    const userMessageId = `msg-user-${Date.now()}`;
    const userMessage: Message = {
      id: userMessageId,
      sender: "user",
      text: inputText,
      timestamp: getTimestamp(),
      attachments: attachedFiles.length > 0 ? attachedFiles : undefined,
    };

    const currentMessages = messagesMap[activeId] || [];
    setMessagesMap({
      ...messagesMap,
      [activeId]: [...currentMessages, userMessage],
    });

    const sentText = inputText;
    const sentFiles = attachedFiles;
    setInputText("");
    setAttachedFiles([]);
    setIsTyping(true);

    // Update conversation title if placeholder
    const activeChat = conversations.find(c => c.id === activeId);
    if (activeChat && activeChat.title === "New AI Session" && sentText.trim()) {
      setConversations(conversations.map(c => 
        c.id === activeId 
          ? { ...c, title: sentText.length > 35 ? `${sentText.substring(0, 35)}…` : sentText, updatedAt: "Just now", messageCount: (c.messageCount || 0) + 2 } 
          : c
      ));
    } else {
      setConversations(conversations.map(c =>
        c.id === activeId ? { ...c, updatedAt: "Just now", messageCount: (c.messageCount || 0) + 2 } : c
      ));
    }

    // Simulate "thinking" delay then stream response
    setTimeout(() => {
      const { aiResponseText, codeSnippet, showWidgets } = generateAIResponse(sentText, sentFiles);
      const aiMessageId = `msg-ai-${Date.now()}`;

      streamResponse(
        aiResponseText,
        aiMessageId,
        activeId,
        codeSnippet,
        showWidgets,
        setMessagesMap,
        () => setIsTyping(false),
      );
    }, 600);
  };

  // Regenerate AI response
  const handleRegenerate = (messageId: string) => {
    const msgs = messagesMap[activeId] || [];
    const msgIndex = msgs.findIndex(m => m.id === messageId);
    if (msgIndex === -1) return;

    // Find the preceding user message
    let userText = "regenerate previous response";
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (msgs[i].sender === "user") {
        userText = msgs[i].text;
        break;
      }
    }

    // Remove the old AI message
    const updatedMsgs = msgs.filter(m => m.id !== messageId);
    setMessagesMap(prev => ({ ...prev, [activeId]: updatedMsgs }));
    setIsTyping(true);

    setTimeout(() => {
      const { aiResponseText, codeSnippet, showWidgets } = generateAIResponse(userText, []);
      const newId = `msg-ai-regen-${Date.now()}`;

      streamResponse(
        aiResponseText,
        newId,
        activeId,
        codeSnippet,
        showWidgets,
        setMessagesMap,
        () => {
          setIsTyping(false);
          toast.success("Response regenerated");
        },
      );
    }, 400);
  };

  // Edit user message and re-send
  const handleEditUserMessage = (messageId: string, newText: string) => {
    const msgs = messagesMap[activeId] || [];
    const msgIndex = msgs.findIndex(m => m.id === messageId);
    if (msgIndex === -1) return;

    // Trim everything after this message
    const trimmedMsgs = msgs.slice(0, msgIndex);
    trimmedMsgs.push({ ...msgs[msgIndex], text: newText, timestamp: getTimestamp() });
    setMessagesMap(prev => ({ ...prev, [activeId]: trimmedMsgs }));
    setIsTyping(true);

    setTimeout(() => {
      const { aiResponseText, codeSnippet, showWidgets } = generateAIResponse(newText, []);
      const newId = `msg-ai-edit-${Date.now()}`;

      streamResponse(
        aiResponseText,
        newId,
        activeId,
        codeSnippet,
        showWidgets,
        setMessagesMap,
        () => {
          setIsTyping(false);
          toast.success("Response updated after edit");
        },
      );
    }, 400);
  };

  // Export current chat
  const handleExportChat = () => {
    const msgs = messagesMap[activeId] || [];
    const content = [
      `# ${activeConversationTitle}`,
      `Exported: ${new Date().toISOString()}`,
      `Messages: ${msgs.length}`,
      "",
      ...msgs.map(m => `### ${m.sender === "ai" ? "Nexus AI" : "You"} — ${m.timestamp || ""}\n${m.text}${m.codeBlock ? `\n\`\`\`${m.codeBlock.language || ""}\n${m.codeBlock.code}\n\`\`\`` : ""}\n`)
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeConversationTitle.replace(/\s+/g, "_").toLowerCase()}_export.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Chat exported as Markdown");
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background text-on-background">
      
      {/* Conversation List Sidebar */}
      <div className="hidden md:flex">
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNewChat={handleNewChat}
          onRename={handleRename}
          onTogglePin={handleTogglePin}
        />
      </div>

      {/* Main Chat Thread area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        
        {/* Header bar */}
        <div className="h-12 border-b border-outline-variant/50 px-6 flex items-center justify-between shrink-0 bg-surface/40 select-none">
          <div className="flex items-center gap-1 text-xs text-on-surface-variant font-medium">
            {/* Mobile history drawer trigger */}
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden size-8 text-on-surface-variant hover:text-on-surface mr-1.5 cursor-pointer"
                >
                  <History className="size-4.5" />
                  <span className="sr-only">Conversation History</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 w-64 border-r border-outline-variant bg-surface" showCloseButton={true}>
                <SheetTitle className="sr-only">Recent Conversations</SheetTitle>
                <SheetDescription className="sr-only">
                  History panel of prior quantum calculations and developer scripts chat logs.
                </SheetDescription>
                <ConversationList
                  conversations={conversations}
                  activeId={activeId}
                  onSelect={(id) => {
                    handleSelectConversation(id);
                  }}
                  onDelete={handleDeleteConversation}
                  onNewChat={handleNewChat}
                  onRename={handleRename}
                  onTogglePin={handleTogglePin}
                />
              </SheetContent>
            </Sheet>

            <span>Workspace</span>
            <ChevronRight className="size-3.5 text-on-surface-variant/40" />
            <span className="text-primary font-semibold truncate max-w-[160px] sm:max-w-xs">
              {activeConversationTitle}
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Export button */}
            {!isEmpty && activeMessages.length > 0 && (
              <Button
                variant="ghost"
                size="xs"
                onClick={handleExportChat}
                className="text-[10px] font-semibold text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors flex items-center gap-1"
              >
                <Download className="size-3" />
                Export
              </Button>
            )}
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setIsEmpty(!isEmpty)}
              className="text-[10px] font-mono text-on-surface-variant/55 hover:text-primary cursor-pointer transition-colors"
            >
              {isEmpty ? "● Show Messages" : "○ Simulate Empty State"}
            </Button>
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-[10px] font-bold text-on-surface-variant/80 uppercase tracking-widest font-mono">
              Workspace Live
            </span>
          </div>
        </div>

        {isEmpty ? (
          <div className="flex-1 flex items-center justify-center p-6 bg-surface-container-lowest/20">
            <EmptyState
              icon={MessageSquare}
              title="No Active Chats"
              description="Start a secure thread with Nexus core agent arrays to diagnose memory leaks, prototype quantum circuits, or query context vectors."
              actionLabel="Start New Chat"
              onAction={handleNewChat}
              accentColor="tertiary"
            />
          </div>
        ) : (
          <>
            {/* Message Feed */}
            <div className="flex-1 overflow-y-auto flex flex-col justify-between">
              <ChatMessages
                messages={activeMessages}
                onRegenerate={handleRegenerate}
                onEditUserMessage={handleEditUserMessage}
              />
              
              {/* Enhanced typing indicator */}
              {isTyping && !activeMessages.some(m => m.isStreaming) && (
                <div className="px-6 py-3 flex items-center gap-3 text-xs text-on-surface-variant max-w-4xl mx-auto w-full select-none">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span className="leading-none pt-0.5 font-medium">Nexus AI is thinking…</span>
                </div>
              )}

              {/* Suggested Prompts (chips above input box) */}
              {activeMessages.length < 5 && (
                <div className="max-w-4xl mx-auto w-full px-6 pb-4">
                  <SuggestedPrompts
                    prompts={SUGGESTED_QUESTIONS}
                    onClick={handleSuggestedPromptClick}
                  />
                </div>
              )}
            </div>

            {/* Chat prompt input area */}
            <MessageInput
              text={inputText}
              onChangeText={setInputText}
              files={attachedFiles}
              onAddFile={handleAddFile}
              onRemoveFile={handleRemoveFile}
              onSend={handleSendPrompt}
            />
          </>
        )}
      </div>
    </div>
  );
}
