import type { Contact } from '../types';

export function ensureIndexes(): Promise<void>;

export interface FindContactsOptions {
  companyId?: string | import('mongodb').ObjectId;
  search?: string;
  contactStatus?: string;
  consentStatus?: string;
  sortBy?: string;
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export function findContacts(options?: FindContactsOptions): Promise<{ records: Contact[]; total: number; page: number; limit: number }>;
export function getContactById(id: string | import('mongodb').ObjectId): Promise<Contact | null>;
export function createContact(doc: Partial<Contact>): Promise<Contact>;
export function updateContact(id: string | import('mongodb').ObjectId, updates: Partial<Contact>): Promise<Contact | null>;
