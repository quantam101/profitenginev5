import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Sparkles, ShieldCheck, TrendingUp } from "lucide-react";
import { getProofOfWork, getDistillationStats, getFleetStats, getStats } from "../lib/api";

function Stat({ label, value, accent, testId }) {
  return (
    <div className="border border-line bg-bg-panel/60 p-6" data-testid={testId}>
      <div className="text-[10px] uppercase tracking-widest text-ink-faint">{label}</div>
      <div className={`mt-2 font-display text-3xl tracking-tighter ${accent ? "text-ok" : "text-ink"}`}>{value}</div>
    </div>
  );
}

function StatGrid({ pow }) {
  return (
    <div className="mt-12 grid grid-cols-2 gap-px bg-line md:grid-cols-4">
      <Stat
        label="fleet success · 24h"
        value={pow ? `${Math.round(pow.uptime_pct * 10) / 10}%` : "—"}
        accent
        testId="pow-uptime"
      />
      <Stat label="cycles completed · 24h" value={pow ? pow.passed_cycles_24h : "—"} testId="pow-cycles" />
      <Stat label="signed assets · 24h" value={pow ? pow.signed_assets_24h : "—"} testId="pow-assets" />
      <Stat label="guard blocks · 24h" value={pow ? pow.guard_blocks_24h : "—"} testId="pow-guards" />
    </div>
  );
}

function DistillationCard({ dist, savings }) {
  return (
    <div className="border border-line bg-bg-panel/60 p-8" data-testid="proof-distillation">
      <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ok">
        <Sparkles className="h-3.5 w-3.5" /> distillation router
      </div>
      <div className="font-display text-5xl tracking-tighter text-ok">
        {savings != null ? `${savings}%` : "—"}
      </div>
      <div className="mt-2 text-xs text-ink-muted">token cost saved vs all-Claude baseline</div>
      <div className="mt-6 space-y-1.5 text-[11px] text-ink-muted">
        <div>cheap tier · <span className="font-mono text-ink">{dist?.cheap_model || "gemini-3-flash"}</span></div>
        <div>expensive tier · <span className="font-mono text-ink">{dist?.expensive_model || "claude-sonnet-4-6"}</span></div>
        <div>cache hit rate · <span className="text-ok">
          {dist?.cache_hit_rate != null ? `${Math.round(dist.cache_hit_rate * 100)}%` : "—"}
        </span></div>
      </div>
    </div>
  );
}

function FleetCard({ fleet }) {
  return (
    <div className="border border-line bg-bg-panel/60 p-8" data-testid="proof-fleet">
      <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ok">
        <Activity className="h-3.5 w-3.5" /> agent fleet
      </div>
      <div className="font-display text-5xl tracking-tighter">
        {fleet?.active != null && fleet?.total != null ? `${fleet.active}/${fleet.total}` : "—"}
      </div>
      <div className="mt-2 text-xs text-ink-muted">agents online</div>
      <div className="mt-6 space-y-1.5 text-[11px] text-ink-muted">
        <div>total runs · <span className="font-mono text-ink">{fleet?.total_runs?.toLocaleString?.() || "—"}</span></div>
        <div>fleet success · <span className="text-ok">{fleet?.fleet_success_rate != null ? `${fleet.fleet_success_rate}%` : "—"}</span></div>
        <div>cycle cadence · <span className="font-mono text-ink">continuous</span></div>
      </div>
    </div>
  );
}

function LedgerCard({ stats }) {
  const revenue = stats?.revenue_30d != null
    ? `$${Math.round(stats.revenue_30d).toLocaleString()}`
    : "—";
  return (
    <div className="border border-line bg-bg-panel/60 p-8" data-testid="proof-revenue">
      <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ok">
        <TrendingUp className="h-3.5 w-3.5" /> ledger · 30d
      </div>
      <div className="font-display text-5xl tracking-tighter">{revenue}</div>
      <div className="mt-2 text-xs text-ink-muted">revenue routed through the engine</div>
      <div className="mt-6 space-y-1.5 text-[11px] text-ink-muted">
        <div>posts published · <span className="font-mono text-ink">{stats?.posts_published?.toLocaleString?.() || "—"}</span></div>
        <div>operators on waitlist · <span className="font-mono text-ink">{stats?.devs_joined?.toLocaleString?.() || "—"}</span></div>
        <div>sovereign decisions · today · <span className="text-ok">{stats?.sovereign_decisions_today ?? "—"}</span></div>
      </div>
    </div>
  );
}

function useProofData() {
  const [pow, setPow] = useState(null);
  const [dist, setDist] = useState(null);
  const [fleet, setFleet] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const safe = (label, p, setter) =>
      p.then(setter).catch((e) => console.warn(`[ProofOfWork] ${label}:`, e?.message || e));
    safe("proof-of-work", getProofOfWork(), setPow);
    safe("distillation-stats", getDistillationStats(), setDist);
    safe("fleet-stats", getFleetStats(), setFleet);
    safe("stats", getStats(), setStats);
  }, []);

  return { pow, dist, fleet, stats };
}

export default function ProofOfWork() {
  const { pow, dist, fleet, stats } = useProofData();
  const savings = dist?.savings_pct != null ? Math.round(dist.savings_pct * 100) : null;

  return (
    <section id="proof" className="border-b border-line py-24 md:py-32" data-testid="proof-of-work-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ok">
            <ShieldCheck className="h-3.5 w-3.5" /> // proof of work · live from the engine
          </div>
          <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
            It's not a demo.<br />
            <span className="text-ok">The engine is running right now.</span>
          </h2>
          <p className="mt-4 max-w-2xl text-sm text-ink-muted">
            Every number on this page is pulled from the live ProfitEngine v5
            backend. Refresh and watch them move. Cycles complete, agents queue
            work, the distillation router shaves tokens off every call.
          </p>
        </motion.div>

        <StatGrid pow={pow} />

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          <DistillationCard dist={dist} savings={savings} />
          <FleetCard fleet={fleet} />
          <LedgerCard stats={stats} />
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-3 text-[11px] text-ink-muted">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ok" />
          live · auto-refreshed each visit · open{" "}
          <code className="font-mono text-ink">/api/proof-of-work</code> and{" "}
          <code className="font-mono text-ink">/api/distillation/stats</code> to verify
        </div>
      </div>
    </section>
  );
}
