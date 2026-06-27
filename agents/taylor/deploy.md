# Taylor — Already Here LLC AI Voice Agent
## Production Deployment Guide

---

### What Taylor does
Answers every inbound call to Already Here LLC 24/7.
Handles two tasks: appointment scheduling and invoice payment collection.
Transfers to your cell phone (602-882-2920) for anything outside that scope.

---

### Architecture
```
Inbound call → Twilio (primary) / Telnyx (backup)
             → Retell AI (primary) / Vapi (backup)
             → Taylor server.py (tool execution)
             → Stripe (payment) + SQLite (appointments)
             → SMS confirmation via Twilio
```

---

### Step 1 — Get accounts (30 minutes total)

| Service | URL | Cost | Purpose |
|---|---|---|---|
| Twilio | console.twilio.com | ~$1/mo + usage | Primary phone number |
| Telnyx | telnyx.com | ~$1/mo + usage | Backup phone number |
| Retell AI | retellai.com | Pay per minute | Primary voice AI |
| Vapi | vapi.ai | Pay per minute | Backup voice AI |
| Stripe | dashboard.stripe.com | 2.9% + 30¢ | Already set up |

---

### Step 2 — Configure Twilio (15 min)

1. Buy a Phoenix AZ number at console.twilio.com (~$1/month)
2. Phone Numbers → Manage → Configure your number
3. Set webhook: `POST https://your-server.com/retell/webhook`
4. Enable "Call Status Callbacks" pointing to same URL

---

### Step 3 — Configure Retell AI (10 min)

1. Create account at retellai.com
2. Create Agent → paste system prompt from `system_prompt.py`
3. Add tools from `tools.py` (copy each JSON block)
4. Set TTS: Cartesia Sonic v3.5
5. Set Voice Activity Detection: 180ms
6. Set barge-in sensitivity: 0.98
7. Set webhook URL: `https://your-server.com/retell/webhook`
8. Copy agent ID → put in `.env` as RETELL_AGENT_ID

---

### Step 4 — Deploy Taylor server (5 min)

Option A — Local (your machine):
```bash
pip install fastapi uvicorn aiohttp stripe
cd agents/taylor
cp .env.example .env
# Fill in all values
python server.py
# Server starts on port 8001
```

Option B — OCI server (recommended — always on):
```bash
ssh opc@129.146.236.177
cd /opt/already-here
git pull
pip install fastapi uvicorn aiohttp stripe
cd agents/taylor
cp .env.example .env && nano .env
pm2 start server.py --name taylor --interpreter python3
pm2 save
```

Option C — Vercel (serverless):
Deploy as a Python serverless function at profitengine-tau.vercel.app/api/taylor

---

### Step 5 — Configure Telnyx + Vapi backup (10 min)

1. Buy a Telnyx number at telnyx.com
2. Create a Vapi assistant with same system prompt
3. Configure Telnyx to forward to Vapi webhook URL
4. Add both to `.env`

Failover is automatic — `failover.py` probes both services every 30 seconds.
If Retell/Twilio fails → switches to Vapi/Telnyx in under 120ms.
If both fail → reads local script + transfers to 602-882-2920.

---

### Step 6 — Test

```bash
# Test calendar tool
curl -X POST http://localhost:8001/tool/check_calendar_availability \
  -H "Content-Type: application/json" \
  -d '{"target_date": "2026-06-10", "service_type": "audit"}'

# Test payment init
curl -X POST http://localhost:8001/tool/initialize_stripe_payment \
  -H "Content-Type: application/json" \
  -d '{"amount_in_cents": 35000, "billing_zip": "85378"}'

# Health check
curl http://localhost:8001/health
```

---

### Stripe payment link alternative (zero-code, works immediately)

While Taylor is being deployed, use Stripe Payment Links in every email:
- Network Audit: stripe.com/pay → create $350 one-time link
- IT Retainer Bronze: $199/month recurring link
- Share these links in every outreach email until Taylor is live

---

### Cost estimate

| Item | Monthly |
|---|---|
| Twilio number + usage (100 calls) | ~$8 |
| Telnyx backup | ~$3 |
| Retell AI (100 min @ $0.05/min) | ~$5 |
| Vapi backup | ~$3 |
| **Total** | **~$19/month** |

Taylor answers calls 24/7, books appointments into the database, collects payments via Stripe, and sends SMS confirmations — for $19/month.
