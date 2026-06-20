# Instagram & Threads Secrets Setup

## Required Secrets

### Instagram
```
INSTAGRAM_ACCESS_TOKEN
  Get from: https://developers.facebook.com → Instagram Graph API
  Format: Starts with IGQVJ...
  Scope needed: instagram_business_content_publish
```

```
INSTAGRAM_BUSINESS_ACCOUNT_ID
  Get from: Meta Business Suite → Instagram Account Settings
  Format: Numeric ID (18+ digits)
```

### Threads
```
THREADS_ACCESS_TOKEN
  Get from: https://developers.facebook.com → Threads API
  Format: Starts with IGQVJ... (same token as Instagram)
  Scope needed: threads_publish
```

```
THREADS_USER_ID
  Get from: Threads account settings
  Format: Numeric ID
```

## Setup Steps

### 1. Create Meta App
1. Go to: https://developers.facebook.com
2. Click "Create App"
3. Choose "Consumer" app type
4. Fill in app details
5. Add Instagram Graph API & Threads API products

### 2. Connect Instagram Business Account
1. In app settings, go to Instagram Graph API
2. Add test users or connect business account
3. Get Instagram Business Account ID
4. Generate long-lived access token (60 days)

### 3. Enable Threads API
1. In app settings, go to Threads
2. Enable Threads API
3. Request necessary permissions
4. Get Threads access token

### 4. Add to GitHub Secrets
1. Go to repo Settings → Secrets
2. Add each secret from above
3. Save

## Testing

```bash
# Test Instagram token
curl -H "Authorization: Bearer $INSTAGRAM_ACCESS_TOKEN" \
  https://graph.instagram.com/me

# Test Threads token
curl -H "Authorization: Bearer $THREADS_ACCESS_TOKEN" \
  https://graph.threads.net/me
```

Both should return user info.

