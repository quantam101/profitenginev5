# Onboarding System - Testing Guide

Complete testing procedures for the ProfitEngine onboarding flow.

## Test Environment Setup

### Prerequisites

```bash
# Install dependencies
npm install

# Add nodemailer for email testing (if not already present)
npm install nodemailer

# Optional: Install testing tools
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
```

### Environment Variables

Create `.env.local.test`:

```env
NEXTAUTH_SECRET=test-secret-key-for-testing-only
NEXTAUTH_URL=http://localhost:3000
SENDGRID_API_KEY=SG.test_key
EMAIL_FROM=test@example.com
EMAIL_REPLY_TO=support@example.com
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### Database

```bash
# Initialize test database
python scripts/init-clients-db.py
```

## Unit Testing

### Auth Utils Tests

```typescript
// lib/auth-utils.test.ts

import { 
  validateEmail, 
  validatePassword, 
  generateAuthToken, 
  verifyAuthToken 
} from '@/lib/auth-utils';

describe('Auth Utils', () => {
  describe('validateEmail', () => {
    test('accepts valid emails', () => {
      expect(validateEmail('user@example.com')).toBe(true);
      expect(validateEmail('test.user+tag@example.co.uk')).toBe(true);
    });

    test('rejects invalid emails', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('user@')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    test('accepts strong passwords', () => {
      expect(validatePassword('TestPassword123')).toBeNull();
      expect(validatePassword('SecurePass456')).toBeNull();
    });

    test('rejects weak passwords', () => {
      expect(validatePassword('short')).toBeTruthy();
      expect(validatePassword('nouppercase123')).toBeTruthy();
      expect(validatePassword('NOLOWERCASE123')).toBeTruthy();
      expect(validatePassword('NoNumbers')).toBeTruthy();
    });
  });

  describe('Token Generation and Verification', () => {
    test('generates and verifies token', () => {
      const token = generateAuthToken(1, 'user@example.com');
      const decoded = verifyAuthToken(token);

      expect(decoded).not.toBeNull();
      expect(decoded?.userId).toBe(1);
      expect(decoded?.email).toBe('user@example.com');
    });

    test('rejects invalid tokens', () => {
      expect(verifyAuthToken('invalid.token')).toBeNull();
      expect(verifyAuthToken('')).toBeNull();
    });

    test('rejects expired tokens', () => {
      // Create token with past expiration
      const payload = {
        userId: 1,
        email: 'user@example.com',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
      };
      const token = Buffer.from(JSON.stringify(payload)).toString('base64');
      expect(verifyAuthToken(token)).toBeNull();
    });
  });
});
```

### Form Validation Tests

```typescript
// lib/form-validation.test.ts

export function validateSignupForm(data: any) {
  const errors: Record<string, string> = {};

  if (!data.email) errors.email = 'Email required';
  else if (!validateEmail(data.email)) errors.email = 'Invalid email';

  if (!data.password) errors.password = 'Password required';
  else {
    const pwError = validatePassword(data.password);
    if (pwError) errors.password = pwError;
  }

  if (!data.capitalAmount) errors.capitalAmount = 'Capital required';
  else if (data.capitalAmount < 1000) 
    errors.capitalAmount = 'Minimum $1,000';

  return Object.keys(errors).length > 0 ? errors : null;
}

describe('Form Validation', () => {
  test('validates complete signup form', () => {
    const validForm = {
      email: 'user@example.com',
      password: 'TestPass123',
      capitalAmount: 5000,
      riskPreference: 'moderate',
      agreeToTerms: true,
    };
    expect(validateSignupForm(validForm)).toBeNull();
  });

  test('rejects incomplete form', () => {
    const invalid = {
      email: 'user@example.com',
      // missing password
      capitalAmount: 5000,
    };
    const errors = validateSignupForm(invalid);
    expect(errors?.password).toBeDefined();
  });
});
```

## Integration Testing

### API Endpoint Tests

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Run tests
npm run test:integration
```

```typescript
// tests/signup.integration.test.mjs

import fetch from 'node-fetch';

const BASE_URL = 'http://localhost:3000';
const TEST_EMAIL = `test-${Date.now()}@example.com`;

describe('Signup API Integration', () => {
  test('POST /api/auth/signup - successful signup', async () => {
    const response = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_EMAIL,
        password: 'TestPassword123',
        capitalAmount: 5000,
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.token).toBeDefined();
    expect(data.user.email).toBe(TEST_EMAIL);
  });

  test('POST /api/auth/signup - duplicate email', async () => {
    // First signup
    await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_EMAIL,
        password: 'TestPassword123',
        capitalAmount: 5000,
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });

    // Second signup with same email
    const response = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: TEST_EMAIL,
        password: 'TestPassword123',
        capitalAmount: 5000,
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(409);
    const data = await response.json();
    expect(data.error).toContain('already registered');
  });

  test('POST /api/auth/signup - invalid password', async () => {
    const response = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'user@example.com',
        password: 'weak',  // Too weak
        capitalAmount: 5000,
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain('Password must be');
  });

  test('POST /api/auth/signup - minimum capital', async () => {
    const response = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'user@example.com',
        password: 'TestPassword123',
        capitalAmount: 500,  // Below minimum
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain('$1,000');
  });
});

describe('KYC API Integration', () => {
  let authToken;

  beforeAll(async () => {
    // Create test user
    const response = await fetch(`${BASE_URL}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: `kyc-test-${Date.now()}@example.com`,
        password: 'TestPassword123',
        capitalAmount: 5000,
        riskPreference: 'moderate',
        agreeToTerms: true,
      }),
    });
    const data = await response.json();
    authToken = data.token;
  });

  test('POST /api/kyc/submit - successful submission', async () => {
    const response = await fetch(`${BASE_URL}/api/kyc/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        firstName: 'John',
        lastName: 'Doe',
        age: 35,
        tradingExperience: 'intermediate',
        riskTolerance: 'moderate',
        investmentGoals: 'Generate passive income',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.user.kycStatus).toBe('pending_review');
  });

  test('GET /api/kyc/status - check status', async () => {
    const response = await fetch(`${BASE_URL}/api/kyc/status`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(['pending', 'approved', 'rejected']).toContain(data.status);
  });

  test('POST /api/kyc/submit - unauthorized without token', async () => {
    const response = await fetch(`${BASE_URL}/api/kyc/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firstName: 'John',
        lastName: 'Doe',
        age: 35,
        tradingExperience: 'intermediate',
        riskTolerance: 'moderate',
        investmentGoals: 'Generate passive income',
        agreeToTerms: true,
      }),
    });

    expect(response.status).toBe(401);
  });
});
```

## Manual Testing

### Smoke Test Checklist

#### Landing Page (`/trading-signup`)

- [ ] Page loads without errors
- [ ] Hero section visible
  - [ ] Title displays correctly
  - [ ] Subtitle visible
  - [ ] Background gradient renders
- [ ] 6 feature cards display
  - [ ] Icons visible
  - [ ] Text readable
  - [ ] Hover effects work
- [ ] CTA button visible and clickable
- [ ] Mobile responsive (test on 375px width)

#### Signup Form

- [ ] Form displays all fields
- [ ] Email field:
  - [ ] Accepts valid emails
  - [ ] Rejects invalid emails
  - [ ] Shows error message
- [ ] Password field:
  - [ ] Shows/hides password toggle (optional)
  - [ ] Accepts strong passwords
  - [ ] Rejects weak passwords
  - [ ] Shows strength indicator (optional)
- [ ] Capital field:
  - [ ] Accepts valid amounts
  - [ ] Rejects amounts < $1,000
  - [ ] Shows minimum message
- [ ] Risk preference dropdown:
  - [ ] All options visible
  - [ ] Can select each option
- [ ] Terms checkbox:
  - [ ] Can toggle
  - [ ] Link to terms works
- [ ] Submit button:
  - [ ] Disabled until form valid
  - [ ] Shows loading state
  - [ ] Disables on submit
- [ ] Error messages:
  - [ ] Display on validation fail
  - [ ] Clear on valid input
  - [ ] Styled appropriately

#### Success Page

- [ ] Displays success message
- [ ] Shows confirmation
- [ ] Auto-redirects to KYC (if enabled)
- [ ] No console errors

#### KYC Form (`/trading-signup/kyc`)

- [ ] Form displays all fields
- [ ] First/Last name:
  - [ ] Required fields
  - [ ] Shows error when empty
- [ ] Age field:
  - [ ] Accepts 18+
  - [ ] Rejects under 18
  - [ ] Shows appropriate message
- [ ] Experience dropdown:
  - [ ] All options visible
  - [ ] Selectable
- [ ] Risk tolerance dropdown:
  - [ ] All options visible
  - [ ] Selectable
- [ ] Goals text area:
  - [ ] Accepts text
  - [ ] Required field
- [ ] Terms checkbox:
  - [ ] Can toggle
  - [ ] Required
- [ ] Submit:
  - [ ] Validates on click
  - [ ] Shows loading state
  - [ ] Success message appears
  - [ ] Redirects to status page

#### Status Page (`/trading-signup/kyc-status`)

- [ ] Loads status
- [ ] Shows appropriate status badge
- [ ] Displays status message
- [ ] Shows timestamps (if applicable)
- [ ] Shows next steps
- [ ] Action button works:
  - [ ] "Go to Dashboard" (approved)
  - [ ] "Try Again" (rejected)
  - [ ] "Retry" (error)

#### Email Testing

**With SendGrid:**
```bash
# Check email in SendGrid dashboard
# Settings → Mail Settings → Event Webhook
# or check spam folder
```

**With Gmail:**
```bash
# Check test Gmail account
# Look in inbox and spam folder
# Verify content renders correctly
```

**Email Validation:**
- [ ] Welcome email received
- [ ] Email formatting correct
- [ ] All links clickable
- [ ] Images load
- [ ] Mobile view readable
- [ ] Sender address correct
- [ ] Reply-to address correct

### Cross-Browser Testing

Test in multiple browsers:

| Browser | Desktop | Mobile |
|---------|---------|--------|
| Chrome  | [ ]     | [ ]    |
| Firefox | [ ]     | [ ]    |
| Safari  | [ ]     | [ ]    |
| Edge    | [ ]     | [ ]    |

### Mobile Responsiveness

Test at breakpoints:

- [ ] 320px (iPhone SE)
- [ ] 375px (iPhone 12)
- [ ] 480px (Android phone)
- [ ] 768px (Tablet)
- [ ] 1024px (Desktop)

Check:
- [ ] Form fields stack vertically
- [ ] Buttons are touch-friendly (48px min)
- [ ] Text is readable (16px+ body)
- [ ] Images scale correctly
- [ ] No horizontal scroll

### Performance Testing

```bash
# Lighthouse audit
# DevTools → Lighthouse → Generate report

