/**
 * Email Subscription API — Beehiiv Integration
 *
 * Subscribes users to the Beehiiv newsletter
 * Triggers welcome sequence + product recommendations
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const { email } = await req.json();

    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: 'Invalid email' },
        { status: 400 }
      );
    }

    const apiKey = process.env.BEEHIIV_API_KEY;
    const pubId = process.env.BEEHIIV_PUBLICATION_ID;

    if (!apiKey || !pubId) {
      console.error('Beehiiv credentials not configured');
      return NextResponse.json(
        { error: 'Email service not configured' },
        { status: 503 }
      );
    }

    // Subscribe to Beehiiv
    const beehiivResponse = await fetch(
      'https://api.beehiiv.com/v1/publications/subscriptions',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          reactivate_existing: true,
          send_welcome_email: true,
          utm_source: 'blog-signup',
          utm_medium: 'organic',
          custom_fields: {
            source: 'blog-homepage',
            timestamp: new Date().toISOString(),
          },
        }),
      }
    );

    if (!beehiivResponse.ok) {
      const error = await beehiivResponse.text();
      console.error('Beehiiv error:', error);
      return NextResponse.json(
        { error: 'Subscription failed' },
        { status: beehiivResponse.status }
      );
    }

    const data = await beehiivResponse.json();

    // Log successful subscription
    console.log(`[Email] Subscribed: ${email}`);

    return NextResponse.json({
      ok: true,
      message: 'Subscription successful',
      subscriberId: (data as any).id,
    });
  } catch (error) {
    console.error('Email subscription error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
