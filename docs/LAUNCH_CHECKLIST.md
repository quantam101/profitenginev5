# Launch Checklist

## Source / CI Status (all passing ✅)

- [x] CI passes
- [x] Lint passes
- [x] Typecheck passes
- [x] Tests pass (34/34)
- [x] Security scan passes — no secrets in repo
- [x] No paid adapters enabled (`max_cost_usd: 0`)
- [x] No-spend policy active
- [x] Approval gate active
- [x] Audit log active
- [x] SEO metadata present
- [x] Rollback documented
- [x] `/api/health` returns 100/100 locally
- [x] Dashboard shows live published-post count + content site link
- [x] Multi-platform publishing: GitHub Pages → Dev.to → Hashnode → Medium
- [x] Affiliate link injection ready (Amazon tag `alreadyhere-20` auto-applied)

---

## Content Pipeline (live ✅)

- [x] GitHub Pages content site live: https://quantam101.github.io/content
- [x] 15+ articles published and growing daily (07:05 UTC auto-publish)
- [x] Daily auto-publish cron: 07:05 UTC via GitHub Actions (free tier)
- [x] 90-topic rotation in `scripts/article_topics.py`
- [x] Affiliate link injection ready (`AFFILIATE_LINKS` env var)
- [x] Amazon Associates tag `alreadyhere-20` auto-appended to Amazon URLs
- [x] FTC disclosure auto-injected in every GitHub Pages post
- [x] Hashnode + Medium publishing wired in (`scripts/publish_article.py`)
- [ ] **Dev.to account** — sign up at https://dev.to/enter?state=new-user
      → Settings → Extensions → API Key → add as GitHub Secret `DEVTO_API_KEY`
- [ ] **Hashnode account** — sign up at https://hashnode.com
      → Settings → Developer → Personal Access Token → add as `HASHNODE_API_KEY`
      → Publication Settings → find Publication ID → add as `HASHNODE_PUB_ID`
- [ ] **Medium account** — sign up at https://medium.com
      → Settings → Security → Integration tokens → add as `MEDIUM_API_KEY`
      → find User ID via API → add as `MEDIUM_AUTHOR_ID`
- [ ] **Affiliate programs** — see `docs/AFFILIATE_SETUP.md`
      → add URLs as GitHub Secret `AFFILIATE_LINKS` (JSON string)

---

## Server Deploy (ONE action needed ⚠️)

The deploy SSH public key must be added to the OCI server once.
After that, every `git push` auto-deploys via GitHub Actions.

**Deploy public key to add:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF5IOnsqRDtbUYu5WQfLaAjAQmc+zKrlK6TDafDgO0Ij profitengine-deploy@github-actions
```

### Option A — OCI Console (easiest, 2 minutes)
1. Go to https://cloud.oracle.com → sign in
2. Compute → Instances → click your instance (IP: 129.146.167.73)
3. Click **Edit** (top right)
4. Under **SSH keys** → **Add SSH keys** → paste the key above
5. Click **Save changes**
6. Go to GitHub → Actions → **Deploy to OCI Server** → **Run workflow**

### Option B — Bitwarden re-auth (if you prefer SSH)
```powershell
# In a PowerShell terminal:
docker exec -it local-operator bash
# Inside container:
bw login   # enter your Bitwarden email + master password
bw list items --search "OCI" | python3 -c "import json,sys; [print(i['login']['password']) for i in json.loads(sys.stdin.read()) if 'key' in i.get('name','').lower()]"
# Copy the private key, save to ~/.ssh/oci_key, chmod 600
# Then SSH: ssh -i ~/.ssh/oci_key ubuntu@129.146.167.73
# Once in: paste the bootstrap one-liner from Option C
```

### Option C — Bootstrap one-liner (run on server after SSH access)
Replace each `<placeholder>` with the actual key from your password manager:
```bash
GROQ_API_KEY="<your-groq-key>" \
GEMINI_API_KEY="<your-gemini-key>" \
GITHUB_CONTENT_TOKEN="<your-github-pat>" \
GMAIL_APP_PASSWORD="<your-gmail-app-password>" \
bash <(curl -fsSL https://raw.githubusercontent.com/quantam101/profitenginev5/main/scripts/bootstrap-server.sh)
```
Keys are in your Bitwarden vault and in the GitHub Actions secrets.

---

## GitHub Secrets Status

| Secret | Status | Notes |
|--------|--------|-------|
| `SERVER_SSH_KEY` | ✅ Set | ED25519 deploy private key |
| `GROQ_API_KEY` | ✅ Set | Groq Cloud free tier |
| `GEMINI_API_KEY` | ✅ Set | Google AI free tier |
| `GMAIL_APP_PASSWORD` | ✅ Set | Gmail digest alerts |
| `CONTENT_REPO_TOKEN` | ✅ Set | GitHub PAT for content repo |
| `DEVTO_API_KEY` | ⬜ Missing | Create Dev.to account first |
| `HASHNODE_API_KEY` | ⬜ Missing | Create Hashnode account first |
| `HASHNODE_PUB_ID` | ⬜ Missing | Get from Hashnode publication settings |
| `MEDIUM_API_KEY` | ⬜ Missing | Create Medium account first |
| `MEDIUM_AUTHOR_ID` | ⬜ Missing | Get from Medium API |
| `AFFILIATE_LINKS` | ⬜ Missing | Add after affiliate approval |
| `AMAZON_PARTNER_TAG` | ⬜ Optional | Set to `alreadyhere-20` (already in code default) |

To add a secret: GitHub → repo → Settings → Secrets → Actions → New secret

---

## Post-Deploy (after server is up)

- [ ] Run `bash scripts/setup-n8n.sh` on server to activate n8n workflows
- [ ] Verify n8n dashboard at https://app.profitengine.alreadyherellc.com
- [ ] Verify `/api/health` returns 100/100
- [ ] HTTPS certificates issued by Caddy (auto, wait ~60s after first deploy)
- [ ] Confirm only ports 22, 80, 443 are open in OCI Security List

---

## Domain / DNS

- [ ] `SITE_DOMAIN` set in `.env` (default: `profitengine.alreadyherellc.com`)
- [ ] A records: `@`, `app`, `api` → 129.146.167.73
- [ ] Caddy is running and HTTPS certificates are issued
- [ ] n8n not publicly exposed until `N8N_BASIC_AUTH_ACTIVE=true` confirmed
