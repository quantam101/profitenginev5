import { NextRequest, NextResponse } from 'next/server';

/**
 * Admin Session Verification
 * Validates admin access based on email and IP address
 * Enforces MFA requirement for production admin access
 */

const ADMIN_EMAIL = 'dispatch@alreadyherellc.com';
const ALLOWED_IPS = process.env.ADMIN_ALLOWED_IPS?.split(',') || [];

export async function POST(req: NextRequest) {
  try {
    const clientIP = req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip') || 'unknown';

    // Get user from headers/session (in production, integrate with NextAuth)
    const userEmail = req.headers.get('x-user-email') || req.headers.get('user-email');

    // Check if authorized email
    if (userEmail !== ADMIN_EMAIL) {
      return NextResponse.json(
        { error: 'Unauthorized: Admin access required' },
        { status: 401 }
      );
    }

    // Check IP whitelist if configured
    if (ALLOWED_IPS.length > 0 && !ALLOWED_IPS.includes(clientIP)) {
      console.warn(`[Admin] Unauthorized IP attempt: ${clientIP} for ${userEmail}`);
      return NextResponse.json(
        { error: 'Unauthorized: IP not whitelisted' },
        { status: 401 }
      );
    }

    // Check if MFA is required (always true for production)
    const requireMFA = process.env.NODE_ENV === 'production';

    if (requireMFA) {
      // Return 403 to trigger MFA flow
      return NextResponse.json(
        { error: 'MFA required', authenticated: false },
        { status: 403 }
      );
    }

    // Session verified
    const sessionData = {
      authenticated: true,
      email: userEmail,
      role: 'admin',
      ipAddress: clientIP,
      lastVerified: Date.now(),
    };

    // Log successful verification
    console.log(`[Admin] Session verified for ${userEmail} from ${clientIP}`);

    return NextResponse.json(sessionData, {
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('[Admin] Verification error:', error);
    return NextResponse.json(
      { error: 'Session verification failed' },
      { status: 500 }
    );
  }
}
