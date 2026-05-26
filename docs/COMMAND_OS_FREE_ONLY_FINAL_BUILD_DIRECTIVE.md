# Already Here Command OS — Free-Only Final Build Directive

Status: authoritative implementation directive for the next build agent.
Target: `quantam101/profitenginev5` / Already Here Command OS / GMAOS / EAOS / ProfitEngine ecosystem.
Cost target: `$0/month`.
Hosting target: Oracle Cloud Always Free.
Secret target: Bitwarden-compatible server-side vault.

This document consolidates the remaining objectives into one build-ready standard. It is intentionally strict. If a requirement cannot run free, fail closed and provide a manual free fallback.

---

## 1. Absolute Operating Law

Everything in this system must be free to create, run, deploy, schedule, automate, monitor, and maintain unless explicitly approved by the operator.

Hard rules:

- Target monthly operating cost is `$0/month`.
- If a path costs money, block it by default.
- If cost is unknown, block it by default.
- If direct automation requires a paid service, create a free manual export workflow instead.
- Never require a paid API, paid model, paid scheduler, paid database, paid queue, paid analytics tool, paid hosting plan, paid rendering tool, paid social scheduler, paid content platform, or paid automation system for core operation.
- Never require a credit-card-backed trial for core operation.
- No fake credentials, fake deployment state, fake publishing success, fake analytics, fake revenue, or fake ASI/military certification claims.

Allowed default stack:

- Oracle Cloud Always Free VM
- Docker Compose and/or PM2
- SQLite first
- local filesystem media/storage first
- local JSONL append-only audit log
- local job queue or SQLite-backed job queue
- cron/systemd/PM2 scheduled workers
- Caddy or nginx with free TLS certificates
- Bitwarden free or self-hosted Vaultwarden-compatible secret loading
- Ollama/local models when available
- free-tier external APIs only when credentials exist and usage limits are tracked
- PWA for mobile delivery
- FFmpeg/Remotion-compatible local rendering
- GitHub Actions free tier where available
- manual export packs when APIs are unavailable, paid, unaudited, or blocked

---

## 2. Product Objective

Build one governed AI ecosystem and dashboard where every build, creation, update, deployment, agent, workflow, content asset, proof asset, revenue system, and automation module can operate independently while reporting into one shared declarative command system.

The system must function as:

- global enterprise command dashboard
- governed multi-agent operating system
- declarative VHLL execution fabric
- free-only content factory and omni-publisher
- self-healing operational controller
- self-learning correction system
- production-gated build/deployment controller
- revenue/content/proposal/proof dashboard
- Bitwarden-backed secret governance layer
- Oracle Cloud Always Free runtime
- Lifelong Catch and Correct AI side panel
- Codex changelog/patch/task viewer

Use truthful language:

- Use `ASI-aligned` or `Agentic Systems Intelligence` unless literal ASI proof exists.
- Use `military-style hardening` unless formal certification exists.

---

## 3. Builds and Modules to Normalize

Connect and normalize all current finished/unfinished assets:

- ProfitEngine v5 / v5.x
- GMAOS
- EAOS
- TradeGate
- UltraFlow VHLL
- BOS / Business Operating System
- Content generator and poster
- Revenue/content/affiliate/proposal engines
- H&M / RFID proof package
- Website/GitHub health monitor
- Deployment monitor
- Agent registry
- Connector registry
- Distillation engine
- VHLL manifest compiler
- Lifelong Auto-Router
- Lifelong Catch and Correct
- all build folders, zips, scripts, docs, reports, manifests, and patch files

Each build must become a registry record with:

- id
- name
- source repo/folder/file
- status
- production gate score
- dependencies
- agents
- connectors
- deployment target
- health endpoint
- revenue role
- evidence/proof assets
- next action
- cost class
- blocked status when applicable

Drive is archive/proof/artifact storage. GitHub is code source of truth. The dashboard database is the operational source of truth.

---

## 4. Required Dashboard

Create one desktop/mobile-ready dashboard with:

- ecosystem overview
- build registry
- agent registry
- connector registry
- deployment registry
- revenue dashboard
- proposal/federal opportunity dashboard
- content automation dashboard
- CapCut-style Content Studio
- omni-publisher scheduler
- TradeGate dashboard
- BOS dashboard
- evidence/proof library
- health/SLO dashboard
- security dashboard
- cost dashboard
- approval queue
- audit log
- changelog viewer
- Codex patch/task viewer
- Lifelong Catch and Correct side panel

