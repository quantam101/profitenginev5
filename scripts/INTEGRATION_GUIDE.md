# ProfitEngine Email List Manager - Integration Guide

This guide shows how to integrate the email list manager into your ProfitEngine v5 backend and frontend.

## Architecture Overview

```
Frontend (Next.js)                 Backend (Go/Python)              Email Services
   ├─ Subscribe form     ────→     Email API Wrapper      ────→    Beehiiv
   ├─ Email preferences  ────→     EmailListManager       ────→    Resend
   ├─ Confirm link       ────→     SQLite Database        ────→    Mailchimp
   └─ Unsubscribe link   ←────     Engagement Tracking    ←────
```

## Backend Integration (FastAPI)

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pydantic requests python-multipart
```

### 2. Create FastAPI App

Create `backend/email_service.py`:

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
import sys

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../scripts'))

from email_api_wrapper import EmailAPIWrapper
from email_integrations import EmailServiceSyncManager

app = FastAPI(
    title="ProfitEngine Email Service",
    description="Email list management and subscriber engagement",
    version="1.0.0"
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize API
email_api = EmailAPIWrapper()

# Request Models
class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str
    interests: Optional[List[str]] = []
    segment: str = "free"

class ConfirmRequest(BaseModel):
    token: str

class TrackOpenRequest(BaseModel):
    email: EmailStr
    campaign_id: str
    user_agent: Optional[str] = ""
    ip_address: Optional[str] = ""

class TrackClickRequest(BaseModel):
    email: EmailStr
    campaign_id: str
    link_url: str
    user_agent: Optional[str] = ""
    ip_address: Optional[str] = ""

class PreferencesRequest(BaseModel):
    email_frequency: Optional[str] = None
    newsletter: Optional[bool] = None
    product_updates: Optional[bool] = None
    promotions: Optional[bool] = None
    account_notifications: Optional[bool] = None

# Subscriber Management Routes

@app.post("/api/email/subscribe")
async def subscribe(request: SubscribeRequest):
    """Subscribe a new email address with double opt-in"""
    return email_api.subscribe(request.dict())

@app.post("/api/email/confirm")
async def confirm(request: ConfirmRequest):
    """Confirm subscription via confirmation token"""
    return email_api.confirm_subscription(request.dict())

@app.post("/api/email/unsubscribe")
async def unsubscribe(token: str):
    """Unsubscribe via token"""
    return email_api.unsubscribe({"token": token})

@app.get("/api/email/subscribers/{email}")
async def get_subscriber(email: str):
    """Get subscriber details"""
    return email_api.get_subscriber(email)

@app.put("/api/email/preferences/{email}")
async def update_preferences(email: str, request: PreferencesRequest):
    """Update subscriber email preferences"""
    return email_api.update_preferences(email, request.dict(exclude_none=True))

@app.post("/api/email/pause/{email}")
async def pause(email: str):
    """Pause subscription"""
    return email_api.pause_subscription(email)

@app.post("/api/email/resume/{email}")
async def resume(email: str):
    """Resume subscription"""
    return email_api.resume_subscription(email)

# Engagement Tracking Routes

@app.post("/api/email/track/open")
async def track_open(request: TrackOpenRequest):
    """Track email open (pixel tracking)"""
    return email_api.track_open(request.dict())

@app.post("/api/email/track/click")
async def track_click(request: TrackClickRequest):
    """Track email click"""
    return email_api.track_click(request.dict())

# Campaign Routes

@app.post("/api/email/campaigns")
async def create_campaign(name: str, subject: str, segment_id: Optional[str] = None):
    """Create an email campaign"""
    return email_api.create_campaign({
        "name": name,
        "subject": subject,
        "segment_id": segment_id
    })

@app.get("/api/email/campaigns/{campaign_id}/stats")
async def campaign_stats(campaign_id: str):
    """Get campaign statistics"""
    return email_api.get_campaign_stats(campaign_id)

# Segment Routes

@app.post("/api/email/segments")
async def create_segment(name: str, segment_type: str, criteria: dict):
    """Create a subscriber segment"""
    return email_api.create_segment({
        "name": name,
        "segment_type": segment_type,
        "criteria": criteria
    })

@app.get("/api/email/subscribers")
async def get_subscribers(segment: Optional[str] = None, limit: int = 1000):
    """Get active subscribers"""
    return email_api.get_active_subscribers(segment, limit)

# Lead Magnet Routes

@app.post("/api/email/lead-magnets")
async def add_magnet(name: str, description: str, file_url: str):
    """Add a lead magnet"""
    return email_api.add_lead_magnet({
        "name": name,
        "description": description,
        "file_url": file_url
    })

@app.post("/api/email/lead-magnets/download")
async def track_download(lead_magnet_id: str, email: Optional[str] = None, subscriber_id: Optional[str] = None):
    """Track lead magnet download"""
    return email_api.track_magnet_download({
        "lead_magnet_id": lead_magnet_id,
        "email": email,
        "subscriber_id": subscriber_id
    })

# Referral Routes

@app.post("/api/email/referrals")
async def create_referral(referrer_id: str, referred_email: EmailStr):
    """Create a referral link"""
    return email_api.create_referral({
        "referrer_id": referrer_id,
        "referred_email": referred_email
    })

# Analytics Routes

@app.get("/api/email/metrics")
async def get_metrics():
    """Get overall email metrics"""
    return email_api.get_metrics()

@app.get("/api/email/export")
async def export_subscribers(segment: Optional[str] = None, format: str = "json"):
    """Export subscribers for integration with email services"""
    return email_api.export_subscribers(segment, format)

# Health Check

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "email-manager"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. Run the Service

```bash
# Development
python backend/email_service.py

