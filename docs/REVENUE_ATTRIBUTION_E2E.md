# End-to-End Revenue Attribution

Canonical transaction chain:

`lead_id -> booking_id -> payment_id -> revenue_event_id`

The implementation is intentionally idempotent. A collected payment is unique by `(provider, paymentId)`, so provider retries cannot create duplicate revenue rows.

## Endpoints

- `POST /api/revenue/lead` — persists a lead, assigns an immutable `leadId`, sends a Resend notification with Formspree fallback, and sends the GA4 `generate_lead` event.
- `POST /api/checkout` — creates a Stripe Checkout Session and propagates `lead_id` and `booking_id` into Checkout Session and PaymentIntent metadata.
- `POST /api/webhooks/stripe` — verifies Stripe signatures and records paid Checkout sessions exactly once.
- `POST /api/webhooks/square` — verifies Square HMAC signatures and records completed Square payments exactly once.

## Required production environment variables

Set these in Vercel/OCI secrets, never in source control:

```text
MONGODB_URI
MONGODB_DB=profitengine
NEXT_PUBLIC_SITE_URL=https://app.alreadyherellc.com
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-...
GA4_API_SECRET=...
RESEND_API_KEY=...
REVENUE_NOTIFICATION_TO=dispatch@alreadyherellc.com
REVENUE_NOTIFICATION_FROM=Already Here Revenue <leads@your-verified-domain>
FORMSPREE_REVENUE_ENDPOINT=https://formspree.io/f/...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=whsec_...
SQUARE_WEBHOOK_SIGNATURE_KEY=...
SQUARE_WEBHOOK_NOTIFICATION_URL=https://app.alreadyherellc.com/api/webhooks/square
```

`FORMSPREE_REVENUE_ENDPOINT` is optional and is only used when Resend is unavailable or fails.

## Certification procedure

Do not call the chain certified merely because deployment is green. Run one controlled production transaction and retain evidence for every stage:

1. Submit a production form and capture the returned `leadId`.
2. Confirm one `revenue_leads` row exists for that ID.
3. Confirm one notification is delivered by Resend or the Formspree fallback.
4. Confirm GA4 receives one `generate_lead` conversion carrying the same `lead_id`.
5. Create Checkout with the same `leadId`; capture `bookingId` and Stripe Session ID.
6. Complete a controlled payment.
7. Confirm the provider webhook validates successfully.
8. Confirm exactly one `revenue_events` row exists for the provider payment ID.
9. Replay the identical provider webhook and verify `duplicate=true` and no second revenue row is created.
10. Reconcile `lead_id -> booking_id -> payment_id -> revenue_event_id` and collected amount.

Only after all ten steps pass should the chain be marked `CERTIFIED`.
