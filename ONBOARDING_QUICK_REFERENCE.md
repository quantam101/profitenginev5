# ProfitEngine Onboarding System - Quick Reference

## 60-Second Setup

```bash
# 1. Install email provider library
npm install nodemailer

# 2. Generate secret
export NEXTAUTH_SECRET=$(openssl rand -base64 32)

# 3. Set email (choose one)
export SENDGRID_API_KEY="SG.your-key"        # OR
export GMAIL_USER="your@gmail.com" GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# 4. Start
npm run dev

# 5. Visit
open http://localhost:3000/trading-signup
```

## Files at a Glance

| File | Purpose | Lines |
|------|---------|-------|
| `app/trading-signup/page.tsx` | Landing + signup | 562 |
| `app/trading-signup/kyc/page.tsx` | KYC form | 526 |
| `app/trading-signup/kyc-status/page.tsx` | Status page | 297 |
| `app/api/auth/signup/route.ts` | Signup API | 111 |
| `app/api/kyc/submit/route.ts` | KYC API | 128 |
| `app/api/kyc/status/route.ts` | Status API | 76 |
| `lib/auth-utils.ts` | Auth functions | 113 |
| `lib/email-service.ts` | Email sending | 216 |
| `lib/emails/welcome.tsx` | Email template | 261 |
| **Total** | | **2,290** |

## User Flow

```
Landing Page (/trading-signup)
    ↓ [Hero + Features + CTA]
    ↓
Signup Form (/trading-signup)
    ↓ [Email, Password, Capital, Risk]
    ↓ [Validation + DB Save + Email Send]
    ↓
Success + KYC Intro (/trading-signup/kyc)
    ↓ [Start KYC Button]
    ↓
KYC Form (/trading-signup/kyc)
    ↓ [Name, Age, Experience, Goals]
    ↓ [Validation + Email Send]
    ↓
Status Page (/trading-signup/kyc-status)
    ↓ [Pending/Approved/Rejected]
    ↓ [Next Steps]
    ↓
Dashboard (/command-center)
```

## API Endpoints

### POST /api/auth/signup
```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123",
    "capitalAmount": 5000,
    "riskPreference": "moderate",
    "agreeToTerms": true
  }'

# Response: { success, token, user }
```

### POST /api/kyc/submit
```bash
curl -X POST http://localhost:3000/api/kyc/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "age": 35,
    "tradingExperience": "intermediate",
    "riskTolerance": "moderate",
    "investmentGoals": "Generate passive income",
    "agreeToTerms": true
  }'

# Response: { success, user }
```

### GET /api/kyc/status
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/kyc/status

# Response: { status, message, submittedAt, nextSteps }
```

## Form Fields

### Signup
- **Email**: Valid format, unique
- **Password**: 8+ chars, uppercase, lowercase, number
- **Capital**: $1,000+ (paper trading)
- **Risk**: conservative | moderate | aggressive

### KYC
- **First/Last Name**: Required text
- **Age**: 18+ required
- **Experience**: beginner | intermediate | advanced
- **Risk Tolerance**: low | moderate | high
- **Goals**: Required text (100+ chars)

## Auth Token

```typescript
import { generateAuthToken, verifyAuthToken } from '@/lib/auth-utils';

// Generate (7-day expiration)
const token = generateAuthToken(userId, email);

// Verify
const decoded = verifyAuthToken(token);
// { userId, email } or null if invalid/expired
```

## Email Providers

### SendGrid (Recommended)
```env
SENDGRID_API_KEY=SG.xxxxx
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
```

### Gmail
```env
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
```

### Custom SMTP
```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=username
SMTP_PASSWORD=password
```

## Database

```typescript
import { ClientsDB } from '@/lib/clients-db';

const db = new ClientsDB();

// Create user
const user = db.createUser(email, 'free');

// Get user
const user = db.getUser(userId);
const user = db.getUserByEmail(email);

// Update activity
db.updateUserActivity(userId);

db.close();
```

## Email Sending

```typescript
import { sendWelcomeEmail } from '@/lib/email-service';

await sendWelcomeEmail({
  email: 'user@example.com',
  username: 'john',
  capitalAmount: 5000,
  riskPreference: 'moderate',
});
```

## Validation

```typescript
import { 
  validateEmail, 
  validatePassword 
} from '@/lib/auth-utils';

// Email
validateEmail('user@example.com')  // true
validateEmail('invalid')            // false

