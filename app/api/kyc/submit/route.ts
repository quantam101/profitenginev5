import { NextRequest, NextResponse } from 'next/server';
import { ClientsDB } from '@/lib/clients-db';
import { verifyAuthToken } from '@/lib/auth-utils';
import { sendKYCVerificationEmail } from '@/lib/email-service';

interface KYCData {
  firstName: string;
  lastName: string;
  age: number;
  tradingExperience: 'beginner' | 'intermediate' | 'advanced';
  riskTolerance: 'low' | 'moderate' | 'high';
  investmentGoals: string;
  agreeToTerms: boolean;
}

export async function POST(request: NextRequest) {
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

    const body = await request.json() as KYCData;

    // Validation
    if (!body.firstName || !body.lastName) {
      return NextResponse.json(
        { error: 'First and last name are required' },
        { status: 400 }
      );
    }

    if (body.age < 18) {
      return NextResponse.json(
        { error: 'Must be at least 18 years old' },
        { status: 400 }
      );
    }

    if (!body.investmentGoals || body.investmentGoals.trim().length === 0) {
      return NextResponse.json(
        { error: 'Investment goals are required' },
        { status: 400 }
      );
    }

    if (!body.agreeToTerms) {
      return NextResponse.json(
        { error: 'Must agree to terms' },
        { status: 400 }
      );
    }

    const db = new ClientsDB();

    // Get user
    const user = db.getUser(decoded.userId);
    if (!user) {
      db.close();
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // In a real system, you would:
    // 1. Store KYC data in a secure database
    // 2. Run automated verification (ID verification service)
    // 3. Send to compliance team for review
    // 4. Update user tier based on verification status

    // For now, we'll update a metadata field (you'd need to add this to the schema)
    // db.updateUserMetadata(user.id, {
    //   kyc_status: 'pending',
    //   kyc_first_name: body.firstName,
    //   kyc_last_name: body.lastName,
    //   kyc_age: body.age,
    //   kyc_trading_experience: body.tradingExperience,
    //   kyc_risk_tolerance: body.riskTolerance,
    //   kyc_investment_goals: body.investmentGoals,
    //   kyc_submitted_at: new Date().toISOString(),
    // });

    // Send verification email
    try {
      const verificationLink = `${process.env.NEXT_PUBLIC_SITE_URL || 'https://app.profitengine.alreadyherellc.com'}/kyc-status`;
      await sendKYCVerificationEmail(user.email, verificationLink);
    } catch (emailError) {
      console.error('Failed to send KYC verification email:', emailError);
      // Don't fail the request if email fails
    }

    db.close();

    return NextResponse.json(
      {
        success: true,
        message: 'KYC verification submitted successfully',
        user: {
          id: user.id,
          email: user.email,
          kycStatus: 'pending_review',
        },
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('KYC submission error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
