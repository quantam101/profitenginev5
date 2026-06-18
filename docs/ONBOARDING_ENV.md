# Onboarding System - Environment Configuration

Complete setup guide for the ProfitEngine onboarding system.

## Required Environment Variables

### Authentication

```env
# Next.js/NextAuth configuration
NEXTAUTH_SECRET=your-random-secret-key-here  # generate with: openssl rand -base64 32
NEXTAUTH_URL=https://app.profitengine.alreadyherellc.com

# Optional: Google OAuth (for sign-in page)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
```

### Email Configuration (Choose One)

#### Option 1: SendGrid (Recommended)
```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

Get API Key:
1. Go to https://sendgrid.com
2. Sign up or log in
3. Settings → API Keys → Create API Key
4. Copy key (never expires unless revoked)

#### Option 2: Gmail
```env
GMAIL_USER=profitengine@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx  # NOT your password
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

Get App Password:
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Create App Password (select "Mail" and "Windows Computer")
4. Use the 16-character code (ignoring spaces)

#### Option 3: Custom SMTP
```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURE=false  # true for port 465 (SSL)
SMTP_USER=username
SMTP_PASSWORD=password
EMAIL_FROM=noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO=support@alreadyherellc.com
```

### Site Configuration

```env
# Frontend URLs
NEXT_PUBLIC_SITE_URL=https://app.profitengine.alreadyherellc.com
SITE_DOMAIN=profitengine.alreadyherellc.com

# Optional: Custom dashboard redirect
NEXT_PUBLIC_DASHBOARD_URL=https://app.profitengine.alreadyherellc.com/command-center
```

### Database

```env
# SQLite (default) - no config needed, uses ./clients.db

# Optional: PostgreSQL (future)
# DATABASE_URL=postgresql://user:password@localhost:5432/profitengine_db
```

## Setup Instructions

### 1. Local Development

Create `.env.local`:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
# Auth
NEXTAUTH_SECRET=$(openssl rand -base64 32)
NEXTAUTH_URL=http://localhost:3000

# Email (use Gmail or SendGrid for testing)
SENDGRID_API_KEY=SG.test_key_here
EMAIL_FROM=test@example.com
EMAIL_REPLY_TO=support@example.com

# URLs
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Start development server:

```bash
npm run dev
```

Test signup at: http://localhost:3000/trading-signup

### 2. Staging (Vercel)

Set environment variables in Vercel dashboard:

1. Go to your Vercel project
2. Settings → Environment Variables
3. Add variables (select "Preview" environment for staging)

```
NEXTAUTH_SECRET          → your-strong-secret
NEXTAUTH_URL             → https://staging-app.profitengine.alreadyherellc.com
SENDGRID_API_KEY         → SG.xxxxxxxx
EMAIL_FROM               → noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO           → support@alreadyherellc.com
NEXT_PUBLIC_SITE_URL     → https://staging-app.profitengine.alreadyherellc.com
```

### 3. Production (Vercel)

Set environment variables in Vercel (Production environment):

```
NEXTAUTH_SECRET          → your-production-secret (generate new)
NEXTAUTH_URL             → https://app.profitengine.alreadyherellc.com
SENDGRID_API_KEY         → SG.xxxxxxxx
EMAIL_FROM               → noreply@profitengine.alreadyherellc.com
EMAIL_REPLY_TO           → support@alreadyherellc.com
NEXT_PUBLIC_SITE_URL     → https://app.profitengine.alreadyherellc.com
GOOGLE_CLIENT_ID         → xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET     → GOCSPX-xxx
```

Deploy:

```bash
git push origin main
```

## Email Provider Setup Guide

### SendGrid Setup

1. **Create Account**
   - Go to https://sendgrid.com
   - Sign up with email

2. **Verify Sender Identity**
   - Settings → Sender Authentication
   - Add domain or single sender email
   - For domain: add DNS records
   - For email: confirm by clicking link in email

3. **Create API Key**
   - Settings → API Keys
   - Create API Key (Full Access)
   - Copy key immediately (not shown again)

4. **Test**
   ```bash
   curl --request POST \
     --url https://api.sendgrid.com/v3/mail/send \
     --header "Authorization: Bearer $SENDGRID_API_KEY" \
     --header "Content-Type: application/json" \
     --data '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"noreply@profitengine.alreadyherellc.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'
   ```

### Gmail Setup

1. **Create Gmail Account** (or use existing)
   - test-profitengine@gmail.com

2. **Enable 2-Factor Authentication**
   - https://myaccount.google.com/security
   - 2-Step Verification → Enable

3. **Create App Password**
   - https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Copy 16-character password

4. **Less Secure Apps** (if 2FA not available)
   - https://myaccount.google.com/u/1/lesssecureapps
   - Turn ON (not recommended for production)

5. **Test**
   ```bash
   npm install -D nodemailer
   node -e "
   const nodemailer = require('nodemailer');
   const transporter = nodemailer.createTransport({
     service: 'gmail',
     auth: {
       user: 'your-email@gmail.com',
       pass: 'xxxx xxxx xxxx xxxx'
     }
   });
   transporter.sendMail({
     from: 'noreply@profitengine.alreadyherellc.com',
     to: 'test@example.com',
     subject: 'Test',
     text: 'Test email'
   }, (err, info) => {
     console.log(err || info);
   });
   "
   ```

### Custom SMTP Setup

Example with Mailgun:

1. **Create Account**
   - https://www.mailgun.com

2. **Get Credentials**
   - Domain Management → SMTP Info
   - SMTP Host: smtp.mailgun.org
   - SMTP Port: 587 or 465
   - Username: postmaster@your-domain
   - Password: (shown in dashboard)

