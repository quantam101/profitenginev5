/**
 * SELF-HELP CONTENT AUTOMATION SYSTEM
 *
 * Complete automation for generating, formatting, and publishing self-help content:
 * - Blog articles with SEO optimization
 * - Course modules and lesson plans
 * - YouTube transcript generation and optimization
 * - eBook chapters with rich formatting
 * - Content syndication and distribution
 * - Affiliate link injection
 * - Multi-format output (Markdown, HTML, PDF, DOCX)
 *
 * Environment Requirements:
 * - OPENAI_API_KEY: for content generation
 * - STRIPE_API_KEY: for course enrollment/payments
 * - YOUTUBE_API_KEY: for transcript processing
 * - GITHUB_TOKEN: for content repo access
 * - RUNTIME_API_URL: backend service URL
 * - AFFILIATE_TAG: Amazon Associates tag
 * - AFFILIATE_LINKS: JSON map of product links
 */

import { readFile, writeFile } from 'fs/promises';
import * as path from 'path';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

export interface ContentTopicRequest {
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  format: 'blog' | 'course' | 'ebook' | 'youtube-transcript' | 'all';
  keywords: string[];
  targetAudience: string;
  tone: 'professional' | 'casual' | 'inspirational' | 'educational';
  includeAffiliates: boolean;
  estimatedLength?: 'short' | 'medium' | 'long';
}

export interface GeneratedContent {
  id: string;
  topic: string;
  format: string;
  title: string;
  content: string;
  markdown: string;
  html: string;
  wordCount: number;
  readingTimeMinutes: number;
  seoKeywords: string[];
  metadata: {
    createdAt: string;
    updatedAt: string;
    author: string;
    category: string;
    tags: string[];
  };
  affiliateLinks?: Record<string, string>;
  generatedAt: string;
}

export interface CourseModule {
  id: string;
  title: string;
  description: string;
  duration: number; // minutes
  lessons: CourseLesson[];
  quizzes: CourseQuiz[];
  resources: CourseResource[];
  prerequisites: string[];
  learningOutcomes: string[];
}

export interface CourseLesson {
  id: string;
  title: string;
  content: string;
  videoUrl?: string;
  transcript?: string;
  duration: number; // seconds
  keyPoints: string[];
  exercises: CourseExercise[];
}

export interface CourseExercise {
  id: string;
  type: 'multiple-choice' | 'short-answer' | 'coding' | 'project';
  question: string;
  options?: string[];
  correctAnswer?: string;
  rubric?: string;
  hints: string[];
}

export interface CourseQuiz {
  id: string;
  title: string;
  questions: CourseExercise[];
  passingScore: number;
  timeLimit?: number; // seconds
}

export interface CourseResource {
  type: 'pdf' | 'video' | 'article' | 'tool' | 'download';
  title: string;
  url: string;
  description?: string;
}

export interface YouTubeTranscript {
  videoId: string;
  title: string;
  transcript: string;
  duration: number; // seconds
  keywords: string[];
  chapters: TranscriptChapter[];
  seoDescription: string;
  blogPost?: string;
  studyGuide?: string;
}

export interface TranscriptChapter {
  startTime: number; // seconds
  title: string;
  content: string;
  keyPoints: string[];
}

export interface EbookChapter {
  chapterNumber: number;
  title: string;
  content: string;
  sections: EbookSection[];
  wordCount: number;
  estimatedReadingTime: number; // minutes
}

export interface EbookSection {
  heading: string;
  content: string;
  subsections?: EbookSection[];
  callouts?: CalloutBox[];
  figures?: FigureReference[];
}

export interface CalloutBox {
  type: 'warning' | 'tip' | 'note' | 'important' | 'exercise';
  title: string;
  content: string;
}

export interface FigureReference {
  id: string;
  caption: string;
  description: string;
  sourceUrl?: string;
}

export interface ContentDistributionResult {
  success: boolean;
  platform: string;
  url?: string;
  postId?: string;
  scheduledTime?: string;
  error?: string;
}

// ============================================================================
// CONTENT GENERATION
// ============================================================================

/**
 * Generate comprehensive content for a given topic
 * Calls OpenAI API to generate SEO-optimized content
 */
