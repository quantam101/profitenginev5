# OCI Caddy SSL Configuration for api.profitengine.alreadyherellc.com
**Deployment Instructions for 129.146.236.177**

---

## STEP 1: Update DNS (Do This FIRST)
**This must complete before Caddy SSL will work**

### Option A: Via Domain Registrar Panel (Most Common)
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Find DNS settings for `alreadyherellc.com`
3. Update the A record:
   - **Name**: `api.profitengine` (or `api.profitengine.alreadyherellc.com`)
   - **Type**: A
   - **Value**: `129.146.236.177`
   - **TTL**: 300 (5 minutes for faster propagation)
4. Save changes
5. Wait 5-15 minutes for propagation

### Option B: Verify DNS is Updated
```bash
# Run from your local machine:
nslookup api.profitengine.alreadyherellc.com
# Should show: Address: 129.146.236.177
```

---

## STEP 2: SSH to OCI Server
```bash
ssh opc@129.146.236.177
```

---

## STEP 3: Check Current Caddy Installation
```bash
# Check if Caddy is installed
which caddy
# Should output: /usr/bin/caddy or /opt/caddy/caddy

# Check Caddy version
caddy version

# Check if Caddy is running
sudo systemctl status caddy

# Check current Caddyfile location
sudo cat /etc/caddy/Caddyfile
# OR
sudo cat /opt/caddy/Caddyfile
# OR find it:
sudo find / -name "Caddyfile" 2>/dev/null
```

---

## STEP 4: Update Caddyfile

### Location Detection
Caddy typically stores config at one of:
- `/etc/caddy/Caddyfile`
- `/opt/caddy/Caddyfile`
- Custom path from systemd service: `sudo systemctl cat caddy | grep ExecStart`

### Backup Current Config
```bash
CADDY_FILE=$(sudo find / -name "Caddyfile" -type f 2>/dev/null | head -1)
sudo cp "$CADDY_FILE" "${CADDY_FILE}.backup.$(date +%s)"
echo "Backup: ${CADDY_FILE}.backup.*"
```

### Add This Configuration
**Option A: Append to existing Caddyfile (if it exists)**
```bash
sudo tee -a /etc/caddy/Caddyfile << 'EOF'

# ===== ProfitEngine API Gateway =====
api.profitengine.alreadyherellc.com:443 {
    # Reverse proxy to local backend API
    reverse_proxy localhost:8001

    # Compression
    encode gzip

    # Security headers
    header -Server
    header X-Real-IP {http.request.remote.host}
    header X-Forwarded-For {http.request.header.X-Forwarded-For}
    header X-Forwarded-Proto "https"
    header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
    
    # Access logging (optional)
    log {
        output file /var/log/caddy/api.profitengine.log
        format json
    }

    # Health check endpoint passthrough
    uri /health* / /api/health*
}

# Also handle HTTP → HTTPS redirect
api.profitengine.alreadyherellc.com:80 {
    redir https://{host}{uri} permanent
}
EOF
```

**Option B: Create New Caddyfile (if none exists)**
```bash
sudo mkdir -p /etc/caddy
sudo tee /etc/caddy/Caddyfile << 'EOF'
# ProfitEngine API Gateway

api.profitengine.alreadyherellc.com:443 {
    reverse_proxy localhost:8001
    encode gzip
    header X-Real-IP {http.request.remote.host}
    header X-Forwarded-For {http.request.header.X-Forwarded-For}
    header X-Forwarded-Proto "https"
    header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    header X-Content-Type-Options "nosniff"
    header X-Frame-Options "DENY"
}

api.profitengine.alreadyherellc.com:80 {
    redir https://{host}{uri} permanent
}
EOF
```

### Verify Caddyfile Syntax
```bash
sudo caddy validate --config /etc/caddy/Caddyfile
# Should output: valid configuration
```

---

## STEP 5: Reload Caddy

### Option A: Using Systemd (Recommended)
```bash
# Reload without downtime
sudo systemctl reload caddy

# Check status
sudo systemctl status caddy

# Watch logs
sudo journalctl -u caddy -f
```

### Option B: Using Caddy CLI
```bash
# If running as systemd service, use reload above
# If running standalone, use:
caddy reload --config /etc/caddy/Caddyfile
```

### Option C: Restart (if reload fails)
```bash
sudo systemctl restart caddy
sleep 3
sudo systemctl status caddy
```

---

