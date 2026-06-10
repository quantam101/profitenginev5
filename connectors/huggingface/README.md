# Hugging Face Connector

## Role In ProfitEngine

Hugging Face is an optional runtime and distribution layer for the Content Factory. It can support model-backed generation for:

- Video concepts and scripts
- Image prompt packs
- Voiceover scripts
- Embeddings and semantic clustering
- Spaces demos
- Local/open model selection

## Default Boundary

The connector is disabled by default. ProfitEngine must continue working through deterministic local generation when Hugging Face is unavailable, disconnected, rate-limited, or not approved.

## Token Handling

Use an environment variable only:

```bash
export HF_TOKEN="..."
```

Never commit tokens, API keys, session cookies, private model credentials, or generated private datasets to the repository.

## Approval Gates

Approval is required before:

- Any external Hugging Face inference call
- Any paid or quota-consuming call
- Any model upload
- Any dataset upload
- Any Space deployment
- Any public publishing action

## Content Factory Flow

1. Campaign payload enters `campaigns/`.
2. Deterministic generator writes local owned assets.
3. Hugging Face enhancer may propose optional model-backed improvements only after approval.
4. All outputs are written to files first.
5. Publishing remains blocked until approval is recorded.

## Fallback

Fallback is mandatory. If Hugging Face is unavailable, ProfitEngine must still generate:

- Book chapter
- Blog post
- Video script
- Social variants
- Email/newsletter copy
- Micro-class outline
- Manifest

The fallback generator is:

```bash
python scripts/content_factory_run.py --campaign campaigns/referrals/acorns-2026-06-09.json --output generated-content
```
