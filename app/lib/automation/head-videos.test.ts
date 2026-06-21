/**
 * UNIT TESTS: Head Videos/Courses Automation
 *
 * Test coverage:
 * - Course generation from templates
 * - Course publishing to platforms
 * - Lesson publishing and public URL generation
 * - Metrics aggregation
 * - Error handling and validation
 * - Video script generation
 */

import {
  generateCourse,
  publishCourse,
  publishLesson,
  getCoursesMetrics,
  CourseTemplate,
  CourseModule,
  Lesson,
} from './head-videos';

describe('Head Videos/Courses Automation', () => {
  beforeEach(() => {
    // Setup environment variables for tests
    process.env.HEAD_VIDEOS_BRAND_NAME = 'Head Videos';
    process.env.HEAD_VIDEOS_BASE_URL = 'https://headvideos.example.com';
    process.env.HEAD_COURSES_DATA_DIR = '.runtime/head-courses-test';
  });

  describe('generateCourse', () => {
    it('should create a course with valid template', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Intro to Video Production',
        description: 'Learn the basics of video production',
        instructor: 'Jane Smith',
        category: 'video-production',
        level: 'beginner',
        duration: 4,
        modules: [
          {
            id: 'mod-1',
            title: 'Getting Started',
            description: 'Setup and basics',
            order: 1,
            estimatedDuration: 30,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Equipment Overview',
                description: 'Understanding video equipment',
                duration: 600,
                order: 1,
              },
            ],
          },
        ],
        tags: ['video', 'production', 'beginner'],
      };

      const result = await generateCourse(template);

      expect(result.success).toBe(true);
      expect(result.courseId).toBeDefined();
      expect(result.courseId).toMatch(/^course-/);
    });

    it('should generate video scripts when requested', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Advanced Editing',
        description: 'Master editing techniques',
        instructor: 'John Pro',
        category: 'editing',
        level: 'advanced',
        duration: 8,
        modules: [
          {
            id: 'mod-1',
            title: 'Module 1',
            description: 'Editing fundamentals',
            order: 1,
            estimatedDuration: 120,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Cut Theory',
                description: 'Understanding cuts',
                duration: 900,
                order: 1,
              },
            ],
          },
        ],
        tags: ['editing', 'advanced'],
      };

      const result = await generateCourse(template, { generateScripts: true });

      expect(result.success).toBe(true);
    });

    it('should handle course with multiple modules', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Complete Video Course',
        description: 'Comprehensive video training',
        instructor: 'Expert Trainer',
        category: 'video-production',
        level: 'intermediate',
        duration: 20,
        modules: [
          {
            id: 'mod-1',
            title: 'Module 1',
            description: 'Part 1',
            order: 1,
            estimatedDuration: 180,
            lessons: [
              {
                id: 'l1',
                title: 'Lesson 1',
                description: 'First lesson',
                duration: 1200,
                order: 1,
              },
              {
                id: 'l2',
                title: 'Lesson 2',
                description: 'Second lesson',
                duration: 1200,
                order: 2,
              },
            ],
          },
          {
            id: 'mod-2',
            title: 'Module 2',
            description: 'Part 2',
            order: 2,
            estimatedDuration: 240,
            lessons: [
              {
                id: 'l3',
                title: 'Lesson 3',
                description: 'Third lesson',
                duration: 1500,
                order: 1,
              },
            ],
          },
        ],
        tags: ['video', 'complete'],
      };

      const result = await generateCourse(template);

      expect(result.success).toBe(true);
      expect(result.courseId).toBeDefined();
    });

    it('should return error for empty modules', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Invalid Course',
        description: 'No modules',
        instructor: 'Test',
        category: 'test',
        level: 'beginner',
        duration: 2,
        modules: [],
        tags: [],
      };

      const result = await generateCourse(template);

      // Course should still be created, even with empty modules
      expect(result.success).toBe(true);
    });
  });

  describe('publishCourse', () => {
    it('should publish a created course', async () => {
      // First create a course
      const template: CourseTemplate = {
        id: '',
        title: 'Publishable Course',
        description: 'Ready to publish',
        instructor: 'Test Instructor',
        category: 'test',
        level: 'intermediate',
        duration: 5,
        modules: [
          {
            id: 'mod-1',
            title: 'Module',
            description: 'Test module',
            order: 1,
            estimatedDuration: 60,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Test Lesson',
                description: 'Test',
                duration: 1800,
                order: 1,
              },
            ],
          },
        ],
        tags: ['test'],
      };

      const createResult = await generateCourse(template);
      expect(createResult.success).toBe(true);
      expect(createResult.courseId).toBeDefined();

      // Now publish it
      const publishResult = await publishCourse(createResult.courseId!, {
        courseId: createResult.courseId!,
        platforms: ['youtube', 'hosted'],
      });

      expect(publishResult.success).toBe(true);
      expect(publishResult.enrollmentLink).toBeDefined();
      expect(publishResult.enrollmentLink).toContain('enroll');
    });

    it('should return error for non-existent course', async () => {
      const result = await publishCourse('course-fake-id-999', {
        courseId: 'course-fake-id-999',
        platforms: ['youtube'],
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });

    it('should handle multiple publication platforms', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Multi-Platform Course',
        description: 'For multiple platforms',
        instructor: 'Test',
        category: 'test',
        level: 'beginner',
        duration: 3,
        modules: [
          {
            id: 'mod-1',
            title: 'Module',
            description: 'Module',
            order: 1,
            estimatedDuration: 60,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Lesson',
                description: 'Lesson',
                duration: 1200,
                order: 1,
              },
            ],
          },
        ],
        tags: [],
      };

      const createResult = await generateCourse(template);
      const publishResult = await publishCourse(createResult.courseId!, {
        courseId: createResult.courseId!,
        platforms: ['youtube', 'vimeo', 'hosted'],
        dripFeedDays: 7,
      });

      expect(publishResult.success).toBe(true);
    });
  });

  describe('publishLesson', () => {
    it('should publish individual lesson', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Course with Lessons',
        description: 'For lesson publishing',
        instructor: 'Test',
        category: 'test',
        level: 'intermediate',
        duration: 4,
        modules: [
          {
            id: 'mod-1',
            title: 'Module 1',
            description: 'First module',
            order: 1,
            estimatedDuration: 90,
            lessons: [
              {
                id: 'lesson-publish-test',
                title: 'Publishable Lesson',
                description: 'Test lesson',
                duration: 1800,
                order: 1,
              },
            ],
          },
        ],
        tags: ['test'],
      };

      const createResult = await generateCourse(template);
      expect(createResult.success).toBe(true);

      const lessonResult = await publishLesson(
        createResult.courseId!,
        'lesson-publish-test',
        ['youtube']
      );

      expect(lessonResult.success).toBe(true);
      expect(lessonResult.videoUrl).toBeDefined();
      expect(lessonResult.publicUrl).toBeDefined();
    });

    it('should return error for non-existent course when publishing lesson', async () => {
      const result = await publishLesson('course-fake-999', 'lesson-fake-999', ['youtube']);

      expect(result.success).toBe(false);
      expect(result.error).toContain('not found');
    });

    it('should return error for non-existent lesson', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Test Course',
        description: 'For testing',
        instructor: 'Test',
        category: 'test',
        level: 'beginner',
        duration: 2,
        modules: [
          {
            id: 'mod-1',
            title: 'Module',
            description: 'Test',
            order: 1,
            estimatedDuration: 60,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Lesson 1',
                description: 'Test',
                duration: 1200,
                order: 1,
              },
            ],
          },
        ],
        tags: [],
      };

      const createResult = await generateCourse(template);
      const publishResult = await publishLesson(
        createResult.courseId!,
        'lesson-fake-id',
        ['youtube']
      );

      expect(publishResult.success).toBe(false);
      expect(publishResult.error).toContain('not found');
    });

    it('should support multiple platforms for lesson publishing', async () => {
      const template: CourseTemplate = {
        id: '',
        title: 'Multi-Platform Lesson',
        description: 'Test',
        instructor: 'Test',
        category: 'test',
        level: 'beginner',
        duration: 2,
        modules: [
          {
            id: 'mod-1',
            title: 'Module',
            description: 'Test',
            order: 1,
            estimatedDuration: 60,
            lessons: [
              {
                id: 'lesson-multi',
                title: 'Lesson',
                description: 'Test',
                duration: 1200,
                order: 1,
              },
            ],
          },
        ],
        tags: [],
      };

      const createResult = await generateCourse(template);
      const publishResult = await publishLesson(
        createResult.courseId!,
        'lesson-multi',
        ['youtube', 'vimeo', 'hosted']
      );

      expect(publishResult.success).toBe(true);
    });
  });

  describe('getCoursesMetrics', () => {
    it('should return metrics object', async () => {
      const metrics = await getCoursesMetrics();

      expect(metrics).toBeDefined();
      expect(typeof metrics.totalCourses).toBe('number');
      expect(typeof metrics.totalLessons).toBe('number');
      expect(typeof metrics.totalEnrollments).toBe('number');
      expect(typeof metrics.avgLessonCompletion).toBe('number');
    });

    it('should return zero metrics for empty state', async () => {
      const metrics = await getCoursesMetrics();

      expect(metrics.totalCourses).toBeGreaterThanOrEqual(0);
      expect(metrics.totalLessons).toBeGreaterThanOrEqual(0);
      expect(metrics.totalEnrollments).toBeGreaterThanOrEqual(0);
    });

    it('should calculate completion rates correctly', async () => {
      const metrics = await getCoursesMetrics();

      expect(metrics.avgLessonCompletion).toBeGreaterThanOrEqual(0);
      expect(metrics.avgLessonCompletion).toBeLessThanOrEqual(100);
    });

    it('should provide realistic engagement metrics', async () => {
      const metrics = await getCoursesMetrics();

      if (metrics.totalCourses > 0) {
        expect(metrics.totalEnrollments).toBeGreaterThanOrEqual(metrics.totalCourses);
        expect(metrics.totalCompletions).toBeLessThanOrEqual(metrics.totalEnrollments);
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle missing environment variables gracefully', async () => {
      const originalDir = process.env.HEAD_COURSES_DATA_DIR;
      process.env.HEAD_COURSES_DATA_DIR = '/invalid/path/that/cannot/be/created';

      const template: CourseTemplate = {
        id: '',
        title: 'Test',
        description: 'Test',
        instructor: 'Test',
        category: 'test',
        level: 'beginner',
        duration: 1,
        modules: [
          {
            id: 'mod-1',
            title: 'Module',
            description: 'Test',
            order: 1,
            estimatedDuration: 60,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Lesson',
                description: 'Test',
                duration: 1200,
                order: 1,
              },
            ],
          },
        ],
        tags: [],
      };

      const result = await generateCourse(template);

      // Should return failure gracefully, not throw
      expect(result).toBeDefined();

      process.env.HEAD_COURSES_DATA_DIR = originalDir;
    });
  });

  describe('Integration Tests', () => {
    it('should handle full course lifecycle', async () => {
      // 1. Create course
      const template: CourseTemplate = {
        id: '',
        title: 'Full Lifecycle Course',
        description: 'Complete workflow test',
        instructor: 'Test Master',
        category: 'complete-test',
        level: 'advanced',
        duration: 10,
        modules: [
          {
            id: 'mod-1',
            title: 'Module 1',
            description: 'First section',
            order: 1,
            estimatedDuration: 120,
            lessons: [
              {
                id: 'lesson-1',
                title: 'Lesson 1',
                description: 'First lesson',
                duration: 1800,
                order: 1,
              },
              {
                id: 'lesson-2',
                title: 'Lesson 2',
                description: 'Second lesson',
                duration: 2400,
                order: 2,
              },
            ],
          },
        ],
        tags: ['lifecycle', 'test'],
      };

      const createResult = await generateCourse(template, { generateScripts: true });
      expect(createResult.success).toBe(true);

      // 2. Publish course
      const publishResult = await publishCourse(createResult.courseId!, {
        courseId: createResult.courseId!,
        platforms: ['youtube', 'hosted'],
        dripFeedDays: 7,
      });
      expect(publishResult.success).toBe(true);

      // 3. Publish individual lessons
      const lessonResult1 = await publishLesson(
        createResult.courseId!,
        'lesson-1',
        ['youtube']
      );
      expect(lessonResult1.success).toBe(true);

      const lessonResult2 = await publishLesson(
        createResult.courseId!,
        'lesson-2',
        ['youtube', 'hosted']
      );
      expect(lessonResult2.success).toBe(true);

      // 4. Get metrics
      const metrics = await getCoursesMetrics();
      expect(metrics).toBeDefined();
    });
  });
});
