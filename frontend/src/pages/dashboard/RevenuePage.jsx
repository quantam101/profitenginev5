import React, { useEffect, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, ResponsiveContainer, CartesianGrid, Tooltip,
} from "recharts";
import { getRevenue } from "../../lib/api";

const RANGES = [
  { label: "7d", days: 7 },
  { label: "14d", days: 14 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
];

export default function RevenuePage() {
  const [days, setDays] = useState(30);
  const [series, setSeries] = useState([]);
  useEffect(() => {
    getRevenue(days).then(setSeries).catch(() => {});
  }, [days]);

  const total = series.reduce((s, p) => s + p.amount, 0);
  const avg = series.length ? total / series.length : 0;
  const max = series.reduce((m, p) => (p.amount > m ? p.amount : m), 0);

  return (
    <div className="px-6 py-10 md:px-10" data-testid="revenue-page">
      <header className="mb-10 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[11px] uppercase tracking-widest text-acid">// revenue</div>
          <h1 className="font-display text-3xl tracking-tighter md:text-4xl">Streams &amp; routing.</h1>
          <p className="mt-2 text-sm text-ink-muted">
            Revenue agent reallocates traffic across affiliates, products and ads every cycle.
          </p>
        </div>
        <div className="flex gap-2" data-testid="revenue-range-selector">
          {RANGES.map((r) => (
            <button
              key={r.label}
              onClick={() => setDays(r.days)}
              data-testid={`revenue-range-${r.label}`}
              className={`border px-3 py-1.5 text-[11px] uppercase tracking-widest transition-colors ${
                days === r.days
                  ? "border-acid bg-acid text-black shadow-glowSm"
                  : "border-line bg-bg-surface text-ink-muted hover:border-acid hover:text-acid"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-3">
        <KPI label="total" value={`$${Math.round(total).toLocaleString()}`} testId="revenue-kpi-total" />
        <KPI label="avg / day" value={`$${Math.round(avg).toLocaleString()}`} testId="revenue-kpi-avg" />
        <KPI label="peak day" value={`$${Math.round(max).toLocaleString()}`} testId="revenue-kpi-peak" />
      </div>

      <div className="mt-px bg-bg-surface p-6">
        <div className="h-80 w-full">
          <ResponsiveContainer>
            <AreaChart data={series}>
              <defs>
                <linearGradient id="rev2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00FF41" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="#00FF41" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1F2937" vertical={false} />
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
              <Area type="monotone" dataKey="amount" stroke="#00FF41" strokeWidth={2} fill="url(#rev2)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function KPI({ label, value, testId }) {
  return (
    <div className="bg-bg-surface px-6 py-6" data-testid={testId}>
      <div className="text-[11px] uppercase tracking-widest text-ink-muted">{label}</div>
      <div className="mt-2 font-display text-3xl tracking-tighter text-acid">{value}</div>
    </div>
  );
}
