# Operational Task — Built-In Content Factory

**Created:** 2026-06-09
**Status:** Implemented as repository subsystem
**Scope:** ProfitEngine core content creation architecture

## Objective

Make ProfitEngine capable of creating owned assets from one approved idea or campaign, including books, videos, posts, emails, blogs, and course material.

## Implemented Components

- Content Factory overview: `content-factory/README.md`
- Campaign schema: `content-factory/schemas/campaign.schema.json`
- Built-in pipeline: `content-factory/pipelines/campaign-to-owned-assets.yaml`
- Deterministic generator: `scripts/content_factory_run.py`
- CI tests: `tests/test_content_factory.py`
- NPM scripts: `content:factory`, `test:content-factory`
- Hugging Face connector policy: `connectors/huggingface/runtime-policy.yaml`
- Hugging Face connector docs: `connectors/huggingface/README.md`
- Central agent registry entries: `content-factory`, `hf-asset-enhancer`
- Central connector registry entry: `huggingface_runtime`

## Required Runtime Principle

Local deterministic generation must work without Hugging Face. Hugging Face is optional and disabled by default until approved.

## Acceptance Criteria

- One campaign JSON can produce book, blog, video, social, email, course, and manifest outputs.
- Public posting remains blocked by approval gate.
- Financial/referral content keeps disclosure language.
- External Hugging Face usage is disabled unless approved.
- CI includes content factory tests.
