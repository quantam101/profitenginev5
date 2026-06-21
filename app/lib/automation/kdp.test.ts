/**
 * KDP Automation Unit Tests
 *
 * Tests for:
 * - Book metadata parsing
 * - Metadata validation
 * - Publication risk assessment
 * - Platform recommendation
 * - Content formatting for different platforms
 */

import {
  validateBookMetadata,
  assessPublicationRisk,
  getRecommendedPlatforms,
  formatContentForKdp,
  formatContentForDraft2Digital,
  formatContentForSmashwords,
  BookMetadata,
} from './kdp';

describe('KDP Automation', () => {
  // ============================================================================
  // Test Data
  // ============================================================================

  const validMetadata: BookMetadata = {
    title: 'The Complete Guide to eBook Publishing',
    author: 'John Doe',
    description: 'Learn how to publish professional eBooks on multiple platforms.',
    category: 'Business',
    keywords: ['ebook', 'publishing', 'self-publishing', 'amazon'],
    price: 14.99,
    language: 'en',
  };

  // ============================================================================
  // Metadata Validation Tests
  // ============================================================================

  describe('validateBookMetadata', () => {
    it('should accept valid metadata', () => {
      const result = validateBookMetadata(validMetadata);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject missing title', () => {
      const metadata = { ...validMetadata, title: '' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Title is required');
    });

    it('should reject short title', () => {
      const metadata = { ...validMetadata, title: 'AB' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Title must be at least 3 characters'))).toBe(true);
    });

    it('should reject missing author', () => {
      const metadata = { ...validMetadata, author: '' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Author is required');
    });

    it('should reject missing description', () => {
      const metadata = { ...validMetadata, description: '' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Description is required');
    });

    it('should reject short description', () => {
      const metadata = { ...validMetadata, description: 'Too short' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Description should be at least 20 characters'))).toBe(true);
    });

    it('should reject missing keywords', () => {
      const metadata = { ...validMetadata, keywords: [] };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('At least one keyword is required');
    });

    it('should reject zero or negative price', () => {
      const metadata = { ...validMetadata, price: 0 };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Price must be greater than 0'))).toBe(true);
    });

    it('should reject price exceeding maximum', () => {
      const metadata = { ...validMetadata, price: 99.99 };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Price exceeds maximum'))).toBe(true);
    });

    it('should reject unsupported language', () => {
      const metadata = { ...validMetadata, language: 'xx' };
      const result = validateBookMetadata(metadata);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Unsupported language'))).toBe(true);
    });

    it('should accept supported languages', () => {
      for (const lang of ['en', 'es', 'fr', 'de']) {
        const metadata = { ...validMetadata, language: lang };
        const result = validateBookMetadata(metadata);
        expect(result.valid).toBe(true);
      }
    });
  });

  // ============================================================================
  // Risk Assessment Tests
  // ============================================================================

  describe('assessPublicationRisk', () => {
    it('should rate low-risk metadata as low', () => {
      const result = assessPublicationRisk(validMetadata);
      expect(result.riskLevel).toBe('low');
      expect(result.score).toBeLessThan(20);
    });

    it('should penalize very short titles', () => {
      const metadata = { ...validMetadata, title: 'Hi' };
      const result = assessPublicationRisk(metadata);
      expect(result.score).toBeGreaterThan(10);
    });

    it('should penalize very long titles', () => {
      const longTitle = 'A'.repeat(101);
      const metadata = { ...validMetadata, title: longTitle };
      const result = assessPublicationRisk(metadata);
      expect(result.warnings.some(w => w.includes('exceeds'))).toBe(true);
    });

    it('should penalize brief descriptions', () => {
      const metadata = {
        ...validMetadata,
        description: 'This is a book about publishing.',
      };
      const result = assessPublicationRisk(metadata);
      expect(result.score).toBeGreaterThan(0);
    });

    it('should penalize few keywords', () => {
      const metadata = { ...validMetadata, keywords: ['ebook'] };
      const result = assessPublicationRisk(metadata);
      expect(result.warnings.some(w => w.includes('fewer than 3 keywords'))).toBe(true);
    });

    it('should warn about missing ISBN', () => {
      const result = assessPublicationRisk(validMetadata);
      expect(result.warnings.some(w => w.includes('ISBN'))).toBe(true);
    });

    it('should rate high-risk metadata correctly', () => {
      const risky = {
        title: 'X',
        author: 'A',
        description: 'Too short',
        category: 'Unknown',
        keywords: [],
        price: 1,
      };
      const result = assessPublicationRisk(risky);
      expect(result.riskLevel).toBe('high');
      expect(result.score).toBeGreaterThan(40);
    });
  });

  // ============================================================================
  // Platform Recommendation Tests
  // ============================================================================

  describe('getRecommendedPlatforms', () => {
    it('should recommend KDP for English books', () => {
      const platforms = getRecommendedPlatforms(validMetadata);
      expect(platforms).toContain('kdp');
    });

    it('should recommend D2D for ebook-focused books', () => {
      const metadata = {
        ...validMetadata,
        keywords: ['ebook', 'digital publishing'],
      };
      const platforms = getRecommendedPlatforms(metadata);
      expect(platforms).toContain('draft2digital');
    });

    it('should recommend Smashwords for self-help books', () => {
      const metadata = {
        ...validMetadata,
        category: 'Self-Help',
      };
      const platforms = getRecommendedPlatforms(metadata);
      expect(platforms).toContain('smashwords');
    });

    it('should recommend Smashwords for low-priced books', () => {
      const metadata = { ...validMetadata, price: 2.99 };
      const platforms = getRecommendedPlatforms(metadata);
      expect(platforms).toContain('smashwords');
    });

    it('should always include at least KDP', () => {
      const metadata = { ...validMetadata, keywords: [] };
      const platforms = getRecommendedPlatforms(metadata);
      expect(platforms.length).toBeGreaterThan(0);
      expect(platforms[0]).toBe('kdp');
    });
  });

  // ============================================================================
  // Content Formatting Tests
  // ============================================================================

  describe('Content Formatting', () => {
    const sampleContent = `---
title: Test Book
author: Test Author
---

# Chapter 1: Introduction

This is the introduction.

## Section 1.1

More content here.

### Subsection 1.1.1

Even more detail.
`;

    describe('formatContentForKdp', () => {
      it('should remove frontmatter', () => {
        const formatted = formatContentForKdp(sampleContent);
        expect(formatted).not.toContain('---');
        expect(formatted).not.toContain('title: Test Book');
      });

      it('should preserve headers', () => {
        const formatted = formatContentForKdp(sampleContent);
        expect(formatted).toContain('# Chapter 1');
        expect(formatted).toContain('## Section 1.1');
      });

      it('should remove script tags', () => {
        const contentWithScript = sampleContent + '<script>alert("test")</script>';
        const formatted = formatContentForKdp(contentWithScript);
        expect(formatted).not.toContain('<script>');
      });

      it('should remove iframe tags', () => {
        const contentWithIframe = sampleContent + '<iframe src="test"></iframe>';
        const formatted = formatContentForKdp(contentWithIframe);
        expect(formatted).not.toContain('<iframe>');
      });
    });

    describe('formatContentForDraft2Digital', () => {
      it('should remove frontmatter', () => {
        const formatted = formatContentForDraft2Digital(sampleContent);
        expect(formatted).not.toContain('---');
      });

      it('should convert markdown to HTML', () => {
        const markdown = '**bold** and *italic*';
        const formatted = formatContentForDraft2Digital(markdown);
        expect(formatted).toContain('<strong>bold</strong>');
        expect(formatted).toContain('<em>italic</em>');
      });

      it('should convert links to HTML', () => {
        const markdown = '[Link](https://example.com)';
        const formatted = formatContentForDraft2Digital(markdown);
        expect(formatted).toContain('<a href="https://example.com">Link</a>');
      });
    });

    describe('formatContentForSmashwords', () => {
      it('should remove frontmatter', () => {
        const formatted = formatContentForSmashwords(sampleContent);
        expect(formatted).not.toContain('---');
      });

      it('should normalize blank lines', () => {
        const contentWithBlanks = sampleContent + '\n\n\n\nMore content';
        const formatted = formatContentForSmashwords(contentWithBlanks);
        const blankLines = formatted.match(/\n\n\n/g);
        expect(blankLines).toBeNull();
      });
    });
  });

  // ============================================================================
  // Edge Cases and Integration
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle metadata with all optional fields', () => {
      const fullMetadata: BookMetadata = {
        title: 'Advanced Book Publishing',
        subtitle: 'A Comprehensive Guide',
        author: 'Jane Doe',
        description: 'Everything you need to know about modern book publishing.',
        category: 'Education',
        keywords: ['books', 'publishing', 'guides', 'education'],
        price: 24.99,
        currency: 'USD',
        language: 'en',
        isbn: '978-1-234567-89-0',
        issueNumber: '1',
        copyrightYear: 2024,
        publishedDate: '2024-06-20',
        publisher: 'Self Published',
        copyrightHolder: 'Jane Doe',
        maturityRating: 'G',
        publicationCountries: ['US', 'GB', 'CA'],
        series: {
          name: 'Complete Guides',
          number: 5,
        },
        contributors: [
          { name: 'Editor Name', role: 'Editor' },
        ],
      };

      const validation = validateBookMetadata(fullMetadata);
      expect(validation.valid).toBe(true);

      const assessment = assessPublicationRisk(fullMetadata);
      expect(assessment.riskLevel).toBe('low');
    });

    it('should handle content with mixed formatting', () => {
      const mixedContent = `
# Header

**Bold text**

*Italic text*

[Link text](https://example.com)

\`\`\`
code block
\`\`\`

- List item 1
- List item 2

1. Numbered item 1
2. Numbered item 2
`;

      const kdpFormatted = formatContentForKdp(mixedContent);
      const d2dFormatted = formatContentForDraft2Digital(mixedContent);
      const swFormatted = formatContentForSmashwords(mixedContent);

      expect(kdpFormatted.length).toBeGreaterThan(0);
      expect(d2dFormatted.length).toBeGreaterThan(0);
      expect(swFormatted.length).toBeGreaterThan(0);
    });
  });
});
