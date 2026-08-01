import type { Opportunity } from '../types';

export const OPPORTUNITY_STAGES: string[];

export function ensureIndexes(): Promise<void>;
export function isActiveOpportunity(doc: Opportunity | null): boolean;
export function isTerminalStage(stage: string): boolean;
export function getNextStage(currentStage: string): string | undefined;

export interface FindOpportunitiesOptions {
  stage?: string;
  companyId?: string | import('mongodb').ObjectId;
  revenuePlayId?: string | import('mongodb').ObjectId;
  assignedTo?: string;
  search?: string;
  active?: boolean;
  sortBy?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export function findOpportunities(options?: FindOpportunitiesOptions): Promise<{ records: Opportunity[]; total: number; page: number; limit: number }>;
export function getOpportunityById(id: string | import('mongodb').ObjectId): Promise<Opportunity | null>;
export function createOpportunity(doc: Partial<Opportunity>): Promise<Opportunity>;
export function updateOpportunity(id: string | import('mongodb').ObjectId, updates: Partial<Opportunity>): Promise<Opportunity | null>;
export function updateOpportunityStage(id: string | import('mongodb').ObjectId, stage: string): Promise<Opportunity | null>;
export interface DashboardStats {
  activeOpportunities: number;
  weightedPipelineValue: number;
  monthlyRecurringPotential: number;
  averageOpportunityScore: number;
  fastCashOpportunities: number;
}

export function countOpportunitiesByStage(): Promise<Record<string, { count: number; value: number }>>;
export function aggregateDashboardStats(): Promise<DashboardStats>;
