import React, { useEffect, useState } from "react";
import { Award } from "lucide-react";
import { PageHeader, Metric } from "./_shared";
import { getProofOfWork } from "../../lib/api";

export default function ProofOfWorkPage() {
  const [pow, setPow] = useState(null);
  useEffect(() => { getProofOfWork().then(setPow).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  if (!pow) return <div className="px-6 py-10 md:px-10" data-testid="pow-page" />;
  const score = Math.round(pow.score * 100);
  const C = 2 * Math.PI * 70;
  const offset = C * (1 - pow.score);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="pow-page">
      <PageHeader eyebrow="// proof of work" title="Operational integrity." subtitle="A signed, cryptographic attestation of the engine's last 24h." />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="sov-card p-6 flex flex-col items-center justify-center" data-testid="pow-meter">
          <div className="profit-meter">
            <svg width="180" height="180">
              <circle className="track" cx="90" cy="90" r="70" />
              <circle className="fill" cx="90" cy="90" r="70" strokeDasharray={C} strokeDashoffset={offset} />
            </svg>
          </div>
          <div className="-mt-[110px] font-display text-4xl font-semibold text-sov-soft">{score}%</div>
          <div className="mt-[80px] text-[11px] uppercase tracking-widest text-ink-muted">
            <Award className="inline h-3 w-3 text-sov-soft" /> attested {pow.last_attestation.slice(11, 16)} UTC
          </div>
        </div>
        <div className="lg:col-span-2 grid grid-cols-2 gap-4 md:grid-cols-3" data-testid="pow-grid">
          <Metric label="uptime" value={`${pow.uptime_pct}%`} testId="pow-uptime" />
          <Metric label="passed cycles · 24h" value={pow.passed_cycles_24h} testId="pow-passed" />
          <Metric label="failed cycles · 24h" value={pow.failed_cycles_24h} tone={pow.failed_cycles_24h > 0 ? "warn" : "ok"} testId="pow-failed" />
          <Metric label="signed assets" value={pow.signed_assets_24h} testId="pow-signed" />
          <Metric label="guard blocks" value={pow.guard_blocks_24h} tone="warn" testId="pow-guard" />
          <Metric label="last attestation" value={pow.last_attestation.slice(11, 16)} testId="pow-att" />
        </div>
      </div>
    </div>
  );
}
