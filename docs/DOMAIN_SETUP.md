# Domain Deployment Plan

## Environment Variable Configuration

This project uses the `SITE_DOMAIN` environment variable for all domain references.
Set it in `.env` before deploying:

```bash
SITE_DOMAIN=alreadyherellc.com
ACME_EMAIL=ops@alreadyherellc.com
```

The Caddyfile uses `{$SITE_DOMAIN}` and `docker-compose.yml` uses `${SITE_DOMAIN}`
to resolve the domain at runtime.

## Production Architecture

- **Frontend / API**: Next.js on Vercel → `https://app.{SITE_DOMAIN}`
- **Runtime**: Python FastAPI in Docker → served behind Caddy at `https://api.{SITE_DOMAIN}`
- **Reverse proxy / TLS**: Caddy on the Docker host
- **Optional status page**: Uptime Kuma in Docker → `https://status.{SITE_DOMAIN}`

The Docker host may be any cloud VM, bare-metal server, or local machine with a public IP.
The specific provider is outside the scope of this repo.

## Recommended DNS Model

Preferred stack:

```txt
Registrar (e.g. GoDaddy)
  -> Cloudflare Free DNS / Proxy
    -> Docker host public IP
      -> Caddy HTTPS reverse proxy
        -> GMAOS / EAOS services
```

Keeping DNS at the registrar also works, but Cloudflare Free is preferred for easier
proxying, TLS handling, security rules, and future access controls.

## Required DNS Records

After the Docker host public IP is known, configure either direct A records:

```txt
A  @      <docker-host-public-ip>
A  www    <docker-host-public-ip>
A  app    <docker-host-public-ip>
A  api    <docker-host-public-ip>
A  status <docker-host-public-ip>
```

Or one root A record plus CNAME aliases:

```txt
A      @      <docker-host-public-ip>
CNAME  www    {SITE_DOMAIN}
CNAME  app    {SITE_DOMAIN}
CNAME  api    {SITE_DOMAIN}
CNAME  status {SITE_DOMAIN}
CNAME  docs   {SITE_DOMAIN}
```

Do not expose `n8n.{SITE_DOMAIN}` until authentication and access controls are confirmed.

## Subdomain Map

```txt
{SITE_DOMAIN}         Public website / landing page (Vercel or Caddy)
www.{SITE_DOMAIN}     Public alias
app.{SITE_DOMAIN}     GMAOS command center
api.{SITE_DOMAIN}     EAOS runtime API gateway
status.{SITE_DOMAIN}  Uptime/status page
n8n.{SITE_DOMAIN}     Automation server, protected only
docs.{SITE_DOMAIN}    Documentation / SOP portal, optional
```

## Host Firewall

Only these public ports should be open:

```txt
22/tcp   SSH, restricted by source IP where possible
80/tcp   HTTP for HTTPS issuance/redirect
443/tcp  HTTPS public web
```

Do not expose these publicly:

```txt
Postgres
Redis
Qdrant / Chroma
Ollama
n8n without auth
internal runtime ports
database admin panels
backup/download routes
approval mutation routes
```

## Deployment Files Added

```txt
caddy/Caddyfile          Uses {$SITE_DOMAIN} env var
docs/DOMAIN_SETUP.md     This file
.env.example             Domain variables template
docker-compose.yml       Uses ${SITE_DOMAIN} env var
```

## Domain Launch Checklist

```txt
[ ] Confirm domain registrar access
[ ] Decide registrar DNS or Cloudflare Free DNS
[ ] Provision a Docker host with a public IP
[ ] Record the Docker host public IP
[ ] Add DNS records (A + CNAMEs)
[ ] Copy .env.example to .env on the server
[ ] Set SITE_DOMAIN=alreadyherellc.com in .env (or the actual production domain)
[ ] Set ACME_EMAIL=ops@alreadyherellc.com in .env
[ ] Replace server-side passwords in .env
[ ] Run docker compose up -d --build
[ ] Verify https://alreadyherellc.com
[ ] Verify https://app.alreadyherellc.com
[ ] Verify https://api.alreadyherellc.com health endpoint
[ ] Verify https://status.alreadyherellc.com
[ ] Keep n8n private until auth/access controls are confirmed
[ ] Add uptime checks
[ ] Confirm no paid adapters enabled
```
