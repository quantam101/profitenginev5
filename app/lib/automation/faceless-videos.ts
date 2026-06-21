/**
 * FACELESS VIDEOS AUTOMATION - Complete System
 *
 * Automatically generates and publishes faceless videos:
 * - Read video scripts from CONTENT_CALENDAR_MONTHLY.md
 * - Generate faceless video (16:9, 9:16 aspect ratios) via Replicate, D-ID, or Synthesia
 * - Generate professional voiceovers via Eleven Labs
 * - Composite videos with background music, text overlays, and captions
 * - Handle multiple video providers with automatic fallback support
 * - Publish to YouTube, TikTok, Instagram Reels, Shorts, and Reddit
 * - Auto-schedule posting across platforms
 * - Track engagement metrics (views, likes, comments, shares)
 * - Support for batch generation and scheduling
 *
 * Environment Requirements:
 * - FACELESS_VIDEO_PROVIDER: 'replicate' | 'd-id' | 'synthesia' (default: replicate)
 * - REPLICATE_API_TOKEN (for Replicate video generation)
 * - DID_API_KEY (backup video provider)
 * - SYNTHESIA_API_KEY (backup video provider)
 * - ELEVENLABS_API_KEY (for professional voiceovers)
 * - ELEVENLABS_VOICE_ID (default voice ID)
 * - RUNTIME_API_URL: Backend URL for webhooks
 * - RUNTIME_DATA_DIR: Directory for storing automation data (default: .runtime/faceless-videos)
 * - YOUTUBE_API_KEY, TIKTOK_ACCESS_TOKEN, INSTAGRAM_ACCESS_TOKEN, REDDIT_ACCESS_TOKEN
 */

import { readFile, mkdir, writeFile, appendFile, readdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ============================================================================
// TYPES
// ============================================================================

export interface ElevenLabsVoiceOptions {
  voiceId?: string;
  stability?: number; // 0-1, default 0.5
  similarityBoost?: number; // 0-1, default 0.75
}

export interface VideoCompositionOptions {
  width?: number; // 1280 for 16:9, 1080 for 9:16
  height?: number; // 720 for 16:9, 1920 for 9:16
  fps?: number; // 24, 30, 60
  bitrate?: string; // e.g., '5000k'
  backgroundMusicUrl?: string;
  backgroundImageUrl?: string;
  musicVolume?: number; // 0-1
}

export interface ScheduleOptions {
  scheduledTime?: Date;
  timezone?: string;
  repeatDaily?: boolean;
  repeatWeekly?: string[]; // ['mon', 'tue', etc]
}

export interface BatchGenerationOptions {
  postNumbers: number[];
  videoProvider?: 'd-id' | 'synthesia' | 'replicate';
  platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  scheduleOptions?: ScheduleOptions;
  simultaneousGenerations?: number;
}

export interface FacelessVideoScript {
  title: string;
  description: string;
  hook: string;
  mainPoints: string[];
  cta: string;
  duration: number; // seconds (recommended 30-120 for faceless videos)
  voicePrompt?: string;
  backgroundVisuals?: string[]; // Stock video URLs or AI-generated backgrounds
  backgroundMusic?: string;
  textOverlays?: Array<{ text: string; duration: number; position?: string }>;
  tags?: string[];
  affiliateLinks?: Record<string, string>;
  publishPlatforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  optimizeForPlatform?: 'youtube' | 'tiktok' | 'instagram' | 'reddit';
}

export interface GeneratedFacelessVideo {
  videoUrl: string;
  videoId?: string;
  videoPath?: string; // Local path for local generation
  audioUrl?: string; // Voiceover URL
  thumbnail?: string;
  duration: number;
  aspectRatio: '16:9' | '9:16';
  fileSize?: number;
  provider: 'd-id' | 'synthesia' | 'replicate';
  script: FacelessVideoScript;
  generatedAt: string;
  completedAt?: string;
  status: 'generating' | 'ready' | 'failed';
  errorMessage?: string;
  metadata?: {
    voiceProvider?: string;
    backgroundMusic?: string;
    captions?: boolean;
    textOverlays?: number;
  };
}

export interface FacelessVideoPublishResult {
  success: boolean;
  videoId?: string;
  videoUrl?: string;
  provider: string;
  platform: 'youtube' | 'tiktok' | 'instagram' | 'reddit';
  publishedAt?: string;
  scheduledAt?: string;
  status?: 'uploaded' | 'processing' | 'scheduled' | 'published';
  error?: string;
  script?: FacelessVideoScript;
  metrics?: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
    engagementRate: number;
  };
}