# Check metrics:
# - First Contentful Paint < 1.5s
# - Largest Contentful Paint < 2.5s
# - Cumulative Layout Shift < 0.1
# - Time to Interactive < 3.5s
```

### Security Testing

- [ ] No sensitive data in LocalStorage
- [ ] Tokens not exposed in URLs
- [ ] No console errors on signup
- [ ] CSRF tokens used (if applicable)
- [ ] Password field masked
- [ ] No API keys in frontend code
- [ ] HTTPS enforced in production

### Error Scenarios

Test error handling:

```
1. Network Error
   - Disable internet during signup
   - Verify error message shows
   - Can retry submission

2. Slow Network
   - Throttle to Slow 4G
   - Verify loading state shows
   - Can cancel submission

3. Server Error
   - Return 500 from API
   - Verify user-friendly error message
   - Can retry

4. Validation Error
   - Submit empty form
   - Submit invalid data
   - Verify field-level errors

5. Duplicate Email
   - Sign up with same email twice
   - Verify "already registered" message
   - Link to login works
```

## Test Data

### Valid Test Accounts

```
Email: test-user-1@example.com
Password: TestPass123
Capital: 5000
Risk: moderate

Email: test-user-2@example.com
Password: SecurePass456
Capital: 10000
Risk: conservative

