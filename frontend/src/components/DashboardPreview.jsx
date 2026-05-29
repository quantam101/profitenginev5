import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, LayoutDashboard, ShieldAlert, BarChart3, FileText } from "lucide-react";

const previews = [
  {
    to: "/dashboard",
    icon: LayoutDashboard,
    title: "Overview",
    desc: "Live cycle, revenue, agent status. The cockpit you check three times a day.",
    metric: "$14,820 / 30d",
  },
  {
    to: "/dashboard/approvals",
    icon: ShieldAlert,
    title: "Approvals queue",
    desc: "Guard escalates risky outbound actions for human sign-off. Approve or veto in one click.",
    metric: "4 pending",
  },
  {
    to: "/dashboard/revenue",
    icon: BarChart3,
    title: "Revenue streams",
    desc: "Track how Revenue routes traffic across affiliates, products and ads — and reallocate.",
    metric: "+18% vs last 30d",
  },
  {
    to: "/dashboard/content",
    icon: FileText,
    title: "Content studio",
    desc: "Every asset Content + Video shipped this week, with channel and earnings inline.",
    metric: "62 assets",
  },
];

export default function DashboardPreview() {
  return (
    <section id="preview" className="border-b border-line py-24 md:py-32" data-testid="preview-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-16 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// command center</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              The dashboard from<br />
              <span className="text-acid">already-here</span> — now in v5.
            </h2>
            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-ink-muted">
              We ported the production command center we built for already-here-llc straight into
              ProfitEngine v5. Same approvals queue, same revenue routing, same agent grid — now
              wired to the v5 cycle bus.
            </p>
          </div>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center gap-2 border border-acid bg-acid px-5 py-3 text-xs font-bold uppercase tracking-widest text-black shadow-glow transition-colors hover:bg-acid-soft md:col-span-4 md:justify-self-end"
            data-testid="preview-open-cta"
          >
            Open dashboard <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-2">
          {previews.map((p, i) => {
            const Icon = p.icon;
            return (
              <Link
                key={p.to}
                to={p.to}
                className="group flex items-center justify-between gap-6 bg-bg-surface p-8 transition-colors hover:bg-bg-elev"
                data-testid={`preview-card-${i}`}
              >
                <div className="flex items-start gap-5">
                  <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center border border-line bg-bg text-acid transition-colors group-hover:border-acid">
                    <Icon className="h-5 w-5" strokeWidth={1.5} />
                  </div>
                  <div>
                    <h3 className="font-display text-lg tracking-tight">{p.title}</h3>
                    <p className="mt-2 max-w-sm text-sm leading-relaxed text-ink-muted">{p.desc}</p>
                    <div className="mt-3 inline-flex items-center gap-2 text-[11px] uppercase tracking-widest text-acid">
                      {p.metric}
                    </div>
                  </div>
                </div>
                <ArrowRight className="hidden h-5 w-5 shrink-0 text-ink-muted transition-colors group-hover:text-acid md:block" />
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
