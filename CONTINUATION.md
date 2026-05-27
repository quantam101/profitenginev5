# ProfitEngine v5 — Session Continuation Guide
**Last updated:** 2026-05-27 (Session 3)

---

## ✅ COMPLETED — OCI Deploy + n8n Workflows

### What Was Fixed (Session 2 — 2026-05-26)
OCI GitHub Actions CI/CD pipeline — fully working end-to-end.
- Last successful run: https://github.com/quantam101/profitenginev5/actions/runs/26436815984

### What Was Done (Session 3 — 2026-05-27)

1. **n8n owner account created** → `admin@alreadyherellc.com` / `ProfitEngine2026!`
2. **n8n workflows imported and activated** via `docker compose exec n8n n8n import:workflow` CLI:
   - `ProfitEngine — Daily Content Pipeline` (id: `6f8691a2-0688-4dae-80bd-8cac8c2a61f5`) — **active: true**
   - `ProfitEngine — Blog Cross-post Webhook` (id: `409ed6db-db7d-4778-b009-5895ef332def`) — **active: true**
3. **setup-n8n.sh rewritten** to use the n8n CLI approach (avoids REST API Secure-cookie issue over HTTP)

---

## SSH Access

```bash
# From WSL2 — deploy key at /tmp/profitengine_deploy
ssh -i /tmp/profitengine_deploy opc@129.146.167.73

# If /tmp/profitengine_deploy is gone (WSL restart):
# Private key stored in GitHub secret SERVER_SSH_KEY (base64-encoded)
# Decode: base64 -d <<< "$SERVER_SSH_KEY" > /tmp/profitengine_deploy && chmod 600 /tmp/profitengine_deploy
```

Deploy public key:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOBHpI9Cb2Nh//Hx3qPPQ6qeY9dZbVDobvh82oiI8e5O profitengine-deploy@github-actions
```

---

## GitHub CI/CD

```powershell
$env:GH_TOKEN = '<your-github-pat>'   # gho_... stored in password manager
& 'C:\Program Files\GitHub CLI\gh.exe' workflow run deploy.yml --repo quantam101/profitenginev5
& 'C:\Program Files\GitHub CLI\gh.exe' run watch --repo quantam101/profitenginev5
```

---

## Live Infrastructure

```
OCI Server:        129.146.167.73 (opc@)
Dashboard:         http://129.146.167.73:3000
n8n:               http://172.18.0.3:5678 (Docker-internal only)
                   Login: admin@alreadyherellc.com / ProfitEngine2026!

Running containers:
  profitenginev5-web-1       Next.js    port 3000
  profitenginev5-runtime-1   FastAPI    port 8080 (healthy)
  profitenginev5-caddy-1     Caddy      ports 80/443
  profitenginev5-n8n-1       n8n        port 5678 (internal)
  profitenginev5-ollama-1    Ollama     port 11434
  profitenginev5-postgres-1  Postgres   port 5432