Email: test-user-3@example.com
Password: AggressivePass789
Capital: 25000
Risk: aggressive
```

### Invalid Test Data

```
// Weak passwords
"password"          // No uppercase
"PASSWORD"          // No lowercase
"Password"          // No number
"Pass1"             // Too short

// Invalid emails
"invalid"
"user@"
"@example.com"
"user name@example.com"

// Invalid capital
500                 // Below minimum
0                   // Invalid
"text"              // Not a number
```

## Performance Benchmarks

Target metrics:

| Metric | Target | Current |
|--------|--------|---------|
| Signup API | < 200ms | __ |
| KYC API | < 200ms | __ |
| Email Send | < 2s | __ |
| Page Load | < 1.5s | __ |
| Form Validation | < 50ms | __ |

## Test Report Template

```markdown
# Onboarding System - Test Report

Date: 2026-06-18
Tester: [Name]
Environment: [Dev/Staging/Production]

## Test Results

### Signup Flow
- Landing page: [PASS/FAIL]
- Form validation: [PASS/FAIL]
- User creation: [PASS/FAIL]
- Email sending: [PASS/FAIL]
- Success message: [PASS/FAIL]

### KYC Flow
- Form display: [PASS/FAIL]
- Form validation: [PASS/FAIL]
- Submission: [PASS/FAIL]
- Status checking: [PASS/FAIL]

### Browser/Device
- Chrome Desktop: [PASS/FAIL]
- Safari Mobile: [PASS/FAIL]
- [...]

## Issues Found

### Critical
- [List critical issues]

### Major
- [List major issues]

### Minor
- [List minor issues]

## Sign-off
- [ ] All critical issues resolved
- [ ] Ready for production
```

## Automation

### Setup Jest

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom jest-environment-jsdom
```

### Configure Jest

Create `jest.config.js`:

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
};
```

### Run Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test signup.test.ts

# Watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage
```

## Continuous Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 20
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
      - run: npm run test:integration
```

## Support

For testing help:
- Email: qa@alreadyherellc.com
- Docs: /docs/ONBOARDING_TESTING.md
- Issues: [repo]/issues?label=onboarding
