-- Migration: Create jobs table for local services
-- Run: psql postgresql://profitengine:password@localhost/profitengine < migrations/001_create_jobs_table.sql

CREATE TABLE IF NOT EXISTS jobs (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  category VARCHAR(50) NOT NULL,
  location VARCHAR(200) NOT NULL,
  pay NUMERIC(10,2) NOT NULL CHECK (pay >= 300),
  miles NUMERIC(5,2) NOT NULL CHECK (miles >= 0 AND miles <= 35),
  margin NUMERIC(10,2) GENERATED ALWAYS AS (pay - miles * 0.72) STORED,
  description TEXT,
  photos JSONB DEFAULT '[]'::jsonb,
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'accepted', 'completed', 'cancelled')),
  created_by_id UUID NOT NULL,
  accepted_by_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  accepted_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  source VARCHAR(50) DEFAULT 'web',
  notes TEXT
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_category ON jobs(category);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_accepted_by ON jobs(accepted_by_id) WHERE status IN ('accepted', 'completed');
CREATE INDEX idx_jobs_created_by ON jobs(created_by_id);