# Production (with Gunicorn)
gunicorn -w 4 -b 0.0.0.0:8000 backend.email_service:app
```

## Frontend Integration (Next.js)

### 1. Create Email Service Hook

Create `lib/useEmailService.ts`:

```typescript
import { useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface SubscribePayload {
  email: string;
  name: string;
  interests?: string[];
  segment?: string;
}

interface TrackOpenPayload {
  email: string;
  campaign_id: string;
  user_agent?: string;
}

interface PreferencesPayload {
  email_frequency?: string;
  newsletter?: boolean;
  product_updates?: boolean;
  promotions?: boolean;
  account_notifications?: boolean;
}

export const useEmailService = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const subscribe = async (payload: SubscribePayload) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Subscription failed');
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const confirm = async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const trackOpen = async (payload: TrackOpenPayload) => {
    try {
      await fetch(`${API_BASE_URL}/api/email/track/open`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      console.error('Failed to track open:', err);
    }
  };

  const updatePreferences = async (email: string, prefs: PreferencesPayload) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/email/preferences/${email}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      });
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.message);
      }
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    subscribe,
    confirm,
    trackOpen,
    updatePreferences,
    loading,
    error,
  };
};
```

### 2. Create Newsletter Signup Component

Create `components/NewsletterSignup.tsx`:

```typescript
import React, { useState } from 'react';
import { useEmailService } from '@/lib/useEmailService';

export default function NewsletterSignup() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const { subscribe, loading, error } = useEmailService();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await subscribe({
        email,
        name,
        interests: ['investing', 'passive-income'],
        segment: 'free',
      });
      setSubmitted(true);
      setEmail('');
      setName('');
    } catch (err) {
      console.error('Signup failed:', err);
    }
  };

  if (submitted) {
    return (
      <div className="bg-green-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-green-900">Thanks for subscribing!</h3>
        <p className="text-green-700">Check your email to confirm your subscription.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        type="text"
        placeholder="Your name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        className="w-full px-4 py-2 border rounded-lg"
      />
      <input
        type="email"
        placeholder="your@email.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="w-full px-4 py-2 border rounded-lg"
      />
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Subscribing...' : 'Subscribe to Newsletter'}
      </button>
    </form>
  );
}
```

### 3. Add Confirmation Page

Create `pages/email/confirm.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useEmailService } from '@/lib/useEmailService';

