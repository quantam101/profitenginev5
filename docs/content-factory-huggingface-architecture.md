# ProfitEngine Built-In Content Factory + Hugging Face Architecture

## Executive Summary

ProfitEngine now treats content production as a core subsystem, not a one-off post writer.

A single campaign payload can become an owned asset package:

- Book chapter
- Blog article
- Short-form video script
- Social post variants
- Email/newsletter copy
- Micro-class/course outline
- Manifest for tracking and approval

Hugging Face is registered as an optional external enhancement layer, disabled by default and blocked behind approval gates.

## Core Principle

The system must work without external APIs.

Local deterministic generation is the baseline. External inference, model uploads, dataset uploads, or Spaces deployments are optional and require explicit approval.

## Primary Flow

```text
campaign JSON
  -> content factory generator
  -> generated owned assets
  -> manifest
  -> approval gate
  -> optional Hugging Face enhancement
  -> channel-specific publishing adapter
```

## Why This Matters

This turns ProfitEngine into a reusable asset factory rather than a social posting bot. Every idea can compound into multiple content surfaces and later become a product, course, lead magnet, or SEO asset.

## Approval Boundary

Generated assets are not automatically public.

Public posting, email sending, Hugging Face inference, Hugging Face uploads, and channel publishing remain blocked until approval is recorded.

## Operational Entry Points

```bash
npm run content:factory
npm run test:content-factory
npm run ci:all
```

## Current Campaign Example

The first queued campaign is:

```text
campaigns/referrals/acorns-2026-06-09.json
```

It routes through:

```text
scripts/content_factory_run.py
```

and outputs into:

```text
generated-content/acorns-referral-2026-06-09/
```
