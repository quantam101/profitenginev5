# Vercel Active Project Decision

Date: 2026-06-10

## Active production target

- Vercel project: `profitenginev5`
- GitHub repository: `quantam101/profitenginev5`
- Status: active build/deploy target

## Paused legacy target

- Vercel project: `profitengine`
- Likely legacy repository lineage: `quantam101/profitengine-v4`
- Status: Git auto-deploy disconnected/paused in Vercel dashboard

## Operating rule

Only `profitenginev5` should create Vercel deployment checks for this repository going forward. Legacy projects must remain disconnected from Git auto-deploy unless explicitly reactivated after review.

## Rationale

`profitenginev5` is the current Next.js/TypeScript production candidate with CI gates, content factory, autopublish gate, gateway tests, opportunity intelligence, and security scanning. `profitengine`/`profitengine-v4` is retained only as a rollback/archive reference.
