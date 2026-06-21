/**
 * Multi-tenant Client Database Schema & Operations
 *
 * Stores client account data in JSON files under .runtime/clients/
 * Each client gets a unique ID and directory with their data
 */

import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';

// Base directory for client data
const CLIENTS_DIR = path.join(process.cwd(), '.runtime', 'clients');

// Ensure clients directory exists
export function ensureClientsDir() {
  if (!fs.existsSync(CLIENTS_DIR)) {
    fs.mkdirSync(CLIENTS_DIR, { recursive: true });
  }
}

/**
 * Client Account Model
 */
export interface Client {
  id: string; // UUID
  email: string;
  business_name: string;
  stripe_account_id: string | null; // from Stripe Connect OAuth
  stripe_test_mode: boolean;
  status: 'signup' | 'stripe_connected' | 'testing' | 'live';
  commission_rate: number; // 2.5% default
  api_key: string; // for webhook authentication
  webhook_url: string | null; // where to send client events
  created_at: number; // timestamp
  updated_at: number;
}

/**
 * Transaction Log Model (for tracking payments)
 */
export interface Transaction {
  id: string; // UUID
  client_id: string;
  stripe_charge_id: string;
  amount: number; // in cents
  status: 'pending' | 'succeeded' | 'failed' | 'refunded';
  webhook_event_id: string | null;
  webhook_delivered: boolean;
  webhook_response_code: number | null;
  created_at: number;
  updated_at: number;
}

/**
 * Generate unique API key for client
 */
function generateApiKey(): string {
  return `sk_${randomUUID().replace(/-/g, '')}_${Date.now().toString(36)}`;
}

/**
 * Get client data file path
 */
function getClientPath(clientId: string): string {
  return path.join(CLIENTS_DIR, clientId, 'client.json');
}

/**
 * Get transactions directory for client
 */
function getTransactionsDir(clientId: string): string {
  return path.join(CLIENTS_DIR, clientId, 'transactions');
}

/**
 * Create new client account
 */
export async function createClient(
  email: string,
  businessName: string
): Promise<Client> {
  ensureClientsDir();

  const clientId = randomUUID();
  const apiKey = generateApiKey();
  const now = Date.now();

  const client: Client = {
    id: clientId,
    email,
    business_name: businessName,
    stripe_account_id: null,
    stripe_test_mode: true,
    status: 'signup',
    commission_rate: 2.5,
    api_key: apiKey,
    webhook_url: null,
    created_at: now,
    updated_at: now,
  };

  // Create client directory
  const clientDir = path.join(CLIENTS_DIR, clientId);
  fs.mkdirSync(clientDir, { recursive: true });
  fs.mkdirSync(path.join(clientDir, 'transactions'), { recursive: true });

  // Save client data
  fs.writeFileSync(
    getClientPath(clientId),
    JSON.stringify(client, null, 2)
  );

  return client;
}

/**
 * Get client by ID
 */
