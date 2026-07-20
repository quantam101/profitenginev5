export type OutreachStatus = 'queued' | 'approved' | 'sending' | 'sent' | 'failed';

export type OutreachRecipient = {
  to: string[];
  cc?: string[];
  bcc?: string[];
};

export type OutreachMessage = {
  id: string;
  company: string;
  lane: string;
  recipients: OutreachRecipient;
  subject: string;
  body: string;
  status: OutreachStatus;
  source?: string;
  leadUrl?: string;
  approvedBy?: string;
  approvedAt?: string;
  sentAt?: string;
  gmailMessageId?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
};

export type CreateOutreachInput = Omit<OutreachMessage, 'id' | 'status' | 'createdAt' | 'updatedAt' | 'approvedAt' | 'sentAt' | 'gmailMessageId' | 'error'>;
