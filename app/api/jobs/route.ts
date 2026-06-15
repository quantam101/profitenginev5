import { NextRequest, NextResponse } from 'next/server';
import { validateJobInput } from '@/lib/jobs';

// GET /api/jobs - List all open and accepted jobs
export async function GET(request: NextRequest) {
  try {
    // Placeholder: Get database connection from your configured provider
    // TODO: Connect to PostgreSQL jobs table
    const jobs = [
      {
        id: '1',
        title: 'Remove 3 couches + debris',
        category: 'Junk Removal',
        location: 'Phoenix, AZ',
        pay: 350,
        miles: 8,
        margin: 344.24,
        status: 'open',
        created_at: new Date().toISOString(),
        created_by_id: 'user-1',
        description: 'Estate sale cleanup',
      },
    ];

    return NextResponse.json(jobs);
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch jobs' },
      { status: 500 }
    );
  }
}

// POST /api/jobs - Create a new job
export async function POST(request: NextRequest) {
  try {
    // TODO: Add NextAuth session validation
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

    // TODO: Create job in PostgreSQL database
    // For now, return mock response
    const newJob = {
      id: Math.random().toString(36).substr(2, 9),
      title: body.title,
      category: body.category,
      location: body.location,
      pay: body.pay,
      miles: body.miles,
      margin: body.pay - body.miles * 0.72,
      description: body.description || '',
      status: 'open',
      created_by_id: userId,
      created_at: new Date().toISOString(),
    };

    return NextResponse.json(newJob, { status: 201 });
  } catch (error) {
    console.error('Failed to create job:', error);
    return NextResponse.json(
      { error: 'Failed to create job' },
      { status: 500 }
    );
  }
}
