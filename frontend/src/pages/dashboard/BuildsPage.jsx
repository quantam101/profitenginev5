import React, { useEffect, useState } from "react";
import { GitBranch, CheckCircle, XCircle, Clock } from "lucide-react";
import { PageHeader } from "./_shared";
import { getBuilds } from "../../lib/api";

export default function BuildsPage() {
  const [builds, setBuilds] = useState([]);
  useEffect(() => { getBuilds().then(setBuilds).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="builds-page">
      <PageHeader eyebrow="// builds" title="CI pipeline." subtitle="Latest runs of the v5 build pipeline — every PR, every merge, every AST self-upgrade." />
      <ul className="space-y-2">
        {builds.map((b) => {
          const ok = b.status === "success";
          const Icon = ok ? CheckCircle : XCircle;
          return (
            <li key={b.id} className="ent-card flex items-center justify-between p-4" data-testid={`build-${b.id}`}>
              <div className="flex items-center gap-4 min-w-0">
                <Icon className={`h-5 w-5 shrink-0 ${ok ? "text-ok" : "text-danger"}`} />
                <div className="min-w-0">
                  <div className="font-display text-sm">{b.title}</div>
                  <div className="mt-1 flex items-center gap-3 text-[11px] text-ink-muted">
                    <span className="inline-flex items-center gap-1"><GitBranch className="h-3 w-3" /> {b.branch}</span>
                    <span className="font-mono">{b.commit}</span>
                    <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {b.duration_s}s</span>
                    <span className="text-ink-faint">{b.started_at}</span>
                  </div>
                </div>
              </div>
              <span className={`status-badge-${ok ? "success" : "failed"}`}>{b.status}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
