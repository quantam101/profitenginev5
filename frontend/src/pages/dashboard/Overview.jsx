import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, Area, AreaChart,
} from "recharts";
import { ArrowUpRight, ShieldAlert, Cpu } from "lucide-react";
import { getRevenue, getAgents, getApprovals, getStats } from "../../lib/api";

export default function Overview() {
  const [revenue, setRevenue] = useState([]);
  const [agents, setAgents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    getRevenue(14).then(setRevenue).catch(() => {});
    getAgents().then(setAgents).catch(() => {});
    getApprovals().then(setApprovals).catch(() => {});
    getStats().then(setStats).catch(() => {});
  }, []);

  const totalRev = revenue.reduce((s, p) => s + p.amount, 0);
  const onlineAgents = agents.filter((a) => a.status === "online").length;

  return (
    <div className="px-6 py-10 md:px-10" data-testid="overview-page">
      <header className="mb-10">
        <div className="mb-2 text-[11px] uppercase tracking-widest text-acid">// overview</div>
        <h1 className="font-display text-3xl tracking-tighter md:text-4xl">Today's autopilot.</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Live state of the engine across revenue, agents and approvals. Updated every cycle tick.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-4">
        <KPI
          label="revenue last 14d"
          value={`$${Math.round(totalRev).toLocaleString()}`}
          delta="+12% vs prior"
          testId="kpi-revenue"
        />
        <KPI label="agents online" value={onlineAgents} delta={`${agents.length} total`} testId="kpi-agents" />
        <KPI label="approvals pending" value={approvals.length} delta="3 low / 1 high" testId="kpi-approvals" />
        <KPI label="operators on beta" value={stats?.devs_joined ?? "—"} delta="closed beta" testId="kpi-beta" />
      </div>

      <section className="mt-px grid gap-px bg-line lg:grid-cols-3">
        <div className="bg-bg-surface p-6 lg:col-span-2" data-testid="overview-revenue-chart">
          <div className="mb-4 flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
            <span>// revenue, last 14 days</span>
            <Link to="/dashboard/revenue" className="inline-flex items-center gap-1 text-acid">
              full view <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer>
              <AreaChart data={revenue}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00FF41" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#00FF41" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#1F2937" strokeDasharray="0" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "#4B5563", fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: "#4B5563", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0C0C0C",
                    border: "1px solid #00FF41",
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: 11,
                  }}
                />
                <Area type="monotone" dataKey="amount" stroke="#00FF41" fill="url(#rev)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-bg-surface p-6" data-testid="overview-approvals">
          <div className="mb-4 flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
            <span><ShieldAlert className="inline h-3.5 w-3.5 text-acid" strokeWidth={1.75} /> approvals queue</span>
            <Link to="/dashboard/approvals" className="text-acid">view</Link>
          </div>
          <ul className="space-y-3">
            {approvals.slice(0, 4).map((a) => (
              <li key={a.id} className="border border-line bg-bg p-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-acid">{a.agent}</span>
                  <span
                    className={`text-[10px] uppercase tracking-widest ${
                      a.risk === "high"
                        ? "text-red-400"
                        : a.risk === "medium"
                        ? "text-yellow-400"
                        : "text-ink-muted"
                    }`}
                  >
                    {a.risk}
                  </span>
                </div>
                <div className="mt-1 text-ink">{a.action}</div>
                <div className="mt-1 text-ink-muted text-[11px]">{a.summary}</div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mt-px grid gap-px bg-line md:grid-cols-2 lg:grid-cols-3" data-testid="overview-agents">
        {agents.map((a) => (
          <div key={a.id} className="bg-bg-surface p-5">
            <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
              <span><Cpu className="inline h-3 w-3 text-acid" /> {a.name}</span>
              <span className={a.status === "online" ? "text-acid" : a.status === "paused" ? "text-yellow-400" : "text-ink-muted"}>
                ● {a.status}
              </span>
            </div>
            <div className="mt-2 text-xs text-ink-muted">{a.role}</div>
            <div className="mt-3 flex items-center justify-between text-[11px]">
              <span><span className="text-acid">{Math.round(a.success_rate * 100)}%</span> success</span>
              <span><span className="text-acid">{a.runs_today}</span> runs</span>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

function KPI({ label, value, delta, testId }) {
  return (
    <div className="bg-bg-surface px-6 py-6" data-testid={testId}>
      <div className="text-[11px] uppercase tracking-widest text-ink-muted">{label}</div>
      <div className="mt-2 font-display text-3xl tracking-tighter text-acid">{value}</div>
      <div className="mt-1 text-[11px] text-ink-muted">{delta}</div>
    </div>
  );
}
