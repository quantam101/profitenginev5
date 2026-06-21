import { NextRequest, NextResponse } from 'next/server';
import { MongoClient } from 'mongodb';
import { generateAuthToken, hashPassword, validateEmail, validatePassword } from '@/lib/auth-utils';

export const runtime = 'nodejs';

type SignupDocument = {
  userId: number;
  email: string;
  passwordHash: string;
  tradingTier: 'free';
  capitalAmount: number;
  riskPreference: 'conservative' | 'moderate' | 'aggressive';
  createdAt: Date;
  updatedAt: Date;
  lastActiveAt: Date;
};

type MongoGlobal = typeof globalThis & {
  __profitEngineMongoClientPromise?: Promise<MongoClient>;
};

function getMongoUri(): string {
  const uri = process.env.MONGODB_URI || process.env.DATABASE_URL;

  if (!uri || !uri.startsWith('mongodb')) {
    throw new Error('Signup storage is not configured. Set MONGODB_URI to a MongoDB connection string.');
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

async function sendWelcomeEmailIfConfigured(options: {
  email: string;
  username: string;
  capitalAmount: number;
  riskPreference: string;
}): Promise<void> {
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
          to: [{ email: options.email }],
          subject: 'Welcome to ProfitEngine - Your Trading Account is Ready',
        },
      ],
      from: { email: fromEmail, name: 'ProfitEngine' },
      reply_to: { email: replyTo },
      content: [
        {
          type: 'text/html',
          value: `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h1 style="color: #5aa2ff;">Welcome to ProfitEngine</h1>
              <p>Hi ${options.username},</p>
              <p>Your account has been created and is ready for paper-trading setup.</p>
              <ul>
                <li>Starting capital: $${options.capitalAmount.toLocaleString()}</li>
                <li>Risk preference: ${options.riskPreference}</li>
                <li>Tier: Free</li>
              </ul>
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

function createUserId(): number {
  return Date.now() * 1000 + Math.floor(Math.random() * 1000);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, capitalAmount, riskPreference } = body;

    if (!email || !password || capitalAmount === undefined || capitalAmount === null) {
      return NextResponse.json(
        { error: 'Missing required fields: email, password, capitalAmount' },
        { status: 400 }
      );
    }

    if (!validateEmail(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      return NextResponse.json(
        { error: passwordError },
        { status: 400 }
      );
    }

    if (typeof capitalAmount !== 'number' || capitalAmount < 1000) {
      return NextResponse.json(
        { error: 'Capital amount must be at least $1,000' },
        { status: 400 }
      );
    }

    const validRiskPreferences = ['conservative', 'moderate', 'aggressive'] as const;
    if (!validRiskPreferences.includes(riskPreference)) {
      return NextResponse.json(
        { error: 'Invalid risk preference' },
        { status: 400 }
      );
    }

    const normalizedEmail = email.toLowerCase().trim();
    const client = await getMongoClient();
    const users = client.db(getDatabaseName()).collection<SignupDocument>('users');

    await users.createIndex({ email: 1 }, { unique: true });

    const existingUser = await users.findOne({ email: normalizedEmail });

    if (existingUser) {
      return NextResponse.json(
        { error: 'Email already registered' },
        { status: 409 }
      );
    }

    const now = new Date();
    const userId = createUserId();
    const user: SignupDocument = {
      userId,
      email: normalizedEmail,
      passwordHash: hashPassword(password),
      tradingTier: 'free',
      capitalAmount,
      riskPreference,
      createdAt: now,
      updatedAt: now,
      lastActiveAt: now,
    };

    await users.insertOne(user);

    const token = generateAuthToken(userId, normalizedEmail);

    try {
      await sendWelcomeEmailIfConfigured({
        email: normalizedEmail,
        username: normalizedEmail.split('@')[0],
        capitalAmount,
        riskPreference,
      });
    } catch (emailError) {
      console.error('Failed to send welcome email:', emailError);
    }

    return NextResponse.json(
      {
        success: true,
        message: 'Account created successfully',
        token,
        user: {
          id: user.userId,
          email: user.email,
          tier: user.tradingTier,
          createdAt: user.createdAt.toISOString(),
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Signup error:', error);

    const message = error instanceof Error ? error.message : 'Internal server error';
    const isConfigError = message.includes('Signup storage is not configured');

    return NextResponse.json(
      { error: isConfigError ? message : 'Internal server error' },
      { status: isConfigError ? 503 : 500 }
    );
  }
}
