import { NextResponse } from 'next/server';
import { confirmSubscriber } from '@/lib/newsletter-business/repository.mjs';
import { publicBaseUrl } from '@/lib/newsletter-business/core.mjs';

export const runtime = 'nodejs';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get('token');
  if (!token) {
    return NextResponse.redirect(`${publicBaseUrl()}/newsletter?confirmed=0`);
  }

  try {
    const subscriber = await confirmSubscriber(token);
    return NextResponse.redirect(`${publicBaseUrl()}/newsletter?confirmed=${subscriber ? '1' : '0'}`);
  } catch (error) {
    console.error('[newsletter] confirmation error:', error);
    return NextResponse.redirect(`${publicBaseUrl()}/newsletter?confirmed=0`);
  }
}
