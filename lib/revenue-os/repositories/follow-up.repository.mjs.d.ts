import type { FollowUpTask } from '../types';

export function ensureIndexes(): Promise<void>;

export interface CreateFollowUpInput {
  entityType: string;
  entityId: string | import('mongodb').ObjectId;
  type?: string;
  summary: string;
  dueDate: Date | string;
  status?: 'OPEN' | 'COMPLETED' | 'SNOOZED' | 'CANCELLED';
  assignedTo?: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
  completedAt?: Date | string;
}

export function createFollowUp(input: CreateFollowUpInput): Promise<FollowUpTask>;

export interface FindFollowUpsOptions {
  entityType?: string;
  entityId?: string | import('mongodb').ObjectId;
  status?: string;
  assignedTo?: string;
  dueBefore?: Date | string;
  dueAfter?: Date | string;
  sortBy?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export function findFollowUps(options?: FindFollowUpsOptions): Promise<{ records: FollowUpTask[]; total: number; page: number; limit: number }>;
export function getFollowUpById(id: string | import('mongodb').ObjectId): Promise<FollowUpTask | null>;
export function completeFollowUp(id: string | import('mongodb').ObjectId, actor: string): Promise<FollowUpTask | null>;
export function countOpenFollowUpsDueBy(date?: Date | string): Promise<number>;
export function countOpenFollowUpsDueBefore(date?: Date | string): Promise<number>;
