import React, { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { joinWaitlist } from "../lib/api";

export default function Waitlist() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("");
  const [useCase, setUseCase] = useState("");
  const [position, setPosition] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      const data = await joinWaitlist({
        email: email.trim(),
        role: role || null,
        use_case: useCase || null,
      });
      setPosition(data.position);
      toast.success(`You're #${data.position} on the v5 launchlist.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed to join — check your email.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="waitlist" className="border-b border-line py-24 md:py-32" data-testid="waitlist-section">
      <div className="mx-auto max-w-4xl px-6 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="border border-line bg-bg-surface p-10 md:p-16"
        >
          <div className="mb-3 text-[11px] uppercase tracking-widest text-acid">// closed beta</div>
          <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
            Run the v5 stack.<br />
            <span className="text-acid">Ship a business.</span>
          </h2>
          <p className="mt-4 max-w-xl text-sm text-ink-muted">
            We're onboarding operators one cohort at a time. Drop your email + the use case you want
            the engine to run — we'll route invites in order.
          </p>

          {position !== null ? (
            <div
              className="mt-10 flex items-center gap-4 border border-acid bg-bg p-6 shadow-glowSm"
              data-testid="waitlist-success"
            >
              <CheckCircle2 className="h-8 w-8 text-acid" strokeWidth={1.5} />
              <div>
                <div className="font-display text-2xl text-acid">#{position}</div>
                <div className="text-xs text-ink-muted">
                  You're on the v5 launchlist. Watch {email} for your invite + onboarding doc.
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={submit} className="mt-10 grid gap-5 md:grid-cols-2" data-testid="waitlist-form">
              <div className="md:col-span-2">
                <label className="mb-2 block text-[11px] uppercase tracking-widest text-ink-muted">&gt; email</label>
                <div className="flex items-center border-b border-line focus-within:border-acid">
                  <Mail className="h-4 w-4 text-ink-faint" strokeWidth={1.5} />
                  <input
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@yourdomain.dev"
                    className="w-full bg-transparent px-3 py-3 text-sm outline-none placeholder:text-ink-faint"
                    data-testid="waitlist-email-input"
                  />
                </div>
              </div>
              <div>
                <label className="mb-2 block text-[11px] uppercase tracking-widest text-ink-muted">&gt; role (optional)</label>
                <input
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="indie operator, agency, fund..."
                  className="w-full border-b border-line bg-transparent px-3 py-3 text-sm outline-none placeholder:text-ink-faint focus:border-acid"
                  data-testid="waitlist-role-input"
                />
              </div>
              <div>
                <label className="mb-2 block text-[11px] uppercase tracking-widest text-ink-muted">&gt; use case (optional)</label>
                <input
                  value={useCase}
                  onChange={(e) => setUseCase(e.target.value)}
                  placeholder="newsletter, affiliate stack, micro-SaaS..."
                  className="w-full border-b border-line bg-transparent px-3 py-3 text-sm outline-none placeholder:text-ink-faint focus:border-acid"
                  data-testid="waitlist-usecase-input"
                />
              </div>
              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center gap-2 border border-acid bg-acid px-6 py-3 text-xs font-bold uppercase tracking-widest text-black shadow-glow transition-colors hover:bg-acid-soft disabled:opacity-60"
                  data-testid="waitlist-submit"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                  {loading ? "joining..." : "claim my slot →"}
                </button>
              </div>
            </form>
          )}
        </motion.div>
      </div>
    </section>
  );
}
