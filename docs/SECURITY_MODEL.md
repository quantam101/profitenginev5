# GMAOS Security Model

## Security posture

GMAOS uses fail-closed controls, least privilege, and explicit approval gates. It does not claim formal government or military certification.

## Rules

- Fail closed.
- Least privilege.
- No raw secrets in frontend or repo.
- No paid adapters enabled by default.
- No risky action without approval.
- Audit every execution.
- Verify before memory commit.
- Back up before production changes.

## Secrets

Use OCI Vault, Bitwarden, GitHub Secrets, or locked server-side environment files.

Never store secrets in:

- frontend bundles
- mobile bundles
- public repositories
- screenshots
- prompts
- ZIP files
- browser local storage

## Approval gates

Approval required for payments, public posting, email sending, production deploy, repo merge, file deletion, secret rotation, account settings, and client outreach.
