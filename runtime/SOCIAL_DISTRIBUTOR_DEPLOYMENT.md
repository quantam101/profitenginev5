# Social Distributor — Production Deployment Checklist

## Pre-Deployment Verification

### Code Quality
- [ ] `python -m py_compile runtime/social_distributor.py` passes
- [ ] `python -m py_compile runtime/social_distributor_examples.py` passes
- [ ] No syntax errors in documentation files
- [ ] Type hints are correct (python -m mypy runtime/social_distributor.py)
- [ ] Code follows PEP 8 (tested with black/flake8)

### Dependencies
- [ ] `apscheduler` installed: `pip list | grep apscheduler`
- [ ] `requests` installed: `pip list | grep requests`
- [ ] Optional `sendgrid` available if needed
- [ ] Optional `boto3` available if using AWS SES
- [ ] All imports work: `python -c "from runtime.social_distributor import *"`

### Integration Tests
- [ ] ProductionSocialEngine imports correctly
- [ ] SocialDistributor initializes without errors
- [ ] Database creates successfully on first run
- [ ] FastAPI routes register without conflicts
- [ ] No circular import dependencies

## Platform Credential Setup

### Twitter/X (OAuth 1.0a)
- [ ] Get API key from https://developer.twitter.com/en/portal/dashboard
- [ ] Get API secret from developer portal
- [ ] Get access token from developer portal
- [ ] Get access secret from developer portal
- [ ] Test credentials work:
  ```bash
  python -c "
  import os
  os.environ['TWITTER_API_KEY'] = 'xxx'
  os.environ['TWITTER_API_SECRET'] = 'xxx'
  os.environ['TWITTER_ACCESS_TOKEN'] = 'xxx'
  os.environ['TWITTER_ACCESS_SECRET'] = 'xxx'
  from runtime.eaos.social_engine import _twitter_auth_header
  header = _twitter_auth_header('POST', 'https://api.twitter.com/2/tweets', {})
  print('OK' if header else 'FAIL')
  "
  ```

### LinkedIn (OAuth 2.0)
- [ ] Register app at https://www.linkedin.com/developers/apps
- [ ] Get access token from app settings
- [ ] Get person URN from profile: `urn:li:person:12345678`
- [ ] Test token with LinkedIn API
- [ ] Verify scopes include: `w_member_social`, `r_member_social`

### Reddit (Script Auth)
- [ ] Create script app at https://www.reddit.com/prefs/apps
- [ ] Get client ID and secret
- [ ] Use Reddit username and password
- [ ] Test auth:
  ```bash
  python -c "
  import base64
  import urllib.request
  import json
  
  client_id = 'xxx'
  client_secret = 'xxx'
  username = 'xxx'
  password = 'xxx'
  
  creds = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
  req = urllib.request.Request(
    'https://www.reddit.com/api/v1/access_token',
    data=f'grant_type=password&username={username}&password={password}'.encode(),
    headers={'Authorization': f'Basic {creds}', 'User-Agent': 'ProfitEngine/5.0'},
    method='POST'
  )
  resp = json.loads(urllib.request.urlopen(req).read())
  print('OK' if 'access_token' in resp else f'FAIL: {resp}')
  "
  ```

### TikTok (Access Token)
- [ ] Register app at https://developers.tiktok.com/
- [ ] Get access token from app
- [ ] Ensure token has video.upload scope
- [ ] Verify refresh token mechanism

### YouTube (OAuth 2.0)
- [ ] Create OAuth 2.0 credentials at https://console.cloud.google.com/
- [ ] Set authorized redirect URI: http://localhost:8000/auth/youtube/callback
- [ ] Get client ID and secret
- [ ] Get refresh token using OAuth flow
- [ ] Test refresh token:
  ```bash
  python -c "
  import urllib.request
  import urllib.parse
  import json
  
  client_id = 'xxx'
  client_secret = 'xxx'
  refresh_token = 'xxx'
  
  data = urllib.parse.urlencode({
    'client_id': client_id,
    'client_secret': client_secret,
    'refresh_token': refresh_token,
    'grant_type': 'refresh_token',
  }).encode()
  
  req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
  resp = json.loads(urllib.request.urlopen(req).read())
  print('OK' if 'access_token' in resp else f'FAIL: {resp}')
  "
  ```

