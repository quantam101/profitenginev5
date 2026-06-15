import { NextRequest, NextResponse } from 'next/server';

// PATCH /api/jobs/[id] - Accept or complete a job
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    // TODO: Add NextAuth session validation
    const userId = request.headers.get('x-user-id') || 'anonymous';
    const { id } = await params;

    const body = await request.json();
    const { action } = body;

    // Validate action
    if (!['accept', 'complete'].includes(action)) {
      return NextResponse.json(
        { error: 'Invalid action' },
        { status: 400 }
      );
    }

    // TODO: Update job in PostgreSQL database
    // For now, return mock response
    const updatedJob = {
      id,
      status: action === 'accept' ? 'accepted' : 'completed',
      accepted_by_id: userId,
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
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    // Get job from database
    // This is a placeholder - adjust based on your DB setup
    const job = {
      id,
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
