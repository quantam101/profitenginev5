import { NextRequest, NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';
import { verifyAuthToken } from '@/lib/auth-utils';

export const runtime = 'nodejs';

interface KYCData {
  firstName: string;
  lastName: string;
  age: number;
  tradingExperience: 'beginner' | 'intermediate' | 'advanced';
  riskTolerance: 'low' | 'moderate' | 'high';
  investmentGoals: string;
  agreeToTerms: boolean;
}

type UserDocument = {
  userId: number;
  email: string;
  tradingTier?: string;
  updatedAt?: Date;
  lastActiveAt?: Date;
};

type KYCSubmissionDocument = KYCData & {
  userId: number;
  email: string;
  status: 'pending_review';
  submittedAt: Date;
  updatedAt: Date;
};

type MongoGlobal = typeof globalThis & {
  __profitEngineMongoClientPromise?: Promise<MongoClient>;
};

function getMongoUri(): string {
  const uri = process.env.MONGODB_URI || process.env.DATABASE_URL;

  if (!uri || !uri.startsWith('mongodb')) {
    throw new Error('KYC storage is not configured. Set MONGODB_URI to a MongoDB connection string.');
  }

  return uri;
}

function getDatabaseName(): string {
  return process.env.MONGODB_DB || process.env.PROFITENGINE_DB || 'profitenginev5';
}

async function getMongoClient(): Promise<MongoClient> {
  const mongoGlobal = globalThis as MongoGlobal;

  if (!mongoGlobal.__profitEngineMongoClientPromise) {
    mongoGlobal.__profitEngineMongoClientPromise = new MongoClient(getMongoUri()).connect();
  }

  return mongoGlobal.__profitEngineMongoClientPromise;
}

async function sendKYCVerificationEmailIfConfigured(email: string, verificationLink: string): Promise<void> {
  const apiKey = process.env.SENDGRID_API_KEY;

  if (!apiKey) {
    return;
  }

  const fromEmail = process.env.EMAIL_FROM || 'noreply@profitengine.alreadyherellc.com';
  const replyTo = process.env.EMAIL_REPLY_TO || 'support@alreadyherellc.com';

  const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      personalizations: [
        {
          to: [{ email }],
          subject: 'Complete Your Identity Verification - ProfitEngine',
        },
      ],
      from: { email: fromEmail, name: 'ProfitEngine' },
      reply_to: { email: replyTo },
      content: [
        {
          type: 'text/html',
          value: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h1 style="color: #5aa2ff;">KYC Verification Submitted</h1>
              <p>Your identity verification has been received and is pending review.</p>
              <p style="margin: 30px 0;">
                <a href="${verificationLink}" style="background-color: #5aa2ff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">
                  View KYC Status
                </a>
              </p>
              <p style="color: #666; font-size: 12px;">ProfitEngine Trading System</p>
            </div>
          `,
        },
      ],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`SendGrid email failed: ${response.status} ${body}`);
  }
}

function validateKYC(body: KYCData): string | null {
  if (!body.firstName || !body.lastName) {
    return 'First and last name are required';
  }

  if (body.age < 18) {
    return 'Must be at least 18 years old';
  }

  if (!body.investmentGoals || body.investmentGoals.trim().length === 0) {
    return 'Investment goals are required';
  }

  if (!body.agreeToTerms) {
    return 'Must agree to terms';
  }

  return null;
}

export async function POST(request: NextRequest) {
  try {
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
    const validationError = validateKYC(body);

    if (validationError) {
      return NextResponse.json(
        { error: validationError },
        { status: 400 }
      );
    }

    const client = await getMongoClient();
    const db = client.db(getDatabaseName());
    const users = db.collection<UserDocument>('users');
    const kycSubmissions = db.collection<KYCSubmissionDocument>('kyc_submissions');

    const user = await users.findOne({ userId: decoded.userId });
    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    const now = new Date();

    await kycSubmissions.updateOne(
      { userId: decoded.userId },
      {
        $set: {
          ...body,
          userId: decoded.userId,
          email: user.email,
          status: 'pending_review',
          updatedAt: now,
        },
        $setOnInsert: {
          submittedAt: now,
        },
      },
      { upsert: true }
    );

    await users.updateOne(
      { userId: decoded.userId },
      {
        $set: {
          updatedAt: now,
          lastActiveAt: now,
        },
      }
    );

    try {
      const verificationLink = `${process.env.NEXT_PUBLIC_SITE_URL || 'https://app.profitengine.alreadyherellc.com'}/kyc-status`;
      await sendKYCVerificationEmailIfConfigured(user.email, verificationLink);
    } catch (emailError) {
      console.error('Failed to send KYC verification email:', emailError);
    }

    return NextResponse.json(
      {
        success: true,
        message: 'KYC verification submitted successfully',
        user: {
          id: user.userId,
          email: user.email,
          kycStatus: 'pending_review',
        },
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('KYC submission error:', error);

    const message = error instanceof Error ? error.message : 'Internal server error';
    const isConfigError = message.includes('KYC storage is not configured');

    return NextResponse.json(
      { error: isConfigError ? message : 'Internal server error' },
      { status: isConfigError ? 503 : 500 }
    );
  }
}
