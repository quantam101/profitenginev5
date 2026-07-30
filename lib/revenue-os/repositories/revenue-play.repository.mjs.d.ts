import type { RevenuePlay } from '../types';

export interface FindRevenuePlaysOptions {
  lane?: string;
  buyerType?: string;
  location?: string;
  status?: string;
  minScore?: number;
  search?: string;
  sortBy?: keyof RevenuePlay;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface FindRevenuePlaysResult {
  records: RevenuePlay[];
  total: number;
  page: number;
  limit: number;
}

export function ensureIndexes(): Promise<void>;
export function countRevenuePlays(filter?: Record<string, unknown>): Promise<number>;
export function findRevenuePlays(options?: FindRevenuePlaysOptions): Promise<FindRevenuePlaysResult>;
export function getRevenuePlayByRecordId(recordId: string): Promise<RevenuePlay | null>;
export function getRevenuePlayById(id: string): Promise<RevenuePlay | null>;
export function upsertRevenuePlay(doc: RevenuePlay): Promise<{
  upsertedId: any;
  modifiedCount: number;
  matchedCount: number;
}>;