export default function ConfirmEmail() {
  const router = useRouter();
  const { confirm, loading, error } = useEmailService();
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    const token = router.query.token as string;
    if (token) {
      confirm(token)
        .then(() => setConfirmed(true))
        .catch(() => {});
    }
  }, [router.query.token, confirm]);

  if (loading) {
    return <div className="text-center py-12">Confirming your subscription...</div>;
  }

  if (confirmed) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold text-green-600">Subscription Confirmed!</h1>
        <p className="text-gray-600 mt-2">Welcome to our newsletter.</p>
      </div>
    );
  }

  return (
    <div className="text-center py-12">
      <h1 className="text-2xl font-bold text-red-600">Confirmation Failed</h1>
      <p className="text-gray-600 mt-2">{error || 'Invalid or expired confirmation link.'}</p>
    </div>
  );
}
```

## Email Service Integration

### 1. Beehiiv Setup

```python
import os
from email_integrations import BeehiivIntegration

# Get API key from Beehiiv (Account → API Keys)
api_key = os.getenv("BEEHIIV_API_KEY")
beehiiv = BeehiivIntegration(api_key)

# Export subscribers from local database
from email_list_manager import EmailListManager
manager = EmailListManager()
subscribers = manager.export_subscribers(export_format="json")

# Import to Beehiiv
success, msg = beehiiv.import_subscribers(json.loads(subscribers))
print(f"Beehiiv sync: {msg}")
```

### 2. Resend Setup

```python
import os
from email_integrations import ResendIntegration

api_key = os.getenv("RESEND_API_KEY")
audience_id = os.getenv("RESEND_AUDIENCE_ID")

resend = ResendIntegration(api_key)

# Send a campaign
success, msg, campaign_id = resend.send_campaign(
    campaign_name="Weekly Update",
    audience_id=audience_id,
    subject="Your Weekly Digest",
    html_content="<h1>Welcome</h1>"
)
print(f"Campaign sent: {campaign_id}")
```

### 3. Mailchimp Setup

```python
import os
from email_integrations import MailchimpIntegration

api_key = os.getenv("MAILCHIMP_API_KEY")
list_id = os.getenv("MAILCHIMP_LIST_ID")
server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX", "us1")

mailchimp = MailchimpIntegration(api_key, server_prefix)

# Sync subscribers
success, msg = mailchimp.sync_list(list_id, subscribers_data)
print(f"Mailchimp sync: {msg}")
```

## Email Tracking Integration

### 1. Pixel Tracking in Email Template

```html
<!-- Add to end of email body -->
<img src="https://api.alreadyherellc.com/api/email/track/open?email=user@example.com&campaign_id=campaign-123" 
     width="1" height="1" alt="" />
```

### 2. Click Tracking with Redirects

```html
<!-- Wrap links -->
<a href="https://api.alreadyherellc.com/api/email/track/click?email=user@example.com&campaign_id=campaign-123&link_url=https://alreadyherellc.com/article">
  Read Article
</a>
```

## Database Migration

### PostgreSQL Migration

Replace SQLite with PostgreSQL in production:

```python
# Change connection string
manager = EmailListManager(
    db_path="postgresql://user:password@localhost/profitengine"
)
```

Schema is fully portable.

## Deployment Checklist

- [ ] Environment variables configured (.env)
- [ ] Database migrations run
- [ ] Email service API keys added
- [ ] Frontend API URL configured
- [ ] CORS allowed origins configured
- [ ] SSL/HTTPS enabled
- [ ] Rate limiting configured
- [ ] Monitoring/logging enabled
- [ ] Backup strategy implemented
- [ ] Load testing completed

## Support

For questions or issues:
1. Check logs: `tail -f logs/email_manager.log`
2. Test API: `curl -X GET http://localhost:8000/health`
3. Review configuration: Verify all environment variables
4. Check database: `sqlite3 profitengine_subscribers.db ".tables"`
