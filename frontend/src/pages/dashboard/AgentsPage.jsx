import React, { useEffect, useState } from "react";
import {
  Bot, Activity, CheckCircle, AlertCircle, Crown, ShieldCheck, FileText,
  DollarSign, GraduationCap, Radar, Film, Palette, Link as LinkIcon, Stethoscope, Briefcase,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader, Metric } from "./_shared";
import { getAgents, executeAgent, getFleetStats } from "../../lib/api";

const CATEGORY_ICON = {
  orchestrator: Crown,
  security: ShieldCheck,
  content: FileText,
  revenue: DollarSign,
  learning: GraduationCap,
};

const CATEGORY_TONE = {
  orchestrator: "text-sov-soft border-sov/40 bg-sov/10",
  security: "text-info border-info/40 bg-info/10",
  content: "text-ok border-ok/30 bg-ok/10",
  revenue: "text-warn border-warn/40 bg-warn/10",
  learning: "text-review border-review/40 bg-review/10",
};

const NAME_ICON = {
  "sovereign-orchestrator": Crown,
  "cost-guard": ShieldCheck,
  "content-generation": FileText,
  "proposal-engine": Briefcase,
  "lifelong-catch-correct": GraduationCap,
  "seo-scout": Radar,
  "faceless-video": Film,
  "pod-designer": Palette,
  "affiliate-link": LinkIcon,
  "health-oracle": Stethoscope,
  "procurement-scout": Radar,
};

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [fleet, setFleet] = useState(null);
  useEffect(() => {
    getAgents().then(setAgents).catch(() => {});
    getFleetStats().then(setFleet).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = async (id) => {
    try {
      const r = await executeAgent(id);
      toast.success(`${r.message} run_id ${r.run_id.slice(0, 8)}`);
    } catch {
      toast.error("Failed to queue agent");
    }
  };

  const total = fleet?.total ?? agents.length;
  const runs = fleet?.total_runs ?? agents.reduce((s, a) => s + a.run_count, 0);
  const success = fleet?.fleet_success_rate ?? 98;

  return (
    <div className="px-6 py-10 md:px-10" data-testid="agents-page">
      <PageHeader
        eyebrow="// agent command center"
        title="Agent Command Center"
        subtitle={`Manage and monitor ${total} autonomous agents · Fleet ${success}% success across ${runs.toLocaleString()} historical runs`}
      />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 mb-6">
        <Metric label="Total Agents" value={total} testId="fleet-total" />
        <Metric label="Active" value={fleet?.active ?? agents.filter((a) => a.status === "active").length} testId="fleet-active" />
        <Metric label="Total Runs" value={runs.toLocaleString()} testId="fleet-runs" />
        <Metric label="Fleet Success Rate" value={`${success}%`} testId="fleet-success" />
      </div>

      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-[11px] uppercase tracking-widest text-ok">// agent fleet</h3>
        <span className="text-[11px] uppercase tracking-widest text-ink-faint">{total} agents</span>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="agents-grid">
        {agents.map((a) => {
          const isSov = a.tier === "sovereign";
          const Icon = NAME_ICON[a.id] || CATEGORY_ICON[a.category] || Bot;
          const successPct = Math.round(a.success_rate * 100);
          const healthy = successPct >= 95;
          return (
            <article key={a.id} className={isSov ? "sov-card p-6" : "ent-card p-6"} data-testid={`agent-${a.id}`}>
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-4 w-4 shrink-0 ${isSov ? "text-sov-soft" : "text-ok"}`} strokeWidth={1.75} />
                    <h4 className="truncate font-display text-base font-semibold">{a.name}</h4>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="status-badge-active">{a.status}</span>
                    <span className={`badge ${CATEGORY_TONE[a.category] || "badge-muted"}`}>{a.category}</span>
                  </div>
                  <p className="mt-3 line-clamp-2 text-sm text-ink-muted">{a.mission}</p>
                </div>
                <button
                  onClick={() => run(a.id)}
                  data-testid={`agent-execute-${a.id}`}
                  className="shrink-0 inline-flex items-center gap-1 rounded-soft border border-ok bg-ok/10 px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-ok hover:bg-ok hover:text-bg-deep"
                >
                  <Activity className="h-3.5 w-3.5" /> Execute
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-line pt-3 text-[11px]">
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">Runs</p>
                  <p className="font-semibold text-ink">{a.run_count.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">Success rate</p>
                  <p className={`font-semibold flex items-center gap-1 ${healthy ? "text-ok" : "text-warn"}`}>
                    {healthy ? <CheckCircle className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                    {successPct}%
                  </p>
                </div>
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">{a.recent_fails === 0 ? "Status" : "Recent fails"}</p>
                  <p className={`font-semibold ${a.recent_fails === 0 ? "text-ok" : "text-warn"}`}>
                    {a.recent_fails === 0 ? "Clean" : a.recent_fails}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-ink-faint">
                <span>model: <span className="font-mono">{a.model}</span></span>
                <span>cycle {a.cycle_interval_min}m</span>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