export async function generateContent(request: ContentTopicRequest): Promise<GeneratedContent> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompt = buildContentPrompt(request);

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: `You are an expert content creator specializing in self-help, personal development, and educational content. Create comprehensive, well-structured, and engaging content that ranks well in search engines. Use clear headings, bullet points, and actionable insights.`,
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 4000,
    }),
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${await response.text()}`);
  }

  const data = (await response.json()) as any;
  const content = data.choices[0].message.content;

  // Parse and format the generated content
  const title = extractTitle(content);
  const markdown = formatAsMarkdown(content);
  const html = markdownToHtml(markdown);
  const wordCount = content.split(/\s+/).length;
  const readingTimeMinutes = Math.ceil(wordCount / 200);

  const generated: GeneratedContent = {
    id: `content-${Date.now()}`,
    topic: request.topic,
    format: request.format,
    title,
    content,
    markdown,
    html,
    wordCount,
    readingTimeMinutes,
    seoKeywords: extractSeoKeywords(content, request.keywords),
    metadata: {
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      author: 'ProfitEngine AI',
      category: request.targetAudience,
      tags: request.keywords,
    },
    generatedAt: new Date().toISOString(),
  };

  // Add affiliate links if requested
  if (request.includeAffiliates) {
    generated.affiliateLinks = await injectAffiliateLinks(content, request.topic);
  }

  return generated;
}

/**
 * Build optimized prompt for content generation
 */
function buildContentPrompt(request: ContentTopicRequest): string {
  const lengthGuide =
    request.estimatedLength === 'short'
      ? '800-1200 words'
      : request.estimatedLength === 'long'
        ? '3000-5000 words'
        : '1500-2500 words';

  return `Create a comprehensive ${request.difficulty} level ${lengthGuide} guide on "${request.topic}".

Target Audience: ${request.targetAudience}
Tone: ${request.tone}
Format: ${request.format === 'all' ? 'blog article with course structure' : request.format}
Key Keywords: ${request.keywords.join(', ')}

Requirements:
1. Start with a compelling title and meta description
2. Include an introduction that hooks the reader
3. Structure with clear H2 and H3 headings
4. Add practical, actionable tips and insights
5. Include relevant statistics, case studies, or real-world examples
6. End with a clear call-to-action
7. Use bullet points and numbered lists for clarity
8. Optimize for SEO while maintaining readability
9. Add internal linking suggestions
10. Include practical exercises or worksheets where relevant

