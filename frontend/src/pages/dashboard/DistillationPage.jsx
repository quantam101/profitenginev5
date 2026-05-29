import React, { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { PageHeader, Metric } from "./_shared";
import { getDistillation } from "../../lib/api";

export default function DistillationPage() {
  const [d, setD] = useState(null);
  useEffect(() => { getDistillation().then(setD).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  if (!d) return <div className="px-6 py-10 md:px-10" data-testid="distillation-page" />;
  return (
    <div className="px-6 py-10 md:px-10" data-testid="distillation-page">
      <PageHeader eyebrow="// distillation" title="Tiered inference router." subtitle={`Cache → ${d.cheap_model || "cheap"} → ${d.expensive_model || "expensive"}. Every prompt hits the cheapest tier that meets quality, with strict-JSON outputs and SHA-256 cache.`} />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 mb-6">
        <Metric label="state" value={d.state} testId="dist-state" />
        <Metric label="savings vs baseline" value={`${Math.round(d.savings_vs_baseline_pct * 100)}%`} testId="dist-savings" />
        <Metric label="pipeline runs · 24h" value={d.pipeline_runs_24h.toLocaleString()} testId="dist-runs" />
        <Metric label="cascade tiers" value={Object.keys(d.tier_routing).length} testId="dist-tiers" />
      </div>
      <div className="ent-card p-6" data-testid="dist-routing">
        <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
          <Sparkles className="h-3.5 w-3.5 text-ok" /> routing split
        </div>
        <div className="space-y-3">
          {Object.entries(d.tier_routing).map(([k, v]) => (
            <div key={k} className="text-sm" data-testid={`distill-${k}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono">{k}</span>
                <span className="text-ok">{Math.round(v * 100)}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-soft bg-bg-elev/60">
                <div className="h-full bg-ok" style={{ width: `${v * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
