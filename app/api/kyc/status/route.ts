import { NextRequest, NextResponse } from 'next/server';
import { verifyAuthToken } from '@/lib/auth-utils';

export async function GET(request: NextRequest) {
  try {
    // Verify authentication
    const authHeader = request.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const token = authHeader.substring(7);
    const decoded = verifyAuthToken(token);

    if (!decoded) {
      return NextResponse.json(
        { error: 'Invalid or expired token' },
        { status: 401 }
      );
    }

    // In a real system, fetch KYC status from database
    // For now, return a mock status

    const mockStatuses = ['pending', 'approved', 'pending'];
    const randomStatus = mockStatuses[Math.floor(Math.random() * mockStatuses.length)];

    const statusResponses: Record<string, any> = {
      pending: {
        status: 'pending',
        message: 'Your identity verification is currently under review. We typically complete this process within 24 hours.',
        submittedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        nextSteps: [
          'Wait for verification team to review your submission',
          'You\'ll receive an email once the review is complete',
          'Check your dashboard for any additional information needed',
        ],
      },
      approved: {
        status: 'approved',
        message: 'Congratulations! Your identity has been verified. You now have access to all features including live trading.',
        submittedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        nextSteps: [
          'Fund your trading account',
          'Set up your trading strategies',
          'Begin live trading',
        ],
      },
      rejected: {
        status: 'rejected',
        message: 'Your verification could not be completed at this time. Please contact support for more information.',
        submittedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        completedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        nextSteps: [
          'Review the rejection reason in your email',
          'Contact support@alreadyherellc.com for assistance',
          'Resubmit with corrected information',
        ],
      },
    };

    return NextResponse.json(statusResponses[randomStatus] || statusResponses.pending, {
      status: 200,
    });
  } catch (error) {
    console.error('KYC status error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
