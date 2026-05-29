import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip } from "recharts";
import { PageHeader, Metric, StatusBadge } from "./_shared";
import { getRevenue, getRevenueStreams, getRevenueStats } from "../../lib/api";

const RANGES = [{ label: "7d", days: 7 }, { label: "14d", days: 14 }, { label: "30d", days: 30 }, { label: "90d", days: 90 }];

export default function RevenuePage() {
  const [days, setDays] = useState(30);
  const [series, setSeries] = useState([]);
  const [streams, setStreams] = useState([]);
  const [stats, setStats] = useState(null);
  useEffect(() => {
    getRevenue(days).then(setSeries).catch(() => {});
 // eslint-disable-next-line react-hooks/exhaustive-deps
 // eslint-disable-next-line react-hooks/exhaustive-deps
 }, [days]);
  useEffect(() => {
    getRevenueStreams().then(setStreams).catch(() => {});
    getRevenueStats().then(setStats).catch(() => {});
 // eslint-disable-next-line react-hooks/exhaustive-deps
 // eslint-disable-next-line react-hooks/exhaustive-deps
 }, []);
  const total = series.reduce((s, p) => s + p.amount, 0);
  const avg = series.length ? total / series.length : 0;
  const max = series.reduce((m, p) => (p.amount > m ? p.amount : m), 0);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="revenue-page">
      <PageHeader
        eyebrow="// revenue"
        title="Streams & routing."
        subtitle="Revenue Tracker reallocates traffic across affiliates, products and ads every cycle."
        action={
          <div className="flex gap-2" data-testid="revenue-range-selector">
            {RANGES.map((r) => (
              <button key={r.label} onClick={() => setDays(r.days)} data-testid={`revenue-range-${r.label}`}
                className={`rounded-soft border px-3 py-1.5 text-[11px] uppercase tracking-widest ${days === r.days ? "border-ok bg-ok/10 text-ok" : "border-line text-ink-muted hover:border-ok hover:text-ok"}`}>
                {r.label}
              </button>
            ))}
          </div>
        }
      />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Metric label="total" value={`$${Math.round(total).toLocaleString()}`} testId="revenue-kpi-total" />
        <Metric label="avg / day" value={`$${Math.round(avg).toLocaleString()}`} testId="revenue-kpi-avg" />
        <Metric label="peak day" value={`$${Math.round(max).toLocaleString()}`} testId="revenue-kpi-peak" />
        <Metric label="active streams" value={stats?.active_streams ?? "—"} delta={stats?.best_stream} testId="revenue-kpi-active" />
      </div>
      <div className="ent-card mt-4 p-6">
        <div className="h-80">
          <ResponsiveContainer>
            <AreaChart data={series}>
              <defs>
                <linearGradient id="rev2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#0f1423", border: "1px solid rgba(34,197,94,0.3)", fontSize: 11, borderRadius: 8 }} />
              <Area type="monotone" dataKey="amount" stroke="#22c55e" strokeWidth={2} fill="url(#rev2)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <h3 className="mt-10 mb-4 text-[11px] uppercase tracking-widest text-ok">// active streams</h3>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3" data-testid="revenue-streams">
        {streams.map((s) => (
          <div key={s.id} className="ent-card p-5">
            <div className="flex items-center justify-between">
              <h4 className="font-display text-base">{s.name}</h4>
              <StatusBadge status={s.active ? "active" : "idle"} />
            </div>
            <div className="mt-1 text-[11px] uppercase tracking-widest text-ink-faint">{s.kind}</div>
            <div className="mt-4 grid grid-cols-3 gap-3 text-[11px]">
              <div><div className="text-ink-faint uppercase tracking-widest">MRR</div><div className="text-ok font-semibold">${s.mrr.toLocaleString()}</div></div>
              <div><div className="text-ink-faint uppercase tracking-widest">CTR</div><div className="text-ink">{(s.ctr * 100).toFixed(2)}%</div></div>
              <div><div className="text-ink-faint uppercase tracking-widest">Health</div><div className="text-ok">{(s.health * 100).toFixed(0)}%</div></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
