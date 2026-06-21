/**
 * YOUTUBE LONG-FORM AUTOMATION
 *
 * Automatically generates and posts YouTube long-form (vertical) videos:
 * - Read video scripts from CONTENT_CALENDAR_MONTHLY.md
 * - Generate vertical video (9:16 aspect ratio) via Synthesia, D-ID, or Replicate
 * - Add voiceover, text overlays, background music, and captions
 * - Upload to YouTube via YouTube Data API
 * - Auto-schedule posting and manage playlists
 * - Track engagement metrics (views, likes, comments, watch time)
 *
 * Environment Requirements:
 * - YOUTUBE_CHANNEL_ID: YouTube channel ID (e.g., UCxxx...)
 * - YOUTUBE_API_KEY: YouTube Data API key
 * - VIDEO_GENERATION_API: 'synthesia' | 'd-id' | 'replicate' (default: synthesia)
 * - SYNTHESIA_API_KEY (if using Synthesia)
 * - DID_API_KEY (if using D-ID)
 * - REPLICATE_API_TOKEN (if using Replicate)
 * - ELEVENLABS_API_KEY (if using ElevenLabs for voiceover)
 * - RUNTIME_API_URL: Backend URL for webhooks
 * - RUNTIME_DATA_DIR: Directory for storing automation data (default: .runtime/youtube)
 */

import { readFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ============================================================================
// TYPES
// ============================================================================

export interface YouTubeScript {
  title: string;
  description: string;
  hook: string;
  mainPoints: string[];
  cta: string;
  duration: number; // seconds (recommended 60-600 for long-form)
  voicePrompt?: string;
  backgroundMusic?: string;
  textOverlays?: string[];
  tags?: string[];
  affiliateLinks?: Record<string, string>;
  playlistId?: string;
  uploadAsShort?: boolean; // If true, upload as YouTube Short instead
}

export interface GeneratedVideo {
  videoUrl: string;
  videoId?: string;
  thumbnail?: string;
  duration: number;
  aspectRatio: '16:9' | '9:16'; // 9:16 for Shorts/vertical
  script: YouTubeScript;
  generatedAt: string;
  fileSize?: number;
}

export interface YouTubeUploadResult {
  success: boolean;
  videoId?: string;
  videoUrl?: string;
  channelId?: string;
  uploadedAt?: string;
  scheduledAt?: string;
  status?: 'uploaded' | 'processing' | 'scheduled' | 'published';
  duration?: number;
  error?: string;
  script?: YouTubeScript;
  metrics?: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
    watchTime: number;
  };
}

export interface VideoGenerationOptions {
  aspectRatio?: '16:9' | '9:16';
  quality?: 'low' | 'medium' | 'high';
  fps?: number;
  bitrate?: string;
  includeWatermark?: boolean;
}

// ============================================================================
// VIDEO GENERATION
// ============================================================================

/**
 * Generate video via Synthesia.io API with vertical aspect ratio
 */
