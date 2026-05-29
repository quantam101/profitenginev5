/**
 * Captures `?ref=<code>` from the URL on first visit and persists it to
 * localStorage so subsequent navigation/checkout flows can credit the referrer.
 *
 * SECURITY NOTE: a referral code is a PUBLIC marketing parameter (it's literally
 * already in the URL), not a credential or session token. localStorage is the
 * correct store: no auth bearer, no PII, no XSS-exfil risk because the value
 * is non-sensitive by design. We do NOT use this pattern for auth tokens.
 * See SECURITY.md → "Client-side storage policy" for the full rule set.
 */
import { useEffect } from "react";
import { trackReferral } from "../lib/api";
import { logger } from "./logger";

const KEY = "pev5.ref";

export function getReferralCode() {
  try {
    return localStorage.getItem(KEY) || null;
  } catch (err) {
    logger.warn("referral.read", err);
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
      logger.warn("referral.capture", err);
      return;
    }
    // Fire network call OUTSIDE the storage try/catch so storage errors don't
    // suppress backend tracking.
    trackReferral(code, window.location.pathname)
      .catch((err) => logger.warn("referral.track", err));
  }, []);
}
