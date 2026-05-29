import React, { useEffect, useState } from "react";
import { Server, ExternalLink } from "lucide-react";
import { PageHeader, StatusBadge } from "./_shared";
import { getDeployments } from "../../lib/api";

export default function DeploymentsPage() {
  const [d, setD] = useState([]);
  useEffect(() => { getDeployments().then(setD).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="deployments-page">
      <PageHeader eyebrow="// deployments" title="Live services." subtitle="Every service ProfitEngine v5 ships, with version and health." />
      <div className="ent-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-line text-left text-[10px] uppercase tracking-widest text-ink-muted">
            <th className="px-5 py-3">service</th><th className="px-5 py-3">env</th><th className="px-5 py-3">version</th>
            <th className="px-5 py-3">status</th><th className="px-5 py-3">url</th><th className="px-5 py-3">deployed</th>
          </tr></thead>
          <tbody>
            {d.map((row) => (
              <tr key={row.id} className="border-b border-line last:border-b-0" data-testid={`deploy-${row.id}`}>
                <td className="px-5 py-4"><span className="flex items-center gap-2"><Server className="h-3.5 w-3.5 text-ok" /> {row.service}</span></td>
                <td className="px-5 py-4 text-ink-muted">{row.env}</td>
                <td className="px-5 py-4 font-mono text-ok">{row.version}</td>
                <td className="px-5 py-4"><StatusBadge status={row.status} /></td>
                <td className="px-5 py-4 text-ink-muted">{row.url === "—" ? "—" : (<a href={`https://${row.url}`} className="text-ok hover:underline" target="_blank" rel="noreferrer">{row.url} <ExternalLink className="inline h-3 w-3" /></a>)}</td>
                <td className="px-5 py-4 text-ink-muted">{row.deployed_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
