/**
 * INSTAGRAM CAROUSEL AUTOMATION
 *
 * Automatically generates and posts Instagram carousels:
 * - Read carousel slide descriptions from INSTAGRAM_CAROUSEL_DESIGNS.md
 * - Generate 7 carousel images via DALL-E, Midjourney, or Replicate
 * - Upload carousel to Instagram via Meta Graph API
 * - Auto-schedule posting (Tue 9 AM, Thu 2 PM, Sat 9 AM ET)
 *
 * Environment Requirements:
 * - IG_USER_ID: Instagram business account ID
 * - FB_PAGE_ACCESS_TOKEN: Meta Graph API access token
 * - IMAGE_GENERATION_API: 'dalle' | 'midjourney' | 'replicate'
 * - OPENAI_API_KEY (if using DALL-E)
 * - MIDJOURNEY_API_KEY (if using Midjourney)
 * - REPLICATE_API_TOKEN (if using Replicate)
 */

import { readFile } from 'fs/promises';

interface CarouselSlide {
  slideNumber: number;
  title?: string;
  description: string;
  imagePrompt?: string;
  cta?: string;
  hashtags?: string[];
}

interface CarouselDesign {
  title: string;
  description: string;
  slides: CarouselSlide[];
  postCaption?: string;
  ctaLink?: string;
  scheduleTime?: string; // ISO 8601 format
  hashtags?: string[];
}

interface GeneratedSlideImage {
  slideNumber: number;
  imageUrl: string;
  prompt: string;
  generatedAt: string;
}

interface InstagramCarouselResult {
  success: boolean;
  postId?: string;
  postUrl?: string;
  scheduledTime?: string;
  generatedImages?: GeneratedSlideImage[];
  error?: string;
  carouselTitle?: string;
}

/**
 * Generate slide image via DALL-E
 */
async function generateDALLESlideImage(
  slideNumber: number,
  description: string,
  imagePrompt?: string
): Promise<string> {
  const openaiKey = process.env.OPENAI_API_KEY;

  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompt =
    imagePrompt ||
    `Instagram carousel slide ${slideNumber}: ${description}. Modern, visually engaging, professional design. Optimized for social media (1080x1350px vertical ratio)`;

  const response = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${openaiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      n: 1,
      size: '1024x1024',
      quality: 'hd',
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`DALL-E API error: ${error}`);
  }

  const data = (await response.json()) as { data: Array<{ url: string }> };

  if (!data.data || data.data.length === 0) {
    throw new Error(`No image generated for slide ${slideNumber}`);
  }

  return data.data[0].url;
}

/**
 * Generate slide image via Midjourney API
 */
async function generateMidjourneySlideImage(
  slideNumber: number,
  description: string,
  imagePrompt?: string
): Promise<string> {
  const midjourneyKey = process.env.MIDJOURNEY_API_KEY;

  if (!midjourneyKey) {
    throw new Error('MIDJOURNEY_API_KEY not configured');
  }

  const prompt =
    imagePrompt ||
    `Instagram carousel slide ${slideNumber}: ${description}. Modern, visually engaging, professional design. 1080x1350px vertical ratio`;

  const response = await fetch('https://api.midjourney.com/v1/imagine', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${midjourneyKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      aspect_ratio: '9:11', // Instagram carousel optimal ratio
      quality: 'high',
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Midjourney API error: ${error}`);
  }

  const data = (await response.json()) as { image_url: string };
  return data.image_url;
}

/**
 * Generate slide image via Replicate
 */
async function generateReplicateSlideImage(
  slideNumber: number,
  description: string,
  imagePrompt?: string
): Promise<string> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const prompt =
    imagePrompt ||
    `Instagram carousel slide ${slideNumber}: ${description}. Modern, visually engaging, professional design`;

  const createResponse = await fetch('https://api.replicate.com/v1/predictions', {
    method: 'POST',
    headers: {
      Authorization: `Token ${replicateToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      version: 'e16e6b96924477906061c6ba27cb8583e4eda351516d365bfed359f94e2e214e', // FLUX model
      input: {
        prompt,
        aspect_ratio: '9:11',
        output_format: 'webp',
      },
    }),
  });

  if (!createResponse.ok) {
    const error = await createResponse.text();
    throw new Error(`Replicate API error: ${error}`);
  }

  const prediction = (await createResponse.json()) as { id: string; output?: string[] };

  // Poll for completion
  let prediction_data = prediction;
  let attempts = 0;
  const maxAttempts = 60;

  while (!prediction_data.output && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 5000));
    const pollResponse = await fetch(
      `https://api.replicate.com/v1/predictions/${prediction_data.id}`,
      {
        headers: {
          Authorization: `Token ${replicateToken}`,
        },
      }
    );

    if (pollResponse.ok) {
      prediction_data = (await pollResponse.json()) as { id: string; output?: string[] };
    }

    attempts++;
  }

  if (!prediction_data.output || prediction_data.output.length === 0) {
    throw new Error(`Image generation failed for slide ${slideNumber}`);
  }

  return prediction_data.output[0];
}

