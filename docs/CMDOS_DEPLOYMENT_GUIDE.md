# Command OS (CMDOS) Unified Server Deployment Guide

**Date:** 2026-06-17  
**Target Server:** 129.146.236.177 (Oracle Cloud - Command OS)  
**Status:** Configuration Complete - Ready for Deployment

---

## Overview

All repositories and services are now configured to point to the centralized Command OS server at **129.146.236.177**. This document outlines the deployment process and configuration changes.

## Server Architecture

```
                    ┌─────────────────────────────────────┐
                    │   CMDOS Server (129.146.236.177)    │
                    │   - Unified Command Dashboard       │
                    │   - All API Backends                │
                    │   - Reverse Proxy (Nginx)           │
                    └─────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
        ┌─────────┐  ┌──────────────┐  ┌──────────────┐
        │  CMDOS  │  │   Runtime    │  │   Backend    │
        │  (3000) │  │   (8000)     │  │   (8001)     │
        │ Next.js │  │ Python API   │  │ FastAPI      │
        └─────────┘  └──────────────┘  └──────────────┘
```

## Configuration Changes

### 1. Environment Variables Updated

**File:** `.env.example`

```bash
# Before
RUNTIME_API_URL=http://runtime:8080
BACKEND_API_URL=http://backend:8001
ORACLE_API_URL=http://localhost:3000

# After
RUNTIME_API_URL=http://129.146.236.177:8000
BACKEND_API_URL=http://129.146.236.177:8001
ORACLE_API_URL=http://129.146.236.177:3000
```

### 2. Docker Compose Production Configuration

**File:** `deploy/docker-compose.prod.yml`

✅ **Updated** - Multi-service deployment with proper networking:
- `cmdos` service (Next.js) on port 3000
- `runtime` service (Python FastAPI) on port 8000
- `backend` service (FastAPI) on port 8001
- `nginx` service handling reverse proxy on ports 80/443
- Shared `cmdos-network` for inter-service communication

### 3. GitHub Actions Workflows Updated

#### Deploy Workflow
**File:** `.github/workflows/deploy.yml`

Changes:
- `oci_host` input → `cmdos_host`
- Default: `129.146.236.177`
- `OCI_RUNTIME_HOST` → `CMDOS_HOST`
- `HEALTH_URL` → Points to cmdos health endpoint

#### Auto-Recovery Workflow
**File:** `.github/workflows/oci-auto-recovery.yml`

Changes:
- `RECOVERY_HOST` → Points to `129.146.236.177`
- `RUNTIME_API_URL` → Points to cmdos runtime API
- `OCI_RUNTIME_INSTANCE_NAME` → `CMDOS_INSTANCE_NAME`

### 4. Vercel Configuration

**File:** `vercel.json`

Environment variables for Next.js frontend:
- `RUNTIME_API_URL=http://129.146.236.177:8000`
- `BACKEND_API_URL=http://129.146.236.177:8001`
- `ORACLE_API_URL=http://129.146.236.177:3000`

### 5. Reverse Proxy Configuration

**File:** `deploy/nginx.conf`

✅ **Created** - Comprehensive nginx configuration:
- Health check endpoint on `/health`
- Primary domain routing to cmdos dashboard
- API routing to runtime/backend services
- SSL/TLS support
- Backend subdomain routing
- Subdomain isolation for api.*, backend.*

### 6. Caddyfile Updated

**File:** `caddy/Caddyfile`

- Updated health check reference: `129.146.236.177/health`
- Internal service routing remains unchanged (uses Docker names)

---

## Deployment Steps

### Prerequisites

✅ SSH access to cmdos server (opc@129.146.236.177)  
✅ Docker & Docker Compose installed  
✅ GitHub SSH deploy key configured  
✅ SSL certificates in place  

### Step 1: Prepare the Cmdos Server

```bash
# SSH to cmdos server
ssh opc@129.146.236.177

# Create application directory
mkdir -p /home/opc/profitenginev5
cd /home/opc/profitenginev5

# Clone repository (if not already present)
git clone https://github.com/quantam101/profitenginev5.git .
```

### Step 2: Configure Environment Variables

```bash
# Create .env file from example
cp .env.example .env

# Edit .env and set required values
nano .env

# Key variables to configure:
# - SITE_DOMAIN=profitengine.alreadyherellc.com
# - POSTGRES_PASSWORD=<secure-password>
# - ANTHROPIC_API_KEY=<from-secrets>
# - All social media and API keys
```

### Step 3: Deploy Services via Docker Compose

```bash
# Navigate to deploy directory
cd deploy

# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Start services
docker compose -f docker-compose.prod.yml up -d --build

# Verify all services are running
docker compose -f docker-compose.prod.yml ps
```

### Step 4: Verify Health Endpoints

```bash
# Check cmdos dashboard
curl http://localhost:3000/

# Check runtime API
curl http://localhost:8000/health

# Check backend API
curl http://localhost:8001/health

# Check nginx health
curl http://localhost/health
```

### Step 5: External Verification (from local machine)

