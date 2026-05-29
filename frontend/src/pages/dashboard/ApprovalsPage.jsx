import React, { useEffect, useState } from "react";
import { ShieldAlert, Check, X } from "lucide-react";
import { toast } from "sonner";
import { getApprovals } from "../../lib/api";

const RISK_TONE = {
  low: "border-line text-ink-muted",
  medium: "border-yellow-400 text-yellow-400",
  high: "border-red-400 text-red-400",
};

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [resolved, setResolved] = useState({});

  useEffect(() => {
    getApprovals().then(setApprovals).catch(() => {});
  }, []);

  const decide = (id, action) => {
    setResolved((r) => ({ ...r, [id]: action }));
    toast.success(`${action === "approve" ? "Approved" : "Vetoed"} ${id}`);
  };

  return (
    <div className="px-6 py-10 md:px-10" data-testid="approvals-page">
      <header className="mb-10">
        <div className="mb-2 text-[11px] uppercase tracking-widest text-acid">// approvals</div>
        <h1 className="font-display text-3xl tracking-tighter md:text-4xl">Human-in-the-loop queue.</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Guard escalates risky outbound actions here. Approve, veto, or open the full context.
        </p>
      </header>

      <ul className="grid gap-px bg-line">
        {approvals.map((a) => {
          const decision = resolved[a.id];
          return (
            <li key={a.id} className="bg-bg-surface p-6" data-testid={`approval-${a.id}`}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 text-[11px] uppercase tracking-widest">
                    <span className="font-mono text-acid">{a.agent}</span>
                    <span className={`border px-2 py-0.5 ${RISK_TONE[a.risk]}`}>{a.risk}</span>
                    <span className="text-ink-faint">{a.created_at}</span>
                  </div>
                  <h3 className="mt-3 font-display text-lg tracking-tight">
                    <ShieldAlert className="mr-2 inline h-4 w-4 text-acid" strokeWidth={1.5} />
                    {a.action}
                  </h3>
                  <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">{a.summary}</p>
                </div>
                <div className="flex shrink-0 gap-2">
                  {decision ? (
                    <span
                      className={`border px-4 py-2 text-[11px] uppercase tracking-widest ${
                        decision === "approve" ? "border-acid text-acid" : "border-red-400 text-red-400"
                      }`}
                      data-testid={`approval-decision-${a.id}`}
                    >
                      {decision === "approve" ? "approved" : "vetoed"}
                    </span>
                  ) : (
                    <>
                      <button
                        onClick={() => decide(a.id, "veto")}
                        data-testid={`approval-veto-${a.id}`}
                        className="inline-flex items-center gap-1 border border-line bg-bg-surface px-3 py-2 text-[11px] uppercase tracking-widest text-ink-muted transition-colors hover:border-red-400 hover:text-red-400"
                      >
                        <X className="h-3 w-3" /> veto
                      </button>
                      <button
                        onClick={() => decide(a.id, "approve")}
                        data-testid={`approval-approve-${a.id}`}
                        className="inline-flex items-center gap-1 border border-acid bg-acid px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-black shadow-glowSm transition-colors hover:bg-acid-soft"
                      >
                        <Check className="h-3 w-3" /> approve
                      </button>
                    </>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
