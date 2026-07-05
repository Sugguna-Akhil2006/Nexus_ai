"use client";

import { useState } from "react";
import { CreditCard, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export interface CardDetails {
  id: string;
  numberMasked: string; // •••• •••• •••• 4242
  expiry: string; // 12/25
  isDefault: boolean;
}

interface PaymentMethodsProps {
  initialCards: CardDetails[];
}

export default function PaymentMethods({
  initialCards,
}: PaymentMethodsProps) {
  const [cards, setCards] = useState<CardDetails[]>(initialCards);

  const handleAddNewCard = () => {
    const cardNum = prompt("Enter a 16-digit credit card number for testing:");
    if (!cardNum) return;

    const trimmed = cardNum.trim().replace(/\s/g, "");
    if (!/^\d{16}$/.test(trimmed)) {
      toast.error("Invalid card number. Please enter exactly 16 digits.");
      return;
    }

    const expiryInput = prompt("Enter expiry date (MM/YY):", "12/28");
    if (!expiryInput) return;

    const formattedNum = `•••• •••• •••• ${trimmed.slice(-4)}`;
    const newCard: CardDetails = {
      id: `card-${Date.now()}`,
      numberMasked: formattedNum,
      expiry: expiryInput,
      isDefault: cards.length === 0, // make default if it is the first card
    };

    setCards((prev) => [...prev, newCard]);
    toast.success("New payment card added successfully for billing simulation.");
  };

  const handleSetDefault = (id: string) => {
    setCards((prev) =>
      prev.map((c) => ({
        ...c,
        isDefault: c.id === id,
      }))
    );
  };

  const handleRemoveCard = (id: string, isDefault: boolean) => {
    if (isDefault) {
      toast.error("Cannot remove default payment method. Set another card as default first.");
      return;
    }
    const updated = cards.filter((c) => c.id !== id);
    setCards(updated);
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 shadow-sm flex flex-col justify-between h-full select-none">
      
      {/* Header */}
      <div className="flex justify-between items-center mb-5 shrink-0">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Payment Methods
        </h3>
        <button
          onClick={handleAddNewCard}
          className="text-primary font-bold text-xs md:text-sm hover:underline cursor-pointer bg-transparent border-none p-0 flex items-center gap-0.5"
        >
          <Plus className="size-4 shrink-0" />
          Add New
        </button>
      </div>

      {/* Cards list */}
      <div className="space-y-3 flex-grow select-text">
        {cards.map((card) => (
          <div
            key={card.id}
            className="flex items-center justify-between p-3.5 border border-outline-variant rounded-lg bg-surface-container-lowest gap-4 hover:border-outline-variant/80 transition-all"
          >
            {/* Left info */}
            <div className="flex items-center gap-3">
              <div className="w-11 h-7 bg-on-surface/5 rounded flex items-center justify-center border border-outline-variant/60 shrink-0">
                <CreditCard className="size-4.5 text-on-surface-variant" />
              </div>
              <div className="min-w-0">
                <p className="font-mono text-xs md:text-sm font-bold text-on-surface leading-tight">
                  {card.numberMasked}
                </p>
                <p className="text-[10px] md:text-xs text-on-surface-variant/80 font-semibold leading-none mt-1">
                  Expires {card.expiry}
                </p>
              </div>
            </div>

            {/* Right actions */}
            <div className="flex items-center gap-3 select-none shrink-0">
              {card.isDefault ? (
                <span className="bg-primary/10 text-primary text-[9px] md:text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider leading-none">
                  Default
                </span>
              ) : (
                <button
                  onClick={() => handleSetDefault(card.id)}
                  className="text-[9px] md:text-[10px] hover:text-primary transition-colors cursor-pointer text-on-surface-variant bg-transparent border-none font-bold uppercase tracking-wider"
                >
                  Set Default
                </button>
              )}
              
              {!card.isDefault && (
                <button
                  onClick={() => handleRemoveCard(card.id, card.isDefault)}
                  className="text-on-surface-variant hover:text-error transition-colors cursor-pointer inline-flex items-center justify-center"
                  title="Remove card"
                >
                  <Trash2 className="size-3.5" />
                </button>
              )}
            </div>

          </div>
        ))}

        {cards.length === 0 && (
          <p className="text-center py-6 text-xs text-on-surface-variant/40 italic font-medium">
            No payment methods registered on this account.
          </p>
        )}
      </div>

    </div>
  );
}
