import { randomUUID } from 'node:crypto';
import { sendGmailMessage } from './gmail-sender';
import { notifyOutreach } from './notify';
import { getOutreach, insertOutreach, listOutreach, updateOutreach } from './store';
import type { CreateOutreachInput, OutreachMessage } from './types';

export async function createOutreach(input: CreateOutreachInput) {
  const now = new Date().toISOString();
  const message: OutreachMessage = {
    ...input,
    id: randomUUID(),
    status: 'queued',
    createdAt: now,
    updatedAt: now,
  };
  await insertOutreach(message);
  await notifyOutreach('queued', message);
  return message;
}

export async function approveMessage(id: string, approvedBy = 'Stephen Franklin') {
  const current = await getOutreach(id);
  if (!current) throw Object.assign(new Error('Outreach message not found'), { status: 404 });
  if (current.status === 'sent') return current;
  const updated = await updateOutreach(id, {
    status: 'approved',
    approvedBy,
    approvedAt: new Date().toISOString(),
    error: '',
  });
  if (!updated) throw Object.assign(new Error('Outreach message not found'), { status: 404 });
  await notifyOutreach('approved', updated);
  return updated;
}

export async function sendMessage(id: string) {
  const current = await getOutreach(id);
  if (!current) throw Object.assign(new Error('Outreach message not found'), { status: 404 });
  if (current.status === 'sent') return current;
  if (current.status !== 'approved') throw Object.assign(new Error('Outreach must be approved before sending'), { status: 409 });

  await updateOutreach(id, { status: 'sending', error: '' });
  try {
    const result = await sendGmailMessage(current);
    const sent = await updateOutreach(id, {
      status: 'sent',
      sentAt: new Date().toISOString(),
      gmailMessageId: result.id,
      error: '',
    });
    if (!sent) throw new Error('Outreach disappeared after send');
    await notifyOutreach('sent', sent);
    return sent;
  } catch (error) {
    const failed = await updateOutreach(id, {
      status: 'failed',
      error: error instanceof Error ? error.message : String(error),
    });
    if (failed) await notifyOutreach('failed', failed);
    throw error;
  }
}

export { listOutreach };
