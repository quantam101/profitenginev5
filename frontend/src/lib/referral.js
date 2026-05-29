/**
 * Captures `?ref=<code>` from the URL on first visit, persists to localStorage,
 * and fires a one-shot tracking call to the backend. Idempotent.
 */
import { useEffect } from "react";
import { trackReferral } from "../lib/api";

const KEY = "pev5.ref";

export function getReferralCode() {
  try {
    return localStorage.getItem(KEY) || null;
  } catch {
    return null;
  }
}

export function useReferralCapture() {
  useEffect(() => {
    try {
      const url = new URL(window.location.href);
      const code = url.searchParams.get("ref");
      if (!code) return;
      const existing = localStorage.getItem(KEY);
      if (existing === code) return;
      localStorage.setItem(KEY, code);
      trackReferral(code, window.location.pathname).catch(() => {});
    } catch {
      /* ignore */
    }
  }, []);
}
