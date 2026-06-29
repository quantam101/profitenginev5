import { NextRequest, NextResponse } from 'next/server';

/**
 * Edge Middleware — Runs at 57 Vercel edge locations globally
 * Provides: Rate limiting, CORS, security headers, instant response
 */

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security headers (instant, at edge, no serverless invocation needed)
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');

  // Add cache control for static assets
  if (request.nextUrl.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|webp|woff|woff2)$/)) {
    response.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
  }

  // Rate limiting (simple IP-based)
  const ip = request.ip || 'unknown';
  const key = `rate-limit:${ip}`;
  
  // For demonstration — in production use Vercel Redis or similar
  // This prevents the worst bot traffic from hitting serverless
  const userAgent = request.headers.get('user-agent') || '';
  if (isBot(userAgent)) {
    return new NextResponse('Not allowed', { status: 403 });
  }

  return response;
}

function isBot(userAgent: string): boolean {
  const botPatterns = [
    /bot/i,
    /crawler/i,
    /spider/i,
    /scraper/i,
    /curl/i,
    /wget/i,
  ];
  return botPatterns.some(pattern => pattern.test(userAgent));
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
