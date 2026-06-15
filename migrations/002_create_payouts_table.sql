-- Migration: Create contractor accounts and payouts tables for Stripe Connect
-- Run: psql postgresql://profitengine:password@localhost/profitengine < migrations/002_create_payouts_table.sql

-- Table for tracking contractor Stripe Connect accounts
CREATE TABLE IF NOT EXISTS contractor_accounts (
  contractor_id UUID PRIMARY KEY,
  contractor_stripe_account VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for tracking payouts to contractors
CREATE TABLE IF NOT EXISTS payouts (
  id BIGSERIAL PRIMARY KEY,
  job_id BIGINT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  contractor_id UUID NOT NULL REFERENCES contractor_accounts(contractor_id),
  contractor_stripe_account VARCHAR(255),
  amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
  currency VARCHAR(3) DEFAULT 'usd',
  stripe_transfer_id VARCHAR(255),
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for efficient querying
CREATE INDEX idx_payouts_contractor ON payouts(contractor_id);
CREATE INDEX idx_payouts_job ON payouts(job_id);
CREATE INDEX idx_payouts_status ON payouts(status);
CREATE INDEX idx_payouts_stripe_transfer ON payouts(stripe_transfer_id) WHERE stripe_transfer_id IS NOT NULL;
CREATE INDEX idx_payouts_created_at ON payouts(created_at DESC);
