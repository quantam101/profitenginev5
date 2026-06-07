import { NextResponse } from 'next/server';
import { getKdpRevenueDashboard, rankKdpOffers } from '../../../lib/kdp-revenue';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const offerId = searchParams.get('offer');
  const dashboard = getKdpRevenueDashboard();

  if (offerId) {
    const offer = rankKdpOffers().find((candidate) => candidate.id === offerId);

    if (!offer) {
      return NextResponse.json(
        {
          ok: false,
          error: 'KDP offer not found',
          availableOfferIds: dashboard.rankedOffers.map((candidate) => candidate.id),
        },
        { status: 404, headers: { 'Cache-Control': 'no-store' } },
      );
    }

    return NextResponse.json(
      {
        ok: true,
        offer,
        approvalRequired: true,
        automaticKdpSubmission: false,
        operatorRule: 'Prepare assets and economics only. Do not publish, certify, or submit anything to KDP without Stephen approval.',
      },
      { headers: { 'Cache-Control': 'no-store' } },
    );
  }

  return NextResponse.json(dashboard, { headers: { 'Cache-Control': 'no-store' } });
}
