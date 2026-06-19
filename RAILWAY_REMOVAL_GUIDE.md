# Railway Removal - Complete Guide

## Status: ✅ Code is clean
Railway has been permanently removed from the codebase:
- ✅ No `railway.json` or `railway.toml` files
- ✅ No Railway environment variables
- ✅ No Railway references in CI/CD workflows
- ✅ All Railway documentation deleted
- ✅ Railway policy check in place (prevents re-addition)

## Problem: Notifications Still Appearing
You're receiving notifications because **Railway still has a GitHub App webhook installed** on the repository.

## Solution: Remove the Railway GitHub App

### Option 1: Via GitHub Settings (Recommended)
1. Go to `https://github.com/settings/installations`
2. Find "Railway" in the installed apps list
3. Click **"Configure"** next to Railway
4. Scroll to bottom → **"Uninstall"**
5. Confirm uninstallation

### Option 2: Via Railway Dashboard
1. Log in to `railway.app`
2. Go to Settings → Integrations
3. Find GitHub integration → **"Disconnect"**
4. Confirm disconnection

### Option 3: Via GitHub Repo Settings
1. Go to `https://github.com/quantam101/profitenginev5/settings/installations`
2. Find Railway in the list
3. Click **"Uninstall"**

## Verification
After removal, you should:
- ❌ Stop receiving Railway deployment notifications
- ❌ No more "Deploy Crashed!" emails
- ✅ Continue receiving GitHub Actions notifications normally

## Why This Happened
Railway was previously used as a deployment platform but has been deprecated in favor of:
- **Frontend**: Vercel (Next.js → `profitengine-tau.vercel.app`)
- **Backend**: OCI Always Free VM (Go + SQLite → `cmdos` at `129.146.236.177`)

Railway's free tier is outdated and no longer needed.

## Prevention
The codebase now includes `scripts/check-no-railway.sh` which runs in CI to ensure Railway configs are never accidentally re-added.
