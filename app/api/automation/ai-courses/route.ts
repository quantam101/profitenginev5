/**
 * API ENDPOINT: POST /api/automation/ai-courses
 *
 * Trigger AI Courses & Tools automation from API request:
 * - Generate course content from topics
 * - Create ChatGPT prompt libraries
 * - Generate tool guides
 * - Bundle courses with discounts
 * - Upload to Gumroad
 * - Setup email funnels
 * - Track course performance
 *
 * Request Examples:
 * ```json
 * // Generate complete course
 * {
 *   "action": "generate-course",
 *   "courseTitle": "Prompt Engineering Mastery",
 *   "topic": "Advanced ChatGPT prompting techniques",
 *   "level": "advanced",
 *   "price": 97,
 *   "moduleCount": 5
 * }
 *
 * // Create prompt library
 * {
 *   "action": "generate-prompts",
 *   "libraryName": "Email Marketing Prompts",
 *   "category": "Email Marketing",
 *   "promptCount": 15
 * }
 *
 * // Generate tool guide
 * {
 *   "action": "generate-tool-guide",
 *   "toolName": "Claude AI",
 *   "toolDescription": "Advanced AI assistant for content creation"
 * }
 *
 * // Create bundle
 * {
 *   "action": "create-bundle",
 *   "bundleTitle": "Complete AI Mastery Bundle",
 *   "courses": ["course-1", "course-2"],
 *   "toolGuides": ["guide-1", "guide-2"],
 *   "promptLibraries": ["lib-1"]
 * }
 *
 * // Publish to Gumroad
 * {
 *   "action": "publish-course",
 *   "courseId": "course-123",
 *   "courseData": { ... }
 * }
 *
 * // Setup email funnel
 * {
 *   "action": "setup-email-funnel",
 *   "courseId": "course-123",
 *   "courseName": "Prompt Engineering 101"
 * }
 *
 * // Get performance metrics
 * {
 *   "action": "get-performance",
 *   "courseId": "course-123",
 *   "gumroadProductId": "product-abc"
 * }
 *
 * // Bulk orchestration
 * {
 *   "action": "orchestrate",
 *   "courses": [
 *     {
 *       "title": "Course 1",
 *       "topic": "Topic 1",
 *       "price": 97
 *     }
 *   ]
 * }
 * ```
 *
 * Response:
 * ```json
 * {
 *   "success": true,
 *   "action": "generate-course",
 *   "result": { ... },
 *   "timestamp": "2024-06-20T...",
 *   "duration": 5234
 * }
 * ```
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  generateCourseContent,
  generatePromptLibrary,
  generateToolGuide,
  createCourseBundle,
  publishCourseToGumroad,
  publishBundleToGumroad,
  createCourseEmailSequence,
  setupEmailCampaignBrevo,
  getCoursePerformance,
  savePromptLibrary,
  saveToolGuide,
  saveCourseBundle,
  parseCourseMeta,
  addAffiliateLinksToCourseMeta,
  AICourseMeta,
  ChatGPTPromptLibrary,
  ToolGuide,
  CourseBundle,
  CourseEmail,
  CoursePublishResult,
  CoursePerformance,
} from '@/app/lib/automation/ai-courses';

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST/RESPONSE TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface GenerateCourseRequest {
  action: 'generate-course';
  courseTitle: string;
  topic: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  price: number;
  moduleCount?: number;
  targetAudience?: string[];
  learningOutcomes?: string[];
  certificateIncluded?: boolean;
  lifetimeAccess?: boolean;
}

interface GeneratePromptsRequest {
  action: 'generate-prompts';
  libraryName: string;
  category: string;
  promptCount?: number;
}

interface GenerateToolGuideRequest {
  action: 'generate-tool-guide';
  toolName: string;
  toolDescription: string;
}

interface CreateBundleRequest {
  action: 'create-bundle';
  bundleTitle: string;
  courseIds: string[];
  toolGuideIds: string[];
  promptLibraryIds: string[];
}

interface PublishCourseRequest {
  action: 'publish-course';
  course: AICourseMeta;
  setupEmailFunnel?: boolean;
}

interface PublishBundleRequest {
  action: 'publish-bundle';
  bundle: CourseBundle;
}

interface SetupEmailFunnelRequest {
  action: 'setup-email-funnel';
  courseId: string;
  courseName: string;
}

interface GetPerformanceRequest {
  action: 'get-performance';
  courseId: string;
  gumroadProductId: string;
}

interface OrchestrateRequest {
  action: 'orchestrate';
  courses: Array<{
    title: string;
    topic: string;
    level: 'beginner' | 'intermediate' | 'advanced';
    price: number;
    moduleCount?: number;
  }>;
  createBundle?: boolean;
  publishToGumroad?: boolean;
  setupEmailFunnel?: boolean;
}

type CourseAutomationRequest =
  | GenerateCourseRequest
  | GeneratePromptsRequest
  | GenerateToolGuideRequest
  | CreateBundleRequest
  | PublishCourseRequest
  | PublishBundleRequest
  | SetupEmailFunnelRequest
  | GetPerformanceRequest
  | OrchestrateRequest;

interface ApiResponse {
  success: boolean;
  action: string;
  result?: unknown;
  error?: string;
  timestamp: string;
  duration: number;
}

// ═══════════════════════════════════════════════════════════════════════════════
// REQUEST HANDLERS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Handle generate-course request
 */
