/**
 * AI TOOLS & COURSES AUTOMATION
 *
 * Auto-generate and package AI course bundles, ChatGPT prompt libraries, and tool guides:
 * - Generate course content using AI content templates
 * - Bundle courses with complementary tools and resources
 * - Create ChatGPT prompt libraries (structured JSON)
 * - Generate tool guides and quick-start documentation
 * - Auto-upload to Gumroad with pricing
 * - Setup email funnel automation
 * - Track course performance and engagement
 * - Generate affiliate links for recommended tools
 *
 * Environment Requirements:
 * - OPENAI_API_KEY: OpenAI API key for content generation
 * - GUMROAD_API_TOKEN: Gumroad API token
 * - GUMROAD_CREATOR_ID: Gumroad store username
 * - BREVO_API_KEY: Brevo email automation
 * - STRIPE_SECRET_KEY: Stripe integration for payments
 * - AMAZON_AFFILIATE_TAG: Amazon Associates tag
 *
 * File Structure:
 * - AI_COURSE_*.md: Course metadata and outline files
 * - AI_PROMPTS_*.json: ChatGPT prompt libraries
 * - AI_TOOL_GUIDES_*.md: Tool guides and tutorials
 */

import { readFile, writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPE DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════════

export interface CourseModule {
  id: string;
  title: string;
  description: string;
  duration: string; // "1 hour", "3 weeks", etc
  lessons: Lesson[];
  resources?: string[]; // URLs to resources
  exerciseCount?: number;
}

export interface Lesson {
  id: string;
  title: string;
  description: string;
  keyPoints: string[];
  examplePrompts?: string[];
  tools?: string[];
}

export interface AICourseMeta {
  id: string;
  title: string;
  subtitle?: string;
  description: string;
  longDescription?: string;
  category: 'prompt-engineering' | 'tool-guide' | 'bundle' | 'masterclass' | 'toolkit';
  level: 'beginner' | 'intermediate' | 'advanced';
  price: number;
  discountPrice?: number;
  duration: string;
  modules: CourseModule[];
  targetAudience: string[];
  learningOutcomes: string[];
  includedTools?: string[]; // Tool IDs included in bundle
  affiliateTools?: AffiliateToolLink[]; // Recommended tools with affiliate links
  tags: string[];
  imagePrompt?: string;
  certificateIncluded?: boolean;
  lifetimeAccess?: boolean;
}

export interface ChatGPTPromptLibrary {
  id: string;
  name: string;
  description: string;
  category: string;
  version: string;
  createdAt: string;
  updatedAt: string;
  totalPrompts: number;
  prompts: ChatGPTPrompt[];
  metadata?: {
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    useCases: string[];
    keywords: string[];
  };
}

export interface ChatGPTPrompt {
  id: string;
  title: string;
  description: string;
  systemPrompt: string;
  userPromptTemplate: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  useCases: string[];
  exampleInput?: string;
  exampleOutput?: string;
  parameters?: PromptParameter[];
  tags: string[];
}

export interface PromptParameter {
  name: string;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'list';
  required: boolean;
  defaultValue?: string | number | boolean;
}

export interface ToolGuide {
  id: string;
  toolName: string;
  description: string;
  category: string;
  setupSteps: SetupStep[];
  useCases: string[];
  tipsTricks: string[];
  integrations: ToolIntegration[];
  pricingTiers?: PricingTier[];
  affiliateLink?: string;
  resources?: {
    documentation?: string;
    videoTutorials?: string[];
    templates?: string[];
  };
}

export interface SetupStep {
  step: number;
  title: string;
  description: string;
  code?: string;
  screenshot?: string;
}

export interface ToolIntegration {
  integrationName: string;
  description: string;
  howToGuide: string;
  exampleUrl?: string;
}

export interface PricingTier {
  name: string;
  price: number;
  features: string[];
  recommended: boolean;
}

export interface AffiliateToolLink {
  toolName: string;
  affiliateUrl: string;
  description: string;
  commission?: string;
}

export interface CourseBundle {
  id: string;
  bundleTitle: string;
  description: string;
  courses: string[]; // Course IDs
  tools: ToolGuide[]; // Tool guides
  prompts: ChatGPTPromptLibrary[]; // Prompt libraries
  bundlePrice: number;
  individualPrice: number;
  discountPercentage: number;
  includedResources: string[];
  bonuses: BonusContent[];
}

export interface BonusContent {
  title: string;
  description: string;
  fileUrl?: string;
  content?: string;
  type: 'template' | 'checklist' | 'worksheet' | 'guide';
}

export interface CourseEmail {
  campaignId: string;
  courseId: string;
  emailSequence: EmailMessage[];
  triggerEvents: string[]; // e.g., ['purchase', 'module-complete', 'day-3']
}

export interface EmailMessage {
  sequence: number;
  subject: string;
  bodyText: string;
  bodyHtml: string;
  ctaText?: string;
  ctaLink?: string;
  sendAfter?: string; // ISO duration, e.g., "P0DT24H" (24 hours)
  condition?: string; // Segmentation condition
}

export interface CoursePublishResult {
  success: boolean;
  courseId: string;
  gumroadProductId?: string;
  gumroadUrl?: string;
  promptLibraryId?: string;
  emailCampaignId?: string;
  error?: string;
  metadata?: AICourseMeta;
  timestamp: string;
}

export interface CoursePerformance {
  courseId: string;
  courseName: string;
  totalSales: number;
  totalRevenue: number;
  conversionRate: number;
  averageRating?: number;
  reviewCount?: number;
  emailOpenRate?: number;
  emailClickRate?: number;
  affiliateCommissions?: number;
  lastUpdated: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONTENT GENERATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Generate course content using OpenAI
 */
export async function generateCourseContent(
  courseTitle: string,
  topic: string,
  level: 'beginner' | 'intermediate' | 'advanced',
  moduleCount: number = 3
): Promise<CourseModule[]> {
  const openaiKey = process.env.OPENAI_API_KEY;
  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const modules: CourseModule[] = [];

  for (let i = 1; i <= moduleCount; i++) {
    const prompt = `
Create a structured course module for: "${courseTitle}"
Module ${i}/${moduleCount}
Topic: ${topic}
Level: ${level}

Return a JSON object with this structure:
{
  "title": "Module title",
  "description": "Module description",
  "duration": "estimated time to complete",
  "lessons": [
    {
      "title": "Lesson title",
      "description": "Lesson description",
      "keyPoints": ["point 1", "point 2", "point 3"],
      "examplePrompts": ["prompt example 1", "prompt example 2"]
    }
  ]
}

Make it practical and immediately actionable. Include 3-4 lessons per module.
`;

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-4-turbo',
          messages: [
            {
              role: 'user',
              content: prompt,
            },
          ],
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        console.error(`OpenAI API error: ${error}`);
        continue;
      }

      const data = (await response.json()) as { choices: Array<{ message: { content: string } }> };
      const content = data.choices[0]?.message.content;

      if (!content) {
        console.warn(`No content generated for module ${i}`);
        continue;
      }

      // Parse JSON from response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        console.warn(`No JSON found in response for module ${i}`);
        continue;
      }

      const moduleData = JSON.parse(jsonMatch[0]);

      // Transform to CourseModule structure
      const module: CourseModule = {
        id: `module-${i}`,
        title: moduleData.title,
        description: moduleData.description,
        duration: moduleData.duration,
        lessons: moduleData.lessons.map((lesson: Record<string, unknown>, idx: number) => ({
          id: `lesson-${i}-${idx + 1}`,
          title: lesson.title,
          description: lesson.description,
          keyPoints: lesson.keyPoints,
          examplePrompts: lesson.examplePrompts,
        })),
      };

      modules.push(module);
    } catch (error) {
      console.error(`Error generating module ${i}: ${error}`);
    }
  }

  return modules;
}

