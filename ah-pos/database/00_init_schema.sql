-- AH-POS Database Schema
-- Past Performance, Capture Intelligence, Pricing & Wrap-Rate Models
-- PostgreSQL 14+

-- ============================================================================
-- PART 1: PAST PERFORMANCE DATABASE
-- ============================================================================

CREATE TABLE IF NOT EXISTS agencies (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  duns_number VARCHAR(20),
  cage_code VARCHAR(10),
  sam_gov_entity_id VARCHAR(100),
  website VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_agencies_name ON agencies(name);
CREATE INDEX idx_agencies_cage ON agencies(cage_code);

CREATE TABLE IF NOT EXISTS naics_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) NOT NULL UNIQUE,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  is_small_business BOOLEAN,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_naics_code ON naics_codes(code);

CREATE TABLE IF NOT EXISTS psc_codes (
  id SERIAL PRIMARY KEY,
  code VARCHAR(10) NOT NULL UNIQUE,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_psc_code ON psc_codes(code);

CREATE TABLE IF NOT EXISTS contract_types (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  rate_model VARCHAR(50) -- 'FFP', 'T&M', 'IDIQ', 'Cost-Plus'
);

INSERT INTO contract_types (code, name, description, rate_model) VALUES
  ('FFP', 'Firm Fixed Price', 'Price locked at proposal', 'FFP'),
  ('T&M', 'Time & Materials', 'Labor hours + materials', 'T&M'),
  ('IDIQ', 'Indefinite Delivery / Indefinite Quantity', 'Task orders as needed', 'IDIQ'),
  ('CP', 'Cost Plus Fixed Fee', 'Costs reimbursed + fixed fee', 'Cost-Plus'),
  ('CPIF', 'Cost Plus Incentive Fee', 'Costs + incentive based on performance', 'Cost-Plus')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS past_performance_contracts (
  id SERIAL PRIMARY KEY,
  contract_id VARCHAR(100) NOT NULL UNIQUE,
  contract_number VARCHAR(100),
  agency_id INTEGER REFERENCES agencies(id),
  agency_name VARCHAR(255),
  naics_id INTEGER REFERENCES naics_codes(id),
  naics_code VARCHAR(10),
  psc_id INTEGER REFERENCES psc_codes(id),
  psc_code VARCHAR(10),
  contract_type_id INTEGER REFERENCES contract_types(id),
  contract_type VARCHAR(20),

  -- Dates
  award_date DATE,
  start_date DATE,
  end_date DATE,
  completion_date DATE,

  -- Performance Metrics
  total_contract_value DECIMAL(15, 2),
  amount_spent DECIMAL(15, 2),
  on_time_percent NUMERIC(5, 2), -- 0-100
  cost_variance_percent NUMERIC(6, 2), -- positive = over budget
  quality_rating NUMERIC(3, 1), -- 1-5
  rework_percent NUMERIC(5, 2),
  re_award BOOLEAN DEFAULT FALSE,

  -- Customer Contact Info
  customer_agency VARCHAR(255),
  customer_poc_name VARCHAR(255),
  customer_poc_email VARCHAR(255),
  customer_poc_phone VARCHAR(20),
  ordering_officer_name VARCHAR(255),
  ordering_officer_email VARCHAR(255),

  -- Opportunity Context
  incumbent_contractor VARCHAR(255),
  number_of_competitors INTEGER,
  win_strategy TEXT,

  -- Narrative & Proof
  executive_summary TEXT,
  relevant_experience_narrative TEXT,
  performance_narrative TEXT,

  -- Document References
  proof_documents_url TEXT, -- S3 or GitHub URL
  cpars_url VARCHAR(255),
  sam_gov_url VARCHAR(255),

  -- Audit Trail
  created_by VARCHAR(255) DEFAULT 'system',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255) DEFAULT 'system',
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT
);
CREATE INDEX idx_pp_agency ON past_performance_contracts(agency_id);
CREATE INDEX idx_pp_naics ON past_performance_contracts(naics_code);
CREATE INDEX idx_pp_psc ON past_performance_contracts(psc_code);
CREATE INDEX idx_pp_award_date ON past_performance_contracts(award_date);
CREATE INDEX idx_pp_end_date ON past_performance_contracts(end_date);
CREATE INDEX idx_pp_contract_id ON past_performance_contracts(contract_id);

