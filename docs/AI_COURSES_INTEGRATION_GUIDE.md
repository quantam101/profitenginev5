# AI Courses Automation - Integration Guide

Complete guide for integrating AI Courses automation into your application.

## TypeScript Types Export

All TypeScript types are exported from `@/app/lib/automation/ai-courses`:

```typescript
import {
  AICourseMeta,
  ChatGPTPromptLibrary,
  ChatGPTPrompt,
  ToolGuide,
  CourseBundle,
  CourseEmail,
  CoursePublishResult,
  CoursePerformance,
  // Functions
  generateCourseContent,
  generatePromptLibrary,
  generateToolGuide,
  createCourseBundle,
  publishCourseToGumroad,
  publishBundleToGumroad,
  createCourseEmailSequence,
  setupEmailCampaignBrevo,
  getCoursePerformance,
} from '@/app/lib/automation/ai-courses';
```

## Server-Side Integration

### 1. Direct Function Calls

Use the library functions directly in your Next.js server code:

```typescript
import { generateCourseContent, publishCourseToGumroad } from '@/app/lib/automation/ai-courses';

// In your server action or API route
export async function createAndPublishCourse(title: string, topic: string, price: number) {
  try {
    // Generate course content
    const modules = await generateCourseContent(title, topic, 'beginner', 3);
    
    // Create course object
    const course = {
      id: `course-${Date.now()}`,
      title,
      description: topic,
      category: 'prompt-engineering',
      level: 'beginner' as const,
      price,
      duration: '6 hours',
      modules,
      targetAudience: [],
      learningOutcomes: [],
      tags: [topic],
    };
    
    // Publish to Gumroad
    const result = await publishCourseToGumroad(course);
    
    return result;
  } catch (error) {
    console.error('Failed to create course:', error);
    throw error;
  }
}
```

### 2. Database Integration

Store course data and metadata in your database:

```typescript
import { db } from '@/app/lib/db';

interface StoredCourse {
  id: string;
  title: string;
  topic: string;
  price: number;
  gumroadProductId: string;
  gumroadUrl: string;
  emailCampaignId: string;
  createdAt: Date;
  publishedAt: Date;
  totalSales: number;
  totalRevenue: number;
}

export async function saveCourseToDatabase(result: CoursePublishResult) {
  await db.course.create({
    data: {
      id: result.courseId,
      title: result.metadata?.title || '',
      gumroadProductId: result.gumroadProductId,
      gumroadUrl: result.gumroadUrl,
      createdAt: new Date(),
      publishedAt: new Date(),
    },
  });
}
```

### 3. Event Tracking

Track course automation events for analytics:

```typescript
import { trackEvent } from '@/app/lib/analytics';

export async function handleCoursePublished(result: CoursePublishResult) {
  // Track in analytics
  await trackEvent('course_published', {
    courseId: result.courseId,
    courseName: result.metadata?.title,
    price: result.metadata?.price,
    gumroadUrl: result.gumroadUrl,
    timestamp: new Date(),
  });
  
  // Send notification
  await notifyAdmins(`New course published: ${result.metadata?.title}`);
  
  // Update user dashboard
  await updateUserDashboard(result.courseId);
}
```

## Client-Side Integration

### 1. React Component for Course Generation

```typescript
'use client';

import { useState } from 'react';
import { generateCourseContent } from '@/app/lib/automation/ai-courses';

export function CourseGenerator() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    topic: '',
    level: 'beginner' as const,
    price: 47,
  });
  const [result, setResult] = useState(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('/api/automation/ai-courses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generate-course',
          ...formData,
        }),
      });
      
      const data = await response.json();
      setResult(data.result);
    } catch (error) {
      console.error('Failed to generate course:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleGenerate}>
      <input
        type="text"
        placeholder="Course Title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
      />
      <textarea
        placeholder="Course Topic"
        value={formData.topic}
        onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
      />
      <select
        value={formData.level}
        onChange={(e) => setFormData({ ...formData, level: e.target.value })}
      >
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </select>
      <input
        type="number"
        placeholder="Price"
        value={formData.price}
        onChange={(e) => setFormData({ ...formData, price: parseInt(e.target.value) })}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate Course'}
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </form>
  );
}
```

### 2. Course Dashboard

