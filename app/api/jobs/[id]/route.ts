import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/auth';

// PATCH /api/jobs/[id] - Accept or complete a job
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const session = await auth();

    // Require authentication
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'You must be logged in' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { action } = body;

    // Validate action
    if (!['accept', 'complete'].includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    // Update job in database
    // This is a placeholder - adjust based on your DB setup
    const updatedJob = {
      id: params.id,
      status: action === 'accept' ? 'accepted' : 'completed',
      accepted_by_id: session.user.id,
      accepted_at: new Date().toISOString(),
    };

    return NextResponse.json(updatedJob);
  } catch (error) {
    console.error('Failed to update job:', error);
    return NextResponse.json(
      { error: 'Failed to update job' },
      { status: 500 }
    );
  }
}

// GET /api/jobs/[id] - Get a single job
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Get job from database
    // This is a placeholder - adjust based on your DB setup
    const job = {
      id: params.id,
      title: 'Sample Job',
      status: 'open',
    };

    return NextResponse.json(job);
  } catch (error) {
    console.error('Failed to fetch job:', error);
    return NextResponse.json(
      { error: 'Failed to fetch job' },
      { status: 500 }
    );
  }
}
