"use client";

import { useState } from "react";
import { History, ChevronRight, MessageSquare } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import ConversationList, { Conversation } from "@/components/chat/conversation-list";
import ChatMessages, { Message } from "@/components/chat/chat-messages";
import MessageInput from "@/components/chat/message-input";
import SuggestedPrompts from "@/components/chat/suggested-prompts";
import { AttachedFile } from "@/components/chat/file-attachments";
import EmptyState from "@/components/common/empty-state";

// Initial Mock Conversations List
const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: "chat-1",
    title: "Quantum Simulation Project",
    updatedAt: "Just now",
    category: "Today",
  },
  {
    id: "chat-2",
    title: "Grover's Search Oracle",
    updatedAt: "2h ago",
    category: "Today",
  },
  {
    id: "chat-3",
    title: "CI/CD Pipeline Fix",
    updatedAt: "Yesterday",
    category: "Yesterday",
  },
  {
    id: "chat-4",
    title: "AWS Cluster Configs",
    updatedAt: "4 days ago",
    category: "Older",
  },
];

// Initial Messages Map for conversations
const INITIAL_MESSAGES_MAP: Record<string, Message[]> = {
  "chat-1": [
    {
      id: "msg-1-1",
      sender: "ai",
      text: "Hello. I've initialized the workspace for the **Quantum Simulation Project**. I can assist with data analysis, code refactoring, or architectural review. What would you like to start with?",
    },
    {
      id: "msg-1-2",
      sender: "user",
      text: "Can you show me a Python snippet for a basic Grover's Algorithm implementation using Qiskit?",
    },
    {
      id: "msg-1-3",
      sender: "ai",
      text: "Certainly. Here is a streamlined implementation of Grover's Algorithm for a 2-qubit system searching for the $|11\\rangle$ state.",
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
      showVisualization: true,
    },
  ],
  "chat-2": [
    {
      id: "msg-2-1",
      sender: "ai",
      text: "Welcome back. I have loaded the Oracle matrices for state searching. We can test standard phase flips or define a multi-target oracle. What is your preference?",
    },
  ],
  "chat-3": [
    {
      id: "msg-3-1",
      sender: "ai",
      text: "Grover build pipeline checks failed on stage 3 (Docker push). It appears that authorization tokens expired in the AWS registry. Let's renew tokens.",
    },
  ],
  "chat-4": [
    {
      id: "msg-4-1",
      sender: "ai",
      text: "Initialized AWS clusters logs. Ready to inspect US-West node latencies.",
    },
  ],
};

