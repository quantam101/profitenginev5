/**
 * INSTAGRAM REELS AUTOMATION (UNIFIED MODULE)
 *
 * Comprehensive Instagram Reels automation that handles:
 * - Reel script extraction from content calendar
 * - Video generation via Synthesia, D-ID, Replicate, or ElevenLabs
 * - Voiceover synthesis and text overlay generation
 * - Background music integration
 * - Instagram Meta Graph API publishing
 * - Scheduling and engagement tracking
 * - Batch processing and error recovery
 *
 * Environment Requirements:
 * - IG_USER_ID: Instagram business account ID
 * - FB_PAGE_ACCESS_TOKEN: Meta Graph API access token
 * - VIDEO_GENERATION_API: 'synthesia' | 'd-id' | 'replicate' | 'elevenlabs'
 * - SYNTHESIA_API_KEY (if using Synthesia)
 * - DID_API_KEY (if using D-ID)
 * - REPLICATE_API_TOKEN (if using Replicate)
 * - ELEVENLABS_API_KEY (if using ElevenLabs)
 * - RUNTIME_API_URL: Base URL for webhook callbacks
 * - RUNTIME_DATA_DIR: Directory for storing reel metadata
 */

import { mkdir, writeFile, readFile } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface ReelScript {
  title: string;
  hook: string;
  mainPoints: string[];
  cta: string;
  affiliateLinks?: Record<string, string>;
  duration: number; // seconds
  voicePrompt?: string;
  backgroundMusic?: string;
  textOverlays?: string[];
  hashtags?: string[];
  contentTopic?: string;
  targetAudience?: string;
}

export interface GeneratedReel {
  videoUrl: string;
  thumbnail?: string;
  duration: number;
  script: ReelScript;
  generatedAt: string;
  videoId?: string;
}