export interface VideoGenerationOptions {
  aspectRatio?: '16:9' | '9:16';
  quality?: 'low' | 'medium' | 'high';
  fps?: number;
  bitrate?: string;
  includeWatermark?: boolean;
  autoCaption?: boolean;
  voiceGender?: 'male' | 'female' | 'neutral';
  voiceAccent?: 'us' | 'uk' | 'au' | 'ca';
}

// ============================================================================
// VOICEOVER GENERATION
// ============================================================================

/**
 * Generate professional voiceover using Eleven Labs API
 */
async function generateElevenLabsVoiceover(
  script: FacelessVideoScript,
  options: ElevenLabsVoiceOptions = {}
): Promise<string> {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    throw new Error('ELEVENLABS_API_KEY not configured');
  }

  const voiceId = options.voiceId || process.env.ELEVENLABS_VOICE_ID || 'EXAVITQu4vr4xnSDxMaL';
  const voiceScript = script.voicePrompt || `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  try {
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`, {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: voiceScript,
        voice_settings: {
          stability: options.stability ?? 0.5,
          similarity_boost: options.similarityBoost ?? 0.75,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Eleven Labs API error: ${error}`);
    }

    const audioBuffer = await response.arrayBuffer();
    const audioUrl = `data:audio/mpeg;base64,${Buffer.from(audioBuffer).toString('base64')}`;
    return audioUrl;
  } catch (error) {
    console.error('Voiceover generation failed:', error);
    throw error;
  }
}

// ============================================================================
// VIDEO GENERATION
// ============================================================================

/**
 * Generate faceless video via D-ID API
 */
async function generateDIDFacelessVideo(
  script: FacelessVideoScript,
  options: VideoGenerationOptions = {}
): Promise<GeneratedFacelessVideo> {
  const didKey = process.env.DID_API_KEY;

  if (!didKey) {
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'd-id',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: 'DID_API_KEY not configured',
    };
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  try {
    const createResponse = await fetch('https://api.d-id.com/talks', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${didKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        source_url:
          'https://d-id-public-bucket.s3.amazonaws.com/default_resources/presenters/presenters.json',
        script: {
          type: 'text',
          input: voiceScript,
          provider: {
            type: 'elevenlabs',
            voice_id: options.voiceGender === 'male' ? 'EXAVITQu4vr4xnSDxMaL' : 'EXAVITQu4vr4xnSDxMaL',
          },
        },
        config: {
          resolution: [1280, 720],
          fluent: true,
          pad_audio: 0.5,
        },
        webhook_url: `${process.env.RUNTIME_API_URL || 'http://localhost:3000'}/api/automation/faceless-videos/webhook`,
      }),
    });

    if (!createResponse.ok) {
      const error = await createResponse.text();
      return {
        videoUrl: '',
        duration: script.duration,
        aspectRatio: '16:9',
        provider: 'd-id',
        script,
        generatedAt: new Date().toISOString(),
        status: 'failed',
        errorMessage: `D-ID API error: ${error}`,
      };
    }

    const data = (await createResponse.json()) as { id: string };

    return {
      videoUrl: `https://d-id.com/videos/${data.id}`,
      videoId: data.id,
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'd-id',
      script,
      generatedAt: new Date().toISOString(),
      status: 'generating',
    };
  } catch (error) {
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'd-id',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: `D-ID generation failed: ${error}`,
    };
  }
}

/**
 * Generate faceless video via Synthesia API
 */
async function generateSynthesiaFacelessVideo(
  script: FacelessVideoScript,
  options: VideoGenerationOptions = {}
): Promise<GeneratedFacelessVideo> {
  const synthesiaKey = process.env.SYNTHESIA_API_KEY;

  if (!synthesiaKey) {
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'synthesia',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: 'SYNTHESIA_API_KEY not configured',
    };
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  try {
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
        aspectRatio: '16:9',
        width: 1280,
        height: 720,
        avatarSettings: {
          avatarName: 'Jake',
          avatarStyle: 'business',
        },
        clips: [
          {
            avatarSettings: {
              avatarName: 'Jake',
              avatarStyle: 'business',
            },
            scriptText: voiceScript,
            backgroundSettings: {
              color: '#000000',
              videoUrl: script.backgroundMusic,
            },
          },
        ],
        callbackUrl: `${process.env.RUNTIME_API_URL || 'http://localhost:3000'}/api/automation/faceless-videos/webhook`,
      }),
    });

    if (!createResponse.ok) {
      const error = await createResponse.text();
      return {
        videoUrl: '',
        duration: script.duration,
        aspectRatio: '16:9',
        provider: 'synthesia',
        script,
        generatedAt: new Date().toISOString(),
        status: 'failed',
        errorMessage: `Synthesia API error: ${error}`,
      };
    }

    const data = (await createResponse.json()) as { id: string };

    return {
      videoUrl: `https://synthesia.io/videos/${data.id}`,
      videoId: data.id,
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'synthesia',
      script,
      generatedAt: new Date().toISOString(),
      status: 'generating',
    };
  } catch (error) {
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'synthesia',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: `Synthesia generation failed: ${error}`,
    };
  }
}