The dashboard must expose missing credentials, blocked connectors, paid/unknown-cost paths, failed deploys, failed health checks, and next recommended repair.

---

## 5. Declarative Operating Layer

All system behavior should be controlled through manifests when possible.

Required manifest families:

```text
config/ecosystem.yaml
config/builds/*.yaml
config/agents/*.yaml
config/connectors/*.yaml
config/policies/*.yaml
config/deployments/*.yaml
config/revenue/*.yaml
config/evidence/*.yaml
config/security/*.yaml
config/vhll/*.yaml
config/content/*.yaml
```

Required generated/runtime models:

- builds
- agents
- connectors
- deployments
- approvals
- audit events
- health checks
- revenue items
- content items
- proposals
- proof assets
- correction memory
- changelog entries
- tasks
- incidents
- repair attempts
- runtime events
- scheduled jobs
- publish attempts
- platform analytics

---

## 6. Agent Runtime

Create all agents needed for full automation:

- Sovereign Orchestrator
- Build Registry Agent
- Drive Inventory Agent
- GitHub Health Agent
- Deployment Agent
- Security Agent
- Cost Guard Agent
- Approval Gate Agent
- Revenue Agent
- Content Agent
- SEO Agent
- Social Agent
- Proposal Agent
- Evidence Agent
- TradeGate Agent
- BOS Agent
- VHLL Compiler Agent
- Distillation Agent
- Self-Healing Agent
- Self-Learning Agent
- Verifier Agent
- Rollback Agent
- Lifelong Catch and Correct Agent
- Codex Patch Agent
- Changelog Agent
- Monitoring Agent
- Connector Agent
- Scheduler Agent
- Omni-Publisher Agent
- CapCut/Pippit Handoff Agent

Each agent must define:

- id
- name
- mission
- allowed actions
- forbidden actions
- approval-required actions
- connector permissions
- cost ceiling
- verifier requirement
- audit logging
- health status
- retry behavior
- failure handling
- rollback behavior where applicable

Every agent action must flow through:

```text
Intent -> Policy Broker -> Cost Guard -> Secret Guard -> Approval Gate -> Execution Adapter -> Verifier -> Audit Log -> Memory Update
```

No agent may directly deploy, email, publish, mutate repo, mutate credentials, call paid APIs, or trigger money movement without the broker.

---

## 7. Cost Guard

Implement a Cost Guard Agent that blocks any action that may create cost.

Inspect:

- connector type
- API pricing risk
- hosting risk
- deployment target
- storage usage
- external service usage
- model provider
- email provider
- publishing provider
- cloud resource type
- estimated cost
- approval state

Connector cost classes:

- `free_local`
- `free_external`
- `free_with_limits`
- `manual_free`
- `unknown_cost_blocked`
- `paid_blocked`

Only `free_local`, `free_external`, `free_with_limits` with tracked limits, and `manual_free` may execute automatically.

Never auto-execute `unknown_cost_blocked` or `paid_blocked`.

Dashboard must show:

- current estimated monthly cost
- target monthly cost: `$0`
- all connectors by cost class
- blocked paid actions
- unknown-cost blocked actions
- approved paid exceptions, if any
- OCI free-tier resource usage
- storage usage
- backup size
- model/API usage
- publishing method: direct free API or manual free export
- missing credentials
- setup steps
- approval requirements

---

## 8. Bitwarden / Vaultwarden Secret Model

All secrets must be server-side only and loaded through Bitwarden-compatible secret management.

Allowed:

- Bitwarden free plan when sufficient
- self-hosted Vaultwarden on the same Oracle Cloud Always Free server
- server-side `.env` generated from vault export or CLI

Not allowed:

- hardcoded API keys
- frontend-exposed keys
- fake credentials
- committed real `.env` files
- embedded secrets inside ZIPs
- paid secret-management dependency for core operation

Required secret behavior:

- validate required secrets during startup
- fail closed if missing
- show missing secret name in dashboard
- show connector status `requires_secret`
- show setup instructions
- show manual fallback path
- show cost class
- show approval requirement

Required credential dashboard fields:

- connector name
- required secret names
- present/missing status
- last validation time
- risk level
- approval requirement

---

## 9. Security and Governance

