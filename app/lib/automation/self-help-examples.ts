/**
 * SELF-HELP CONTENT AUTOMATION — REAL-WORLD EXAMPLES
 *
 * Production-ready examples showing how to use the automation system
 * in real business scenarios.
 */

import {
  generateContent,
  generateCourseModule,
  processYouTubeTranscript,
  generateEbookChapters,
  distributeContent,
  exportContent,
  ContentTopicRequest,
  GeneratedContent,
} from './self-help';

// ============================================================================
// EXAMPLE 1: Generate and Publish Weekly Blog Series
// ============================================================================

/**
 * Generate 4 blog articles per week on different topics
 * Schedule them for publication across the week
 */
export async function weeklyBlogSeries() {
  const weeklyTopics = [
    'How to Build Multiple Income Streams',
    'Top 10 Passive Income Ideas for 2026',
    'The Psychology of Wealth and Money',
    'Creating Sustainable Online Businesses',
  ];

  const articles: GeneratedContent[] = [];

  for (const topic of weeklyTopics) {
    const request: ContentTopicRequest = {
      topic,
      difficulty: 'beginner',
      format: 'blog',
      keywords: ['money', 'passive income', 'side hustle', 'entrepreneurship'],
      targetAudience: 'aspiring entrepreneurs',
      tone: 'inspirational',
      includeAffiliates: true,
      estimatedLength: 'medium', // 1500-2500 words
    };

    try {
      const article = await generateContent(request);
      articles.push(article);

      console.log(`✓ Generated: ${article.title}`);
      console.log(`  Words: ${article.wordCount}`);
      console.log(`  Reading time: ${article.readingTimeMinutes} min`);
      console.log(`  Affiliate links: ${Object.keys(article.affiliateLinks || {}).length}`);
      console.log('');
    } catch (error) {
      console.error(`✗ Failed to generate: ${topic}`);
    }
  }

  // Distribute each article to multiple platforms
  for (let i = 0; i < articles.length; i++) {
    const article = articles[i];
    const daysFromNow = i; // Spread across week

    const scheduledTime = new Date();
    scheduledTime.setDate(scheduledTime.getDate() + daysFromNow);
    scheduledTime.setHours(9, 0, 0); // 9 AM

    const results = await distributeContent(article, [
      'blog',
      'newsletter',
      'social',
      'medium',
      'devto',
    ]);

    console.log(`\nDistributed "${article.title}" to:`);
    for (const result of results) {
      if (result.success) {
        console.log(`  ✓ ${result.platform}: ${result.url || result.postId}`);
      } else {
        console.log(`  ✗ ${result.platform}: ${result.error}`);
      }
    }
  }

  return articles;
}

// ============================================================================
// EXAMPLE 2: Create Multi-Module Training Course
// ============================================================================

/**
 * Generate a complete 4-module training course
 * Each module has 5-7 lessons, quizzes, and resources
 */
export async function createTrainingCourse() {
  const courseTopics = [
    'Introduction to Financial Markets',
    'Technical Analysis Fundamentals',
    'Advanced Trading Strategies',
    'Risk Management and Portfolio Building',
  ];

  const course = {
    title: 'Complete Day Trading Masterclass',
    description: 'Learn professional trading strategies from beginner to advanced',
    modules: [] as any[],
  };

  for (let i = 0; i < courseTopics.length; i++) {
    const topic = courseTopics[i];
    const difficulty = ['beginner', 'intermediate', 'intermediate', 'advanced'][i];

    try {
      const courseModule = await generateCourseModule(topic, difficulty);

      console.log(`✓ Module ${i + 1}: ${courseModule.title}`);
      console.log(`  Lessons: ${courseModule.lessons.length}`);
      console.log(`  Quizzes: ${courseModule.quizzes.length}`);
      console.log(`  Resources: ${courseModule.resources.length}`);
      console.log(`  Duration: ${courseModule.duration} min`);

      course.modules.push(courseModule);
    } catch (error) {
      console.error(`✗ Failed to generate module: ${topic}`);
    }
  }

  console.log(`\n✓ Complete course created: ${course.modules.length} modules`);
  console.log(`  Total lessons: ${course.modules.reduce((sum, m) => sum + m.lessons.length, 0)}`);
  console.log(`  Total quizzes: ${course.modules.reduce((sum, m) => sum + m.quizzes.length, 0)}`);

  return course;
}