/**
 * Generate ChatGPT prompt library
 */
export async function generatePromptLibrary(
  libraryName: string,
  category: string,
  promptCount: number = 10
): Promise<ChatGPTPromptLibrary> {
  const openaiKey = process.env.OPENAI_API_KEY;
  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompts: ChatGPTPrompt[] = [];

  for (let i = 1; i <= promptCount; i++) {
    const prompt = `
Generate a professional ChatGPT prompt for: ${category}
Prompt ${i}/${promptCount}

Return a JSON object with this structure:
{
  "title": "Prompt title",
  "description": "What this prompt does",
  "systemPrompt": "The system message to set context",
  "userPromptTemplate": "Template with {{variable}} placeholders",
  "category": "${category}",
  "difficulty": "beginner|intermediate|advanced",
  "useCases": ["use case 1", "use case 2"],
  "exampleInput": "Example input",
  "exampleOutput": "Expected output"
}

Make it production-ready and reusable.
`;

    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-4-turbo',
          messages: [
            {
              role: 'user',
              content: prompt,
            },
          ],
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        console.error(`OpenAI API error generating prompt ${i}`);
        continue;
      }

      const data = (await response.json()) as { choices: Array<{ message: { content: string } }> };
      const content = data.choices[0]?.message.content;

      if (!content) continue;

      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) continue;

      const promptData = JSON.parse(jsonMatch[0]);
      prompts.push({
        id: `prompt-${i}`,
        title: promptData.title,
        description: promptData.description,
        systemPrompt: promptData.systemPrompt,
        userPromptTemplate: promptData.userPromptTemplate,
        category: promptData.category,
        difficulty: promptData.difficulty,
        useCases: promptData.useCases,
        exampleInput: promptData.exampleInput,
        exampleOutput: promptData.exampleOutput,
        tags: [category],
      });
    } catch (error) {
      console.error(`Error generating prompt ${i}: ${error}`);
    }
  }

  return {
    id: `lib-${Date.now()}`,
    name: libraryName,
    description: `${promptCount} professional prompts for ${category}`,
    category,
    version: '1.0.0',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    totalPrompts: prompts.length,
    prompts,
    metadata: {
      difficulty: 'intermediate',
      useCases: [category],
      keywords: [category],
    },
  };
}

