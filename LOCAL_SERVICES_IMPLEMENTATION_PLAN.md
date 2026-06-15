# Local Services Implementation Plan: MVP Edition

**Branch**: `feature/local-services-track`  
**Database**: PostgreSQL (already configured)  
**Auth**: NextAuth + Google OAuth (already configured)  
**Philosophy**: MVP first, sophistication later (build reputation → unlock premium features)

---

## Phase 1: MVP (This Week) - Zero Dependencies

**Goal**: Get 5+ jobs/day posted and executed. Simple, lean, fast.

### New Database Table

```sql
CREATE TABLE jobs (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  category VARCHAR(50) NOT NULL,  -- "Hauling", "Cleaning", "Handyman", etc.
  location VARCHAR(200) NOT NULL,
  pay NUMERIC(10,2) NOT NULL,      -- Customer pays
  miles NUMERIC(5,2) NOT NULL,     -- Distance
  margin NUMERIC(10,2) GENERATED ALWAYS AS (pay - miles * 0.72) STORED,
  description TEXT,
  photos JSON,                       -- Array of image URLs (if uploaded)
  status VARCHAR(20) DEFAULT 'open', -- open, accepted, completed, cancelled
  created_by_id UUID NOT NULL REFERENCES auth.users(id),  -- Contractor who posted
  accepted_by_id UUID,              -- Contractor who accepted job
  created_at TIMESTAMP DEFAULT now(),
  accepted_at TIMESTAMP,
  completed_at TIMESTAMP,
  
  -- Tracking
  source VARCHAR(50) DEFAULT 'web', -- "web", "api", "scraped"
  notes TEXT
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_accepted_by ON jobs(accepted_by_id);
```

### New Files (5 simple files)

```
app/
├── pages/
│   └── work.tsx                 (Job posting page)
├── api/
│   └── jobs/
│       ├── route.ts              (GET /api/jobs, POST /api/jobs)
│       └── [id]/route.ts         (GET /api/jobs/:id, PATCH /api/jobs/:id)
├── components/
│   ├── JobPostingForm.tsx       (Form to post new job)
│   └── JobBoard.tsx             (List of open/accepted jobs)
└── lib/
    └── jobs.ts                  (Job utilities, validation)
```

### Implementation Steps

#### Step 1: Database Table (5 min)
```bash
# Connect to postgres
psql postgresql://profitengine:password@localhost/profitengine

# Paste CREATE TABLE + indexes
# Done
```

#### Step 2: /work Page (30 min)
```typescript
// app/pages/work.tsx
import { JobPostingForm } from '@/components/JobPostingForm'
import { JobBoard } from '@/components/JobBoard'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'

export default function WorkPage() {
  const { data: session } = useSession()
  
  if (!session) redirect('/api/auth/signin')
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1>Post or Accept Work</h1>
      <div className="grid grid-cols-2 gap-6">
        <JobPostingForm />
        <JobBoard />
      </div>
    </div>
  )
}
```

#### Step 3: Job Posting Form (45 min)
```typescript
// app/components/JobPostingForm.tsx
import { useState } from 'react'
import { useSession } from 'next-auth/react'

const CATEGORIES = [
  'Hauling', 'Junk Removal', 'Cleaning', 'Handyman',
  'Landscaping', 'Pressure Washing', 'Moving', 'Other'
]

export function JobPostingForm() {
  const { data: session } = useSession()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    category: 'Hauling',
    location: 'Phoenix, AZ',
    pay: 300,
    miles: 0,
    description: ''
  })

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    const res = await fetch('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(formData)
    })
    
    if (res.ok) {
      // Reset form
      setFormData({ title: '', category: 'Hauling', ... })
      // Refresh job board
      window.location.reload()
    }
    
    setLoading(false)
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <input
        type="text"
        placeholder="Job title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        required
      />
      
      <select
        value={formData.category}
        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
      >
        {CATEGORIES.map(cat => (
          <option key={cat} value={cat}>{cat}</option>
        ))}
      </select>
      
      <input type="text" placeholder="Location" ... />
      <input type="number" placeholder="Pay ($)" min="300" ... />
      <input type="number" placeholder="Miles" min="0" max="35" ... />
      <textarea placeholder="Description..." ... />
      
      <button type="submit" disabled={loading}>
        {loading ? 'Posting...' : 'Post Job'}
      </button>
    </form>
  )
}
```

