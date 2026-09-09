# ProfitEngine AI Newsletter Business

This module turns the Sep. 6, 2026 newsletter playbook into an operating system inside ProfitEngine v5.

## Business objective

Build an owned audience that converts Already Here LLC operating knowledge into recurring, attributable revenue through:

1. free practical issues,
2. service conversion,
3. relevant affiliate offers,
4. sponsor inventory after engagement proof,
5. premium implementation assets after demand is proven.

The system does not count opens or clicks as revenue. The revenue chain is:

`subscriber source -> issue -> CTA -> lead -> qualified opportunity -> quote -> booking -> fulfillment -> invoice -> contractual due date -> actual settlement -> variance`

## Routes

- `/newsletter` — public opt-in landing page.
- `/newsletter/30-day-checklist` — lead magnet / execution checklist.
- `/newsletter/admin` — authenticated operations dashboard.
- `POST /api/newsletter/subscribe` — durable subscriber capture + confirmation workflow.
- `GET /api/newsletter/confirm?token=...` — double-opt-in confirmation.
- `GET /api/newsletter/unsubscribe?token=...` — unsubscribe.
- `GET/POST /api/newsletter/issues` — public published-issue list / authenticated issue creation.
- `POST /api/newsletter/generate` — authenticated AI editorial generation through ProfitEngine AI Gateway.
- `GET /api/newsletter/metrics` — authenticated subscriber/issue/delivery metrics.
- `POST /api/newsletter/publish` — authenticated, explicit approval-gated newsletter delivery.

## Required production configuration

Subscriber persistence uses the existing ProfitEngine MongoDB connection:

- `MONGODB_URI`
- `MONGODB_DB=profitengine`

Newsletter delivery uses Resend's REST API:

- `NEWSLETTER_BUSINESS_ENABLED=true`
- `RESEND_API_KEY` — server-side secret only.
- `NEWSLETTER_FROM_EMAIL` — verified sender, recommended value after domain verification: `ProfitEngine AI <newsletter@alreadyherellc.com>`.
- `NEWSLETTER_REPLY_TO=dispatch@alreadyherellc.com`
- `NEXT_PUBLIC_SITE_URL=https://app.alreadyherellc.com`

Do not commit real secrets.

## First issue

The inaugural article is stored at:

`data/newsletter/issue-001.json`

It is deliberately seeded as `ready`, not automatically published.

Seed it into MongoDB:

```bash
npm run newsletter:seed
```

## AI editorial workflow

The newsletter reuses the existing audited AI Gateway. It does not require a separate AI provider.

Example authenticated request:

```json
POST /api/newsletter/generate
{
  "mode": "ideas",
  "brief": "Prioritize Phoenix service-business automation, dispatch, recurring revenue, and proof-of-work."
}
```

Supported modes:

- `ideas`
- `draft`
- `subject_lines`

AI output is a draft only. It does not publish or send.

## Publishing gate

The issue must be in `ready` state. The operator must be authenticated. The request must contain the literal confirmation value:

```json
POST /api/newsletter/publish
{
  "slug": "how-to-build-a-newsletter-business-with-ai-in-under-30-days",
  "confirm": "PUBLISH"
}
```

The publisher sends in Resend batches of up to 100 recipients and uses idempotency keys to reduce duplicate-send risk. A partial batch failure does not mark the issue published.

## Subscriber safety and compliance

- Subscriber capture requires explicit consent.
- Email addresses are normalized before storage.
- Confirmation tokens expire after 24 hours.
- Subscriber state supports `pending`, `active`, and `unsubscribed`.
- Every delivered issue includes an unsubscribe link.
- Purchased lists and scraped private contacts are outside this workflow.
- Notification delivery is not the system of record; MongoDB persistence happens first.

## 30-day operating cadence

### Week 1 — Position and capture

Launch `/newsletter`, seed issue #1, verify MongoDB persistence, configure the sender domain, and run a controlled signup test.

### Week 2 — Content factory

Use `/api/newsletter/generate` to create a 30-day editorial queue. Keep at least two approved issues ahead of schedule.

### Week 3 — Distribution and monetization

Publish on a predictable cadence. Use one attributable CTA per issue. Route high-intent readers toward Already Here LLC implementation services first; add affiliate or sponsor inventory only where editorial fit is strong.

### Week 4 — Optimize

Review active subscribers, confirmation rate, delivery failures, issue engagement, attributable leads, booked work, invoices, and actual settlement. Remove content that gets attention without useful action.

## Initial monetization model

The newsletter itself stays free initially. Revenue is generated from attributable downstream actions.

Recommended first offer:

**Newsletter + AI Content System implementation for service businesses**

- Standard implementation: `$799 setup + $299/month`.
- Lower-friction pilot: `$299 setup + $199/month + $25 per attributable qualified lead`.
- Larger CRM/dispatch/content integrations: `$1,500-$2,500 setup + $499-$799/month`.

This matches the same system we are proving internally, making the newsletter both a lead channel and proof-of-work asset.

## Production acceptance tests

Do not call the system live until these pass:

1. `/newsletter` returns 200 on desktop and mobile.
2. A test subscription creates a MongoDB subscriber record before any email-provider result.
3. Duplicate signups do not create duplicate subscriber records.
4. Confirmation email delivers from the verified Already Here LLC domain.
5. Confirmation activates the subscriber.
6. Unsubscribe changes status and prevents later delivery.
7. Issue #1 seeds as `ready`.
8. AI generation returns an audited result without publishing.
9. Publishing refuses unauthenticated requests.
10. Publishing refuses requests without `confirm=PUBLISH`.
11. A controlled one-recipient issue sends once and remains idempotent on immediate retry.
12. A deliberately invalid delivery configuration leaves captured subscribers intact.
13. Metrics reflect subscriber state and send failures.
14. Sitemap includes `/newsletter` and `/newsletter/30-day-checklist`.
15. `npm run lint`, `npm run typecheck`, `npm run test:newsletter`, and `npm run build` pass.

## Next integration after launch

After the first real issues produce data, connect newsletter CTA events to Revenue OS opportunities so each campaign can be reconciled against booked and settled revenue rather than email engagement alone.
