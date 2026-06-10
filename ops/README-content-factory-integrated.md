# Content Factory Integration Summary

ProfitEngine now includes a built-in Content Factory subsystem.

## Built In

- Campaign schema
- Campaign-to-owned-assets pipeline
- Deterministic generator
- NPM script entrypoint
- Pytest coverage
- Agent registry entries
- Connector registry entry
- Hugging Face optional runtime policy
- Generated Acorns campaign asset pack
- Approval records
- Status records
- Agent event logs

## Commands

```bash
npm run content:factory
npm run test:content-factory
npm run ci:all
```

## Current State

Generated content exists in:

```text
generated-content/acorns-referral-2026-06-09/
```

Publishing state is blocked until approval is recorded.

Hugging Face is available as a system adapter but disabled by default.