#### Step 4: Job Board Display (45 min)
```typescript
// app/components/JobBoard.tsx
import { useEffect, useState } from 'react'

export function JobBoard() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/jobs')
      .then(r => r.json())
      .then(data => {
        setJobs(data.filter(j => j.status === 'open'))
        setLoading(false)
      })
  }, [])

  return (
    <div className="space-y-4">
      <h2>Available Jobs</h2>
      {loading ? (
        <p>Loading...</p>
      ) : jobs.length === 0 ? (
        <p>No jobs available</p>
      ) : (
        jobs.map(job => (
          <div key={job.id} className="border p-4 rounded">
            <h3>{job.title}</h3>
            <p>{job.location} • {job.miles} miles</p>
            <p className="text-xl font-bold">${job.pay}</p>
            <p className="text-sm text-green-600">
              Margin: ${job.margin.toFixed(2)}
            </p>
            <button onClick={() => acceptJob(job.id)}>
              Accept Job
            </button>
          </div>
        ))
      )}
    </div>
  )
}
```

#### Step 5: API Endpoints (45 min)
```typescript
// app/api/jobs/route.ts
import { auth } from '@/lib/auth'
import { db } from '@/lib/db'

export async function GET() {
  const jobs = await db.query(`
    SELECT id, title, category, location, pay, miles, margin, status, created_at
    FROM jobs
    WHERE status IN ('open', 'accepted')
    ORDER BY created_at DESC
    LIMIT 50
  `)
  return Response.json(jobs)
}

export async function POST(request: Request) {
  const session = await auth()
  if (!session) return new Response('Unauthorized', { status: 401 })

  const { title, category, location, pay, miles, description } = await request.json()

  // Validate
  if (pay < 300) return new Response('Min pay $300', { status: 400 })
  if (miles > 35) return new Response('Max 35 miles', { status: 400 })
  if (!title || !category) return new Response('Missing fields', { status: 400 })

  // Create
  const job = await db.query(`
    INSERT INTO jobs (title, category, location, pay, miles, description, created_by_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING *
  `, [title, category, location, pay, miles, description, session.user.id])

  return Response.json(job[0], { status: 201 })
}
```

---

## Phase 2: Reputation Building (Weeks 2-4)

Once MVP is live and you have 10+ jobs completed:

- Track completion rate (% of jobs finished)
- Collect feedback/ratings
- Display contractor reputation
- Prioritize high-rated contractors

## Phase 3: Sophistication (Month 2+)

Once reputation is strong:

- Add Telegram notifications
- Auto-matching (AI suggests best contractor for job)
- Dynamic pricing (high-demand jobs cost more)
- Revenue commission model (if desired)
- Detailed analytics dashboard

---

## Testing Checklist (Before Launch)

- [ ] `npm run build` succeeds (no errors)
- [ ] `/work` page loads
- [ ] Create test job (works)
- [ ] Accept job (works)
- [ ] Database query succeeds
- [ ] NextAuth login required (works)
- [ ] Mobile responsive (test on phone)

---

## Rollback (If Needed)

```bash
git reset --hard restore-point-pre-local-services
```

Done. Back to safe state in 1 second.

---

## Success Definition (MVP)

✅ **Week 1**: 
- /work page live
- 5+ jobs posted
- 3+ jobs completed
- $500+ revenue captured

✅ **Week 2-4**:
- Consistent $500+/day
- 70%+ completion rate
- Contractor feedback collected
- Reputation metrics tracked

✅ **Month 2+**:
- Ready for sophistication (notifications, matching, pricing)
- Build reputation foundation first

---

## Start Implementation?

Ready to build this MVP? It's:
- 5 files (2 components, 2 API routes, 1 page)
- 200-300 lines total
- Zero external dependencies
- ~2-3 hours to code
- 1 hour to test

**Yes, proceed?** 👇