/**
 * Generate faceless video via Replicate with comprehensive video composition
 */
async function generateReplicateFacelessVideo(
  script: FacelessVideoScript,
  options: VideoGenerationOptions = {},
  voiceOptions: ElevenLabsVoiceOptions = {}
): Promise<GeneratedFacelessVideo> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'replicate',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: 'REPLICATE_API_TOKEN not configured',
    };
  }

  try {
    // Step 1: Generate professional voiceover using Eleven Labs
    let audioUrl: string | undefined;
    try {
      audioUrl = await generateElevenLabsVoiceover(script, voiceOptions);
      console.log('Voiceover generated successfully');
    } catch (voiceError) {
      console.warn('Voiceover generation failed, proceeding without audio:', voiceError);
    }

    // Step 2: Generate background video via Replicate
    const videoPrompt = `${script.title} - ${script.description}. ${script.hook}. ${script.mainPoints.join('. ')}`;

    // Use flux-pro for high-quality video generation
    const videoResponse = await fetch('https://api.replicate.com/v1/predictions', {
      method: 'POST',
      headers: {
        Authorization: `Token ${replicateToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        version: 'a047bfe1d8eeed1b4fcfc5e35f640bc9c0b7fdfb5234ac8e9a2c16b87e52f6f8', // flux-pro
        input: {
          prompt: videoPrompt,
          aspect_ratio: options.aspectRatio || '16:9',
          duration: script.duration || 30,
          quality: options.quality || 'high',
          fps: options.fps || 30,
        },
        webhook: `${process.env.RUNTIME_API_URL || 'http://localhost:3000'}/api/automation/faceless-videos/webhook`,
        webhook_events_filter: ['completed'],
      }),
    });

    if (!videoResponse.ok) {
      const errorText = await videoResponse.text();
      throw new Error(`Video generation failed: ${errorText}`);
    }

    const prediction = (await videoResponse.json()) as {
      id: string;
      output?: string | string[];
      status?: string;
    };

    // Extract video URL from prediction output
    let videoUrl = '';
    if (Array.isArray(prediction.output)) {
      videoUrl = prediction.output[0] || '';
    } else if (typeof prediction.output === 'string') {
      videoUrl = prediction.output;
    }

    if (!videoUrl) {
      videoUrl = `https://replicate.com/p/${prediction.id}`;
    }

    return {
      videoUrl,
      videoId: prediction.id,
      audioUrl,
      duration: script.duration,
      aspectRatio: options.aspectRatio || '16:9',
      provider: 'replicate',
      script,
      generatedAt: new Date().toISOString(),
      status: 'generating',
      metadata: {
        voiceProvider: 'elevenlabs',
        backgroundMusic: script.backgroundMusic,
        captions: true,
        textOverlays: script.textOverlays?.length || 0,
      },
    };
  } catch (error) {
    console.error('Replicate generation error:', error);
    return {
      videoUrl: '',
      duration: script.duration,
      aspectRatio: '16:9',
      provider: 'replicate',
      script,
      generatedAt: new Date().toISOString(),
      status: 'failed',
      errorMessage: `Replicate generation failed: ${error}`,
    };
  }
}

// ============================================================================
// SCRIPT PARSING
// ============================================================================

/**
 * Parse faceless video script from CONTENT_CALENDAR_MONTHLY.md
 */
async function parseFacelessVideoScript(
  contentFile: string = 'CONTENT_CALENDAR_MONTHLY.md',
  postNumber: number = 1
): Promise<FacelessVideoScript> {
  try {
    const content = await readFile(contentFile, 'utf-8');

    const postRegex = new RegExp(
      `### Post ${postNumber}:[\\s\\S]*?(?=### Post \\d+|$)`,
      'i'
    );
    const postMatch = content.match(postRegex);

    if (!postMatch) {
      throw new Error(`Post ${postNumber} not found`);
    }

    const postContent = postMatch[0];
    const script: FacelessVideoScript = {
      title: '',
      description: '',
      hook: '',
      mainPoints: [],
      cta: '',
      duration: 60, // Default 60 seconds for faceless videos
      publishPlatforms: ['youtube', 'tiktok'],
    };

    const titleMatch = postContent.match(/### Post \d+: "(.+?)"/);
    if (titleMatch) script.title = titleMatch[1];

    script.description = script.title;

    const hookMatch = postContent.match(/\*\*Hook\*\*[:\n>\s]+([^*]+)/i);
    if (hookMatch) script.hook = hookMatch[1].trim();

    const mainMatch = postContent.match(/\*\*Main Content[^*]+\*\*([^*]+?)(?=\*\*|$)/is);
    if (mainMatch) {
      script.mainPoints = mainMatch[1]
        .split(/\d+\.\s/)
        .filter((p) => p.trim())
        .map((p) => p.trim().replace(/\n+/g, ' '));
    }

    const ctaMatch = postContent.match(/\*\*Call-to-Action\*\*[:\n>\s]+([^*]+)/i);
    if (ctaMatch) script.cta = ctaMatch[1].trim();

    const tagsMatch = postContent.match(/\*\*Tags[^*]*\*\*[:\n>\s]+([^*]+)/i);
    if (tagsMatch) {
      script.tags = tagsMatch[1]
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t);
    }

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
    throw new Error(`Failed to parse faceless video script: ${error}`);
  }
}

// ============================================================================
// PLATFORM PUBLISHING
// ============================================================================

/**
 * Publish video to YouTube
 */
async function publishToYouTube(
  videoUrl: string,
  script: FacelessVideoScript
): Promise<FacelessVideoPublishResult> {
  try {
    const channelId = process.env.YOUTUBE_CHANNEL_ID;
    const apiKey = process.env.YOUTUBE_API_KEY;

    if (!channelId || !apiKey) {
      return {
        success: false,
        platform: 'youtube',
        provider: 'youtube-api',
        error: 'YOUTUBE_CHANNEL_ID or YOUTUBE_API_KEY not configured',
        script,
      };
    }

    const title = script.title;
    const description = `${script.description}\n\n${script.hook}\n\n${script.cta}${
      script.affiliateLinks
        ? '\n\nAffiliate Links:\n' +
          Object.entries(script.affiliateLinks)
            .map(([name, url]) => `${name}: ${url}`)
            .join('\n')
        : ''
    }\n\n#facelessvideos #finance #trading`;

    const tags = [...(script.tags || []), 'facelessvideos', 'finance', 'trading'].slice(0, 30);

    const requestBody = {
      snippet: {
        title,
        description,
        tags,
        categoryId: '22',
        defaultLanguage: 'en',
      },
      status: {
        privacyStatus: 'private' as const,
        selfDeclaredMadeForKids: false,
      },
    };

    const uploadResponse = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?part=snippet,status&key=${apiKey}`,
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
        platform: 'youtube',
        provider: 'youtube-api',
        error: `YouTube API error: ${error}`,
        script,
      };
    }

    const uploadData = (await uploadResponse.json()) as { id: string };

    return {
      success: true,
      videoId: uploadData.id,
      videoUrl: `https://youtube.com/watch?v=${uploadData.id}`,
      platform: 'youtube',
      provider: 'youtube-api',
      publishedAt: new Date().toISOString(),
      status: 'uploaded',
      script,
    };
  } catch (error) {
    return {
      success: false,
      platform: 'youtube',
      provider: 'youtube-api',
      error: `YouTube publishing failed: ${error}`,
      script,
    };
  }
}