3. **Add to `.env.local`**
   ```env
   SMTP_HOST=smtp.mailgun.org
   SMTP_PORT=587
   SMTP_SECURE=false
   SMTP_USER=postmaster@your-domain
   SMTP_PASSWORD=your-password
   ```

## Database Setup

### SQLite (Default)

Database is automatically created if not present:

```bash
# Initialize database
cd /path/to/profitengine-v5-final
python scripts/init-clients-db.py
```

Or via the TypeScript wrapper:

```typescript
import { ClientsDB } from '@/lib/clients-db';
ClientsDB.initializeDatabase();
```

### PostgreSQL (Optional)

For larger deployments:

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15

   # Linux
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database**
   ```bash
   createdb profitengine_db
   createuser profitengine
   psql -c "ALTER USER profitengine WITH PASSWORD 'your-password';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE profitengine_db TO profitengine;"
   ```

3. **Set Connection String**
   ```env
   DATABASE_URL=postgresql://profitengine:your-password@localhost:5432/profitengine_db
   ```

4. **Run Migrations** (when implemented)
   ```bash
   npm run db:migrate
   ```

## Verification Checklist

### Local Testing

- [ ] `.env.local` created with all required vars
- [ ] `npm run dev` starts without errors
- [ ] Can access http://localhost:3000/trading-signup
- [ ] Signup form renders correctly
- [ ] Can submit signup form
- [ ] Success message appears
- [ ] Check email is received (if configured)
- [ ] Email contains correct content
- [ ] Can access KYC form
- [ ] KYC status page works

### Staging Testing

- [ ] Environment variables set in Vercel staging
- [ ] Deploy to staging branch completes
- [ ] Can access https://staging-app.profitengine.alreadyherellc.com/trading-signup
- [ ] Signup flow works end-to-end
- [ ] Email received (check spam folder)
- [ ] Form validation works
- [ ] Error messages display correctly
- [ ] Mobile responsive design verified

### Production Checklist

- [ ] NEXTAUTH_SECRET is strong (32+ characters)
- [ ] NEXTAUTH_URL matches production domain
- [ ] Email provider is verified and working
- [ ] Sender email verified in email service
- [ ] All URLs use HTTPS
- [ ] Database backups configured
- [ ] Error logging enabled
- [ ] Rate limiting configured
- [ ] CORS policy set correctly
- [ ] 404 pages handled
- [ ] Support email configured

## Troubleshooting

### Email Not Sending

**Check 1: Configuration**
```bash
# Verify env vars loaded
node -e "console.log(process.env.SENDGRID_API_KEY)"
```

**Check 2: API Key Valid**
```bash
# Test SendGrid API
curl -X GET "https://api.sendgrid.com/v3/mail/send" \
  -H "Authorization: Bearer $SENDGRID_API_KEY"
```

**Check 3: Sender Not Verified**
- Go to SendGrid Settings → Sender Authentication
- Verify domain or single sender email
- Wait up to 48 hours for domain verification

**Check 4: Logs**
```bash
# Check Next.js logs
npm run dev 2>&1 | grep -i email
```

### Signup Fails

**Check 1: Database**
```bash
# Verify database exists
ls -la clients.db

# Initialize if missing
python scripts/init-clients-db.py
```

**Check 2: Validation**
- Email: Must be valid format (user@domain.com)
- Password: Min 8 chars, uppercase, lowercase, number
- Capital: Min $1,000
- All fields: Check browser console for errors

**Check 3: API**
```bash
# Test signup endpoint
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"TestPass123",
    "capitalAmount":5000,
    "riskPreference":"moderate",
    "agreeToTerms":true
  }'
```

### KYC Not Submitting

**Check 1: Authentication**
- Token stored in localStorage? Check DevTools
- Token valid (not expired)?
- Authorization header sent correctly?

**Check 2: Validation**
- Age must be 18+
- Goals not empty
- All checkboxes checked

**Check 3: API**
```bash
# Test with token
curl -X POST http://localhost:3000/api/kyc/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Production Deployment

### Vercel Deployment

1. **Connect Repository**
   ```bash
   vercel link
   ```

2. **Set Environment Variables**
   - Dashboard → Settings → Environment Variables
   - Add all production variables

3. **Configure Domain**
   - Dashboard → Settings → Domains
   - Add production domain
   - Update DNS records

4. **Deploy**
   ```bash
   git push origin main
   ```

### Self-Hosted Deployment (OCI)

1. **Build**
   ```bash
   npm run build
   ```

2. **Start Server**
   ```bash
   npm run start
   ```

3. **Configure Reverse Proxy**
   ```nginx
   # /etc/caddy/Caddyfile
   app.profitengine.alreadyherellc.com {
     reverse_proxy localhost:3000
     encode gzip
   }
   ```

4. **Enable HTTPS**
   ```bash
   caddy reload
   ```

## Security Best Practices

1. **Rotate Secrets Regularly**
   - Generate new `NEXTAUTH_SECRET` quarterly
   - Rotate API keys yearly

2. **Environment Separation**
   - Never commit secrets to repo
   - Use `.env.local` (in .gitignore)
   - Different secrets per environment

3. **Email Security**
   - Use separate email account for transactional
   - Configure SPF, DKIM, DMARC records
   - Monitor for abuse

4. **Database Security**
   - Encrypt passwords with bcrypt (when implementing)
   - Regular backups
   - Access controls

5. **API Security**
   - Rate limiting
   - HTTPS only
   - CORS configuration
   - Input validation

## Support

For configuration help:
- Docs: /docs/ONBOARDING_FLOW.md
- Email: support@alreadyherellc.com
- GitHub Issues: [repo]/issues