/**
 * Generate tool guide from tool information
 */
export async function generateToolGuide(
  toolName: string,
  toolDescription: string
): Promise<ToolGuide> {
  const openaiKey = process.env.OPENAI_API_KEY;
  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompt = `
Generate a comprehensive guide for using: ${toolName}
Description: ${toolDescription}

Return a JSON object with this structure:
{
  "setupSteps": [
    {
      "step": 1,
      "title": "Step title",
      "description": "Detailed instructions"
    }
  ],
  "useCases": ["use case 1", "use case 2", "use case 3"],
  "tipsTricks": ["tip 1", "tip 2", "tip 3"],
  "integrations": [
    {
      "integrationName": "Tool name",
      "description": "How it integrates",
      "howToGuide": "Step by step instructions"
    }
  ]
}

Make it beginner-friendly and actionable.
`;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openaiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4-turbo',
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`OpenAI API error: ${error}`);
    }

    const data = (await response.json()) as { choices: Array<{ message: { content: string } }> };
    const content = data.choices[0]?.message.content;

    if (!content) {
      throw new Error('No content generated');
    }

    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('No JSON found in response');
    }

    const guideData = JSON.parse(jsonMatch[0]);

    return {
      id: `guide-${Date.now()}`,
      toolName,
      description: toolDescription,
      category: 'AI Tools',
      setupSteps: guideData.setupSteps,
      useCases: guideData.useCases,
      tipsTricks: guideData.tipsTricks,
      integrations: guideData.integrations,
    };
  } catch (error) {
    throw new Error(`Failed to generate tool guide: ${error}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// BUNDLING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create a course bundle combining courses, tools, and prompts
 */
export function createCourseBundle(
  bundleTitle: string,
  courses: AICourseMeta[],
  toolGuides: ToolGuide[],
  promptLibraries: ChatGPTPromptLibrary[]
): CourseBundle {
  const individualPrice = courses.reduce((sum, course) => sum + course.price, 0);

  return {
    id: `bundle-${Date.now()}`,
    bundleTitle,
    description: `Complete bundle: ${courses.length} courses, ${toolGuides.length} tools, ${promptLibraries.length} prompt libraries`,
    courses: courses.map((c) => c.id),
    tools: toolGuides,
    prompts: promptLibraries,
    bundlePrice: Math.floor(individualPrice * 0.7), // 30% discount
    individualPrice,
    discountPercentage: 30,
    includedResources: [
      'Lifetime access to all courses',
      'Monthly updates and new content',
      'Private community access',
      'Email support',
      'Certificate of completion',
    ],
    bonuses: [
      {
        title: 'AI Tools Comparison Guide',
        description: 'Detailed comparison of 50+ AI tools',
        type: 'guide',
      },
      {
        title: 'Prompting Playbook',
        description: '100+ tested prompts for every use case',
        type: 'template',
      },
      {
        title: 'Weekly Tips & Tricks',
        description: 'Email newsletter with latest AI strategies',
        type: 'guide',
      },
    ],
  };
}

/**
 * Add affiliate links to course
 */
export function addAffiliateLinksToCourseMeta(
  course: AICourseMeta,
  tools: AffiliateToolLink[]
): AICourseMeta {
  return {
    ...course,
    affiliateTools: tools,
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// GUMROAD INTEGRATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Upload course to Gumroad
 */
export async function publishCourseToGumroad(course: AICourseMeta): Promise<CoursePublishResult> {
  const apiToken = process.env.GUMROAD_API_TOKEN;
  const creatorId = process.env.GUMROAD_CREATOR_ID;

  if (!apiToken || !creatorId) {
    return {
      success: false,
      courseId: course.id,
      error: 'GUMROAD_API_TOKEN or GUMROAD_CREATOR_ID not configured',
      timestamp: new Date().toISOString(),
    };
  }

  try {
    // Format course content as product description
    const description = formatCourseDescription(course);

    // Create product on Gumroad
    const response = await fetch('https://api.gumroad.com/v2/products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        access_token: apiToken,
        name: course.title,
        description,
        price: course.price.toString(),
        currency: 'usd',
        category: 'online-courses',
        tags: course.tags.join(','),
        published: 'true',
      }).toString(),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        success: false,
        courseId: course.id,
        error: `Gumroad API error: ${error}`,
        timestamp: new Date().toISOString(),
      };
    }

    const data = (await response.json()) as {
      product: { id: string; url: string };
    };

    return {
      success: true,
      courseId: course.id,
      gumroadProductId: data.product.id,
      gumroadUrl: data.product.url,
      metadata: course,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      courseId: course.id,
      error: `Publish failed: ${error}`,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Upload bundle to Gumroad
 */
export async function publishBundleToGumroad(bundle: CourseBundle): Promise<CoursePublishResult> {
  const apiToken = process.env.GUMROAD_API_TOKEN;
  const creatorId = process.env.GUMROAD_CREATOR_ID;

  if (!apiToken || !creatorId) {
    return {
      success: false,
      courseId: bundle.id,
      error: 'GUMROAD_API_TOKEN or GUMROAD_CREATOR_ID not configured',
      timestamp: new Date().toISOString(),
    };
  }

  try {
    const description = formatBundleDescription(bundle);

    const response = await fetch('https://api.gumroad.com/v2/products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        access_token: apiToken,
        name: bundle.bundleTitle,
        description,
        price: bundle.bundlePrice.toString(),
        currency: 'usd',
        category: 'online-courses',
        published: 'true',
      }).toString(),
    });

    if (!response.ok) {
      const error = await response.text();
      return {
        success: false,
        courseId: bundle.id,
        error: `Gumroad API error: ${error}`,
        timestamp: new Date().toISOString(),
      };
    }

    const data = (await response.json()) as {
      product: { id: string; url: string };
    };

    return {
      success: true,
      courseId: bundle.id,
      gumroadProductId: data.product.id,
      gumroadUrl: data.product.url,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      courseId: bundle.id,
      error: `Bundle publish failed: ${error}`,
      timestamp: new Date().toISOString(),
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// EMAIL FUNNEL AUTOMATION
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create email sequence for course
 */
export function createCourseEmailSequence(courseId: string, courseName: string): CourseEmail {
  const emailSequence: EmailMessage[] = [
    {
      sequence: 1,
      subject: `Welcome to ${courseName}! Your Access Granted`,
      bodyText: `Congratulations on purchasing ${courseName}!

You now have lifetime access to all course materials, tools, and prompts.

Getting started:
1. Visit your account dashboard
2. Download all course modules
3. Join our private community
4. Set up your favorite AI tools

First lesson: Getting Started with AI`,
      bodyHtml: `<p>Congratulations on purchasing <strong>${courseName}</strong>!</p>
<p>You now have lifetime access to all course materials, tools, and prompts.</p>
<h3>Getting started:</h3>
<ol>
  <li>Visit your account dashboard</li>
  <li>Download all course modules</li>
  <li>Join our private community</li>
  <li>Set up your favorite AI tools</li>
</ol>`,
      ctaText: 'Start Learning Now',
      ctaLink: 'https://profitengine-tau.vercel.app/courses/access',
      sendAfter: 'PT1H', // Send 1 hour after purchase
    },
    {
      sequence: 2,
      subject: `Module 1 Complete? Here's What's Next`,
      bodyText: `Great work on completing Module 1!

Now that you understand the fundamentals, Module 2 dives into advanced techniques.

What's in Module 2:
- Real-world case studies
- Advanced prompting strategies
- Tool integrations
- Live Q&A session recording`,
      bodyHtml: `<p>Great work on completing Module 1!</p>
<p>Module 2 is now available with advanced techniques and real-world applications.</p>`,
      ctaText: 'Start Module 2',
      ctaLink: 'https://profitengine-tau.vercel.app/courses/module-2',
      sendAfter: 'P2D', // Send 2 days after module 1 completion
      condition: 'module-1-complete',
    },
    {
      sequence: 3,
      subject: `Your ${courseName} Bonus Pack is Ready`,
      bodyText: `As a ${courseName} student, you get exclusive bonuses:

1. AI Tools Comparison Guide (50+ tools reviewed)
2. Prompting Playbook (100+ tested prompts)
3. Weekly Tips & Tricks newsletter
4. Private Discord community access

Download them now before they're gone.`,
      bodyHtml: `<p>As a <strong>${courseName}</strong> student, you've unlocked exclusive bonuses:</p>
<ul>
  <li>AI Tools Comparison Guide (50+ tools reviewed)</li>
  <li>Prompting Playbook (100+ tested prompts)</li>
  <li>Weekly Tips & Tricks newsletter</li>
  <li>Private Discord community access</li>
</ul>`,
      ctaText: 'Access My Bonuses',
      ctaLink: 'https://profitengine-tau.vercel.app/courses/bonuses',
      sendAfter: 'P5D', // Send 5 days after purchase
    },
    {
      sequence: 4,
      subject: `${courseName} Graduation Survey - Help Shape Future Content`,
      bodyText: `You're officially a ${courseName} graduate!

To help us create even better courses, please take 2 minutes to answer 5 quick questions.

Your feedback helps us:
- Improve existing content
- Create new courses
- Build tools you actually need
- Build community

Survey takes ~2 minutes.`,
      bodyHtml: `<p>You're officially a <strong>${courseName}</strong> graduate!</p>
<p>Help us create even better courses with a quick 2-minute survey.</p>`,
      ctaText: 'Take the Survey',
      ctaLink: 'https://profitengine-tau.vercel.app/courses/feedback',
      sendAfter: 'P14D', // Send 14 days after purchase
      condition: 'course-complete',
    },
    {
      sequence: 5,
      subject: `Get ${courseName} + 3 More Courses (Save 30%)`,
      bodyText: `You loved ${courseName}.

We've bundled it with 3 more advanced courses for 30% off. Bundle includes:

- ${courseName}
- Advanced AI Strategies Course
- Prompt Engineering Masterclass
- AI Tools Bundle

$99 bundle vs $142 individual = Save $43`,
      bodyHtml: `<p>Love <strong>${courseName}</strong>? You'll love our bundle!</p>
<p>Save 30% on 4 courses: $99 instead of $142</p>`,
      ctaText: 'View Bundle Deal',
      ctaLink: 'https://profitengine-tau.vercel.app/courses/bundle',
      sendAfter: 'P21D', // Send 21 days after purchase
    },
  ];

  return {
    campaignId: `campaign-${Date.now()}`,
    courseId,
    emailSequence,
    triggerEvents: ['purchase', 'module-complete', 'course-complete'],
  };
}

