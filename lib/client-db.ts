// Client database module — types and database operations for multi-tenant Stripe integration

export interface Client {
  id: string;
  email: string;
  business_name: string;
  status: 'registered' | 'stripe_connected' | 'testing' | 'live' | 'suspended';
  api_key: string;
  created_at: number;
  stripe_account_id: string | null;
  stripe_test_mode: boolean;
  webhook_url: string | null;
  commission_rate: number;
}

export interface Transaction {
  id: string;
  client_id: string;
  stripe_charge_id: string;
  amount: number;
  status: 'pending' | 'succeeded' | 'failed';
  webhook_event_id: string | null;
  webhook_delivered: boolean;
  webhook_response_code: number | null;
  created_at: number;
  updated_at: number;
}

// In-memory storage for build-time operations (before database is ready)
const clientStore = new Map<string, Client>();
const transactionStore = new Map<string, Transaction[]>();

// Attempt to load database driver — @ts-ignore allows compilation even if pg isn't installed
let db: any = null;
try {
  // When pg is installed and configured, swap this for real database calls
  const { Pool } = require('pg');
  db = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
  });
} catch (error) {
  // Fallback: use in-memory store during build/development without pg
  console.log('[client-db] Running in memory-only mode (pg not configured)');
}

function generateClientId(): string {
  return `client_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function generateApiKey(): string {
  return `pk_${Buffer.from(Math.random().toString()).toString('base64').slice(0, 24)}`;
}

export async function createClient(
  email: string,
  business_name: string
): Promise<Client> {
  const client: Client = {
    id: generateClientId(),
    email,
    business_name,
    status: 'registered',
    api_key: generateApiKey(),
    created_at: Date.now(),
    stripe_account_id: null,
    stripe_test_mode: true,
    webhook_url: null,
    commission_rate: 2.5,
  };

  if (db) {
    try {
      const result = await db.query(
        `INSERT INTO clients (id, email, business_name, status, api_key, created_at, commission_rate)
         VALUES ($1, $2, $3, $4, $5, $6, $7)
         RETURNING *`,
        [
          client.id,
          email,
          business_name,
          client.status,
          client.api_key,
          client.created_at,
          client.commission_rate,
        ]
      );
      return result.rows[0];
    } catch (error) {
      console.error('Failed to create client in database:', error);
    }
  }

  // Fallback to in-memory storage
  clientStore.set(client.id, client);
  return client;
}

export async function getClientByEmail(email: string): Promise<Client | null> {
  if (db) {
    try {
      const result = await db.query(
        'SELECT * FROM clients WHERE email = $1',
        [email]
      );
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to get client by email:', error);
    }
  }

  // Fallback to in-memory search
  for (const client of Array.from(clientStore.values())) {
    if (client.email === email) return client;
  }
  return null;
}

export async function getClient(client_id: string): Promise<Client | null> {
  if (db) {
    try {
      const result = await db.query(
        'SELECT * FROM clients WHERE id = $1',
        [client_id]
      );
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to get client:', error);
    }
  }

  // Fallback to in-memory lookup
  return clientStore.get(client_id) || null;
}

export async function getClientByStripeAccount(
  stripe_account_id: string
): Promise<Client | null> {
  if (db) {
    try {
      const result = await db.query(
        'SELECT * FROM clients WHERE stripe_account_id = $1',
        [stripe_account_id]
      );
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to get client by stripe account:', error);
    }
  }

  // Fallback to in-memory search
  for (const client of Array.from(clientStore.values())) {
    if (client.stripe_account_id === stripe_account_id) return client;
  }
  return null;
}

export async function updateClient(
  client_id: string,
  updates: Partial<Client>
): Promise<Client | null> {
  const updateFields: string[] = [];
  const values: any[] = [];
  let paramIndex = 1;

  // Build dynamic UPDATE query
  for (const [key, value] of Object.entries(updates)) {
    if (key !== 'id') {
      updateFields.push(`${key} = $${paramIndex}`);
      values.push(value);
      paramIndex++;
    }
  }

  if (updateFields.length === 0) {
    return getClient(client_id);
  }

  values.push(client_id);

  if (db) {
    try {
      const query = `UPDATE clients SET ${updateFields.join(', ')} WHERE id = $${paramIndex} RETURNING *`;
      const result = await db.query(query, values);
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to update client:', error);
    }
  }

  // Fallback to in-memory update
  const client = clientStore.get(client_id);
  if (client) {
    const updated = { ...client, ...updates };
    clientStore.set(client_id, updated);
    return updated;
  }
  return null;
}

export async function logTransaction(transaction: Transaction): Promise<void> {
  if (db) {
    try {
      await db.query(
        `INSERT INTO client_events (id, client_id, stripe_charge_id, amount, status, webhook_event_id, webhook_delivered, webhook_response_code, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [
          transaction.id,
          transaction.client_id,
          transaction.stripe_charge_id,
          transaction.amount,
          transaction.status,
          transaction.webhook_event_id,
          transaction.webhook_delivered,
          transaction.webhook_response_code,
          transaction.created_at,
          transaction.updated_at,
        ]
      );
    } catch (error) {
      console.error('Failed to log transaction:', error);
    }
    return;
  }

  // Fallback to in-memory storage
  if (!transactionStore.has(transaction.client_id)) {
    transactionStore.set(transaction.client_id, []);
  }
  transactionStore.get(transaction.client_id)!.push(transaction);
}