### Gmail (SMTP)
- [ ] Login to https://myaccount.google.com/apppasswords
- [ ] Generate app-specific password (NOT regular password)
- [ ] Test email sending:
  ```bash
  python -c "
  import smtplib
  
  gmail_user = 'alreadyherellc@gmail.com'
  gmail_pass = 'YOUR_APP_PASSWORD'
  
  with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login(gmail_user, gmail_pass)
    print('OK')
  "
  ```

## Environment Configuration

### Server .env Setup
- [ ] Create/edit server `.env` file (never commit)
- [ ] Add all platform credentials
- [ ] Set `PROFITENGINE_URL` to production domain
- [ ] Set `GMAIL_USER` and `ALERT_EMAIL`
- [ ] Set `AFFILIATE_TAG` to `alreadyhere-20`
- [ ] Verify `.env` is in `.gitignore`
- [ ] No placeholder values remain (check CLAUDE.md NO-PLACEHOLDER-RULE)

### GitHub Secrets Setup
- [ ] Add `TWITTER_API_KEY` to GitHub Secrets
- [ ] Add `TWITTER_API_SECRET` to GitHub Secrets
- [ ] Add `TWITTER_ACCESS_TOKEN` to GitHub Secrets
- [ ] Add `TWITTER_ACCESS_SECRET` to GitHub Secrets
- [ ] Add `LINKEDIN_ACCESS_TOKEN` to GitHub Secrets
- [ ] Add `LINKEDIN_PERSON_URN` to GitHub Secrets
- [ ] Add `REDDIT_CLIENT_ID` to GitHub Secrets
- [ ] Add `REDDIT_CLIENT_SECRET` to GitHub Secrets
- [ ] Add `REDDIT_USERNAME` to GitHub Secrets
- [ ] Add `REDDIT_PASSWORD` to GitHub Secrets
- [ ] Add `TIKTOK_ACCESS_TOKEN` to GitHub Secrets
- [ ] Add `YOUTUBE_CLIENT_ID` to GitHub Secrets
- [ ] Add `YOUTUBE_CLIENT_SECRET` to GitHub Secrets
- [ ] Add `YOUTUBE_REFRESH_TOKEN` to GitHub Secrets
- [ ] Add `GMAIL_USER` to GitHub Secrets
- [ ] Add `GMAIL_APP_PASSWORD` to GitHub Secrets
- [ ] Add `ALERT_EMAIL` to GitHub Secrets

### Vercel Environment Variables
- [ ] Copy all credentials to Vercel project settings
- [ ] Set production domain variables
- [ ] Verify variables are marked as "Sensitive"
- [ ] Test deployment with real values

## Database Setup

### Local Development
- [ ] Create `datacenter/` directory: `mkdir -p datacenter`
- [ ] Test database creation:
  ```bash
  python -c "
  from runtime.social_distributor import SocialDistributorDB
  db = SocialDistributorDB()
  print('Database initialized:', db.db_path)
  "
  ```
- [ ] Verify tables created:
  ```bash
  sqlite3 datacenter/social_distributor.db ".tables"
  ```

### Production (OCI Server)
- [ ] Create `datacenter/` on OCI server
- [ ] Set proper permissions: `chmod 755 datacenter/`
- [ ] Ensure disk space available: `df -h`
- [ ] Enable WAL mode for concurrent access:
  ```bash
  sqlite3 /path/to/social_distributor.db "PRAGMA journal_mode=WAL;"
  ```
- [ ] Schedule daily backups

## API Integration

