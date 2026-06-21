/**
 * API ENDPOINT: /api/automation/kdp
 *
 * Comprehensive eBook publishing automation via Amazon KDP, Draft2Digital, and Smashwords
 *
 * POST Operations:
 * 1. publish — Publish one or more eBooks
 * 2. validate — Validate book metadata without publishing
 * 3. track-royalties — Fetch royalty earnings by ASIN
 * 4. batch-publish — Publish multiple books with quality checks
 *
 * GET Operations:
 * 1. status — Get overall KDP automation status
 * 2. royalties — Get royalties for a specific ASIN (query param: asin=B0...)
 *
 * Environment:
 * - KDP_ACCESS_TOKEN: Amazon KDP API token
 * - DRAFT2DIGITAL_API_KEY: Draft2Digital API key
 * - SMASHWORDS_API_KEY: Smashwords API key
 * - AUTOMATION_API_TOKEN: Optional auth token
 */

import { NextRequest, NextResponse } from 'next/server';

// Dynamic import for server-side only
let orchestrateKdpPublication: () => Promise<unknown>;
let parseBookMetadata: (filePath: string) => Promise<unknown>;
let generateBookCover: (metadata: unknown) => Promise<string>;
let uploadToKdp: (metadata: unknown, coverUrl: string) => Promise<unknown>;
let uploadToDraft2Digital: (metadata: unknown, coverUrl: string) => Promise<unknown>;
let uploadToSmashwords: (metadata: unknown, coverUrl: string) => Promise<unknown>;
let trackKdpRoyalties: (asin: string) => Promise<unknown>;
let validateBookMetadata: (metadata: unknown) => { valid: boolean; errors: string[] };
let assessPublicationRisk: (metadata: unknown) => { riskLevel: string; score: number; warnings: string[] };
let getRecommendedPlatforms: (metadata: unknown) => string[];
let batchPublishBooks: (files: string[], options: unknown) => Promise<unknown>;

/**
 * Initialize KDP automation modules (lazy load)
 */
async function initializeKdpAutomation() {
  if (!orchestrateKdpPublication) {
    try {
      const kdpModule = await import('@/app/lib/automation/kdp');
      orchestrateKdpPublication = kdpModule.orchestrateKdpPublication;
      parseBookMetadata = kdpModule.parseBookMetadata;
      generateBookCover = kdpModule.generateBookCover;
      uploadToKdp = kdpModule.uploadToKdp;
      uploadToDraft2Digital = kdpModule.uploadToDraft2Digital;
      uploadToSmashwords = kdpModule.uploadToSmashwords;
      trackKdpRoyalties = kdpModule.trackKdpRoyalties;
      validateBookMetadata = kdpModule.validateBookMetadata;
      assessPublicationRisk = kdpModule.assessPublicationRisk;
      getRecommendedPlatforms = kdpModule.getRecommendedPlatforms;
      batchPublishBooks = kdpModule.batchPublishBooks;
    } catch (error) {
      console.error('Failed to load KDP automation modules:', error);
      throw new Error('KDP automation modules not available');
    }
  }
}

interface KdpRequest {
  operation: 'publish' | 'validate' | 'track-royalties' | 'batch-publish';
  bookFiles?: string[];
  asin?: string;
  platforms?: ('kdp' | 'draft2digital' | 'smashwords')[];
  validateOnly?: boolean;
}

interface KdpResponse {
  success: boolean;
  runId?: string;
  operation?: string;
  booksProcessed?: number;
  platformsPerBook?: number;
  estimatedDuration?: string;
  status?: string;
  asin?: string;
  earnings?: unknown;
  lastRun?: unknown;
  validationResults?: unknown;
  error?: string;
  timestamp?: string;
  duration?: number;
}

/**
 * POST /api/automation/kdp — Publish to all platforms, validate, or track royalties
 */
