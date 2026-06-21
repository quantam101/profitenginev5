/**
 * Client Authentication Utilities
 *
 * Provides functions to verify client API keys and validate webhook requests
 */

import { getClientByApiKey, getClientByEmail } from './client-db';

/**
 * Verify client API key from request header
 * Returns client ID if valid, null otherwise
 */
export async function verifyClientApiKey(
  apiKey: string | undefined | null
): Promise<string | null> {
  if (!apiKey || typeof apiKey !== 'string') {
    return null;
  }

  try {
    const client = await getClientByApiKey(apiKey);
    return client ? client.id : null;
  } catch (error) {
    console.error('API key verification failed:', error);
    return null;
  }
}

/**
 * Verify client from email and client ID
 */
export async function verifyClientEmail(
  email: string | undefined | null
): Promise<string | null> {
  if (!email || typeof email !== 'string') {
    return null;
  }

  try {
    const client = await getClientByEmail(email);
    return client ? client.id : null;
  } catch (error) {
    console.error('Email verification failed:', error);
    return null;
  }
}

/**
 * Extract API key from request headers
 */
export function getApiKeyFromHeaders(
  headers: Record<string, string | null>
): string | null {
  // Check 'X-API-Key' header (preferred)
  if (headers['x-api-key']) {
    return headers['x-api-key'];
  }

  // Check 'Authorization: Bearer <key>' header
  const authHeader = headers['authorization'];
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  return null;
}

/**
 * Hash API key for storage (basic approach)
 * In production, use bcrypt or similar
 */
export function hashApiKey(apiKey: string): string {
  // For MVP, we use simple base64 encoding
  // In production, use proper password hashing
  return Buffer.from(apiKey).toString('base64');
}

/**
 * Verify hashed API key
 */
export function verifyHashedApiKey(
  plaintext: string,
  hashed: string
): boolean {
  return hashApiKey(plaintext) === hashed;
}
