import type { Activity } from '../types';

export function ensureIndexes(): Promise<void>;

export interface CreateActivityInput {
  entityType: string;
  entityId: string | import('mongodb').ObjectId;
  actionType: string;
  actor: string;
  summary: string;
  metadata?: Record<string, unknown>;
}

export function createActivity(input: CreateActivityInput): Promise<Activity>;

export interface FindActivitiesOptions {
  entityType?: string;
  entityId?: string | import('mongodb').ObjectId;
  actor?: string;
  limit?: number;
  page?: number;
}

export function findActivities(options?: FindActivitiesOptions): Promise<{ records: Activity[]; total: number; page: number; limit: number }>;
