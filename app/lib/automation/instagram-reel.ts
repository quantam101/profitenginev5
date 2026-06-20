/**
 * INSTAGRAM REEL AUTOMATION
 *
 * Automatically generates and posts Instagram reels:
 * - Read reel scripts from CONTENT_CALENDAR_MONTHLY.md
 * - Generate 60-second video via Synthesia.io, D-ID, Replicate, or ElevenLabs
 * - Add voiceover, text overlays, background music
 * - Upload to Instagram via Meta Graph API
 * - Auto-schedule posting
 *
 * Environment Requirements:
 * - IG_USER_ID: Instagram business account ID
 * - FB_PAGE_ACCESS_TOKEN: Meta Graph API access token
 * - VIDEO_GENERATION_API: 'synthesia' | 'd-id' | 'replicate' | 'elevenlabs'
 * - SYNTHESIA_API_KEY (if using Synthesia)
 * - DID_API_KEY (if using D-ID)
 * - REPLICATE_API_TOKEN (if using Replicate)
 * - ELEVENLABS_API_KEY (if using ElevenLabs)
 */

import { readFile } from 'fs/promises';

interface ReelScript {
  title: string;
  hook: string;
  mainPoints: string[];
  cta: string;
  affiliateLinks?: Record<string, string>;
  duration: number; // seconds
  voicePrompt?: string;
  backgroundMusic?: string;
  textOverlays?: string[];
}

interface GeneratedReel {
  videoUrl: string;
  thumbnail?: string;
  duration: number;
  script: ReelScript;
  generatedAt: string;
}

interface InstagramReelResult {
  success: boolean;
  postId?: string;
  postUrl?: string;
  scheduledTime?: string;
  videoUrl?: string;
  error?: string;
  script?: ReelScript;
}

/**
 * Generate video via Synthesia.io API
 */
async function generateSynthesiaVideo(script: ReelScript): Promise<string> {
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
      description: `Trading insight: ${script.title}`,
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
      callbackUrl: `${process.env.RUNTIME_API_URL}/api/webhooks/video-ready`,
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Synthesia API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string };

  // Poll for completion (async, may need webhook)
  return `https://synthesia.io/videos/${data.id}`;
}

/**
 * Generate video via D-ID API (avatar video generation)
 */
async function generateDIDVideo(script: ReelScript): Promise<string> {
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
      webhook_url: `${process.env.RUNTIME_API_URL}/api/webhooks/video-ready`,
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`D-ID API error: ${error}`);
  }

  const data = (await createResponse.json()) as { id: string };
  return `https://d-id.com/videos/${data.id}`;
}

/**
 * Generate video via Replicate (Cog video generation models)
 */
async function generateReplicateVideo(script: ReelScript): Promise<string> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  // First, generate voiceover via ElevenLabs through Replicate
  const voiceResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: 'e995f61bf6dc5bb2db36670b1abc4eb988f9d569e0696b9f5e29ff37773f5d2b', // Text-to-speech
      input: {
        text: voiceScript,
        voice_id: 'EXAVITQu4vr4xnSDxMaL',
      },
    }),
  });

  if (!voiceResponse.ok) {
    throw new Error(`ElevenLabs voice generation failed: ${await voiceResponse.text()}`);
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

  // Then, generate video with voiceover
  const videoResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: '4fe07e23faffc7af3c24cbf1234c9c86c7b3c135498c9b1a3d19e122d9b51670', // Video generation
      input: {
        audio_url: voiceData.output,
        frames: 60,
        fps: 30,
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

  return videoData.output;
}

/**
 * Generate video via ElevenLabs (simple voiceover generation)
 */
async function generateElevenLabsVoiceover(script: ReelScript): Promise<string> {
  const elevenLabsKey = process.env.ELEVENLABS_API_KEY;

  if (!elevenLabsKey) {
    throw new Error('ELEVENLABS_API_KEY not configured');
  }

  const voiceScript =
    script.voicePrompt ||
    `${script.hook} ${script.mainPoints.join(' ')} ${script.cta}`;

  const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL', {
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
  });

  if (!response.ok) {
    throw new Error(`ElevenLabs API error: ${await response.text()}`);
  }

  // Store as temporary audio file
  const buffer = await response.arrayBuffer();
  const audioUrl = `data:audio/mpeg;base64,${Buffer.from(buffer).toString('base64')}`;

  return audioUrl;
}