const SUGGESTED_QUESTIONS = [
  "Optimize Qiskit circuit",
  "Explain diffusion operator",
  "Add measurement gates",
];

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [activeId, setActiveId] = useState<string>("chat-1");
  const [messagesMap, setMessagesMap] = useState<Record<string, Message[]>>(INITIAL_MESSAGES_MAP);
  const [isEmpty, setIsEmpty] = useState(false);
  
  // Input states
  const [inputText, setInputText] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const activeMessages = messagesMap[activeId] || [];
  const activeConversationTitle = conversations.find(c => c.id === activeId)?.title || "AI Chat";

  // Handle Switch Conversation
  const handleSelectConversation = (id: string) => {
    setActiveId(id);
    setInputText("");
    setAttachedFiles([]);
  };

  // Handle Delete Conversation
  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newConversations = conversations.filter(c => c.id !== id);
    setConversations(newConversations);
    
    // Clean messages cache
    const newMap = { ...messagesMap };
    delete newMap[id];
    setMessagesMap(newMap);

    // If deleting active conversation, select another one
    if (activeId === id && newConversations.length > 0) {
      setActiveId(newConversations[0].id);
    }
  };

  // Create New Chat Session
  const handleNewChat = () => {
    const newId = `chat-${Date.now()}`;
    const newChat: Conversation = {
      id: newId,
      title: "New AI Simulation",
      updatedAt: "Just now",
      category: "Today",
    };
    
    setConversations([newChat, ...conversations]);
    setMessagesMap({
      ...messagesMap,
      [newId]: [
        {
          id: `msg-${Date.now()}-greet`,
          sender: "ai",
          text: "I've opened a new session. Ask any questions about Grover's search amplitude amplification, Qiskit circuits, or cluster latency analysis.",
        }
      ]
    });
    setActiveId(newId);
    setInputText("");
    setAttachedFiles([]);
  };

  // Manage Attachment States
  const handleAddFile = (file: AttachedFile) => {
    setAttachedFiles([...attachedFiles, file]);
  };

  const handleRemoveFile = (id: string) => {
    setAttachedFiles(attachedFiles.filter(f => f.id !== id));
  };

  // Suggested Prompts trigger
  const handleSuggestedPromptClick = (prompt: string) => {
    setInputText(prompt);
  };

  // Send Prompt Message
  const handleSendPrompt = () => {
    if (!inputText.trim() && attachedFiles.length === 0) return;

    const userMessageId = `msg-user-${Date.now()}`;
    const userMessage: Message = {
      id: userMessageId,
      sender: "user",
      text: inputText,
      attachments: attachedFiles.length > 0 ? attachedFiles : undefined,
    };

    // Update messages map locally
    const currentMessages = messagesMap[activeId] || [];
    const updatedMessages = [...currentMessages, userMessage];
    
    setMessagesMap({
      ...messagesMap,
      [activeId]: updatedMessages,
    });

    // Clear inputs
    const sentText = inputText;
    const sentFiles = attachedFiles;
    setInputText("");
    setAttachedFiles([]);
    setIsTyping(true);

    // Update conversation title if it was a default placeholder
    const activeChat = conversations.find(c => c.id === activeId);
    if (activeChat && activeChat.title === "New AI Simulation" && sentText.trim()) {
      setConversations(conversations.map(c => 
        c.id === activeId 
          ? { ...c, title: sentText.length > 30 ? `${sentText.substring(0, 30)}...` : sentText } 
          : c
      ));
    }

    // Trigger simulated AI response after a 1.2 second delay
    setTimeout(() => {
      setIsTyping(false);
      
      let aiResponseText = "";
      let codeSnippet = undefined;
      let showWidgets = false;

      // Custom mock responses based on input keywords
      if (sentText.toLowerCase().includes("optimize")) {
        aiResponseText = "To optimize your Grover's Qiskit circuit, we can replace the standard multi-controlled-Z diffusion gates with an optimized phase oracle. This reduces gate count and depth, improving error mitigation on noisy quantum devices (NISQ).";
        codeSnippet = {
          filename: "optimized_diffusion.py",
          code: `from qiskit.circuit.library import GroverOperator
# Qiskit's built-in GroverOperator optimizes transpilations automatically
grover_op = GroverOperator(oracle_circuit)
transpiled_circuit = transpile(grover_op, basis_gates=['u', 'cx'], optimization_level=3)`,
          language: "python",
        };
      } else if (sentText.toLowerCase().includes("diffusion") || sentText.toLowerCase().includes("explain")) {
        aiResponseText = "The diffusion operator performs amplitude amplification. Geometrically, it reflects the state vectors around the average amplitude. If the target state had its phase flipped by the oracle, this reflection increases the amplitude of the target state while shrinking all other states.";
      } else if (sentText.toLowerCase().includes("gate") || sentText.toLowerCase().includes("measure")) {
        aiResponseText = "I have appended measurement gates to both qubits. This maps quantum state collapses onto classical register channels. Here is how to run measurement transpilations.";
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
      } else {
        aiResponseText = `I have received your prompt${sentFiles.length > 0 ? ` with the attached files (${sentFiles.map(f => f.name).join(", ")})` : ""}. I am initiating quantum state vectors calculations using Aer simulator backend. Let me know if you would like me to optimize gate transpilations, write tests, or analyze circuit depths.`;
      }

      const aiMessageId = `msg-ai-${Date.now()}`;
      const aiResponse: Message = {
        id: aiMessageId,
        sender: "ai",
        text: aiResponseText,
        codeBlock: codeSnippet,
        showVisualization: showWidgets,
      };

      setMessagesMap(prevMap => ({
        ...prevMap,
        [activeId]: [...(prevMap[activeId] || []), aiResponse],
      }));

    }, 1200);
  };

  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background text-on-background">
      
      {/* Conversation List Sidebar - Hidden on mobile, visible on desktop */}
      <div className="hidden md:flex">
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelectConversation}
          onDelete={handleDeleteConversation}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Main Chat Thread area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        
        {/* Workspace Breadcrumbs / Mobile history drawer trigger */}
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
              <ChatMessages messages={activeMessages} />
              
              {/* Simulated loading indicator */}
              {isTyping && (
                <div className="px-6 py-2 flex items-center gap-2 text-xs text-on-surface-variant max-w-4xl mx-auto w-full select-none animate-pulse">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-75" />
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-150" />
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce delay-300" />
                  <span className="ml-1 leading-none pt-0.5">Nexus AI is calculating...</span>
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
