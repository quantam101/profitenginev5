import type { Company } from '../types';

export function ensureIndexes(): Promise<void>;
export function normalizeDomain(website?: string): string;
export function normalizeCompanyName(name?: string): string;
export function buildDuplicateKey(company: Partial<Company>): string;

export interface FindCompaniesOptions {
  industry?: string;
  companyType?: string;
  search?: string;
  qualificationStatus?: string;
  sortBy?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export function findCompanies(options?: FindCompaniesOptions): Promise<{ records: Company[]; total: number; page: number; limit: number }>;
export function getCompanyById(id: string | import('mongodb').ObjectId): Promise<Company | null>;
export function getCompanyByDuplicateKey(key: string): Promise<Company | null>;
export function createCompany(doc: Partial<Company>): Promise<Company>;
export function updateCompany(id: string | import('mongodb').ObjectId, updates: Partial<Company>): Promise<Company | null>;