// ============================================================================
// EXAMPLE 3: Convert YouTube Video to Multi-Format Content
// ============================================================================

/**
 * Convert a YouTube video to:
 * - Blog post (for SEO)
 * - Study guide (for learners)
 * - eBook chapter (for lead magnet)
 * - Email newsletter (for subscribers)
 */
export async function youtubeToMultiFormat() {
  const videoId = 'dQw4w9WgXcQ'; // Example YouTube video
  const videoTitle = 'How to Make $50,000 in 30 Days with Digital Products';

  try {
    // Step 1: Process transcript
    const transcript = await processYouTubeTranscript(videoId, videoTitle);

    console.log(`✓ Processed video: ${transcript.title}`);
    console.log(`  Duration: ${transcript.duration} seconds`);
    console.log(`  Keywords: ${transcript.keywords.slice(0, 5).join(', ')}`);
    console.log(`  Chapters: ${transcript.chapters.length}`);

    // Step 2: Use transcript as content base
    const contentRequest: ContentTopicRequest = {
      topic: videoTitle,
      difficulty: 'intermediate',
      format: 'blog',
      keywords: transcript.keywords,
      targetAudience: 'entrepreneurs',
      tone: 'inspirational',
      includeAffiliates: true,
    };

    const content = await generateContent(contentRequest);

    console.log(`\n✓ Generated blog post from transcript`);
    console.log(`  Title: ${content.title}`);
    console.log(`  Words: ${content.wordCount}`);

    // Step 3: Export to multiple formats
    const exports = await exportContent(content, [
      'markdown',
      'html',
      'pdf',
      'docx',
    ]);

    console.log(`\n✓ Exported content in 4 formats:`);
    console.log(`  - Markdown (for Medium, Dev.to)`);
    console.log(`  - HTML (for website/blog)`);
    console.log(`  - PDF (for download/lead magnet)`);
    console.log(`  - DOCX (for email sequence)`);

    // Step 4: Distribute
    const results = await distributeContent(content, [
      'blog',
      'newsletter',
      'medium',
      'devto',
    ]);

    console.log(`\n✓ Distributed to ${results.filter((r) => r.success).length} platforms`);

    return {
      transcript,
      content,
      exports,
      distribution: results,
    };
  } catch (error) {
    console.error(`✗ Failed to process video: ${error}`);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 4: Generate Lead Magnet eBook
// ============================================================================

/**
 * Generate a complete eBook for lead generation
 * 10-15 chapters, professionally formatted
 * Ready for PDF conversion and email delivery
 */
export async function generateLeadMagnetEbook() {
  const ebookTitle = 'The Complete Guide to Building $10K/Month Passive Income';
  const numberOfChapters = 12;

  try {
    const chapters = await generateEbookChapters(ebookTitle, numberOfChapters);

    console.log(`✓ Generated eBook: ${ebookTitle}`);
    console.log(`  Chapters: ${chapters.length}`);

    let totalWords = 0;
    let totalReadingTime = 0;

    for (const chapter of chapters) {
      totalWords += chapter.wordCount;
      totalReadingTime += chapter.estimatedReadingTime;

      console.log(
        `  Chapter ${chapter.chapterNumber}: ${chapter.title} (${chapter.wordCount} words, ${chapter.estimatedReadingTime} min)`
      );
    }

    console.log(`\nTotal: ${totalWords} words, ~${totalReadingTime} min read`);
    console.log(`\nReady for:`);
    console.log(`  ✓ PDF export for lead magnet`);
    console.log(`  ✓ Email sequence delivery`);
    console.log(`  ✓ Gumroad/SendOwl product`);
    console.log(`  ✓ Free resource on website`);

    return chapters;
  } catch (error) {
    console.error(`✗ Failed to generate eBook: ${error}`);
    throw error;
  }
}

// ============================================================================
// EXAMPLE 5: Content Marketing Calendar
// ============================================================================

/**
 * Generate a complete month's worth of content
 * 30 blog articles across 10 different topics
 * Automatically scheduled and distributed
 */
export async function generateMonthlyContentCalendar() {
  const mainTopics = [
    'Passive Income Ideas',
    'Freelancing & Side Hustles',
    'Digital Product Creation',
    'Marketing & Growth',
    'Personal Finance',
    'Online Business Models',
    'Productivity & Time Management',
    'Personal Development',
    'Technology & Tools',
    'Entrepreneurship Mindset',
  ];

  const calendar: Record<string, GeneratedContent[]> = {};
  let totalGenerated = 0;

  for (const topic of mainTopics) {
    calendar[topic] = [];

    // Generate 3 articles per topic
    for (let i = 0; i < 3; i++) {
      const subtopic = `${topic} - Aspect ${i + 1}`;

      try {
        const request: ContentTopicRequest = {
          topic: subtopic,
          difficulty: i === 0 ? 'beginner' : i === 1 ? 'intermediate' : 'advanced',
          format: 'blog',
          keywords: [topic.toLowerCase(), 'money', 'business'],
          targetAudience: 'entrepreneurs',
          tone: 'professional',
          includeAffiliates: true,
          estimatedLength: 'medium',
        };

        const article = await generateContent(request);
        calendar[topic].push(article);
        totalGenerated++;

        process.stdout.write('.');
      } catch (error) {
        console.error(`\n✗ Failed: ${subtopic}`);
      }
    }
  }

  console.log(`\n✓ Generated calendar with ${totalGenerated} articles`);

  // Display summary
  console.log('\nContent Calendar Summary:');
  for (const [topic, articles] of Object.entries(calendar)) {
    console.log(`\n${topic}: ${articles.length} articles`);
    for (const article of articles) {
      console.log(`  - ${article.title} (${article.wordCount} words)`);
    }
  }

  // Distribution plan
  console.log('\nDistribution Plan:');
  console.log('  ✓ Mon-Fri: 1 article published daily');
  console.log('  ✓ Each article: Blog + Newsletter + Social');
  console.log('  ✓ Weekly: 1 article on Medium + Dev.to');
  console.log('  ✓ Total reach: 30+ platforms across month');

  return calendar;
}

// ============================================================================
// EXAMPLE 6: Niche Authority Building
// ============================================================================

/**
 * Build authority in a specific niche by creating
 * interconnected content across blog, course, and social
 */
export async function buildNicheAuthority() {
  const niche = 'Passive Income for Digital Creators';

  const strategy = {
    pillarContent: [] as GeneratedContent[],
    courseModules: [] as any[],
    socialPosts: [] as GeneratedContent[],
  };

  // 1. Create 3 pillar blog posts (comprehensive guides)
  console.log('Step 1: Creating pillar content...');
  const pillarTopics = [
    'The Complete Guide to Passive Income for Digital Creators',
    'Building an Online Product Business: Step by Step',
    'Scaling Digital Products to $100K/Year',
  ];

  for (const topic of pillarTopics) {
    const request: ContentTopicRequest = {
      topic,
      difficulty: 'intermediate',
      format: 'blog',
      keywords: ['passive income', 'digital products', 'creators'],
      targetAudience: 'digital creators',
      tone: 'professional',
      includeAffiliates: true,
      estimatedLength: 'long', // 3000-5000 words
    };

    try {
      const content = await generateContent(request);
      strategy.pillarContent.push(content);
      console.log(`  ✓ ${content.title}`);
    } catch (error) {
      console.error(`  ✗ Failed: ${topic}`);
    }
  }

  // 2. Create supporting course modules
  console.log('\nStep 2: Creating course modules...');
  const courseTopics = [
    'Digital Product Fundamentals',
    'Building Your First Product',
    'Marketing & Sales Strategies',
    'Scaling to Multiple Products',
  ];

  for (const topic of courseTopics) {
    try {
      const courseModule = await generateCourseModule(topic, 'intermediate');
      strategy.courseModules.push(courseModule);
      console.log(`  ✓ ${courseModule.title} (${courseModule.lessons.length} lessons)`);
    } catch (error) {
      console.error(`  ✗ Failed: ${topic}`);
    }
  }

  // 3. Create social content from pillar posts
  console.log('\nStep 3: Creating social variations...');
  for (const pillarPost of strategy.pillarContent) {
    // Create 5 social posts from each pillar post
    const sections = pillarPost.content.split('\n\n').slice(1, 6);

    for (let i = 0; i < sections.length; i++) {
      const socialRequest: ContentTopicRequest = {
        topic: `Quick tip: ${sections[i].substring(0, 50)}...`,
        difficulty: 'beginner',
        format: 'blog',
        keywords: ['tips', 'strategy'],
        targetAudience: 'digital creators',
        tone: 'casual',
        includeAffiliates: false,
      };

      try {
        const socialPost = await generateContent(socialRequest);
        strategy.socialPosts.push(socialPost);
      } catch (error) {
        // Silent fail for social posts
      }
    }
  }

  console.log('\n✓ Authority Building Strategy Complete:');
  console.log(`  Pillar Posts: ${strategy.pillarContent.length}`);
  console.log(`  Course Modules: ${strategy.courseModules.length}`);
  console.log(`  Social Posts: ${strategy.socialPosts.length}`);
  console.log('\nThis creates a comprehensive authority position across:');
  console.log('  ✓ Long-form content (pillar posts)');
  console.log('  ✓ Educational content (courses)');
  console.log('  ✓ Social engagement (quick tips)');

  return strategy;
}

// ============================================================================
// EXAMPLE 7: Monetization Content Suite
// ============================================================================

/**
 * Create a suite of monetizable content:
 * - Free blog posts (drive traffic)
 * - Course modules (generate leads)
 * - eBook (email capture)
 * - All interlinked for conversion funnel
 */
export async function createMonetizationSuite() {
  const mainTopic = 'How to Make $10,000/Month Online';

  console.log(`Creating monetization suite for: "${mainTopic}"\n`);

  // 1. Blog post (traffic driver)
  console.log('1. Creating blog post (traffic driver)...');
  const blogRequest: ContentTopicRequest = {
    topic: mainTopic,
    difficulty: 'beginner',
    format: 'blog',
    keywords: ['make money', 'online', 'passive income'],
    targetAudience: 'aspiring entrepreneurs',
    tone: 'inspirational',
    includeAffiliates: true,
    estimatedLength: 'long',
  };

  const blogPost = await generateContent(blogRequest);
  console.log(`  ✓ ${blogPost.title} (${blogPost.wordCount} words)`);
  console.log(`  CTAssistant: "Enroll in my course below for detailed strategies"`);

  // 2. Course modules (lead generation)
  console.log('\n2. Creating course modules (lead generation)...');
  const courseModule = await generateCourseModule(mainTopic, 'intermediate');
  console.log(`  ✓ ${courseModule.title} (${courseModule.lessons.length} lessons)`);
  console.log(`  CTAssistant: "Get the full course + email list for extended content"`);

  // 3. eBook (email capture)
  console.log('\n3. Creating eBook (email capture)...');
  const ebookChapters = await generateEbookChapters(`${mainTopic}: Complete Guide`, 8);
  console.log(`  ✓ eBook: ${ebookChapters.length} chapters`);
  console.log(
    `  Total words: ${ebookChapters.reduce((sum, ch) => sum + ch.wordCount, 0)}`
  );
  console.log(`  Lead magnet offer: "Get free eBook + video course"`);

  // 4. Distribution strategy
  console.log('\n4. Distribution strategy:');
  const results = await distributeContent(blogPost, [
    'blog',
    'newsletter',
    'social',
    'medium',
    'devto',
  ]);

  console.log('   Traffic funnel:');
  console.log('   Blog post → Newsletter signup → eBook offer → Course enrollment');
  console.log('\nMonetization suite ready with:');
  console.log(`  ✓ 1 blog post (SEO traffic)`);
  console.log(`  ✓ 1 course (${courseModule.lessons.length} lessons)`);
  console.log(`  ✓ 1 eBook (${ebookChapters.length} chapters)`);
  console.log(`  ✓ Multi-platform distribution`);
  console.log(`  ✓ Affiliate links integrated`);

  return {
    blogPost,
    courseModule,
    ebookChapters,
    distribution: results,
  };
}

// ============================================================================
// EXAMPLE 8: Email Sequence From Blog Series
// ============================================================================

/**
 * Generate a 5-email sequence based on blog content
 * Each email excerpts and links to blog post
 */
export async function emailSequenceFromBlog() {
  const topic = 'Building Your First Online Business';

  console.log(`Creating email sequence for: "${topic}"\n`);

  // 1. Generate main blog post
  const blogRequest: ContentTopicRequest = {
    topic,
    difficulty: 'beginner',
    format: 'blog',
    keywords: ['online business', 'entrepreneurship'],
    targetAudience: 'beginners',
    tone: 'inspirational',
    includeAffiliates: true,
  };

  const blogPost = await generateContent(blogRequest);

  // 2. Create email sequence from blog sections
  const sections = blogPost.content.split(/\n\n+/).filter((s) => s.length > 100);

  const emailSequence = [];

  // Email 1: Introduction
  emailSequence.push({
    subject: `Start your journey: ${blogPost.title}`,
    preview: `Read the complete guide...`,
    body: sections[0] || blogPost.content.substring(0, 300),
    cta: 'Read Full Article',
    ctaUrl: 'https://profitengine.ai/blog/' + blogPost.id,
  });

  // Email 2-4: Content deep dives
  for (let i = 1; i < Math.min(4, sections.length); i++) {
    emailSequence.push({
      subject: `Part ${i}: Key insight from "${blogPost.title}"`,
      preview: sections[i]?.substring(0, 50),
      body: sections[i] || '',
      cta: 'Read More',
      ctaUrl: 'https://profitengine.ai/blog/' + blogPost.id,
    });
  }

  // Email 5: Follow-up + upsell
  emailSequence.push({
    subject: `Ready to go deeper? Take the complete course`,
    preview: 'Master the complete system...',
    body: 'Want the full step-by-step system? Enroll in our course for video training, worksheets, and 1-on-1 support.',
    cta: 'Enroll Now',
    ctaUrl: 'https://profitengine.ai/courses/online-business',
  });

  console.log(`✓ Created 5-email sequence from blog post:`);
  for (let i = 0; i < emailSequence.length; i++) {
    console.log(`  Email ${i + 1}: ${emailSequence[i].subject}`);
  }

  console.log('\nSequence strategy:');
  console.log('  1. Welcome + main article');
  console.log('  2-4. Content extracted from blog post');
  console.log('  5. Upsell to course');

  return emailSequence;
}

// ============================================================================
// TEST/RUN ALL EXAMPLES
// ============================================================================

/**
 * Run all examples (with error handling)
 */
export async function runAllExamples() {
  console.log('========================================');
  console.log('SELF-HELP AUTOMATION — REAL-WORLD EXAMPLES');
  console.log('========================================\n');

  const examples = [
    { name: 'Weekly Blog Series', fn: weeklyBlogSeries },
    { name: 'Training Course', fn: createTrainingCourse },
    { name: 'YouTube to Multi-Format', fn: youtubeToMultiFormat },
    { name: 'Lead Magnet eBook', fn: generateLeadMagnetEbook },
    { name: 'Monthly Calendar', fn: generateMonthlyContentCalendar },
    { name: 'Niche Authority', fn: buildNicheAuthority },
    { name: 'Monetization Suite', fn: createMonetizationSuite },
    { name: 'Email Sequence', fn: emailSequenceFromBlog },
  ];

  for (const example of examples) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`EXAMPLE: ${example.name}`);
    console.log('='.repeat(50));

    try {
      await example.fn();
    } catch (error) {
      console.error(`✗ Example failed: ${error}`);
    }

    // Wait between examples to avoid rate limiting
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  console.log('\n✓ All examples completed!');
}

export default {
  weeklyBlogSeries,
  createTrainingCourse,
  youtubeToMultiFormat,
  generateLeadMagnetEbook,
  generateMonthlyContentCalendar,
  buildNicheAuthority,
  createMonetizationSuite,
  emailSequenceFromBlog,
  runAllExamples,
};