/**
 * Setup email campaign with Brevo
 */
export async function setupEmailCampaignBrevo(courseEmail: CourseEmail): Promise<string> {
  const brevoKey = process.env.BREVO_API_KEY;

  if (!brevoKey) {
    throw new Error('BREVO_API_KEY not configured');
  }

  try {
    // Create contact list
    const listResponse = await fetch('https://api.brevo.com/v3/contacts/lists', {
      method: 'POST',
      headers: {
        'api-key': brevoKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: `${courseEmail.courseId}-subscribers`,
        description: `Subscribers to course ${courseEmail.courseId}`,
      }),
    });

    if (!listResponse.ok) {
      throw new Error(`Failed to create contact list`);
    }

    const listData = (await listResponse.json()) as { id: number };

    // Create automation workflow
    const automationResponse = await fetch('https://api.brevo.com/v3/automations', {
      method: 'POST',
      headers: {
        'api-key': brevoKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: `${courseEmail.courseId}-automation`,
        enabled: true,
        trigger: {
          type: 'contact_added',
          listId: listData.id,
        },
        steps: courseEmail.emailSequence.map((email) => ({
          type: 'email',
          delay: email.sendAfter || 'PT0H',
          email: {
            subject: email.subject,
            content: email.bodyHtml || email.bodyText,
            fromName: 'ProfitEngine AI Academy',
            fromEmail: 'courses@profitengine-tau.vercel.app',
          },
        })),
      }),
    });

    if (!automationResponse.ok) {
      const error = await automationResponse.text();
      throw new Error(`Failed to create automation: ${error}`);
    }

    const automationData = (await automationResponse.json()) as { id: string };
    return automationData.id;
  } catch (error) {
    throw new Error(`Email campaign setup failed: ${error}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// FILE PARSING & PERSISTENCE
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Parse course metadata from AI_COURSE_*.md file
 */
export async function parseCourseMeta(filePath: string): Promise<AICourseMeta> {
  try {
    const content = await readFile(filePath, 'utf-8');
    const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);

    const metadata: Partial<AICourseMeta> = {
      id: path.basename(filePath, '.md'),
      category: 'prompt-engineering',
      level: 'intermediate',
      modules: [],
      targetAudience: [],
      learningOutcomes: [],
      tags: [],
    };

    if (yamlMatch) {
      const yaml = yamlMatch[1];

      // Simple YAML front matter parsing
      const titleMatch = yaml.match(/title:\s*["']?(.+?)["']?$/m);
      if (titleMatch) metadata.title = titleMatch[1];

      const descMatch = yaml.match(/description:\s*["']?(.+?)["']?$/m);
      if (descMatch) metadata.description = descMatch[1];

      const priceMatch = yaml.match(/price:\s*([\d.]+)/);
      if (priceMatch) metadata.price = parseFloat(priceMatch[1]);

      const levelMatch = yaml.match(/level:\s*["']?(.+?)["']?$/m);
      if (levelMatch) metadata.level = levelMatch[1] as 'beginner' | 'intermediate' | 'advanced';

      const categoryMatch = yaml.match(/category:\s*["']?(.+?)["']?$/m);
      if (categoryMatch) metadata.category = categoryMatch[1] as AICourseMeta['category'];

      const tagsMatch = yaml.match(/tags:\s*\[(.*?)\]/);
      if (tagsMatch) {
        metadata.tags = tagsMatch[1]
          .split(',')
          .map((t) => t.trim().replace(/["']/g, ''));
      }
    }

    return metadata as AICourseMeta;
  } catch (error) {
    throw new Error(`Failed to parse course metadata: ${error}`);
  }
}

/**
 * Save prompt library to JSON file
 */
export async function savePromptLibrary(
  library: ChatGPTPromptLibrary,
  outputDir: string = '.runtime/ai-courses'
): Promise<string> {
  try {
    // Ensure directory exists
    if (!existsSync(outputDir)) {
      await mkdir(outputDir, { recursive: true });
    }

    const filename = path.join(outputDir, `PROMPTS_${library.id}.json`);
    await writeFile(filename, JSON.stringify(library, null, 2), 'utf-8');

    return filename;
  } catch (error) {
    throw new Error(`Failed to save prompt library: ${error}`);
  }
}

/**
 * Save tool guide to file
 */
export async function saveToolGuide(
  guide: ToolGuide,
  outputDir: string = '.runtime/ai-courses'
): Promise<string> {
  try {
    if (!existsSync(outputDir)) {
      await mkdir(outputDir, { recursive: true });
    }

    const filename = path.join(outputDir, `GUIDE_${guide.id}.json`);
    await writeFile(filename, JSON.stringify(guide, null, 2), 'utf-8');

    return filename;
  } catch (error) {
    throw new Error(`Failed to save tool guide: ${error}`);
  }
}

/**
 * Save course bundle to file
 */
export async function saveCourseBundle(
  bundle: CourseBundle,
  outputDir: string = '.runtime/ai-courses'
): Promise<string> {
  try {
    if (!existsSync(outputDir)) {
      await mkdir(outputDir, { recursive: true });
    }

    const filename = path.join(outputDir, `BUNDLE_${bundle.id}.json`);
    await writeFile(filename, JSON.stringify(bundle, null, 2), 'utf-8');

    return filename;
  } catch (error) {
    throw new Error(`Failed to save course bundle: ${error}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ANALYTICS & REPORTING
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get course performance metrics from Gumroad
 */
export async function getCoursePerformance(
  courseId: string,
  gumroadProductId: string
): Promise<CoursePerformance> {
  const apiToken = process.env.GUMROAD_API_TOKEN;

  if (!apiToken) {
    throw new Error('GUMROAD_API_TOKEN not configured');
  }

  try {
    const response = await fetch(
      `https://api.gumroad.com/v2/products/${gumroadProductId}/summary`,
      {
        headers: {
          'Authorization': `Bearer ${apiToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch Gumroad product data');
    }

    const data = (await response.json()) as {
      product: {
        name: string;
        sales_count: number;
        sales_revenue: number;
      };
    };

    return {
      courseId,
      courseName: data.product.name,
      totalSales: data.product.sales_count,
      totalRevenue: data.product.sales_revenue,
      conversionRate: 0.02, // Placeholder - calculate from analytics
      lastUpdated: new Date().toISOString(),
    };
  } catch (error) {
    throw new Error(`Failed to get course performance: ${error}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

function formatCourseDescription(course: AICourseMeta): string {
  let description = `${course.description}\n\n`;

  description += `Level: ${course.level}\n`;
  description += `Duration: ${course.duration}\n`;

  if (course.learningOutcomes.length > 0) {
    description += `\nWhat You'll Learn:\n`;
    course.learningOutcomes.forEach((outcome) => {
      description += `• ${outcome}\n`;
    });
  }

  if (course.modules.length > 0) {
    description += `\nCourse Modules:\n`;
    course.modules.forEach((module) => {
      description += `\n${module.title}\n`;
      description += `${module.description}\n`;
    });
  }

  if (course.certificateIncluded) {
    description += `\nIncludes certificate of completion.\n`;
  }

  if (course.lifetimeAccess) {
    description += `Lifetime access to all course materials.\n`;
  }

  return description;
}

function formatBundleDescription(bundle: CourseBundle): string {
  let description = `${bundle.description}\n\n`;
  description += `Regular Price: $${bundle.individualPrice}\n`;
  description += `Bundle Price: $${bundle.bundlePrice} (${bundle.discountPercentage}% off)\n`;

  if (bundle.courses.length > 0) {
    description += `\nIncluded Courses: ${bundle.courses.length} courses\n`;
  }

  if (bundle.tools.length > 0) {
    description += `\nTool Guides: ${bundle.tools.length} tools\n`;
  }

  if (bundle.prompts.length > 0) {
    description += `\nPrompt Libraries: ${bundle.prompts.length} libraries\n`;
  }

  if (bundle.bonuses.length > 0) {
    description += `\nBonus Content:\n`;
    bundle.bonuses.forEach((bonus) => {
      description += `• ${bonus.title}: ${bonus.description}\n`;
    });
  }

  return description;
}

export {
  CourseModule,
  Lesson,
  CourseEmail,
  EmailMessage,
  AffiliateToolLink,
};
