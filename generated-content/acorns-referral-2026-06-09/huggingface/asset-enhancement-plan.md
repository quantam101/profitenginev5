# Hugging Face Enhancement Plan — Acorns Referral Campaign

## Status

Optional. Disabled until approved.

## Purpose

Use Hugging Face only as an enhancement layer after the deterministic Content Factory produces owned assets.

## Candidate Enhancements

- Generate image prompt variants for short-form visuals.
- Generate voiceover variants from the approved video script.
- Generate embedding clusters for reusing the campaign across future financial-habit content.
- Prototype a private/internal Space demo for campaign review after approval.

## Controls

- Do not use Hugging Face unless `huggingface_runtime` is enabled and approved.
- Do not upload private user data.
- Do not upload datasets.
- Do not deploy a public Space without approval.
- Do not make paid inference calls without approval.
- Use local deterministic output as the fallback.

## Source Files

- `campaigns/referrals/acorns-2026-06-09.json`
- `generated-content/acorns-referral-2026-06-09/video/short-form-45s.md`
- `generated-content/acorns-referral-2026-06-09/social/platform-variants.md`
