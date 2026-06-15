// Server-side only job database operations
// This file uses pg (Node.js) and should only be imported in server code (API routes, server actions)
import { queryAll, queryOne, query } from './db';
import type { Job, CreateJobInput } from './jobs';

export async function getOpenJobs(): Promise<Job[]> {
  const jobs = await queryAll<any>(
    `SELECT id, title, category, location, pay, miles, margin, description,
            photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
            completed_at, source, notes
     FROM jobs
     WHERE status IN ('open', 'accepted')
     ORDER BY created_at DESC`,
  );
  return jobs.map(jobRowToJob);
}

export async function getJobById(id: string): Promise<Job | null> {
  const job = await queryOne<any>(
    `SELECT id, title, category, location, pay, miles, margin, description,
            photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
            completed_at, source, notes
     FROM jobs WHERE id = $1`,
    [id],
  );
  return job ? jobRowToJob(job) : null;
}

export async function createJob(
  input: CreateJobInput,
  userId: string,
  source = 'web'
): Promise<Job> {
  const { title, category, location, pay, miles, description } = input;

  const job = await queryOne<any>(
    `INSERT INTO jobs
     (title, category, location, pay, miles, description, created_by_id, source)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
     RETURNING id, title, category, location, pay, miles, margin, description,
               photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
               completed_at, source, notes`,
    [title, category, location, pay, miles, description || null, userId, source],
  );

  if (!job) throw new Error('Failed to create job');
  return jobRowToJob(job);
}

export async function acceptJob(jobId: string, contractorId: string): Promise<Job> {
  const job = await queryOne<any>(
    `UPDATE jobs
     SET status = 'accepted', accepted_by_id = $1, accepted_at = CURRENT_TIMESTAMP
     WHERE id = $2 AND status = 'open'
     RETURNING id, title, category, location, pay, miles, margin, description,
               photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
               completed_at, source, notes`,
    [contractorId, jobId],
  );

  if (!job) throw new Error('Job not found or already accepted');
  return jobRowToJob(job);
}

export async function completeJob(jobId: string): Promise<Job> {
  const job = await queryOne<any>(
    `UPDATE jobs
     SET status = 'completed', completed_at = CURRENT_TIMESTAMP
     WHERE id = $1 AND status = 'accepted'
     RETURNING id, title, category, location, pay, miles, margin, description,
               photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
               completed_at, source, notes`,
    [jobId],
  );

  if (!job) throw new Error('Job not found or not in accepted state');
  return jobRowToJob(job);
}

export async function getContractorJobs(contractorId: string): Promise<Job[]> {
  const jobs = await queryAll<any>(
    `SELECT id, title, category, location, pay, miles, margin, description,
            photos, status, created_by_id, accepted_by_id, created_at, accepted_at,
            completed_at, source, notes
     FROM jobs
     WHERE accepted_by_id = $1
     ORDER BY created_at DESC`,
    [contractorId],
  );
  return jobs.map(jobRowToJob);
}

function jobRowToJob(row: any): Job {
  return {
    id: row.id.toString(),
    title: row.title,
    category: row.category,
    location: row.location,
    pay: parseFloat(row.pay),
    miles: parseFloat(row.miles),
    margin: parseFloat(row.margin),
    description: row.description || '',
    photos: Array.isArray(row.photos) ? row.photos : [],
    status: row.status,
    created_by_id: row.created_by_id,
    accepted_by_id: row.accepted_by_id || undefined,
    created_at: new Date(row.created_at).toISOString(),
    accepted_at: row.accepted_at ? new Date(row.accepted_at).toISOString() : undefined,
    completed_at: row.completed_at ? new Date(row.completed_at).toISOString() : undefined,
    source: row.source,
    notes: row.notes || undefined,
  };
}