## STEP 6: Verify SSL Certificate
```bash
# Check certificate was issued
sudo caddy list-certs

# Should show:
# - api.profitengine.alreadyherellc.com
# - Issuer: Let's Encrypt
# - Expires: [future date]

# View detailed cert info
echo | openssl s_client -servername api.profitengine.alreadyherellc.com -connect 129.146.236.177:443 2>/dev/null | openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not Before|Not After"
```

---

## STEP 7: Test Connectivity

### From OCI Server (local test)
```bash
curl -v https://api.profitengine.alreadyherellc.com/
# Expected: 200 OK or connection to localhost:8001
```

### From Remote Machine
```bash
# Test basic connectivity
curl -v https://api.profitengine.alreadyherellc.com/

# Test health endpoint (if available)
curl -s https://api.profitengine.alreadyherellc.com/api/health | jq .

# Test with headers
curl -I https://api.profitengine.alreadyherellc.com/

# Should see:
# HTTP/2 200 OK
# server: Caddy
# x-real-ip: [your-ip]
```

---

## STEP 8: Verify Backend Service
```bash
# Check if backend API is running on port 8001
sudo netstat -tlnp | grep 8001
# Or:
sudo ss -tlnp | grep 8001

# Should show: LISTEN ... 127.0.0.1:8001 or 0.0.0.0:8001

# Test backend directly
curl http://localhost:8001/
# Should get 200 or relevant API response
```

---

## TROUBLESHOOTING

### Issue: "Certificate not issued" or 404 errors
**Cause**: DNS hasn't propagated yet or domain is still pointing to wrong IP
**Fix**:
```bash
# Wait 5-15 minutes
# Verify DNS:
nslookup api.profitengine.alreadyherellc.com
# Must show: 129.146.236.177

# Then reload Caddy:
sudo systemctl reload caddy
```

### Issue: "Connection refused" or "No route to host"
**Cause**: DNS update incomplete or firewall blocking
**Fix**:
```bash
# Check firewall rules on OCI
sudo firewall-cmd --list-all
# Port 443 should be open

# If closed, open it:
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### Issue: Reverse proxy errors (502 Bad Gateway)
**Cause**: Backend API not running on localhost:8001
**Fix**:
```bash
# Verify backend is listening
curl http://localhost:8001/api/health

# If not responding, start the service:
# (depends on your deployment - could be systemd service, Docker, etc.)
ps aux | grep 8001
ps aux | grep api
ps aux | grep backend
```

### Issue: Certificate renewal failing
**Cause**: Let's Encrypt validation failing (rare with Caddy)
**Fix**:
```bash
# Check logs
sudo journalctl -u caddy -n 50

# Force renewal (if needed):
sudo caddy stop
sudo caddy start --config /etc/caddy/Caddyfile
```

---

## VERIFICATION CHECKLIST

After deployment, verify all these pass:

- [ ] DNS resolves to 129.146.236.177: `nslookup api.profitengine.alreadyherellc.com`
- [ ] Caddy is running: `sudo systemctl status caddy`
- [ ] Caddyfile is valid: `sudo caddy validate --config /etc/caddy/Caddyfile`
- [ ] SSL cert exists: `sudo caddy list-certs | grep api.profitengine`
- [ ] Port 443 is open: `sudo ss -tlnp | grep 443`
- [ ] Backend is responsive: `curl http://localhost:8001/`
- [ ] Reverse proxy works locally: `curl https://api.profitengine.alreadyherellc.com/`
- [ ] Remote test passes: `curl -I https://api.profitengine.alreadyherellc.com/` (from another machine)

---

## TIMELINE

| Step | Time | Blocking |
|------|------|----------|
| 1. DNS Update | 5-15 min | YES - do first |
| 2-4. SSH & Caddy Config | 5 min | NO - depends on DNS |
| 5. Reload Caddy | <1 min | NO |
| 6-7. Verify & Test | 5 min | NO |
| **TOTAL** | **20-25 min** | — |

---

## AFTER VERIFICATION

Once all tests pass, notify the team:

```bash
# From OCI server, test one final time:
curl -s https://api.profitengine.alreadyherellc.com/api/health | jq .

# Should return 200 with valid JSON
# Example: {"status": "ok", "uptime": 12345}
```

Then update your `.env` file to use the new domain if needed:
```bash
# Already configured as:
RUNTIME_API_URL=https://api.profitengine.alreadyherellc.com
# ✅ Ready for TokenForge conversions
```

---

**Next**: Test TokenForge paid conversion flow end-to-end
- POST `/api/tokenforge/checkout`
- Verify Stripe webhook integration
- Monitor payment processing logs

---

*Generated by: Claude Code Agent*  
*For: ProfitEngine v5 | OCI Backend (cmdos at 129.146.236.177)*
