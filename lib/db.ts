import { Pool, PoolClient } from 'pg';

let pool: Pool | null = null;

export function getPool(): Pool {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL || process.env.POSTGRES_CONNECTION_STRING;

    if (!connectionString) {
      throw new Error(
        'DATABASE_URL or POSTGRES_CONNECTION_STRING environment variable is required. ' +
        'For local development, use: postgres://profitengine:password@localhost:5432/profitengine'
      );
    }

    pool = new Pool({
      connectionString,
      // Connection pool settings
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    pool.on('error', (err: Error) => {
      console.error('Unexpected error on idle client', err);
    });
  }

  return pool;
}

export async function query(text: string, params?: unknown[]) {
  const pool = getPool();
  return pool.query(text, params);
}

export async function getClient(): Promise<PoolClient> {
  const pool = getPool();
  return pool.connect();
}

export async function closePool() {
  if (pool) {
    await pool.end();
    pool = null;
  }
}

// Helper: Execute a query and return the first row
export async function queryOne<T = any>(
  text: string,
  params?: unknown[]
): Promise<T | null> {
  const result = await query(text, params);
  return result.rows[0] || null;
}

// Helper: Execute a query and return all rows
export async function queryAll<T = any>(
  text: string,
  params?: unknown[]
): Promise<T[]> {
  const result = await query(text, params);
  return result.rows;
}

// Transaction helper
export async function withTransaction<T>(
  callback: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await getClient();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}
