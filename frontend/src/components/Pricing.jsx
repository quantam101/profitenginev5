import React from "react";
import { Check, Zap } from "lucide-react";

const TIERS = [
  {
    name: "Hobby",
    price: "$0",
    cadence: "open source",
    features: [
      "Unlimited local CLI runs",
      "Python + JS/TS merge",
      "AST quality scoring",
      "GitHub Action template",
    ],
    cta: "pip install profitengine",
    href: "https://github.com/quantam101",
    accent: false,
  },
  {
    name: "Pro",
    price: "$29",
    cadence: "/ dev / month",
    features: [
      "Everything in Hobby",
      "Hosted playground & API",
      "Pull-request bot for repos",
      "Custom scoring weights",
      "Priority discord support",
    ],
    cta: "Join waitlist",
    href: "#waitlist",
    accent: true,
    tag: "Most popular",
  },
  {
    name: "Enterprise",
    price: "Custom",
    cadence: "annual",
    features: [
      "Self-hosted on your VPC",
      "SSO + audit log",
      "Bulk repo migrations",
      "Compliance review pipeline",
      "Dedicated engineer slot",
    ],
    cta: "Talk to founder",
    href: "#waitlist",
    accent: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="border-b border-line py-24 md:py-32" data-testid="pricing-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-12 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// pricing</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              Free to run.<br />
              Pay when it ships.
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            The CLI is open source forever. Paid tiers add hosted infra, PR automation and
            enterprise controls.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`relative flex flex-col p-8 transition-colors ${
                tier.accent ? "bg-bg-elev shadow-glowSm" : "bg-bg-surface hover:bg-bg-elev"
              }`}
              data-testid={`tier-${tier.name.toLowerCase()}`}
            >
              {tier.tag && (
                <span className="absolute -top-3 left-8 inline-flex items-center gap-1 border border-acid bg-acid px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-black">
                  <Zap className="h-3 w-3" strokeWidth={2.5} /> {tier.tag}
                </span>
              )}
              <h3 className="font-display text-2xl tracking-tighter">{tier.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="font-display text-4xl tracking-tighter text-acid">{tier.price}</span>
                <span className="text-xs text-ink-muted">{tier.cadence}</span>
              </div>
              <ul className="mt-8 flex-1 space-y-3 text-sm">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-ink-muted">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-acid" strokeWidth={2} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <a
                href={tier.href}
                className={`mt-8 inline-flex items-center justify-center border px-5 py-3 text-xs font-bold uppercase tracking-widest transition-colors ${
                  tier.accent
                    ? "border-acid bg-acid text-black shadow-glowSm hover:bg-acid-soft"
                    : "border-line bg-transparent text-ink hover:border-acid hover:text-acid"
                }`}
                data-testid={`tier-cta-${tier.name.toLowerCase()}`}
              >
                {tier.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