/**
 * Parse reel script from CONTENT_CALENDAR_MONTHLY.md
 */
async function parseReelScript(
  contentFile: string = 'CONTENT_CALENDAR_MONTHLY.md',
  postNumber: number = 1
): Promise<ReelScript> {
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
    const script: ReelScript = {
      title: '',
      hook: '',
      mainPoints: [],
      cta: '',
      duration: 60,
    };

    // Extract title
    const titleMatch = postContent.match(/### Post \d+: "(.+?)"/);
    if (titleMatch) script.title = titleMatch[1];

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
    throw new Error(`Failed to parse reel script: ${error}`);
  }
}

/**
 * Upload reel to Instagram via Meta Graph API
 */
async function uploadReelToInstagram(
  videoUrl: string,
  script: ReelScript
): Promise<InstagramReelResult> {
  try {
    const igUserId = process.env.IG_USER_ID;
    const accessToken = process.env.FB_PAGE_ACCESS_TOKEN;

    if (!igUserId || !accessToken) {
      return {
        success: false,
        error: 'IG_USER_ID or FB_PAGE_ACCESS_TOKEN not configured',
        script,
      };
    }

    // Create media container for reel
    const containerResponse = await fetch(
      `https://graph.instagram.com/v18.0/${igUserId}/media`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          media_type: 'REELS',
          video_url: videoUrl,
          caption: `${script.title}\n\n${script.hook}\n\n${script.cta}\n\n${
            script.affiliateLinks
              ? Object.entries(script.affiliateLinks)
                  .map(([name, url]) => `${name}: ${url}`)
                  .join('\n')
              : ''
          }\n\n#trading #forex #crypto #profitengine`,
          access_token: accessToken,
        }),
      }
    );

    if (!containerResponse.ok) {
      const error = await containerResponse.text();
      return {
        success: false,
        error: `Instagram API error: ${error}`,
        script,
      };
    }

    const containerData = (await containerResponse.json()) as { id: string };

    // Publish the reel
    const publishResponse = await fetch(
      `https://graph.instagram.com/v18.0/${igUserId}/media_publish`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          creation_id: containerData.id,
          access_token: accessToken,
        }),
      }
    );

    if (!publishResponse.ok) {
      const error = await publishResponse.text();
      return {
        success: false,
        error: `Instagram publish failed: ${error}`,
        script,
      };
    }

    const publishData = (await publishResponse.json()) as { id: string };

    return {
      success: true,
      postId: publishData.id,
      postUrl: `https://instagram.com/reels/${publishData.id}`,
      videoUrl,
      script,
    };
  } catch (error) {
    return {
      success: false,
      error: `Reel upload failed: ${error}`,
      script,
    };
  }
}

/**
 * Main orchestration function: Generate and post Instagram reel
 */
export async function generateAndPostReel(postNumber: number = 1): Promise<InstagramReelResult> {
  try {
    // Parse reel script from content calendar
    console.log(`Parsing reel script: Post ${postNumber}`);
    const script = await parseReelScript('CONTENT_CALENDAR_MONTHLY.md', postNumber);

    // Generate video
    console.log(`Generating 60-second reel for: ${script.title}`);
    const videoProvider = process.env.VIDEO_GENERATION_API || 'synthesia';
    let videoUrl: string;

    if (videoProvider === 'synthesia') {
      videoUrl = await generateSynthesiaVideo(script);
    } else if (videoProvider === 'd-id') {
      videoUrl = await generateDIDVideo(script);
    } else if (videoProvider === 'elevenlabs') {
      videoUrl = await generateElevenLabsVoiceover(script);
    } else {
      videoUrl = await generateReplicateVideo(script);
    }

    console.log(`Generated video: ${videoUrl}`);

    // Upload to Instagram
    console.log(`Uploading reel to Instagram...`);
    const result = await uploadReelToInstagram(videoUrl, script);

    if (result.success) {
      console.log(`✓ Reel posted: ${result.postUrl}`);
    } else {
      console.error(`✗ Reel upload failed: ${result.error}`);
    }

    return result;
  } catch (error) {
    return {
      success: false,
      error: `Reel orchestration failed: ${error}`,
    };
  }
}

export { ReelScript, GeneratedReel, InstagramReelResult };
