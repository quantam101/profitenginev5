import React, { useEffect, useState } from "react";
import { Vote, ThumbsUp, ThumbsDown } from "lucide-react";
import { PageHeader, StatusBadge } from "./_shared";
import { getProposals } from "../../lib/api";

export default function ProposalsPage() {
  const [props_, setProps] = useState([]);
  useEffect(() => { getProposals().then(setProps).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="proposals-page">
      <PageHeader eyebrow="// proposals" title="Governance votes." subtitle="Agents propose, operators vote. Sovereign breaks ties." />
      <div className="grid gap-4 md:grid-cols-2">
        {props_.map((p) => (
          <div key={p.id} className="ent-card p-5" data-testid={`proposal-${p.id}`}>
            <div className="flex items-center justify-between">
              <Vote className="h-4 w-4 text-ok" />
              <StatusBadge status={p.state === "passed" ? "success" : p.state === "open" ? "active" : "idle"} />
            </div>
            <h3 className="mt-2 font-display text-base">{p.title}</h3>
            <div className="mt-1 text-[11px] text-ink-faint">proposed by <span className="font-mono">{p.author}</span></div>
            <div className="mt-4 flex items-center justify-between text-[11px]">
              <span className="inline-flex items-center gap-1 text-ok"><ThumbsUp className="h-3 w-3" /> {p.votes_for}</span>
              <span className="inline-flex items-center gap-1 text-danger"><ThumbsDown className="h-3 w-3" /> {p.votes_against}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
