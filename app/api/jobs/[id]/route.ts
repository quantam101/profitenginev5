import { NextRequest, NextResponse } from 'next/server';
import { getJobById, acceptJob, completeJob } from '@/lib/jobs.server';

// PATCH /api/jobs/[id] - Accept or complete a job
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const userId = request.headers.get('x-user-id') || 'anonymous';
    const { id } = await params;

    const body = await request.json();
    const { action } = body;

    if (!['accept', 'complete'].includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action. Must be "accept" or "complete"' },
        { status: 400 }
      );
    }

    const updatedJob = action === 'accept'
      ? await acceptJob(id, userId)
      : await completeJob(id);

    return NextResponse.json(updatedJob);
  } catch (error) {
    console.error('Failed to update job:', error);
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}

// GET /api/jobs/[id] - Get a single job
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const job = await getJobById(id);

    if (!job) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error('Failed to fetch job:', error);
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}
