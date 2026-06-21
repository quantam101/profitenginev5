/**
 * API ENDPOINT: /api/automation/affiliate
 *
 * Comprehensive affiliate automation API
 *
 * Supported Actions:
 * - create-link: Create single affiliate link
 * - batch-create: Create multiple links
 * - track-click: Track affiliate click event
 * - track-conversion: Track conversion with value
 * - get-links: Retrieve links (filtered by niche/network)
 * - get-metrics: Dashboard metrics for period
 * - get-niche-metrics: Metrics for specific niche
 * - get-commissions: Commission report
 * - optimize-link: Optimize single link
 * - optimize-niche: Optimize all links in niche
 * - export-csv: Export links as CSV
 * - import-csv: Import links from CSV
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  NETWORKS,
  createAmazonLink,
  createClickBankLink,
  createCJLink,
  createShareASaleLink,
  createMultiNetworkLinks,
  trackAffiliateClick,
  trackConversion,
  saveLink,
  getLinkById,
  getAllLinks,
  getConversionEvents,
  getCommissionRecords,
  getDashboardMetrics,
  getNicheMetrics,
  generateCommissionReport,
  optimizeLink,
  optimizeNicheLinks,
  batchCreateLinks,
  importLinksFromCSV,
  exportLinksAsCSV,
  AffiliateProduct,
  AffiliateLink,
} from '@/app/lib/automation/affiliate-enhanced';

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface CreateLinkRequest {
  action: 'create-link';
  product: AffiliateProduct;
  networks?: ('amazon' | 'clickbank' | 'cj' | 'shareasale')[];
}

interface BatchCreateRequest {
  action: 'batch-create';
  products: AffiliateProduct[];
}

interface TrackClickRequest {
  action: 'track-click';
  linkId: string;
  referer?: string;
  userId?: string;
}

interface TrackConversionRequest {
  action: 'track-conversion';
  linkId: string;
  value: number;
  orderId?: string;
  metadata?: Record<string, any>;
}

interface GetLinksRequest {
  action: 'get-links';
  niche?: string;
  network?: string;
  status?: string;
}

interface GetMetricsRequest {
  action: 'get-metrics';
  startDate: string;
  endDate: string;
}

interface GetNicheMetricsRequest {
  action: 'get-niche-metrics';
  niche: string;
}

interface GetCommissionsRequest {
  action: 'get-commissions';
  startDate: string;
  endDate: string;
  status?: string;
}

interface OptimizeLinkRequest {
  action: 'optimize-link';
  linkId: string;
}

interface OptimizeNicheRequest {
  action: 'optimize-niche';
  niche: string;
}

interface ExportCSVRequest {
  action: 'export-csv';
  niche?: string;
}

interface ImportCSVRequest {
  action: 'import-csv';
  csv: string;
}

type RequestBody =
  | CreateLinkRequest
  | BatchCreateRequest
  | TrackClickRequest
  | TrackConversionRequest
  | GetLinksRequest
  | GetMetricsRequest
  | GetNicheMetricsRequest
  | GetCommissionsRequest
  | OptimizeLinkRequest
  | OptimizeNicheRequest
  | ExportCSVRequest
  | ImportCSVRequest;

// ═══════════════════════════════════════════════════════════════════════════════
// API HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

export async function POST(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    const body = (await request.json()) as RequestBody;
    const action = body.action;

    // ───────────────────────────────────────────────────────────────────────
    // CREATE SINGLE LINK
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'create-link') {
      const req = body as CreateLinkRequest;
      const networkFilter = req.networks || ['amazon', 'clickbank', 'cj', 'shareasale'];

      let links: AffiliateLink[] = [];

      if (networkFilter.includes('amazon')) {
        try {
          links.push(createAmazonLink(req.product));
        } catch (err) {
          console.error('Amazon link creation failed:', err);
        }
      }

      if (networkFilter.includes('clickbank')) {
        try {
          links.push(createClickBankLink(req.product));
        } catch (err) {
          console.error('ClickBank link creation failed:', err);
        }
      }

      if (networkFilter.includes('cj')) {
        try {
          links.push(createCJLink(req.product));
        } catch (err) {
          console.error('CJ link creation failed:', err);
        }
      }

      if (networkFilter.includes('shareasale')) {
        try {
          links.push(createShareASaleLink(req.product));
        } catch (err) {
          console.error('ShareASale link creation failed:', err);
        }
      }

      // Save links
      for (const link of links) {
        await saveLink(link);
      }

      return NextResponse.json({
        success: true,
        action: 'create-link',
        productId: req.product.id,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // BATCH CREATE LINKS
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'batch-create') {
      const req = body as BatchCreateRequest;
      const links = await batchCreateLinks(req.products);

      return NextResponse.json({
        success: true,
        action: 'batch-create',
        productCount: req.products.length,
        linkCount: links.length,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // TRACK CLICK
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'track-click') {
      const req = body as TrackClickRequest;
      const event = await trackAffiliateClick(req.linkId, req.referer, req.userId);

      return NextResponse.json({
        success: true,
        action: 'track-click',
        event,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // TRACK CONVERSION
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'track-conversion') {
      const req = body as TrackConversionRequest;
      const event = await trackConversion(
        req.linkId,
        req.value,
        req.orderId,
        req.metadata
      );

      return NextResponse.json({
        success: true,
        action: 'track-conversion',
        event,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // GET LINKS
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'get-links') {
      const req = body as GetLinksRequest;
      let links = await getAllLinks();

      if (req.niche) {
        links = links.filter((l) => l.niche === req.niche);
      }

      if (req.network) {
        links = links.filter((l) => l.network === req.network);
      }

      if (req.status) {
        links = links.filter((l) => l.status === req.status);
      }

      return NextResponse.json({
        success: true,
        action: 'get-links',
        count: links.length,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // GET METRICS
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'get-metrics') {
      const req = body as GetMetricsRequest;
      const startDate = new Date(req.startDate);
      const endDate = new Date(req.endDate);

      const metrics = await getDashboardMetrics(startDate, endDate);

      return NextResponse.json({
        success: true,
        action: 'get-metrics',
        metrics,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // GET NICHE METRICS
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'get-niche-metrics') {
      const req = body as GetNicheMetricsRequest;
      const metrics = await getNicheMetrics(req.niche);

      return NextResponse.json({
        success: true,
        action: 'get-niche-metrics',
        metrics,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // GET COMMISSIONS
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'get-commissions') {
      const req = body as GetCommissionsRequest;
      const startDate = new Date(req.startDate);
      const endDate = new Date(req.endDate);

      const report = await generateCommissionReport(startDate, endDate);

      return NextResponse.json({
        success: true,
        action: 'get-commissions',
        report,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // OPTIMIZE SINGLE LINK
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'optimize-link') {
      const req = body as OptimizeLinkRequest;
      const result = await optimizeLink(req.linkId);

      return NextResponse.json({
        success: true,
        action: 'optimize-link',
        result,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // OPTIMIZE NICHE
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'optimize-niche') {
      const req = body as OptimizeNicheRequest;
      const results = await optimizeNicheLinks(req.niche);

      return NextResponse.json({
        success: true,
        action: 'optimize-niche',
        niche: req.niche,
        optimizationCount: results.length,
        results,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // EXPORT CSV
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'export-csv') {
      const req = body as ExportCSVRequest;
      const csv = await exportLinksAsCSV(req.niche);

      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="affiliate-links-${req.niche || 'all'}-${Date.now()}.csv"`,
        },
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // IMPORT CSV
    // ───────────────────────────────────────────────────────────────────────
    if (action === 'import-csv') {
      const req = body as ImportCSVRequest;
      const links = await importLinksFromCSV(req.csv);

      return NextResponse.json({
        success: true,
        action: 'import-csv',
        importedCount: links.length,
        links,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      });
    }

    // ───────────────────────────────────────────────────────────────────────
    // UNKNOWN ACTION
    // ───────────────────────────────────────────────────────────────────────
    return NextResponse.json(
      {
        success: false,
        error: `Unknown action: ${action}`,
        supportedActions: [
          'create-link',
          'batch-create',
          'track-click',
          'track-conversion',
          'get-links',
          'get-metrics',
          'get-niche-metrics',
          'get-commissions',
          'optimize-link',
          'optimize-niche',
          'export-csv',
          'import-csv',
        ],
      },
      { status: 400 }
    );
  } catch (error) {
    console.error('Affiliate API error:', error);

    return NextResponse.json(
      {
        success: false,
        error: (error as Error).message,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      },
      { status: 500 }
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// OPTIONS (CORS)
// ═══════════════════════════════════════════════════════════════════════════════

export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json({}, { status: 200 });
}

// ═══════════════════════════════════════════════════════════════════════════════
// GET (QUICK STATUS)
// ═══════════════════════════════════════════════════════════════════════════════

export async function GET(request: NextRequest): Promise<NextResponse> {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action');

  try {
    // Get network status
    if (action === 'networks') {
      const status = Object.entries(NETWORKS).map(([id, net]) => ({
        id,
        name: net.name,
        enabled: net.enabled,
        tier: net.tier,
      }));

      return NextResponse.json({
        success: true,
        networks: status,
      });
    }

    // Get quick stats
    if (action === 'stats') {
      const links = await getAllLinks();
      const events = await getConversionEvents();
      const commissions = await getCommissionRecords();

      const activeLinks = links.filter((l) => l.status === 'active').length;
      const clicks = events.filter((e) => e.eventType === 'click').length;
      const conversions = events.filter((e) => e.eventType === 'conversion').length;
      const totalCommission = commissions.reduce((sum, c) => sum + c.amount, 0);

      return NextResponse.json({
        success: true,
        stats: {
          totalLinks: links.length,
          activeLinks,
          clicks,
          conversions,
          conversionRate: clicks > 0 ? conversions / clicks : 0,
          totalCommission,
        },
      });
    }

    // Default: show available actions
    return NextResponse.json({
      success: true,
      message: 'Affiliate API is operational',
      availableQueries: ['networks', 'stats'],
      postActions: [
        'create-link',
        'batch-create',
        'track-click',
        'track-conversion',
        'get-links',
        'get-metrics',
        'get-niche-metrics',
        'get-commissions',
        'optimize-link',
        'optimize-niche',
        'export-csv',
        'import-csv',
      ],
    });
  } catch (error) {
    console.error('Affiliate API GET error:', error);

    return NextResponse.json(
      {
        success: false,
        error: (error as Error).message,
      },
      { status: 500 }
    );
  }
}
