/**
 * Instagram Graph API v18.0 Wrapper
 * Handles carousel, reel, story uploads and engagement metrics
 */

export interface InstagramGraphAPIConfig {
  businessAccountId: string;
  accessToken: string;
  apiVersion?: string;
}

export interface CarouselSlideMediaInput {
  imageUrl: string;
  caption?: string;
}

export interface CarouselUploadRequest {
  mediaType: 'CAROUSEL';
  children: string[]; // Array of media IDs from individual slide uploads
  caption: string;
  accessToken: string;
}

export interface ReelUploadRequest {
  mediaType: 'REELS';
  videoUrl: string;
  caption: string;
  videoData?: Buffer; // Alternative to videoUrl
  accessToken: string;
}

export interface StoryUploadRequest {
  mediaType: 'STORIES';
  imageUrl?: string;
  videoUrl?: string;
  caption?: string;
  accessToken: string;
}

export interface MediaResponse {
  id: string;
  mediaType: string;
  createdAt: string;
  status: 'PROCESSING' | 'FINISHED' | 'ERROR';
  errors?: string[];
}

export interface InsightsData {
  metric: string;
  values: Array<{ value: number; date?: string }>;
  title: string;
  description?: string;
  period?: string;
}

export class InstagramGraphAPI {
  private readonly apiVersion: string = 'v18.0';
  private readonly baseUrl = 'https://graph.instagram.com';
  private config: InstagramGraphAPIConfig;

  constructor(config: InstagramGraphAPIConfig) {
    this.config = {
      ...config,
      apiVersion: config.apiVersion || 'v18.0',
    };
    this.apiVersion = this.config.apiVersion || 'v18.0';
  }