async function handleGenerateCourse(
  req: GenerateCourseRequest
): Promise<{ course: AICourseMeta; modules: unknown[] }> {
  console.log(`Generating course: ${req.courseTitle}`);

  const modules = await generateCourseContent(
    req.courseTitle,
    req.topic,
    req.level,
    req.moduleCount || 3
  );

  const course: AICourseMeta = {
    id: `course-${Date.now()}`,
    title: req.courseTitle,
    description: req.topic,
    category: 'prompt-engineering',
    level: req.level,
    price: req.price,
    duration: `${(req.moduleCount || 3) * 2} hours`,
    modules,
    targetAudience: req.targetAudience || [],
    learningOutcomes: req.learningOutcomes || [],
    tags: [req.topic],
    certificateIncluded: req.certificateIncluded ?? true,
    lifetimeAccess: req.lifetimeAccess ?? true,
  };

  console.log(`Generated course with ${modules.length} modules`);

  return {
    course,
    modules,
  };
}

/**
 * Handle generate-prompts request
 */
async function handleGeneratePrompts(
  req: GeneratePromptsRequest
): Promise<ChatGPTPromptLibrary> {
  console.log(`Generating prompt library: ${req.libraryName}`);

  const library = await generatePromptLibrary(
    req.libraryName,
    req.category,
    req.promptCount || 10
  );

  console.log(`Generated ${library.totalPrompts} prompts`);

  return library;
}

/**
 * Handle generate-tool-guide request
 */
async function handleGenerateToolGuide(req: GenerateToolGuideRequest): Promise<ToolGuide> {
  console.log(`Generating tool guide: ${req.toolName}`);

  const guide = await generateToolGuide(req.toolName, req.toolDescription);

  console.log(`Generated guide for ${req.toolName}`);

  return guide;
}

/**
 * Handle create-bundle request
 */
async function handleCreateBundle(req: CreateBundleRequest): Promise<CourseBundle> {
  console.log(`Creating bundle: ${req.bundleTitle}`);

  // TODO: Load actual course, tool, and prompt data from IDs
  // For now, return skeleton
  const bundle: CourseBundle = {
    id: `bundle-${Date.now()}`,
    bundleTitle: req.bundleTitle,
    description: `Bundle containing ${req.courseIds.length} courses, ${req.toolGuideIds.length} tools, and ${req.promptLibraryIds.length} prompt libraries`,
    courses: req.courseIds,
    tools: [],
    prompts: [],
    bundlePrice: 199,
    individualPrice: 299,
    discountPercentage: 33,
    includedResources: [
      'Lifetime access',
      'All updates',
      'Community access',
      'Email support',
    ],
    bonuses: [],
  };

  console.log(`Created bundle: ${bundle.id}`);

  return bundle;
}

/**
 * Handle publish-course request
 */
async function handlePublishCourse(req: PublishCourseRequest): Promise<{
  publishResult: CoursePublishResult;
  emailCampaignId?: string;
}> {
  console.log(`Publishing course: ${req.course.title}`);

  const publishResult = await publishCourseToGumroad(req.course);

  if (!publishResult.success) {
    throw new Error(`Failed to publish: ${publishResult.error}`);
  }

  let emailCampaignId: string | undefined;

  if (req.setupEmailFunnel) {
    console.log(`Setting up email funnel for: ${req.course.title}`);
    const emailSequence = createCourseEmailSequence(req.course.id, req.course.title);

    try {
      emailCampaignId = await setupEmailCampaignBrevo(emailSequence);
      console.log(`Email campaign created: ${emailCampaignId}`);
    } catch (error) {
      console.warn(`Failed to setup email campaign: ${error}`);
    }
  }

  return {
    publishResult,
    emailCampaignId,
  };
}

/**
 * Handle publish-bundle request
 */
async function handlePublishBundle(req: PublishBundleRequest): Promise<CoursePublishResult> {
  console.log(`Publishing bundle: ${req.bundle.bundleTitle}`);

  const publishResult = await publishBundleToGumroad(req.bundle);

  if (!publishResult.success) {
    throw new Error(`Failed to publish bundle: ${publishResult.error}`);
  }

  console.log(`Bundle published: ${publishResult.gumroadUrl}`);

  return publishResult;
}

/**
 * Handle setup-email-funnel request
 */
