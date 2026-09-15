# Enterprise AI Passive Income Engine

Policy snapshot: 2026-09-14

## Production architecture

ProfitEngineV5 remains the control plane. A bounded Revenue Supervisor ranks and dispatches three lane agents: Technical Product Agent, Stock Asset Agent, and Industry Briefing Agent. AI is used inside defined tasks; deterministic code controls spend, platform policy, publishing, credential handling, evidence, and failure behavior.

The system defaults to zero variable spend and no external writes. External publication is enabled only when the corresponding authorized provider adapter is configured and `PASSIVE_INCOME_EXTERNAL_WRITES=true`. This prevents a model from spending money, accepting terms, leaking credentials, or publishing unsupported claims.

## Agent lanes

### Technical Product Agent

The agent selects a narrow technical problem, produces positioning and SEO metadata, then produces a complete structured source packet with chapter bodies, code files, README, validation checklist, and a source-verification queue. Products remain in the review/compile queue unless an authorized storefront/worker adapter is configured. Gumroad and Payhip are treated as zero-monthly-cost storefronts, not zero-fee storefronts.

### Stock Asset Agent

The agent generates differentiated concepts, compliant prompts, 30-keyword metadata, format guidance, rights checks, and a marketplace routing decision. Adobe Stock is allowed only with generative-AI disclosure, rights checks, quality checks, and final contributor review. AI-generated contributor uploads to Shutterstock are blocked by code.

### Industry Briefing Agent

The scheduler collects RSS/Atom items from configured feeds, strips markup, deduplicates items, and passes the material to the summarization agent as untrusted data. A briefing needs at least two source items before it can become publishable. Beehiiv API creation is enabled only for a configured Max/Enterprise publication and is kept in draft state. Substack remains a reviewed publishing handoff rather than an assumed write API. The existing ProfitEngine newsletter delivery path remains the preferred owned-channel publishing system because it already requires an explicit publish confirmation.

## Supervisor optimization

Lane scoring combines demand, buyer intent, existing proof, reusability, automation, margin, speed to cash, competition, compliance risk, and variable cost. The default portfolio ranks technical micro-products first, the newsletter second, and stock assets third. This deliberately favors early real revenue and owned distribution over slower marketplace royalties.

## Lifelong Catch and Correct

The learning loop records quality, conversion, acceptance, revenue, refund rate, cost, time-to-cash, subscriber growth, and policy rejections. It may recommend prompt/config changes. Source-code optimization must go through tests and a pull request; production runtime code is never autonomously rewritten.

## Runtime configuration

Core controls:

- `REVENUE_OS_ENABLED`: must be `true` for execution.
- `CRON_SECRET`: server-side scheduler authentication secret.
- `PASSIVE_INCOME_ZERO_SPEND`: defaults to `true`.
- `PASSIVE_INCOME_EXTERNAL_WRITES`: defaults to `false`; enable only after provider credentials and policy checks pass.
- `PASSIVE_INCOME_MIN_QUALITY_SCORE`: defaults to `82`.
- `PASSIVE_INCOME_MIN_PROFIT_SCORE`: defaults to `68`.
- `PASSIVE_INCOME_TIMEZONE`: defaults to `America/Phoenix`.
- `PASSIVE_INCOME_RSS_FEEDS`: comma-separated, operator-approved RSS or Atom source URLs.
- `PASSIVE_INCOME_NEWSLETTER_NICHE`: publication positioning used by the briefing agent.

Optional authorized adapters:

- `PASSIVE_INCOME_WORKER_WEBHOOK_URL`
- `PASSIVE_INCOME_WORKER_TOKEN`
- `PASSIVE_INCOME_STOREFRONT_WEBHOOK_URL`
- `PASSIVE_INCOME_ANALYTICS_WEBHOOK_URL`
- `BEEHIIV_PLAN`: only `max` or `enterprise` is treated as create-post API eligible.
- `BEEHIIV_API_KEY`
- `BEEHIIV_PUBLICATION_ID`

AI credentials remain server-side through the existing ProfitEngine AI Gateway. Provider API keys must never be embedded in browser code, Git history, static bundles, downloadable artifacts, or client-visible configuration.

## Schedule

Vercel Cron calls `/api/revenue-os/passive-income/cron` daily at `12:05 UTC`, which is `05:05 America/Phoenix` year-round. Daily cycles can create technical-product and stock-asset work. The newsletter lane is limited to its configured weekly cadence. `CRON_SECRET` authenticates the scheduled route.

## Fail-closed behaviors

- Unknown marketplaces: blocked.
- Shutterstock plus AI-generated contributor asset: blocked.
- Adobe Stock without AI disclosure, adequate quality, or IP clearance: review-blocked.
- Newsletter with fewer than two source items: blocked from publishing.
- External writes without explicit enablement: review queue.
- Beehiiv without eligible plan and credentials: reviewed handoff.
- Paid AI cost under zero-spend mode: cycle marked non-compliant.
- Runtime source-code self-modification: blocked.
- No publication or revenue event is reported as completed without provider/tool proof.
