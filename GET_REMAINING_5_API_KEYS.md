# GET REMAINING 5 API KEYS (15 minutes)

**You have**: ✅ GUMROAD_API_TOKEN, ✅ OPENAI_API_KEY  
**You need**: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, REPLICATE_API_TOKEN, ELEVEN_LABS_API_KEY, KLAVIYO_API_KEY

---

## 1️⃣ INSTAGRAM ACCESS TOKEN + BUSINESS ACCOUNT ID (5 min)

### Get Instagram Access Token:

1. Go to: https://developers.facebook.com
2. Create/Select your app
3. Go to "Settings" → "Basic"
4. Copy `App ID` and `App Secret`
5. Go to "Roles" → "Test Users"
6. Create test user or use existing
7. Go to "Instagram" → "Basic Display"
8. Click "Get Started"
9. Select your Instagram Business Account
10. Approve permissions
11. Copy the **User Access Token**

### Get Instagram Business Account ID:

Run this command with your token:
```bash
curl "https://graph.instagram.com/me?fields=ig_user_id&access_token=YOUR_ACCESS_TOKEN"
```

You'll get:
```json
{
  "ig_user_id": "1234567890",
  "id": "1234567890"
}
```

Copy the `ig_user_id` value.

**Add to GitHub:**
```bash
gh secret set INSTAGRAM_ACCESS_TOKEN --body "YOUR_TOKEN"
gh secret set INSTAGRAM_BUSINESS_ACCOUNT_ID --body "YOUR_ID"
```

---

## 2️⃣ REPLICATE API TOKEN (2 min)

1. Go to: https://replicate.com/account/api-tokens
2. Create new API token
3. Copy it

**Add to GitHub:**
```bash
gh secret set REPLICATE_API_TOKEN --body "YOUR_TOKEN"
```

---

## 3️⃣ ELEVEN LABS API KEY (2 min)

1. Go to: https://elevenlabs.io/account/api-keys
2. Create new API key
3. Copy it

**Add to GitHub:**
```bash
gh secret set ELEVEN_LABS_API_KEY --body "YOUR_KEY"
```

---

## 4️⃣ KLAVIYO API KEY (2 min)

1. Go to: https://www.klaviyo.com/account/api-keys
2. Create new API key (Private)
3. Copy it

**Add to GitHub:**
```bash
gh secret set KLAVIYO_API_KEY --body "YOUR_KEY"
```

---

## ✅ VERIFICATION

After adding all 5, verify with:
```bash
gh secret list
```

Should show 7 total:
- [ ] GUMROAD_API_TOKEN ✅
- [ ] OPENAI_API_KEY ✅
- [ ] INSTAGRAM_ACCESS_TOKEN
- [ ] INSTAGRAM_BUSINESS_ACCOUNT_ID
- [ ] REPLICATE_API_TOKEN
- [ ] ELEVEN_LABS_API_KEY
- [ ] KLAVIYO_API_KEY

---

## 🚀 THEN COMPLETE SETUP

Once all 7 secrets are in GitHub:

1. **Add to Vercel:**
   Go to: https://vercel.com/quantam101/profitenginev5/settings/environment-variables
   Add same 7 variables (Production + Preview + Development)

2. **Trigger automation:**
   ```bash
   gh workflow run automation.yml
   ```

3. **Watch it run:**
   ```bash
   gh run list
   gh run watch <run-id>
   ```

---

## 📋 QUICK CHECKLIST

Services to set up (in order):

### Instagram (5 min)
- [ ] Go to developers.facebook.com
- [ ] Create/select app
- [ ] Generate access token
- [ ] Get Business Account ID
- [ ] Add both to GitHub

### Replicate (2 min)
- [ ] Go to replicate.com/account
- [ ] Create API token
- [ ] Add to GitHub

### Eleven Labs (2 min)
- [ ] Go to elevenlabs.io/account
- [ ] Create API key
- [ ] Add to GitHub

### Klaviyo (2 min)
- [ ] Go to klaviyo.com/account
- [ ] Create API key
- [ ] Add to GitHub

### Vercel (3 min)
- [ ] Add all 7 to Vercel env vars
- [ ] Apply to Production/Preview/Development

### Trigger (1 min)
- [ ] Run `gh workflow run automation.yml`
- [ ] Watch automation execute

**Total time: 15 minutes**

---

## 🎯 AFTER COMPLETION

Automation will automatically:
- ✅ Upload 5 products to Gumroad (daily)
- ✅ Generate & post Instagram carousels (3x weekly)
- ✅ Generate & post Instagram reels (daily)
- ✅ Generate & post 3 daily stories
- ✅ Trigger email sequences
- ✅ Track all metrics

**Revenue starts flowing immediately.**