async function handleSetupEmailFunnel(req: SetupEmailFunnelRequest): Promise<{
  campaignId: string;
  emailCount: number;
}> {
  console.log(`Setting up email funnel for: ${req.courseName}`);

  const emailSequence = createCourseEmailSequence(req.courseId, req.courseName);
  const campaignId = await setupEmailCampaignBrevo(emailSequence);

  return {
    campaignId,
    emailCount: emailSequence.emailSequence.length,
  };
}

/**
 * Handle get-performance request
 */
async function handleGetPerformance(req: GetPerformanceRequest): Promise<CoursePerformance> {
  console.log(`Getting performance for: ${req.courseId}`);

  const performance = await getCoursePerformance(req.courseId, req.gumroadProductId);

  return performance;
}

/**
 * Handle orchestrate request - generate and publish multiple courses
 */
async function handleOrchestrate(req: OrchestrateRequest): Promise<{
  courses: CoursePublishResult[];
  bundle?: CoursePublishResult;
  totalTime: number;
}> {
  console.log(`Orchestrating ${req.courses.length} courses`);

  const results: CoursePublishResult[] = [];
  let bundleResult: CoursePublishResult | undefined;

  for (const courseReq of req.courses) {
    try {
      // Generate course
      const { course } = await handleGenerateCourse({
        action: 'generate-course',
        courseTitle: courseReq.title,
        topic: courseReq.topic,
        level: courseReq.level,
        price: courseReq.price,
        moduleCount: courseReq.moduleCount || 3,
      });

      // Publish if requested
      if (req.publishToGumroad) {
        const { publishResult } = await handlePublishCourse({
          action: 'publish-course',
          course,
          setupEmailFunnel: req.setupEmailFunnel ?? false,
        });

        results.push(publishResult);
      } else {
        results.push({
          success: true,
          courseId: course.id,
          metadata: course,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      console.error(`Error processing course ${courseReq.title}: ${error}`);
      results.push({
        success: false,
        courseId: `course-${Date.now()}`,
        error: `Failed to process: ${error}`,
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Create and publish bundle if requested
  if (req.createBundle && results.length > 0) {
    try {
      const courseIds = results
        .filter((r) => r.success)
        .map((r) => r.courseId);

      const bundle = await handleCreateBundle({
        action: 'create-bundle',
        bundleTitle: `Complete Course Bundle (${courseIds.length} courses)`,
        courseIds,
        toolGuideIds: [],
        promptLibraryIds: [],
      });

      if (req.publishToGumroad) {
        bundleResult = await handlePublishBundle({
          action: 'publish-bundle',
          bundle,
        });
      }
    } catch (error) {
      console.warn(`Failed to create/publish bundle: ${error}`);
    }
  }

  return {
    courses: results,
    bundle: bundleResult,
    totalTime: results.length * 2, // Rough estimate
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN HANDLER
// ═══════════════════════════════════════════════════════════════════════════════

export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  const startTime = Date.now();

  try {
    const body = (await request.json()) as CourseAutomationRequest;

    console.log(`[${new Date().toISOString()}] Processing action: ${body.action}`);

    let result: unknown;

    switch (body.action) {
      case 'generate-course':
        result = await handleGenerateCourse(body as GenerateCourseRequest);
        break;

      case 'generate-prompts':
        result = await handleGeneratePrompts(body as GeneratePromptsRequest);
        break;

      case 'generate-tool-guide':
        result = await handleGenerateToolGuide(body as GenerateToolGuideRequest);
        break;

      case 'create-bundle':
        result = await handleCreateBundle(body as CreateBundleRequest);
        break;

      case 'publish-course':
        result = await handlePublishCourse(body as PublishCourseRequest);
        break;

      case 'publish-bundle':
        result = await handlePublishBundle(body as PublishBundleRequest);
        break;

      case 'setup-email-funnel':
        result = await handleSetupEmailFunnel(body as SetupEmailFunnelRequest);
        break;

      case 'get-performance':
        result = await handleGetPerformance(body as GetPerformanceRequest);
        break;

      case 'orchestrate':
        result = await handleOrchestrate(body as OrchestrateRequest);
        break;

      default:
        throw new Error(`Unknown action: ${body.action}`);
    }

    const duration = Date.now() - startTime;

    return NextResponse.json(
      {
        success: true,
        action: body.action,
        result,
        timestamp: new Date().toISOString(),
        duration,
      },
      { status: 200 }
    );
  } catch (error) {
    const duration = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : String(error);

    console.error(`[${new Date().toISOString()}] API Error: ${errorMessage}`);

    return NextResponse.json(
      {
        success: false,
        action: 'unknown',
        error: errorMessage,
        timestamp: new Date().toISOString(),
        duration,
      },
      { status: 500 }
    );
  }
}

/**
 * GET handler for health checks
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  return NextResponse.json(
    {
      status: 'ok',
      service: 'ai-courses-automation',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
    },
    { status: 200 }
  );
}

export {
  AICourseMeta,
  ChatGPTPromptLibrary,
  ToolGuide,
  CourseBundle,
  CourseEmail,
  CoursePublishResult,
  CoursePerformance,
};
