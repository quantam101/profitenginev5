# Ops Runbook — OCI Server & Workflow Fleet

Last verified: 2026-07-08 (full-fleet workflow sweep). This documents server facts,
fixed configuration, and open items. No secret values live in this file — secrets are
in GitHub Actions secrets, Vercel project env, and the server's `.env` files only.

## OCI Server (cmdos)

- Host: `129.146.236.177`, user `opc` (the box runs **Ubuntu 20.04** despite the OCI-style username)
- Python: **3.8.10** only — no `dataclass(slots=True)`, no ensurepip/venv package.
  pip is bootstrapped user-side: `curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | python3 - --user`
- **sudo is password-protected** — no non-interactive root. All automation must run rootless:
  - pm2 lives under `NPM_CONFIG_PREFIX=$HOME/.npm-global` (add `$HOME/.npm-global/bin` to PATH)
  - Python packages install with `python3 -m pip install --user`
- GitHub access: read-only deploy key `~/.ssh/github_deploy` (registered on profitenginev5,
  key id 156746536); private-repo clones use the `git@github.com:` remote form
- pm2 processes: `profitengine` and `mcp-trading-engine` (port 8000; health:
  `curl http://localhost:8000/healthz` → `{"status":"ok","engine":"mcp-trading"}`;
  engine requires `httpx[http2]`)
- Docker socket is `root:docker` and **opc is not in the docker group** — see Open Items

## GitHub Actions secrets (names only, verified working 2026-07-08)

- `profitenginev5.CMDOS_SSH_KEY` — private key for `opc@129.146.236.177` (refreshed 2026-07-08)
- `already-here-llc.ORACLE_SSH_KEY` — same key; `already-here-llc.ORACLE_VM_HOST` = 129.146.236.177
- Deploy workflows that touch `.github/workflows/**` cannot merge via the gh OAuth API
  (no `workflow` scope) — merge locally via git push instead

## Workflow fleet facts

- `hybrid-micro-trading.yml` / `aggressive-micro-trading.yml` are **disabled**: their entry
  scripts (`trading-agent/run_hybrid_trading.py`, `run_aggressive_trading.py`) never existed
  in any recoverable history. Write the scripts before re-enabling.
- `oci-hybrid-setup.yml` is blocked at step 2 by design (needs root for system packages).
- `premarket-research.yml`: Slack alert is gated on `SLACK_WEBHOOK_URL` being configured;
  note that the `secrets` context is invalid in step-level `if:` — the gate uses a check-step output.
- `deploy-mcp-engine.yml`: syncs with `git fetch && git reset --hard FETCH_HEAD` (race-proof),
  installs `fastapi 'httpx[http2]' 'uvicorn[standard]' numpy` user-side, pm2 under user prefix.
- roadkingstransport (Vercel project `roadkings-transport-site`, NOT git-connected):
  deploy with `vercel deploy --prod` from a checkout, then `vercel alias set <deploy-url>
  www.roadkingstransport.us` — aliasing the apex alone leaves www on the old deployment.
  vercel.json gotcha: redirect `source` must be `"/(.*)"` (+`$1`) — `/:path*` does not match `/`.

## Open items (need owner action)

1. **One root session on the OCI box** (OCI Console serial console or sudo password) to run:
   - `usermod -aG docker opc` — without it, workflow docker commands silently no-op
   - provision TLS for `api.alreadyherellc.com` (cert + proxy vhost → 127.0.0.1:8001);
     until then `register-client.yml` fails with curl exit 35
   - optional: `echo 'opc ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/opc` to unblock oci-hybrid-setup
2. **Rotate `GMAIL_APP_PASSWORD`** (Google rejects the stored value — send-medium-email fails)
3. **Add YouTube OAuth secrets** `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` /
   `YOUTUBE_REFRESH_TOKEN` (autonomous-video-production)
4. **Run `setup-telegram.yml` once** with the real bot token from @BotFather
5. **Regenerate `GH_PAT_WRITE`** in already-here-llc (repo+workflow scopes) — apply-patches
