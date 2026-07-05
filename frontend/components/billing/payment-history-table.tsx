"use client";

import { useState } from "react";
import { Download, FileText } from "lucide-react";
import { toast } from "sonner";

export interface InvoiceItem {
  id: string;
  invoiceCode: string; // #INV-88219-Nexus
  date: string;
  amount: string; // $499.00
  status: "Paid" | "Pending" | "Failed";
}

interface PaymentHistoryTableProps {
  initialInvoices: InvoiceItem[];
}

export default function PaymentHistoryTable({
  initialInvoices,
}: PaymentHistoryTableProps) {
  const [invoices, setInvoices] = useState<InvoiceItem[]>(initialInvoices);
  const [expanded, setExpanded] = useState(false);

  const handleExportAll = () => {
    toast.success("Exporting workspace billing statements ledger to PDF/CSV. Download starting shortly.");
  };

  const handleDownloadInvoice = (code: string) => {
    toast.success(`Downloading PDF copy of receipt: ${code}`);
  };

  const handleShowMore = () => {
    // Simulated load of older receipts
    const older: InvoiceItem[] = [
      {
        id: "inv-3",
        invoiceCode: "#INV-86190-Nexus",
        date: "Aug 24, 2023",
        amount: "$499.00",
        status: "Paid",
      },
      {
        id: "inv-4",
        invoiceCode: "#INV-85012-Nexus",
        date: "Jul 24, 2023",
        amount: "$29.00",
        status: "Paid",
      },
    ];

    setInvoices((prev) => [...prev, ...older]);
    setExpanded(true);
  };

  return (
    <section className="space-y-4 select-none">
      
      {/* Title block */}
      <div className="flex justify-between items-center shrink-0">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Payment History
        </h3>
        <button
          onClick={handleExportAll}
          className="flex items-center gap-1 text-primary font-bold text-xs md:text-sm hover:underline cursor-pointer bg-transparent border-none p-0"
        >
          <Download className="size-4 shrink-0" />
          Export All
        </button>
      </div>

      {/* Invoice list table */}
      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm border-collapse">
            <thead>
              <tr className="border-b border-outline-variant/60 bg-surface-container-low/70 select-none text-[10px] md:text-[11px] tracking-wider uppercase font-bold text-on-surface-variant">
                <th className="px-6 py-3 font-semibold">Invoice ID</th>
                <th className="px-6 py-3 font-semibold">Date</th>
                <th className="px-6 py-3 font-semibold">Amount</th>
                <th className="px-6 py-3 font-semibold">Status</th>
                <th className="px-6 py-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            
            <tbody className="divide-y divide-outline-variant/30 select-text">
              {invoices.map((inv) => (
                <tr key={inv.id} className="hover:bg-surface-container-high/35 transition-colors">
                  
                  {/* Code */}
                  <td className="px-6 py-4 font-mono font-bold text-on-surface">
                    {inv.invoiceCode}
                  </td>
                  
                  {/* Date */}
                  <td className="px-6 py-4 font-medium text-on-surface-variant">
                    {inv.date}
                  </td>
                  
                  {/* Amount */}
                  <td className="px-6 py-4 font-extrabold text-on-surface">
                    {inv.amount}
                  </td>
                  
                  {/* Status badge */}
                  <td className="px-6 py-4 select-none">
                    <span className="px-2.5 py-0.5 bg-green-900/25 border border-green-500/25 text-green-400 text-[9px] md:text-[10px] rounded font-bold uppercase tracking-wider">
                      {inv.status}
                    </span>
                  </td>
                  
                  {/* Download PDF button */}
                  <td className="px-6 py-4 text-right select-none">
                    <button
                      onClick={() => handleDownloadInvoice(inv.invoiceCode)}
                      className="text-on-surface-variant hover:text-white transition-all cursor-pointer inline-flex items-center justify-center p-1 hover:bg-surface-container-high rounded-md"
                      title="Download receipt PDF"
                    >
                      <FileText className="size-4 shrink-0" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Show more button */}
      {!expanded && (
        <div className="flex justify-center pt-2 select-none">
          <button
            onClick={handleShowMore}
            className="text-xs md:text-sm font-bold text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer bg-transparent border-none"
          >
            Show more invoices
          </button>
        </div>
      )}

    </section>
  );
}