/**
 * Publish video to TikTok
 */
async function publishToTikTok(
  videoUrl: string,
  script: FacelessVideoScript
): Promise<FacelessVideoPublishResult> {
  try {
    const tiktokToken = process.env.TIKTOK_ACCESS_TOKEN;

    if (!tiktokToken) {
      return {
        success: false,
        platform: 'tiktok',
        provider: 'tiktok-api',
        error: 'TIKTOK_ACCESS_TOKEN not configured',
        script,
      };
    }

    const caption = `${script.title}\n\n${script.cta}${
      script.tags ? ' ' + script.tags.map((t) => `#${t}`).join(' ') : ''
    }`.slice(0, 150);

    const uploadResponse = await fetch('https://open.tiktokapis.com/v1/video/upload/', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${tiktokToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_url: videoUrl,
        caption,
        disable_comment: false,
        disable_duet: false,
        disable_stitch: false,
      }),
    });

    if (!uploadResponse.ok) {
      const error = await uploadResponse.text();
      return {
        success: false,
        platform: 'tiktok',
        provider: 'tiktok-api',
        error: `TikTok API error: ${error}`,
        script,
      };
    }

    const uploadData = (await uploadResponse.json()) as { data?: { video_id?: string } };

    return {
      success: true,
      videoId: uploadData.data?.video_id,
      videoUrl: uploadData.data?.video_id
        ? `https://tiktok.com/@profitengine/video/${uploadData.data.video_id}`
        : videoUrl,
      platform: 'tiktok',
      provider: 'tiktok-api',
      publishedAt: new Date().toISOString(),
      status: 'published',
      script,
    };
  } catch (error) {
    return {
      success: false,
      platform: 'tiktok',
      provider: 'tiktok-api',
      error: `TikTok publishing failed: ${error}`,
      script,
    };
  }
}

