/**
 * Caching utility for Vercel Serverless Functions
 * Reduces invocations and improves response times
 */

export const CACHE_CONFIG = {
  // Immutable data (never changes) — cache forever
  IMMUTABLE: {
    'Cache-Control': 'public, max-age=31536000, immutable',
  },

  // Long-lived data (updates rarely) — cache 24 hours
  LONG: {
    'Cache-Control': 'public, max-age=86400, s-maxage=86400',
  },

  // Standard data (updates sometimes) — cache 1 hour
  STANDARD: {
    'Cache-Control': 'public, max-age=3600, s-maxage=3600',
  },

  // Short-lived data (updates frequently) — cache 5 minutes
  SHORT: {
    'Cache-Control': 'public, max-age=300, s-maxage=300',
  },

  // Sensitive data (user-specific) — cache 1 minute, private
  PRIVATE_SHORT: {
    'Cache-Control': 'private, max-age=60, s-maxage=0',
  },

  // Real-time data (must not cache)
  NO_CACHE: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
  },
};

export function getCacheHeaders(
  type: keyof typeof CACHE_CONFIG
): HeadersInit {
  return {
    ...CACHE_CONFIG[type],
    'Pragma': 'cache' as any,
    'Expires': new Date(Date.now() + 86400000).toUTCString(),
  };
}