  /**
   * Upload a carousel post with multiple slides
   * Steps:
   * 1. Upload each slide image individually
   * 2. Collect media IDs
   * 3. Create carousel container with all media IDs
   */
  async uploadCarousel(
    slides: CarouselSlideMediaInput[],
    caption: string
  ): Promise<MediaResponse> {
    if (slides.length < 2 || slides.length > 10) {
      throw new Error('Carousel must have 2-10 slides');
    }

    try {
      // Step 1: Upload each slide
      const mediaIds: string[] = [];

      for (const slide of slides) {
        const mediaId = await this.uploadSlideImage(slide.imageUrl);
        mediaIds.push(mediaId);
      }

      // Step 2: Create carousel container
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}/media`;

      const payload = {
        media_type: 'CAROUSEL',
        children: mediaIds,
        caption: caption,
        access_token: this.config.accessToken,
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to create carousel: ${error.error?.message || response.statusText}`
        );
      }

      const data = await response.json();

      return {
        id: data.id,
        mediaType: 'CAROUSEL',
        createdAt: new Date().toISOString(),
        status: 'PROCESSING',
      };
    } catch (error) {
      throw new Error(
        `Carousel upload failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Upload individual slide image
   */
  private async uploadSlideImage(imageUrl: string): Promise<string> {
    const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}/media`;

    const payload = {
      image_url: imageUrl,
      access_token: this.config.accessToken,
    };

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        `Failed to upload slide image: ${error.error?.message || response.statusText}`
      );
    }

    const data = await response.json();
    return data.id;
  }

  /**
   * Upload a reel (video post)
   * Requires video in mp4 format, max 90 seconds
   */
  async uploadReel(
    videoUrl: string,
    caption: string,
    thumbnail?: string
  ): Promise<MediaResponse> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}/media`;

      const payload: Record<string, unknown> = {
        media_type: 'REELS',
        video_url: videoUrl,
        caption: caption,
        access_token: this.config.accessToken,
      };

      // Optional: Add custom thumbnail
      if (thumbnail) {
        payload.thumbnail_url = thumbnail;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to upload reel: ${error.error?.message || response.statusText}`
        );
      }

      const data = await response.json();

      return {
        id: data.id,
        mediaType: 'REELS',
        createdAt: new Date().toISOString(),
        status: 'PROCESSING',
      };
    } catch (error) {
      throw new Error(
        `Reel upload failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Upload a story (image or video)
   * Stories expire after 24 hours
   */
  async uploadStory(
    imageUrl: string | null,
    videoUrl: string | null,
    caption?: string
  ): Promise<MediaResponse> {
    if (!imageUrl && !videoUrl) {
      throw new Error('Story must have either imageUrl or videoUrl');
    }

    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}/media`;

      const payload: Record<string, unknown> = {
        media_type: 'STORIES',
        access_token: this.config.accessToken,
      };

      if (imageUrl) {
        payload.image_url = imageUrl;
      } else {
        payload.video_url = videoUrl;
      }

      if (caption) {
        payload.caption = caption;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to upload story: ${error.error?.message || response.statusText}`
        );
      }

      const data = await response.json();

      return {
        id: data.id,
        mediaType: 'STORIES',
        createdAt: new Date().toISOString(),
        status: 'PROCESSING',
      };
    } catch (error) {
      throw new Error(
        `Story upload failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get engagement insights
   * Metrics: impressions, reach, saves, likes, comments, shares, video_views
   */
  async getInsights(
    metrics: string[] = [
      'impressions',
      'reach',
      'saves',
      'likes',
      'comments',
      'shares',
    ]
  ): Promise<InsightsData[]> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}/insights`;

      const params = new URLSearchParams({
        metric: metrics.join(','),
        period: 'day',
        access_token: this.config.accessToken,
      });

      const response = await fetch(`${endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to fetch insights: ${error.error?.message || response.statusText}`
        );
      }

      const data = await response.json();
      return data.data as InsightsData[];
    } catch (error) {
      throw new Error(
        `Failed to get insights: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Get insights for a specific media post
   */
  async getMediaInsights(mediaId: string): Promise<InsightsData[]> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${mediaId}/insights`;

      const params = new URLSearchParams({
        metric: 'impressions,reach,likes,comments,saves',
        access_token: this.config.accessToken,
      });

      const response = await fetch(`${endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to fetch media insights: ${error.error?.message || response.statusText}`
        );
      }

      const data = await response.json();
      return data.data as InsightsData[];
    } catch (error) {
      throw new Error(
        `Failed to get media insights: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Check media status (useful for checking if carousel/reel finished processing)
   */
  async getMediaStatus(mediaId: string): Promise<{
    id: string;
    status: string;
    timestamp?: string;
  }> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${mediaId}`;

      const params = new URLSearchParams({
        fields: 'id,status,timestamp',
        access_token: this.config.accessToken,
      });

      const response = await fetch(`${endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to fetch media status: ${error.error?.message || response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      throw new Error(
        `Failed to get media status: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Validate access token and connection
   */
  async validateConnection(): Promise<boolean> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/me`;

      const params = new URLSearchParams({
        access_token: this.config.accessToken,
      });

      const response = await fetch(`${endpoint}?${params.toString()}`, {
        method: 'GET',
      });

      return response.ok;
    } catch (error) {
      console.error('Connection validation failed:', error);
      return false;
    }
  }

  /**
   * Get account info
   */
  async getAccountInfo(): Promise<{
    id: string;
    name: string;
    username?: string;
    biography?: string;
    followers_count?: number;
  }> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${this.config.businessAccountId}`;

      const params = new URLSearchParams({
        fields: 'id,name,username,biography,followers_count',
        access_token: this.config.accessToken,
      });

      const response = await fetch(`${endpoint}?${params.toString()}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to fetch account info: ${error.error?.message || response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      throw new Error(
        `Failed to get account info: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Publish scheduled media (must be in scheduled state first)
   */
  async publishMedia(mediaId: string): Promise<{ success: boolean }> {
    try {
      const endpoint = `${this.baseUrl}/${this.apiVersion}/${mediaId}/publish`;

      const payload = {
        access_token: this.config.accessToken,
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(
          `Failed to publish media: ${error.error?.message || response.statusText}`
        );
      }

      return { success: true };
    } catch (error) {
      throw new Error(
        `Failed to publish media: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}

/**
 * Create API instance from environment variables
 */
export function createInstagramAPI(): InstagramGraphAPI {
  const businessAccountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;
  const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;

  if (!businessAccountId || !accessToken) {
    throw new Error(
      'Missing INSTAGRAM_BUSINESS_ACCOUNT_ID or INSTAGRAM_ACCESS_TOKEN environment variables'
    );
  }

  return new InstagramGraphAPI({
    businessAccountId,
    accessToken,
    apiVersion: 'v18.0',
  });
}