export async function POST(request: NextRequest): Promise<NextResponse<KdpResponse>> {
  const startTime = Date.now();

  try {
    // Verify request authentication
    const authToken = request.headers.get('Authorization');
    const expectedToken = process.env.AUTOMATION_API_TOKEN;

    if (expectedToken && authToken !== `Bearer ${expectedToken}`) {
      return NextResponse.json(
        {
          success: false,
          error: 'Unauthorized',
          timestamp: new Date().toISOString(),
          duration: Date.now() - startTime,
        },
        { status: 401 }
      );
    }

    // Parse request body
    const body = (await request.json()) as KdpRequest;
    const {
      operation = 'publish',
      bookFiles = [],
      asin,
      platforms = ['kdp', 'draft2digital', 'smashwords'],
      validateOnly = false,
    } = body;

    // Initialize KDP modules
    await initializeKdpAutomation();

    // Validate operation
    if (!['publish', 'validate', 'track-royalties', 'batch-publish'].includes(operation)) {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid operation. Must be: publish, validate, track-royalties, or batch-publish',
          timestamp: new Date().toISOString(),
          duration: Date.now() - startTime,
        },
        { status: 400 }
      );
    }

    // Handle validate operation
    if (operation === 'validate') {
      if (bookFiles.length === 0) {
        return NextResponse.json(
          {
            success: false,
            error: 'bookFiles array required for validation',
            timestamp: new Date().toISOString(),
            duration: Date.now() - startTime,
          },
          { status: 400 }
        );
      }

      try {
        const validationResults = await batchPublishBooks(bookFiles, {
          validateOnly: true,
          platforms,
        });

        return NextResponse.json({
          success: validationResults.validationErrors.length === 0,
          operation: 'validate',
          validationResults,
          timestamp: new Date().toISOString(),
          duration: Date.now() - startTime,
        });
      } catch (error) {
        return NextResponse.json(
          {
            success: false,
            error: error instanceof Error ? error.message : 'Validation failed',
            timestamp: new Date().toISOString(),
            duration: Date.now() - startTime,
          },
          { status: 500 }
        );
      }
    }

    // Handle track-royalties operation
    if (operation === 'track-royalties') {
      if (!asin) {
        return NextResponse.json(
          {
            success: false,
            error: 'ASIN required for royalty tracking',
            timestamp: new Date().toISOString(),
            duration: Date.now() - startTime,
          },
          { status: 400 }
        );
      }

      try {
        const earnings = await trackKdpRoyalties(asin);
        return NextResponse.json({
          success: true,
          operation: 'track-royalties',
          asin,
          earnings,
          timestamp: new Date().toISOString(),
          duration: Date.now() - startTime,
        });
      } catch (error) {
        return NextResponse.json(
          {
            success: false,
            error: error instanceof Error ? error.message : 'Failed to track royalties',
            timestamp: new Date().toISOString(),
            duration: Date.now() - startTime,
          },
          { status: 500 }
        );
      }
    }

    // Handle batch-publish or publish operation
    const runId = `kdp-publication-${Date.now()}`;
    const booksCount = bookFiles.length;

    // Start publication in background (don't await)
    if (typeof global !== 'undefined') {
      setImmediate(async () => {
        try {
          if (operation === 'batch-publish') {
            const result = await batchPublishBooks(bookFiles, { platforms });
            console.log(`KDP batch publication completed for run ${runId}:`, result);
          } else {
            const result = await orchestrateKdpPublication();
            console.log(`KDP publication completed for run ${runId}:`, result);
          }
        } catch (error) {
          console.error(`Background KDP publication failed: ${error}`);
        }
      });
    }

    return NextResponse.json({
      success: true,
      runId,
      operation: operation === 'batch-publish' ? 'batch-publish' : 'publish',
      booksProcessed: booksCount,
      platformsPerBook: platforms.length,
      estimatedDuration: booksCount > 0 ? `${booksCount * 100}s` : '300s',
      status: 'initiated',
      timestamp: new Date().toISOString(),
      duration: Date.now() - startTime,
    });
  } catch (error) {
    console.error('KDP request failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to start KDP automation',
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
      },
      { status: 500 }
    );
  }
}

/**
 * GET /api/automation/kdp — Get status of KDP publications
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    // Get optional query parameters
    const { searchParams } = new URL(request.url);
    const asin = searchParams.get('asin');

    await initializeKdpAutomation();

    // Track royalties if ASIN provided
    if (asin) {
      const earnings = await trackKdpRoyalties(asin);
      return NextResponse.json({
        success: true,
        asin,
        earnings,
      });
    }

    // Return general status
    return NextResponse.json({
      success: true,
      status: 'ready',
      operations: ['publish', 'track-royalties'],
      platforms: ['kdp', 'draft2digital', 'smashwords'],
    });
  } catch (error) {
    console.error('KDP status request failed:', error);

    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get KDP status',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/automation/kdp — CORS preflight
 */
export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