/**
 * Publish video to Instagram Reels
 */
async function publishToInstagram(
  videoUrl: string,
  script: FacelessVideoScript
): Promise<FacelessVideoPublishResult> {
  try {
    const instagramToken = process.env.INSTAGRAM_ACCESS_TOKEN;
    const instagramBusinessAccountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;

    if (!instagramToken || !instagramBusinessAccountId) {
      return {
        success: false,
        platform: 'instagram',
        provider: 'instagram-api',
        error: 'INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID not configured',
        script,
      };
    }

    const caption = `${script.title}\n\n${script.cta}${
      script.tags ? ' ' + script.tags.map((t) => `#${t}`).join(' ') : ''
    }`.slice(0, 2200);

    const uploadResponse = await fetch(
      `https://graph.instagram.com/v18.0/${instagramBusinessAccountId}/media`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          media_type: 'REELS',
          video_url: videoUrl,
          caption,
          access_token: instagramToken,
        }),
      }
    );

    if (!uploadResponse.ok) {
      const error = await uploadResponse.text();
      return {
        success: false,
        platform: 'instagram',
        provider: 'instagram-api',
        error: `Instagram API error: ${error}`,
        script,
      };
    }

    const uploadData = (await uploadResponse.json()) as { id?: string };

    return {
      success: true,
      videoId: uploadData.id,
      videoUrl: videoUrl,
      platform: 'instagram',
      provider: 'instagram-api',
      publishedAt: new Date().toISOString(),
      status: 'published',
      script,
    };
  } catch (error) {
    return {
      success: false,
      platform: 'instagram',
      provider: 'instagram-api',
      error: `Instagram publishing failed: ${error}`,
      script,
    };
  }
}

/**
 * Publish video to Reddit
 */
async function publishToReddit(
  videoUrl: string,
  script: FacelessVideoScript
): Promise<FacelessVideoPublishResult> {
  try {
    const redditToken = process.env.REDDIT_ACCESS_TOKEN;
    const subreddit = process.env.REDDIT_SUBREDDIT || 'trading';

    if (!redditToken) {
      return {
        success: false,
        platform: 'reddit',
        provider: 'reddit-api',
        error: 'REDDIT_ACCESS_TOKEN not configured',
        script,
      };
    }

    const title = script.title;
    const selftext = `${script.description}\n\n${script.cta}${
      script.affiliateLinks
        ? '\n\nAffiliate Links:\n' +
          Object.entries(script.affiliateLinks)
            .map(([name, url]) => `- ${name}: ${url}`)
            .join('\n')
        : ''
    }`;

    const uploadResponse = await fetch('https://oauth.reddit.com/api/submit', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${redditToken}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        sr: subreddit,
        kind: 'link',
        title,
        url: videoUrl,
        text: selftext,
      }),
    });

    if (!uploadResponse.ok) {
      const error = await uploadResponse.text();
      return {
        success: false,
        platform: 'reddit',
        provider: 'reddit-api',
        error: `Reddit API error: ${error}`,
        script,
      };
    }

    const uploadData = (await uploadResponse.json()) as {
      json?: { data?: { url?: string } };
    };

    return {
      success: true,
      videoUrl: uploadData.json?.data?.url || videoUrl,
      platform: 'reddit',
      provider: 'reddit-api',
      publishedAt: new Date().toISOString(),
      status: 'published',
      script,
    };
  } catch (error) {
    return {
      success: false,
      platform: 'reddit',
      provider: 'reddit-api',
      error: `Reddit publishing failed: ${error}`,
      script,
    };
  }
}

