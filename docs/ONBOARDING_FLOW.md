# ProfitEngine Customer Onboarding Flow

Complete customer signup and KYC verification system for ProfitEngine trading platform.

## Overview

The onboarding flow consists of three main stages:

1. **Landing Page** - Hero section with feature highlights
2. **Account Signup** - Email, password, capital amount, risk preference
3. **KYC Verification** - Identity verification for compliance (optional but recommended)
4. **Dashboard Access** - Full trading platform access

## Architecture

### Files Created

```
app/
├── trading-signup/
│   ├── page.tsx                 # Landing page + signup form
│   ├── kyc/
│   │   └── page.tsx            # KYC form
│   └── kyc-status/
│       └── page.tsx            # KYC status checker
└── api/
    └── auth/
        └── signup/
            └── route.ts         # Signup API endpoint
    └── kyc/
        ├── submit/
        │   └── route.ts         # KYC submission endpoint
        └── status/
            └── route.ts         # KYC status endpoint

lib/
├── auth-utils.ts               # Password validation, token generation
├── email-service.ts            # Email sending service
└── emails/
    └── welcome.tsx            # Welcome email template
```

## User Journey

### Stage 1: Landing Page (`/trading-signup`)

Users land on the homepage where they see:

- **Hero Section**
  - "PROFITENGINE Trading System" headline
  - "Start your paper trading journey with 11 AI-powered strategies"
  
- **Feature Cards** (6 features highlighted)
  - 11 Trading Strategies
  - 90%+ Win Rate Target
  - Paper Trading First
  - Real-Time Monitoring
  - Secure Accounts
  - 24/7 AI Assistant Support

- **CTA Button**
  - "Start Free Signup"
  - Takes user to signup form

### Stage 2: Account Signup

Form fields:
- **Email Address** (required)
  - Validated format
  - Checked for existing accounts
  
- **Password** (required)
  - Minimum 8 characters
  - Must include uppercase, lowercase, and number
  
- **Starting Capital** (required)
  - Minimum $1,000
  - User specifies initial paper trading capital
  
- **Risk Preference** (required)
  - Conservative (1-2% per trade)
  - Moderate (2-4% per trade)
  - Aggressive (4-6% per trade)

- **Terms Agreement** (required checkbox)

**Validation:**
```typescript
- Email: standard email regex
- Password: 8+ chars with uppercase, lowercase, number
- Capital: numeric, minimum $1,000
- Risk: must be one of three options
```

**API Endpoint:** `POST /api/auth/signup`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "capitalAmount": 5000,
  "riskPreference": "moderate",
  "agreeToTerms": true
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Account created successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "tier": "free",
    "createdAt": "2026-06-18T..."
  }
}
```

**Actions on Signup:**
1. Create user in `clients.db` via `ClientsDB.createUser()`
2. Generate JWT-like auth token (7-day expiration)
3. Send welcome email
4. Store token in localStorage
5. Redirect to KYC form (optional) or dashboard

### Stage 3: Welcome Email

**Template:** `lib/emails/welcome.tsx`

**Content:**
- Welcome greeting
- Account summary (email, capital, risk preference)
- 6 feature cards with checkmarks
- Next steps (email verification, KYC, start trading)
- Important notes about paper trading
- Support contact info
- Link to dashboard

**Email Headers:**
- From: `noreply@profitengine.alreadyherellc.com`
- Reply-To: `support@alreadyherellc.com`
- Subject: "Welcome to ProfitEngine - Your Trading Account is Ready"

### Stage 4: KYC Verification (Optional)

**Route:** `/trading-signup/kyc`

Form fields:
- **First Name** (required)
- **Last Name** (required)
- **Age** (required)
  - Minimum 18 years old
- **Trading Experience** (required)
  - Beginner
  - Intermediate
  - Advanced
- **Risk Tolerance** (required)
  - Low
  - Moderate
  - High
- **Investment Goals** (required, text area)
- **Agree to Terms** (required checkbox)

**API Endpoint:** `POST /api/kyc/submit`

**Request:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "age": 35,
  "tradingExperience": "intermediate",
  "riskTolerance": "moderate",
  "investmentGoals": "Generate passive income and learn trading strategies",
  "agreeToTerms": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "KYC verification submitted successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "kycStatus": "pending_review"
  }
}
```

**KYC Status Flow:**

1. **Pending** (default)
   - Submitted for review
   - 24-hour review window
   - User notified via email

2. **Approved**
   - User fully verified
   - Access to premium features
   - Live trading available

3. **Rejected**
   - Requires resubmission
   - User directed to support
   - Can retry form

**Status Endpoint:** `GET /api/kyc/status`

**Response:**
```json
{
  "status": "pending|approved|rejected",
  "message": "Status message...",
  "submittedAt": "2026-06-18T...",
  "completedAt": "2026-06-18T...",
  "nextSteps": ["step 1", "step 2"]
}
```

## Email Configuration

The system supports multiple email providers:

### 1. SendGrid (Recommended)
```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

### 2. Gmail
```env
GMAIL_USER=profitengine@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

### 3. Custom SMTP
```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=username
SMTP_PASSWORD=password
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

### 4. Development (Ethereal)
- Automatically used if no provider configured
- Test emails viewable in Ethereal UI

## Authentication System

### Token Generation

```typescript
import { generateAuthToken } from '@/lib/auth-utils';

