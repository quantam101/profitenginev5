import { NextResponse } from 'next/server';

function authUnavailable() {
  return NextResponse.json(
    {
      ok: false,
      status: 'auth_unavailable',
      message: 'Authentication is temporarily disabled while backend and auth configuration are repaired.',
    },
    { status: 503 },
  );
}

export async function GET() {
  return authUnavailable();
}

export async function POST() {
  return authUnavailable();
}