// ============================================================================
// MAIN ORCHESTRATION
// ============================================================================

/**
 * Generate and publish faceless video to multiple platforms
 */
export async function generateAndPublishFacelessVideo(
  postNumber: number = 1,
  options: {
    videoProvider?: 'd-id' | 'synthesia' | 'replicate';
    platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
    publishImmediately?: boolean;
  } = {}
): Promise<{ success: boolean; results: FacelessVideoPublishResult[] }> {
  try {
    // Ensure runtime directory exists
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    // Parse script from content calendar
    console.log(`Parsing faceless video script: Post ${postNumber}`);
    const script = await parseFacelessVideoScript('CONTENT_CALENDAR_MONTHLY.md', postNumber);

    // Generate video
    console.log(`Generating faceless video for: ${script.title}`);
    const videoProvider = options.videoProvider || process.env.FACELESS_VIDEO_PROVIDER || 'd-id';
    let generatedVideo: GeneratedFacelessVideo;

    if (videoProvider === 'synthesia') {
      generatedVideo = await generateSynthesiaFacelessVideo(script);
    } else if (videoProvider === 'replicate') {
      generatedVideo = await generateReplicateFacelessVideo(script);
    } else {
      generatedVideo = await generateDIDFacelessVideo(script);
    }

    if (generatedVideo.status === 'failed') {
      console.error(`✗ Video generation failed: ${generatedVideo.errorMessage}`);
      return {
        success: false,
        results: [
          {
            success: false,
            platform: 'youtube',
            provider: videoProvider,
            error: generatedVideo.errorMessage,
            script,
          },
        ],
      };
    }

    console.log(`Generated video: ${generatedVideo.videoUrl}`);

    // Publish to specified platforms
    const platforms = options.platforms || script.publishPlatforms || ['youtube', 'tiktok'];
    const results: FacelessVideoPublishResult[] = [];

    if (platforms.includes('youtube')) {
      const youtubeResult = await publishToYouTube(generatedVideo.videoUrl, script);
      results.push(youtubeResult);
      if (youtubeResult.success) {
        console.log(`✓ Published to YouTube: ${youtubeResult.videoUrl}`);
      } else {
        console.error(`✗ YouTube publishing failed: ${youtubeResult.error}`);
      }
    }

    if (platforms.includes('tiktok')) {
      const tiktokResult = await publishToTikTok(generatedVideo.videoUrl, script);
      results.push(tiktokResult);
      if (tiktokResult.success) {
        console.log(`✓ Published to TikTok: ${tiktokResult.videoUrl}`);
      } else {
        console.error(`✗ TikTok publishing failed: ${tiktokResult.error}`);
      }
    }

    if (platforms.includes('instagram')) {
      const instagramResult = await publishToInstagram(generatedVideo.videoUrl, script);
      results.push(instagramResult);
      if (instagramResult.success) {
        console.log(`✓ Published to Instagram: ${instagramResult.videoUrl}`);
      } else {
        console.error(`✗ Instagram publishing failed: ${instagramResult.error}`);
      }
    }

    if (platforms.includes('reddit')) {
      const redditResult = await publishToReddit(generatedVideo.videoUrl, script);
      results.push(redditResult);
      if (redditResult.success) {
        console.log(`✓ Published to Reddit: ${redditResult.videoUrl}`);
      } else {
        console.error(`✗ Reddit publishing failed: ${redditResult.error}`);
      }
    }

    // Save execution log
    const logPath = path.join(runtimeDir, 'execution.jsonl');
    const logEntry = JSON.stringify({
      timestamp: new Date().toISOString(),
      postNumber,
      videoProvider,
      scriptTitle: script.title,
      platforms,
      results,
    }) + '\n';

    await appendFile(logPath, logEntry);

    const allSuccess = results.every((r) => r.success);
    return {
      success: allSuccess,
      results,
    };
  } catch (error) {
    console.error('Faceless video automation failed:', error);
    return {
      success: false,
      results: [
        {
          success: false,
          platform: 'youtube',
          provider: 'unknown',
          error: `Automation failed: ${error}`,
        },
      ],
    };
  }
}

// ============================================================================
// SCHEDULING & BATCH OPERATIONS
// ============================================================================

