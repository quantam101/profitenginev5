# Launch Checklist

## Source / CI Status

- [ ] CI passes
- [ ] Lint passes
- [ ] Typecheck passes
- [ ] Tests pass (`npm test`)
- [ ] Security scan passes (`npm run security:scan`) — no secrets in repo
- [ ] No paid adapters enabled (`max_cost_usd: 0`)
- [ ] No-spend policy active
- [ ] Approval gate active
- [ ] Audit log active
- [ ] SEO metadata present
- [ ] Rollback documented
- [ ] `/api/health` returns 100/100 locally
- [ ] Dashboard shows live published-post count + content site link
- [ ] Multi-platform publishing: GitHub Pages → Dev.to → Hashnode → Medium
- [ ] Affiliate link injection ready (Amazon tag `alreadyhere-20` auto-applied)

---

## Content Pipeline

- [ ] GitHub Pages content site live: https://quantam101.github.io/content
- [ ] 15+ articles published and growing daily (07:05 UTC auto-publish)
- [ ] Daily auto-publish cron: 07:05 UTC via GitHub Actions (free tier)
- [ ] 90-topic rotation in `scripts/article_topics.py`
- [ ] Affiliate link injection ready (`AFFILIATE_LINKS` env var)
- [ ] Amazon Associates tag `alreadyhere-20` auto-appended to Amazon URLs
- [ ] FTC disclosure auto-injected in every GitHub Pages post
- [ ] Hashnode + Medium publishing wired in (`scripts/publish_article.py`)
- [ ] Dev.to account — sign up at https://dev.to/enter?state=new-user
      → Settings → Extensions → API Key → add as GitHub Secret `DEVTO_API_KEY`
- [ ] Hashnode account — sign up at https://hashnode.com
      → Settings → Developer → Personal Access Token → add as `HASHNODE_API_KEY`
      → Publication Settings → find Publication ID → add as `HASHNODE_PUB_ID`
- [ ] Medium account — sign up at https://medium.com
      → Settings → Security → Integration tokens → add as `MEDIUM_API_KEY`
      → find User ID via API → add as `MEDIUM_AUTHOR_ID`
- [ ] Affiliate programs — see `docs/AFFILIATE_SETUP.md`
      → add URLs as GitHub Secret `AFFILIATE_LINKS` (JSON string)

---

## Server Deploy

The live services (runtime, backend, taylor, ollama, n8n) run on a Docker host
behind Caddy. Vercel hosts the Next.js frontend.

1. Provision a Docker host with a public IP.
2. Add the host SSH key as a GitHub Actions secret (`SERVER_SSH_KEY`) or run
docker compose locally.
3. Copy `.env.example` to `.env` on the server and fill in real secrets.
4. Run `docker compose up -d --build` on the server.

For local development use `npm run dev` and `docker compose up -d` for the
backing services.

---

## GitHub Secrets Status

| Secret | Status | Notes |
|--------|--------|-------|
| `SERVER_SSH_KEY` | optional | ED25519 deploy private key (only for remote server deploy) |
| `GROQ_API_KEY` | optional | Groq Cloud free tier |
| `GEMINI_API_KEY` | optional | Google AI free tier |
| `GMAIL_APP_PASSWORD` | optional | Gmail digest alerts |
| `CONTENT_REPO_TOKEN` | optional | GitHub PAT for content repo |
| `DEVTO_API_KEY` | optional | Create Dev.to account first |
| `HASHNODE_API_KEY` | optional | Create Hashnode account first |
| `HASHNODE_PUB_ID` | optional | Get from Hashnode publication settings |
| `MEDIUM_API_KEY` | optional | Create Medium account first |
| `MEDIUM_AUTHOR_ID` | optional | Get from Medium API |
| `AFFILIATE_LINKS` | optional | Add after affiliate approval |
| `AMAZON_PARTNER_TAG` | optional | Defaults to `alreadyhere-20` in code |

To add a secret: GitHub → repo → Settings → Secrets → Actions → New secret

---

## Post-Deploy

- [ ] Run `bash scripts/setup-n8n.sh` on the server to activate n8n workflows
- [ ] Verify n8n dashboard at the private `n8n` subdomain
- [ ] Verify `/api/health` returns 100/100
- [ ] HTTPS certificates issued by Caddy (auto, wait ~60s after first deploy)
- [ ] Confirm only ports 22, 80, 443 are open on the host firewall

---

## Domain / DNS

- [ ] `SITE_DOMAIN` set in `.env` (default: `alreadyherellc.com`)
- [ ] A records: `@`, `www`, `app`, `api` → Docker host public IP
- [ ] Caddy is running and HTTPS certificates are issued
- [ ] n8n not publicly exposed until `N8N_BASIC_AUTH_ACTIVE=true` confirmed
