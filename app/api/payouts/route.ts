import { NextRequest, NextResponse } from 'next/server';
import { createPayout, getContractorPayouts } from '@/lib/payouts.server';

// POST /api/payouts - Create a payout to a contractor
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { jobId, contractorId, contractorEmail, contractorName, amount } = body;

    // Validate required fields
    if (!jobId || !contractorId || !contractorEmail || !amount) {
      return NextResponse.json(
        { error: 'Missing required fields: jobId, contractorId, contractorEmail, amount' },
        { status: 400 }
      );
    }

    if (amount < 100) {
      return NextResponse.json(
        { error: 'Minimum payout is $1.00' },
        { status: 400 }
      );
    }

    // Create payout
    const payout = await createPayout({
      jobId,
      contractorId,
      contractorEmail,
      contractorName,
      amount,
    });

    return NextResponse.json(payout, { status: 201 });
  } catch (error) {
    console.error('Failed to create payout:', error);
    return NextResponse.json(
      { error: 'Failed to create payout', details: (error as Error).message },
      { status: 500 }
    );
  }
}

// GET /api/payouts?contractorId=... - Get payouts for a contractor
export async function GET(request: NextRequest) {
  try {
    const contractorId = request.nextUrl.searchParams.get('contractorId');

    if (!contractorId) {
      return NextResponse.json(
        { error: 'contractorId query parameter is required' },
        { status: 400 }
      );
    }

    const payouts = await getContractorPayouts(contractorId);
    return NextResponse.json(payouts);
  } catch (error) {
    console.error('Failed to fetch payouts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch payouts', details: (error as Error).message },
      { status: 500 }
    );
  }
}