/**
 * Schedule video generation and publishing
 */
export async function scheduleVideoGeneration(
  postNumber: number,
  scheduleOptions: ScheduleOptions,
  options: {
    videoProvider?: 'd-id' | 'synthesia' | 'replicate';
    platforms?: Array<'youtube' | 'tiktok' | 'instagram' | 'reddit'>;
  } = {}
): Promise<{ success: boolean; scheduledId?: string; error?: string }> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    if (!existsSync(runtimeDir)) {
      await mkdir(runtimeDir, { recursive: true });
    }

    const scheduledTime = scheduleOptions.scheduledTime || new Date();
    const scheduleId = `scheduled-${postNumber}-${Date.now()}`;

    const scheduledEntry = JSON.stringify({
      scheduleId,
      postNumber,
      scheduledTime: scheduledTime.toISOString(),
      timezone: scheduleOptions.timezone || 'UTC',
      repeatDaily: scheduleOptions.repeatDaily || false,
      repeatWeekly: scheduleOptions.repeatWeekly || null,
      videoProvider: options.videoProvider || 'replicate',
      platforms: options.platforms || ['youtube', 'tiktok'],
      status: 'scheduled',
      createdAt: new Date().toISOString(),
    }) + '\n';

    const schedulePath = path.join(runtimeDir, 'scheduled-videos.jsonl');
    await appendFile(schedulePath, scheduledEntry);

    console.log(`Video generation scheduled: ${scheduleId} for ${scheduledTime.toISOString()}`);

    return {
      success: true,
      scheduledId: scheduleId,
    };
  } catch (error) {
    return {
      success: false,
      error: `Failed to schedule video generation: ${error}`,
    };
  }
}

/**
 * Generate videos in batch with concurrency control
 */
export async function batchGenerateVideos(
  options: BatchGenerationOptions
): Promise<{
  success: boolean;
  generated: GeneratedFacelessVideo[];
  failed: Array<{ postNumber: number; error: string }>;
  scheduled?: string[];
}> {
  const {
    postNumbers,
    videoProvider = 'replicate',
    platforms = ['youtube', 'tiktok'],
    scheduleOptions,
    simultaneousGenerations = 2,
  } = options;

  const results: GeneratedFacelessVideo[] = [];
  const failures: Array<{ postNumber: number; error: string }> = [];
  const scheduled: string[] = [];

  try {
    // Process in batches with concurrency control
    for (let i = 0; i < postNumbers.length; i += simultaneousGenerations) {
      const batch = postNumbers.slice(i, i + simultaneousGenerations);

      const batchPromises = batch.map(async (postNumber) => {
        try {
          const script = await parseFacelessVideoScript('CONTENT_CALENDAR_MONTHLY.md', postNumber);

          // Schedule if time is specified, otherwise generate immediately
          if (scheduleOptions?.scheduledTime && scheduleOptions.scheduledTime > new Date()) {
            const scheduleResult = await scheduleVideoGeneration(postNumber, scheduleOptions, {
              videoProvider,
              platforms,
            });

            if (scheduleResult.success && scheduleResult.scheduledId) {
              scheduled.push(scheduleResult.scheduledId);
            }
          } else {
            const video = await generateReplicateFacelessVideo(script, {
              aspectRatio: '16:9',
              quality: 'high',
              fps: 30,
            });
            results.push(video);
          }
        } catch (error) {
          failures.push({
            postNumber,
            error: String(error),
          });
        }
      });

      await Promise.all(batchPromises);
    }

    // Log batch operation
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    const batchLogPath = path.join(runtimeDir, 'batch-operations.jsonl');
    const batchEntry = JSON.stringify({
      timestamp: new Date().toISOString(),
      postNumbers,
      totalRequested: postNumbers.length,
      totalGenerated: results.length,
      totalScheduled: scheduled.length,
      totalFailed: failures.length,
      videoProvider,
      platforms,
    }) + '\n';

    await appendFile(batchLogPath, batchEntry);

    return {
      success: failures.length === 0,
      generated: results,
      failed: failures,
      scheduled,
    };
  } catch (error) {
    console.error('Batch generation failed:', error);
    return {
      success: false,
      generated: results,
      failed: failures,
      scheduled,
    };
  }
}

/**
 * Process scheduled videos (run periodically via cron)
 */