Format the output as structured Markdown with clear sections.`;
}

/**
 * Extract title from generated content
 */
function extractTitle(content: string): string {
  const titleMatch = content.match(/^#\s+(.+?)$/m) || content.match(/^(.+?)(?:\n|$)/);
  return titleMatch ? titleMatch[1].trim() : 'Untitled Content';
}

/**
 * Format content as Markdown
 */
function formatAsMarkdown(content: string): string {
  let markdown = content;

  // Ensure proper heading hierarchy
  markdown = markdown.replace(/^(#{1,6})\s+/gm, '$1 ');

  // Format lists
  markdown = markdown.replace(/^\s*[-•]\s+/gm, '- ');

  // Add spacing around sections
  markdown = markdown.replace(/\n(#+\s+)/g, '\n\n$1');

  return markdown;
}

/**
 * Convert Markdown to HTML
 */
function markdownToHtml(markdown: string): string {
  let html = '<div class="content">';

  const lines = markdown.split('\n');
  let currentTag = '';

  for (const line of lines) {
    if (line.match(/^#####\s+/)) {
      html += `<h5>${line.replace(/^#+\s+/, '').trim()}</h5>`;
    } else if (line.match(/^####\s+/)) {
      html += `<h4>${line.replace(/^#+\s+/, '').trim()}</h4>`;
    } else if (line.match(/^###\s+/)) {
      html += `<h3>${line.replace(/^#+\s+/, '').trim()}</h3>`;
    } else if (line.match(/^##\s+/)) {
      html += `<h2>${line.replace(/^#+\s+/, '').trim()}</h2>`;
    } else if (line.match(/^#\s+/)) {
      html += `<h1>${line.replace(/^#+\s+/, '').trim()}</h1>`;
    } else if (line.match(/^-\s+/)) {
      if (currentTag !== 'ul') {
        if (currentTag === 'ol') html += '</ol>';
        html += '<ul>';
        currentTag = 'ul';
      }
      html += `<li>${line.replace(/^-\s+/, '').trim()}</li>`;
    } else if (line.match(/^\d+\.\s+/)) {
      if (currentTag !== 'ol') {
        if (currentTag === 'ul') html += '</ul>';
        html += '<ol>';
        currentTag = 'ol';
      }
      html += `<li>${line.replace(/^\d+\.\s+/, '').trim()}</li>`;
    } else if (line.trim()) {
      if (currentTag) {
        html += currentTag === 'ul' ? '</ul>' : '</ol>';
        currentTag = '';
      }
      html += `<p>${line.trim()}</p>`;
    }
  }

  if (currentTag) {
    html += currentTag === 'ul' ? '</ul>' : '</ol>';
  }

  html += '</div>';
  return html;
}

/**
 * Extract and optimize SEO keywords
 */
function extractSeoKeywords(content: string, providedKeywords: string[]): string[] {
  const keywords = new Set(providedKeywords);
  const commonWords = new Set([
    'the',
    'a',
    'an',
    'and',
    'or',
    'but',
    'in',
    'on',
    'at',
    'to',
    'for',
    'of',
    'is',
    'are',
  ]);

  const words = content.toLowerCase().split(/\W+/);
  const wordFreq = new Map<string, number>();

  for (const word of words) {
    if (word.length > 4 && !commonWords.has(word)) {
      wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
    }
  }

  // Add most frequent relevant words
  const sorted = Array.from(wordFreq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  for (const [word] of sorted) {
    keywords.add(word);
  }

  return Array.from(keywords);
}

/**
 * Inject affiliate links into content
 */
async function injectAffiliateLinks(
  content: string,
  topic: string
): Promise<Record<string, string>> {
  const affiliateLinksEnv = process.env.AFFILIATE_LINKS;
  const affiliateTag = process.env.AFFILIATE_TAG || 'alreadyhere-20';

  if (!affiliateLinksEnv) {
    return {};
  }

  let affiliateLinks: Record<string, string> = {};
  try {
    affiliateLinks = JSON.parse(affiliateLinksEnv);
  } catch (error) {
    console.error('Failed to parse AFFILIATE_LINKS:', error);
    return {};
  }

  // Filter relevant affiliate links based on topic
  const relevantLinks: Record<string, string> = {};
  for (const [product, url] of Object.entries(affiliateLinks)) {
    if (content.toLowerCase().includes(product.toLowerCase())) {
      // Append affiliate tag to Amazon links
      if (url.includes('amazon.com') && !url.includes('tag=')) {
        relevantLinks[product] = `${url}?tag=${affiliateTag}`;
      } else {
        relevantLinks[product] = url;
      }
    }
  }

  return relevantLinks;
}

// ============================================================================
// COURSE GENERATION
// ============================================================================

/**
 * Generate complete course module from topic
 */
export async function generateCourseModule(topic: string, difficulty: string): Promise<CourseModule> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const prompt = `Create a structured course module for "${topic}" at ${difficulty} level.

Structure the response as JSON with:
- Title and description
- 5-7 lessons with detailed content
- 2-3 quizzes with 5 questions each
- 5-10 recommended resources
- Learning outcomes (5-7 items)
- Prerequisites (if any)

Make lessons practical and progressive, building on each other.
Include code examples, diagrams descriptions, and real-world applications.`;

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content:
            'You are an expert curriculum designer. Create structured, engaging course modules with clear learning objectives and progression.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 6000,
    }),
  });

  if (!response.ok) {
    throw new Error(`Course generation failed: ${await response.text()}`);
  }

  const data = (await response.json()) as any;
  const responseText = data.choices[0].message.content;

  // Parse JSON from response
  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  const courseData = jsonMatch ? JSON.parse(jsonMatch[0]) : parseCourseLikeStructure(responseText);

  const courseModule: CourseModule = {
    id: `course-${Date.now()}`,
    title: courseData.title || topic,
    description: courseData.description || '',
    duration: courseData.duration || 0,
    lessons: (courseData.lessons || []).map((lesson: any, index: number) => ({
      id: `lesson-${Date.now()}-${index}`,
      title: lesson.title || `Lesson ${index + 1}`,
      content: lesson.content || '',
      duration: lesson.duration || 600,
      keyPoints: lesson.keyPoints || [],
      exercises: (lesson.exercises || []).map((ex: any, exIndex: number) => ({
        id: `exercise-${Date.now()}-${exIndex}`,
        type: ex.type || 'multiple-choice',
        question: ex.question || '',
        options: ex.options || [],
        correctAnswer: ex.correctAnswer || '',
        hints: ex.hints || [],
      })),
    })),
    quizzes: (courseData.quizzes || []).map((quiz: any, index: number) => ({
      id: `quiz-${Date.now()}-${index}`,
      title: quiz.title || `Quiz ${index + 1}`,
      questions: (quiz.questions || []).map((q: any, qIndex: number) => ({
        id: `question-${Date.now()}-${qIndex}`,
        type: 'multiple-choice',
        question: q.question || '',
        options: q.options || [],
        correctAnswer: q.correctAnswer || '',
        hints: [],
      })),
      passingScore: quiz.passingScore || 70,
      timeLimit: quiz.timeLimit || 1800,
    })),
    resources: (courseData.resources || []).map((res: any) => ({
      type: res.type || 'article',
      title: res.title || '',
      url: res.url || '',
      description: res.description || '',
    })),
    prerequisites: courseData.prerequisites || [],
    learningOutcomes: courseData.learningOutcomes || [],
  };

  return courseModule;
}

