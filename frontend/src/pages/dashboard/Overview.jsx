import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Area, AreaChart } from "recharts";
import { ArrowUpRight, ShieldAlert, Cpu, Crown, Award, DollarSign } from "lucide-react";
import { PageHeader, Metric, StatusBadge } from "./_shared";
import {
  getRevenue, getAgents, getApprovals, getStats, getLedgerProgress, getSovereignStatus,
  getSovereignDecisions, getProofOfWork,
} from "../../lib/api";

function riskTone(risk) {
  if (risk === "high") return "text-danger";
  if (risk === "medium") return "text-warn";
  return "text-ink-muted";
}

export default function Overview() {
  const [revenue, setRevenue] = useState([]);
  const [agents, setAgents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [stats, setStats] = useState(null);
  const [ledger, setLedger] = useState(null);
  const [sov, setSov] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [pow, setPow] = useState(null);

  useEffect(() => {
    getRevenue(14).then(setRevenue).catch(() => {});
    getAgents().then(setAgents).catch(() => {});
    getApprovals().then(setApprovals).catch(() => {});
    getStats().then(setStats).catch(() => {});
    getLedgerProgress().then(setLedger).catch(() => {});
    getSovereignStatus().then(setSov).catch(() => {});
    getSovereignDecisions().then(setDecisions).catch(() => {});
    getProofOfWork().then(setPow).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalRev = revenue.reduce((s, p) => s + p.amount, 0);
  const onlineAgents = agents.filter((a) => a.status === "online" || a.status === "active").length;
  const pct = ledger ? Math.round(ledger.pct * 100) : 0;

  return (
    <div className="px-6 py-10 md:px-10" data-testid="overview-page">
      <PageHeader
        eyebrow="// overview"
        title="Today's autopilot."
        subtitle="Live state of the Command OS across revenue, agents, approvals and Sovereign decisions. Updated every cycle tick."
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5" data-testid="overview-kpis">
        <Metric label="revenue last 14d" value={`$${Math.round(totalRev).toLocaleString()}`} delta="+12% vs prior" testId="kpi-revenue" />
        <Metric label="agents online" value={`${onlineAgents}/${agents.length}`} delta="11-agent fleet" testId="kpi-agents" />
        <Metric label="approvals pending" value={approvals.length} delta="3 low / 1 high" tone="warn" testId="kpi-approvals" />
        <Metric label="proof-of-work" value={pow ? `${Math.round(pow.score * 100)}%` : "—"} delta={pow ? `${pow.uptime_pct}% uptime` : null} testId="kpi-pow" />
        <Metric label="$25k unlock progress" value={`${pct}%`} delta={ledger ? `$${Math.round(ledger.earned_usd).toLocaleString()} / $25,000` : null} tone="sov" testId="kpi-ledger" />
      </div>

      {/* Sovereign + chart */}
      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="sov-card p-6 lg:col-span-2" data-testid="overview-sov-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-sov-soft">
              <Crown className="h-3.5 w-3.5" strokeWidth={1.75} /> sovereign decision · latest
            </div>
            <Link to="/dashboard/sovereign" className="inline-flex items-center gap-1 text-[11px] text-ok">
              full log <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          {decisions[0] && (
            <div className="relative mt-4">
              <h3 className="font-display text-lg leading-snug">{decisions[0].summary}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">{decisions[0].rationale}</p>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px]">
                <span className="badge badge-sov">{decisions[0].verdict}</span>
                <span className="text-ink-muted">confidence {(decisions[0].confidence * 100).toFixed(0)}%</span>
                <span className="text-ink-faint">· {decisions[0].at}</span>
              </div>
            </div>
          )}
          {sov && (
            <div className="relative mt-6 grid grid-cols-3 gap-3 border-t border-line pt-4 text-[11px] text-ink-muted">
              <div><span className="text-ok">{sov.safety.daily_tokens_used.toLocaleString()}</span>/{sov.safety.daily_token_cap.toLocaleString()} tokens</div>
              <div><span className="text-ok">${sov.safety.daily_usd}</span>/${sov.safety.daily_usd_cap} spend cap</div>
              <div>circuit breaker <span className="text-ok">{sov.safety.circuit_breaker}</span></div>
            </div>
          )}
        </div>

        <div className="ent-card p-6" data-testid="overview-approvals">
          <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
            <span className="inline-flex items-center gap-1.5"><ShieldAlert className="h-3.5 w-3.5 text-ok" strokeWidth={1.75} /> approvals queue</span>
            <Link to="/dashboard/approvals" className="text-ok">view</Link>
          </div>
          <ul className="mt-3 space-y-2">
            {approvals.slice(0, 4).map((a) => (
              <li key={a.id} className="rounded-soft border border-line bg-bg-panel/40 p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-ok">{a.agent}</span>
                  <span className={`text-[10px] uppercase tracking-widest ${riskTone(a.risk)}`}>{a.risk}</span>
                </div>
                <div className="mt-1 text-ink">{a.action}</div>
                <div className="mt-1 text-[11px] text-ink-muted">{a.summary}</div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-3" data-testid="overview-revenue-chart">
        <div className="ent-card p-6 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
            <span className="inline-flex items-center gap-1.5"><DollarSign className="h-3.5 w-3.5 text-ok" /> revenue · last 14 days</span>
            <Link to="/dashboard/revenue" className="inline-flex items-center gap-1 text-ok">full view <ArrowUpRight className="h-3 w-3" /></Link>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer>
              <AreaChart data={revenue}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
                <Tooltip contentStyle={{ background: "#0f1423", border: "1px solid rgba(34,197,94,0.3)", fontSize: 11, borderRadius: 8 }} />
                <Area type="monotone" dataKey="amount" stroke="#22c55e" fill="url(#rev)" strokeWidth={1.75} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="ent-card p-6">
          <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
            <Award className="h-3.5 w-3.5 text-ok" strokeWidth={1.75} /> proof of work · 24h
          </div>
          {pow && (
            <div className="space-y-3 text-sm">
              <Row label="passed cycles" value={pow.passed_cycles_24h} good />
              <Row label="failed cycles" value={pow.failed_cycles_24h} bad={pow.failed_cycles_24h > 0} />
              <Row label="signed assets" value={pow.signed_assets_24h} good />
              <Row label="guard blocks" value={pow.guard_blocks_24h} warn={pow.guard_blocks_24h > 0} />
              <Row label="uptime" value={`${pow.uptime_pct}%`} good />
            </div>
          )}
        </div>
      </section>

      {/* Agent fleet snapshot */}
      <section className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" data-testid="overview-agents">
        {agents.map((a) => (
          <div key={a.id} className={a.tier === "sovereign" ? "sov-card p-5" : "ent-card p-5"}>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-ink-muted">
                {a.tier === "sovereign" ? (
                  <Crown className="h-3.5 w-3.5 text-sov-soft" />
                ) : (
                  <Cpu className="h-3.5 w-3.5 text-ok" />
                )}
                <span className="truncate">{a.name}</span>
              </span>
              <StatusBadge status={a.status} />
            </div>
            <div className="mt-1 text-[11px] text-ink-faint">{a.category || (a.tier === "sovereign" ? "orchestrator" : "specialist")}</div>
            <div className="mt-3 flex items-center justify-between text-[11px]">
              <span><span className="text-ok">{Math.round(a.success_rate * 100)}%</span> success</span>
              <span><span className="text-ok">{(a.run_count || a.runs_today).toLocaleString()}</span> runs</span>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

function rowTone({ good, bad, warn }) {
  if (bad) return "text-danger";
  if (warn) return "text-warn";
  if (good) return "text-ok";
  return "text-ink";
}

function Row({ label, value, good, bad, warn }) {
  return (
    <div className="flex items-center justify-between border-b border-line pb-2 last:border-b-0">
      <span className="text-ink-muted text-xs uppercase tracking-widest">{label}</span>
      <span className={`font-mono text-sm font-semibold ${rowTone({ good, bad, warn })}`}>{value}</span>
    </div>
  );
}