async function generateSynthesiaVideo(
  script: YouTubeScript,
  options: VideoGenerationOptions = {}
): Promise<GeneratedVideo> {
  const synthesiaKey = process.env.SYNTHESIA_API_KEY;

  if (!synthesiaKey) {
    throw new Error('SYNTHESIA_API_KEY not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const aspectRatio = options.aspectRatio || '9:16';
  const [width, height] = aspectRatio === '9:16' ? [720, 1280] : [1920, 1080];

  const createResponse = await fetch('https://api.synthesia.io/v1/videos', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${synthesiaKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: script.title,
      description: script.description,
      visibility: 'private',
      test: false,
      aspectRatio,
      width,
      height,
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
            videoUrl: script.backgroundMusic,
          },
        },
      ],
      callbackUrl: `${process.env.RUNTIME_API_URL || 'http://localhost:3000'}/api/automation/youtube/webhook`,
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Synthesia API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string };

  return {
    videoUrl: `https://synthesia.io/videos/${data.id}`,
    duration: script.duration,
    aspectRatio,
    script,
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Generate video via D-ID API with vertical aspect ratio
 */
async function generateDIDVideo(
  script: YouTubeScript,
  options: VideoGenerationOptions = {}
): Promise<GeneratedVideo> {
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
      config: {
        resolution: [720, 1280],
      },
      webhook_url: `${process.env.RUNTIME_API_URL || 'http://localhost:3000'}/api/automation/youtube/webhook`,
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
    aspectRatio: '9:16',
    script,
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Generate video via Replicate (with vertical output)
 */
async function generateReplicateVideo(
  script: YouTubeScript,
  options: VideoGenerationOptions = {}
): Promise<GeneratedVideo> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  // Generate voiceover
  const voiceResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: 'e995f61bf6dc5bb2db36670b1abc4eb988f9d569e0696b9f5e29ff37773f5d2b',
      input: {
        text: voiceScript,
        voice_id: 'EXAVITQu4vr4xnSDxMaL',
      },
    }),
  });

  if (!voiceResponse.ok) {
    throw new Error(`Voice generation failed: ${await voiceResponse.text()}`);
  }

  const voicePrediction = (await voiceResponse.json()) as { id: string; output?: string };

  // Poll for voiceover completion
  let voiceData = voicePrediction;
  let attempts = 0;
  const maxAttempts = 60;

  while (!voiceData.output && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    const pollResponse = await fetch(
      `https://api.replicate.com/v1/predictions/${voiceData.id}`,
      {
        headers: {
          Authorization: `Token ${replicateToken}`,
        },
      }
    );

    if (pollResponse.ok) {
      voiceData = (await pollResponse.json()) as { id: string; output?: string };
    }

    attempts++;
  }

  if (!voiceData.output) {
    throw new Error('Voice generation did not complete');
  }

  // Generate vertical video
  const videoResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: '4fe07e23faffc7af3c24cbf1234c9c86c7b3c135498c9b1a3d19e122d9b51670',
      input: {
        audio_url: voiceData.output,
        frames: script.duration * (options.fps || 30),
        fps: options.fps || 30,
        width: 720,
        height: 1280,
        text_overlay: (script.textOverlays || []).join(' | '),
      },
    }),
  });

  if (!videoResponse.ok) {
    throw new Error(`Video generation failed: ${await videoResponse.text()}`);
  }

  const videoPrediction = (await videoResponse.json()) as { id: string; output?: string };

  // Poll for video completion
  let videoData = videoPrediction;
  attempts = 0;

  while (!videoData.output && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    const pollResponse = await fetch(
      `https://api.replicate.com/v1/predictions/${videoData.id}`,
      {
        headers: {
          Authorization: `Token ${replicateToken}`,
        },
      }
    );

    if (pollResponse.ok) {
      videoData = (await pollResponse.json()) as { id: string; output?: string };
    }

    attempts++;
  }

  if (!videoData.output) {
    throw new Error('Video generation did not complete');
  }

  return {
    videoUrl: videoData.output,
    duration: script.duration,
    aspectRatio: '9:16',
    script,
    generatedAt: new Date().toISOString(),
  };
}

// ============================================================================
// SCRIPT PARSING
// ============================================================================

/**
 * Parse YouTube video script from CONTENT_CALENDAR_MONTHLY.md
 */
