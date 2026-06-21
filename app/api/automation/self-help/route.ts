/**
 * SELF-HELP CONTENT AUTOMATION API ENDPOINTS
 *
 * Routes:
 * POST /api/automation/self-help/generate — Generate content
 * POST /api/automation/self-help/course — Generate course module
 * POST /api/automation/self-help/transcript — Process YouTube transcript
 * POST /api/automation/self-help/ebook — Generate ebook chapters
 * POST /api/automation/self-help/distribute — Publish content to platforms
 * POST /api/automation/self-help/export — Export content in multiple formats
 * GET /api/automation/self-help/status — Check generation status
 *
 * Request Examples:
 *
 * Generate Blog Article:
 * POST /api/automation/self-help/generate
 * {
 *   "topic": "How to Build Passive Income Streams",
 *   "difficulty": "beginner",
 *   "format": "blog",
 *   "keywords": ["passive income", "side hustle", "freelancing"],
 *   "targetAudience": "entrepreneurs",
 *   "tone": "inspirational",
 *   "includeAffiliates": true,
 *   "estimatedLength": "medium"
 * }
 *
 * Generate Course Module:
 * POST /api/automation/self-help/course
 * {
 *   "topic": "Advanced Trading Strategies",
 *   "difficulty": "advanced",
 *   "numberOfLessons": 7
 * }
 *
 * Process YouTube Transcript:
 * POST /api/automation/self-help/transcript
 * {
 *   "videoId": "dQw4w9WgXcQ",
 *   "title": "10 Ways to Make Money Online"
 * }
 *
 * Generate eBook:
 * POST /api/automation/self-help/ebook
 * {
 *   "title": "The Complete Guide to Financial Freedom",
 *   "numberOfChapters": 10
 * }
 *
 * Distribute Content:
 * POST /api/automation/self-help/distribute
 * {
 *   "contentId": "content-1719000000000",
 *   "platforms": ["blog", "newsletter", "social", "medium", "devto"],
 *   "schedule": "2026-06-21T09:00:00Z"
 * }
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateContent,
  generateCourseModule,
  processYouTubeTranscript,
  generateEbookChapters,
  distributeContent,
  exportContent,
  ContentTopicRequest,
  GeneratedContent,
  CourseModule,
  YouTubeTranscript,
  EbookChapter,
  ContentDistributionResult,
} from '@/app/lib/automation/self-help';

// Simple in-memory cache for generation status
const generationStatus = new Map<
  string,
  {
    status: 'pending' | 'generating' | 'complete' | 'error';
    progress: number;
    result?: any;
    error?: string;
    startedAt: number;
  }
>();

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

interface GenerateContentRequest {
  topic: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  format?: 'blog' | 'course' | 'ebook' | 'youtube-transcript' | 'all';
  keywords?: string[];
  targetAudience?: string;
  tone?: 'professional' | 'casual' | 'inspirational' | 'educational';
  includeAffiliates?: boolean;
  estimatedLength?: 'short' | 'medium' | 'long';
}

interface GenerateCourseRequest {
  topic: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  numberOfLessons?: number;
}

interface ProcessTranscriptRequest {
  videoId: string;
  title: string;
}

interface GenerateEbookRequest {
  title: string;
  numberOfChapters?: number;
}

interface DistributeContentRequest {
  contentId: string;
  platforms?: string[];
  schedule?: string;
}

interface ExportContentRequest {
  contentId: string;
  formats?: string[];
}

interface StatusCheckRequest {
  generationId: string;
}

// ============================================================================
// MAIN HANDLER
// ============================================================================

export async function POST(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const pathSegments = url.pathname.split('/');
    const action = pathSegments[pathSegments.length - 1]; // Last segment

    const body = await req.json();

    // Route to appropriate handler
    if (action === 'generate') {
      return handleGenerateContent(body);
    } else if (action === 'course') {
      return handleGenerateCourse(body);
    } else if (action === 'transcript') {
      return handleProcessTranscript(body);
    } else if (action === 'ebook') {
      return handleGenerateEbook(body);
    } else if (action === 'distribute') {
      return handleDistributeContent(body);
    } else if (action === 'export') {
      return handleExportContent(body);
    } else {
      return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
    }
  } catch (error) {
    console.error('Error in self-help automation:', error);
    return NextResponse.json(
      {
        error: 'Failed to process request',
        details: String(error),
      },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const status = url.searchParams.get('status');
    const generationId = url.searchParams.get('id');

    if (status && generationId) {
      return handleStatusCheck({ generationId });
    }

    return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
  } catch (error) {
    console.error('Error checking status:', error);
    return NextResponse.json(
      { error: 'Failed to check status', details: String(error) },
      { status: 500 }
    );
  }
}

// ============================================================================
// HANDLER FUNCTIONS
// ============================================================================

/**
 * Generate content (blog, course structure, or hybrid)
 */
