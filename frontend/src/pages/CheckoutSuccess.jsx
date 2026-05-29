import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, Loader2, AlertCircle, Sparkles } from "lucide-react";
import { checkoutStatus } from "../lib/api";
import { logger } from "../lib/logger";

const POLL_MS = 2000;
const MAX_ATTEMPTS = 8;

function LoadingView({ attempts, max }) {
  return (
    <>
      <Loader2 className="mx-auto h-10 w-10 animate-spin text-ok" />
      <h1 className="mt-6 font-display text-2xl">Confirming with Stripe…</h1>
      {attempts > 0 && (
        <p className="mt-2 text-sm text-ink-muted">attempt {attempts}/{max}</p>
      )}
    </>
  );
}

function PaidView({ info }) {
  return (
    <>
      <CheckCircle2 className="mx-auto h-12 w-12 text-ok" />
      <h1 className="mt-6 font-display text-3xl">You're in.</h1>
      <p className="mt-3 text-sm text-ink-muted">
        Welcome to ProfitEngine v5. Your Studio workspace is provisioning.
        You'll receive onboarding within 24h.
      </p>
      <div className="mt-6 inline-flex items-center gap-2 border border-ok/40 bg-ok/5 px-4 py-2 text-[11px] uppercase tracking-widest text-ok">
        <Sparkles className="h-3.5 w-3.5" />
        ${info?.amount_total ? (info.amount_total / 100).toFixed(2) : "—"} {info?.currency?.toUpperCase()}
      </div>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link
          to="/dashboard"
          className="border border-ok bg-ok px-5 py-2 text-[11px] font-bold uppercase tracking-widest text-black shadow-glow hover:bg-ok-soft"
          data-testid="success-dashboard"
        >
          open command center →
        </Link>
        <Link
          to="/"
          className="border border-line bg-transparent px-5 py-2 text-[11px] font-bold uppercase tracking-widest text-ink hover:border-ok hover:text-ok"
          data-testid="success-home"
        >
          back to launch
        </Link>
      </div>
    </>
  );
}

const FAILURE_MESSAGE = {
  expired: "Your checkout session expired. Please try again.",
  timeout: "Still processing — check your email or try again in a moment.",
  error: "Network error while checking with Stripe.",
  missing: "Open the pricing page to start a new checkout.",
};

function FailureView({ kind }) {
  const title = kind === "missing" ? "No session." : "Couldn't confirm payment.";
  return (
    <>
      <AlertCircle className="mx-auto h-10 w-10 text-warn" />
      <h1 className="mt-6 font-display text-2xl">{title}</h1>
      <p className="mt-3 text-sm text-ink-muted">{FAILURE_MESSAGE[kind]}</p>
      <Link
        to="/#pricing"
        className="mt-6 inline-flex items-center justify-center border border-line bg-bg-panel px-5 py-2 text-[11px] font-bold uppercase tracking-widest text-ink hover:border-ok hover:text-ok"
        data-testid="success-retry"
      >
        retry checkout
      </Link>
    </>
  );
}

function useCheckoutPolling(sessionId) {
  const [state, setState] = useState({ status: "loading", attempts: 0 });

  useEffect(() => {
    if (!sessionId) {
      setState({ status: "missing" });
      return;
    }
    let cancelled = false;
    let attempt = 0;
    const poll = async () => {
      if (cancelled) return;
      attempt += 1;
      try {
        const r = await checkoutStatus(sessionId);
        if (cancelled) return;
        if (r.payment_status === "paid") {
          setState({ status: "paid", info: r });
          return;
        }
        if (r.status === "expired") {
          setState({ status: "expired", info: r });
          return;
        }
        if (attempt >= MAX_ATTEMPTS) {
          setState({ status: "timeout", info: r });
          return;
        }
        setState({ status: "pending", attempts: attempt, info: r });
        setTimeout(poll, POLL_MS);
      } catch (e) {
        logger.warn("checkout.poll", e);
        if (attempt >= MAX_ATTEMPTS) {
          setState({ status: "error", err: e?.message || "unknown" });
          return;
        }
        setTimeout(poll, POLL_MS);
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [sessionId]);

  return state;
}

export default function CheckoutSuccess() {
  const [search] = useSearchParams();
  const sessionId = search.get("session_id");
  const state = useCheckoutPolling(sessionId);

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-16" data-testid="checkout-success-page">
      <div className="ent-card w-full max-w-xl p-10 text-center">
        {state.status === "loading" && <LoadingView attempts={0} max={MAX_ATTEMPTS} />}
        {state.status === "pending" && <LoadingView attempts={state.attempts} max={MAX_ATTEMPTS} />}
        {state.status === "paid" && <PaidView info={state.info} />}
        {(state.status === "expired" ||
          state.status === "timeout" ||
          state.status === "missing" ||
          state.status === "error") && <FailureView kind={state.status} />}
      </div>
    </div>
  );
}
