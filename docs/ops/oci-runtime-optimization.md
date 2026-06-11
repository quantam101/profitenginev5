# OCI Runtime Optimization

Date: 2026-06-11

## Target architecture

Vercel remains the primary public deployment for the revenue-facing ProfitEngine app. OCI is a runtime mirror and worker host. OCI instability must not break Vercel deployment status, CI readiness, or revenue-capture confidence.

## Optimized flow

1. GitHub CI validates application correctness.
2. `Runtime Image — GHCR` builds and publishes `ghcr.io/quantam101/profitenginev5-runtime:latest`.
3. The OCI host runs `scripts/oci-runtime-update.sh` through systemd every 10 minutes.
4. The host pulls the prebuilt image, retags it as `profitenginev5-runtime:latest`, swaps only the `runtime` compose service, verifies health, and rolls back if health fails.

## Why this is better

The previous flow mixed build validation, Docker image creation, and OCI host synchronization. A blocked SSH port or an unreachable runtime endpoint could make CI look failed even when the production Vercel deployment was usable.

The optimized flow separates concerns:

| Layer | Responsibility | Failure impact |
|---|---|---|
| CI Stage 1-6 | Code correctness, tests, build readiness | Blocks release |
| Vercel | Public revenue-facing deployment | Blocks revenue surface if failed |
| GHCR image workflow | Runtime artifact creation | Blocks Docker runtime rollout |
| OCI systemd updater | Host-side mirror update | Degraded mirror only |
| Docker Guard | Disk/container hygiene | Operational warning only |
| OCI Exec | Manual diagnostic helper | Operational warning only |

## Files added

- `scripts/oci-runtime-update.sh`
- `scripts/install-oci-runtime-updater.sh`
- `ops/systemd/profitengine-runtime-update.service`
- `ops/systemd/profitengine-runtime-update.timer`

## OCI install command

Run from OCI console, serial console, or an already-authenticated shell on the OCI host:

```bash
cd /home/opc/profitenginev5
git fetch origin main
git reset --hard origin/main
sudo APP_DIR=/home/opc/profitenginev5 bash scripts/install-oci-runtime-updater.sh
```

## Manual one-shot update

```bash
cd /home/opc/profitenginev5
APP_DIR=/home/opc/profitenginev5 bash scripts/oci-runtime-update.sh
```

## Status checks

```bash
systemctl status profitengine-runtime-update.timer --no-pager
systemctl status profitengine-runtime-update.service --no-pager
journalctl -u profitengine-runtime-update.service -n 100 --no-pager
curl -fsS https://api.profitengine.alreadyherellc.com/health
```

## Safety rules

Do not mount `/var/run/docker.sock` into the public runtime container. Docker socket access gives the container effective control over the host.

Do not run Docker builds on the OCI host. The host should only pull prebuilt images, retag, compose up, verify, rollback, and prune safely.

Do not make OCI mirror failures block Vercel production unless `OCI_SYNC_STRICT=true` is intentionally enabled.