```typescript
'use client';

import { useState, useEffect } from 'react';
import { CoursePerformance } from '@/app/lib/automation/ai-courses';

export function CourseDashboard() {
  const [courses, setCourses] = useState<CoursePerformance[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerformance = async () => {
      const response = await fetch('/api/user/courses/performance');
      const data = await response.json();
      setCourses(data.courses);
      setLoading(false);
    };

    fetchPerformance();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      {courses.map((course) => (
        <div key={course.courseId} className="course-card">
          <h3>{course.courseName}</h3>
          <p>Sales: {course.totalSales}</p>
          <p>Revenue: ${course.totalRevenue}</p>
          <p>Conversion: {(course.conversionRate * 100).toFixed(1)}%</p>
          <p>Rating: {course.averageRating}/5 ({course.reviewCount} reviews)</p>
          <p>Email Open Rate: {course.emailOpenRate}%</p>
        </div>
      ))}
    </div>
  );
}
```

## Webhook Integration

### Gumroad Webhooks

Handle course purchases via Gumroad webhooks:

```typescript
// app/api/webhooks/gumroad/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();

  if (body.type === 'purchase') {
    // Send welcome email
    await sendWelcomeEmail(body.email, body.product_id);
    
    // Add to email list
    await addToBrevoContact(body.email, body.product_id);
    
    // Track purchase
    await trackPurchase(body.product_id, body.price);
    
    // Grant course access
    await grantCourseAccess(body.email, body.product_id);
  }

  return NextResponse.json({ success: true });
}
```

### Stripe Webhooks

If using Stripe directly:

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: NextRequest) {
  const sig = request.headers.get('stripe-signature')!;
  const body = await request.text();

  try {
    const event = stripe.webhooks.constructEvent(
      body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );

    if (event.type === 'checkout.session.completed') {
      const session = event.data.object as Stripe.Checkout.Session;
      
      // Trigger course delivery
      await deliverCourse(
        session.customer_email!,
        session.metadata?.courseId!
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: 'Webhook failed' }, { status: 400 });
  }
}
```

## Email Template Integration

### Custom Email Template System

```typescript
import { CourseEmail } from '@/app/lib/automation/ai-courses';

interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  bodyHtml: string;
  variables: string[];
}

export function customizeEmailSequence(
  baseSequence: CourseEmail,
  template: EmailTemplate
): CourseEmail {
  return {
    ...baseSequence,
    emailSequence: baseSequence.emailSequence.map((email, idx) => ({
      ...email,
      subject: applyVariables(template.subject, { course: baseSequence.courseId }),
      bodyHtml: applyVariables(template.bodyHtml, { course: baseSequence.courseId }),
    })),
  };
}

function applyVariables(text: string, variables: Record<string, string>): string {
  return text.replace(/{{(\w+)}}/g, (match, key) => variables[key] || match);
}
```

## Performance Optimization

### Caching Course Data

```typescript
import { cache } from 'react';

// Cache course data for 5 minutes
export const getCachedCoursePerformance = cache(async (courseId: string) => {
  const response = await fetch(`/api/courses/${courseId}/performance`, {
    next: { revalidate: 300 }, // 5 minutes
  });
  return response.json();
});
```

### Batch Operations

```typescript
export async function batchGenerateCourses(
  courseRequests: Array<{ title: string; topic: string; price: number }>
) {
  const results = await Promise.all(
    courseRequests.map((req) =>
      fetch('/api/automation/ai-courses', {
        method: 'POST',
        body: JSON.stringify({
          action: 'generate-course',
          ...req,
        }),
      }).then((r) => r.json())
    )
  );
  return results;
}
```

## Error Handling

### Robust Error Management

```typescript
export class CourseAutomationError extends Error {
  constructor(
    public action: string,
    public details: unknown,
    message: string
  ) {
    super(message);
    this.name = 'CourseAutomationError';
  }
}

export async function generateCourseWithRetry(
  title: string,
  topic: string,
  maxRetries = 3
) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await generateCourseContent(title, topic, 'beginner');
    } catch (error) {
      if (attempt === maxRetries) {
        throw new CourseAutomationError(
          'generate-course',
          error,
          `Failed to generate course after ${maxRetries} attempts`
        );
      }
      // Exponential backoff
      await new Promise((resolve) => 
        setTimeout(resolve, Math.pow(2, attempt) * 1000)
      );
    }
  }
}
```

## Monitoring & Logging

### Structured Logging

```typescript
import { logger } from '@/app/lib/logger';