Implement military-style hardening controls without unsupported certification claims.

Required controls:

- zero-trust boundaries
- least privilege permissions
- server-side secret handling
- no raw secrets in repo/frontend/ZIPs
- webhook HMAC or token validation
- rate limiting
- input validation
- output validation
- RBAC
- audit logging
- immutable append-only event log
- approval gates for risky actions
- no-spend policy
- security scan
- secrets scan
- dependency audit
- SBOM generation
- rollback plan
- backup/restore verification
- production readiness scoring
- fail-closed behavior

Risky actions requiring approval by default:

- production deploy
- repo write/merge
- external publishing
- email send
- credential mutation
- account mutation
- payment activation
- financial action
- destructive file/database action
- paid or unknown-cost action

---

## 10. ASI-Aligned Automation

Implement ASI-aligned architecture through:

- multi-agent arbitration
- recursive improvement loops
- verifier loops
- memory compounding
- distillation
- semantic compression
- cost-aware routing
- local-first execution
- self-correction records
- changelog learning
- failure-pattern detection
- Codex patch suggestions
- automatic test generation
- automatic documentation updates
- automatic production gate rechecks

Do not claim literal ASI unless the system can prove it. Label implementation as `ASI-aligned` or `Agentic Systems Intelligence`.

---

## 11. Self-Healing

The system must detect, triage, and repair failures where safe:

- failed CI
- failed deploy
- missing env vars
- stale endpoints
- broken webhooks
- failed health checks
- agent crashes
- missing manifests
- duplicate build records
- broken links
- security scan failures
- dependency drift
- runtime errors
- missing rollback records
- cost-risk drift
- credential expiry
- platform API scope failures

Self-healing must:

- create repair plan
- run safe local fixes automatically
- generate Codex-ready patch tasks
- require approval for production deploy, repo write, credential change, external publish, financial action, or destructive action
- audit every repair attempt

---

## 12. Self-Learning / Lifelong Catch and Correct

Implement a persistent right-side AI panel named `Lifelong Catch and Correct`.

Required functions:

- track failures
- track fixes
- track repeated mistake patterns
- track successful patches
- generate future prevention rules
- maintain correction memory
- maintain Codex changelog
- update agent heuristics
- recommend one concrete improvement per cycle
- surface risks
- never hide uncertainty or failed work

It must learn from:

- CI failures
- deploy failures
- content performance
- blocked publish attempts
- security blocks
- cost blocks
- recurring credential failures
- stale build records
- broken integrations

---

## 13. Production Gates

A build is not production-ready unless required gates pass:

- install passes
- lint passes
- format passes
- typecheck passes
- unit tests pass
- integration tests pass
- security scan passes
- secrets scan passes
- dependency audit passes
- SBOM generated
- build passes
- health endpoint passes
- mobile smoke test passes
- desktop smoke test passes
- SEO metadata present
- sitemap present
- analytics integrated through free/local path
- audit log active
- approval gate active
- no-spend policy active
- cost guard active
- rollback documented
- backup tested
- restore tested
- deployment verified

Display gate status in the dashboard. Do not claim production-ready without gate evidence.

---

## 14. Required Coding Tooling

Include by default:

- ESLint
- Prettier
- TypeScript strict mode
- pytest where Python is used
- security scanner
- secrets scanner
- dependency audit
- SBOM generation
- GitHub Actions CI
- build validation script
- healthcheck script
- auto-format command
- auto-fix command
- Codex-ready issue/patch format
- changelog generator
- repair-plan generator
- zero-cost validation script

---

## 15. Oracle Cloud Always Free Deployment

Required infrastructure behavior:

- OCI Always Free-compatible architecture
- Docker Compose deployment
- PM2 deployment where applicable
- Caddy or nginx reverse proxy with HTTPS
- SQLite-first persistence
- optional self-hosted Postgres only on same free OCI instance
- optional self-hosted Redis only on same free OCI instance; prefer SQLite queue where simpler
- local filesystem backups
- backup rotation within free storage limits
- health checks
- restart scripts
- rollback scripts
- restore scripts
- firewall setup
- zero-spend OCI deployment validation

Bootstrap script must:

