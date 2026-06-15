// Job utilities and types
import { Session } from 'next-auth';

export type Job = {
  id: string;
  title: string;
  category: string;
  location: string;
  pay: number;
  miles: number;
  margin: number;
  description: string;
  photos: string[];
  status: 'open' | 'accepted' | 'completed' | 'cancelled';
  created_by_id: string;
  accepted_by_id?: string;
  created_at: string;
  accepted_at?: string;
  completed_at?: string;
  source: string;
  notes?: string;
};

export type CreateJobInput = {
  title: string;
  category: string;
  location: string;
  pay: number;
  miles: number;
  description?: string;
};

export const JOB_CATEGORIES = [
  'Hauling',
  'Junk Removal',
  'Cleaning',
  'Pressure Washing',
  'Window Cleaning',
  'Handyman',
  'Landscaping',
  'Moving',
  'Delivery',
  'Other',
];

export const CATEGORY_ICONS: Record<string, string> = {
  'Hauling': '🚚',
  'Junk Removal': '♻️',
  'Cleaning': '🧹',
  'Pressure Washing': '💦',
  'Window Cleaning': '🪟',
  'Handyman': '🔨',
  'Landscaping': '🌱',
  'Moving': '📦',
  'Delivery': '📮',
  'Other': '⭐',
};

export function validateJobInput(input: Partial<CreateJobInput>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!input.title || input.title.trim().length === 0) {
    errors.push('Job title is required');
  } else if (input.title.length > 200) {
    errors.push('Job title must be 200 characters or less');
  }

  if (!input.category || !JOB_CATEGORIES.includes(input.category)) {
    errors.push('Valid job category is required');
  }

  if (!input.location || input.location.trim().length === 0) {
    errors.push('Location is required');
  }

  if (!input.pay || input.pay < 300) {
    errors.push('Minimum pay is $300');
  } else if (input.pay > 100000) {
    errors.push('Maximum pay is $100,000');
  }

  if (input.miles === undefined || input.miles < 0 || input.miles > 35) {
    errors.push('Miles must be between 0 and 35');
  }

  // XSS protection: check for script tags
  const dangerousPatterns = /<script|onerror|onload|javascript:|data:/i;
  if (dangerousPatterns.test(input.title || '') || dangerousPatterns.test(input.description || '')) {
    errors.push('Invalid characters in input');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export function sanitizeInput(text: string): string {
  return text
    .replace(/[<>"'`;&|]/g, '')
    .trim()
    .slice(0, 500);
}

export function calculateMargin(pay: number, miles: number): number {
  return Math.max(0, pay - miles * 0.72);
}
