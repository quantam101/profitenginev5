import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus } from "lucide-react";

const ITEMS = [
  {
    q: "Is ProfitEngine v5 actually autonomous, or does it just generate content?",
    a: "v5 is an orchestration layer. It pipelines six agents through a cycle bus and only ships outputs after Guard reviews them. You can run it fully unattended once you trust the agents — most operators keep approvals on for the first 30 days.",
  },
  {
    q: "How does it differ from already-here-dashboard?",
    a: "already-here-dashboard is the production cockpit we built for a single LLC running this stack. v5 is the open-core engine underneath. We use the AST merger to pull battle-tested functions from already-here back into v5 every release.",
  },
  {
    q: "Do I need to bring my own LLM keys?",
    a: "Yes for Studio and Holding tiers — you wire OpenAI, Anthropic or Gemini and we route through your account. Operator tier ships with the Emergent Universal Key for local-only use.",
  },
  {
    q: "Where does the revenue come from?",
    a: "Revenue agent currently supports affiliate links, digital product checkout (Stripe), display ads and sponsorship slots. Each is a connector you wire once and Revenue routes traffic across them daily.",
  },
  {
    q: "Can I self-host?",
    a: "Yes. Operator and Holding tiers both run on your infra. We publish a docker-compose, a Caddyfile, and Terraform for OCI / DigitalOcean / Fly. The hosted Studio tier is a managed copy of the same stack.",
  },
  {
    q: "What happens if Guard flags something?",
    a: "The asset is held in the approvals queue and you (or a designated reviewer) get a mobile push. Approve, edit or veto in one tap. Nothing leaves the workspace until Guard signs off.",
  },
];

export default function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <section id="faq" className="border-b border-line py-24 md:py-32" data-testid="faq-section">
      <div className="mx-auto max-w-4xl px-6 md:px-10">
        <div className="mb-12">
          <div className="mb-4 text-[11px] uppercase tracking-widest text-ok">// FAQ</div>
          <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
            Questions<br />
            <span className="text-ok">we keep getting.</span>
          </h2>
        </div>
        <ul className="border-t border-line">
          {ITEMS.map((it, i) => {
            const isOpen = open === i;
            return (
              <li key={it.q} className="border-b border-line" data-testid={`faq-${i}`}>
                <button
                  onClick={() => setOpen(isOpen ? -1 : i)}
                  className="flex w-full items-center justify-between gap-6 py-6 text-left transition-colors hover:text-ok"
                  data-testid={`faq-trigger-${i}`}
                >
                  <span className="font-display text-base tracking-tight md:text-lg">{it.q}</span>
                  {isOpen ? (
                    <Minus className="h-5 w-5 shrink-0 text-ok" strokeWidth={2} />
                  ) : (
                    <Plus className="h-5 w-5 shrink-0 text-ink-muted" strokeWidth={2} />
                  )}
                </button>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25 }}
                      className="overflow-hidden"
                    >
                      <p className="pb-6 pr-10 text-sm leading-relaxed text-ink-muted" data-testid={`faq-answer-${i}`}>
                        {it.a}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