```

---

## GitHub Secrets Status

| Secret | Status | Notes |
|--------|--------|-------|
| GROQ_API_KEY | ✅ Set | 2026-05-24 |
| GEMINI_API_KEY | ✅ Set | 2026-05-24 |
| GMAIL_APP_PASSWORD | ✅ Set | 2026-05-24 |
| CONTENT_REPO_TOKEN | ✅ Set | 2026-05-24 |
| SERVER_SSH_KEY | ✅ Set (base64) | 2026-05-26 |
| DEVTO_API_KEY | ❌ Missing | dev.to/settings/extensions |
| HASHNODE_API_KEY | ❌ Missing | hashnode.com/settings/developer |
| HASHNODE_PUB_ID | ❌ Missing | Your Hashnode publication ID |
| MEDIUM_API_KEY | ❌ Missing | medium.com/me/settings |
| MEDIUM_AUTHOR_ID | ❌ Missing | Your Medium user ID |
| AFFILIATE_LINKS | ❌ Missing | JSON object of affiliate links |
| AMAZON_PARTNER_TAG | ❌ Missing | Amazon Associates tag |

---

## Remaining Manual Steps (priority order)

### 1 — Vercel Webhook Token (5 min)

The server already has `WEBHOOK_SECRET=29d6accb030f7d60f1d0503197f9017e74962e18fdee514ea85c0635124f2700` in `.env`.
Add the matching token to Vercel:

1. Go to: https://vercel.com/already-here-llc-s-projects/profitengine/settings/environment-variables
2. Click **Add New**
3. Key: `PROFITENGINE_WEBHOOK_TOKEN`
4. Value: `29d6accb030f7d60f1d0503197f9017e74962e18fdee514ea85c0635124f2700`
5. Check all environments (Production, Preview, Development)
6. Save, then redeploy

### 2 — DNS A Records (5 min)

1. Go to: https://dcc.godaddy.com/control/portfolio/alreadyherellc.com/settings/dns
2. Add these A records (all pointing to `129.146.167.73`):
   - Name: `profitengine` → `129.146.167.73`
   - Name: `api.profitengine` → `129.146.167.73`
   - Name: `status.profitengine` → `129.146.167.73`
3. TTL: 600

### 3 — Blog Platform API Keys

Run `gh secret set <NAME> --repo quantam101/profitenginev5` for each:

**Dev.to** (free, 2 min):
- https://dev.to/settings/extensions → "DEV Community API Key"
- `gh secret set DEVTO_API_KEY`

**Hashnode** (free, 3 min):
- https://hashnode.com/settings/developer → Personal Access Token
- Publication ID from your Hashnode publication URL
- `gh secret set HASHNODE_API_KEY`
- `gh secret set HASHNODE_PUB_ID`

**Medium** (free, 5 min):
- https://medium.com/me/settings → Integration Tokens
- Author ID: `curl -H "Authorization: Bearer TOKEN" https://api.medium.com/v1/me`
- `gh secret set MEDIUM_API_KEY`
- `gh secret set MEDIUM_AUTHOR_ID`

### 4 — Affiliate Programs

- Amazon Associates: https://affiliate-program.amazon.com (takes days to approve)
- After approval: `gh secret set AMAZON_PARTNER_TAG` and `gh secret set AFFILIATE_LINKS`

### 5 — n8n External Access (optional)

n8n is currently only reachable on the Docker internal network. To expose via Caddy:
1. Add DNS record `n8n.profitengine` → `129.146.167.73`
2. Uncomment the n8n block in `caddy/Caddyfile`
3. Push to trigger a redeploy

---

## Key Infrastructure Details

```
OCI Server:
  IP: 129.146.167.73 / user: opc / OS: Oracle Linux / region: us-phoenix-1
  Instance OCID: ocid1.instance.oc1.phx.anyhqljsmvp52oyc4e4u537ie7faz2spvhfzciy2uyx53zmj3azzueccp7aq
  Repo dir: /home/opc/profitenginev5
  WEBHOOK_SECRET: 29d6accb030f7d60f1d0503197f9017e74962e18fdee514ea85c0635124f2700

n8n:
  Owner: admin@alreadyherellc.com / ProfitEngine2026!
  Workflow IDs:
    content-pipeline-daily:  6f8691a2-0688-4dae-80bd-8cac8c2a61f5
    blog-crosspost-webhook:   409ed6db-db7d-4778-b009-5895ef332def

GitHub:
  Repo: quantam101/profitenginev5
  Token: stored in your password manager (GH_TOKEN env var)
  CLI: C:\Program Files\GitHub CLI\gh.exe

Local Paths:
  Repo: C:\Users\alrea\profitenginev5\
  Deploy workflow: .github\workflows\deploy.yml
  Bootstrap script: scripts\bootstrap-server.sh
  n8n setup: scripts\setup-n8n.sh

OCI CLI:
  Config: C:\Users\alrea\.oci\config / Profile: PROFITENGINE
  Bastion OCID: ocid1.bastion.oc1.phx.amaaaaaamvp52oyafrslzyr3dbajlctmptq6lfdprpmplwy3kdgqa5wcrvpq
```

---

## Disk Space Warning

OCI root disk was at 95% (1.7 GB free) after first Docker build.
Free space: `ssh opc@129.146.167.73 'docker buildx prune -af'`
Or expand boot volume to 50 GB via OCI Console:
  Compute → Instances → profitenginev5 → Boot Volume → Resize
