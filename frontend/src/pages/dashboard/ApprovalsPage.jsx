import React, { useEffect, useState } from "react";
import { ShieldAlert, Check, X } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "./_shared";
import { getApprovals, decideApproval } from "../../lib/api";

const RISK_TONE = { low: "badge-info", medium: "badge-warn", high: "badge-danger" };

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState([]);
  const [resolved, setResolved] = useState({});
  useEffect(() => {
    getApprovals().then(setApprovals).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const decide = async (id, decision) => {
    setResolved((r) => ({ ...r, [id]: decision }));
    try {
      await decideApproval(id, decision);
      toast.success(`${decision === "approve" ? "Approved" : "Vetoed"} ${id}`);
    } catch {
      toast.error("Could not record decision");
    }
  };

  return (
    <div className="px-6 py-10 md:px-10" data-testid="approvals-page">
      <PageHeader eyebrow="// approvals" title="Human-in-the-loop queue." subtitle="Guard escalates risky outbound actions. Approve, veto, or open the full context — every decision lands in the audit log." />
      <ul className="space-y-3">
        {approvals.map((a) => {
          const decision = resolved[a.id];
          return (
            <li key={a.id} className="ent-card p-6" data-testid={`approval-${a.id}`}>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-[11px]">
                    <span className="font-mono text-ok">{a.agent}</span>
                    <span className={`badge ${RISK_TONE[a.risk]}`}>{a.risk}</span>
                    <span className="text-ink-faint">{a.created_at}</span>
                  </div>
                  <h3 className="mt-2 font-display text-lg">
                    <ShieldAlert className="mr-2 inline h-4 w-4 text-ok" strokeWidth={1.75} />
                    {a.action}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink-muted">{a.summary}</p>
                </div>
                <div className="flex shrink-0 gap-2">
                  {decision ? (
                    <span className={`badge ${decision === "approve" ? "badge-ok" : "badge-danger"}`} data-testid={`approval-decision-${a.id}`}>
                      {decision === "approve" ? "approved" : "vetoed"}
                    </span>
                  ) : (
                    <>
                      <button onClick={() => decide(a.id, "veto")} data-testid={`approval-veto-${a.id}`}
                        className="inline-flex items-center gap-1 rounded-soft border border-line px-3 py-2 text-[11px] uppercase tracking-widest text-ink-muted hover:border-danger hover:text-danger">
                        <X className="h-3 w-3" /> veto
                      </button>
                      <button onClick={() => decide(a.id, "approve")} data-testid={`approval-approve-${a.id}`}
                        className="inline-flex items-center gap-1 rounded-soft border border-ok bg-ok/10 px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-ok hover:bg-ok hover:text-bg-deep">
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
