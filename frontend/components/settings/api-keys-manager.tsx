"use client";

import { useState } from "react";
import { Key, Copy, Check, Trash2, ShieldAlert, Plus, Lock, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import ConfirmationDialog from "@/components/common/confirmation-dialog";

export interface ApiKeyItem {
  id: string;
  name: string;
  keyMasked: string;
  fullValue?: string;
  lastUsed: string;
  status: "Active" | "Inactive";
}

interface ApiKeysManagerProps {
  initialKeys: ApiKeyItem[];
  onKeysChange: (keys: ApiKeyItem[]) => void;
}

export default function ApiKeysManager({
  initialKeys,
  onKeysChange,
}: ApiKeysManagerProps) {
  const [keys, setKeys] = useState<ApiKeyItem[]>(initialKeys);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  
  // Create Key Modal Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [tempKeyName, setTempKeyName] = useState("");

  // Key Success/Reveal Modal states
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [newKeyFullValue, setNewKeyFullValue] = useState("");
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyCopied, setNewKeyCopied] = useState(false);

  // Revocation Confirmation states
  const [revokeTargetId, setRevokeTargetId] = useState<string | null>(null);

  const handleCopyKey = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKeyId(id);
      toast.success("API Key copied to clipboard");
      setTimeout(() => setCopiedKeyId(null), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRevokeKeyConfirm = async () => {
    if (!revokeTargetId) return;
    const keyItem = keys.find((k) => k.id === revokeTargetId);
    if (!keyItem) return;
    
    const updated = keys.filter((k) => k.id !== revokeTargetId);
    setKeys(updated);
    onKeysChange(updated);
    setRevokeTargetId(null);
    toast.success(`API Key "${keyItem.name}" has been revoked.`);
  };

  const handleOpenCreateModal = () => {
    setTempKeyName("");
    setShowCreateDialog(true);
  };

  const handleGenerateKeySubmit = () => {
    const finalName = tempKeyName.trim() || `API_Key_${Date.now()}`;
    setNewKeyName(finalName);
    
    // Generate a secure looking mock token
    const randomHex = Array.from({ length: 8 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
    const generatedToken = `nx_live_${randomHex}_qXm_p092_KzL_${Date.now().toString().slice(-8)}`;
    
    setNewKeyFullValue(generatedToken);
    setNewKeyCopied(false);
    setShowCreateDialog(false);
    setShowSuccessModal(true);
  };

  const handleConfirmCreateKey = () => {
    const newKeyItem: ApiKeyItem = {
      id: `key-${Date.now()}`,
      name: newKeyName,
      keyMasked: `${newKeyFullValue.slice(0, 8)}••••••••••••${newKeyFullValue.slice(-4)}`,
      fullValue: newKeyFullValue,
      lastUsed: "Never used",
      status: "Active",
    };

    const updated = [newKeyItem, ...keys];
    setKeys(updated);
    onKeysChange(updated);
    setShowSuccessModal(false);
    toast.success(`API Key "${newKeyName}" successfully created.`);
  };

  const handleCopyNewKey = async () => {
    try {
      await navigator.clipboard.writeText(newKeyFullValue);
      setNewKeyCopied(true);
      toast.success("New API Key copied to clipboard");
      setTimeout(() => setNewKeyCopied(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const activeRevokeTargetName = revokeTargetId ? keys.find(k => k.id === revokeTargetId)?.name : "";

  return (
    <>
      <div className="bg-surface-container-low border border-outline-variant rounded-2xl overflow-hidden shadow-sm select-none">
        
        {/* Header Panel */}
        <div className="px-6 py-4 border-b border-outline-variant flex justify-between items-center bg-surface-container shrink-0">
          <div>
            <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
              API Credentials
            </h3>
            <p className="text-[10px] md:text-xs text-on-surface-variant font-medium mt-0.5">
              Secret keys to authenticate your external applications.
            </p>
          </div>
          <Button
            onClick={handleOpenCreateModal}
            className="flex items-center gap-1.5 px-4 py-2 bg-transparent border border-outline hover:bg-surface-container-highest text-on-surface text-xs font-bold rounded-lg cursor-pointer transition-all"
          >
            <Plus className="size-4" />
            Create Key
          </Button>
        </div>

        {/* Keys List */}
        <div className="divide-y divide-outline-variant shrink-0">
          {keys.map((item) => {
            const isCopied = copiedKeyId === item.id;
            const isActive = item.status === "Active";
            return (
              <div
                key={item.id}
                className="p-5 flex items-center justify-between hover:bg-surface-container-high/40 transition-colors gap-6"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center shrink-0 shadow-sm border border-outline-variant/30",
                    isActive ? "bg-primary/10 text-primary" : "bg-surface-container-highest text-on-surface-variant"
                  )}>
                    <Key className="size-5" />
                  </div>
                  
                  <div className="min-w-0">
                    <h4 className="text-xs md:text-sm font-bold text-on-surface truncate">
                      {item.name}
                    </h4>
                    <div className="flex items-center gap-2 mt-1 select-none">
                      <code className="font-mono text-[10px] md:text-xs text-on-surface-variant/90 bg-surface-container-highest px-2 py-0.5 rounded leading-none select-all">
                        {item.keyMasked}
                      </code>
                      <button
                        onClick={() => handleCopyKey(item.id, item.fullValue || item.keyMasked)}
                        className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer shrink-0 bg-transparent border-none"
                        title="Copy Key value"
                      >
                        {isCopied ? <Check className="size-3.5 text-green-400" /> : <Copy className="size-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Status and revokes */}
                <div className="flex items-center gap-6 shrink-0">
                  <div className="hidden md:block text-right select-text">
                    <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider pl-0.5 mb-0.5 leading-none">
                      Last used
                    </p>
                    <p className="text-xs font-semibold text-on-surface leading-none mt-1">
                      {item.lastUsed}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 select-none">
                    <span className={cn(
                      "px-2 py-0.5 text-[8px] rounded uppercase tracking-wider font-bold border leading-none",
                      isActive ? "bg-primary/10 text-primary border-primary/20" : "bg-surface-container-highest text-on-surface-variant border-outline-variant/30"
                    )}>
                      {item.status}
                    </span>
                    
                    <button
                      onClick={() => setRevokeTargetId(item.id)}
                      className="p-2 text-on-surface-variant hover:text-error transition-colors cursor-pointer rounded hover:bg-error/5 bg-transparent border-none"
                      title="Revoke Key"
                    >
                      <Trash2 className="size-4 text-on-surface-variant hover:text-error" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}

          {keys.length === 0 && (
            <div className="p-8 text-center text-xs md:text-sm text-on-surface-variant/40 italic">
              No API Keys recorded. Create a key above to initiate integrations.
            </div>
          )}
        </div>

        {/* Footer warning */}
        <div className="p-5 bg-surface-container-highest/15 border-t border-outline-variant/60 shrink-0">
          <div className="flex items-start gap-3 text-on-surface-variant select-text">
            <ShieldAlert className="size-5 text-primary shrink-0 mt-0.5" />
            <p className="text-[11px] md:text-xs font-medium leading-relaxed">
              Security Warning: Never share your API keys or expose them in client-side code. If a key is compromised, revoke it immediately and generate a new one.
            </p>
          </div>
        </div>
      </div>

      {/* Dialog Modal for entering new Key Details */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-md bg-surface border border-outline-variant text-on-surface p-6 rounded-xl">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Key className="size-5 text-primary" />
              Generate API Credential
            </DialogTitle>
            <DialogDescription className="text-xs text-on-surface-variant">
              Provide a descriptive label for this key to track external usage.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 my-4 text-xs md:text-sm">
            <div className="space-y-2">
              <label className="text-[10px] text-on-surface-variant font-bold block uppercase tracking-wider pl-0.5">Key Name / Description</label>
              <input
                type="text"
                placeholder="e.g. Production_Worker_Node"
                value={tempKeyName}
                onChange={(e) => setTempKeyName(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant rounded-lg p-2.5 text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-xs"
              />
            </div>
          </div>

          <DialogFooter className="flex justify-end gap-2.5 pt-2">
            <Button
              variant="outline"
              size="xs"
              onClick={() => setShowCreateDialog(false)}
              className="text-xs cursor-pointer"
            >
              Cancel
            </Button>
            <Button
              onClick={handleGenerateKeySubmit}
              className="bg-primary text-primary-foreground font-semibold px-4 py-2 rounded-lg text-xs cursor-pointer border-none"
            >
              Generate Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Modal overlay reveal details */}
      {showSuccessModal && (
        <div className="fixed inset-0 bg-black/80 z-[60] flex items-center justify-center p-4">
          <div className="bg-surface border border-outline-variant rounded-2xl p-6 md:p-8 max-w-md w-full shadow-2xl relative select-none animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-start mb-5">
              <div className="w-12 h-12 rounded-full bg-primary/15 flex items-center justify-center text-primary shadow-inner">
                <Lock className="size-5" />
              </div>
              <button
                onClick={() => setShowSuccessModal(false)}
                className="text-on-surface-variant hover:text-on-surface cursor-pointer rounded hover:bg-surface-container-high p-1 bg-transparent border-none"
              >
                <X className="size-4" />
              </button>
            </div>

            <h3 className="text-base md:text-lg font-bold text-on-surface mb-1">
              New API Key Created
            </h3>
            <p className="text-xs md:text-sm text-on-surface-variant/90 font-medium mb-6 leading-relaxed select-text">
              Please copy your new API key now. For your security, it will not be shown again.
            </p>

            <div className="bg-surface-container-high rounded-xl p-4 border border-outline-variant flex items-center justify-between gap-4 mb-6 group select-text">
              <code className="font-mono text-xs md:text-sm text-primary font-bold break-all select-all">
                {newKeyFullValue}
              </code>
              <button
                onClick={handleCopyNewKey}
                className="p-2 text-on-surface-variant hover:text-primary transition-colors cursor-pointer shrink-0 bg-transparent border-none"
              >
                {newKeyCopied ? <Check className="size-4 text-green-400" /> : <Copy className="size-4" />}
              </button>
            </div>

            <Button
              onClick={handleConfirmCreateKey}
              className="w-full py-5 bg-primary text-primary-foreground font-bold rounded-lg hover:opacity-90 active:scale-98 transition-all cursor-pointer border-none text-xs md:text-sm shadow-md shadow-primary/15"
            >
              I&apos;ve copied the key
            </Button>
          </div>
        </div>
      )}

      {/* Revocation Confirmation Dialog */}
      <ConfirmationDialog
        open={revokeTargetId !== null}
        onOpenChange={(open) => { if (!open) setRevokeTargetId(null); }}
        title="Revoke API Credential?"
        description={`This will permanently revoke the credential key "${activeRevokeTargetName}". Any external applications or automation scripts using this key will immediately fail to authenticate. This action cannot be undone.`}
        confirmLabel="Revoke Key"
        variant="destructive"
        onConfirm={handleRevokeKeyConfirm}
      />
    </>
  );
}