export async function getClient(clientId: string): Promise<Client | null> {
  ensureClientsDir();

  try {
    const filePath = getClientPath(clientId);
    if (!fs.existsSync(filePath)) {
      return null;
    }
    const data = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Failed to get client ${clientId}:`, error);
    return null;
  }
}

/**
 * Get client by email
 */
export async function getClientByEmail(email: string): Promise<Client | null> {
  ensureClientsDir();

  try {
    // List all client IDs
    if (!fs.existsSync(CLIENTS_DIR)) {
      return null;
    }

    const clientIds = fs.readdirSync(CLIENTS_DIR);
    for (const clientId of clientIds) {
      const client = await getClient(clientId);
      if (client && client.email === email) {
        return client;
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to search clients by email:', error);
    return null;
  }
}

/**
 * Get client by API key
 */
export async function getClientByApiKey(apiKey: string): Promise<Client | null> {
  ensureClientsDir();

  try {
    if (!fs.existsSync(CLIENTS_DIR)) {
      return null;
    }

    const clientIds = fs.readdirSync(CLIENTS_DIR);
    for (const clientId of clientIds) {
      const client = await getClient(clientId);
      if (client && client.api_key === apiKey) {
        return client;
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to search clients by API key:', error);
    return null;
  }
}

/**
 * Get client by Stripe Account ID
 */
export async function getClientByStripeAccount(stripeAccountId: string): Promise<Client | null> {
  ensureClientsDir();

  try {
    if (!fs.existsSync(CLIENTS_DIR)) {
      return null;
    }

    const clientIds = fs.readdirSync(CLIENTS_DIR);
    for (const clientId of clientIds) {
      const client = await getClient(clientId);
      if (client && client.stripe_account_id === stripeAccountId) {
        return client;
      }
    }
    return null;
  } catch (error) {
    console.error('Failed to search clients by Stripe account:', error);
    return null;
  }
}

/**
 * Update client status and fields
 */
export async function updateClient(
  clientId: string,
  updates: Partial<Client>
): Promise<Client | null> {
  ensureClientsDir();

  try {
    const client = await getClient(clientId);
    if (!client) {
      return null;
    }

    const updated: Client = {
      ...client,
      ...updates,
      id: client.id, // prevent ID change
      api_key: client.api_key, // prevent API key change
      created_at: client.created_at, // prevent creation time change
      updated_at: Date.now(),
    };

    fs.writeFileSync(
      getClientPath(clientId),
      JSON.stringify(updated, null, 2)
    );

    return updated;
  } catch (error) {
    console.error(`Failed to update client ${clientId}:`, error);
    return null;
  }
}

/**
 * List all clients (for admin dashboard)
 */
export async function listClients(): Promise<Client[]> {
  ensureClientsDir();

  try {
    if (!fs.existsSync(CLIENTS_DIR)) {
      return [];
    }

    const clientIds = fs.readdirSync(CLIENTS_DIR);
    const clients: Client[] = [];

    for (const clientId of clientIds) {
      const client = await getClient(clientId);
      if (client) {
        clients.push(client);
      }
    }

    return clients;
  } catch (error) {
    console.error('Failed to list clients:', error);
    return [];
  }
}

/**
 * Log transaction for a client
 */
export async function logTransaction(transaction: Transaction): Promise<void> {
  ensureClientsDir();

  try {
    const transactionsDir = getTransactionsDir(transaction.client_id);
    fs.mkdirSync(transactionsDir, { recursive: true });

    const filePath = path.join(transactionsDir, `${transaction.id}.json`);
    fs.writeFileSync(filePath, JSON.stringify(transaction, null, 2));
  } catch (error) {
    console.error(`Failed to log transaction for client ${transaction.client_id}:`, error);
  }
}

/**
 * Get transaction by ID
 */
export async function getTransaction(
  clientId: string,
  transactionId: string
): Promise<Transaction | null> {
  ensureClientsDir();

  try {
    const filePath = path.join(
      getTransactionsDir(clientId),
      `${transactionId}.json`
    );
    if (!fs.existsSync(filePath)) {
      return null;
    }
    const data = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Failed to get transaction ${transactionId}:`, error);
    return null;
  }
}

/**
 * Update transaction status (webhook delivery, etc)
 */
export async function updateTransaction(
  clientId: string,
  transactionId: string,
  updates: Partial<Transaction>
): Promise<Transaction | null> {
  ensureClientsDir();

  try {
    const transaction = await getTransaction(clientId, transactionId);
    if (!transaction) {
      return null;
    }

    const updated: Transaction = {
      ...transaction,
      ...updates,
      id: transaction.id, // prevent ID change
      client_id: transaction.client_id, // prevent client ID change
      updated_at: Date.now(),
    };

    const filePath = path.join(
      getTransactionsDir(clientId),
      `${transactionId}.json`
    );
    fs.writeFileSync(filePath, JSON.stringify(updated, null, 2));

    return updated;
  } catch (error) {
    console.error(`Failed to update transaction ${transactionId}:`, error);
    return null;
  }
}

/**
 * Get all transactions for a client (optionally filtered by date)
 */
export async function getClientTransactions(
  clientId: string,
  sinceTimestamp?: number
): Promise<Transaction[]> {
  ensureClientsDir();

  try {
    const transactionsDir = getTransactionsDir(clientId);
    if (!fs.existsSync(transactionsDir)) {
      return [];
    }

    const files = fs.readdirSync(transactionsDir);
    const transactions: Transaction[] = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        const data = fs.readFileSync(path.join(transactionsDir, file), 'utf-8');
        const txn: Transaction = JSON.parse(data);
        if (!sinceTimestamp || txn.created_at >= sinceTimestamp) {
          transactions.push(txn);
        }
      }
    }

    return transactions.sort((a, b) => b.created_at - a.created_at);
  } catch (error) {
    console.error(`Failed to get transactions for client ${clientId}:`, error);
    return [];
  }
}

/**
 * Calculate commission earned by client
 */
export async function calculateClientCommission(
  clientId: string,
  sinceTimestamp?: number
): Promise<number> {
  const transactions = await getClientTransactions(clientId, sinceTimestamp);
  const client = await getClient(clientId);

  if (!client) {
    return 0;
  }

  const totalVolume = transactions
    .filter((t) => t.status === 'succeeded')
    .reduce((sum, t) => sum + t.amount, 0);

  return Math.round(totalVolume * (client.commission_rate / 100));
}
