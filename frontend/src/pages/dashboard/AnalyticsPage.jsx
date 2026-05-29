import React, { useEffect, useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { PageHeader, Metric } from "./_shared";
import { getAnalytics, getRevenue } from "../../lib/api";
import { logger } from "../../lib/logger";

// Module-level constants — avoid re-allocating object literals every render.
const CHART_TICK = { fill: "#64748b", fontSize: 10 };
const CHART_TOOLTIP = {
  background: "#0f1423",
  border: "1px solid rgba(34,197,94,0.3)",
  fontSize: 11,
  borderRadius: 8,
};
const BAR_RADIUS = [6, 6, 0, 0];
const TICK_DATE_FMT = (d) => d.slice(5);

export default function AnalyticsPage() {
  const [an, setAn] = useState(null);
  const [series, setSeries] = useState([]);
  useEffect(() => {
    getAnalytics().then(setAn).catch((e) => logger.warn("Analytics.an", e));
    getRevenue(30).then(setSeries).catch((e) => logger.warn("Analytics.revenue", e));
    // Intentional empty deps: API fetchers + setters are module-level stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const channels = an ? Object.entries(an.channel_split).map(([k, v]) => ({ channel: k, pct: Math.round(v * 100) })) : [];
  return (
    <div className="px-6 py-10 md:px-10" data-testid="analytics-page">
      <PageHeader eyebrow="// analytics" title="Mesh telemetry." subtitle="Cycle completion, approval latency and channel split across the 20-agent mesh." />
      {an && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 mb-6">
          <Metric label="daily active agents" value={`${an.daily_active_agents}/20`} testId="analytics-dau" />
          <Metric label="weekly active agents" value={`${an.weekly_active_agents}/20`} testId="analytics-wau" />
          <Metric label="cycle completion" value={`${Math.round(an.cycle_completion_rate * 100)}%`} testId="analytics-cycle" />
          <Metric label="median approval latency" value={`${an.approval_latency_median_s}s`} testId="analytics-latency" />
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="ent-card p-6">
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// revenue · last 30d</div>
          <div className="h-64">
            <ResponsiveContainer>
              <LineChart data={series}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="date" tick={CHART_TICK} tickFormatter={TICK_DATE_FMT} />
                <YAxis tick={CHART_TICK} />
                <Tooltip contentStyle={CHART_TOOLTIP} />
                <Line type="monotone" dataKey="amount" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="ent-card p-6">
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// channel split</div>
          <div className="h-64">
            <ResponsiveContainer>
              <BarChart data={channels}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="channel" tick={CHART_TICK} />
                <YAxis tick={CHART_TICK} />
                <Tooltip contentStyle={CHART_TOOLTIP} />
                <Bar dataKey="pct" fill="#6366f1" radius={BAR_RADIUS} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
