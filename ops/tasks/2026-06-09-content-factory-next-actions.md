# Content Factory Next Actions

## Immediate

1. Run `npm run test:content-factory` locally or in CI.
2. Run `npm run content:factory` to regenerate campaign assets from the campaign JSON.
3. Review generated outputs under `generated-content/acorns-referral-2026-06-09/`.
4. Approve or hold public posting in `ops/approvals/pending/2026-06-09-acorns-referral.md`.

## Hugging Face

Hugging Face is built into the system as an optional adapter but remains disabled by default.

To proceed later, approve the pending record:

`ops/approvals/pending/2026-06-09-content-factory-huggingface.md`

## Hard Boundary

Do not post, email, deploy, infer externally, or upload models/datasets until approval is recorded.
