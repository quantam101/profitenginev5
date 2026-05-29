import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Activity, Copy, Check } from "lucide-react";

const TYPED = "$ pe v5 cycle run --autonomous";

export default function Hero() {
  const [typed, setTyped] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setTyped(TYPED.slice(0, i));
      if (i >= TYPED.length) clearInterval(interval);
    }, 55);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const copy = () => {
    navigator.clipboard.writeText(TYPED.replace("$ ", ""));
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  return (
    <section id="top" className="relative overflow-hidden border-b border-line pt-32 pb-24 md:pt-40 md:pb-32">
      <div className="grid-bg pointer-events-none absolute inset-0 opacity-40" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-ok to-transparent opacity-50" />
      <div className="relative mx-auto grid max-w-7xl items-end gap-16 px-6 md:grid-cols-12 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="md:col-span-7"
        >
          <div className="mb-6 inline-flex items-center gap-2 border border-line bg-bg-panel/60 px-3 py-1 text-[11px] text-ink-muted rounded-soft">
            <span className="h-1.5 w-1.5 animate-pulse bg-ok rounded-full" />
            <span>v5 · CLOSED BETA · 7-AGENT MESH</span>
          </div>
          <h1
            className="font-display text-5xl leading-[0.95] tracking-tighter md:text-7xl"
            data-testid="hero-title"
          >
            Ship an<br />
            <span className="text-ok">autonomous</span><br />
            content business.
          </h1>
          <p className="mt-6 max-w-xl text-sm leading-relaxed text-ink-muted md:text-base">
            ProfitEngine v5 runs a 24/7 mesh of <span className="text-ok">one Sovereign orchestrator</span> + six AI specialists —
            Scout, Content, Video, Social, Revenue and Guard — that find niches, produce assets, distribute, monetize and stay
            compliant. You approve the moves. The engine ships them.
          </p>

          <div
            className="mt-10 flex w-full max-w-xl items-center gap-3 border border-line bg-bg-panel px-4 py-3 font-mono text-sm"
            data-testid="hero-install"
          >
            <span className="text-ok">{">_"}</span>
            <span className="flex-1 truncate">
              {typed}
              <span className="cursor align-middle" />
            </span>
            <button
              onClick={copy}
              className="text-ink-muted transition-colors hover:text-ok"
              data-testid="hero-copy-install"
              aria-label="Copy command"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 border border-ok bg-ok px-5 py-3 text-xs font-bold uppercase tracking-widest text-black shadow-glow transition-colors hover:bg-ok-soft"
              data-testid="hero-open-dashboard"
            >
              Open command center <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
            </Link>
            <a
              href="#agents"
              className="inline-flex items-center gap-2 border border-line bg-transparent px-5 py-3 text-xs font-bold uppercase tracking-widest text-ink transition-colors hover:border-ok hover:text-ok"
              data-testid="hero-meet-agents"
            >
              Meet the agents <Activity className="h-4 w-4" strokeWidth={2} />
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="md:col-span-5"
        >
          <CyclePanel />
        </motion.div>
      </div>
    </section>
  );
}

function stepTone(state) {
  if (state === "done") return "text-ok";
  if (state === "running") return "animate-pulse text-ok-soft";
  return "text-ink-faint";
}

function CyclePanel() {
  const steps = [
    { name: "scout", state: "done", ms: "412ms" },
    { name: "content", state: "done", ms: "9.8s" },
    { name: "video", state: "running", ms: "—" },
    { name: "social", state: "queued", ms: "—" },
    { name: "revenue", state: "queued", ms: "—" },
    { name: "guard", state: "queued", ms: "—" },
  ];
  return (
    <div className="relative">
      <div className="absolute -inset-4 bg-ok/5 blur-2xl" />
      <div className="relative border border-line bg-bg-panel">
        <div className="flex items-center justify-between border-b border-line px-4 py-2 text-[10px] uppercase tracking-widest text-ink-muted">
          <span>cycle.run · #4017</span>
          <span className="flex items-center gap-2 text-ok">
            <span className="h-1.5 w-1.5 animate-pulse bg-ok" /> live
          </span>
        </div>
        <ul className="divide-y divide-line">
          {steps.map((s, i) => (
            <li key={s.name} className="flex items-center justify-between px-4 py-3 text-xs">
              <div className="flex items-center gap-3">
                <span className="text-ink-faint">0{i + 1}</span>
                <span className="font-mono lowercase">{s.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-ink-faint">{s.ms}</span>
                <span className={stepTone(s.state)}>
                  ● {s.state}
                </span>
              </div>
            </li>
          ))}
        </ul>
        <div className="border-t border-line bg-black/40 px-4 py-2 text-[11px] text-ink-muted">
          <span className="text-ok">guard:</span> waiting on human approval for outbound asset
        </div>
      </div>
    </div>
  );
}
