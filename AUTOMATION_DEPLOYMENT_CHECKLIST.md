# ProfitEngine v5 — Automation Deployment Checklist

Quick reference checklist for deploying the automation system.

---

## Phase 1: Setup & Configuration (30 minutes)

- [ ] Copy `.env.automation` to `.env.automation.local`
- [ ] Add `.env.automation.local` to `.gitignore`
- [ ] Get Gumroad API key (3 min)
- [ ] Get Instagram token + account ID (10 min)
- [ ] Choose image generation (Replicate/DALL-E) (5 min)
- [ ] Get email platform key (Klaviyo/Substack/ConvertKit) (5 min)
- [ ] Get GitHub Actions token (2 min)
- [ ] Get Slack webhook (optional) (2 min)

---

## Phase 2: GitHub Configuration (10 minutes)

Add secrets to GitHub → Settings → Secrets → Actions:

- [ ] GUMROAD_API_KEY
- [ ] INSTAGRAM_ACCESS_TOKEN
- [ ] INSTAGRAM_BUSINESS_ACCOUNT_ID
- [ ] REPLICATE_API_TOKEN or DALLE_API_KEY
- [ ] KLAVIYO_API_KEY (or alternative email platform)
- [ ] GITHUB_ACTIONS_TOKEN
- [ ] SLACK_WEBHOOK_URL (optional)

---

## Phase 3: Verification (5 minutes)

```bash
npx ts-node scripts/automation/verify-automation.ts
```

- [ ] All API connections succeed
- [ ] No failures reported
- [ ] Shows "All critical APIs verified!"

---

## Phase 4: Testing (10 minutes)

Dry-run test:
```bash
gh workflow run automation-launch.yml \
  -f trigger_type=full-launch \
  -f dry_run=true
```

- [ ] Workflow completes successfully
- [ ] Opens automation-dashboard.html (loads OK)
- [ ] Check automation-status.json (valid JSON)

---

## Phase 5: Go Live (5 minutes)

```bash
gh workflow run automation-launch.yml \
  -f trigger_type=full-launch \
  -f dry_run=false
```

- [ ] Workflow succeeds
- [ ] Products published to Gumroad
- [ ] Posts appear on Instagram
- [ ] Email sent successfully
- [ ] Metrics updated
- [ ] Slack notified

---

## Phase 6: Ongoing (5 min/week)

- [ ] Weekly: Check dashboard
- [ ] Monthly: Verify schedules
- [ ] Quarterly: Rotate API keys

---

## Success = All Green ✅

1. ✅ Verification passes
2. ✅ Dry-run succeeds
3. ✅ Live automation publishes
4. ✅ All platforms updated
5. ✅ Dashboard working
6. ✅ Metrics tracking

**Status**: ☐ COMPLETE
