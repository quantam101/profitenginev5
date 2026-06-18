import { NextRequest, NextResponse } from 'next/server';

/**
 * MFA Verification Endpoint
 * Validates 6-digit MFA code from authenticator app
 * In production, integrate with a real TOTP provider or service
 */

async function verifyMFACode(code: string, email: string): Promise<boolean> {
  // TODO: Integrate with real MFA service
  // For now, accept any valid 6-digit code as placeholder
  // In production, use TOTP library or third-party MFA service

  // Example implementation using a real service would look like:
  // const verified = await verifyTOTPCode(email, code, userSecret);

  // Placeholder: accept if code is 6 digits
  // NEVER use this in production without real MFA
  if (!/^\d{6}$/.test(code)) {
    return false;
  }

  // In production, verify against stored TOTP secret
  // This is just a placeholder to accept valid format
  return true;
}

export async function POST(req: NextRequest) {
  try {
    const { code } = await req.json();

    if (!code || typeof code !== 'string') {
      return NextResponse.json(
        { error: 'Invalid MFA code format' },
        { status: 400 }
      );
    }

    const userEmail = req.headers.get('x-user-email') || 'dispatch@alreadyherellc.com';
    const clientIP = req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip') || 'unknown';

    // Verify MFA code
    const isValid = await verifyMFACode(code, userEmail);

    if (!isValid) {
      console.warn(`[Admin] MFA verification failed for ${userEmail}`);
      return NextResponse.json(
        { error: 'Invalid MFA code' },
        { status: 401 }
      );
    }

    // Log successful MFA verification
    console.log(`[Admin] MFA verified for ${userEmail} from ${clientIP}`);

    const sessionData = {
      authenticated: true,
      email: userEmail,
      role: 'admin',
      ipAddress: clientIP,
      lastVerified: Date.now(),
      mfaVerified: true,
    };

    return NextResponse.json(sessionData, {
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('[Admin] MFA verification error:', error);
    return NextResponse.json(
      { error: 'MFA verification failed' },
      { status: 500 }
    );
  }
}
