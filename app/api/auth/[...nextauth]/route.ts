import NextAuth from 'next-auth';
import { NextResponse } from 'next/server';
import { authOptions, authReady } from '@/lib/auth';

const handler = authReady ? NextAuth(authOptions) : null;

function authUnavailable() {
  return NextResponse.json(
    {
      ok: false,
      status: 'auth_unavailable',
      message: 'Authentication is disabled until NEXTAUTH_SECRET, GOOGLE_CLIENT_ID, and GOOGLE_CLIENT_SECRET are configured in the production environment.',
    },
    { status: 503 },
  );
}

export async function GET(request: Request) {
  if (!handler) return authUnavailable();
  return handler(request);
}

export async function POST(request: Request) {
  if (!handler) return authUnavailable();
  return handler(request);
}