- verify Oracle Cloud Always Free-compatible target
- refuse paid OCI resource provisioning
- install only free/open-source dependencies
- install Docker/Compose and/or PM2
- configure firewall
- configure Caddy/nginx HTTPS
- create required directories
- generate `.env` from Bitwarden/Vaultwarden or `.env.example`
- start services
- run health checks
- print dashboard URL
- print cost status
- print missing connector secrets
- print blocked paid connectors
- write bootstrap audit event

Do not execute unpinned remote scripts blindly. Pin commit SHA or verify checksum where possible.

---

## 16. CapCut-Style Content Factory

Implement a complete internal content production system similar to CapCut/Pippit, but free/local-first.

Content flow:

```text
Idea -> Script -> Hook -> Storyboard -> Media -> Edit -> Captions -> Platform Variants -> Schedule -> Publish or Export -> Analytics -> Learn -> Repurpose
```

Required Content Studio features:

- idea bank
- trend scanner
- topic generator
- hook generator
- script generator
- shot list generator
- storyboard generator
- caption/subtitle generator
- hashtag generator
- title generator
- description generator
- thumbnail generator
- blog/social caption generator
- platform-specific copy variants
- asset library
- brand kit
- template library
- video template system
- short-form video generator
- long-form video prep
- image/post generator
- carousel generator
- product/service promo generator
- proposal/capability content generator
- H&M proof-to-content generator
- voiceover script generator
- AI avatar handoff field
- CapCut/Pippit handoff workflow
- FFmpeg/Remotion local render pipeline
- export queue
- schedule queue
- publish queue
- analytics queue
- repurpose queue

CapCut/Pippit behavior:

- optional creative handoff only
- not required for core operation
- no unsupported scraping/ToS-violating automation
- export editable asset packs for manual import
- store project notes, template refs, prompts, edit instructions
- track rendered internally / exported to CapCut / exported to Pippit / manually edited / ready / published / failed / blocked
- if no official free API, connector status is `manual_handoff`

Local video pipeline must support:

- FFmpeg processing
- Remotion-compatible rendering
- subtitle generation
- thumbnail extraction
- aspect-ratio conversion
- local media storage
- SQLite media/content database
- JSONL audit log
- backup/restore

Generate platform variants:

- 9:16 short-form video
- 1:1 square video
- 4:5 social feed video
- 16:9 YouTube video
- vertical thumbnail
- horizontal thumbnail
- captions/subtitles file
- post caption
- title
- hashtags
- description
- call to action
- affiliate/link slot
- proof/source notes
- compliance notes

---

## 17. Omni-Publisher and Scheduler

Create an Omni-Publisher that can publish or prepare content for:

- TikTok
- YouTube
- YouTube Shorts
- Instagram
- Instagram Reels
- Facebook Pages
- Facebook Reels
- LinkedIn
- X/Twitter
- Threads
- Pinterest
- Reddit
- Medium
- Dev.to
- Hashnode
- Substack-ready export
- WordPress-ready export
- website/blog publishing
- Google Business Profile if free API access exists
- email newsletter export
- RSS feed output
- generic webhook destination
- manual upload destination

Each destination must define:

- connector id
- credential requirements
- API support status
- manual fallback status
- supported media types
- max file size
- max duration
- caption length
- hashtag rules
- link rules
- scheduling support
- approval requirement
- cost class
- posting status
- last validation time

Scheduler requirements:

- calendar view
- queue view
- per-platform schedule
- bulk scheduling
- recurring campaigns
- timezone support
- best-time recommendation field
- draft/ready/approved/scheduled/publishing/published/failed/blocked/manual-upload states
- retry policy
- rate-limit handling
- dead-letter queue
- audit log for every schedule and post attempt

Publishing flow:

```text
Intent -> Policy Broker -> Cost Guard -> Secret Guard -> Platform Validator -> Approval Gate -> Publisher Connector -> Verification -> Audit Log -> Analytics Queue -> Lifelong Catch and Correct
```

Publishing must be blocked when:

- credentials missing
- OAuth expired
- API scope missing
- app review incomplete
- platform audit required
- file violates platform limits
- cost risk unknown
- policy risk unknown
- unsupported claims detected
- approval required but missing
- rate limit exceeded
- account disconnected

Manual ready-to-post pack required when direct publishing is blocked:

- video file
- thumbnail
- captions/subtitles
- title
- description
- hashtags
- platform post copy
- schedule date/time
- upload instructions
- compliance notes
- source/proof notes

Do not fake posting success.

---

## 18. Content Status Model

