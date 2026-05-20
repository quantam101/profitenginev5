import { NextResponse } from 'next/server';

export function GET() {
  return NextResponse.json({
    ok: true,
    service: 'profitengine-command-center',
    version: '0.1.0',
    mode: 'strict_zero_spend',
    paidAdaptersEnabled: false,
    externalExecutionEnabled: false,
    staleSourceEnabled: false,
    timestamp: new Date().toISOString()
  });
}