/**
 * Generate all carousel slide images in parallel
 */
async function generateCarouselImages(carousel: CarouselDesign): Promise<GeneratedSlideImage[]> {
  const apiProvider = process.env.IMAGE_GENERATION_API || 'dalle';
  const generationFn =
    apiProvider === 'dalle'
      ? generateDALLESlideImage
      : apiProvider === 'midjourney'
        ? generateMidjourneySlideImage
        : generateReplicateSlideImage;

  const imagePromises = carousel.slides.map((slide) =>
    generationFn(slide.slideNumber, slide.description, slide.imagePrompt)
      .then((imageUrl) => ({
        slideNumber: slide.slideNumber,
        imageUrl,
        prompt: slide.imagePrompt || slide.description,
        generatedAt: new Date().toISOString(),
      }))
      .catch((error) => {
        throw new Error(`Slide ${slide.slideNumber} generation failed: ${error}`);
      })
  );

  return Promise.all(imagePromises);
}

/**
 * Upload carousel to Instagram via Meta Graph API
 */
async function uploadCarouselToInstagram(
  carousel: CarouselDesign,
  generatedImages: GeneratedSlideImage[]
): Promise<InstagramCarouselResult> {
  try {
    const igUserId = process.env.IG_USER_ID;
    const accessToken = process.env.FB_PAGE_ACCESS_TOKEN;

    if (!igUserId || !accessToken) {
      return {
        success: false,
        error: 'IG_USER_ID or FB_PAGE_ACCESS_TOKEN not configured',
        carouselTitle: carousel.title,
      };
    }

    // Upload images to Instagram and create carousel
    const containerResponse = await fetch(
      `https://graph.instagram.com/v18.0/${igUserId}/media`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          media_type: 'CAROUSEL',
          children: generatedImages.map((img) => ({
            media_type: 'IMAGE',
            image_url: img.imageUrl,
          })),
          caption:
            carousel.postCaption ||
            `${carousel.title}\n\n${carousel.slides.map((s) => `• ${s.title || `Slide ${s.slideNumber}`}: ${s.description}`).join('\n')}\n\n${carousel.hashtags?.join(' ') || '#trading #forex #crypto'}`,
          access_token: accessToken,
        }),
      }
    );

    if (!containerResponse.ok) {
      const error = await containerResponse.text();
      return {
        success: false,
        error: `Instagram API error: ${error}`,
        carouselTitle: carousel.title,
      };
    }

    const containerData = (await containerResponse.json()) as { id: string };

    // Publish the carousel
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
        carouselTitle: carousel.title,
      };
    }

    const publishData = (await publishResponse.json()) as { id: string };

    return {
      success: true,
      postId: publishData.id,
      postUrl: `https://instagram.com/p/${publishData.id}`,
      generatedImages,
      carouselTitle: carousel.title,
    };
  } catch (error) {
    return {
      success: false,
      error: `Carousel upload failed: ${error}`,
      carouselTitle: carousel.title,
    };
  }
}

/**
 * Calculate next scheduled post time (Tue 9 AM, Thu 2 PM, Sat 9 AM ET)
 */
