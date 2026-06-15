# Local Services Track: Safety & Rollback Checklist

**Branch**: `feature/local-services-track`  
**Restore Point**: `restore-point-pre-local-services` (git tag)  
**Current Commit**: `01ed5b3`

---

## Restore Instructions (If Needed)

### Option 1: Instant Rollback (Nuclear)
```bash
# Go back to safe state immediately
git checkout restore-point-pre-local-services

# Or keep local services branch, just reset to restore point
git reset --hard restore-point-pre-local-services
```

### Option 2: Soft Rollback (Review Changes First)
```bash
# See what changed since restore point
git diff restore-point-pre-local-services..HEAD

# Cherry-pick only safe changes
git cherry-pick <commit-hash>
```

### Option 3: Branch Rollback
```bash
# Delete local services branch, go back to main
git checkout main
git branch -D feature/local-services-track
```

---

## Changes Made (Tracking)

### Files Modified
- [ ] `app/api/ai-vp/leads/route.ts` (already enhanced, NOT touched)
- [ ] `app/components/` (work intake form - NEW)
- [ ] `app/pages/work.tsx` (job posting page - NEW)
- [ ] `public/` (new assets if needed)
- [ ] `.github/workflows/` (new CI/CD for local services - CAREFUL)

### Files Created
- [ ] `app/components/JobPostingForm.tsx` (NEW - safe)
- [ ] `app/components/ContractorJobBoard.tsx` (NEW - safe)
- [ ] `app/pages/work.tsx` (NEW - safe)
- [ ] `app/api/jobs/route.ts` (NEW - safe)
- [ ] `docs/LOCAL_SERVICES_SPEC.md` (docs only - safe)

### Files NOT Touched (Protected)
- ✅ `app/api/ai-vp/leads/route.ts` (enhanced, don't change)
- ✅ `.github/workflows/daily-content.yml` (production, don't change)
- ✅ `scripts/` (production, don't change)
- ✅ `app/api/dispatch/` (B2B, don't change)
- ✅ `app/pages/index.tsx` (homepage - safe to add CTA only)

---

## Testing Checklist (Before Merge to Main)

### Phase 1: New Pages Don't Break
- [ ] `npm run build` (no errors)
- [ ] `npm run dev` (local dev server starts)
- [ ] Visit `http://localhost:3000/work` (new page loads)
- [ ] Visit `http://localhost:3000/` (homepage loads, B2B unchanged)
- [ ] Visit `http://localhost:3000/dispatch` (existing dispatch unchanged)

### Phase 2: API Endpoints Work
- [ ] POST `/api/jobs` (create job - test)
- [ ] GET `/api/jobs` (list jobs - test)
- [ ] POST `/api/ai-vp/leads` (lead scraper unchanged - verify)
- [ ] Existing B2B endpoints still work (spot check 3)

### Phase 3: No Regressions
- [ ] Existing dispatch form still works
- [ ] RFQ form still works
- [ ] Email notifications still send (if applicable)
- [ ] Database queries unchanged (if DB involved)
- [ ] Build time <5 min (no bloat)

### Phase 4: Security/Data
- [ ] No SQL injection vectors (sanitize all inputs)
- [ ] No XSS in job titles (HTML escape)
- [ ] No auth bypass (existing auth still required)
- [ ] No exposed secrets (check git diff for API keys)
- [ ] No public data exposure (job details privacy)

---

## Rollback Scenarios

### If Build Fails
```bash
git reset --hard restore-point-pre-local-services
# Fix issue, commit separately
```

### If Homepage Breaks
```bash
# Revert only homepage changes
git checkout restore-point-pre-local-services -- app/pages/index.tsx
git commit -m "Revert homepage to safe state"
```

### If API Breaks B2B
```bash
# Delete new API endpoints, keep new pages
git rm app/api/jobs/route.ts
git commit -m "Remove new jobs API, keep pages"
```

### If Performance Degrades
```bash
# Check bundle size impact
npm run build -- --analyze
# If >+500kb, rollback
git reset --hard restore-point-pre-local-services
```

---

## Success Criteria (Before Merge to Main)

- ✅ Build succeeds (`npm run build`)
- ✅ No TypeScript errors
- ✅ All tests pass (if applicable)
- ✅ No regressions in existing B2B flows
- ✅ New pages load without errors
- ✅ New APIs respond correctly
- ✅ No sensitive data in git diff
- ✅ Code review passes (if team)
- ✅ Tested on mobile (responsive)
- ✅ Performance acceptable (<3s load time)

---

## Branch Strategy

```
main (production - PROTECTED)
├─ restore-point-pre-local-services (safe tag)
└─ feature/local-services-track (working branch)
    ├─ [WIP] Job posting form
    ├─ [WIP] Job board display
    ├─ [WIP] API endpoints
    └─ [MERGE] → main (once tested)
```

---

## Commit History (Feature Branch)

Each commit should be atomic and reversible:

```
1. feat: add /work page skeleton (NEW - safe)
2. feat: add JobPostingForm component (NEW - safe)
3. feat: add ContractorJobBoard component (NEW - safe)
4. feat: add POST /api/jobs endpoint (NEW - safe)
5. feat: add GET /api/jobs endpoint (NEW - safe)
6. feat: update homepage CTA for local services (MODIFY - safe)
7. feat: add job validation + sanitization (NEW - safe)
8. test: verify existing B2B flows unchanged (TEST - safe)
```

Each commit is independently safe and revertible.

---

## Go/No-Go Checklist

### Before Starting Any Changes
- [ ] Restore point created? ✅ Yes (`restore-point-pre-local-services`)
- [ ] On new branch? ✅ Yes (`feature/local-services-track`)
- [ ] Working tree clean? ✅ Yes (no uncommitted changes)
- [ ] All tests passing? ⚠️ Check with `npm test`

### Before Merging to Main
- [ ] Build succeeds? ⚠️ Check with `npm run build`
- [ ] No regressions? ⚠️ Verify existing flows
- [ ] Code reviewed? ⚠️ If team project
- [ ] Ready for production? ⚠️ Manual testing complete

### If Anything Breaks
```bash
# Instant rollback (1 command)
git reset --hard restore-point-pre-local-services
```

---

## Questions Before Proceeding

1. **Database**: Does job data go to Supabase, MongoDB, or Postgres? (Need to create new table)
2. **Auth**: Do contractors need login, or anonymous job posting?
3. **Payment**: Should job posting be free, or charge fee?
4. **Notifications**: Telegram, email, SMS, or in-app alerts for new jobs?
5. **Moderation**: Auto-publish jobs, or manual approval before going live?

---

**Status**: Ready to proceed safely. ✅ Restore point created. Ready to implement.
