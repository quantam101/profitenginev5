import React, { useEffect, useState } from "react";
import { X, ArrowRight, Cpu, Brain, ShieldAlert, Sparkles, Rocket, Check } from "lucide-react";
import { logger } from "../lib/logger";

const STEPS = [
  {
    icon: Cpu,
    title: "Meet your 20-agent fleet",
    body: "The Prime Orchestrator + 19 specialists are already running. Open AI Agents to see live cycle counts and the missions each one owns.",
    cta: { label: "Open Agents", to: "/dashboard/agents" },
  },
  {
    icon: Brain,
    title: "Trigger your first cycle",
    body: "Hit Cash AI → Trigger Cycle. The engine queues work, broadcasts a live WebSocket event, and writes an audit entry. You'll see the event pill light up.",
    cta: { label: "Open Cash AI", to: "/dashboard/cash-ai" },
  },
  {
    icon: ShieldAlert,
    title: "Approve a pending decision",
    body: "The Approval Queue holds high-confidence actions waiting on you. Approving any one persists to Mongo and bumps your audit trail.",
    cta: { label: "Open Approvals", to: "/dashboard/approvals" },
  },
  {
    icon: Sparkles,
    title: "See your token cost evaporate",
    body: "Distillation routes 80%+ of LLM calls through Gemini Flash with SHA-256 caching. Open Distillation to watch the savings counter climb.",
    cta: { label: "Open Distillation", to: "/dashboard/distillation" },
  },
  {
    icon: Rocket,
    title: "Share the launch — make $10k this week",
    body: "Every operator on your referral link tracks back to you. Copy the launch URL, post on X, get attribution credit on every paid signup.",
    cta: { label: "Open Launch", to: "/" },
  },
];

const KEY = "pev5.quickstart.seen";

// NOTE: this is a UX preference flag ("user has dismissed the onboarding modal"),
// NOT a credential. localStorage is the correct store for non-sensitive UX state.
// See SECURITY.md → "Client-side storage policy".
export function shouldAutoOpenQuickstart() {
  try { return !localStorage.getItem(KEY); }
  catch (err) { logger.warn("quickstart.read", err); return false; }
}

export function markQuickstartSeen() {
  try { localStorage.setItem(KEY, "1"); }
  catch (err) { logger.warn("quickstart.write", err); }
}

export default function QuickstartModal({ open, onClose }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (!open) setI(0);
  }, [open]);
  if (!open) return null;
  const step = STEPS[i];
  const Icon = step.icon;
  const last = i === STEPS.length - 1;
  const finish = () => { markQuickstartSeen(); onClose(); };
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 p-6 backdrop-blur"
      role="dialog"
      data-testid="quickstart-modal"
    >
      <div className="ent-card relative w-full max-w-2xl p-8">
        <button
          type="button"
          onClick={finish}
          className="absolute right-4 top-4 text-ink-faint hover:text-ink"
          aria-label="Close quickstart"
          data-testid="quickstart-close"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="mb-6 flex items-center gap-3">
          <Icon className="h-5 w-5 text-ok" strokeWidth={1.75} />
          <span className="text-[11px] uppercase tracking-widest text-ok">
            // quickstart · step {i + 1} of {STEPS.length}
          </span>
        </div>
        <h2 className="font-display text-3xl leading-tight tracking-tighter" data-testid="quickstart-title">
          {step.title}
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-ink-muted" data-testid="quickstart-body">
          {step.body}
        </p>

        <div className="mt-6 flex gap-2">
          {STEPS.map((s, idx) => (
            <span
              key={s.title}
              className={`h-1.5 flex-1 rounded-soft transition-colors ${idx <= i ? "bg-ok" : "bg-line"}`}
            />
          ))}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setI((n) => Math.max(0, n - 1))}
            disabled={i === 0}
            className="text-[11px] uppercase tracking-widest text-ink-muted hover:text-ok disabled:opacity-40"
            data-testid="quickstart-prev"
          >
            ← back
          </button>
          <div className="flex gap-3">
            <a
              href={step.cta.to}
              className="inline-flex items-center gap-2 border border-line bg-bg-panel px-4 py-2 text-[11px] font-bold uppercase tracking-widest text-ink hover:border-ok hover:text-ok"
              data-testid="quickstart-cta"
            >
              {step.cta.label}
            </a>
            <button
              type="button"
              onClick={() => (last ? finish() : setI(i + 1))}
              className="inline-flex items-center gap-2 border border-ok bg-ok px-4 py-2 text-[11px] font-bold uppercase tracking-widest text-black shadow-glow hover:bg-ok-soft"
              data-testid="quickstart-next"
            >
              {last ? <><Check className="h-3.5 w-3.5" /> finish</> : <>next <ArrowRight className="h-3.5 w-3.5" /></>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
