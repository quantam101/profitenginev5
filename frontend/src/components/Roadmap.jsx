import React from "react";
import { CheckCircle2, Circle, CircleDot } from "lucide-react";

const ITEMS = [
  {
    quarter: "Q4 2025",
    title: "v4 → v5 migration",
    body: "Cycle bus rewrite, Guard agent introduced, AST self-merge engine shipped.",
    state: "done",
  },
  {
    quarter: "Q1 2026",
    title: "Hosted command center",
    body: "Real-time approvals, mobile push, Connector registry v2, audit log export.",
    state: "done",
  },
  {
    quarter: "Q2 2026",
    title: "Public beta + Studio tier",
    body: "Open the waitlist, ship the Studio plan, bake Stripe + paid distribution agents.",
    state: "active",
  },
  {
    quarter: "Q3 2026",
    title: "Multi-workspace orgs",
    body: "Holding tier, SSO, custom Guard policy DSL, white-label brand mode.",
    state: "next",
  },
  {
    quarter: "Q4 2026",
    title: "Edge runtime",
    body: "Self-hosted on your own VPS or k8s, OpenTelemetry, signed assets.",
    state: "next",
  },
];

const ICONS = { done: CheckCircle2, active: CircleDot, next: Circle };
const TONE = { done: "text-ok", active: "text-ok animate-pulse", next: "text-ink-faint" };

export default function Roadmap() {
  return (
    <section id="roadmap" className="border-b border-line py-24 md:py-32" data-testid="roadmap-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-12 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-ok">// roadmap</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              Where the<br />
              <span className="text-ok">engine</span> is heading.
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            Five quarters, eight agents, one autonomous operator stack. Shipped publicly with
            changelogs each Friday.
          </p>
        </div>

        <ol className="relative grid grid-cols-1 gap-px bg-line md:grid-cols-5">
          {ITEMS.map((it, i) => {
            const Icon = ICONS[it.state];
            return (
              <li
                key={it.quarter}
                className="bg-bg-panel p-6"
                data-testid={`roadmap-${it.state}-${i}`}
              >
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-widest text-ok">{it.quarter}</span>
                  <Icon className={`h-4 w-4 ${TONE[it.state]}`} strokeWidth={2} />
                </div>
                <h3 className="font-display text-base leading-tight tracking-tight">{it.title}</h3>
                <p className="mt-3 text-xs leading-relaxed text-ink-muted">{it.body}</p>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
