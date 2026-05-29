import React, { useEffect, useState } from "react";
import { ScrollText, User, Bot } from "lucide-react";
import { PageHeader } from "./_shared";
import { getAudit } from "../../lib/api";

export default function AuditPage() {
  const [audit, setAudit] = useState([]);
  useEffect(() => { getAudit().then(setAudit).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="audit-page">
      <PageHeader eyebrow="// audit log" title="Immutable event trail." subtitle="Every action — by an operator or an agent — lands here, append-only and signed." />
      <ol className="space-y-2">
        {audit.map((e) => {
          const human = e.actor.includes("@");
          return (
            <li key={e.id} className="ent-card flex items-center justify-between p-4 text-sm" data-testid={`audit-${e.id}`}>
              <div className="flex items-center gap-3 min-w-0">
                {human ? <User className="h-4 w-4 text-info" /> : <Bot className="h-4 w-4 text-ok" />}
                <div>
                  <div className="font-mono text-ok">{e.actor}</div>
                  <div className="text-[11px] text-ink-muted">{e.action} → <span className="font-mono">{e.target}</span></div>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 text-[11px] text-ink-faint"><ScrollText className="h-3 w-3" />{e.at}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
