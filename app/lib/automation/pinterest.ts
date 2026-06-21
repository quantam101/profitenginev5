/**
 * PINTEREST AUTOMATION
 *
 * Automatically generates and posts Pinterest pins:
 * - Read pin designs from CONTENT_CALENDAR_MONTHLY.md
 * - Generate pin images (1000x1500px) via Canva API, Unsplash, or Replicate
 * - Add text overlays, brand colors, affiliate links
 * - Upload to Pinterest business account via Pinterest API v5
 * - Schedule pin postings and manage boards
 * - Track engagement metrics and clicks via UTM parameters
 *
 * Environment Requirements:
 * - PINTEREST_ACCESS_TOKEN: Pinterest OAuth access token
 * - PINTEREST_BUSINESS_ACCOUNT_ID: Pinterest business account ID
 * - IMAGE_GENERATION_API: 'canva' | 'unsplash' | 'replicate'
 * - CANVA_API_KEY (if using Canva)
 * - REPLICATE_API_TOKEN (if using Replicate)
 * - AFFILIATE_LINKS: JSON map of {keyword: affiliate_url}
 * - PINTEREST_BOARDS: JSON map of {category: board_name}
 */

import { mkdir, writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * ============================================================================
 * TYPE DEFINITIONS
 * ============================================================================
 */

interface PinDesign {
  title: string;
  description: string;
  keywords: string[];
  imagePrompt?: string;
  backgroundColor?: string;
  textColor?: string;
  affiliateLink?: string;
  category?: string;
  boardName?: string;
}

interface GeneratedPin {
  imageUrl: string;
  imageFilePath?: string;
  width: number;
  height: number;
  design: PinDesign;
  generatedAt: string;
}

interface PinterestPinResult {
  success: boolean;
  pinId?: string;
  pinUrl?: string;
  boardId?: string;
  boardName?: string;
  scheduledTime?: string;
  imageUrl?: string;
  error?: string;
  design?: PinDesign;
}

interface PinterestMetrics {
  pinId: string;
  pinUrl: string;
  title: string;
  impressions: number;
  outboundClicks: number;
  saves: number;
  createdAt: string;
  boardName: string;
}

interface TrackingEvent {
  eventId: string;
  pinId: string;
  pinUrl: string;
  eventType: 'impression' | 'click' | 'save' | 'close-up';
  userId?: string;
  timestamp: string;
  utmSource?: string;
  utmMedium?: string;
  utmCampaign?: string;
}

/**
 * Generate pin image via Canva API
 */
async function generateCanvaImage(design: PinDesign): Promise<string> {
  const canvaKey = process.env.CANVA_API_KEY;

  if (!canvaKey) {
    throw new Error('CANVA_API_KEY not configured');
  }

  const createResponse = await fetch('https://api.canva.com/v1/designs', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${canvaKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: design.title,
      design_type: 'pin',
      width: 1000,
      height: 1500,
      background_color: design.backgroundColor || '#FFFFFF',
      elements: [
        {
          type: 'text',
          text: design.title,
          font_size: 48,
          font_weight: 'bold',
          color: design.textColor || '#000000',
          x: 50,
          y: 100,
          width: 900,
          alignment: 'center',
        },
        {
          type: 'text',
          text: design.description,
          font_size: 24,
          color: design.textColor || '#000000',
          x: 50,
          y: 400,
          width: 900,
          alignment: 'center',
        },
        {
          type: 'text',
          text: design.keywords.join(' • '),
          font_size: 16,
          color: design.textColor || '#666666',
          x: 50,
          y: 1350,
          width: 900,
          alignment: 'center',
        },
      ],
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Canva API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string; export_url?: string };

  // Export to PNG
  const exportResponse = await fetch(`https://api.canva.com/v1/designs/${data.id}/exports`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${canvaKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      format: 'png',
      scale: 1,
    }),
  });

  if (!exportResponse.ok) {
    throw new Error(`Canva export error: ${await exportResponse.text()}`);
  }

  const exportData = (await exportResponse.json()) as { url: string };
  return exportData.url;
}

/**
 * Generate pin image via Replicate (DALL-E / Stable Diffusion)
 */
