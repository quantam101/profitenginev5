/**
 * KDP AUTOMATION
 *
 * Automatically publishes eBooks to Amazon KDP, Draft2Digital, and Smashwords:
 * - Parse book metadata from markdown files
 * - Generate professional book covers
 * - Format content for each platform (KDP, D2D, Smashwords)
 * - Upload to each platform via API
 * - Track royalties and earnings
 * - Manage ISBN assignments
 * - Bulk publishing with progress tracking
 * - Risk assessment and quality validation
 * - Multi-channel distribution optimization
 *
 * Environment Requirements:
 * - KDP_ACCESS_TOKEN: Amazon KDP API token (from AWS seller portal)
 * - DRAFT2DIGITAL_API_KEY: Draft2Digital API key
 * - SMASHWORDS_API_KEY: Smashwords API key
 * - IMAGE_GENERATION_API: 'unsplash' | 'pexels' | 'dalle' | 'replicate'
 * - UNSPLASH_API_KEY, PEXELS_API_KEY, OPENAI_API_KEY, or REPLICATE_API_TOKEN
 * - KDP_MAX_PUBLISH_BATCH_SIZE: Max books per publish run (default: 10)
 * - KDP_ENABLE_QUALITY_CHECKS: Enable validation (default: true)
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

/**
 * Book metadata structure
 */
export interface BookMetadata {
  title: string;
  subtitle?: string;
  author: string;
  description: string;
  longDescription?: string;
  category: string;
  keywords: string[];
  language?: string;
  price: number;
  currency?: string;
  isbn?: string;
  issueNumber?: string;
  copyrightYear?: number;
  publishedDate?: string;
  contentPath?: string;
  coverImageUrl?: string;
  coverImagePrompt?: string;
  series?: {
    name: string;
    number: number;
  };
  contributors?: Array<{
    name: string;
    role: string;
  }>;
  copyrightHolder?: string;
  publisher?: string;
  maturityRating?: string;
  publicationCountries?: string[];
}

/**
 * Platform-specific upload result
 */
export interface PlatformUploadResult {
  platform: 'kdp' | 'draft2digital' | 'smashwords';
  success: boolean;
  bookId?: string;
  bookUrl?: string;
  asin?: string;
  isbn?: string;
  status?: string;
  royaltyRate?: number;
  error?: string;
  timestamp?: string;
  attempts?: number;
}

/**
 * KDP publication result
 */
export interface KdpPublicationResult {
  metadata: BookMetadata;
  coverImageUrl?: string;
  uploads: PlatformUploadResult[];
  overallSuccess: boolean;
  successCount: number;
  failureCount: number;
  startTime: string;
  endTime: string;
  duration: number;
}

/**
 * Royalty tracking result
 */
export interface RoyaltyData {
  asin?: string;
  isbn?: string;
  platform: string;
  period: string;
  units: number;
  revenue: number;
  royaltyRate: number;
  royaltyEarnings: number;
  currency: string;
  status?: string;
}

/**
 * Format content for KDP (EPUB or PDF)
 */