/**
 * Fallback parser for course structure
 */
function parseCourseLikeStructure(text: string): any {
  return {
    title: 'Course Module',
    description: text.slice(0, 200),
    lessons: [],
    quizzes: [],
    resources: [],
  };
}

// ============================================================================
// YOUTUBE TRANSCRIPT PROCESSING
// ============================================================================

/**
 * Process YouTube video into structured transcript with chapters and study materials
 */
export async function processYouTubeTranscript(
  videoId: string,
  title: string
): Promise<YouTubeTranscript> {
  const youtubeKey = process.env.YOUTUBE_API_KEY;
  if (!youtubeKey) {
    throw new Error('YOUTUBE_API_KEY not configured');
  }

  // Fetch transcript from YouTube API
  const transcriptUrl = `https://www.googleapis.com/youtube/v3/captions?videoId=${videoId}&key=${youtubeKey}`;

  const captionsResponse = await fetch(transcriptUrl);
  if (!captionsResponse.ok) {
    throw new Error('Failed to fetch video captions');
  }

  const captionsData = (await captionsResponse.json()) as any;

  // Use first available caption track
  const captionTrack = captionsData.items?.[0];
  if (!captionTrack) {
    throw new Error('No captions available for video');
  }

  // Download and parse transcript
  const transcriptData = await fetch(captionTrack.baseUrl).then((r) => r.text());
  const transcript = parseYouTubeTranscript(transcriptData);

  // Extract chapters and key points
  const chapters = extractTranscriptChapters(transcript);
  const keywords = extractKeywords(transcript);

  // Generate SEO description
  const seoDescription = generateSeoDescription(title, keywords, transcript);

  // Generate complementary materials
  const blogPost = await generateBlogFromTranscript(transcript, title);
  const studyGuide = generateStudyGuide(transcript, chapters);

  return {
    videoId,
    title,
    transcript,
    duration: captionTrack.duration || 0,
    keywords,
    chapters,
    seoDescription,
    blogPost,
    studyGuide,
  };
}

/**
 * Parse YouTube XML caption format
 */
function parseYouTubeTranscript(xmlContent: string): string {
  // Remove XML tags and join text
  const textRegex = />([^<]+)</g;
  let transcript = '';
  let match;

  while ((match = textRegex.exec(xmlContent))) {
    transcript += match[1] + ' ';
  }

  return transcript.replace(/\s+/g, ' ').trim();
}

/**
 * Extract chapters from transcript based on natural breaks
 */
function extractTranscriptChapters(transcript: string): TranscriptChapter[] {
  const chapters: TranscriptChapter[] = [];
  const sentences = transcript.split(/\.\s+/);

  // Group sentences into chapters (approximately every 500 characters)
  let currentChapter = '';
  let charCount = 0;
  let chapterIndex = 0;

  for (const sentence of sentences) {
    currentChapter += sentence + '. ';
    charCount += sentence.length;

    if (charCount > 500 || sentence.length === 0) {
      if (currentChapter.trim()) {
        chapters.push({
          startTime: chapterIndex * 300, // Estimate 5 min per chapter
          title: `Chapter ${chapterIndex + 1}: ${currentChapter.substring(0, 50)}...`,
          content: currentChapter.trim(),
          keyPoints: extractKeyPoints(currentChapter),
        });
      }
      currentChapter = '';
      charCount = 0;
      chapterIndex++;
    }
  }

  return chapters;
}

/**
 * Extract key points from text
 */
