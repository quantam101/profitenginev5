# Launch Checklist

The source artifact is deploy-ready when source checks pass. Public production is not live-ready until the infrastructure checks also pass:

- CI passes
- lint passes
- typecheck passes
- tests pass
- security scan passes
- no secrets in repo
- no paid adapters enabled
- no-spend policy active
- approval gate active
- audit log active
- [blocked] backups tested on the selected host
- [blocked] restore tested on the selected host
- [blocked] uptime monitor active
- [blocked] HTTPS active
- [blocked] firewall active
- [blocked] mobile smoke test passes
- SEO metadata present
- sitemap present
- rollback documented
- stale source scan passes

Current deployment blocker: Vercel CLI has no token in the local environment, and SSH to the OCI ProfitEngine instance times out from the Codex workspace.


## Domain / DNS

- [ ] `SITE_DOMAIN` set in `.env` and DNS points to OCI public IP.
- [ ] `www`, `app`, `api`, and `status` records exist.
- [ ] Caddy is running and HTTPS certificates are issued.
- [ ] `n8n` is not public unless authentication/access control is active.
- [ ] Only ports 22, 80, and 443 are publicly open.