async function generateReplicateImage(design: PinDesign): Promise<string> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const prompt =
    design.imagePrompt ||
    `Pinterest pin design for: ${design.title}. ${design.description}. Professional, eye-catching, 1000x1500px aspect ratio. Keywords: ${design.keywords.join(', ')}`;

  const createResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: '27b786e6e6ffcf07d66f51b33f36567e64d639770374a46dd5ad63bc1320pqrs', // DALL-E 3
      input: {
        prompt,
        image_dimensions: '1000x1500',
        num_outputs: 1,
        quality: 'hd',
      },
    }),
  });

  if (!createResponse.ok) {
    throw new Error(`Image generation failed: ${await createResponse.text()}`);
  }

  const prediction = (await createResponse.json()) as { id: string; output?: string[] };

  // Poll for completion
  let imageData = prediction;
  let attempts = 0;
  const maxAttempts = 60;

  while (!imageData.output && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    const pollResponse = await fetch(
      `https://api.replicate.com/v1/predictions/${imageData.id}`,
      {
        headers: {
          Authorization: `Token ${replicateToken}`,
        },
      }
    );

    if (pollResponse.ok) {
      imageData = (await pollResponse.json()) as { id: string; output?: string[] };
    }

    attempts++;
  }

  if (!imageData.output || imageData.output.length === 0) {
    throw new Error('Image generation did not complete');
  }

  return imageData.output[0];
}

/**
 * Generate pin image via Unsplash (stock photo service)
 */
async function generateUnsplashImage(design: PinDesign): Promise<string> {
  const unsplashKey = process.env.UNSPLASH_ACCESS_KEY;

  if (!unsplashKey) {
    throw new Error('UNSPLASH_ACCESS_KEY not configured');
  }

  const query = design.keywords[0] || design.title;

  const searchResponse = await fetch(
    `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&per_page=1`,
    {
      headers: {
        Authorization: `Client-ID ${unsplashKey}`,
      },
    }
  );

  if (!searchResponse.ok) {
    throw new Error(`Unsplash search failed: ${await searchResponse.text()}`);
  }

  const data = (await searchResponse.json()) as {
    results?: Array<{ urls?: { regular?: string } }>;
  };

  if (!data.results || data.results.length === 0) {
    throw new Error('No images found for design keywords');
  }

  return data.results[0].urls?.regular || '';
}

/**
 * Parse pin design from CONTENT_CALENDAR_MONTHLY.md
 */
