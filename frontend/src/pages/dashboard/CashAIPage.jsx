import React, { useEffect, useState, useCallback } from "react";
import { Brain, Zap, Eraser, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader, Metric } from "./_shared";
import {
  getCashLastDecision, getCashAuditTrail, triggerCashCycle, clearCashCache,
  getAgents, subscribeCycle,
} from "../../lib/api";

const RISK_CLASS = {
  low: "border-ok/40 bg-ok/5 text-ok",
  medium: "border-warn/40 bg-warn/5 text-warn",
  high: "border-danger/40 bg-danger/5 text-danger",
};

function RiskPill({ risk }) {
  const c = RISK_CLASS[risk] || RISK_CLASS.low;
  return (
    <span
      className={`inline-flex items-center border px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest ${c}`}
      data-testid={`risk-${risk}`}
    >
      {risk} risk
    </span>
  );
}

function AgentCard({ a }) {
  const dot = a.status === "active" ? "bg-ok" : "bg-warn";
  return (
    <div className="ent-card p-5" data-testid={`cash-agent-${a.id}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="font-display text-base">{a.name}</div>
          <div className="mt-0.5 font-mono text-[11px] text-ink-faint">{a.id}</div>
        </div>
        <span className={`h-2.5 w-2.5 animate-pulse rounded-full ${dot}`} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-[11px] text-ink-muted">
        <div>
          <div className="text-ink-faint uppercase tracking-widest">cycle</div>
          <div className="text-ink">every {a.cycle_interval_min}m</div>
        </div>
        <div>
          <div className="text-ink-faint uppercase tracking-widest">runs · 24h</div>
          <div className="text-ink">{a.runs_today.toLocaleString()}</div>
        </div>
        <div>
          <div className="text-ink-faint uppercase tracking-widest">success</div>
          <div className="text-ok">{Math.round(a.success_rate * 100)}%</div>
        </div>
        <div>
          <div className="text-ink-faint uppercase tracking-widest">last</div>
          <div className="text-ink truncate">{a.last_run}</div>
        </div>
      </div>
    </div>
  );
}

function DecisionRow({ d }) {
  return (
    <li className="ent-card p-5" data-testid={`audit-row-${d.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1">
          <div className="font-display text-base">{d.summary}</div>
          {d.rationale && (
            <p className="mt-1 text-sm leading-relaxed text-ink-muted">{d.rationale}</p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {(d.tags || []).map((t) => (
              <span key={t} className="border border-line bg-bg-elev px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
                {t}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <RiskPill risk={d.risk || "low"} />
          <span className="text-[10px] text-ink-faint">{d.at}</span>
        </div>
      </div>
    </li>
  );
}

export default function CashAIPage() {
  const [decision, setDecision] = useState(null);
  const [trail, setTrail] = useState([]);
  const [agents, setAgents] = useState([]);
  const [busy, setBusy] = useState(null);
  const [liveEvent, setLiveEvent] = useState(null);

  const refresh = useCallback(() => {
    getCashLastDecision().then(setDecision)
      .catch((e) => console.warn("[CashAI] last-decision:", e?.message || e));
    getCashAuditTrail(20).then(setTrail)
      .catch((e) => console.warn("[CashAI] audit-trail:", e?.message || e));
    getAgents().then(setAgents)
      .catch((e) => console.warn("[CashAI] agents:", e?.message || e));
  }, []);

  useEffect(() => {
    refresh();
    const unsubscribe = subscribeCycle((evt) => {
      setLiveEvent(evt);
      refresh();
    });
    return () => unsubscribe && unsubscribe();
  }, [refresh]);

  const onTrigger = async () => {
    setBusy("cycle");
    try {
      const r = await triggerCashCycle();
      toast.success(`Cycle ${r.id} triggered`);
    } catch {
      toast.error("Failed to trigger cycle");
    } finally {
      setBusy(null);
    }
  };

  const onClearCache = async () => {
    setBusy("cache");
    try {
      const r = await clearCashCache();
      toast.success(`Cleared ${r.deleted} cache entries`);
    } catch {
      toast.error("Failed to clear cache");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="px-6 py-10 md:px-10" data-testid="cash-ai-page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          eyebrow="// cash ai"
          title="Cash AI."
          subtitle="Governing intelligence · dispatch authority · immutable audit. The Sovereign chooses the highest-confidence pending decision, every cycle."
        />
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClearCache}
            disabled={busy === "cache"}
            className="inline-flex items-center gap-2 border border-line bg-bg-panel px-4 py-2 text-xs font-bold uppercase tracking-widest text-ink-muted transition-colors hover:border-ok hover:text-ok disabled:opacity-60"
            data-testid="cash-clear-cache"
          >
            {busy === "cache" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eraser className="h-3.5 w-3.5" />}
            Clear AI Cache
          </button>
          <button
            type="button"
            onClick={onTrigger}
            disabled={busy === "cycle"}
            className="inline-flex items-center gap-2 border border-sov bg-sov px-4 py-2 text-xs font-bold uppercase tracking-widest text-white shadow-glow transition-colors hover:bg-sov-soft disabled:opacity-60"
            data-testid="cash-trigger-cycle"
          >
            {busy === "cycle" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
            Trigger Cycle
          </button>
        </div>
      </div>

      {liveEvent && (
        <div className="mt-4 ent-card border-ok/30 bg-ok/5 p-3 text-[11px] uppercase tracking-widest text-ok" data-testid="cash-live-event">
          ● live · {liveEvent.event} · {new Date(liveEvent.at).toLocaleTimeString()}
        </div>
      )}

      {/* Last Cash Decision */}
      {decision && (
        <div className="mt-8 sov-card p-6" data-testid="cash-last-decision">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-sov-soft">
                <Brain className="h-3.5 w-3.5" /> last cash decision
                <span className="text-ink-faint">· {decision.at}</span>
              </div>
              <h2 className="mt-2 font-display text-2xl leading-tight">{decision.summary}</h2>
              {decision.rationale && (
                <p className="mt-2 max-w-3xl text-sm text-ink-muted">{decision.rationale}</p>
              )}
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {(decision.tags || []).map((t) => (
                  <span key={t} className="border border-sov/30 bg-sov/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-sov-soft">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col items-end gap-2">
              <RiskPill risk={decision.risk || "low"} />
              {decision.confidence != null && (
                <span className="text-xs text-ink-muted">conf {Math.round(decision.confidence * 100)}%</span>
              )}
              <span className="badge badge-ok">all ok</span>
            </div>
          </div>
        </div>
      )}

      {/* Fleet metrics */}
      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Metric label="registered agents" value={agents.length} testId="cash-agent-count" />
        <Metric label="active" value={agents.filter((a) => a.status === "active").length} tone="ok" testId="cash-active-count" />
        <Metric label="audit rows" value={trail.length} testId="cash-audit-count" />
        <Metric label="auto-refresh" value="live · ws" tone="sov" testId="cash-refresh" />
      </div>

      {/* Agent Fleet */}
      <h3 className="mt-10 mb-4 text-[11px] uppercase tracking-widest text-ok">// agent fleet</h3>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="cash-fleet-grid">
        {agents.map((a) => <AgentCard key={a.id} a={a} />)}
      </div>

      {/* Decision Audit Trail */}
      <h3 className="mt-10 mb-4 text-[11px] uppercase tracking-widest text-ok">
        ▸ decision audit trail <span className="text-ink-faint">· {trail.length} entries</span>
      </h3>
      <ul className="space-y-3" data-testid="cash-audit-trail">
        {trail.map((d) => <DecisionRow key={d.id} d={d} />)}
      </ul>
    </div>
  );
}