Persistent states:

- idea
- drafted
- scripted
- storyboarded
- assets_ready
- rendered
- captioned
- variant_ready
- pending_review
- approved
- scheduled
- publishing
- published
- failed
- blocked
- manual_upload_required
- archived
- repurpose_candidate

Analytics fields:

- platform
- post URL
- publish time
- title
- hook
- caption
- hashtags
- format
- video duration
- aspect ratio
- views
- likes
- comments
- shares
- saves
- clicks
- watch time where available
- conversion event
- revenue event where available
- failure reason
- improvement recommendation

Learning recommendations:

- make another variant
- repost at better time
- change hook
- shorten video
- rewrite caption
- change thumbnail
- add proof
- convert to blog
- convert to short
- convert to carousel
- convert to email
- create follow-up post

---

## 19. Event Bus

Create a unified event system so all modules operate separately but together.

Required event names:

- build.created
- build.updated
- build.failed
- deploy.started
- deploy.failed
- deploy.succeeded
- agent.started
- agent.failed
- agent.completed
- approval.requested
- approval.granted
- approval.denied
- security.blocked
- cost.blocked
- revenue.created
- content.generated
- content.rendered
- content.scheduled
- content.published
- content.blocked
- proposal.created
- correction.recorded
- repair.generated
- repair.completed
- secret.missing
- connector.blocked
- health.failed
- health.recovered

Every event must include:

- event id
- timestamp
- actor
- module
- entity id
- action
- status
- correlation id
- cost class
- approval id when applicable
- verification result
- error details when applicable

---

## 20. Optional Connectors Disabled by Default

The following must be optional and disabled unless free credentials exist and Cost Guard approves:

- Emergent LLM
- Stripe
- Google OAuth
- YouTube API
- TikTok API
- Meta/Instagram API
- LinkedIn API
- X/Twitter API
- Medium API
- Dev.to API
- Hashnode API
- WordPress API
- any external AI provider
- any payment provider
- any paid scheduler
- any paid analytics provider

Stripe must not be required to boot. Payment pages and checkout may exist only as gated modules disabled until explicitly approved.

---

## 21. No-Placeholder Standard

Do not ship:

- placeholder production paths
- fake dashboard data
- fake publish buttons
- fake analytics
- fake post URLs
- fake scheduling
- fake credentials
- fake deployment success
- fake AI claims
- fake security claims
- hidden TODOs
- mock-only APIs where real integration boundary is required

If a platform cannot be completed without credentials, app review, OAuth scope, or official API access, implement the real boundary, fail closed, mark blocked, and provide a manual free fallback.

---

## 22. Final Deliverables

The completed build must deliver:

- complete source code
- ZIP package
- mobile-ready PWA
- desktop-ready app
- README
- OCI deployment guide
- environment variable guide
- Bitwarden/Vaultwarden guide
- security guide
- agent registry
- connector registry
- build registry
- production gate checklist
- changelog
- Codex patch/task queue
- rollback instructions
- healthcheck commands
- backup/restore commands
- free-tier validation commands
- content factory guide
- scheduler/publisher guide
- full audit/logging implementation

---

## 23. Final Success Criteria

The build is not complete unless:

- dashboard boots without paid services
- health endpoint returns healthy
- system runs on Oracle Cloud Always Free
- SQLite persistence works
- audit log writes
- cost dashboard shows `$0/month` target
- paid connectors are blocked
- unknown-cost connectors are blocked
- Bitwarden/Vaultwarden secret status works
- missing credentials are surfaced
- manual fallback exists for every paid/unavailable API
- build registry loads
- agent registry loads
- connector registry loads
- deployment registry loads
- production gate scoring works
- approval gates work
- no-spend policy works
- security gates work
- scheduler works without paid services
- content factory works
- ready-to-post export packs work
- direct publishing works only where official free API credentials exist
- Lifelong Catch and Correct works
- changelog viewer works
- Codex patch/task queue works
- backup and restore scripts exist
- restart and rollback scripts exist
- mobile layout works
- desktop layout works
- CI passes
- build passes
- no placeholder production logic remains
- all blocked external dependencies are explicit
- every module can operate independently and report into unified command system

Final rule:

```text
If it costs money, block it.
If cost is unknown, block it.
If automation costs money, create a free manual fallback.
Free is not optional.
Zero-cost operation is the default law of the system.
```
