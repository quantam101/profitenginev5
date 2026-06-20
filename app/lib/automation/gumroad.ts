/**
 * GUMROAD AUTOMATION
 *
 * Automatically uploads eBooks, courses, and products to Gumroad:
 * - Read product metadata from GUMROAD_PRODUCT_*.md files
 * - Generate cover images via Unsplash/Pexels/DALL-E
 * - Upload to Gumroad via API
 * - Set pricing, description, categories, and publish
 *
 * Environment Requirements:
 * - GUMROAD_API_TOKEN: Your Gumroad API token (from account settings)
 * - GUMROAD_CREATOR_ID: Your Gumroad store username
 * - IMAGE_GENERATION_API: 'unsplash' | 'pexels' | 'dalle' | 'replicate'
 * - UNSPLASH_API_KEY (if using Unsplash)
 * - PEXELS_API_KEY (if using Pexels)
 * - OPENAI_API_KEY (if using DALL-E)
 * - REPLICATE_API_TOKEN (if using Replicate)
 */

import { readFile } from 'fs/promises';
import path from 'path';

interface ProductMetadata {
  title: string;
  description: string;
  longDescription?: string;
  price: number;
  category?: string;
  tags?: string[];
  imageUrl?: string;
  imagePrompt?: string;
  affiliateLinks?: Record<string, string>;
  contentPath?: string;
  productType: 'ebook' | 'course' | 'template' | 'tool';
}

interface GumroadProduct {
  id?: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  category?: string;
  tags?: string[];
  cover_image_url?: string;
  product_type?: string;
  requires_license?: boolean;
  license_expiration_months?: number;
  published: boolean;
}

interface GumroadUploadResult {
  success: boolean;
  productId?: string;
  productUrl?: string;
  error?: string;
  coverImageUrl?: string;
  metadata?: ProductMetadata;
}

/**
 * Generate product cover image via image generation API
 */
async function generateCoverImage(
  productTitle: string,
  imagePrompt?: string
): Promise<string> {
  const apiProvider = process.env.IMAGE_GENERATION_API || 'unsplash';

  if (apiProvider === 'unsplash') {
    return generateUnsplashImage(productTitle, imagePrompt);
  } else if (apiProvider === 'pexels') {
    return generatePexelsImage(productTitle, imagePrompt);
  } else if (apiProvider === 'dalle') {
    return generateDALLEImage(productTitle, imagePrompt);
  } else if (apiProvider === 'replicate') {
    return generateReplicateImage(productTitle, imagePrompt);
  }

  throw new Error(`Unsupported image generation API: ${apiProvider}`);
}

/**
 * Generate image via Unsplash API (free tier available)
 */
async function generateUnsplashImage(
  productTitle: string,
  imagePrompt?: string
): Promise<string> {
  const query = imagePrompt || productTitle;
  const unsplashKey = process.env.UNSPLASH_API_KEY;

  if (!unsplashKey) {
    throw new Error('UNSPLASH_API_KEY not configured');
  }

  const response = await fetch(
    `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&client_id=${unsplashKey}&per_page=1`
  );

  if (!response.ok) {
    throw new Error(`Unsplash API error: ${response.statusText}`);
  }

  const data = (await response.json()) as { results: Array<{ urls: { full: string } }> };

  if (!data.results || data.results.length === 0) {
    throw new Error(`No images found for: ${query}`);
  }

  return data.results[0].urls.full;
}

/**
 * Generate image via Pexels API (free tier available)
 */
async function generatePexelsImage(
  productTitle: string,
  imagePrompt?: string
): Promise<string> {
  const query = imagePrompt || productTitle;
  const pexelsKey = process.env.PEXELS_API_KEY;

  if (!pexelsKey) {
    throw new Error('PEXELS_API_KEY not configured');
  }

  const response = await fetch('https://api.pexels.com/v1/search', {
    headers: {
      Authorization: pexelsKey,
    },
    method: 'POST',
    body: JSON.stringify({
      query,
      per_page: 1,
    }),
  });

  if (!response.ok) {
    throw new Error(`Pexels API error: ${response.statusText}`);
  }

  const data = (await response.json()) as { photos: Array<{ src: { large: string } }> };

  if (!data.photos || data.photos.length === 0) {
    throw new Error(`No images found for: ${query}`);
  }

  return data.photos[0].src.large;
}

/**
 * Generate image via DALL-E API
 */
async function generateDALLEImage(
  productTitle: string,
  imagePrompt?: string
): Promise<string> {
  const openaiKey = process.env.OPENAI_API_KEY;

  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompt =
    imagePrompt ||
    `Professional eBook cover for: ${productTitle}. Modern design, high quality, market-ready`;

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
    throw new Error('No image generated');
  }

  return data.data[0].url;
}

/**
 * Generate image via Replicate (Stable Diffusion, FLUX, etc.)
 */
async function generateReplicateImage(
  productTitle: string,
  imagePrompt?: string
): Promise<string> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const prompt =
    imagePrompt ||
    `Professional eBook cover for: ${productTitle}. Modern design, high quality, market-ready`;

  // Create prediction
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
        aspect_ratio: '1:1',
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
  const maxAttempts = 60; // 5 minutes with 5-second intervals

  while (!prediction_data.output && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 5000)); // Wait 5 seconds
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
    throw new Error('Image generation did not complete');
  }

  return prediction_data.output[0];
}

/**
 * Parse product metadata from GUMROAD_PRODUCT_*.md file
 */
