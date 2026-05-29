import React from "react";
import { motion } from "framer-motion";
import { ShieldCheck, Type, GitBranch, Lock, GaugeCircle, Code2 } from "lucide-react";

const items = [
  {
    icon: ShieldCheck,
    title: "Robustness scoring",
    body:
      "Functions with try/except, raise statements and defensive returns score higher. The merger swaps a brittle base block for the hardened version automatically.",
  },
  {
    icon: Type,
    title: "Type & doc coverage",
    body:
      "Each typed argument, return annotation and docstring adds to the completeness score. Type-safe Python and TypeScript implementations outrank untyped twins.",
  },
  {
    icon: GaugeCircle,
    title: "Cyclomatic complexity",
    body:
      "We walk the AST and count decision nodes (if/for/try/case) to penalize spaghetti. Shorter logical paths win — maintainability is a first-class metric.",
  },
  {
    icon: GitBranch,
    title: "Imports follow the function",
    body:
      "When a swapped function depends on a new module, the merger prepends the required import statement — no broken upgrades, no manual cleanup.",
  },
  {
    icon: Code2,
    title: "Python + JS/TS",
    body:
      "Native ast for Python, brace-balanced tokenizer for JS/TS that handles arrow functions, exports and template literals. One CLI, two ecosystems.",
  },
  {
    icon: Lock,
    title: "No LLM, no leaks",
    body:
      "Pure static analysis. Your code never leaves your machine — run it locally as a CLI, in CI, or via this hosted playground.",
  },
];

export default function Features() {
  return (
    <section id="features" className="border-b border-line py-24 md:py-32" data-testid="features-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-16 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-7">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// what it does</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              An opinionated judge<br />for your own code.
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-5">
            ProfitEngine measures every function in both repos against the same rubric — then
            keeps the winner. Predictable, reproducible, diff-friendly.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-2 lg:grid-cols-3">
          {items.map((it, i) => {
            const Icon = it.icon;
            return (
              <motion.div
                key={it.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.05 }}
                className="group relative bg-bg-surface p-8 transition-colors hover:bg-bg-elev"
                data-testid={`feature-card-${i}`}
              >
                <div className="mb-6 inline-flex h-10 w-10 items-center justify-center border border-line bg-bg text-acid transition-colors group-hover:border-acid">
                  <Icon className="h-5 w-5" strokeWidth={1.5} />
                </div>
                <h3 className="font-display text-lg tracking-tight">{it.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-muted">{it.body}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