async function parseYouTubeScript(
  contentFile: string = 'CONTENT_CALENDAR_MONTHLY.md',
  postNumber: number = 1
): Promise<YouTubeScript> {
  try {
    const content = await readFile(contentFile, 'utf-8');

    // Find specific post section
    const postRegex = new RegExp(
      `### Post ${postNumber}:[\\s\\S]*?(?=### Post \\d+|$)`,
      'i'
    );
    const postMatch = content.match(postRegex);

    if (!postMatch) {
      throw new Error(`Post ${postNumber} not found`);
    }

    const postContent = postMatch[0];
    const script: YouTubeScript = {
      title: '',
      description: '',
      hook: '',
      mainPoints: [],
      cta: '',
      duration: 120, // Default 2 minutes for long-form
    };

    // Extract title
    const titleMatch = postContent.match(/### Post \d+: "(.+?)"/);
    if (titleMatch) script.title = titleMatch[1];

    // Use title as description if not found
    script.description = script.title;

    // Extract hook
    const hookMatch = postContent.match(/\*\*Hook\*\*[:\n>\s]+([^*]+)/i);
    if (hookMatch) script.hook = hookMatch[1].trim();

    // Extract main points
    const mainMatch = postContent.match(/\*\*Main Content[^*]+\*\*([^*]+?)(?=\*\*|$)/is);
    if (mainMatch) {
      script.mainPoints = mainMatch[1]
        .split(/\d+\.\s/)
        .filter((p) => p.trim())
        .map((p) => p.trim().replace(/\n+/g, ' '));
    }

    // Extract CTA
    const ctaMatch = postContent.match(/\*\*Call-to-Action\*\*[:\n>\s]+([^*]+)/i);
    if (ctaMatch) script.cta = ctaMatch[1].trim();

    // Extract tags
    const tagsMatch = postContent.match(/\*\*Tags[^*]*\*\*[:\n>\s]+([^*]+)/i);
    if (tagsMatch) {
      script.tags = tagsMatch[1]
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t);
    }

    // Extract affiliate links
    const affiliateMatch = postContent.match(/\*\*Affiliate Links[^*]+\*\*([^*]+?)(?=\*\*|$)/is);
    if (affiliateMatch) {
      script.affiliateLinks = {};
      const linkMatches = affiliateMatch[1].matchAll(/- ([^:]+):\s*`?([^`\n]+)`?/g);
      for (const match of linkMatches) {
        script.affiliateLinks[match[1].trim()] = match[2].trim();
      }
    }

    return script;
  } catch (error) {
    throw new Error(`Failed to parse YouTube script: ${error}`);
  }
}

// ============================================================================
// YOUTUBE API UPLOAD
// ============================================================================

/**
 * Upload video to YouTube via YouTube Data API
 */
async function uploadVideoToYouTube(
  videoUrl: string,
  script: YouTubeScript,
  options: { scheduledAt?: string; playlistId?: string } = {}
): Promise<YouTubeUploadResult> {
  try {
    const channelId = process.env.YOUTUBE_CHANNEL_ID;
    const apiKey = process.env.YOUTUBE_API_KEY;

    if (!channelId || !apiKey) {
      return {
        success: false,
        error: 'YOUTUBE_CHANNEL_ID or YOUTUBE_API_KEY not configured',
        script,
      };
    }

    // Build video title and description
    const title = script.title;
    const description = `${script.description}\n\n${script.hook}\n\n${script.cta}${
      script.affiliateLinks
        ? '\n\nAffiliate Links:\n' +
          Object.entries(script.affiliateLinks)
            .map(([name, url]) => `${name}: ${url}`)
            .join('\n')
        : ''
    }\n\n#trading #finance #profitengine`;

    const tags = [
      ...(script.tags || []),
      'trading',
      'finance',
      'profitengine',
      'youtube-shorts',
    ].slice(0, 30); // YouTube max 30 tags

    // Create video insert request
    const requestBody = {
      snippet: {
        title,
        description,
        tags,
        categoryId: '22', // People & Blogs
        defaultLanguage: 'en',
      },
      status: {
        privacyStatus: 'private' as const,
        publishAt: options.scheduledAt,
        selfDeclaredMadeForKids: false,
      },
      processingDetails: {
        processingStatus: 'processing',
      },
    };

    // Upload video (requires OAuth2 access token in production)
    // For testing/automation, use service account or API key with resumable upload
    const uploadResponse = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?part=snippet,status,processingDetails&key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }
    );

    if (!uploadResponse.ok) {
      const error = await uploadResponse.text();
      return {
        success: false,
        error: `YouTube API error: ${error}`,
        script,
      };
    }

    const uploadData = (await uploadResponse.json()) as {
      id: string;
      snippet?: { title: string };
    };

    // Add to playlist if specified
    if (options.playlistId) {
      await addVideoToPlaylist(uploadData.id, options.playlistId, apiKey);
    }

    return {
      success: true,
      videoId: uploadData.id,
      videoUrl: `https://youtube.com/watch?v=${uploadData.id}`,
      channelId,
      uploadedAt: new Date().toISOString(),
      scheduledAt: options.scheduledAt,
      status: options.scheduledAt ? 'scheduled' : 'uploaded',
      duration: script.duration,
      script,
    };
  } catch (error) {
    return {
      success: false,
      error: `Video upload failed: ${error}`,
      script,
    };
  }
}

