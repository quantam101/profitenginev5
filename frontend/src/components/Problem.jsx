import React from "react";
import { motion } from "framer-motion";
import { TriangleAlert, Clock4, Wallet } from "lucide-react";

const items = [
  {
    icon: Clock4,
    stat: "73%",
    title: "of solo operators stall by week 4",
    body: "Writing, editing, posting, monetizing, replying. One human burns out before any flywheel forms.",
  },
  {
    icon: TriangleAlert,
    stat: "1 in 4",
    title: "AI tools ship something that gets flagged",
    body: "DMCA, IP, brand safety, hallucinated stats. The fix isn't more LLM prompts — it's a Guard agent in the loop.",
  },
  {
    icon: Wallet,
    stat: "$0.62",
    title: "average margin per AI-generated post",
    body: "Without orchestration, traffic doesn't compound. Revenue and Scout have to share state with everyone else.",
  },
];

export default function Problem() {
  return (
    <section id="problem" className="border-b border-line py-24 md:py-32" data-testid="problem-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-16 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// the gap</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              AI tools generate.<br />
              <span className="text-acid">Businesses orchestrate.</span>
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            ProfitEngine isn't another writer or scheduler. It's a coordination layer between
            specialist agents — built to run unattended, profitably.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-3">
          {items.map((it, i) => {
            const Icon = it.icon;
            return (
              <motion.div
                key={it.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.06 }}
                className="bg-bg-surface p-8"
                data-testid={`problem-card-${i}`}
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center border border-line bg-bg text-acid">
                  <Icon className="h-5 w-5" strokeWidth={1.5} />
                </div>
                <div className="font-display text-4xl tracking-tighter text-acid">{it.stat}</div>
                <h3 className="mt-2 font-display text-lg tracking-tight">{it.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-muted">{it.body}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
