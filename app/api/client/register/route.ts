import { NextRequest, NextResponse } from 'next/server';
import { createClient, getClientByEmail } from '@/lib/client-db';

export async function POST(request: NextRequest) {
  try {
    const { email, business_name } = await request.json();

    // Validate input
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Valid email required' },
        { status: 400 }
      );
    }

    if (!business_name || business_name.trim().length === 0) {
      return NextResponse.json(
        { error: 'Business name required' },
        { status: 400 }
      );
    }

    // Check if client already exists
    const existing = await getClientByEmail(email);
    if (existing) {
      return NextResponse.json(
        {
          error: 'Email already registered',
          client_id: existing.id,
          status: existing.status,
        },
        { status: 409 }
      );
    }

    // Create new client
    const client = await createClient(email, business_name);

    // Generate setup token (valid for 24 hours)
    const setupToken = Buffer.from(
      JSON.stringify({
        clientId: client.id,
        email: client.email,
        issuedAt: Date.now(),
        expiresAt: Date.now() + 24 * 60 * 60 * 1000,
      })
    ).toString('base64');

    console.log(`✅ New client registered: ${client.id} (${email})`);

    return NextResponse.json(
      {
        ok: true,
        client_id: client.id,
        email: client.email,
        business_name: client.business_name,
        status: client.status,
        setup_token: setupToken,
        api_key: client.api_key,
        next_step: `Connect your Stripe account at /client/${client.id}/stripe-oauth`,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Client registration failed:', error);
    return NextResponse.json(
      { error: 'Registration failed' },
      { status: 500 }
    );
  }
}
