# GitHub Secrets Setup - Required for Production

## Instructions

1. Go to: `https://github.com/quantam101/profitenginev5`
2. Settings → Secrets and variables → Actions
3. Add each secret below

---

## Required Secrets (CRITICAL - Deployment Won't Work Without These)

### Gumroad Integration

**Name:** `GUMROAD_ACCESS_TOKEN`  
**Value:** Your Gumroad API token  
**Get from:** https://app.gumroad.com/settings/api → Copy access token  
**Used for:** Automated product creation and sales tracking

**Name:** `GUMROAD_SELLER_ID`  
**Value:** Your Gumroad seller ID  
**Get from:** Your Gumroad profile or API dashboard  
**Used for:** Product management

---

### Printify Integration

**Name:** `PRINTIFY_API_TOKEN`  
**Value:** Your Printify API token  
**Get from:** https://printify.com/dashboard → Settings → API → Create/copy token  
**Used for:** Automated product creation and order tracking

---

### Beehiiv Integration

**Name:** `BEEHIIV_API_KEY`  
**Value:** Your Beehiiv API key  
**Get from:** https://dashboard.beehiiv.com → Settings → API  
**Used for:** Newsletter automation and subscriber management

**Name:** `BEEHIIV_PUBLICATION_ID`  
**Value:** Your publication ID  
**Get from:** Beehiiv dashboard → Publication ID in settings  
**Used for:** Sending newsletters and tracking campaigns

---

### YouTube Analytics Integration

**Name:** `YOUTUBE_CLIENT_ID`  
**Value:** OAuth 2.0 Client ID from Google Cloud Console  
**Get from:** https://console.cloud.google.com → APIs & Services → Credentials  
**Used for:** YouTube Analytics API authentication

**Name:** `YOUTUBE_CLIENT_SECRET`  
**Value:** OAuth 2.0 Client Secret  
**Get from:** Same location as CLIENT_ID  
**Used for:** Token refresh

**Name:** `YOUTUBE_REFRESH_TOKEN`  
**Value:** Refresh token for YouTube OAuth  
**Get from:** Run `python scripts/get_youtube_refresh_token.py`  
**Used for:** Accessing YouTube Analytics data

**Name:** `YOUTUBE_CHANNEL_ID`  
**Value:** Your YouTube channel ID (UCxxxxxx...)  
**Get from:** youtube.com/account_advanced  
**Used for:** Fetching your channel's revenue data

---

### OCI Server Deployment

**Name:** `OCI_SSH_KEY`  
**Value:** Private SSH key for OCI server  
**Get from:** Run `bash scripts/setup-oci-ssh-secret.sh`  
**Used for:** SSH access to deploy backend

**Format:** Starts with `-----BEGIN OPENSSH PRIVATE KEY-----`

**Instructions:**
```bash
# Generate key pair
bash scripts/setup-oci-ssh-secret.sh

# This outputs:
# 1. Private key → Add to GitHub Secrets as OCI_SSH_KEY
# 2. Public key → Add to OCI console instance settings
```

---

### Database Credentials

**Name:** `POSTGRES_PASSWORD`  
**Value:** Strong password for PostgreSQL  
**Generate:** `openssl rand -base64 32`  
**Used for:** Local PostgreSQL container (if running locally)

---

### Third-Party API Keys

**Name:** `STRIPE_API_KEY`  
**Value:** Stripe API key (starts with `sk_live_`)  
**Get from:** https://dashboard.stripe.com → Developers → API keys  
**Used for:** Payment processing

**Name:** `OPENAI_API_KEY`  
**Value:** OpenAI API key (starts with `sk-`)  
**Get from:** https://platform.openai.com → API keys  
**Used for:** AI content generation (optional)

---

### Monitoring & Alerts

**Name:** `SLACK_WEBHOOK_URL`  
**Value:** Slack webhook for deployment notifications  
**Get from:** Slack workspace → Create Webhook  
**Used for:** Notifications on revenue, deployments, errors

---

## How to Add Secrets to GitHub

### Via Web Interface (Easiest)

1. Go to repository settings
2. Click "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Paste secret name and value
5. Click "Add secret"

### Via GitHub CLI

```bash
gh secret set GUMROAD_ACCESS_TOKEN --body "your-token-here"
gh secret set PRINTIFY_API_TOKEN --body "your-token-here"
# ... repeat for each secret
```

---

## Verification

After adding all secrets, verify in GitHub Actions:

```bash
# View all added secrets (masked)
gh secret list

# Expected output:
BEEHIIV_API_KEY
GUMROAD_ACCESS_TOKEN
OCI_SSH_KEY
PRINTIFY_API_TOKEN
STRIPE_API_KEY
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_CHANNEL_ID
YOUTUBE_REFRESH_TOKEN
# ... etc
```

---

## Security Notes

⚠️ **CRITICAL:**
- Never commit secrets to git
- Never share secret values
- Rotate secrets regularly (monthly minimum)
- Use strong passwords (30+ characters)
- Store copies in secure password manager (1Password, Bitwarden, etc.)

✓ **DO:**
- Keep secrets in GitHub Secrets only
- Review access logs monthly
- Rotate if compromised
- Use separate test/prod tokens

---

## Emergency Rotation

If a secret is compromised:

1. **Immediately revoke** the token in the source platform
2. **Generate new** token
3. **Update GitHub Secret** with new value
4. **Redeploy** application
5. **Monitor** for unauthorized access

---

## Testing Secrets

Before full deployment, test each integration:

```bash
# Test Gumroad
curl -H "Authorization: Bearer $GUMROAD_ACCESS_TOKEN" \
  https://api.gumroad.com/v2/products

# Test Printify
curl -H "Authorization: Bearer $PRINTIFY_API_TOKEN" \
  https://api.printify.com/v1/shops

# Test Beehiiv
curl -H "Authorization: Bearer $BEEHIIV_API_KEY" \
  https://api.beehiiv.com/v1/publications/$BEEHIIV_PUBLICATION_ID

# Test OCI SSH
ssh -i "$OCI_SSH_KEY" opc@129.146.236.177 "echo 'SSH working'"
```

All should return 200 OK or successful response.

---

## Production Checklist

Before going live:

- [ ] All required secrets added to GitHub
- [ ] Secrets verified (test commands above)
- [ ] Backup secrets stored securely
- [ ] Rotation schedule documented
- [ ] Team members notified of secret locations
- [ ] Monitoring alerts configured
- [ ] Incident response plan ready

---

## Support

If you need help:
1. Check GitHub Actions logs: https://github.com/quantam101/profitenginev5/actions
2. Review error messages in deployment logs
3. Verify secret names match exactly (case-sensitive)
4. Confirm tokens have correct permissions in source systems

---

**Last Updated:** June 20, 2026  
**Status:** Production Ready