function getNextScheduledTime(): Date {
  const now = new Date();
  const schedules = [
    { day: 2, hour: 13, min: 0 }, // Tuesday 9 AM ET (13 UTC)
    { day: 4, hour: 18, min: 0 }, // Thursday 2 PM ET (18 UTC)
    { day: 6, hour: 13, min: 0 }, // Saturday 9 AM ET (13 UTC)
  ];

  const currentDay = now.getUTCDay();
  const currentHour = now.getUTCHours();

  for (const schedule of schedules) {
    if (schedule.day > currentDay || (schedule.day === currentDay && schedule.hour > currentHour)) {
      const next = new Date(now);
      next.setUTCDate(next.getUTCDate() + (schedule.day - currentDay));
      next.setUTCHours(schedule.hour, schedule.min, 0, 0);
      return next;
    }
  }

  // If no schedule found this week, use first schedule of next week
  const next = new Date(now);
  next.setUTCDate(next.getUTCDate() + (2 - currentDay + 7) % 7 || 7); // Next Tuesday
  next.setUTCHours(13, 0, 0, 0);
  return next;
}

/**
 * Parse carousel design from INSTAGRAM_CAROUSEL_DESIGNS.md
 */
async function parseCarouselDesign(filePath: string): Promise<CarouselDesign> {
  try {
    const content = await readFile(filePath, 'utf-8');

    const carousel: CarouselDesign = {
      title: '',
      description: '',
      slides: [],
    };

    // Extract title
    const titleMatch = content.match(/# (.+?)$/m);
    if (titleMatch) carousel.title = titleMatch[1];

    // Extract description
    const descMatch = content.match(/^## Description\n\n(.+?)$/m);
    if (descMatch) carousel.description = descMatch[1];

    // Extract hashtags
    const hashtagMatch = content.match(/^## Hashtags\n\n(.+?)$/m);
    if (hashtagMatch) {
      carousel.hashtags = hashtagMatch[1]
        .split(/[\s,#]+/)
        .filter((h) => h.trim());
    }

    // Extract CTA
    const ctaMatch = content.match(/^## CTA\n\n(.+?)$/m);
    if (ctaMatch) carousel.postCaption = ctaMatch[1];

    // Extract slides
    const slideMatches = content.matchAll(/### Slide (\d+)\n\n(.+?)(?=###|$)/gms);
    for (const match of slideMatches) {
      const slideNumber = parseInt(match[1], 10);
      const slideContent = match[2];

      const titleMatch = slideContent.match(/^Title: (.+?)$/m);
      const descriptionMatch = slideContent.match(/^Description: (.+?)$/m);
      const imagePromptMatch = slideContent.match(/^Image Prompt: (.+?)$/m);
      const ctaMatch = slideContent.match(/^CTA: (.+?)$/m);

      carousel.slides.push({
        slideNumber,
        title: titleMatch ? titleMatch[1] : undefined,
        description: descriptionMatch ? descriptionMatch[1] : slideContent.split('\n')[0],
        imagePrompt: imagePromptMatch ? imagePromptMatch[1] : undefined,
        cta: ctaMatch ? ctaMatch[1] : undefined,
      });
    }

    return carousel;
  } catch (error) {
    throw new Error(`Failed to parse carousel design: ${error}`);
  }
}

/**
 * Main orchestration function: Generate and post Instagram carousel
 */
export async function generateAndPostCarousel(
  carouselFile: string = 'INSTAGRAM_CAROUSEL_DESIGNS.md'
): Promise<InstagramCarouselResult> {
  try {
    // Parse carousel design
    console.log(`Parsing carousel: ${carouselFile}`);
    const carousel = await parseCarouselDesign(carouselFile);

    // Generate all slide images
    console.log(`Generating ${carousel.slides.length} carousel images...`);
    const generatedImages = await generateCarouselImages(carousel);
    console.log(`Generated ${generatedImages.length} images`);

    // Upload carousel to Instagram
    console.log(`Uploading carousel to Instagram...`);
    const result = await uploadCarouselToInstagram(carousel, generatedImages);

    if (result.success) {
      console.log(`✓ Carousel posted: ${result.postUrl}`);
    } else {
      console.error(`✗ Carousel upload failed: ${result.error}`);
    }

    return result;
  } catch (error) {
    return {
      success: false,
      error: `Carousel orchestration failed: ${error}`,
    };
  }
}

export { CarouselDesign, CarouselSlide, GeneratedSlideImage, InstagramCarouselResult };
