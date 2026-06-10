# Referral Campaign Intake Runbook

## Purpose

Standardize how ProfitEngine ingests referral campaigns without creating compliance, spam, or trust risk.

## Required Inputs

- Campaign ID
- Referral URL
- Primary post copy
- Short post copy
- Disclosure language
- Allowed channels
- Approval status

## Mandatory Controls

- Manual approval before public publishing
- Referral disclosure retained
- No guaranteed outcome claims
- No personalized financial advice
- No scraped/cold bulk outreach
- Platform rules respected

## Processing Steps

1. Read the campaign payload from `campaigns/referrals/`.
2. Read the human handoff from `content-queue/`.
3. Generate channel-specific variants.
4. Store variants under the campaign record.
5. Wait for approval record update before publishing.
6. Track clicks, signups, and rewards separately.

## Current Intake Example

- `campaigns/referrals/acorns-2026-06-09.json`
