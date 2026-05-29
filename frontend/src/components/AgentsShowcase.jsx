import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Radar, Pencil, Film, Megaphone, DollarSign, ShieldCheck, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { getAgents } from "../lib/api";

const ICONS = { scout: Radar, content: Pencil, video: Film, social: Megaphone, revenue: DollarSign, guard: ShieldCheck };

const STATUS_TONE = {
  online: "text-acid",
  thinking: "text-acid-soft animate-pulse",
  paused: "text-yellow-400",
  offline: "text-ink-faint",
};

export default function AgentsShowcase() {
  const [agents, setAgents] = useState([]);
  useEffect(() => {
    getAgents().then(setAgents).catch(() => setAgents([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section id="agents" className="border-b border-line py-24 md:py-32" data-testid="agents-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-16 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// the mesh</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              Six specialists.<br />
              <span className="text-acid">One company.</span>
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            Each agent owns one job and shares state through the cycle bus. The result is a small
            staff of expert collaborators, not a single overworked LLM prompt.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((a, i) => {
            const Icon = ICONS[a.id] || Radar;
            return (
              <motion.div
                key={a.id}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.04 }}
                className="group bg-bg-surface p-7 transition-colors hover:bg-bg-elev"
                data-testid={`agent-card-${a.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="inline-flex h-10 w-10 items-center justify-center border border-line bg-bg text-acid transition-colors group-hover:border-acid">
                    <Icon className="h-5 w-5" strokeWidth={1.5} />
                  </div>
                  <span className={`text-[11px] uppercase tracking-widest ${STATUS_TONE[a.status]}`}>
                    ● {a.status}
                  </span>
                </div>
                <h3 className="mt-5 font-display text-xl tracking-tight">{a.name}</h3>
                <div className="mt-1 text-[11px] uppercase tracking-widest text-ink-faint">{a.role}</div>
                <p className="mt-4 text-sm leading-relaxed text-ink-muted">{a.description}</p>
                <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-[11px] text-ink-muted">
                  <span>
                    <span className="text-acid">{Math.round(a.success_rate * 100)}%</span> success
                  </span>
                  <span>
                    <span className="text-acid">{a.runs_today}</span> runs today
                  </span>
                  <span>{a.last_run}</span>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-10 flex justify-center">
          <Link
            to="/dashboard/agents"
            className="inline-flex items-center gap-2 border border-line bg-bg-surface px-5 py-3 text-xs font-bold uppercase tracking-widest text-ink transition-colors hover:border-acid hover:text-acid"
            data-testid="agents-open-mesh"
          >
            See the full mesh in the command center <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
