# Security Policy

## Client-side storage policy

The frontend writes ONLY non-sensitive UX state to `localStorage`. Specifically:

| Key | Purpose | Sensitivity |
|-----|---------|-------------|
| `pev5.ref` | Referral code captured from `?ref=<code>` URL parameter | **Public** — already in the URL, marketing attribution only |
| `pev5.quickstart.seen` | UX preference: user dismissed onboarding modal | **None** — boolean preference |

The following are **never** stored in `localStorage` or `sessionStorage`:
- Authentication tokens (JWT, session IDs, refresh tokens)
- Stripe customer IDs, payment method IDs, or any payment data
- Personal information (email, name, address)
- API keys (publishable or secret)
- Subscription / entitlement state (always re-fetched from `/api/subscriptions/me` server-side)

If/when authentication is added, session tokens will go in **httpOnly cookies**
set by the backend with `Secure` and `SameSite=Strict` — inaccessible to JS,
therefore immune to XSS exfiltration.

## Server secrets

Never commit:
- `backend/.env` (Mongo URL, Stripe secret key, Anthropic key, Gemini key, Emergent LLM key)
- Any file matching `*.env`, `*.key`, `*.pem`

`frontend/scripts/check-env.js` blocks builds if any server-only secret is
detected in `frontend/.env`.

## Stripe

- Backend uses `STRIPE_API_KEY` (`sk_*`). Auto-routes real Stripe keys through
  the native SDK and the Emergent magic key (`sk_test_emergent`) through the
  Emergent transport.
- Webhook signatures verified via `STRIPE_WEBHOOK_SECRET` when using the
  native transport.
- Frontend never sees the secret key. If Stripe Elements are added later,
  `REACT_APP_STRIPE_PUBLISHABLE_KEY` (`pk_*`) will be safe to ship in the
  bundle — that's what publishable keys are for.

## LLM providers

- `EMERGENT_LLM_KEY` works only inside the Emergent pod.
- `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` (direct provider keys) work everywhere.
- The Distiller auto-detects which key set is present (`llm_provider.py`).

## Reporting a vulnerability

Email security@yourdomain.com. We respond within 48h.
