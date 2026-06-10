# ProfitEngine Content Factory

## Purpose

ProfitEngine must be able to turn one approved source idea or campaign into reusable owned assets:

- Book chapters
- Blog posts
- Short-form video scripts
- Voiceover scripts
- Captions and hashtags
- Email/newsletter copy
- Micro-class/course outlines
- Platform-specific social variants

This module is local-first, zero-spend by default, and approval-gated before any public publishing.

## Operating Model

One source payload becomes many outputs.

`campaign JSON -> deterministic content pack -> approval gate -> channel adapters -> publishing/logging`

## Non-Negotiable Controls

- No paid API calls by default
- No public posting without approval
- No cold bulk messaging
- No scraped contact outreach
- No guaranteed financial outcome claims
- Required disclosure for affiliate/referral/financial content
- Outputs are generated as files first, then reviewed before distribution

## Current Generator

Run from repository root:

```bash
python scripts/content_factory_run.py --campaign campaigns/referrals/acorns-2026-06-09.json --output generated-content
```

Expected output directory:

```text
generated-content/acorns-referral-2026-06-09/
```

Generated assets include:

- `book/chapter-01.md`
- `blog/article.md`
- `video/short-form-45s.md`
- `social/platform-variants.md`
- `email/newsletter.md`
- `course/micro-class-outline.md`
- `manifest.json`

## State Boundary

Generated content does not equal published content. Publishing remains blocked until the approval record is updated and the applicable channel adapter confirms the channel permits the post type and link type.
