#!/usr/bin/env node
/**
 * Database initialization script
 * Run migrations and set up PostgreSQL for ProfitEngine
 *
 * Usage:
 *   npx ts-node scripts/init-db.ts [--seed]
 *   DATABASE_URL="postgres://..." npx ts-node scripts/init-db.ts
 */

import { Pool } from 'pg';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATABASE_URL =
  process.env.DATABASE_URL ||
  process.env.POSTGRES_CONNECTION_STRING ||
  'postgres://profitengine:password@localhost:5432/profitengine';

const MIGRATIONS_DIR = path.join(__dirname, '../migrations');
const shouldSeed = process.argv.includes('--seed');

async function runMigrations() {
  const pool = new Pool({ connectionString: DATABASE_URL });

  try {
    console.log('🔄 Connecting to PostgreSQL...');
    const client = await pool.connect();
    const version = await client.query('SELECT version()');
    console.log('✅ Connected to:', version.rows[0].version.split(',')[0]);
    client.release();

    // Get all migration files
    const migrationFiles = fs
      .readdirSync(MIGRATIONS_DIR)
      .filter((f) => f.endsWith('.sql'))
      .sort();

    if (migrationFiles.length === 0) {
      console.log('⚠️  No migrations found in', MIGRATIONS_DIR);
      return;
    }

    console.log(`\n📋 Found ${migrationFiles.length} migration(s)`);

    for (const file of migrationFiles) {
      const filePath = path.join(MIGRATIONS_DIR, file);
      const sql = fs.readFileSync(filePath, 'utf-8');

      console.log(`\n▶️  Running: ${file}`);
      try {
        await pool.query(sql);
        console.log(`   ✅ ${file}`);
      } catch (error) {
        console.error(`   ❌ ${file}`);
        console.error('   Error:', (error as Error).message);
        throw error;
      }
    }

    console.log('\n✨ All migrations completed successfully!');

    if (shouldSeed) {
      console.log('\n🌱 Seeding database with sample data...');
      await seedDatabase(pool);
    }
  } catch (error) {
    console.error('\n❌ Migration failed:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

async function seedDatabase(pool: Pool) {
  try {
    // Seed sample jobs
    const sampleJobs = [
      {
        title: 'Remove 3 couches + debris',
        category: 'Junk Removal',
        location: 'Phoenix, AZ',
        pay: 350,
        miles: 8,
        description: 'Estate sale cleanup',
      },
      {
        title: 'Pressure wash driveway and deck',
        category: 'Pressure Washing',
        location: 'Tempe, AZ',
        pay: 275,
        miles: 5,
        description: '2000 sq ft driveway + 500 sq ft deck',
      },
      {
        title: 'Remove fence + haul debris',
        category: 'Hauling',
        location: 'Mesa, AZ',
        pay: 450,
        miles: 12,
        description: '200 linear feet wood fence',
      },
    ];

    for (const job of sampleJobs) {
      await pool.query(
        `INSERT INTO jobs (title, category, location, pay, miles, description, created_by_id, source)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
         ON CONFLICT DO NOTHING`,
        [
          job.title,
          job.category,
          job.location,
          job.pay,
          job.miles,
          job.description,
          'seed-user',
          'seed',
        ]
      );
    }

    console.log(`✅ Seeded ${sampleJobs.length} sample jobs`);
  } catch (error) {
    console.error('❌ Seeding failed:', error);
    throw error;
  }
}

// Run migrations
runMigrations().then(() => {
  console.log('\n✅ Database initialization complete!');
  process.exit(0);
});
