import React, { useEffect, useState } from "react";
import { Crown, ShieldCheck } from "lucide-react";
import { PageHeader, Metric, StatusBadge } from "./_shared";
import { getSovereignStatus, getSovereignDecisions } from "../../lib/api";

export default function SovereignPage() {
  const [sov, setSov] = useState(null);
  const [decisions, setDecisions] = useState([]);
  useEffect(() => {
    getSovereignStatus().then(setSov).catch(() => {});
    getSovereignDecisions().then(setDecisions).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="sovereign-page">
      <PageHeader
        eyebrow="// sovereign-v1"
        title="Governance layer."
        subtitle="Sovereign orchestrates the six specialists. Every decision is logged with rationale, confidence and a verdict."
      />
      {sov && (
        <>
          <div className="sov-card p-6" data-testid="sov-mission">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-sov-soft">
              <Crown className="h-3.5 w-3.5" /> current objective
            </div>
            <h2 className="mt-2 font-display text-2xl">{sov.current_objective}</h2>
            <div className="mt-3 text-[11px] uppercase tracking-widest text-ink-muted">
              model {sov.model} · next cycle in {sov.next_cycle_in_min}m
            </div>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4" data-testid="sov-safety">
            <Metric label="tokens used today" value={sov.safety.daily_tokens_used.toLocaleString()} delta={`cap ${sov.safety.daily_token_cap.toLocaleString()}`} testId="sov-tokens" />
            <Metric label="spend today" value={`$${sov.safety.daily_usd}`} delta={`cap $${sov.safety.daily_usd_cap}`} testId="sov-spend" />
            <Metric label="circuit breaker" value={sov.safety.circuit_breaker} tone="ok" testId="sov-breaker" />
            <Metric label="decisions today" value={sov.decisions_today} tone="sov" testId="sov-decisions" />
          </div>
        </>
      )}
      <h3 className="mt-10 mb-4 text-[11px] uppercase tracking-widest text-ok">// decision log</h3>
      <ul className="space-y-3">
        {decisions.map((d) => (
          <li key={d.id} className="sov-card p-5" data-testid={`sov-decision-${d.id}`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className="font-display text-lg">{d.summary}</h4>
              <div className="flex items-center gap-2 text-[11px]">
                <span className="badge badge-sov">{d.verdict}</span>
                <span className="text-ink-muted">conf {(d.confidence * 100).toFixed(0)}%</span>
                <span className="text-ink-faint">{d.at}</span>
              </div>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ink-muted">
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5 text-sov-soft" strokeWidth={1.75} />
              {d.rationale}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
