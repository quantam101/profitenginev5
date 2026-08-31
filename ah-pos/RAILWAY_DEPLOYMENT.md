# Railway.app Deployment — Dead Simple

**Cost:** Free tier ($5/month usage, usually free)  
**Setup Time:** 10 minutes  
**Complexity:** Minimal (one-click deployment)

---

## Step 1: Create Railway Account (2 minutes)

1. Go to **https://railway.app**
2. Click **"Start for Free"**
3. Sign in with **GitHub** (authorize)
4. Done

---

## Step 2: Create New Project (3 minutes)

1. Click **"Create Project"**
2. Select **"Deploy from GitHub repo"**
3. **Authorize Railway** to access your GitHub repos
4. Select **`profitenginev5`** repo
5. Click **"Deploy"**

Railway will automatically:
- ✅ Detect Next.js frontend
- ✅ Create PostgreSQL database
- ✅ Set up environment variables
- ✅ Deploy to production

**Wait 2-3 minutes for deployment to complete.**

---

## Step 3: Configure Environment Variables (2 minutes)

Railway auto-detects most variables, but you need to set:

1. Go to **Project Settings** → **Variables**
2. Add these:

```
DATABASE_URL=                             # Railway PostgreSQL URL (auto-filled)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=     # pk_test_... from Stripe Dashboard
NEXT_PUBLIC_STRIPE_PRICING_TABLE_ID=    # pricing table ID from Stripe Dashboard
STRIPE_SECRET_KEY=                      # sk_test_... from Stripe Dashboard
PROFITENGINE_WEBHOOK_TOKEN=             # generate with: openssl rand -hex 32
RUNTIME_API_URL=                        # e.g. https://profitengine-runtime.onrender.com
```

**Get these from:**
- `DATABASE_URL` → Railway PostgreSQL connection (auto-shown)
- Stripe keys → Stripe Dashboard settings
- Custom tokens → Generate in your admin panel

---

## Step 4: Deploy AH-POS Backend (5 minutes)

Railway auto-deploys the Next.js frontend, but you need to deploy the Python backend separately.

### Option A: Deploy Backend as Service (Recommended)

1. In Railway project, click **"New Service"**
2. Select **"GitHub repo"**
3. Select same **`profitenginev5`** repo
4. In settings, configure:
   - **Root Directory:** `ah-pos`
   - **Start Command:** `python backend/scrape_sam_gov.py`
   - **Runtime:** Python 3.11

5. Click **"Deploy"**

### Option B: Use Railway Cron (Scheduled Syncs)

1. Go to **Railway** → **Create new service**
2. Select **"Cron Job"**
3. **Schedule:** `0 6,12,18 * * *` (06:00, 12:00, 18:00 UTC)
4. **Command:** `python backend/scrape_sam_gov.py`
5. Deploy

---

## Step 5: Initialize Database (2 minutes)

Railway creates empty PostgreSQL. Initialize schema:

1. Get database connection from Railway dashboard
2. Run locally:

```bash
psql postgresql://postgres:PASSWORD@DB_HOST:5432/ah_pos < database/00_init_schema.sql
```

Or via Railway CLI:

```bash
railway shell
psql < database/00_init_schema.sql
```

---

## Step 6: Verify Deployment (1 minute)

1. Go to **Railway** → **Deployments**
2. Check status: **"Live"** (green)
3. Click **Domains** to get your live URL
4. Test: `https://your-domain.railway.app`

---

## Complete Setup Checklist

```
□ Railway account created
□ GitHub repo connected
□ Next.js frontend deployed (auto)
□ PostgreSQL created (auto)
□ Environment variables set
□ Backend service deployed
□ Database schema initialized
□ Sample data imported
□ SAM.gov scraper tested
□ Daily cron jobs running
□ System live at railway.app URL
```

---

## What You Get

✅ **Live Frontend** — Next.js on Railway  
✅ **Live Database** — PostgreSQL managed  
✅ **Live Backend** — Python scraper running  
✅ **Auto-Deploy** — Push to GitHub → Auto-deploys  
✅ **Daily Syncs** — Cron jobs run automatically  
✅ **24/7 Uptime** — Railway handles it  
✅ **Free Forever** — Under $5/month usage  

---

## Monitoring

### Check Logs
```
Railway Dashboard → Logs → View real-time output
```

### Check Database
```
Railway Dashboard → PostgreSQL → Connect
```

### Check Deployments
```
Railway Dashboard → Deployments → View status
```

---

## Cost

| Item | Cost |
|------|------|
| Compute | Free (generous quota) |
| PostgreSQL | Free (up to 1GB) |
| Bandwidth | Free |
| **Total** | **$0/month** (or $5+ if you scale) |

---

## Auto-Deploy on Git Push

Once deployed, **every push to `main` auto-deploys:**

```bash
git add .
git commit -m "Update AH-POS"
git push origin main
# Railway auto-deploys within 1-2 minutes
```

No manual deployment needed ever again!

---

## Troubleshooting

### Deployment failed
```
Check: Railway Logs → Look for error message
Usually: Missing environment variable or database connection
```

### Database empty
```
Run schema initialization (Step 5)
psql postgresql://user:pass@host/db < database/00_init_schema.sql
```

### Scraper not running
```
Check: Railway Cron Job status
Verify: DATABASE_URL is set correctly
```

### Frontend shows 500 error
```
Check: Next.js environment variables
Check: Backend service is running
```

---

## Next Steps

1. ✅ Create Railway account (2 min)
2. ✅ Deploy from GitHub (5 min)
3. ✅ Initialize database (2 min)
4. ✅ System live (1 min)

**Total: 10 minutes to production!**

---

## Your URLs After Deployment

```
Frontend:  https://your-app.railway.app
Database:  postgres://user:pass@host:5432/ah_pos
Logs:      railway.app/project/logs
```

---

**Ready? Go to railway.app and click "Start for Free"** 🚀