// Password
validatePassword('weak')            // "Password must be..."
validatePassword('Password123')     // null (valid)
```

## Environments

### Development
```env
NEXTAUTH_SECRET=dev-secret
NEXTAUTH_URL=http://localhost:3000
SENDGRID_API_KEY=test
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### Staging
```env
NEXTAUTH_SECRET=staging-secret
NEXTAUTH_URL=https://staging-app.profitengine.alreadyherellc.com
SENDGRID_API_KEY=SG.staging-key
NEXT_PUBLIC_SITE_URL=https://staging-app.profitengine.alreadyherellc.com
```

### Production
```env
NEXTAUTH_SECRET=strong-random-secret
NEXTAUTH_URL=https://app.profitengine.alreadyherellc.com
SENDGRID_API_KEY=SG.production-key
NEXT_PUBLIC_SITE_URL=https://app.profitengine.alreadyherellc.com
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=yyy
```

## Deployment

### Vercel
```bash
vercel env add NEXTAUTH_SECRET
vercel env add SENDGRID_API_KEY
# ... add other vars
git push origin main  # Auto-deploys
```

### Self-Hosted
```bash
npm run build
npm run start
# Configure Caddy/Nginx proxy to localhost:3000
```

## Testing

### Quick Test
```bash
# Start server
npm run dev

# In browser, visit:
# http://localhost:3000/trading-signup

# Fill form:
# Email: test@example.com
# Password: TestPass123
# Capital: 5000
# Risk: moderate
# Terms: check

# Should see success message
# Check email (SendGrid/Gmail inbox or spam)
```

### Check Email Received
- **SendGrid**: Dashboard → Activity Feed or check inbox
- **Gmail**: Login to test account and check inbox/spam
- **Ethereal**: Automatic preview link in logs

## Common Errors

### "Email already registered"
- Email is in database
- Check: `SELECT * FROM users WHERE email = 'xxx'`

### "Password must be at least 8 characters"
- Password too short or missing requirements
- Example good password: `MyPassword123`

### "Capital amount must be at least $1,000"
- Amount below $1,000
- Minimum is $1,000

### Email not sending
- Check SENDGRID_API_KEY is set
- Verify sender domain in SendGrid
- Check spam folder
- View logs: `npm run dev 2>&1 | grep -i email`

### Token invalid/expired
- Token valid for 7 days only
- Refresh by re-logging in
- Clear localStorage if needed

## Performance Targets

| Operation | Target | How |
|-----------|--------|-----|
| Signup API | <200ms | Optimized DB query |
| Email send | <2s | Async, doesn't block |
| KYC API | <150ms | Minimal DB operations |
| Page load | <1s | Vercel CDN, optimized assets |

## Security Checklist

- [x] Password strength validation
- [x] Email format validation  
- [x] Token signing (HMAC-SHA256)
- [x] Token expiration (7 days)
- [x] No passwords logged
- [x] Environment variable secrets
- [x] HTTPS enforced (Vercel/self-hosted)
- [ ] Email verification workflow (optional)
- [ ] KYC automation (future)
- [ ] 2FA support (with NextAuth)

## Documentation Files

| File | Purpose |
|------|---------|
| `ONBOARDING_README.md` | Overview & quick reference |
| `ONBOARDING_FLOW.md` | Complete flow & specifications |
| `ONBOARDING_ENV.md` | Setup instructions |
| `ONBOARDING_TESTING.md` | Testing procedures |
| `ONBOARDING_IMPLEMENTATION.md` | Implementation details |

## Support Links

- **Docs**: `/docs/ONBOARDING_*.md`
- **Email**: support@alreadyherellc.com
- **GitHub**: [repo]/issues?label=onboarding
- **Status**: https://profitengine.alreadyherellc.com/status

## Quick Commands

```bash
# Install dependencies
npm install nodemailer

# Initialize database
python scripts/init-clients-db.py

# Start development
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run tests
npm test

# Lint code
npm run lint

# Type check
npm run typecheck
```

## Environment Variables Template

```env
# Auth
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
NEXTAUTH_URL=http://localhost:3000

# Email (pick one provider)
SENDGRID_API_KEY=SG.xxx
# OR
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
# OR
SMTP_HOST=smtp.example.com
SMTP_PORT=587

# Email headers
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com

# Site
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 201 | Created | Signup successful |
| 200 | OK | KYC submitted |
| 400 | Bad Request | Invalid password |
| 401 | Unauthorized | Missing/invalid token |
| 409 | Conflict | Email already exists |
| 500 | Server Error | Database error |

## Next Steps After Signup

1. Verify email (optional, in welcome email)
2. Complete KYC (optional, recommended)
3. Access trading dashboard
4. Set up trading strategies
5. Begin paper trading

---

**ProfitEngine Onboarding System v1.0.0 - Quick Reference**

For complete documentation, see `/docs/ONBOARDING_README.md`