async function handleGenerateContent(body: GenerateContentRequest) {
  const generationId = `gen-${Date.now()}`;

  // Start generation asynchronously
  const request: ContentTopicRequest = {
    topic: body.topic,
    difficulty: body.difficulty || 'intermediate',
    format: body.format || 'blog',
    keywords: body.keywords || [],
    targetAudience: body.targetAudience || 'professionals',
    tone: body.tone || 'professional',
    includeAffiliates: body.includeAffiliates ?? true,
    estimatedLength: body.estimatedLength || 'medium',
  };

  // Mark as generating
  generationStatus.set(generationId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  // Generate in background
  generateContent(request)
    .then((result) => {
      generationStatus.set(generationId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(generationId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      generationId,
      status: 'generating',
      message: 'Content generation started',
      statusUrl: `/api/automation/self-help?status=check&id=${generationId}`,
    },
    { status: 202 }
  );
}

/**
 * Generate course module
 */
async function handleGenerateCourse(body: GenerateCourseRequest) {
  const generationId = `course-${Date.now()}`;

  generationStatus.set(generationId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  generateCourseModule(body.topic, body.difficulty || 'intermediate')
    .then((result) => {
      generationStatus.set(generationId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(generationId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      generationId,
      status: 'generating',
      message: 'Course module generation started',
      statusUrl: `/api/automation/self-help?status=check&id=${generationId}`,
    },
    { status: 202 }
  );
}

/**
 * Process YouTube transcript
 */
async function handleProcessTranscript(body: ProcessTranscriptRequest) {
  const generationId = `transcript-${Date.now()}`;

  if (!body.videoId || !body.title) {
    return NextResponse.json(
      { error: 'Missing videoId or title' },
      { status: 400 }
    );
  }

  generationStatus.set(generationId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  processYouTubeTranscript(body.videoId, body.title)
    .then((result) => {
      generationStatus.set(generationId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(generationId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      generationId,
      status: 'generating',
      message: 'Transcript processing started',
      statusUrl: `/api/automation/self-help?status=check&id=${generationId}`,
    },
    { status: 202 }
  );
}

/**
 * Generate eBook chapters
 */
async function handleGenerateEbook(body: GenerateEbookRequest) {
  const generationId = `ebook-${Date.now()}`;

  if (!body.title) {
    return NextResponse.json({ error: 'Missing title' }, { status: 400 });
  }

  generationStatus.set(generationId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  generateEbookChapters(body.title, body.numberOfChapters || 8)
    .then((result) => {
      generationStatus.set(generationId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(generationId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      generationId,
      status: 'generating',
      message: 'eBook generation started',
      statusUrl: `/api/automation/self-help?status=check&id=${generationId}`,
    },
    { status: 202 }
  );
}

/**
 * Distribute content to platforms
 */
async function handleDistributeContent(body: DistributeContentRequest) {
  if (!body.contentId) {
    return NextResponse.json({ error: 'Missing contentId' }, { status: 400 });
  }

  // In production, retrieve actual content from database
  // For now, create a mock content object
  const mockContent: GeneratedContent = {
    id: body.contentId,
    topic: 'General Topic',
    format: 'blog',
    title: 'Generated Content',
    content: 'Content here',
    markdown: '# Generated Content\n\nContent here',
    html: '<h1>Generated Content</h1><p>Content here</p>',
    wordCount: 100,
    readingTimeMinutes: 1,
    seoKeywords: [],
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: 'ProfitEngine AI',
      category: 'General',
      tags: [],
    },
    generatedAt: new Date().toISOString(),
  };

  const platforms = body.platforms || ['blog', 'newsletter', 'social'];
  const distributionId = `dist-${Date.now()}`;

  generationStatus.set(distributionId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  distributeContent(mockContent, platforms)
    .then((result) => {
      generationStatus.set(distributionId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(distributionId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      distributionId,
      status: 'distributing',
      message: 'Content distribution started',
      platforms,
      statusUrl: `/api/automation/self-help?status=check&id=${distributionId}`,
    },
    { status: 202 }
  );
}

/**
 * Export content in multiple formats
 */
async function handleExportContent(body: ExportContentRequest) {
  if (!body.contentId) {
    return NextResponse.json({ error: 'Missing contentId' }, { status: 400 });
  }

  const mockContent: GeneratedContent = {
    id: body.contentId,
    topic: 'General Topic',
    format: 'blog',
    title: 'Generated Content',
    content: 'Content here',
    markdown: '# Generated Content\n\nContent here',
    html: '<h1>Generated Content</h1><p>Content here</p>',
    wordCount: 100,
    readingTimeMinutes: 1,
    seoKeywords: [],
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: 'ProfitEngine AI',
      category: 'General',
      tags: [],
    },
    generatedAt: new Date().toISOString(),
  };

  const formats = body.formats || ['markdown', 'html', 'pdf'];
  const exportId = `export-${Date.now()}`;

  generationStatus.set(exportId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  exportContent(mockContent, formats)
    .then((result) => {
      generationStatus.set(exportId, {
        status: 'complete',
        progress: 100,
        result,
        startedAt: Date.now(),
      });
    })
    .catch((error) => {
      generationStatus.set(exportId, {
        status: 'error',
        progress: 0,
        error: String(error),
        startedAt: Date.now(),
      });
    });

  return NextResponse.json(
    {
      success: true,
      exportId,
      status: 'exporting',
      message: 'Content export started',
      formats,
      statusUrl: `/api/automation/self-help?status=check&id=${exportId}`,
    },
    { status: 202 }
  );
}

/**
 * Check generation/distribution status
 */
async function handleStatusCheck(body: StatusCheckRequest) {
  const status = generationStatus.get(body.generationId);

  if (!status) {
    return NextResponse.json({ error: 'Generation not found' }, { status: 404 });
  }

  const elapsedSeconds = (Date.now() - status.startedAt) / 1000;

  return NextResponse.json({
    generationId: body.generationId,
    status: status.status,
    progress: status.progress,
    elapsedSeconds,
    result: status.status === 'complete' ? status.result : null,
    error: status.error || null,
  });
}

// ============================================================================
// BATCH OPERATION ENDPOINTS
// ============================================================================

/**
 * Generate multiple content pieces in sequence
 */
export async function generateContentBatch(
  topics: string[],
  options?: {
    difficulty?: string;
    format?: string;
    tone?: string;
    parallel?: boolean;
  }
) {
  const batchId = `batch-${Date.now()}`;
  const results: GeneratedContent[] = [];

  generationStatus.set(batchId, {
    status: 'generating',
    progress: 0,
    startedAt: Date.now(),
  });

  try {
    for (let i = 0; i < topics.length; i++) {
      const request: ContentTopicRequest = {
        topic: topics[i],
        difficulty: (options?.difficulty as any) || 'intermediate',
        format: (options?.format as any) || 'blog',
        keywords: [],
        targetAudience: 'professionals',
        tone: (options?.tone as any) || 'professional',
        includeAffiliates: true,
      };

      const content = await generateContent(request);
      results.push(content);

      // Update progress
      const progress = Math.round(((i + 1) / topics.length) * 100);
      const status = generationStatus.get(batchId);
      if (status) {
        status.progress = progress;
      }
    }

    generationStatus.set(batchId, {
      status: 'complete',
      progress: 100,
      result: results,
      startedAt: Date.now(),
    });

    return NextResponse.json({
      success: true,
      batchId,
      totalGenerated: results.length,
      contents: results,
    });
  } catch (error) {
    generationStatus.set(batchId, {
      status: 'error',
      progress: 0,
      error: String(error),
      startedAt: Date.now(),
    });

    return NextResponse.json(
      {
        error: 'Batch generation failed',
        batchId,
        details: String(error),
      },
      { status: 500 }
    );
  }
}

/**
 * Generate content calendar for month
 */
export async function generateContentCalendar(
  topics: string[],
  numberOfPostsPerTopic: number = 4
) {
  const calendarId = `calendar-${Date.now()}`;
  const calendar: Record<string, GeneratedContent[]> = {};

  try {
    for (const topic of topics) {
      calendar[topic] = [];

      for (let i = 0; i < numberOfPostsPerTopic; i++) {
        const request: ContentTopicRequest = {
          topic: `${topic} - Part ${i + 1}`,
          difficulty: 'intermediate',
          format: 'blog',
          keywords: [topic],
          targetAudience: 'entrepreneurs',
          tone: 'professional',
          includeAffiliates: true,
        };

        const content = await generateContent(request);
        calendar[topic].push(content);
      }
    }

    return NextResponse.json({
      success: true,
      calendarId,
      calendar,
      totalPosts: Object.values(calendar).flat().length,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Calendar generation failed',
        details: String(error),
      },
      { status: 500 }
    );
  }
}

export default POST;