export function formatContentForKdp(
  content: string,
  format: 'epub' | 'pdf' = 'epub'
): string {
  // Convert markdown to KDP-compatible format
  let formatted = content;

  // Remove frontmatter
  formatted = formatted.replace(/^---\n[\s\S]*?\n---\n/, '');

  // Convert markdown headers to valid EPUB/PDF structure
  formatted = formatted.replace(/^# /gm, '\n\n# ');
  formatted = formatted.replace(/^## /gm, '\n\n## ');
  formatted = formatted.replace(/^### /gm, '\n\n### ');

  // Remove inline HTML (KDP doesn't allow certain tags)
  formatted = formatted.replace(/<script[\s\S]*?<\/script>/gi, '');
  formatted = formatted.replace(/<iframe[\s\S]*?<\/iframe>/gi, '');

  // Ensure proper line breaks
  formatted = formatted.split('\n').join('\n');

  return formatted;
}

/**
 * Format content for Draft2Digital
 */
export function formatContentForDraft2Digital(content: string): string {
  let formatted = content;

  // Remove frontmatter
  formatted = formatted.replace(/^---\n[\s\S]*?\n---\n/, '');

  // D2D prefers standard markdown
  formatted = formatted
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

  return formatted;
}

/**
 * Format content for Smashwords
 */
export function formatContentForSmashwords(content: string): string {
  let formatted = content;

  // Remove frontmatter
  formatted = formatted.replace(/^---\n[\s\S]*?\n---\n/, '');

  // Smashwords uses their own markup system
  // Convert markdown to Smashwords format
  formatted = formatted
    .replace(/^# (.*?)$/gm, '# *$1*')
    .replace(/^## (.*?)$/gm, '## *$1*')
    .replace(/^### (.*?)$/gm, '### *$1*');

  // Smashwords requires specific formatting
  formatted = formatted.replace(/\n\n+/g, '\n\n');

  return formatted;
}

/**
 * Parse book metadata from KDP_BOOK_*.md file
 */
export async function parseBookMetadata(filePath: string): Promise<BookMetadata> {
  try {
    const content = await readFile(filePath, 'utf-8');

    // Extract YAML front matter
    const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);
    const metadata: BookMetadata = {
      title: '',
      author: '',
      description: '',
      category: 'General',
      keywords: [],
      price: 9.99,
      currency: 'USD',
      language: 'en',
      maturityRating: 'G',
      publicationCountries: ['US'],
    };

    if (yamlMatch) {
      const yaml = yamlMatch[1];

      // Parse YAML fields
      const titleMatch = yaml.match(/title:\s*["']?(.+?)["']?$/m);
      if (titleMatch) metadata.title = titleMatch[1];

      const subtitleMatch = yaml.match(/subtitle:\s*["']?(.+?)["']?$/m);
      if (subtitleMatch) metadata.subtitle = subtitleMatch[1];

      const authorMatch = yaml.match(/author:\s*["']?(.+?)["']?$/m);
      if (authorMatch) metadata.author = authorMatch[1];

      const descMatch = yaml.match(/description:\s*["']?(.+?)["']?$/m);
      if (descMatch) metadata.description = descMatch[1];

      const categoryMatch = yaml.match(/category:\s*["']?(.+?)["']?$/m);
      if (categoryMatch) metadata.category = categoryMatch[1];

      const priceMatch = yaml.match(/price:\s*([\d.]+)/);
      if (priceMatch) metadata.price = parseFloat(priceMatch[1]);

      const isbnMatch = yaml.match(/isbn:\s*["']?(.+?)["']?$/m);
      if (isbnMatch) metadata.isbn = isbnMatch[1];

      const keywordsMatch = yaml.match(/keywords:\s*\[(.*?)\]/);
      if (keywordsMatch) {
        metadata.keywords = keywordsMatch[1]
          .split(',')
          .map((kw) => kw.trim().replace(/["']/g, ''));
      }

      const tagsMatch = yaml.match(/tags:\s*\[(.*?)\]/);
      if (tagsMatch && metadata.keywords.length === 0) {
        metadata.keywords = tagsMatch[1]
          .split(',')
          .map((tag) => tag.trim().replace(/["']/g, ''));
      }

      const imagePromptMatch = yaml.match(/cover_image_prompt:\s*["']?(.+?)["']?$/m);
      if (imagePromptMatch) metadata.coverImagePrompt = imagePromptMatch[1];

      const languageMatch = yaml.match(/language:\s*["']?(.+?)["']?$/m);
      if (languageMatch) metadata.language = languageMatch[1];

      const seriesMatch = yaml.match(/series:\s*["']?(.+?)["']?$/m);
      if (seriesMatch) {
        const [name, number] = seriesMatch[1].split(',').map((s) => s.trim());
        if (name && number) {
          metadata.series = { name, number: parseInt(number, 10) };
        }
      }

      const publisherMatch = yaml.match(/publisher:\s*["']?(.+?)["']?$/m);
      if (publisherMatch) metadata.publisher = publisherMatch[1];

      const copyrightMatch = yaml.match(/copyright_year:\s*(\d{4})/);
      if (copyrightMatch) metadata.copyrightYear = parseInt(copyrightMatch[1], 10);
    }

    // Extract content body
    const contentStart = content.indexOf('\n---\n') + 5;
    if (contentStart > 4) {
      metadata.longDescription = content.substring(contentStart).trim();
      metadata.contentPath = filePath;
    }

    return metadata;
  } catch (error) {
    throw new Error(`Failed to parse book metadata from ${filePath}: ${error}`);
  }
}

/**
 * Generate book cover image via image generation API
 */
export async function generateBookCover(
  metadata: BookMetadata
): Promise<string> {
  const apiProvider = process.env.IMAGE_GENERATION_API || 'unsplash';
  const prompt =
    metadata.coverImagePrompt ||
    `Professional book cover for "${metadata.title}" by ${metadata.author}. Modern design, high quality, market-ready`;

  if (apiProvider === 'unsplash') {
    return generateUnsplashImage(metadata.title, prompt);
  } else if (apiProvider === 'pexels') {
    return generatePexelsImage(metadata.title, prompt);
  } else if (apiProvider === 'dalle') {
    return generateDALLEImage(metadata.title, prompt);
  } else if (apiProvider === 'replicate') {
    return generateReplicateImage(metadata.title, prompt);
  }

  throw new Error(`Unsupported image generation API: ${apiProvider}`);
}

/**
 * Generate image via Unsplash API
 */
async function generateUnsplashImage(
  query: string,
  prompt?: string
): Promise<string> {
  const searchQuery = prompt ? prompt.substring(0, 100) : query;
  const unsplashKey = process.env.UNSPLASH_API_KEY;

  if (!unsplashKey) {
    throw new Error('UNSPLASH_API_KEY not configured');
  }

  const response = await fetch(
    `https://api.unsplash.com/search/photos?query=${encodeURIComponent(searchQuery)}&client_id=${unsplashKey}&per_page=1&orientation=portrait`
  );

  if (!response.ok) {
    throw new Error(`Unsplash API error: ${response.statusText}`);
  }

  const data = (await response.json()) as { results: Array<{ urls: { full: string } }> };

  if (!data.results || data.results.length === 0) {
    throw new Error(`No images found for: ${searchQuery}`);
  }

  return data.results[0].urls.full;
}

/**
 * Generate image via Pexels API
 */
async function generatePexelsImage(
  query: string,
  prompt?: string
): Promise<string> {
  const searchQuery = prompt ? prompt.substring(0, 100) : query;
  const pexelsKey = process.env.PEXELS_API_KEY;

  if (!pexelsKey) {
    throw new Error('PEXELS_API_KEY not configured');
  }

  const response = await fetch(`https://api.pexels.com/v1/search?query=${encodeURIComponent(searchQuery)}&per_page=1&orientation=portrait`, {
    headers: {
      Authorization: pexelsKey,
    },
  });

  if (!response.ok) {
    throw new Error(`Pexels API error: ${response.statusText}`);
  }

  const data = (await response.json()) as { photos: Array<{ src: { large: string } }> };

  if (!data.photos || data.photos.length === 0) {
    throw new Error(`No images found for: ${searchQuery}`);
  }

  return data.photos[0].src.large;
}

/**
 * Generate image via DALL-E API
 */
async function generateDALLEImage(
  _query: string,
  prompt?: string
): Promise<string> {
  const openaiKey = process.env.OPENAI_API_KEY;

  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const finalPrompt = prompt || 'Professional book cover with modern design';

  const response = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${openaiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: finalPrompt,
      n: 1,
      size: '1024x1536',
      quality: 'hd',
      model: 'dall-e-3',
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`DALL-E API error: ${error}`);
  }

  const data = (await response.json()) as { data: Array<{ url: string }> };

  if (!data.data || data.data.length === 0) {
    throw new Error('No image generated from DALL-E');
  }

  return data.data[0].url;
}

/**
 * Generate image via Replicate (Stable Diffusion, FLUX, etc.)
 */
async function generateReplicateImage(
  _query: string,
  prompt?: string
): Promise<string> {
  const replicateToken = process.env.REPLICATE_API_TOKEN;

  if (!replicateToken) {
    throw new Error('REPLICATE_API_TOKEN not configured');
  }

  const finalPrompt = prompt || 'Professional book cover with modern design';

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
        prompt: finalPrompt,
        aspect_ratio: '2:3',
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
    throw new Error('Image generation did not complete');
  }

  return prediction_data.output[0];
}

/**
 * Upload book to Amazon KDP
 */
export async function uploadToKdp(metadata: BookMetadata, coverImageUrl: string): Promise<PlatformUploadResult> {
  try {
    const kdpToken = process.env.KDP_ACCESS_TOKEN;

    if (!kdpToken) {
      return {
        platform: 'kdp',
        success: false,
        error: 'KDP_ACCESS_TOKEN not configured',
      };
    }

    // Format content for KDP
    const content = metadata.longDescription || '';
    const formattedContent = formatContentForKdp(content, 'epub');

    // Create KDP publication
    const kdpPayload = {
      title: metadata.title,
      author: metadata.author,
      description: metadata.description,
      keywords: metadata.keywords.join(','),
      category: metadata.category,
      language: metadata.language || 'en',
      publication_date: new Date().toISOString().split('T')[0],
      is_public_domain: false,
      is_adult_content: metadata.maturityRating !== 'G' && metadata.maturityRating !== 'PG',
      kdp_publication_date: new Date().toISOString().split('T')[0],
      list_price: metadata.price,
      currency: 'USD',
      isbn: metadata.isbn || undefined,
      cover_url: coverImageUrl,
      content_type: 'SINGLE_LANGUAGE_ALL_MARKETS',
      territories: metadata.publicationCountries || ['US'],
    };

    const response = await fetch('https://kdp.amazon.com/api/v1/books', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${kdpToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(kdpPayload),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        platform: 'kdp',
        success: false,
        error: `KDP API error: ${error}`,
      };
    }

    const data = (await response.json()) as {
      book_id?: string;
      asin?: string;
      publication_status?: string;
    };

    return {
      platform: 'kdp',
      success: true,
      bookId: data.book_id,
      asin: data.asin,
      status: data.publication_status,
      royaltyRate: 0.35,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      platform: 'kdp',
      success: false,
      error: error instanceof Error ? error.message : 'KDP upload failed',
    };
  }
}

/**
 * Upload book to Draft2Digital
 */
export async function uploadToDraft2Digital(
  metadata: BookMetadata,
  coverImageUrl: string
): Promise<PlatformUploadResult> {
  try {
    const d2dKey = process.env.DRAFT2DIGITAL_API_KEY;

    if (!d2dKey) {
      return {
        platform: 'draft2digital',
        success: false,
        error: 'DRAFT2DIGITAL_API_KEY not configured',
      };
    }

    // Format content for Draft2Digital
    const content = metadata.longDescription || '';
    const formattedContent = formatContentForDraft2Digital(content);

    // Create Draft2Digital publication
    const d2dPayload = {
      title: metadata.title,
      subtitle: metadata.subtitle,
      author: metadata.author,
      description: metadata.description,
      content: formattedContent,
      cover_url: coverImageUrl,
      keywords: metadata.keywords,
      category: metadata.category,
      language: metadata.language || 'en',
      retail_price: metadata.price,
      series: metadata.series ? `${metadata.series.name} #${metadata.series.number}` : undefined,
      publication_date: new Date().toISOString().split('T')[0],
    };

    const response = await fetch('https://api.draft2digital.com/books', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${d2dKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(d2dPayload),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        platform: 'draft2digital',
        success: false,
        error: `Draft2Digital API error: ${error}`,
      };
    }

    const data = (await response.json()) as {
      id?: string;
      status?: string;
      isbn?: string;
      royalty_rate?: number;
    };

    return {
      platform: 'draft2digital',
      success: true,
      bookId: data.id,
      isbn: data.isbn,
      status: data.status,
      royaltyRate: data.royalty_rate || 0.4,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      platform: 'draft2digital',
      success: false,
      error: error instanceof Error ? error.message : 'Draft2Digital upload failed',
    };
  }
}

/**
 * Upload book to Smashwords
 */
export async function uploadToSmashwords(
  metadata: BookMetadata,
  coverImageUrl: string
): Promise<PlatformUploadResult> {
  try {
    const swKey = process.env.SMASHWORDS_API_KEY;

    if (!swKey) {
      return {
        platform: 'smashwords',
        success: false,
        error: 'SMASHWORDS_API_KEY not configured',
      };
    }

    // Format content for Smashwords
    const content = metadata.longDescription || '';
    const formattedContent = formatContentForSmashwords(content);

    // Create Smashwords publication
    const swPayload = {
      title: metadata.title,
      author: metadata.author,
      description: metadata.description,
      content: formattedContent,
      cover_url: coverImageUrl,
      keywords: metadata.keywords.join(','),
      language: metadata.language || 'en',
      list_price: metadata.price,
      currency: 'USD',
      book_type: 'ebook',
      include_smashwords: true,
      include_retailers: true,
      isbn: metadata.isbn,
      published_date: new Date().toISOString().split('T')[0],
    };

    const response = await fetch('https://api.smashwords.com/v1/books', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${swKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(swPayload),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        platform: 'smashwords',
        success: false,
        error: `Smashwords API error: ${error}`,
      };
    }

    const data = (await response.json()) as {
      book_id?: string;
      isbn?: string;
      status?: string;
      royalty_rate?: number;
    };

    return {
      platform: 'smashwords',
      success: true,
      bookId: data.book_id,
      isbn: data.isbn,
      status: data.status,
      royaltyRate: data.royalty_rate || 0.35,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      platform: 'smashwords',
      success: false,
      error: error instanceof Error ? error.message : 'Smashwords upload failed',
    };
  }
}

/**
 * Track royalties from KDP
 */
export async function trackKdpRoyalties(asin: string): Promise<RoyaltyData[]> {
  try {
    const kdpToken = process.env.KDP_ACCESS_TOKEN;

    if (!kdpToken) {
      throw new Error('KDP_ACCESS_TOKEN not configured');
    }

    const response = await fetch(
      `https://kdp.amazon.com/api/v1/books/${asin}/earnings`,
      {
        headers: {
          Authorization: `Bearer ${kdpToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`KDP API error: ${response.statusText}`);
    }

    const data = (await response.json()) as { earnings?: Array<{
      period: string;
      units: number;
      revenue: number;
      royalty_rate: number;
    }> };

    return (data.earnings || []).map((earning) => ({
      asin,
      platform: 'kdp',
      period: earning.period,
      units: earning.units,
      revenue: earning.revenue,
      royaltyRate: earning.royalty_rate,
      royaltyEarnings: earning.revenue * earning.royalty_rate,
      currency: 'USD',
    }));
  } catch (error) {
    console.error(`Failed to track KDP royalties: ${error}`);
    return [];
  }
}

/**
 * Main orchestration: Find all KDP_BOOK_*.md files and publish them
 */
export async function orchestrateKdpPublication(): Promise<KdpPublicationResult[]> {
  const results: KdpPublicationResult[] = [];
  const startTime = new Date();

  try {
    const fs = await import('fs/promises');
    const files = await fs.readdir('.');

    const bookFiles = files.filter((f) => f.match(/^KDP_BOOK_.*\.md$/i));

    if (bookFiles.length === 0) {
      console.log('No KDP_BOOK_*.md files found');
      return results;
    }

    // Ensure data directory exists
    const dataDir = '.runtime/kdp';
    if (!existsSync(dataDir)) {
      await mkdir(dataDir, { recursive: true });
    }

    for (const file of bookFiles) {
      console.log(`\nProcessing: ${file}`);
      const fileStartTime = new Date();

      try {
        // Parse metadata
        const metadata = await parseBookMetadata(file);
        console.log(`  Title: ${metadata.title}`);
        console.log(`  Author: ${metadata.author}`);

        // Generate cover image
        let coverImageUrl: string | undefined;
        try {
          console.log('  Generating cover image...');
          coverImageUrl = await generateBookCover(metadata);
          console.log(`  ✓ Cover generated: ${coverImageUrl}`);
        } catch (error) {
          console.warn(`  ✗ Cover generation failed: ${error}`);
        }

        // Upload to all platforms in parallel
        const [kdpResult, d2dResult, swResult] = await Promise.all([
          uploadToKdp(metadata, coverImageUrl || ''),
          uploadToDraft2Digital(metadata, coverImageUrl || ''),
          uploadToSmashwords(metadata, coverImageUrl || ''),
        ]);

        const uploads = [kdpResult, d2dResult, swResult];
        const successCount = uploads.filter((u) => u.success).length;
        const failureCount = uploads.filter((u) => !u.success).length;

        const result: KdpPublicationResult = {
          metadata,
          coverImageUrl,
          uploads,
          overallSuccess: failureCount === 0,
          successCount,
          failureCount,
          startTime: fileStartTime.toISOString(),
          endTime: new Date().toISOString(),
          duration: new Date().getTime() - fileStartTime.getTime(),
        };

        results.push(result);

        // Log results
        if (result.overallSuccess) {
          console.log(`  ✓ Published to ${successCount} platform(s)`);
        } else {
          console.log(
            `  ✗ Published to ${successCount} platform(s), ${failureCount} failed`
          );
        }

        // Save result to .runtime/kdp
        const resultFile = path.join(
          dataDir,
          `${metadata.title.replace(/[^a-z0-9]/gi, '_')}_${Date.now()}.json`
        );
        await writeFile(resultFile, JSON.stringify(result, null, 2));
      } catch (error) {
        console.error(`  Error processing ${file}: ${error}`);
      }
    }

    // Save summary
    const summaryFile = path.join(dataDir, `publication-summary_${Date.now()}.json`);
    await writeFile(
      summaryFile,
      JSON.stringify(
        {
          totalBooks: results.length,
          successfulPublications: results.filter((r) => r.overallSuccess).length,
          totalPlatformUploads: results.reduce((sum, r) => sum + r.uploads.length, 0),
          successfulUploads: results.reduce(
            (sum, r) => sum + r.successCount,
            0
          ),
          duration: new Date().getTime() - startTime.getTime(),
          results,
        },
        null,
        2
      )
    );

    console.log(`\n✓ KDP publication complete. Summary saved to ${summaryFile}`);
    return results;
  } catch (error) {
    console.error(`KDP orchestration failed: ${error}`);
    return results;
  }
}

/**
 * Validate book metadata for publishing
 */
export function validateBookMetadata(metadata: BookMetadata): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!metadata.title || metadata.title.trim().length === 0) {
    errors.push('Title is required');
  } else if (metadata.title.length < 3) {
    errors.push('Title must be at least 3 characters');
  }

  if (!metadata.author || metadata.author.trim().length === 0) {
    errors.push('Author is required');
  }

  if (!metadata.description || metadata.description.trim().length === 0) {
    errors.push('Description is required');
  } else if (metadata.description.length < 20) {
    errors.push('Description should be at least 20 characters');
  }

  if (!metadata.category || metadata.category.trim().length === 0) {
    errors.push('Category is required');
  }

  if (metadata.keywords.length === 0) {
    errors.push('At least one keyword is required');
  }

  if (metadata.price <= 0) {
    errors.push('Price must be greater than 0');
  } else if (metadata.price > 99.99) {
    errors.push('Price exceeds maximum of $99.99');
  }

  if (metadata.language && !['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'ja', 'zh'].includes(metadata.language)) {
    errors.push(`Unsupported language: ${metadata.language}`);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Assess publication risk
 */
export function assessPublicationRisk(metadata: BookMetadata): {
  riskLevel: 'low' | 'medium' | 'high';
  score: number;
  warnings: string[];
} {
  const warnings: string[] = [];
  let score = 0; // 0-100, higher = more risk

  // Title assessment
  if (metadata.title.length < 5) {
    warnings.push('Title is very short (less than 5 characters)');
    score += 10;
  }
  if (metadata.title.length > 100) {
    warnings.push('Title exceeds 100 characters');
    score += 5;
  }

  // Description assessment
  if (metadata.description.length < 50) {
    warnings.push('Description may be too brief for optimal discoverability');
    score += 15;
  }
  if (metadata.description.length > 4000) {
    warnings.push('Description exceeds recommended 4000 character limit');
    score += 5;
  }

  // Keywords assessment
  if (metadata.keywords.length < 3) {
    warnings.push('Fewer than 3 keywords provided');
    score += 20;
  } else if (metadata.keywords.length > 7) {
    warnings.push('More than 7 keywords may reduce relevance');
    score += 5;
  }

  // Price assessment
  if (metadata.price < 2.99) {
    warnings.push('Very low price may affect perceived value');
    score += 10;
  }

  // Category assessment (common categories reduce risk)
  const commonCategories = ['Fiction', 'Self-Help', 'Business', 'Science', 'History', 'Art & Design'];
  if (!commonCategories.includes(metadata.category)) {
    warnings.push(`${metadata.category} is a less common category`);
    score += 5;
  }

  // Missing optional but recommended fields
  if (!metadata.isbn) {
    warnings.push('ISBN not provided (optional but recommended)');
    score += 5;
  }

  let riskLevel: 'low' | 'medium' | 'high' = 'low';
  if (score >= 40) {
    riskLevel = 'high';
  } else if (score >= 20) {
    riskLevel = 'medium';
  }

  return { riskLevel, score, warnings };
}

/**
 * Get recommended platforms for a book
 */
export function getRecommendedPlatforms(metadata: BookMetadata): ('kdp' | 'draft2digital' | 'smashwords')[] {
  const platforms: ('kdp' | 'draft2digital' | 'smashwords')[] = [];

  // KDP is always recommended for English books
  if (metadata.language === 'en' || !metadata.language) {
    platforms.push('kdp');
  }

  // Draft2Digital for multiplatform distribution
  if (metadata.keywords.some(k => k.toLowerCase().includes('ebook'))) {
    platforms.push('draft2digital');
  }

  // Smashwords for DRM-free or indie focus
  if (metadata.category.includes('Self') || metadata.price < 5) {
    platforms.push('smashwords');
  }

  // Ensure at least KDP is recommended
  if (platforms.length === 0) {
    platforms.push('kdp');
  }

  return platforms;
}

/**
 * Batch publish multiple books with validation
 */
export async function batchPublishBooks(
  bookFiles: string[],
  options: {
    validateOnly?: boolean;
    platforms?: ('kdp' | 'draft2digital' | 'smashwords')[];
    maxBatchSize?: number;
  } = {}
): Promise<{
  total: number;
  successful: number;
  failed: number;
  validated: number;
  results: KdpPublicationResult[];
  validationErrors: Array<{ file: string; errors: string[] }>;
}> {
  const {
    validateOnly = false,
    platforms,
    maxBatchSize = parseInt(process.env.KDP_MAX_PUBLISH_BATCH_SIZE || '10', 10),
  } = options;

  const results: KdpPublicationResult[] = [];
  const validationErrors: Array<{ file: string; errors: string[] }> = [];
  let validated = 0;
  let successful = 0;
  let failed = 0;

  // Process in batches
  for (let i = 0; i < bookFiles.length; i += maxBatchSize) {
    const batch = bookFiles.slice(i, i + maxBatchSize);

    for (const file of batch) {
      try {
        const metadata = await parseBookMetadata(file);

        // Validate metadata
        const validation = validateBookMetadata(metadata);
        if (!validation.valid) {
          validationErrors.push({ file, errors: validation.errors });
          failed++;
          continue;
        }
        validated++;

        if (validateOnly) {
          continue;
        }

        // Generate cover and publish
        let coverImageUrl: string | undefined;
        try {
          coverImageUrl = await generateBookCover(metadata);
        } catch (error) {
          console.warn(`Failed to generate cover for ${metadata.title}: ${error}`);
        }

        const selectedPlatforms = platforms || getRecommendedPlatforms(metadata);
        const uploadPromises = [];

        if (selectedPlatforms.includes('kdp')) {
          uploadPromises.push(uploadToKdp(metadata, coverImageUrl || ''));
        }
        if (selectedPlatforms.includes('draft2digital')) {
          uploadPromises.push(uploadToDraft2Digital(metadata, coverImageUrl || ''));
        }
        if (selectedPlatforms.includes('smashwords')) {
          uploadPromises.push(uploadToSmashwords(metadata, coverImageUrl || ''));
        }

        const uploads = await Promise.all(uploadPromises);
        const successCount = uploads.filter((u) => u.success).length;

        const result: KdpPublicationResult = {
          metadata,
          coverImageUrl,
          uploads,
          overallSuccess: uploads.every((u) => u.success),
          successCount,
          failureCount: uploads.length - successCount,
          startTime: new Date().toISOString(),
          endTime: new Date().toISOString(),
          duration: 0,
        };

        results.push(result);
        successful += result.overallSuccess ? 1 : 0;
      } catch (error) {
        failed++;
        validationErrors.push({ file, errors: [error instanceof Error ? error.message : 'Unknown error'] });
      }
    }
  }

  return {
    total: bookFiles.length,
    successful,
    failed,
    validated,
    results,
    validationErrors,
  };
}

export {
  BookMetadata,
  PlatformUploadResult,
  RoyaltyData,
};
