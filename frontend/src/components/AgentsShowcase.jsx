import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Crown, ShieldCheck, FileText, Briefcase, GraduationCap, Radar, Film,
  Palette, Link as LinkIcon, Stethoscope, DollarSign, Bot, ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { getAgents } from "../lib/api";

const ICONS = {
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

const STATUS_TONE = {
  active: "text-ok",
  online: "text-ok",
  thinking: "text-ok-soft animate-pulse",
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
            <div className="mb-4 text-[11px] uppercase tracking-widest text-ok">// the mesh</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              Eleven specialists.<br />
              <span className="text-ok">One company.</span>
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            Each agent owns one job and shares state through the cycle bus. The result is a small
            staff of expert collaborators, not a single overworked LLM prompt.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((a, i) => {
            const Icon = ICONS[a.id] || Bot;
            return (
              <motion.div
                key={a.id}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.04 }}
                className="group bg-bg-panel p-7 transition-colors hover:bg-bg-elev"
                data-testid={`agent-card-${a.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="inline-flex h-10 w-10 items-center justify-center border border-line bg-bg text-ok transition-colors group-hover:border-ok">
                    <Icon className="h-5 w-5" strokeWidth={1.5} />
                  </div>
                  <span className={`text-[11px] uppercase tracking-widest ${STATUS_TONE[a.status]}`}>
                    ● {a.status}
                  </span>
                </div>
                <h3 className="mt-5 font-display text-xl tracking-tight">{a.name}</h3>
                <div className="mt-1 text-[11px] uppercase tracking-widest text-ink-faint">{a.category || a.type}</div>
                <p className="mt-4 text-sm leading-relaxed text-ink-muted">{a.mission || a.description}</p>
                <div className="mt-5 flex items-center justify-between border-t border-line pt-4 text-[11px] text-ink-muted">
                  <span><span className="text-ok">{Math.round(a.success_rate * 100)}%</span> success</span>
                  <span><span className="text-ok">{a.run_count?.toLocaleString() ?? a.runs_today}</span> runs</span>
                  <span>{a.last_run}</span>
                </div>
              </motion.div>
            );
          })}
        </div>

        <div className="mt-10 flex justify-center">
          <Link
            to="/dashboard/agents"
            className="inline-flex items-center gap-2 border border-line bg-bg-panel px-5 py-3 text-xs font-bold uppercase tracking-widest text-ink transition-colors hover:border-ok hover:text-ok"
            data-testid="agents-open-mesh"
          >
            See the full fleet in the command center <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