function extractKeyPoints(text: string): string[] {
  const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 20);
  return sentences.slice(0, 5).map((s) => s.trim());
}

/**
 * Extract keywords from transcript
 */
function extractKeywords(transcript: string): string[] {
  const words = transcript.toLowerCase().split(/\W+/);
  const wordFreq = new Map<string, number>();
  const commonWords = new Set([
    'the',
    'a',
    'an',
    'and',
    'or',
    'but',
    'in',
    'on',
    'is',
    'are',
    'that',
    'this',
    'it',
  ]);

  for (const word of words) {
    if (word.length > 4 && !commonWords.has(word)) {
      wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
    }
  }

  return Array.from(wordFreq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([word]) => word);
}

/**
 * Generate SEO-optimized description
 */
function generateSeoDescription(title: string, keywords: string[], transcript: string): string {
  const preview = transcript.substring(0, 150);
  return `${title} - Learn about ${keywords.slice(0, 3).join(', ')}. ${preview}...`;
}

/**
 * Generate blog post from transcript
 */
async function generateBlogFromTranscript(transcript: string, title: string): Promise<string> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return '';

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'user',
          content: `Convert this video transcript into a well-structured blog post with headings, bullet points, and actionable insights:\n\nTitle: ${title}\n\nTranscript:\n${transcript.substring(0, 2000)}`,
        },
      ],
      max_tokens: 2000,
    }),
  });

  if (response.ok) {
    const data = (await response.json()) as any;
    return data.choices[0].message.content;
  }

  return '';
}

/**
 * Generate study guide from transcript
 */
function generateStudyGuide(transcript: string, chapters: TranscriptChapter[]): string {
  let guide = '# Study Guide\n\n';

  for (const chapter of chapters) {
    guide += `## ${chapter.title}\n\n`;
    guide += '### Key Points:\n';
    for (const point of chapter.keyPoints) {
      guide += `- ${point}\n`;
    }
    guide += '\n### Review Questions:\n';
    guide += '1. What were the main concepts discussed?\n';
    guide += '2. How can you apply this to your work?\n';
    guide += '3. What questions do you still have?\n\n';
  }

  return guide;
}

// ============================================================================
// EBOOK GENERATION
// ============================================================================

/**
 * Generate complete ebook with multiple chapters
 */
