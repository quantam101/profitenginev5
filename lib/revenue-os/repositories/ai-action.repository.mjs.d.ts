import type { AIAction } from '../types';

export function ensureIndexes(): Promise<void>;
export function createAIAction(doc: Partial<AIAction>): Promise<AIAction>;
export function getAIActionById(id: string): Promise<AIAction | null>;
export function updateAIActionStatus(id: string, status: string, reviewer?: string): Promise<AIAction | null>;
export function findAIActions(options?: Record<string, unknown>): Promise<{ records: AIAction[]; total: number; page: number; limit: number }>;
export function deleteExpiredActions(before?: Date): Promise<{ deletedCount: number }>;
