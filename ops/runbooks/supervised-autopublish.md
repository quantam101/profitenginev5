# Supervised Autopublish Runbook

## Start Date

Supervised autopublishing begins on 2026-06-23 after the 14-day warmup validation period that starts on 2026-06-09.

## Current Mode

From 2026-06-09 through 2026-06-22:

- Generate content assets
- Queue campaign posts
- Create platform variants
- Validate disclosures
- Test connectors
- Confirm channel allowlist
- Keep public publishing off

## Autopublish Mode Beginning 2026-06-23

Beginning 2026-06-23, ProfitEngine may autopublish to allowlisted channels when all required checks pass.

Allowed after warmup:

- Owned website/news posts
- Approved blog platform posts
- Approved social posts
- Approved short-form video captions
- Approved newsletter content to opted-in contacts only

Still blocked:

- Paid ads
- Cold bulk direct messages
- Scraped contact outreach
- Platform rule evasion
- Paid Hugging Face usage without approval
- Model uploads without approval
- Dataset uploads without approval
- Public Hugging Face Space deployment without approval
- Money movement

## Publishing Gate

Before publishing any item, the system must verify:

1. Campaign type is allowed.
2. Channel is allowlisted.
3. Disclosure rules pass.
4. No guaranteed income, investment, or performance claims are present.
5. No cold outreach target is used.
6. Rate limit is respected.
7. Rollback path exists.
8. Audit log event is written.

## Hugging Face Use

Hugging Face is enabled as a governed connector during warmup. It can prepare assets as files now. External inference and supervised enhancement become eligible after the warmup date only when token, quota, and policy checks pass.
