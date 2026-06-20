# Setup Finnhub API for Live Trading

## Quick Setup (2 minutes)

### Step 1: Register for Free Finnhub API
1. Go to: https://finnhub.io/register
2. Sign up with your email
3. Verify email
4. Accept terms

### Step 2: Get Your API Key
1. Log in to Finnhub Dashboard
2. Go to Account Settings / API Keys
3. Copy your API key (free tier available)

### Step 3: Add to .env
Edit your `.env` file and add:
```
FINNHUB_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key from Finnhub dashboard.

### Step 4: Verify Setup
Run this command:
```bash
python deploy_premarket_4am.py
```

You should see:
```
[INFO] PRE-MARKET TRADING SESSION - PAPER TRADING
[INFO] Data Source: Finnhub API (REAL market prices)
[INFO] Starting Balance: $100.00
[INFO] Target Balance: $1,000.00
```

## Why Finnhub?
- **FREE tier**: Up to 60 API calls/minute (more than enough for trading)
- **Real market data**: Stock prices, options, earnings
- **Reliable**: Used by professional traders
- **No credit card**: Free tier doesn't require payment

## API Key Limits (Free Tier)
- 60 API calls per minute
- Quote data: Real-time
- Historical data: Available
- Perfect for autonomous trading with 1-minute scan cycles

## After Setup
Once you add the API key to `.env`, run:
```bash
python deploy_premarket_4am.py
```

The autonomous trading system will:
1. Connect to Finnhub for real market prices
2. Start paper trading with $100
3. Execute trades via 11-strategy hybrid engine
4. Track revenue across all 8 channels
5. Target: Reach $1,000 profit (then rotate API keys)

---

**Estimated time to live:** 5 minutes