export interface InstagramReelMetadata {
  reelId: string;
  postId?: string;
  postUrl?: string;
  status: 'pending' | 'generating' | 'uploaded' | 'published' | 'failed';
  script: ReelScript;
  videoUrl?: string;
  scheduledTime?: string;
  publishedTime?: string;
  error?: string;
  metrics?: {
    views?: number;
    likes?: number;
    comments?: number;
    shares?: number;
    saves?: number;
    lastFetchedAt?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface InstagramReelResult {
  success: boolean;
  reelId?: string;
  postId?: string;
  postUrl?: string;
  scheduledTime?: string;
  publishedTime?: string;
  videoUrl?: string;
  error?: string;
  script?: ReelScript;
  retries?: number;
  duration?: number;
}

export interface BatchReelResult {
  requestId: string;
  timestamp: string;
  totalReels: number;
  successCount: number;
  failureCount: number;
  results: InstagramReelResult[];
  totalDuration: number;
}

// ============================================================================
// VIDEO GENERATION ADAPTERS
// ============================================================================

/**
 * Generate video via Synthesia.io API
 */
async function generateSynthesiaVideo(script: ReelScript): Promise<GeneratedReel> {
  const synthesiaKey = process.env.SYNTHESIA_API_KEY;

  if (!synthesiaKey) {
    throw new Error('SYNTHESIA_API_KEY not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const createResponse = await fetch('https://api.synthesia.io/v1/videos', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${synthesiaKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: script.title,
      description: `Instagram Reel: ${script.title}`,
      visibility: 'private',
      test: false,
      avatarSettings: {
        avatarName: 'Amy',
        avatarStyle: 'expressive',
      },
      clips: [
        {
          avatarSettings: {
            avatarName: 'Amy',
            avatarStyle: 'expressive',
          },
          scriptText: voiceScript,
          backgroundSettings: {
            color: '#1a1a1a',
          },
        },
      ],
      callbackUrl: `${process.env.RUNTIME_API_URL}/api/webhooks/instagram-reel-ready`,
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Synthesia API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string };
  const videoUrl = `https://synthesia.io/videos/${data.id}`;

  return {
    videoUrl,
    duration: script.duration,
    script,
    generatedAt: new Date().toISOString(),
    videoId: data.id,
  };
}

/**
 * Generate video via D-ID API
 */
async function generateDIDVideo(script: ReelScript): Promise<GeneratedReel> {
  const didKey = process.env.DID_API_KEY;

  if (!didKey) {
    throw new Error('DID_API_KEY not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const createResponse = await fetch('https://api.d-id.com/talks', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${didKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      source_url:
        'https://d-id-public-bucket.s3.amazonaws.com/default_resources/presenters/amy.png',
      script: {
        type: 'text',
        input: voiceScript,
        provider: {
          type: 'elevenlabs',
          voice_id: 'EXAVITQu4vr4xnSDxMaL',
        },
      },
      webhook_url: `${process.env.RUNTIME_API_URL}/api/webhooks/instagram-reel-ready`,
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`D-ID API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string };

  return {
    videoUrl: `https://d-id.com/videos/${data.id}`,
    duration: script.duration,
    script,
    generatedAt: new Date().toISOString(),
    videoId: data.id,
  };
}

/**
 * Generate video via Replicate API
 */
async function generateReplicateVideo(script: ReelScript): Promise<GeneratedReel> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const createResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version:
        'e223c2d91b78198c3aa39e78ceb7a4cb625e1224176e1f18fc65a3917dd96b01',
      input: {
        prompt: voiceScript,
        negative_prompt: 'blurry, low quality',
        num_frames: Math.min(script.duration * 24, 200),
      },
      webhook: `${process.env.RUNTIME_API_URL}/api/webhooks/instagram-reel-ready`,
      webhook_events_filter: ['completed'],
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Replicate API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string; output?: string[] };

  return {
    videoUrl: (data.output && data.output[0]) || `https://replicate.com/predictions/${data.id}`,
    duration: script.duration,
    script,
    generatedAt: new Date().toISOString(),
    videoId: data.id,
  };
}

/**
 * Generate video via ElevenLabs (voiceover only, requires video template)
 */
async function generateElevenLabsVoiceover(script: ReelScript): Promise<GeneratedReel> {
  const elevenLabsKey = process.env.ELEVENLABS_API_KEY;

  if (!elevenLabsKey) {
    throw new Error('ELEVENLABS_API_KEY not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const ttsResponse = await fetch(
    'https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL',
    {
      method: 'POST',
      headers: {
        'xi-api-key': elevenLabsKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: voiceScript,
        model_id: 'eleven_monolingual_v1',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
      }),
    }
  );

  if (!ttsResponse.ok) {
    const error = await ttsResponse.text();
    throw new Error(`ElevenLabs TTS error: ${error}`);
  }

  const audioBuffer = await ttsResponse.arrayBuffer();
  const audioUrl = `data:audio/mpeg;base64,${Buffer.from(audioBuffer).toString('base64')}`;

  return {
    videoUrl: audioUrl,
    duration: script.duration,
    script,
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Unified video generation router
 */
async function generateVideo(script: ReelScript): Promise<GeneratedReel> {
  const generationApi = process.env.VIDEO_GENERATION_API || 'synthesia';

  switch (generationApi) {
    case 'synthesia':
      return generateSynthesiaVideo(script);
    case 'd-id':
      return generateDIDVideo(script);
    case 'replicate':
      return generateReplicateVideo(script);
    case 'elevenlabs':
      return generateElevenLabsVoiceover(script);
    default:
      throw new Error(`Unknown video generation API: ${generationApi}`);
  }
}

// ============================================================================
// INSTAGRAM PUBLISHING
// ============================================================================

/**
 * Publish generated reel to Instagram via Meta Graph API
 */
async function publishToInstagram(
  generatedReel: GeneratedReel,
  options: {
    scheduleTime?: string;
    caption?: string;
    retries?: number;
  } = {}
): Promise<InstagramReelResult> {
  const igUserId = process.env.IG_USER_ID;
  const accessToken = process.env.FB_PAGE_ACCESS_TOKEN;

  if (!igUserId || !accessToken) {
    return {
      success: false,
      error: 'IG_USER_ID or FB_PAGE_ACCESS_TOKEN not configured',
    };
  }

  const { scheduleTime, caption, retries = 3 } = options;
  let lastError: string | undefined;
  let attempt = 0;

  while (attempt < retries) {
    attempt++;
    try {
      // Create media container
      const containerResponse = await fetch(
        `https://graph.instagram.com/v18.0/${igUserId}/media`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            media_type: 'REELS',
            video_url: generatedReel.videoUrl,
            caption:
              caption ||
              `${generatedReel.script.hook}\n\n${generatedReel.script.mainPoints.join('\n')}\n\n${generatedReel.script.cta}`,
            access_token: accessToken,
          }),
        }
      );

      if (!containerResponse.ok) {
        throw new Error(
          `Failed to create media container: ${containerResponse.statusText}`
        );
      }

      const containerData = (await containerResponse.json()) as { id: string };
      const mediaId = containerData.id;

      // Publish the media
      let publishUrl = `https://graph.instagram.com/v18.0/${igUserId}/media_publish`;
      if (scheduleTime) {
        publishUrl += `?scheduled_publish_time=${Math.floor(new Date(scheduleTime).getTime() / 1000)}`;
      }

      const publishResponse = await fetch(publishUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          creation_id: mediaId,
          access_token: accessToken,
        }),
      });

