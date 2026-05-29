import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowRight, GitMerge, Copy, Check } from "lucide-react";

const TYPED = "$ npx profitengine repo ./base ./target -o ./merged";

export default function Hero() {
  const [typed, setTyped] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setTyped(TYPED.slice(0, i));
      if (i >= TYPED.length) clearInterval(interval);
    }, 40);
    return () => clearInterval(interval);
  }, []);

  const copy = () => {
    navigator.clipboard.writeText(TYPED.replace("$ ", ""));
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };

  return (
    <section id="top" className="relative overflow-hidden border-b border-line pt-32 pb-24 md:pt-40 md:pb-32">
      <div className="grid-bg pointer-events-none absolute inset-0 opacity-40" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-acid to-transparent opacity-50" />
      <div className="relative mx-auto grid max-w-7xl items-end gap-16 px-6 md:grid-cols-12 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="md:col-span-7"
        >
          <div className="mb-6 inline-flex items-center gap-2 border border-line bg-bg-surface px-3 py-1 text-[11px] text-ink-muted">
            <span className="h-1.5 w-1.5 animate-pulse bg-acid" />
            <span>v0.1 PUBLIC ALPHA · AST-NATIVE</span>
          </div>
          <h1
            className="font-display text-5xl leading-[0.95] tracking-tighter md:text-7xl"
            data-testid="hero-title"
          >
            Merge the<br />
            <span className="text-acid">best</span> of every<br />
            codebase.
          </h1>
          <p className="mt-6 max-w-xl text-sm leading-relaxed text-ink-muted md:text-base">
            ProfitEngine reads two repos as Abstract Syntax Trees, scores every function on
            robustness, typing and complexity, then auto-upgrades the weaker one — function
            by function. Python &amp; JS/TS. No prompts, no LLM hallucinations.
          </p>

          <div
            className="mt-10 flex w-full max-w-xl items-center gap-3 border border-line bg-bg-surface px-4 py-3 font-mono text-sm"
            data-testid="hero-install"
          >
            <span className="text-acid">{">_"}</span>
            <span className="flex-1 truncate">
              {typed}
              <span className="cursor align-middle" />
            </span>
            <button
              onClick={copy}
              className="text-ink-muted transition-colors hover:text-acid"
              data-testid="hero-copy-install"
              aria-label="Copy command"
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <a
              href="#playground"
              className="inline-flex items-center gap-2 border border-acid bg-acid px-5 py-3 text-xs font-bold uppercase tracking-widest text-black shadow-glow transition-colors hover:bg-acid-soft"
              data-testid="hero-try-playground"
            >
              Try the playground <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
            </a>
            <a
              href="#demo"
              className="inline-flex items-center gap-2 border border-line bg-transparent px-5 py-3 text-xs font-bold uppercase tracking-widest text-ink transition-colors hover:border-acid hover:text-acid"
              data-testid="hero-see-demo"
            >
              See real merge report <GitMerge className="h-4 w-4" strokeWidth={2} />
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="md:col-span-5"
        >
          <CodeRain />
        </motion.div>
      </div>
    </section>
  );
}

function CodeRain() {
  const before = `def parse(data):
    return data`;
  const after = `import json

def parse(data: str) -> dict:
    """Parse a JSON blob safely."""
    try:
        return json.loads(data)
    except Exception:
        return {}`;

  return (
    <div className="relative">
      <div className="absolute -inset-4 bg-acid/5 blur-2xl" />
      <div className="relative border border-line bg-bg-surface">
        <div className="flex items-center justify-between border-b border-line px-4 py-2 text-[10px] uppercase tracking-widest text-ink-muted">
          <span>service.py</span>
          <span className="flex items-center gap-2 text-acid">
            <span className="h-1.5 w-1.5 animate-pulse bg-acid" /> merging
          </span>
        </div>
        <div className="grid grid-cols-2 divide-x divide-line text-[12px] leading-6">
          <pre className="overflow-hidden p-4 text-ink-muted line-through decoration-red-500/60">{before}</pre>
          <pre className="overflow-hidden p-4 text-acid">{after}</pre>
        </div>
        <div className="border-t border-line bg-black/40 px-4 py-2 text-[11px] text-ink-muted">
          <span className="text-acid">↑ score 0.0 → 4.5</span> · +try/except · +docstring · +types
        </div>
      </div>
    </div>
  );
}
