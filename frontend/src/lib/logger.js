/**
 * Environment-aware logger.
 *
 * In development (`process.env.NODE_ENV !== "production"`), forwards to
 * `console.warn` / `console.error` so engineers see diagnostic output.
 *
 * In production, becomes a no-op for warnings (avoids leaking internal
 * details to end users via DevTools console) and routes errors to an
 * external sink if `REACT_APP_ERROR_REPORTING_URL` is set.
 *
 * Replace `console.warn(...)` with `logger.warn(label, err)` everywhere in
 * the client.
 */
const isProd = process.env.NODE_ENV === "production";
const SINK = process.env.REACT_APP_ERROR_REPORTING_URL || null;

function _post(payload) {
  if (!SINK) return;
  try {
    fetch(SINK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* never crash the app on telemetry */
  }
}

export const logger = {
  warn(label, err) {
    if (!isProd) {
      // eslint-disable-next-line no-console
      console.warn(`[${label}]`, err?.message || err);
    }
    // Warnings stay client-side only — no remote spam.
  },

  error(label, err) {
    if (!isProd) {
      // eslint-disable-next-line no-console
      console.error(`[${label}]`, err);
    }
    _post({ level: "error", label, message: err?.message || String(err), at: new Date().toISOString() });
  },
};