export async function publishCourseWithLogging(course: AICourseMeta) {
  const startTime = Date.now();
  
  try {
    logger.info('Publishing course', {
      courseId: course.id,
      title: course.title,
      price: course.price,
    });

    const result = await publishCourseToGumroad(course);

    logger.info('Course published successfully', {
      courseId: course.id,
      gumroadProductId: result.gumroadProductId,
      duration: Date.now() - startTime,
    });

    return result;
  } catch (error) {
    logger.error('Failed to publish course', {
      courseId: course.id,
      error: error instanceof Error ? error.message : String(error),
      duration: Date.now() - startTime,
    });
    throw error;
  }
}
```

## Testing

### Unit Tests

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { createCourseBundle } from '@/app/lib/automation/ai-courses';

describe('AI Courses Automation', () => {
  it('should create bundle with correct discount', () => {
    const courses = [
      { id: 'c1', title: 'Course 1', price: 97, modules: [], targetAudience: [], learningOutcomes: [], tags: [], category: 'prompt-engineering', level: 'beginner', description: '' },
      { id: 'c2', title: 'Course 2', price: 97, modules: [], targetAudience: [], learningOutcomes: [], tags: [], category: 'prompt-engineering', level: 'beginner', description: '' },
    ];

    const bundle = createCourseBundle('Bundle', courses, [], []);

    expect(bundle.individualPrice).toBe(194);
    expect(bundle.bundlePrice).toBe(Math.floor(194 * 0.7));
    expect(bundle.discountPercentage).toBe(30);
  });

  it('should generate email sequence with correct count', () => {
    const emailSequence = createCourseEmailSequence('course-1', 'Test Course');
    expect(emailSequence.emailSequence).toHaveLength(5);
  });
});
```

## API Rate Limiting

### Implement Rate Limiting

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '1 h'),
  analytics: true,
  prefix: 'ai-courses',
});

export async function POST(request: NextRequest) {
  const ip = request.headers.get('x-forwarded-for');
  const { success } = await ratelimit.limit(ip || 'anonymous');

  if (!success) {
    return NextResponse.json(
      { error: 'Rate limit exceeded' },
      { status: 429 }
    );
  }

  // ... continue with request
}
```

## Scheduled Tasks

### Automated Course Generation

```typescript
// Using a cron service like Vercel Cron or node-cron
import { schedule } from 'node-cron';

// Generate and publish a course every Friday at 10 AM
schedule('0 10 * * 5', async () => {
  const courses = [
    {
      title: 'Weekly Course: AI Trends',
      topic: 'Latest AI trends and breakthroughs',
      level: 'intermediate' as const,
      price: 47,
    },
  ];

  const result = await fetch('http://localhost:3000/api/automation/ai-courses', {
    method: 'POST',
    body: JSON.stringify({
      action: 'orchestrate',
      courses,
      publishToGumroad: true,
      setupEmailFunnel: true,
    }),
  }).then((r) => r.json());

  console.log('Weekly course published:', result);
});
```

## Documentation Generation

### Auto-generate API Docs

```typescript
export function generateOpenAPISchema() {
  return {
    openapi: '3.0.0',
    info: {
      title: 'AI Courses Automation API',
      version: '1.0.0',
    },
    paths: {
      '/api/automation/ai-courses': {
        post: {
          summary: 'Trigger course automation',
          requestBody: {
            content: {
              'application/json': {
                schema: {
                  oneOf: [
                    { $ref: '#/components/schemas/GenerateCourseRequest' },
                    { $ref: '#/components/schemas/PublishCourseRequest' },
                    // ... other action schemas
                  ],
                },
              },
            },
          },
          responses: {
            '200': {
              description: 'Success',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/ApiResponse' },
                },
              },
            },
          },
        },
      },
    },
  };
}
```

## Summary

The AI Courses Automation system integrates seamlessly with:

- ✅ Next.js 15 server components and API routes
- ✅ React client components
- ✅ Gumroad webhooks for purchase handling
- ✅ Brevo for email automation
- ✅ OpenAI APIs for content generation
- ✅ MongoDB/PostgreSQL for data storage
- ✅ Stripe for alternative payment processing
- ✅ Analytics tracking and monitoring
- ✅ Scheduled tasks and cron jobs
- ✅ TypeScript for type safety

For more details, see:
- Main implementation: `/app/lib/automation/ai-courses.ts`
- API route: `/app/api/automation/ai-courses/route.ts`
- Examples: `/examples/AI_COURSES_EXAMPLES.md`
- Quick reference: `/docs/AI_COURSES_QUICK_REFERENCE.md`