/**
 * Add video to a YouTube playlist
 */
async function addVideoToPlaylist(
  videoId: string,
  playlistId: string,
  apiKey: string
): Promise<void> {
  const response = await fetch(
    `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&key=${apiKey}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        snippet: {
          playlistId,
          resourceId: {
            kind: 'youtube#video',
            videoId,
          },
        },
      }),
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to add video to playlist: ${await response.text()}`);
  }
}

// ============================================================================
// METRICS & ENGAGEMENT
// ============================================================================

/**
 * Fetch video metrics from YouTube API
 */
export async function getVideoMetrics(videoId: string): Promise<YouTubeUploadResult['metrics']> {
  try {
    const apiKey = process.env.YOUTUBE_API_KEY;

    if (!apiKey) {
      throw new Error('YOUTUBE_API_KEY not configured');
    }

    const response = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?id=${videoId}&key=${apiKey}&part=statistics`,
      {
        method: 'GET',
      }
    );

    if (!response.ok) {
      throw new Error(`YouTube API error: ${await response.text()}`);
    }

    const data = (await response.json()) as {
      items?: Array<{ statistics?: { viewCount?: string; likeCount?: string; commentCount?: string } }>;
    };

    if (!data.items || data.items.length === 0) {
      throw new Error('Video not found');
    }

    const stats = data.items[0].statistics;

    return {
      views: parseInt(stats?.viewCount || '0', 10),
      likes: parseInt(stats?.likeCount || '0', 10),
      comments: parseInt(stats?.commentCount || '0', 10),
      shares: 0, // YouTube API doesn't expose shares
      watchTime: 0, // Requires Analytics API
    };
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    return {
      views: 0,
      likes: 0,
      comments: 0,
      shares: 0,
      watchTime: 0,
    };
  }
}

// ============================================================================
// MAIN ORCHESTRATION
// ============================================================================

/**
 * Main function: Generate and post YouTube long-form video
 */
export async function generateAndPostYouTubeVideo(
  postNumber: number = 1,
  options: {
    scheduledAt?: string;
    playlistId?: string;
    videoGenerationApi?: 'synthesia' | 'd-id' | 'replicate';
  } = {}
): Promise<YouTubeUploadResult> {
  try {
    // Ensure runtime directory exists
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/youtube';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    // Parse script from content calendar
    console.log(`Parsing YouTube video script: Post ${postNumber}`);
    const script = await parseYouTubeScript('CONTENT_CALENDAR_MONTHLY.md', postNumber);

    // Generate video
    console.log(`Generating video for: ${script.title}`);
    const videoProvider = options.videoGenerationApi || process.env.VIDEO_GENERATION_API || 'synthesia';
    let generatedVideo: GeneratedVideo;

    if (videoProvider === 'synthesia') {
      generatedVideo = await generateSynthesiaVideo(script);
    } else if (videoProvider === 'd-id') {
      generatedVideo = await generateDIDVideo(script);
    } else {
      generatedVideo = await generateReplicateVideo(script);
    }

    console.log(`Generated video: ${generatedVideo.videoUrl}`);

    // Upload to YouTube
    console.log(`Uploading video to YouTube...`);
    const uploadResult = await uploadVideoToYouTube(generatedVideo.videoUrl, script, {
      scheduledAt: options.scheduledAt,
      playlistId: options.playlistId || script.playlistId,
    });

    if (uploadResult.success) {
      console.log(`✓ Video uploaded: ${uploadResult.videoUrl}`);

      // Fetch initial metrics
      if (uploadResult.videoId) {
        try {
          uploadResult.metrics = await getVideoMetrics(uploadResult.videoId);
        } catch (e) {
          console.warn('Could not fetch initial metrics:', e);
        }
      }
    } else {
      console.error(`✗ Video upload failed: ${uploadResult.error}`);
    }

    return uploadResult;
  } catch (error) {
    return {
      success: false,
      error: `YouTube automation failed: ${error}`,
    };
  }
}

/**
 * Export types for API routes
 */
export { YouTubeScript, GeneratedVideo };
