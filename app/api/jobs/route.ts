import { NextRequest, NextResponse } from 'next/server';
import { validateJobInput } from '@/lib/jobs';
import { getOpenJobs, createJob } from '@/lib/jobs.server';

// GET /api/jobs - List all open and accepted jobs
export async function GET(request: NextRequest) {
  try {
    const jobs = await getOpenJobs();
    return NextResponse.json(jobs);
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch jobs', details: (error as Error).message },
      { status: 500 }
    );
  }
}

// POST /api/jobs - Create a new job
export async function POST(request: NextRequest) {
  try {
    const userId = request.headers.get('x-user-id') || 'anonymous';
    const body = await request.json();

    // Validate input
    const { valid, errors } = validateJobInput(body);
    if (!valid) {
      return NextResponse.json(
        { error: errors.join(', ') },
        { status: 400 }
      );
    }

    // Create job in PostgreSQL database
    const newJob = await createJob(body, userId);
    return NextResponse.json(newJob, { status: 201 });
  } catch (error) {
    console.error('Failed to create job:', error);
    return NextResponse.json(
      { error: 'Failed to create job', details: (error as Error).message },
      { status: 500 }
    );
  }
}