### FastAPI Routes
- [ ] Verify routes register in main `api.py`:
  ```python
  from runtime.social_distributor import register_routes
  register_routes(app)
  ```
- [ ] Test endpoints:
  ```bash
  curl http://localhost:8000/api/social/posts
  curl http://localhost:8000/api/social/engagement
  ```
- [ ] Check no route conflicts with existing API

### Webhook Handlers
- [ ] Blog publish webhook registers
- [ ] Signature verification implemented
- [ ] Error handling for malformed payloads
- [ ] Rate limiting configured

## Scheduler Configuration

### APScheduler Setup
- [ ] Verify APScheduler imports:
  ```bash
  python -c "from apscheduler.schedulers.background import BackgroundScheduler; print('OK')"
  ```
- [ ] Test scheduler initialization:
  ```python
  from runtime.social_distributor import SocialDistributor
  dist = SocialDistributor()
  dist.schedule_daily_posts()
  print('Scheduler running:', dist.scheduler.running)
  ```
- [ ] Verify timezone set to US/Mountain (MST)
- [ ] Check all 6 scheduled jobs registered:
  - twitter_morning (9 AM)
  - twitter_evening (5 PM)
  - linkedin_daily (9 AM)
  - tiktok_daily (5 PM)
  - youtube_daily (5 PM)
  - email_digest_weekly (Friday 10 AM)

### Cron Configuration (Alternative)
- [ ] If using system cron instead of APScheduler:
  ```bash
  crontab -e
  # 0 9 * * * python /app/runtime/social_distributor.py --post twitter
  # 0 17 * * * python /app/runtime/social_distributor.py --post all
  ```

## Logging & Monitoring

### Log Files
- [ ] Create log directory: `mkdir -p logs/`
- [ ] `social_distributor.log` created on first run
- [ ] Log rotation configured (optional):
  ```python
  from logging.handlers import RotatingFileHandler
  handler = RotatingFileHandler(
    'social_distributor.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
  )
  ```
- [ ] Logs readable by monitoring service

### Monitoring Setup
- [ ] Health check endpoint `/health/social` working
- [ ] Logging aggregation configured (optional: Datadog, CloudWatch)
- [ ] Alerts configured for:
  - Post failures
  - Rate limit hits
  - Database errors
  - Network connectivity loss

### Performance Metrics
- [ ] Avg post latency tracked
- [ ] Engagement metrics updated
- [ ] Error rate monitored
- [ ] Database size monitored

## Testing

### Unit Tests
- [ ] Run all tests:
  ```bash
  pytest runtime/tests/test_social_distributor.py -v
  ```
- [ ] Duplicate detection works
- [ ] Platform formatting correct
- [ ] Database operations succeed
- [ ] API endpoints return proper status codes

### Integration Tests
- [ ] Test full distribution pipeline
- [ ] Test with real platform credentials (dry-run)
- [ ] Test scheduler triggers
- [ ] Test email digest generation
- [ ] Test offline caching behavior

### Manual Testing (With Real Accounts)
- [ ] Post test tweet to Twitter
- [ ] Post test article to LinkedIn
- [ ] Post test entry to Reddit
- [ ] Verify all posts appear on actual platforms
- [ ] Check engagement metrics populate
- [ ] Send test email digest

## Documentation Review

- [ ] [SOCIAL_DISTRIBUTOR_README.md](SOCIAL_DISTRIBUTOR_README.md) up-to-date
- [ ] [SOCIAL_DISTRIBUTOR_SETUP.md](SOCIAL_DISTRIBUTOR_SETUP.md) complete
- [ ] [SOCIAL_DISTRIBUTOR_QUICKREF.md](SOCIAL_DISTRIBUTOR_QUICKREF.md) accurate
- [ ] [SOCIAL_DISTRIBUTOR_INTEGRATION.md](SOCIAL_DISTRIBUTOR_INTEGRATION.md) current
- [ ] Examples all runnable
- [ ] No broken links in docs
- [ ] Platform-specific setup instructions correct

