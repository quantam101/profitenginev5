import React, { useEffect, useState } from "react";
import { Cpu, Pause, Play } from "lucide-react";
import { getAgents } from "../../lib/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  useEffect(() => {
    getAgents().then(setAgents).catch(() => {});
  }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="agents-page">
      <header className="mb-10">
        <div className="mb-2 text-[11px] uppercase tracking-widest text-acid">// agents</div>
        <h1 className="font-display text-3xl tracking-tighter md:text-4xl">The six-agent mesh.</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Each specialist runs in its own sandbox and communicates through the cycle bus.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-2">
        {agents.map((a) => (
          <article key={a.id} className="bg-bg-surface p-6" data-testid={`agent-row-${a.id}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <div className="inline-flex h-11 w-11 items-center justify-center border border-line bg-bg text-acid">
                  <Cpu className="h-5 w-5" strokeWidth={1.5} />
                </div>
                <div>
                  <h3 className="font-display text-xl tracking-tight">{a.name}</h3>
                  <div className="text-[11px] uppercase tracking-widest text-ink-faint">{a.role}</div>
                </div>
              </div>
              <span
                className={`text-[11px] uppercase tracking-widest ${
                  a.status === "online" ? "text-acid" : a.status === "paused" ? "text-yellow-400" : "text-ink-muted"
                }`}
              >
                ● {a.status}
              </span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-ink-muted">{a.description}</p>
            <div className="mt-5 grid grid-cols-3 gap-px border-t border-line text-center text-[11px]">
              <div className="bg-bg-surface px-3 py-3">
                <div className="font-display text-lg text-acid">{Math.round(a.success_rate * 100)}%</div>
                <div className="mt-1 text-ink-muted">success</div>
              </div>
              <div className="bg-bg-surface px-3 py-3">
                <div className="font-display text-lg text-acid">{a.runs_today}</div>
                <div className="mt-1 text-ink-muted">runs / 24h</div>
              </div>
              <div className="bg-bg-surface px-3 py-3">
                <div className="font-display text-lg text-acid">{a.last_run}</div>
                <div className="mt-1 text-ink-muted">last run</div>
              </div>
            </div>
            <div className="mt-5 flex gap-3">
              <button
                className="inline-flex items-center gap-1 border border-line bg-bg-surface px-3 py-2 text-[10px] uppercase tracking-widest text-ink-muted transition-colors hover:border-acid hover:text-acid"
                data-testid={`agent-toggle-${a.id}`}
              >
                {a.status === "paused" ? (
                  <><Play className="h-3 w-3" /> resume</>
                ) : (
                  <><Pause className="h-3 w-3" /> pause</>
                )}
              </button>
              <button
                className="inline-flex items-center gap-1 border border-line bg-bg-surface px-3 py-2 text-[10px] uppercase tracking-widest text-ink-muted transition-colors hover:border-acid hover:text-acid"
                data-testid={`agent-logs-${a.id}`}
              >
                view logs
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
