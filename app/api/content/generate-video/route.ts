/**
 * Content Generation API — Faceless Avatar Video Production
 *
 * Generates short-form videos for TikTok, Instagram Reels, YouTube Shorts
 * Uses the underlying Python video engine (video_engine.py) for production
 *
 * POST /api/content/generate-video
 * {
 *   "title": "How to Make $25K/Month",
 *   "body": "Here's the 4-stream business model...",
 *   "platforms": ["tiktok", "instagram", "youtube"]
 * }
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { title, body, platforms = ['tiktok', 'instagram', 'youtube'] } = body;

    if (!title || !body) {
      return NextResponse.json(
        { error: 'Missing title or body' },
        { status: 400 }
      );
    }

    // Call Python video engine endpoint
    const videoResponse = await fetch('http://localhost:8000/api/v1/video/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        body,
        output_format: '9:16', // Vertical for social media
        include_subtitles: true,
        include_audio: true,
      }),
    });

    if (!videoResponse.ok) {
      throw new Error(`Video generation failed: ${videoResponse.statusText}`);
    }

    const videoData = await videoResponse.json();

    // Post to configured social platforms
    const postResults = await Promise.allSettled(
      platforms.map(platform => postToSocialMedia(platform, videoData, title))
    );

    return NextResponse.json({
      status: 'success',
      video: videoData,
      posts: postResults.map(r =>
        r.status === 'fulfilled' ? r.value : { error: (r as PromiseRejectedResult).reason }
      ),
    });
  } catch (error) {
    console.error('Video generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate video', details: String(error) },
      { status: 500 }
    );
  }
}

/**
 * Post video to social media platform
 * Integrates with TikTok, Instagram, YouTube, Twitter, LinkedIn APIs
 */
async function postToSocialMedia(
  platform: string,
  videoData: { video_path: string; title: string; description: string },
  title: string
) {
  const socialConfig = {
    tiktok: {
      apiEndpoint: 'https://open.tiktokapis.com/v1/video/upload/',
      accessToken: process.env.TIKTOK_ACCESS_TOKEN,
    },
    instagram: {
      apiEndpoint: 'https://graph.instagram.com/v18.0/me/media',
      accessToken: process.env.INSTAGRAM_ACCESS_TOKEN,
    },
    youtube: {
      apiEndpoint: 'https://www.googleapis.com/youtube/v3/videos',
      accessToken: process.env.YOUTUBE_ACCESS_TOKEN,
    },
    twitter: {
      apiEndpoint: 'https://api.twitter.com/2/tweets',
      accessToken: process.env.TWITTER_ACCESS_TOKEN,
    },
    linkedin: {
      apiEndpoint: 'https://api.linkedin.com/v2/ugcPosts',
      accessToken: process.env.LINKEDIN_ACCESS_TOKEN,
    },
  };

  const config = socialConfig[platform as keyof typeof socialConfig];
  if (!config || !config.accessToken) {
    throw new Error(`No configuration for platform: ${platform}`);
  }

  // Platform-specific posting logic
  switch (platform) {
    case 'tiktok':
      return postToTikTok(videoData, config);
    case 'instagram':
      return postToInstagram(videoData, config);
    case 'youtube':
      return postToYouTube(videoData, config);
    case 'twitter':
      return postToTwitter(videoData, config);
    case 'linkedin':
      return postToLinkedIn(videoData, config);
    default:
      throw new Error(`Unsupported platform: ${platform}`);
  }
}

async function postToTikTok(
  videoData: any,
  config: { apiEndpoint: string; accessToken: string }
) {
  const formData = new FormData();
  const videoFile = await fetch(videoData.video_path).then(r => r.blob());

  formData.append('video', videoFile);
  formData.append('source', 'CREATOR_STUDIO');
  formData.append('post_mode', 'DRAFT');
  formData.append('text', videoData.title);

  const response = await fetch(config.apiEndpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.accessToken}`,
    },
    body: formData,
  });

  return response.json();
}

async function postToInstagram(
  videoData: any,
  config: { apiEndpoint: string; accessToken: string }
) {
  const response = await fetch(config.apiEndpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      media_type: 'REELS',
      video_url: videoData.video_path,
      caption: videoData.title,
    }),
  });

  return response.json();
}

async function postToYouTube(
  videoData: any,
  config: { apiEndpoint: string; accessToken: string }
) {
  const response = await fetch(config.apiEndpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      snippet: {
        title: videoData.title,
        description: videoData.description,
        categoryId: '28', // Science & Tech
      },
      status: {
        privacyStatus: 'public',
      },
    }),
  });

  return response.json();
}

async function postToTwitter(
  videoData: any,
  config: { apiEndpoint: string; accessToken: string }
) {
  const response = await fetch(config.apiEndpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: videoData.title,
      media: {
        media_ids: [videoData.media_id],
      },
    }),
  });

  return response.json();
}

async function postToLinkedIn(
  videoData: any,
  config: { apiEndpoint: string; accessToken: string }
) {
  const response = await fetch(config.apiEndpoint, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      specificContent: {
        'com.linkedin.ugc:ShareContent': {
          shareCommentary: {
            text: videoData.title,
          },
          shareMediaCategory: 'VIDEO',
          media: [
            {
              status: 'READY',
              media: videoData.linkedin_asset_id,
            },
          ],
        },
      },
      visibility: {
        'com.linkedin.ugc:ShareAudienceType': 'PUBLIC',
      },
    }),
  });

  return response.json();
}
