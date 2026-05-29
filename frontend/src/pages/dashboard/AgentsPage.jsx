import React, { useEffect, useState } from "react";
import { Bot, Activity, CheckCircle, AlertCircle, Crown } from "lucide-react";
import { toast } from "sonner";
import { PageHeader, StatusBadge } from "./_shared";
import { getAgents, executeAgent } from "../../lib/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  useEffect(() => {
    getAgents().then(setAgents).catch(() => {});
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

  return (
    <div className="px-6 py-10 md:px-10" data-testid="agents-page">
      <PageHeader
        eyebrow="// agents"
        title="The 7-agent mesh."
        subtitle="One Sovereign orchestrator + six operational specialists. Each runs in its own sandbox and shares state through the cycle bus."
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {agents.map((a) => {
          const isSov = a.tier === "sovereign";
          const total = (a.success_count || 0) + (a.failure_count || 0);
          const successRate = total > 0 ? Math.round((a.success_count / total) * 100) : Math.round(a.success_rate * 100);
          const healthy = successRate >= 90;
          return (
            <article key={a.id} className={isSov ? "sov-card p-6" : "ent-card p-6"} data-testid={`agent-${a.id}`}>
              <div className="mb-3 flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {isSov ? <Crown className="h-4 w-4 text-sov-soft" /> : <Bot className="h-4 w-4 text-ok" />}
                    <h4 className="truncate font-display text-base font-semibold">{a.name}</h4>
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <StatusBadge status={a.status} />
                    <span className={`status-badge-${isSov ? "active" : "online"}`} style={{ background: isSov ? "rgba(99,102,241,.12)" : "rgba(90,162,255,.10)", color: isSov ? "#818cf8" : "#5aa2ff" }}>{a.type}</span>
                  </div>
                  <p className="mt-3 line-clamp-2 text-sm text-ink-muted">{a.mission}</p>
                </div>
                <button
                  onClick={() => run(a.id)}
                  data-testid={`execute-agent-${a.id}`}
                  className="shrink-0 inline-flex items-center gap-1 rounded-soft border border-ok bg-ok/10 px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-ok hover:bg-ok hover:text-bg-deep"
                >
                  <Activity className="h-3.5 w-3.5" /> Execute
                </button>
              </div>
              <div className="grid grid-cols-3 gap-3 border-t border-line pt-3 text-[11px]">
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">Runs</p>
                  <p className="font-semibold text-ink">{a.run_count}</p>
                </div>
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">Success</p>
                  <p className={`font-semibold flex items-center gap-1 ${healthy ? "text-ok" : "text-warn"}`}>
                    {healthy ? <CheckCircle className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                    {successRate}%
                  </p>
                </div>
                <div>
                  <p className="text-ink-faint uppercase tracking-widest">Cycle</p>
                  <p className="font-semibold text-ink">{a.cycle_interval_min}m</p>
                </div>
              </div>
              <div className="mt-3 text-[10px] text-ink-faint">model: <span className="font-mono">{a.model}</span></div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