export async function getTransaction(
  client_id: string,
  txn_id: string
): Promise<Transaction | null> {
  if (db) {
    try {
      const result = await db.query(
        'SELECT * FROM client_events WHERE id = $1 AND client_id = $2',
        [txn_id, client_id]
      );
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to get transaction:', error);
    }
  }

  // Fallback to in-memory lookup
  const transactions = transactionStore.get(client_id) || [];
  return transactions.find((t) => t.id === txn_id) || null;
}

export async function updateTransaction(
  client_id: string,
  txn_id: string,
  updates: Partial<Transaction>
): Promise<Transaction | null> {
  const updateFields: string[] = [];
  const values: any[] = [];
  let paramIndex = 1;

  for (const [key, value] of Object.entries(updates)) {
    if (key !== 'id' && key !== 'client_id') {
      updateFields.push(`${key} = $${paramIndex}`);
      values.push(value);
      paramIndex++;
    }
  }

  if (updateFields.length === 0) {
    return getTransaction(client_id, txn_id);
  }

  values.push(txn_id);
  values.push(client_id);

  if (db) {
    try {
      const query = `UPDATE client_events SET ${updateFields.join(', ')} WHERE id = $${paramIndex} AND client_id = $${paramIndex + 1} RETURNING *`;
      const result = await db.query(query, values);
      return result.rows[0] || null;
    } catch (error) {
      console.error('Failed to update transaction:', error);
    }
  }

  // Fallback to in-memory update
  const transaction = await getTransaction(client_id, txn_id);
  if (transaction) {
    const updated = { ...transaction, ...updates };
    const transactions = transactionStore.get(client_id) || [];
    const index = transactions.findIndex((t) => t.id === txn_id);
    if (index >= 0) {
      transactions[index] = updated;
    }
    return updated;
  }
  return null;
}

export async function getClientTransactions(
  client_id: string
): Promise<Transaction[]> {
  if (db) {
    try {
      const result = await db.query(
        'SELECT * FROM client_events WHERE client_id = $1 ORDER BY created_at DESC',
        [client_id]
      );
      return result.rows;
    } catch (error) {
      console.error('Failed to get client transactions:', error);
    }
  }

  // Fallback to in-memory retrieval
  return transactionStore.get(client_id) || [];
}

export async function calculateClientCommission(
  client_id: string
): Promise<number> {
  const transactions = await getClientTransactions(client_id);
  const successful = transactions.filter((t) => t.status === 'succeeded');
  const totalVolume = successful.reduce((sum, t) => sum + t.amount, 0);
  return Math.round(totalVolume * 0.025); // 2.5% commission
}