export async function generateEbookChapters(
  title: string,
  numChapters: number = 8
): Promise<EbookChapter[]> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  const chapters: EbookChapter[] = [];

  for (let i = 1; i <= numChapters; i++) {
    const prompt = `Write chapter ${i} of an ebook titled "${title}".

Chapter ${i} should:
- Have a compelling title
- Include 3-5 sections with subsections
- Contain 1500-2500 words
- Include 2-3 callout boxes (tips, warnings, or exercises)
- Reference figures or diagrams (describe them)
- Build progressively from previous chapters
- End with key takeaways

Format the response as structured markdown.`;

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4-turbo-preview',
        messages: [
          {
            role: 'system',
            content:
              'You are a professional ebook author. Write comprehensive, engaging chapters that educate and inspire readers.',
          },
          {
            role: 'user',
            content: prompt,
          },
        ],
        temperature: 0.7,
        max_tokens: 3000,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chapter generation failed: ${await response.text()}`);
    }

    const data = (await response.json()) as any;
    const content = data.choices[0].message.content;

    const chapter: EbookChapter = {
      chapterNumber: i,
      title: extractChapterTitle(content),
      content,
      sections: parseEbookSections(content),
      wordCount: content.split(/\s+/).length,
      estimatedReadingTime: Math.ceil(content.split(/\s+/).length / 200),
    };

    chapters.push(chapter);
  }

  return chapters;
}

/**
 * Extract chapter title
 */
function extractChapterTitle(content: string): string {
  const match = content.match(/^#\s+(.+?)$/m);
  return match ? match[1].trim() : 'Chapter';
}

/**
 * Parse content sections
 */
function parseEbookSections(content: string): EbookSection[] {
  const sections: EbookSection[] = [];
  const lines = content.split('\n');
  let currentSection: EbookSection | null = null;
  let currentSubsection: EbookSection | null = null;

  for (const line of lines) {
    if (line.startsWith('## ')) {
      currentSection = {
        heading: line.replace(/^##\s+/, ''),
        content: '',
        subsections: [],
      };
      sections.push(currentSection);
    } else if (line.startsWith('### ') && currentSection) {
      currentSubsection = {
        heading: line.replace(/^###\s+/, ''),
        content: '',
      };
      if (!currentSection.subsections) {
        currentSection.subsections = [];
      }
      currentSection.subsections.push(currentSubsection);
    } else if (line.match(/^\*\*\*Note:/i) && currentSection) {
      const callout: CalloutBox = {
        type: 'note',
        title: 'Note',
        content: line.replace(/^\*\*\*Note:\*\*\*/i, '').trim(),
      };
      if (!currentSection.callouts) {
        currentSection.callouts = [];
      }
      currentSection.callouts.push(callout);
    } else if (currentSubsection) {
      currentSubsection.content += line + '\n';
    } else if (currentSection) {
      currentSection.content += line + '\n';
    }
  }

  return sections;
}

// ============================================================================
// CONTENT DISTRIBUTION
// ============================================================================

/**
 * Distribute content to multiple platforms
 */
export async function distributeContent(
  content: GeneratedContent,
  platforms: string[] = ['blog', 'newsletter', 'social']
): Promise<ContentDistributionResult[]> {
  const results: ContentDistributionResult[] = [];

  for (const platform of platforms) {
    try {
      let result: ContentDistributionResult;

      switch (platform) {
        case 'blog':
          result = await publishToBlog(content);
          break;
        case 'newsletter':
          result = await publishToNewsletter(content);
          break;
        case 'social':
          result = await publishToSocial(content);
          break;
        case 'medium':
          result = await publishToMedium(content);
          break;
        case 'devto':
          result = await publishToDevTo(content);
          break;
        case 'github':
          result = await publishToGitHub(content);
          break;
        default:
          result = { success: false, platform, error: 'Unknown platform' };
      }

      results.push(result);
    } catch (error) {
      results.push({
        success: false,
        platform,
        error: String(error),
      });
    }
  }

  return results;
}

/**
 * Publish to blog (GitHub)
 */
async function publishToBlog(content: GeneratedContent): Promise<ContentDistributionResult> {
  const githubToken = process.env.GITHUB_TOKEN;
  if (!githubToken) {
    throw new Error('GITHUB_TOKEN not configured');
  }

  const owner = 'quantam101';
  const repo = 'content';
  const filename = `${content.id}-${content.title.toLowerCase().replace(/\s+/g, '-')}.md`;
  const filePath = `blog/${filename}`;

  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/contents/${filePath}`,
    {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Add blog post: ${content.title}`,
        content: Buffer.from(content.markdown).toString('base64'),
      }),
    }
  );

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'blog',
      postId: data.content.name,
      url: `https://github.com/${owner}/${repo}/blob/main/${filePath}`,
    };
  }

  throw new Error(`GitHub API error: ${await response.text()}`);
}

/**
 * Publish to newsletter (via email automation)
 */
async function publishToNewsletter(content: GeneratedContent): Promise<ContentDistributionResult> {
  const runtimeUrl = process.env.RUNTIME_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

  const response = await fetch(`${runtimeUrl}/api/v1/newsletter/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.NEWSLETTER_API_KEY || ''}`,
    },
    body: JSON.stringify({
      subject: content.title,
      html: content.html,
      markdown: content.markdown,
      tags: content.metadata.tags,
      metadata: content.metadata,
    }),
  });

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'newsletter',
      postId: data.campaign_id,
      scheduledTime: data.scheduled_time,
    };
  }

  return {
    success: false,
    platform: 'newsletter',
    error: 'Failed to publish to newsletter',
  };
}

/**
 * Publish to social media
 */
async function publishToSocial(content: GeneratedContent): Promise<ContentDistributionResult> {
  // Create excerpt for social
  const excerpt = content.content.substring(0, 280);

  const runtimeUrl = process.env.RUNTIME_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

  const response = await fetch(`${runtimeUrl}/api/v1/social/post`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: excerpt,
      title: content.title,
      url: `https://profitengine.ai/blog/${content.id}`,
      tags: content.metadata.tags,
      platforms: ['twitter', 'linkedin', 'instagram'],
    }),
  });

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'social',
      url: data.url,
    };
  }

  return {
    success: false,
    platform: 'social',
    error: 'Failed to publish to social media',
  };
}

/**
 * Publish to Medium
 */