async function parseProductMetadata(filePath: string): Promise<ProductMetadata> {
  try {
    const content = await readFile(filePath, 'utf-8');

    // Extract YAML front matter
    const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);
    const metadata: ProductMetadata = {
      title: '',
      description: '',
      price: 0,
      productType: 'ebook',
    };

    if (yamlMatch) {
      const yaml = yamlMatch[1];

      // Parse YAML fields
      const titleMatch = yaml.match(/title:\s*["']?(.+?)["']?$/m);
      if (titleMatch) metadata.title = titleMatch[1];

      const descMatch = yaml.match(/description:\s*["']?(.+?)["']?$/m);
      if (descMatch) metadata.description = descMatch[1];

      const priceMatch = yaml.match(/price:\s*([\d.]+)/);
      if (priceMatch) metadata.price = parseFloat(priceMatch[1]);

      const categoryMatch = yaml.match(/category:\s*["']?(.+?)["']?$/m);
      if (categoryMatch) metadata.category = categoryMatch[1];

      const typeMatch = yaml.match(/product_type:\s*["']?(.+?)["']?$/m);
      if (typeMatch) metadata.productType = typeMatch[1] as 'ebook' | 'course' | 'template' | 'tool';

      const tagsMatch = yaml.match(/tags:\s*\[(.*?)\]/);
      if (tagsMatch) {
        metadata.tags = tagsMatch[1]
          .split(',')
          .map((tag) => tag.trim().replace(/["']/g, ''));
      }

      const imagePromptMatch = yaml.match(/image_prompt:\s*["']?(.+?)["']?$/m);
      if (imagePromptMatch) metadata.imagePrompt = imagePromptMatch[1];
    }

    // Extract content body
    const contentStart = content.indexOf('\n---\n') + 5;
    if (contentStart > 4) {
      metadata.longDescription = content.substring(contentStart).trim();
    }

    return metadata;
  } catch (error) {
    throw new Error(`Failed to parse product metadata: ${error}`);
  }
}

/**
 * Upload product to Gumroad via API
 */
async function uploadProductToGumroad(
  metadata: ProductMetadata
): Promise<GumroadUploadResult> {
  try {
    const apiToken = process.env.GUMROAD_API_TOKEN;
    const creatorId = process.env.GUMROAD_CREATOR_ID;

    if (!apiToken || !creatorId) {
      return {
        success: false,
        error: 'GUMROAD_API_TOKEN or GUMROAD_CREATOR_ID not configured',
        metadata,
      };
    }

    // Generate cover image
    let coverImageUrl: string | undefined;
    try {
      coverImageUrl = await generateCoverImage(metadata.title, metadata.imagePrompt);
      console.log(`Generated cover image: ${coverImageUrl}`);
    } catch (error) {
      console.warn(`Failed to generate cover image: ${error}`);
    }

    // Prepare Gumroad product payload
    const gumroadPayload: GumroadProduct = {
      name: metadata.title,
      description: metadata.description,
      price: metadata.price,
      currency: 'usd',
      category: metadata.category || 'book',
      tags: metadata.tags || [],
      cover_image_url: coverImageUrl,
      product_type: metadata.productType,
      requires_license: false,
      published: true,
    };

    // Create or update product via Gumroad API
    const response = await fetch(`https://api.gumroad.com/v2/products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        access_token: apiToken,
        name: gumroadPayload.name,
        description: gumroadPayload.description,
        price: gumroadPayload.price.toString(),
        currency: gumroadPayload.currency,
        category: gumroadPayload.category || 'book',
        tags: (gumroadPayload.tags || []).join(','),
        ...(coverImageUrl && { cover_image_url: coverImageUrl }),
        published: 'true',
      }).toString(),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        success: false,
        error: `Gumroad API error: ${error}`,
        metadata,
      };
    }

    const data = (await response.json()) as {
      product: { id: string; url: string };
    };

    return {
      success: true,
      productId: data.product.id,
      productUrl: data.product.url,
      coverImageUrl,
      metadata,
    };
  } catch (error) {
    return {
      success: false,
      error: `Upload failed: ${error}`,
      metadata,
    };
  }
}

/**
 * Main orchestration function: Find all GUMROAD_PRODUCT_*.md files and upload
 */
export async function orchestrateGumroadUpload(): Promise<GumroadUploadResult[]> {
  const results: GumroadUploadResult[] = [];

  try {
    // Find all GUMROAD_PRODUCT_*.md files in project root
    const fs = await import('fs/promises');
    const files = await fs.readdir('.');

    const productFiles = files.filter((f) => f.match(/^GUMROAD_PRODUCT_.*\.md$/i));

    if (productFiles.length === 0) {
      console.log('No GUMROAD_PRODUCT_*.md files found');
      return results;
    }

    for (const file of productFiles) {
      console.log(`Processing: ${file}`);

      try {
        // Parse metadata
        const metadata = await parseProductMetadata(file);

        // Upload to Gumroad
        const result = await uploadProductToGumroad(metadata);
        results.push(result);

        if (result.success) {
          console.log(`✓ Uploaded: ${metadata.title} → ${result.productUrl}`);
        } else {
          console.error(`✗ Failed: ${metadata.title} - ${result.error}`);
        }
      } catch (error) {
        results.push({
          success: false,
          error: `Processing failed: ${error}`,
        });
      }
    }

    return results;
  } catch (error) {
    console.error(`Gumroad orchestration failed: ${error}`);
    return results;
  }
}

export { ProductMetadata, GumroadProduct, GumroadUploadResult };