      if (!publishResponse.ok) {
        throw new Error(
          `Failed to publish media: ${publishResponse.statusText}`
        );
      }

      const publishData = (await publishResponse.json()) as { id: string };

      return {
        success: true,
        reelId: generatedReel.videoId,
        postId: publishData.id,
        postUrl: `https://instagram.com/reels/${publishData.id}`,
        scheduledTime: scheduleTime,
        publishedTime: scheduleTime ? undefined : new Date().toISOString(),
        videoUrl: generatedReel.videoUrl,
        script: generatedReel.script,
        retries: attempt - 1,
      };
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);

      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
      }
    }
  }

  return {
    success: false,
    error: lastError,
    retries: attempt - 1,
  };
}

// ============================================================================
// METADATA PERSISTENCE
// ============================================================================

/**
 * Save reel metadata to persistent storage
 */
export async function saveReelMetadata(metadata: InstagramReelMetadata): Promise<void> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/instagram';

  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  const metadataPath = path.join(runtimeDir, `${metadata.reelId}.json`);
  await writeFile(metadataPath, JSON.stringify(metadata, null, 2));
}

/**
 * Load reel metadata from storage
 */
export async function loadReelMetadata(reelId: string): Promise<InstagramReelMetadata | null> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/instagram';
  const metadataPath = path.join(runtimeDir, `${reelId}.json`);

  if (!existsSync(metadataPath)) {
    return null;
  }

  const content = await readFile(metadataPath, 'utf-8');
  return JSON.parse(content) as InstagramReelMetadata;
}

/**
 * List all reels metadata
 */
export async function listReelsMetadata(): Promise<InstagramReelMetadata[]> {
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/instagram';

  if (!existsSync(runtimeDir)) {
    return [];
  }

  const files = await readFile(runtimeDir, 'utf-8').catch(() => '[]');
  const filenames = JSON.parse(files) as string[];

  const metadataList: InstagramReelMetadata[] = [];
  for (const filename of filenames) {
    const metadata = await loadReelMetadata(filename.replace('.json', ''));
    if (metadata) {
      metadataList.push(metadata);
    }
  }

  return metadataList;
}

// ============================================================================
// ENGAGEMENT METRICS
// ============================================================================

/**
 * Fetch engagement metrics for a published reel
 */
export async function getReelMetrics(
  postId: string
): Promise<{
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
} | null> {
  const accessToken = process.env.FB_PAGE_ACCESS_TOKEN;

  if (!accessToken) {
    return null;
  }

  try {
    const metricsResponse = await fetch(
      `https://graph.instagram.com/v18.0/${postId}/insights?metric=impressions,engagement,reach,saves&access_token=${accessToken}`
    );

    if (!metricsResponse.ok) {
      return null;
    }

    const data = (await metricsResponse.json()) as {
      data: Array<{ name: string; values: Array<{ value: number }> }>;
    };

    const metrics = {
      views: 0,
      likes: 0,
      comments: 0,
      shares: 0,
      saves: 0,
    };

    for (const insight of data.data) {
      if (insight.values && insight.values.length > 0) {
        const value = insight.values[0].value;
        if (insight.name === 'impressions') metrics.views = value;
        if (insight.name === 'engagement') metrics.likes = value;
        if (insight.name === 'reach') metrics.comments = value;
        if (insight.name === 'saves') metrics.saves = value;
      }
    }

    return metrics;
  } catch (error) {
    console.error('Failed to fetch reel metrics:', error);
    return null;
  }
}

// ============================================================================
// MAIN ORCHESTRATION FUNCTIONS
// ============================================================================

/**
 * Generate and publish a single Instagram Reel
 */