## Security Audit

### Credentials
- [ ] No credentials in source code
- [ ] All secrets in `.env` (server-only)
- [ ] All GitHub Secrets configured
- [ ] `.env` in `.gitignore`
- [ ] `*.log` in `.gitignore`
- [ ] Credentials rotated within 90 days

### Input Validation
- [ ] Tweet length validation (≤280 chars)
- [ ] LinkedIn length validation (≤3000 chars)
- [ ] Post title/body sanitized
- [ ] No SQL injection possible (parameterized queries)
- [ ] No XSS in email digest (HTML-escaped)

### API Security
- [ ] Webhook signature verification enabled
- [ ] Rate limiting configured
- [ ] HTTPS only for external APIs
- [ ] Timeout values set (15-30s)
- [ ] Error messages don't leak secrets

### Data Privacy
- [ ] No personal data stored longer than needed
- [ ] Database backups encrypted
- [ ] Logs don't contain sensitive info
- [ ] GDPR compliance considered (if EU users)

## Deployment Process

### Pre-Deployment
- [ ] All tests passing
- [ ] Code review completed
- [ ] Credentials verified working
- [ ] Backup database created
- [ ] Rollback plan documented

### Deployment Steps
1. [ ] Merge PR to main branch
2. [ ] GitHub Actions CI/CD runs
3. [ ] Deploy to OCI server:
   ```bash
   # Pull latest code
   git pull origin main
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create database
   python -c "from runtime.social_distributor import SocialDistributor; SocialDistributor().db"
   
   # Restart service
   docker restart profitengine-runtime
   ```
4. [ ] Verify health check: `curl http://server:8000/health/social`
5. [ ] Monitor logs: `tail -f social_distributor.log`
6. [ ] Send test post to verify working

### Post-Deployment
- [ ] All scheduled jobs running
- [ ] No errors in logs
- [ ] Database accessible
- [ ] API endpoints responsive
- [ ] Email sending works
- [ ] Engagement tracking active

## Rollback Plan

If issues occur:

```bash
# 1. Stop scheduler
pkill -f "social_distributor"

# 2. Restore previous code
git revert <commit-hash>

# 3. Restore database backup
cp social_distributor.db.backup datacenter/social_distributor.db

# 4. Restart service
docker restart profitengine-runtime

# 5. Verify
curl http://localhost:8000/health/social
```

## Maintenance

### Daily
- [ ] Check logs for errors: `grep ERROR social_distributor.log`
- [ ] Monitor posting success rate
- [ ] Verify scheduled jobs fired

### Weekly
- [ ] Review engagement metrics
- [ ] Check email digest delivery
- [ ] Verify database size reasonable
- [ ] Monitor error rate

### Monthly
- [ ] Rotate API credentials
- [ ] Backup database
- [ ] Review top-performing posts
- [ ] Analyze platform-specific performance
- [ ] Update documentation

### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Update dependencies
- [ ] Test disaster recovery
- [ ] Plan Q2 improvements

## Success Criteria

✅ Deployment is successful when:

- All platform credentials configured and tested
- Database created and accessible
- Scheduler running with 6 jobs registered
- Health check endpoint returns `"ok": true`
- At least one test post successful on each platform
- Email digest sent successfully
- Engagement metrics tracking
- All logs clean (no ERROR messages)
- Documentation complete and accurate
- Team trained on using the system
- Monitoring/alerts configured

## Support Contacts

- **Technical Issues**: dispatch@alreadyherellc.com
- **Platform-Specific**: Check [SOCIAL_DISTRIBUTOR_SETUP.md](SOCIAL_DISTRIBUTOR_SETUP.md)
- **Bug Reports**: Include logs and reproduction steps
- **Feature Requests**: Document use case and expected behavior

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Verified By**: _______________  
**Sign-Off**: _______________  

**Version**: 1.0.0  
**Last Updated**: 2026-06-18
