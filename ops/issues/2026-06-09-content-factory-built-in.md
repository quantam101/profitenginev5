# Issue Mirror — Built-In Content Factory + Hugging Face Adapter

## Title

Build Content Factory into ProfitEngine core with optional Hugging Face enhancement

## Body

ProfitEngine must create reusable owned assets from a single approved campaign payload.

Implemented scope:

- Campaign-to-assets pipeline
- Deterministic local generator
- Book/blog/video/social/email/course outputs
- Campaign schema
- Generated Acorns campaign asset pack
- Hugging Face optional connector policy
- Central agent registry updates
- Central connector registry updates
- NPM scripts and CI test hook
- Approval records and operational status files

Default behavior:

- No public posting
- No cold bulk outreach
- No paid API usage
- No external Hugging Face usage
- No model/dataset/Space uploads
- Approval required before external/public action

Validation target:

```bash
npm run test:content-factory
npm run ci:all
```