async function parsePinDesign(
  contentFile: string = 'CONTENT_CALENDAR_MONTHLY.md',
  pinNumber: number = 1
): Promise<PinDesign> {
  try {
    const content = await readFile(contentFile, 'utf-8');

    // Find specific post section
    const postRegex = new RegExp(
      `### Post ${pinNumber}:[\\s\\S]*?(?=### Post \\d+|$)`,
      'i'
    );
    const postMatch = content.match(postRegex);

    if (!postMatch) {
      throw new Error(`Post ${pinNumber} not found`);
    }

    const postContent = postMatch[0];
    const design: PinDesign = {
      title: '',
      description: '',
      keywords: [],
    };

    // Extract title
    const titleMatch = postContent.match(/### Post \d+: "(.+?)"/);
    if (titleMatch) design.title = titleMatch[1];

    // Extract hook/description
    const hookMatch = postContent.match(/\*\*Hook\*\*[:\n>\s]+([^*]+)/i);
    if (hookMatch) design.description = hookMatch[1].trim();

    // Extract keywords/tags
    const tagsMatch = postContent.match(/\*\*Tags?\*\*[:\n>\s]+([^*]+)/i);
    if (tagsMatch) {
      design.keywords = tagsMatch[1]
        .split(/[,\n#]/)
        .map((t) => t.trim())
        .filter((t) => t)
        .slice(0, 5); // Max 5 keywords for Pinterest
    }

    // Extract affiliate link
    const affiliateMatch = postContent.match(/\*\*Affiliate Links?\*\*[:\n>\s]+`?([^\n`]+)`?/i);
    if (affiliateMatch) design.affiliateLink = affiliateMatch[1].trim();

    // Extract board/category
    const boardMatch = postContent.match(/\*\*Board\*\*[:\n>\s]+([^*\n]+)/i);
    if (boardMatch) design.boardName = boardMatch[1].trim();

    return design;
  } catch (error) {
    throw new Error(`Failed to parse pin design: ${error}`);
  }
}

/**
 * Get or create Pinterest board
 */
async function getOrCreateBoard(boardName: string): Promise<string> {
  const accessToken = process.env.PINTEREST_ACCESS_TOKEN;
  const accountId = process.env.PINTEREST_BUSINESS_ACCOUNT_ID;

  if (!accessToken || !accountId) {
    throw new Error('PINTEREST_ACCESS_TOKEN or PINTEREST_BUSINESS_ACCOUNT_ID not configured');
  }

  // List existing boards
  const listResponse = await fetch(
    `https://api.pinterest.com/v5/boards?access_token=${accessToken}`,
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  if (listResponse.ok) {
    const listData = (await listResponse.json()) as {
      items?: Array<{ id?: string; name?: string }>;
    };
    const existingBoard = listData.items?.find(
      (b) => b.name?.toLowerCase() === boardName.toLowerCase()
    );
    if (existingBoard?.id) {
      return existingBoard.id;
    }
  }

  // Create new board if not found
  const createResponse = await fetch(
    `https://api.pinterest.com/v5/boards?access_token=${accessToken}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: boardName,
        description: `Automated pins for ${boardName}`,
        privacy: 'PUBLIC',
      }),
    }
  );

  if (!createResponse.ok) {
    throw new Error(`Failed to create board: ${await createResponse.text()}`);
  }

  const createData = (await createResponse.json()) as { id?: string };

  if (!createData.id) {
    throw new Error('Board created but no ID returned');
  }

  return createData.id;
}

/**
 * Upload pin to Pinterest
 */
async function uploadPinToPinterest(
  imageUrl: string,
  design: PinDesign
): Promise<PinterestPinResult> {
  try {
    const accessToken = process.env.PINTEREST_ACCESS_TOKEN;
    const accountId = process.env.PINTEREST_BUSINESS_ACCOUNT_ID;

    if (!accessToken || !accountId) {
      return {
        success: false,
        error: 'PINTEREST_ACCESS_TOKEN or PINTEREST_BUSINESS_ACCOUNT_ID not configured',
        design,
      };
    }

    // Get or create board
    const boardName = design.boardName || 'General';
    const boardId = await getOrCreateBoard(boardName);

    // Build pin description with UTM parameters
    const utmParams = new URLSearchParams({
      utm_source: 'pinterest',
      utm_medium: 'pin',
      utm_campaign: 'profitengine',
    });

    const pinDescription = `${design.title}\n\n${design.description}\n\n${
      design.affiliateLink
        ? `${design.affiliateLink}?${utmParams.toString()}`
        : 'https://profitengine.com'
    }`;

    // Create pin
    const createResponse = await fetch(
      `https://api.pinterest.com/v5/pins?access_token=${accessToken}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: design.title,
          description: pinDescription,
          image_url: imageUrl,
          board_id: boardId,
          link: design.affiliateLink || 'https://profitengine.com',
          media_source: {
            source_type: 'image_url',
            url: imageUrl,
          },
        }),
      }
    );

    if (!createResponse.ok) {
      const error = await createResponse.text();
      return {
        success: false,
        error: `Pinterest API error: ${error}`,
        design,
      };
    }

    const pinData = (await createResponse.json()) as { id?: string };

    return {
      success: true,
      pinId: pinData.id,
      pinUrl: `https://pinterest.com/pin/${pinData.id}`,
      boardId,
      boardName,
      imageUrl,
      design,
    };
  } catch (error) {
    return {
      success: false,
      error: `Pin upload failed: ${error}`,
      design,
    };
  }
}

/**
 * Log tracking event for pin engagement
 */
async function logPinTrackingEvent(event: TrackingEvent): Promise<boolean> {
  try {
    const logDir = process.env.AUTOMATION_LOG_DIR || '.runtime/automation';

    if (!existsSync(logDir)) {
      await mkdir(logDir, { recursive: true });
    }

    const logFile = path.join(logDir, 'pinterest-tracking.jsonl');
    await appendFile(logFile, JSON.stringify(event) + '\n');

    return true;
  } catch (error) {
    console.error('Failed to log tracking event:', error);
    return false;
  }
}