const token = generateAuthToken(userId, email);
// Returns: "<base64_payload>.<hmac_signature>"
```

**Token Structure:**
```json
{
  "userId": 1,
  "email": "user@example.com",
  "iat": 1718704000,
  "exp": 1719309600  // 7 days
}
```

**Signature:** HMAC-SHA256 using `NEXTAUTH_SECRET`

### Token Verification

```typescript
import { verifyAuthToken } from '@/lib/auth-utils';

const decoded = verifyAuthToken(token);
if (decoded) {
  console.log(decoded.userId, decoded.email);
} else {
  console.log('Token invalid or expired');
}
```

### Protected Routes

Add authentication check to any endpoint:

```typescript
const authHeader = request.headers.get('Authorization');
const token = authHeader?.substring(7); // Remove "Bearer "
const decoded = verifyAuthToken(token);

if (!decoded) {
  return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
}
```

## Database Integration

### User Creation

```typescript
import { ClientsDB } from '@/lib/clients-db';

const db = new ClientsDB();
const user = db.createUser(
  'user@example.com',
  'free',  // trading tier
  '2026-06-18'  // optional signup date
);

console.log(user.id);        // Auto-generated ID
console.log(user.email);     // user@example.com
console.log(user.createdAt); // Timestamp
```

### User Lookup

```typescript
// By ID
const user = db.getUser(1);

// By email
const user = db.getUserByEmail('user@example.com');
```

### Activity Tracking

```typescript
// Update last active timestamp
db.updateUserActivity(userId);

// Upgrade tier (for future use)
db.updateUserTier(userId, 'premium');
```

## Frontend Integration

### Landing Page Component

```tsx
import TradingSignupPage from '@/app/trading-signup/page';

// This page includes:
// - Hero section with features
// - Signup form with validation
// - Success confirmation
```

### Sign In Page

Existing sign-in page at `/sign-in` uses NextAuth with Google OAuth.

To add custom email/password auth:

```tsx
// In app/sign-in/page.tsx
// Add email input form
// Call POST /api/auth/signin
```

## Security Considerations

1. **Password Requirements**
   - Minimum 8 characters
   - Must include uppercase, lowercase, number
   - Consider adding special character requirement
   - Hash passwords with bcrypt in production

2. **Email Verification**
   - Send verification link on signup
   - 24-hour expiration
   - Prevent email spoofing

3. **Rate Limiting**
   - Limit signup attempts per IP
   - Limit password reset requests
   - Implement CAPTCHA for signup

4. **Token Security**
   - JWT tokens stored in localStorage (httpOnly in production)
   - 7-day expiration
   - Refresh token mechanism recommended
   - Verify NEXTAUTH_SECRET is strong

5. **Data Protection**
   - Never log passwords
   - Encrypt PII in database
   - Use HTTPS only
   - Implement audit logging

## Testing

### Unit Tests

```bash
npm test
```

### Integration Tests

1. **Signup Flow**
   ```bash
   # Test email validation
   # Test password strength
   # Test user creation
   # Test email sending
   ```

2. **KYC Flow**
   ```bash
   # Test form validation
   # Test age verification
   # Test KYC submission
   # Test status retrieval
   ```

### Manual Testing

1. Navigate to `/trading-signup`
2. Fill signup form with:
   - Email: `test@example.com`
   - Password: `TestPassword123`
   - Capital: `5000`
   - Risk: `moderate`
3. Submit form
4. Check success message
5. Navigate to `/trading-signup/kyc`
6. Fill KYC form
7. Check status at `/trading-signup/kyc-status`

## Deployment Checklist

- [ ] Set `NEXTAUTH_SECRET` in environment
- [ ] Configure email provider (SendGrid/Gmail/SMTP)
- [ ] Set `NEXT_PUBLIC_SITE_URL` to production domain
- [ ] Set `EMAIL_FROM` and `EMAIL_REPLY_TO`
- [ ] Verify database is initialized with schema
- [ ] Test signup flow end-to-end
- [ ] Test email delivery
- [ ] Test KYC flow
- [ ] Configure CORS for API endpoints
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging
- [ ] Create support email templates
- [ ] Document user support process

## Future Enhancements

1. **Email Verification**
   - Send verification link on signup
   - Prevent account access until verified
   - Resend verification option

2. **KYC Automation**
   - Integration with ID verification service (IDology, Onfido)
   - OCR for document scanning
   - Automated compliance checks

3. **Multi-Factor Authentication**
   - SMS 2FA
   - Authenticator app support
   - Backup codes

4. **Account Recovery**
   - Password reset flow
   - Email recovery
   - Phone recovery

5. **Advanced KYC**
   - Document upload (ID, proof of address)
   - Liveness detection
   - Business account support

6. **Analytics**
   - Signup funnel tracking
   - Dropout points
   - Conversion metrics

7. **Referral System**
   - Referral codes
   - Bonus tracking
   - Affiliate payouts

## Troubleshooting

### Signup Fails with "Email Already Registered"
- User already has account
- Check database for existing user
- Direct to login page

### Welcome Email Not Sent
- Check email provider configuration
- Verify SMTP credentials
- Check spam folder
- Enable "less secure apps" if using Gmail

### KYC Status Always "Pending"
- Implementation is mock-based
- In production, integrate with actual verification service
- Check database for KYC records

### Token Expired
- Default expiration is 7 days
- Implement refresh token flow
- Clear localStorage and re-login

## Support

For issues or questions:
- Email: support@alreadyherellc.com
- Docs: https://profitengine.alreadyherellc.com
- Status: https://profitengine.alreadyherellc.com/status
