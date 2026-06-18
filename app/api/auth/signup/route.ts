import { NextRequest, NextResponse } from 'next/server';
import { ClientsDB } from '@/lib/clients-db';
import { sendWelcomeEmail } from '@/lib/email-service';
import { generateAuthToken, validatePassword, validateEmail } from '@/lib/auth-utils';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, capitalAmount, riskPreference } = body;

    // Validation
    if (!email || !password || !capitalAmount) {
      return NextResponse.json(
        { error: 'Missing required fields: email, password, capitalAmount' },
        { status: 400 }
      );
    }

    // Validate email format
    if (!validateEmail(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Validate password strength
    const passwordError = validatePassword(password);
    if (passwordError) {
      return NextResponse.json(
        { error: passwordError },
        { status: 400 }
      );
    }

    // Validate capital amount
    if (typeof capitalAmount !== 'number' || capitalAmount < 1000) {
      return NextResponse.json(
        { error: 'Capital amount must be at least $1,000' },
        { status: 400 }
      );
    }

    // Validate risk preference
    const validRiskPreferences = ['conservative', 'moderate', 'aggressive'];
    if (!validRiskPreferences.includes(riskPreference)) {
      return NextResponse.json(
        { error: 'Invalid risk preference' },
        { status: 400 }
      );
    }

    // Check if user already exists
    const db = new ClientsDB();
    const existingUser = db.getUserByEmail(email);

    if (existingUser) {
      db.close();
      return NextResponse.json(
        { error: 'Email already registered' },
        { status: 409 }
      );
    }

    // Create user in database
    const user = db.createUser(email, 'free');

    // Store metadata in custom fields (if your schema supports it)
    // For now, we'll just track basic user creation
    db.updateUserActivity(user.id);

    db.close();

    // Generate auth token
    const token = generateAuthToken(user.id, email);

    // Send welcome email
    try {
      await sendWelcomeEmail({
        email,
        username: email.split('@')[0],
        capitalAmount,
        riskPreference,
      });
    } catch (emailError) {
      console.error('Failed to send welcome email:', emailError);
      // Don't fail the signup if email fails, but log it
    }

    return NextResponse.json(
      {
        success: true,
        message: 'Account created successfully',
        token,
        user: {
          id: user.id,
          email: user.email,
          tier: user.tradingTier,
          createdAt: user.createdAt,
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