/**
 * Fetch Pinterest metrics for a pin
 */
async function getPinMetrics(pinId: string): Promise<PinterestMetrics | null> {
  try {
    const accessToken = process.env.PINTEREST_ACCESS_TOKEN;

    if (!accessToken) {
      throw new Error('PINTEREST_ACCESS_TOKEN not configured');
    }

    const response = await fetch(
      `https://api.pinterest.com/v5/pins/${pinId}?access_token=${accessToken}&fields=id,url,title,created_at,note`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      return null;
    }

    const pinData = (await response.json()) as {
      id?: string;
      url?: string;
      title?: string;
      created_at?: string;
    };

    // Fetch analytics (requires different endpoint)
    const analyticsResponse = await fetch(
      `https://api.pinterest.com/v5/pins/${pinId}/analytics?access_token=${accessToken}&start_date=2024-01-01&end_date=2099-12-31&metric_types=IMPRESSION,OUTBOUND_CLICK,SAVE&pin_metrics=true`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    let metrics = {
      impressions: 0,
      outboundClicks: 0,
      saves: 0,
    };

    if (analyticsResponse.ok) {
      const analyticsData = (await analyticsResponse.json()) as {
        data?: Array<{ metric_type?: string; data?: Array<{ value?: number }> }>;
      };

      analyticsData.data?.forEach((item) => {
        if (item.metric_type === 'IMPRESSION') {
          metrics.impressions = item.data?.[0]?.value || 0;
        } else if (item.metric_type === 'OUTBOUND_CLICK') {
          metrics.outboundClicks = item.data?.[0]?.value || 0;
        } else if (item.metric_type === 'SAVE') {
          metrics.saves = item.data?.[0]?.value || 0;
        }
      });
    }

    return {
      pinId: pinData.id || pinId,
      pinUrl: pinData.url || '',
      title: pinData.title || '',
      createdAt: pinData.created_at || new Date().toISOString(),
      boardName: 'General',
      ...metrics,
    };
  } catch (error) {
    console.error('Failed to fetch pin metrics:', error);
    return null;
  }
}

/**
 * Main orchestration function: Generate and post Pinterest pin
 */
export async function generateAndPostPin(pinNumber: number = 1): Promise<PinterestPinResult> {
  try {
    // Parse pin design from content calendar
    console.log(`Parsing pin design: Pin ${pinNumber}`);
    const design = await parsePinDesign('CONTENT_CALENDAR_MONTHLY.md', pinNumber);

    // Generate image
    console.log(`Generating pin image for: ${design.title}`);
    const imageProvider = process.env.IMAGE_GENERATION_API || 'replicate';
    let imageUrl: string;

    if (imageProvider === 'canva') {
      imageUrl = await generateCanvaImage(design);
    } else if (imageProvider === 'unsplash') {
      imageUrl = await generateUnsplashImage(design);
    } else {
      imageUrl = await generateReplicateImage(design);
    }

    console.log(`Generated image: ${imageUrl}`);

    // Upload to Pinterest
    console.log(`Uploading pin to Pinterest...`);
    const result = await uploadPinToPinterest(imageUrl, design);

    if (result.success) {
      console.log(`✓ Pin posted: ${result.pinUrl}`);
    } else {
      console.error(`✗ Pin upload failed: ${result.error}`);
    }

    return result;
  } catch (error) {
    return {
      success: false,
      error: `Pin orchestration failed: ${error}`,
    };
  }
}

/**
 * Batch generate and post multiple pins
 */
export async function generateAndPostPins(count: number = 5): Promise<PinterestPinResult[]> {
  const results: PinterestPinResult[] = [];

  for (let i = 1; i <= count; i++) {
    try {
      const result = await generateAndPostPin(i);
      results.push(result);

      // Rate limiting - wait between requests
      if (i < count) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    } catch (error) {
      results.push({
        success: false,
        error: `Failed to generate pin ${i}: ${error}`,
      });
    }
  }

  return results;
}

// Import appendFile from fs/promises (missing from earlier imports)
import { appendFile } from 'fs/promises';

export {
  PinDesign,
  GeneratedPin,
  PinterestPinResult,
  PinterestMetrics,
  TrackingEvent,
};
