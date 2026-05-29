import React, { useEffect, useState } from "react";
import { KeyRound, Lock, AlertTriangle } from "lucide-react";
import { PageHeader, StatusBadge } from "./_shared";
import { getSecrets } from "../../lib/api";

export default function SecretsPage() {
  const [secrets, setSecrets] = useState([]);
  useEffect(() => { getSecrets().then(setSecrets).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="secrets-page">
      <PageHeader eyebrow="// secrets" title="Credential vault." subtitle="Names + rotation status only. Values are never returned to the dashboard." />
      <div className="grid gap-3 md:grid-cols-2">
        {secrets.map((s) => (
          <div key={s.id} className="ent-card flex items-center justify-between p-4" data-testid={`secret-${s.id}`}>
            <div className="flex items-center gap-3 min-w-0">
              {s.set ? <Lock className="h-4 w-4 shrink-0 text-ok" /> : <AlertTriangle className="h-4 w-4 shrink-0 text-warn" />}
              <div>
                <div className="font-mono text-sm">{s.name}</div>
                <div className="mt-0.5 text-[11px] text-ink-muted">last rotated {s.last_rotated}</div>
              </div>
            </div>
            <StatusBadge status={s.set ? "active" : "idle"} />
          </div>
        ))}
      </div>
      <p className="mt-6 inline-flex items-center gap-2 text-[11px] text-ink-muted">
        <KeyRound className="h-3.5 w-3.5" /> Secrets are stored in your OS keychain or .env — never persisted by the dashboard.
      </p>
    </div>
  );
}
