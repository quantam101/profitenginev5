import React from "react";
import { Check, Zap, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";
import { createCheckout } from "../lib/api";
import { getReferralCode } from "../lib/referral";

const TIERS = [
  {
    name: "Operator",
    price: "$0",
    cadence: "open core",
    features: [
      "All 11 agents, local-only",
      "Single project / workspace",
      "Community discord",
      "Self-host on your VPS",
    ],
    cta: "Clone the repo",
    href: "https://github.com/quantam101/profitenginev5",
    accent: false,
  },
  {
    name: "Studio",
    price: "$149",
    cadence: "/ workspace / mo",
    package_id: "studio_monthly",
    features: [
      "Hosted command center",
      "Approvals via mobile push",
      "Up to 5 connected channels",
      "Revenue routing presets",
      "Distillation engine · 80%+ savings",
      "Email + Discord priority",
    ],
    cta: "Start Studio →",
    accent: true,
    tag: "Most popular",
  },
  {
    name: "Holding",
    price: "$2,500",
    cadence: "reservation deposit",
    package_id: "holding_deposit",
    features: [
      "Multi-workspace org",
      "SSO + audit log",
      "Custom Guard policy DSL",
      "White-label brand mode",
      "Dedicated engineer slot",
    ],
    cta: "Reserve Holding →",
    accent: false,
  },
];

export default function Pricing() {
  const [loading, setLoading] = useState(null);
  const onBuy = async (tier) => {
    if (!tier.package_id) {
      if (tier.href) window.open(tier.href, "_blank", "noreferrer");
      return;
    }
    setLoading(tier.package_id);
    try {
      const referral_code = getReferralCode();
      const { url } = await createCheckout({
        package_id: tier.package_id,
        origin_url: window.location.origin,
        referral_code,
      });
      if (!url) throw new Error("no checkout url");
      window.location.href = url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Checkout failed — try again");
      setLoading(null);
    }
  };

  return (
    <section id="pricing" className="border-b border-line py-24 md:py-32" data-testid="pricing-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-12 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-ok">// pricing</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              Run it free.<br />
              Pay when it earns.
            </h2>
          </div>
          <p className="max-w-md text-sm text-ink-muted md:col-span-4">
            The full engine is open core — clone it, run it, hack it. Paid tiers
            add hosted cockpit, mobile approvals and org controls.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line md:grid-cols-3">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`relative flex flex-col p-8 transition-colors ${
                tier.accent ? "bg-bg-elev shadow-glow" : "bg-bg-panel hover:bg-bg-elev"
              }`}
              data-testid={`tier-${tier.name.toLowerCase()}`}
            >
              {tier.tag && (
                <span className="absolute -top-3 left-8 inline-flex items-center gap-1 border border-ok bg-ok px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest text-black">
                  <Zap className="h-3 w-3" strokeWidth={2.5} /> {tier.tag}
                </span>
              )}
              <h3 className="font-display text-2xl tracking-tighter">{tier.name}</h3>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="font-display text-4xl tracking-tighter text-ok">{tier.price}</span>
                <span className="text-xs text-ink-muted">{tier.cadence}</span>
              </div>
              <ul className="mt-8 flex-1 space-y-3 text-sm">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-ink-muted">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-ok" strokeWidth={2} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <button
                type="button"
                onClick={() => onBuy(tier)}
                disabled={loading === tier.package_id}
                className={`mt-8 inline-flex items-center justify-center border px-5 py-3 text-xs font-bold uppercase tracking-widest transition-colors disabled:opacity-60 ${
                  tier.accent
                    ? "border-ok bg-ok text-black shadow-glow hover:bg-ok-soft"
                    : "border-line bg-transparent text-ink hover:border-ok hover:text-ok"
                }`}
                data-testid={`tier-cta-${tier.name.toLowerCase()}`}
              >
                {loading === tier.package_id ? (
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                ) : null}
                {loading === tier.package_id ? "redirecting…" : tier.cta}
              </button>
            </div>
          ))}
        </div>

        <p className="mt-8 text-center text-[11px] text-ink-faint">
          secured by Stripe · test mode · cancel anytime · prices in USD
        </p>
      </div>
    </section>
  );
}