```bash
# Test from outside the server
curl -v http://129.146.236.177/health
curl -v http://129.146.236.177:3000/
curl -v http://129.146.236.177:8000/health
curl -v http://129.146.236.177:8001/health
```

---

## Service Endpoints

| Service | Internal URL | External URL | Port |
|---------|--------------|--------------|------|
| Dashboard | http://cmdos:3000 | http://129.146.236.177:3000 | 3000 |
| Runtime API | http://runtime:8000 | http://129.146.236.177:8000 | 8000 |
| Backend API | http://backend:8001 | http://129.146.236.177:8001 | 8001 |
| Reverse Proxy | http://nginx | http://129.146.236.177 | 80/443 |

---

## Integration Points

### All Repositories Now Point To:

1. **ProfitEngine v5 (main)**
   - API: http://129.146.236.177:8000
   - Backend: http://129.146.236.177:8001
   - Web: http://129.146.236.177:3000

2. **GitHub Actions Workflows**
   - Deploy target: 129.146.236.177
   - Health checks: http://129.146.236.177/health
   - Recovery operations: ssh opc@129.146.236.177

3. **Vercel Frontend Deployment**
   - Runtime API: http://129.146.236.177:8000
   - Backend API: http://129.146.236.177:8001
   - Dashboard: http://129.146.236.177:3000

4. **Content/Publishing Pipelines**
   - All webhooks point to: http://129.146.236.177/api/webhooks/*
   - All API calls routed through nginx

---

## Monitoring & Troubleshooting

### Health Check Status

```bash
# SSH to cmdos server
ssh opc@129.146.236.177

# Check all service health
docker compose -f deploy/docker-compose.prod.yml ps

# View logs
docker compose -f deploy/docker-compose.prod.yml logs -f

# Check specific service
docker compose -f deploy/docker-compose.prod.yml logs runtime
docker compose -f deploy/docker-compose.prod.yml logs backend
docker compose -f deploy/docker-compose.prod.yml logs cmdos
```

### Common Issues

#### Services not starting
```bash
# Check disk space
df -h /home/opc

# Check Docker daemon
docker ps

# Rebuild images
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

#### Network connectivity issues
```bash
# Test connectivity from server
curl -v http://localhost:3000
curl -v http://localhost:8000/health
curl -v http://localhost:8001/health

# Check firewall
sudo ufw status

# Restart services
docker compose -f deploy/docker-compose.prod.yml restart
```

#### SSL/TLS certificate issues
```bash
# Verify certificate exists
ls -la deploy/ssl/

# Update nginx configuration
# Edit: deploy/nginx.conf (update cert paths)
docker compose -f deploy/docker-compose.prod.yml restart nginx
```

---

## Post-Deployment Verification

### 1. Dashboard Accessibility

```bash
# From local machine
curl -I http://129.146.236.177:3000
# Expected: 200 OK
```

### 2. API Endpoint Tests

```bash
# Runtime API
curl http://129.146.236.177:8000/health
# Expected: {"status": "healthy"}

# Backend API
curl http://129.146.236.177:8001/health
# Expected: 200 OK
```

### 3. GitHub Actions Workflow

```bash
# Trigger deploy workflow manually
gh workflow run deploy.yml -f cmdos_host=129.146.236.177
```

### 4. Domain Resolution

```bash
# Test main domain (when configured)
curl -I https://profitengine.alreadyherellc.com
curl -I https://api.profitengine.alreadyherellc.com
curl -I https://backend.alreadyherellc.com
```

---

## Rollback Procedure

If issues occur, rollback to previous deployment:

```bash
# SSH to cmdos server
ssh opc@129.146.236.177

# Stop current services
docker compose -f deploy/docker-compose.prod.yml down

# Checkout previous commit
git checkout HEAD~1

# Redeploy
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

---

## Files Modified/Created

### Modified Files:
- ✅ `.env.example` - Updated API URLs
- ✅ `vercel.json` - Updated environment variables
- ✅ `.github/workflows/deploy.yml` - Updated server references
- ✅ `.github/workflows/oci-auto-recovery.yml` - Updated recovery host
- ✅ `deploy/docker-compose.prod.yml` - Complete rewrite for multi-service deployment
- ✅ `caddy/Caddyfile` - Updated IP reference in comments

### Created Files:
- ✅ `deploy/nginx.conf` - New reverse proxy configuration
- ✅ `docs/CMDOS_DEPLOYMENT_GUIDE.md` - This guide

---

## Next Steps

1. **SSH to cmdos server** and follow Step 1-5 above
2. **Verify health endpoints** are all responding (Step 5)
3. **Update GitHub Secrets** with cmdos credentials if needed
4. **Run GitHub Actions deploy** to push latest code
5. **Monitor logs** for any issues
6. **Test end-to-end** flow from frontend → API → backend

---

## Support & Escalation

For deployment issues:

1. Check service logs: `docker compose logs -f`
2. Verify network connectivity: `curl http://localhost:8000/health`
3. Check disk space: `df -h`
4. Review GitHub Actions workflow runs
5. Check DNS resolution if using domains

---

**Status:** ✅ Ready for Production Deployment  
**Last Updated:** 2026-06-17  
**Version:** 1.0