export async function generateAndPostReel(
  script: ReelScript,
  options: {
    scheduleTime?: string;
    caption?: string;
    retries?: number;
  } = {}
): Promise<InstagramReelResult> {
  const reelId = `reel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const startTime = Date.now();

  try {
    // Save initial metadata
    const initialMetadata: InstagramReelMetadata = {
      reelId,
      status: 'generating',
      script,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    await saveReelMetadata(initialMetadata);

    // Generate video
    const generatedReel = await generateVideo(script);

    // Update metadata with generated video
    const updatedMetadata: InstagramReelMetadata = {
      ...initialMetadata,
      status: 'uploaded',
      videoUrl: generatedReel.videoUrl,
      videoId: generatedReel.videoId,
      updatedAt: new Date().toISOString(),
    };
    await saveReelMetadata(updatedMetadata);

    // Publish to Instagram
    const publishResult = await publishToInstagram(generatedReel, options);

    // Update metadata with publish result
    if (publishResult.success) {
      const finalMetadata: InstagramReelMetadata = {
        ...updatedMetadata,
        status: 'published',
        postId: publishResult.postId,
        postUrl: publishResult.postUrl,
        scheduledTime: options.scheduleTime,
        publishedTime: publishResult.publishedTime,
        updatedAt: new Date().toISOString(),
      };
      await saveReelMetadata(finalMetadata);
    } else {
      const failedMetadata: InstagramReelMetadata = {
        ...updatedMetadata,
        status: 'failed',
        error: publishResult.error,
        updatedAt: new Date().toISOString(),
      };
      await saveReelMetadata(failedMetadata);
    }

    return {
      ...publishResult,
      reelId,
      duration: Date.now() - startTime,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);

    const failedMetadata: InstagramReelMetadata = {
      reelId,
      status: 'failed',
      script,
      error: errorMsg,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    await saveReelMetadata(failedMetadata);

    return {
      success: false,
      reelId,
      error: errorMsg,
      duration: Date.now() - startTime,
    };
  }
}

/**
 * Generate and publish multiple Instagram Reels in batch
 */
export async function generateAndPostReelsBatch(
  scripts: ReelScript[],
  options: {
    parallel?: boolean;
    scheduleTimeOffset?: number; // milliseconds between scheduled posts
    retries?: number;
  } = {}
): Promise<BatchReelResult> {
  const { parallel = true, scheduleTimeOffset = 86400000, retries = 3 } = options;
  const requestId = `batch-${Date.now()}`;
  const startTime = Date.now();

  const results: InstagramReelResult[] = [];

  if (parallel) {
    const promises = scripts.map((script, index) => {
      const scheduleTime = new Date(
        Date.now() + index * scheduleTimeOffset
      ).toISOString();
      return generateAndPostReel(script, { scheduleTime, retries });
    });

    const batchResults = await Promise.allSettled(promises);
    for (const result of batchResults) {
      if (result.status === 'fulfilled') {
        results.push(result.value);
      } else {
        results.push({
          success: false,
          error: result.reason?.message || 'Unknown error',
        });
      }
    }
  } else {
    for (let index = 0; index < scripts.length; index++) {
      const script = scripts[index];
      const scheduleTime = new Date(
        Date.now() + index * scheduleTimeOffset
      ).toISOString();
      const result = await generateAndPostReel(script, { scheduleTime, retries });
      results.push(result);
    }
  }

  const batchResult: BatchReelResult = {
    requestId,
    timestamp: new Date().toISOString(),
    totalReels: scripts.length,
    successCount: results.filter((r) => r.success).length,
    failureCount: results.filter((r) => !r.success).length,
    results,
    totalDuration: Date.now() - startTime,
  };

  // Save batch results
  const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/instagram';
  if (!existsSync(runtimeDir)) {
    await mkdir(runtimeDir, { recursive: true });
  }

  const batchPath = path.join(runtimeDir, `batch-${requestId}.json`);
  await writeFile(batchPath, JSON.stringify(batchResult, null, 2));

  return batchResult;
}

/**
 * Update reel metrics by fetching from Instagram
 */
export async function updateReelMetrics(reelId: string): Promise<InstagramReelMetadata | null> {
  const metadata = await loadReelMetadata(reelId);

  if (!metadata || !metadata.postId) {
    return null;
  }

  const metrics = await getReelMetrics(metadata.postId);

  if (metrics) {
    const updated: InstagramReelMetadata = {
      ...metadata,
      metrics,
      updatedAt: new Date().toISOString(),
    };
    await saveReelMetadata(updated);
    return updated;
  }

  return metadata;
}

/**
 * Get reel status and details
 */
export async function getReelStatus(reelId: string): Promise<InstagramReelMetadata | null> {
  return loadReelMetadata(reelId);
}

/**
 * Get all reel statuses
 */
export async function getAllReelStatuses(): Promise<InstagramReelMetadata[]> {
  return listReelsMetadata();
}
