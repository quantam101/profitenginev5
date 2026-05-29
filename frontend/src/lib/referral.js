/**
 * Captures `?ref=<code>` from the URL on first visit and persists it to
 * localStorage so subsequent navigation/checkout flows can credit the referrer.
 *
 * SECURITY NOTE: a referral code is a PUBLIC marketing parameter (it's literally
 * already in the URL), not a credential or session token. localStorage is the
 * correct store: no auth bearer, no PII, no XSS-exfil risk because the value
 * is non-sensitive by design. We do NOT use this pattern for auth tokens.
 */
import { useEffect } from "react";
import { trackReferral } from "../lib/api";

const KEY = "pev5.ref";

export function getReferralCode() {
  try {
    return localStorage.getItem(KEY) || null;
  } catch (err) {
    console.warn("[referral] localStorage read failed:", err?.message || err);
    return null;
  }
}

export function useReferralCapture() {
  useEffect(() => {
    let code;
    try {
      const url = new URL(window.location.href);
      code = url.searchParams.get("ref");
      if (!code) return;
      const existing = localStorage.getItem(KEY);
      if (existing === code) return;
      localStorage.setItem(KEY, code);
    } catch (err) {
      console.warn("[referral] capture failed:", err?.message || err);
      return;
    }
    // Fire the network call OUTSIDE the storage try/catch so storage errors
    // don't suppress backend tracking.
    trackReferral(code, window.location.pathname)
      .catch((err) => console.warn("[referral] backend track failed:", err?.message || err));
  }, []);
}
