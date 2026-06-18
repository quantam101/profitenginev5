import crypto from 'crypto';

/**
 * Validate email format
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 * Returns error message if invalid, null if valid
 */
export function validatePassword(password: string): string | null {
  if (password.length < 8) {
    return 'Password must be at least 8 characters';
  }

  // Check for at least one uppercase letter
  if (!/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter';
  }

  // Check for at least one lowercase letter
  if (!/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter';
  }

  // Check for at least one number
  if (!/[0-9]/.test(password)) {
    return 'Password must contain at least one number';
  }

  return null;
}

/**
 * Generate a secure auth token (JWT-like format)
 * In production, use a proper JWT library like jsonwebtoken
 */
export function generateAuthToken(userId: number, email: string): string {
  const payload = {
    userId,
    email,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 7 * 24 * 60 * 60, // 7 days
  };

  // Create a simple token (in production, use jsonwebtoken)
  const token = Buffer.from(JSON.stringify(payload)).toString('base64');
  const signature = crypto
    .createHmac('sha256', process.env.NEXTAUTH_SECRET || 'dev-secret')
    .update(token)
    .digest('hex');

  return `${token}.${signature}`;
}

/**
 * Verify an auth token
 */
export function verifyAuthToken(token: string): { userId: number; email: string } | null {
  try {
    const [tokenPart, signaturePart] = token.split('.');

    if (!tokenPart || !signaturePart) {
      return null;
    }

    // Verify signature
    const expectedSignature = crypto
      .createHmac('sha256', process.env.NEXTAUTH_SECRET || 'dev-secret')
      .update(tokenPart)
      .digest('hex');

    if (signaturePart !== expectedSignature) {
      return null;
    }

    // Decode payload
    const payload = JSON.parse(Buffer.from(tokenPart, 'base64').toString('utf-8'));

    // Check expiration
    if (payload.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }

    return {
      userId: payload.userId,
      email: payload.email,
    };
  } catch (error) {
    return null;
  }
}

/**
 * Hash password (in production, use bcrypt)
 */
export function hashPassword(password: string): string {
  return crypto
    .createHash('sha256')
    .update(password + (process.env.PASSWORD_SALT || 'dev-salt'))
    .digest('hex');
}

/**
 * Verify password against hash
 */
export function verifyPasswordHash(password: string, hash: string): boolean {
  return hashPassword(password) === hash;
}