async function publishToMedium(content: GeneratedContent): Promise<ContentDistributionResult> {
  const mediumToken = process.env.MEDIUM_API_TOKEN;
  if (!mediumToken) {
    return {
      success: false,
      platform: 'medium',
      error: 'MEDIUM_API_TOKEN not configured',
    };
  }

  // Get user profile first
  const userResponse = await fetch('https://api.medium.com/v1/me', {
    headers: {
      Authorization: `Bearer ${mediumToken}`,
    },
  });

  if (!userResponse.ok) {
    return {
      success: false,
      platform: 'medium',
      error: 'Failed to authenticate with Medium',
    };
  }

  const userData = (await userResponse.json()) as any;
  const userId = userData.data.id;

  // Publish post
  const response = await fetch(`https://api.medium.com/v1/users/${userId}/posts`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${mediumToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: content.title,
      contentFormat: 'markdown',
      content: content.markdown,
      publishStatus: 'draft',
      tags: content.metadata.tags,
    }),
  });

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'medium',
      postId: data.data.id,
      url: data.data.url,
    };
  }

  return {
    success: false,
    platform: 'medium',
    error: await response.text(),
  };
}

/**
 * Publish to Dev.to
 */
async function publishToDevTo(content: GeneratedContent): Promise<ContentDistributionResult> {
  const devtoKey = process.env.DEVTO_API_KEY;
  if (!devtoKey) {
    return {
      success: false,
      platform: 'devto',
      error: 'DEVTO_API_KEY not configured',
    };
  }

  const response = await fetch('https://dev.to/api/articles', {
    method: 'POST',
    headers: {
      'api-key': devtoKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      article: {
        title: content.title,
        body_markdown: content.markdown,
        tags: content.metadata.tags.slice(0, 4),
        published: false,
      },
    }),
  });

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'devto',
      postId: String(data.id),
      url: data.url,
    };
  }

  return {
    success: false,
    platform: 'devto',
    error: await response.text(),
  };
}

/**
 * Publish to GitHub Pages
 */
async function publishToGitHub(content: GeneratedContent): Promise<ContentDistributionResult> {
  const githubToken = process.env.GITHUB_TOKEN;
  if (!githubToken) {
    return {
      success: false,
      platform: 'github',
      error: 'GITHUB_TOKEN not configured',
    };
  }

  const owner = 'quantam101';
  const repo = 'profitengine-v5';
  const filename = `${content.id}-${content.title.toLowerCase().replace(/\s+/g, '-')}.md`;
  const filePath = `content/${filename}`;

  const response = await fetch(
    `https://api.github.com/repos/${owner}/${repo}/contents/${filePath}`,
    {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${githubToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Add self-help content: ${content.title}`,
        content: Buffer.from(content.markdown).toString('base64'),
      }),
    }
  );

  if (response.ok) {
    const data = (await response.json()) as any;
    return {
      success: true,
      platform: 'github',
      postId: data.content.name,
      url: `https://github.com/${owner}/${repo}/blob/main/${filePath}`,
    };
  }

  return {
    success: false,
    platform: 'github',
    error: await response.text(),
  };
}

// ============================================================================
// CONTENT FORMATTING
// ============================================================================

/**
 * Convert content to multiple formats (HTML, PDF, DOCX)
 */
export async function exportContent(
  content: GeneratedContent,
  formats: string[] = ['markdown', 'html', 'pdf']
): Promise<Record<string, string>> {
  const exported: Record<string, string> = {
    markdown: content.markdown,
    html: content.html,
  };

  if (formats.includes('pdf')) {
    // PDF generation would use a library like puppeteer or pdf-lib
    exported.pdf = await generatePDF(content.html);
  }

  if (formats.includes('docx')) {
    // DOCX generation
    exported.docx = await generateDOCX(content);
  }

  return exported;
}

/**
 * Generate PDF from HTML
 */
async function generatePDF(html: string): Promise<string> {
  // In production, use puppeteer or similar
  // For now, return placeholder
  return `data:application/pdf;base64,${Buffer.from(html).toString('base64')}`;
}

/**
 * Generate DOCX from content
 */
async function generateDOCX(content: GeneratedContent): Promise<string> {
  // In production, use docx library
  // For now, return placeholder
  return `data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,${Buffer.from(content.markdown).toString('base64')}`;
}

const selfHelp = {
  generateContent,
  generateCourseModule,
  processYouTubeTranscript,
  generateEbookChapters,
  distributeContent,
  exportContent,
};
export default selfHelp;