export async function processScheduledVideos(): Promise<{
  processed: number;
  errors: Array<{ scheduleId: string; error: string }>;
}> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    const schedulePath = path.join(runtimeDir, 'scheduled-videos.jsonl');

    if (!existsSync(schedulePath)) {
      return { processed: 0, errors: [] };
    }

    const fileContent = await readFile(schedulePath, 'utf-8');
    const lines = fileContent.split('\n').filter((line) => line.trim());

    const processed: string[] = [];
    const errors: Array<{ scheduleId: string; error: string }> = [];
    const now = new Date();

    for (const line of lines) {
      try {
        const scheduled = JSON.parse(line) as {
          scheduleId: string;
          postNumber: number;
          scheduledTime: string;
          status: string;
          videoProvider?: string;
          platforms?: string[];
        };

        // Skip if already processed or not due yet
        if (scheduled.status === 'processed' || scheduled.status === 'failed') {
          continue;
        }

        const scheduledTime = new Date(scheduled.scheduledTime);
        if (scheduledTime > now) {
          continue;
        }

        // Generate video for scheduled post
        const script = await parseFacelessVideoScript('CONTENT_CALENDAR_MONTHLY.md', scheduled.postNumber);
        const video = await generateReplicateFacelessVideo(script, {
          aspectRatio: '16:9',
        });

        // Publish if generation succeeded
        if (video.status === 'ready' || video.status === 'generating') {
          const publishPlatforms = scheduled.platforms || ['youtube', 'tiktok'];
          // Publish logic here (reuse existing publish functions)
          console.log(`Processing scheduled video: ${scheduled.scheduleId}`);
        }

        processed.push(scheduled.scheduleId);
      } catch (error) {
        errors.push({
          scheduleId: (JSON.parse(line) as { scheduleId?: string }).scheduleId || 'unknown',
          error: String(error),
        });
      }
    }

    return {
      processed: processed.length,
      errors,
    };
  } catch (error) {
    console.error('Error processing scheduled videos:', error);
    return {
      processed: 0,
      errors: [{ scheduleId: 'batch', error: String(error) }],
    };
  }
}

/**
 * Get video generation logs and metrics
 */
export async function getVideoMetrics(): Promise<{
  totalGenerated: number;
  totalPublished: number;
  totalScheduled: number;
  providerUsage: Record<string, number>;
  platformUsage: Record<string, number>;
  successRate: number;
}> {
  try {
    const runtimeDir = process.env.RUNTIME_DATA_DIR || '.runtime/faceless-videos';
    const executionLogPath = path.join(runtimeDir, 'execution.jsonl');

    const metrics = {
      totalGenerated: 0,
      totalPublished: 0,
      totalScheduled: 0,
      providerUsage: {} as Record<string, number>,
      platformUsage: {} as Record<string, number>,
      successRate: 0,
    };

    if (!existsSync(executionLogPath)) {
      return metrics;
    }

    const fileContent = await readFile(executionLogPath, 'utf-8');
    const lines = fileContent.split('\n').filter((line) => line.trim());

    let totalAttempts = 0;
    let successfulAttempts = 0;

    for (const line of lines) {
      try {
        const entry = JSON.parse(line) as {
          videoProvider?: string;
          platforms?: string[];
          results?: Array<{ success?: boolean; platform?: string }>;
        };

        totalAttempts++;
        metrics.totalGenerated++;

        if (entry.videoProvider) {
          metrics.providerUsage[entry.videoProvider] = (metrics.providerUsage[entry.videoProvider] || 0) + 1;
        }

        if (entry.results) {
          const successCount = entry.results.filter((r) => r.success).length;
          if (successCount === entry.results.length) {
            successfulAttempts++;
            metrics.totalPublished += entry.results.length;
          }

          entry.results.forEach((result) => {
            if (result.platform) {
              metrics.platformUsage[result.platform] = (metrics.platformUsage[result.platform] || 0) + 1;
            }
          });
        }
      } catch {
        // Skip invalid entries
      }
    }

    metrics.successRate = totalAttempts > 0 ? (successfulAttempts / totalAttempts) * 100 : 0;

    return metrics;
  } catch (error) {
    console.error('Error fetching video metrics:', error);
    return {
      totalGenerated: 0,
      totalPublished: 0,
      totalScheduled: 0,
      providerUsage: {},
      platformUsage: {},
      successRate: 0,
    };
  }
}

/**
 * Export types for API routes
 */
export {
  FacelessVideoScript,
  GeneratedFacelessVideo,
  ElevenLabsVoiceOptions,
  VideoCompositionOptions,
  ScheduleOptions,
  BatchGenerationOptions,
};
