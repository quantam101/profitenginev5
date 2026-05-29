import React from "react";

export function PageHeader({ eyebrow, title, subtitle, action }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <div className="mb-2 text-[11px] uppercase tracking-widest text-ok">{eyebrow}</div>
        <h1 className="font-display text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
        {subtitle && <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

export function Metric({ label, value, delta, tone = "ok", testId }) {
  const toneCls = tone === "danger" ? "text-danger" : tone === "sov" ? "text-sov-soft" : tone === "warn" ? "text-warn" : "text-ok";
  return (
    <div className="metric" data-testid={testId}>
      <div className="label">{label}</div>
      <div className={`value ${tone === "sov" ? "text-sov-soft" : ""}`}>{value}</div>
      {delta && <div className={`delta ${toneCls}`}>{delta}</div>}
    </div>
  );
}

export function StatusBadge({ status }) {
  return <span className={`status-badge-${status}`}>{status}</span>;
}

export function EmptyState({ children }) {
  return <p className="rounded-card border border-line bg-bg-panel/40 p-6 text-center text-sm text-ink-muted">{children}</p>;
}