CREATE TABLE IF NOT EXISTS past_performance_references (
  id SERIAL PRIMARY KEY,
  contract_id INTEGER NOT NULL REFERENCES past_performance_contracts(id) ON DELETE CASCADE,
  reference_name VARCHAR(255),
  reference_email VARCHAR(255),
  reference_phone VARCHAR(20),
  reference_title VARCHAR(255),
  contact_frequency VARCHAR(100),
  reference_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ppr_contract ON past_performance_references(contract_id);

-- ============================================================================
-- PART 2: CAPTURE INTELLIGENCE DATABASE
-- ============================================================================

CREATE TABLE IF NOT EXISTS solicitations (
  id SERIAL PRIMARY KEY,
  solicitation_id VARCHAR(100) NOT NULL UNIQUE,
  solicitation_number VARCHAR(100),
  title VARCHAR(500),
  description TEXT,
  agency_id INTEGER REFERENCES agencies(id),
  agency_name VARCHAR(255),

  -- NAICS & PSC
  naics_codes TEXT[], -- array of codes for multi-NAICS solicitations
  psc_codes TEXT[],

  -- Key Dates
  posted_date DATE,
  response_deadline DATE,
  days_to_close INTEGER GENERATED ALWAYS AS (EXTRACT(DAY FROM response_deadline - CURRENT_DATE)::INTEGER) STORED,

  -- Set-Asides & Restrictions
  small_business_setaside BOOLEAN,
  wosb_setaside BOOLEAN,
  hubzone_setaside BOOLEAN,
  8a_setaside BOOLEAN,
  veteran_owned BOOLEAN,
  service_disabled_veteran BOOLEAN,

  -- Opportunity Details
  estimated_value DECIMAL(15, 2),
  contract_type VARCHAR(20),
  place_of_performance VARCHAR(255),

  -- Scoring
  relevance_score INTEGER, -- 0-100, based on NAICS match
  timeline_score INTEGER, -- 0-100, based on days_to_close
  agency_fit_score INTEGER, -- 0-100, based on past performance with agency
  incumbent_risk_score INTEGER, -- 0-100, higher = harder to beat incumbent
  opportunity_score INTEGER GENERATED ALWAYS AS ((relevance_score * 0.35 + timeline_score * 0.30 + agency_fit_score * 0.25 + (100 - incumbent_risk_score) * 0.10)::INTEGER) STORED,

  -- Status
  status VARCHAR(50) DEFAULT 'open', -- 'open', 'closed', 'awarded', 'cancelled'
  awarded_to VARCHAR(255),
  awarded_date DATE,

  -- Links
  sam_gov_url VARCHAR(255),
  fbo_url VARCHAR(255),

  -- Audit Trail
  first_seen_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  alert_generated BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_sol_agency ON solicitations(agency_id);
CREATE INDEX idx_sol_naics ON solicitations USING GIN(naics_codes);
CREATE INDEX idx_sol_posted ON solicitations(posted_date);
CREATE INDEX idx_sol_deadline ON solicitations(response_deadline);
CREATE INDEX idx_sol_status ON solicitations(status);
CREATE INDEX idx_sol_score ON solicitations(opportunity_score DESC);
CREATE INDEX idx_sol_days ON solicitations(days_to_close);

CREATE TABLE IF NOT EXISTS incumbent_contracts (
  id SERIAL PRIMARY KEY,
  contract_id VARCHAR(100) NOT NULL UNIQUE,
  contract_number VARCHAR(100),
  agency_id INTEGER REFERENCES agencies(id),
  agency_name VARCHAR(255),
  incumbent_contractor VARCHAR(255),
  incumbent_duns VARCHAR(20),

  -- Dates
  award_date DATE,
  expiration_date DATE,
  recompete_window_start DATE GENERATED ALWAYS AS (expiration_date - INTERVAL '12 months') STORED,
  days_to_expiration INTEGER GENERATED ALWAYS AS (EXTRACT(DAY FROM expiration_date - CURRENT_DATE)::INTEGER) STORED,

  -- Contract Details
  naics_code VARCHAR(10),
  psc_code VARCHAR(10),
  contract_value DECIMAL(15, 2),
  contract_type VARCHAR(20),

  -- Performance Data (pulled from CPARS)
  cpars_rating NUMERIC(3, 1),
  cpars_last_reviewed DATE,

  -- Recompete Intelligence
  recompete_likely BOOLEAN,
  recompete_comments TEXT,

  -- Links
  sam_gov_url VARCHAR(255),
  cpars_url VARCHAR(255),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_ic_agency ON incumbent_contracts(agency_id);
CREATE INDEX idx_ic_expiration ON incumbent_contracts(expiration_date);
CREATE INDEX idx_ic_recompete ON incumbent_contracts(days_to_expiration);

CREATE TABLE IF NOT EXISTS agency_budget_trends (
  id SERIAL PRIMARY KEY,
  agency_id INTEGER NOT NULL REFERENCES agencies(id),
  naics_code VARCHAR(10) NOT NULL,
  fiscal_year INTEGER,
  contract_count INTEGER,
  total_awards DECIMAL(15, 2),
  avg_contract_value DECIMAL(15, 2),
  yoy_growth_percent NUMERIC(6, 2),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(agency_id, naics_code, fiscal_year)
);
CREATE INDEX idx_budget_agency ON agency_budget_trends(agency_id);
CREATE INDEX idx_budget_naics ON agency_budget_trends(naics_code);
CREATE INDEX idx_budget_fy ON agency_budget_trends(fiscal_year);

CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  alert_type VARCHAR(50), -- 'new_solicitation', 'recompete_window', 'budget_growth', 'cpars_update'
  severity VARCHAR(20), -- 'high', 'medium', 'low'
  title VARCHAR(500),
  description TEXT,
  solicitation_id INTEGER REFERENCES solicitations(id),
  incumbent_id INTEGER REFERENCES incumbent_contracts(id),
  agency_id INTEGER REFERENCES agencies(id),

  -- Context
  naics_code VARCHAR(10),
  estimated_value DECIMAL(15, 2),
  opportunity_score INTEGER,

  -- Status
  status VARCHAR(50) DEFAULT 'new', -- 'new', 'acknowledged', 'dismissed', 'actioned'
  acknowledged_by VARCHAR(255),
  acknowledged_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_alert_status ON alerts(status);
CREATE INDEX idx_alert_created ON alerts(created_at DESC);
CREATE INDEX idx_alert_severity ON alerts(severity);

-- ============================================================================
-- PART 3: PRICING & WRAP-RATE MODEL
-- ============================================================================

CREATE TABLE IF NOT EXISTS labor_categories (
  id SERIAL PRIMARY KEY,
  category_code VARCHAR(50) NOT NULL,
  category_name VARCHAR(255) NOT NULL,
  description TEXT,
  gsa_schedule_number VARCHAR(50),

  -- Rates
  loaded_rate_2024 DECIMAL(10, 2),
  loaded_rate_2025 DECIMAL(10, 2),
  loaded_rate_2026 DECIMAL(10, 2),

  -- Rate Components
  base_hourly_rate DECIMAL(10, 2),
  burden_rate_percent NUMERIC(5, 2),
  overhead_percent NUMERIC(5, 2),
  ga_percent NUMERIC(5, 2),
  profit_percent NUMERIC(5, 2),

  -- Contract Type Variations
  ffp_rate DECIMAL(10, 2),
  tm_rate DECIMAL(10, 2),
  idiq_rate DECIMAL(10, 2),

  -- Minimum Experience
  min_years_experience INTEGER,
  required_clearance VARCHAR(100),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_labor_code ON labor_categories(category_code);
CREATE INDEX idx_labor_name ON labor_categories(category_name);

CREATE TABLE IF NOT EXISTS indirect_cost_rates (
  id SERIAL PRIMARY KEY,
  contractor_name VARCHAR(255) NOT NULL,
  duns_number VARCHAR(20),
  cage_code VARCHAR(10),

  -- Rate Information
  indirect_type VARCHAR(50), -- 'overhead', 'g_and_a', 'fringe'
  rate_percent NUMERIC(5, 2),
  base_amount DECIMAL(15, 2),

  -- Dates
  effective_from DATE,
  effective_to DATE,

  -- Status
  status VARCHAR(50), -- 'provisional', 'negotiated', 'final', 'pending_negotiation'
  dcaa_approved BOOLEAN,
  dcaa_audit_date DATE,

  -- References
  dcaa_decision_url VARCHAR(255),
  notes TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_icr_contractor ON indirect_cost_rates(contractor_name);
CREATE INDEX idx_icr_effective ON indirect_cost_rates(effective_from, effective_to);
CREATE INDEX idx_icr_status ON indirect_cost_rates(status);

CREATE TABLE IF NOT EXISTS rate_cards (
  id SERIAL PRIMARY KEY,
  rate_card_name VARCHAR(255) NOT NULL,
  gsa_schedule_number VARCHAR(50),
  effective_from DATE,
  effective_to DATE,

  -- Contractor Info
  contractor_name VARCHAR(255),
  duns_number VARCHAR(20),
  cage_code VARCHAR(10),

  -- Rates (aggregate)
  min_labor_rate DECIMAL(10, 2),
  max_labor_rate DECIMAL(10, 2),
  avg_labor_rate DECIMAL(10, 2),

  -- Overhead
  overhead_rate_percent NUMERIC(5, 2),
  g_and_a_percent NUMERIC(5, 2),

  -- Profit
  profit_percent_ffp NUMERIC(5, 2),
  profit_percent_tm NUMERIC(5, 2),
  profit_percent_idiq NUMERIC(5, 2),

  -- Historical Tracking
  previous_rate_card_id INTEGER REFERENCES rate_cards(id),
  cola_increase_percent NUMERIC(5, 2),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_rc_contractor ON rate_cards(contractor_name);
CREATE INDEX idx_rc_effective ON rate_cards(effective_from, effective_to);

CREATE TABLE IF NOT EXISTS cost_analyses (
  id SERIAL PRIMARY KEY,
  proposal_id VARCHAR(100) NOT NULL,
  solicitation_id VARCHAR(100),
  opportunity_id INTEGER REFERENCES solicitations(id),

  -- Proposal Info
  proposal_name VARCHAR(500),
  proposal_date DATE DEFAULT CURRENT_DATE,
  contractor_name VARCHAR(255),

  -- Cost Elements
  total_labor_hours DECIMAL(10, 2),
  total_labor_cost DECIMAL(15, 2),
  total_material_cost DECIMAL(15, 2),
  total_overhead DECIMAL(15, 2),
  total_ga DECIMAL(15, 2),
  total_profit DECIMAL(15, 2),

  -- Totals
  subtotal_cost DECIMAL(15, 2),
  total_contract_value DECIMAL(15, 2),

  -- Contract Type & Terms
  contract_type VARCHAR(20),
  contract_duration_months INTEGER,

  -- Compliance
  dcaa_compliant BOOLEAN,
  sf1411_certified BOOLEAN,
  risk_buffer_percent NUMERIC(5, 2),
  profit_margin_percent NUMERIC(5, 2),

  -- Audit Trail
  created_by VARCHAR(255) DEFAULT 'system',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_by VARCHAR(255),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT
);
CREATE INDEX idx_ca_proposal ON cost_analyses(proposal_id);
CREATE INDEX idx_ca_solicitation ON cost_analyses(solicitation_id);
CREATE INDEX idx_ca_created ON cost_analyses(created_at DESC);

CREATE TABLE IF NOT EXISTS cost_analysis_line_items (
  id SERIAL PRIMARY KEY,
  cost_analysis_id INTEGER NOT NULL REFERENCES cost_analyses(id) ON DELETE CASCADE,
  line_number INTEGER,
  labor_category_id INTEGER REFERENCES labor_categories(id),
  labor_category VARCHAR(255),

  -- Quantities
  hours_per_month DECIMAL(10, 2),
  months INTEGER,
  total_hours DECIMAL(10, 2),

  -- Rates & Costs
  hourly_rate DECIMAL(10, 2),
  extended_cost DECIMAL(15, 2),

  -- Burden
  burden_percent NUMERIC(5, 2),
  burden_amount DECIMAL(15, 2),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_cali_analysis ON cost_analysis_line_items(cost_analysis_id);

-- ============================================================================
-- PART 4: AUDIT & TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  table_name VARCHAR(100),
  record_id INTEGER,
  action VARCHAR(50), -- 'INSERT', 'UPDATE', 'DELETE'
  changed_fields JSONB,
  changed_by VARCHAR(255),
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_table ON audit_log(table_name);
CREATE INDEX idx_audit_changed ON audit_log(changed_at DESC);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

CREATE OR REPLACE VIEW high_priority_opportunities AS
SELECT
  s.id,
  s.solicitation_number,
  s.title,
  s.agency_name,
  s.opportunity_score,
  s.days_to_close,
  s.response_deadline,
  s.estimated_value,
  COUNT(CASE WHEN ppc.id IS NOT NULL THEN 1 END) as past_perf_matches,
  CASE
    WHEN s.opportunity_score >= 75 AND s.days_to_close > 0 AND s.days_to_close <= 30 THEN 'IMMEDIATE'
    WHEN s.opportunity_score >= 70 AND s.days_to_close > 0 AND s.days_to_close <= 60 THEN 'HIGH'
    WHEN s.opportunity_score >= 60 AND s.days_to_close > 0 THEN 'MEDIUM'
    ELSE 'LOW'
  END as urgency
FROM solicitations s
LEFT JOIN past_performance_contracts ppc ON (
  ppc.naics_code = ANY(s.naics_codes)
  AND ppc.agency_id = s.agency_id
  AND ppc.end_date >= CURRENT_DATE - INTERVAL '10 years'
)
WHERE s.status = 'open'
GROUP BY s.id, s.solicitation_number, s.title, s.agency_name, s.opportunity_score, s.days_to_close, s.response_deadline, s.estimated_value
ORDER BY s.opportunity_score DESC, s.days_to_close ASC;

CREATE OR REPLACE VIEW recompete_alerts AS
SELECT
  ic.id,
  ic.contract_number,
  ic.incumbent_contractor,
  ic.agency_name,
  ic.naics_code,
  ic.contract_value,
  ic.expiration_date,
  ic.days_to_expiration,
  ic.cpars_rating,
  COUNT(CASE WHEN ppc.id IS NOT NULL THEN 1 END) as our_past_perf_in_this_naics
FROM incumbent_contracts ic
LEFT JOIN past_performance_contracts ppc ON (
  ppc.naics_code = ic.naics_code
  AND ppc.agency_id = ic.agency_id
  AND ppc.end_date >= CURRENT_DATE - INTERVAL '10 years'
)
WHERE ic.days_to_expiration BETWEEN 180 AND 365
  AND ic.recompete_likely = TRUE
GROUP BY ic.id, ic.contract_number, ic.incumbent_contractor, ic.agency_name, ic.naics_code,
         ic.contract_value, ic.expiration_date, ic.days_to_expiration, ic.cpars_rating
ORDER BY ic.days_to_expiration ASC;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
GRANT INSERT, UPDATE ON all_tables IN SCHEMA public TO postgres;
