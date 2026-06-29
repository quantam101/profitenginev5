-- ============================================================================
-- FEDERAL CONTRACT PRICING & WRAP-RATE SCHEMA
-- DCAA-Compliant, GSA Schedule & IDIQ Support
-- ============================================================================
-- Comprehensive schema for labor rate management, indirect cost allocation,
-- profit margin tracking, and federal contract bidding with audit trails.
-- ============================================================================

-- ============================================================================
-- 1. LABOR CATEGORIES & RATE MASTERS
-- ============================================================================

CREATE TABLE labor_categories (
    labor_category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(50) NOT NULL UNIQUE,
    category_name VARCHAR(255) NOT NULL,
    category_type VARCHAR(50) NOT NULL, -- 'GSA_SCHEDULE', 'CLIN', 'CUSTOM', 'SOW'
    description TEXT,
    min_experience_years INT DEFAULT 0,
    skill_level VARCHAR(50), -- 'Entry', 'Intermediate', 'Senior', 'Expert'
    industry_segment VARCHAR(100), -- 'IT', 'Engineering', 'Management', 'Admin'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT valid_category_type CHECK (category_type IN ('GSA_SCHEDULE', 'CLIN', 'CUSTOM', 'SOW')),
    CONSTRAINT valid_skill_level CHECK (skill_level IN ('Entry', 'Intermediate', 'Senior', 'Expert', NULL))
);

CREATE INDEX idx_labor_categories_code ON labor_categories(category_code);
CREATE INDEX idx_labor_categories_active ON labor_categories(is_active);

-- ============================================================================
-- 2. LABOR RATES (by year, contract type, category)
-- ============================================================================

CREATE TABLE labor_rates (
    labor_rate_id SERIAL PRIMARY KEY,
    labor_category_id INT NOT NULL REFERENCES labor_categories(labor_category_id),
    fiscal_year INT NOT NULL,
    contract_type VARCHAR(50) NOT NULL, -- 'FFP', 'T&M', 'IDIQ', 'GSA_SCHEDULE'

    -- Base Rate Components (per hour or per unit)
    base_rate_usd NUMERIC(10, 2) NOT NULL,
    base_rate_currency VARCHAR(3) DEFAULT 'USD',

    -- Cost Components
    direct_labor_cost_usd NUMERIC(10, 2) NOT NULL, -- Labor cost w/o overhead
    billable_rate_usd NUMERIC(10, 2) NOT NULL, -- Rate charged to customer

    -- Loaded Cost (includes burden)
    loaded_cost_usd NUMERIC(10, 2) NOT NULL, -- Direct labor + burdens (FICA, insurance, etc.)

    -- Profit Margin
    profit_margin_percent NUMERIC(5, 2) NOT NULL DEFAULT 0,
    profit_margin_usd NUMERIC(10, 2) GENERATED ALWAYS AS
        (billable_rate_usd - loaded_cost_usd) STORED,

    -- Rate Effective Date
    effective_date DATE NOT NULL,
    expiration_date DATE,

    -- Rate Status
    rate_status VARCHAR(50) DEFAULT 'PROVISIONAL', -- 'PROVISIONAL', 'APPROVED', 'NEGOTIATED', 'LOCKED'
    rate_justification TEXT, -- Audit trail: why this rate?

    -- COLA & Adjustments
    cola_percent NUMERIC(5, 2) DEFAULT 0,
    adjustment_reason VARCHAR(255),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_positive_base_rate CHECK (base_rate_usd > 0),
    CONSTRAINT check_positive_billable_rate CHECK (billable_rate_usd > 0),
    CONSTRAINT check_positive_loaded_cost CHECK (loaded_cost_usd > 0),
    CONSTRAINT check_billable_exceeds_cost CHECK (billable_rate_usd >= loaded_cost_usd),
    CONSTRAINT check_profit_margin CHECK (profit_margin_percent >= 0 AND profit_margin_percent <= 30),
    CONSTRAINT valid_rate_status CHECK (rate_status IN ('PROVISIONAL', 'APPROVED', 'NEGOTIATED', 'LOCKED')),
    CONSTRAINT valid_contract_type CHECK (contract_type IN ('FFP', 'T&M', 'IDIQ', 'GSA_SCHEDULE')),
    CONSTRAINT valid_cola CHECK (cola_percent >= 0 AND cola_percent <= 10)
);

CREATE INDEX idx_labor_rates_category ON labor_rates(labor_category_id);
CREATE INDEX idx_labor_rates_fy ON labor_rates(fiscal_year);
CREATE INDEX idx_labor_rates_contract_type ON labor_rates(contract_type);
CREATE INDEX idx_labor_rates_active ON labor_rates(is_active);
CREATE INDEX idx_labor_rates_status ON labor_rates(rate_status);

-- ============================================================================
-- 3. BURDEN RATES (FICA, Insurance, Training, Facilities, etc.)
-- ============================================================================

CREATE TABLE burden_rates (
    burden_rate_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,
    burden_type VARCHAR(100) NOT NULL, -- 'FICA', 'HEALTH_INSURANCE', 'PENSION', 'TRAINING', 'FACILITIES', 'ADMIN'

    rate_percent NUMERIC(5, 2) NOT NULL, -- Percentage of labor cost
    rate_amount_usd NUMERIC(10, 2), -- Fixed amount (if not percentage-based)

    allocation_method VARCHAR(50) NOT NULL, -- '%_OF_LABOR', '%_OF_COST', 'PER_HOUR', 'FIXED'

    -- DCAA Compliance
    dcaa_compliant BOOLEAN DEFAULT TRUE,
    dcaa_rate_id VARCHAR(100), -- Reference to DCAA approved rate

    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_positive_percent CHECK (rate_percent >= 0 AND rate_percent <= 100),
    CONSTRAINT valid_allocation CHECK (allocation_method IN ('%_OF_LABOR', '%_OF_COST', 'PER_HOUR', 'FIXED'))
);

CREATE INDEX idx_burden_rates_fy ON burden_rates(fiscal_year);
CREATE INDEX idx_burden_rates_type ON burden_rates(burden_type);
CREATE INDEX idx_burden_rates_active ON burden_rates(is_active);

-- Sample Burden Types
INSERT INTO burden_rates (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, description, is_active, created_by)
VALUES
    (2026, 'FICA', 7.65, '%_OF_LABOR', TRUE, 'FICA payroll tax (7.65%)', TRUE, 'SYSTEM'),
    (2026, 'HEALTH_INSURANCE', 15.50, '%_OF_LABOR', TRUE, 'Group health insurance premium', TRUE, 'SYSTEM'),
    (2026, 'PENSION', 8.00, '%_OF_LABOR', TRUE, 'Defined benefit pension contribution', TRUE, 'SYSTEM'),
    (2026, 'TRAINING', 2.50, '%_OF_LABOR', TRUE, 'Training & development fund', TRUE, 'SYSTEM'),
    (2026, 'FACILITIES', 12.00, '%_OF_LABOR', TRUE, 'Facilities, utilities, rent allocation', TRUE, 'SYSTEM'),
    (2026, 'ADMIN', 5.00, '%_OF_LABOR', TRUE, 'Administrative overhead allocation', TRUE, 'SYSTEM');

-- ============================================================================
-- 4. OVERHEAD & G&A RATES (DCAA Compliance)
-- ============================================================================

CREATE TABLE overhead_ga_rates (
    overhead_ga_rate_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,

    -- Rate Components
    overhead_percent NUMERIC(5, 2) NOT NULL, -- Overhead as % of direct labor
    gna_percent NUMERIC(5, 2) NOT NULL, -- General & Administrative as % of direct labor
    profit_percent NUMERIC(5, 2) NOT NULL DEFAULT 10, -- Standard profit margin

    -- Allocation Methods
    overhead_allocation_method VARCHAR(50) NOT NULL, -- '%_OF_LABOR', '%_OF_TOTAL_COST', 'PER_HOUR'
    gna_allocation_method VARCHAR(50) NOT NULL,

    -- DCAA Compliance
    dcaa_rate_approval_date DATE, -- Date of DCAA approval
    dcaa_approval_number VARCHAR(100), -- DCAA approval reference
    provisional_rate BOOLEAN DEFAULT TRUE,
    negotiated_date DATE,

    -- Contract Type Override
    contract_type VARCHAR(50), -- If NULL, applies to all contract types

    description TEXT,
    audit_trail TEXT, -- JSON or text: justification, amendments

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_overhead_percent CHECK (overhead_percent >= 0 AND overhead_percent <= 150),
    CONSTRAINT check_gna_percent CHECK (gna_percent >= 0 AND gna_percent <= 150),
    CONSTRAINT check_profit_percent CHECK (profit_percent >= 0 AND profit_percent <= 30),
    CONSTRAINT valid_allocation_oh CHECK (overhead_allocation_method IN ('%_OF_LABOR', '%_OF_TOTAL_COST', 'PER_HOUR')),
    CONSTRAINT valid_allocation_gna CHECK (gna_allocation_method IN ('%_OF_LABOR', '%_OF_TOTAL_COST', 'PER_HOUR'))
);

CREATE INDEX idx_overhead_ga_rates_fy ON overhead_ga_rates(fiscal_year);
CREATE INDEX idx_overhead_ga_rates_contract_type ON overhead_ga_rates(contract_type);

-- Sample Overhead & G&A Structure
INSERT INTO overhead_ga_rates (fiscal_year, overhead_percent, gna_percent, profit_percent, overhead_allocation_method, gna_allocation_method, dcaa_rate_approval_date, provisional_rate, description, created_by)
VALUES
    (2026, 65.00, 12.00, 10.00, '%_OF_LABOR', '%_OF_LABOR', '2025-10-15', FALSE, 'Standard FFP/T&M rates - DCAA approved', 'SYSTEM'),
    (2026, 75.00, 15.00, 12.00, '%_OF_LABOR', '%_OF_LABOR', NULL, TRUE, 'IDIQ provisional rates - pending negotiation', 'SYSTEM'),
    (2026, 55.00, 10.00, 8.00, '%_OF_LABOR', '%_OF_LABOR', '2025-06-01', FALSE, 'GSA Schedule rates - volume discount', 'SYSTEM');

-- ============================================================================
-- 5. INDIRECT COST RATES (DCAA - Compliant)
-- ============================================================================

CREATE TABLE indirect_cost_rates (
    indirect_cost_rate_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,

    rate_type VARCHAR(50) NOT NULL, -- 'APPROVED', 'NEGOTIATED', 'PROVISIONAL', 'TENTATIVE'
    rate_value NUMERIC(5, 2) NOT NULL, -- Percentage of allocation base
    allocation_base VARCHAR(100) NOT NULL, -- 'DIRECT_LABOR', 'TOTAL_COST', 'DIRECT_COST'

    -- DCAA Reference
    dcaa_rate_id VARCHAR(100), -- Reference to DCAA rate database
    dcaa_audit_date DATE,
    dcaa_approval_date DATE,
    negotiated_with_agency VARCHAR(100), -- 'DFARS', 'DCAA', 'NASA', etc.

    -- Time Period
    effective_date DATE NOT NULL,
    expiration_date DATE,

    -- Rate Components (for transparency)
    includes_overhead BOOLEAN DEFAULT TRUE,
    includes_gna BOOLEAN DEFAULT TRUE,
    includes_profit BOOLEAN DEFAULT FALSE,

    rate_justification TEXT,
    audit_trail TEXT, -- JSON: amendments, reviews, appeals

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_rate_value CHECK (rate_value >= 0 AND rate_value <= 300),
    CONSTRAINT valid_rate_type CHECK (rate_type IN ('APPROVED', 'NEGOTIATED', 'PROVISIONAL', 'TENTATIVE')),
    CONSTRAINT valid_allocation_base CHECK (allocation_base IN ('DIRECT_LABOR', 'TOTAL_COST', 'DIRECT_COST'))
);

CREATE INDEX idx_indirect_cost_rates_fy ON indirect_cost_rates(fiscal_year);
CREATE INDEX idx_indirect_cost_rates_type ON indirect_cost_rates(rate_type);

-- ============================================================================
-- 6. VOLUME PRICING DISCOUNTS (by Contract Value)
-- ============================================================================

CREATE TABLE volume_pricing_tiers (
    volume_pricing_tier_id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,
    contract_type VARCHAR(50) NOT NULL, -- 'FFP', 'T&M', 'IDIQ', 'GSA_SCHEDULE'

    min_contract_value_usd NUMERIC(15, 2) NOT NULL, -- Minimum contract value for this tier
    max_contract_value_usd NUMERIC(15, 2), -- NULL = no maximum

    discount_percent NUMERIC(5, 2) NOT NULL DEFAULT 0, -- Discount applied to billable rate
    discount_type VARCHAR(50) DEFAULT 'PERCENTAGE', -- 'PERCENTAGE', 'FIXED', 'TIERED'

    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_min_value CHECK (min_contract_value_usd >= 0),
    CONSTRAINT check_discount_percent CHECK (discount_percent >= 0 AND discount_percent <= 50),
    CONSTRAINT valid_discount_type CHECK (discount_type IN ('PERCENTAGE', 'FIXED', 'TIERED'))
);

CREATE INDEX idx_volume_pricing_tiers_contract_type ON volume_pricing_tiers(contract_type);

-- Sample Volume Discounts
INSERT INTO volume_pricing_tiers (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd, discount_percent, description, created_by)
VALUES
    (2026, 'IDIQ', 0, 999999.99, 0, 'Base rate (no volume discount)', 'SYSTEM'),
    (2026, 'IDIQ', 1000000, 4999999.99, 2.5, 'Volume discount: $1M-$5M', 'SYSTEM'),
    (2026, 'IDIQ', 5000000, 9999999.99, 5.0, 'Volume discount: $5M-$10M', 'SYSTEM'),
    (2026, 'IDIQ', 10000000, NULL, 7.5, 'Volume discount: $10M+', 'SYSTEM'),
    (2026, 'GSA_SCHEDULE', 0, NULL, 0, 'GSA Schedule - no volume discount', 'SYSTEM');

-- ============================================================================
-- 7. CONTRACT-SPECIFIC RATE AGREEMENTS
-- ============================================================================

CREATE TABLE contract_rate_agreements (
    contract_rate_agreement_id SERIAL PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL UNIQUE,
    contract_number VARCHAR(50),
    contract_name VARCHAR(255),
    customer_name VARCHAR(255),

    fiscal_year INT NOT NULL,
    contract_type VARCHAR(50) NOT NULL, -- 'FFP', 'T&M', 'IDIQ', 'GSA_SCHEDULE'

    -- Rate Lock (for FFP contracts, rates are locked at proposal)
    rate_lock_date DATE,
    rate_lock_status VARCHAR(50) DEFAULT 'PROPOSED', -- 'PROPOSED', 'AGREED', 'LOCKED'

    -- Contract Ceiling & Budget
    contract_ceiling_usd NUMERIC(15, 2),
    not_to_exceed_usd NUMERIC(15, 2),

    -- Profit Target
    target_profit_percent NUMERIC(5, 2),
    minimum_profit_percent NUMERIC(5, 2) DEFAULT 0,

    -- Rate Adjustments
    escalation_percent NUMERIC(5, 2) DEFAULT 0, -- Annual escalation (if allowed by contract)
    escalation_type VARCHAR(50), -- 'COLA', 'FIXED', 'CPI'

    -- Compliance
    dcaa_compliant BOOLEAN DEFAULT TRUE,
    audit_status VARCHAR(50) DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'QUESTIONED'

    agreement_document_path VARCHAR(500), -- Reference to stored PDF/document

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),

    CONSTRAINT check_ceiling CHECK (contract_ceiling_usd IS NULL OR contract_ceiling_usd > 0),
    CONSTRAINT check_ntx CHECK (not_to_exceed_usd IS NULL OR not_to_exceed_usd > 0),
    CONSTRAINT check_target_profit CHECK (target_profit_percent >= 0 AND target_profit_percent <= 30),
    CONSTRAINT valid_rate_lock_status CHECK (rate_lock_status IN ('PROPOSED', 'AGREED', 'LOCKED')),
    CONSTRAINT valid_escalation_type CHECK (escalation_type IN ('COLA', 'FIXED', 'CPI', NULL))
);

CREATE INDEX idx_contract_rate_agreements_fy ON contract_rate_agreements(fiscal_year);
CREATE INDEX idx_contract_rate_agreements_type ON contract_rate_agreements(contract_type);

-- ============================================================================
-- 8. CONTRACT RATE LINE ITEMS (rates assigned to a specific contract)
-- ============================================================================

CREATE TABLE contract_rate_line_items (
    contract_rate_line_item_id SERIAL PRIMARY KEY,
    contract_rate_agreement_id INT NOT NULL REFERENCES contract_rate_agreements(contract_rate_agreement_id),
    labor_category_id INT NOT NULL REFERENCES labor_categories(labor_category_id),
    labor_rate_id INT NOT NULL REFERENCES labor_rates(labor_rate_id),

    -- Rate Specific to This Contract
    negotiated_rate_usd NUMERIC(10, 2) NOT NULL, -- May differ from standard rate
    negotiated_billable_rate_usd NUMERIC(10, 2) NOT NULL,

    -- Justification & Audit Trail
    rate_justification TEXT,
    negotiation_notes TEXT,
    approved_by VARCHAR(100),
    approval_date DATE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_negotiated_rate CHECK (negotiated_rate_usd > 0),
    CONSTRAINT check_negotiated_billable CHECK (negotiated_billable_rate_usd > 0),
    CONSTRAINT check_negotiated_exceeds_cost CHECK (negotiated_billable_rate_usd >= negotiated_rate_usd)
);

CREATE INDEX idx_contract_rate_line_items_agreement ON contract_rate_line_items(contract_rate_agreement_id);
CREATE INDEX idx_contract_rate_line_items_category ON contract_rate_line_items(labor_category_id);

-- ============================================================================
-- 9. RATE JUSTIFICATION & AUDIT TRAIL
-- ============================================================================

CREATE TABLE rate_audit_trail (
    audit_trail_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- 'LABOR_RATE', 'OVERHEAD_GA', 'INDIRECT_COST', 'VOLUME_PRICING'
    entity_id INT NOT NULL,

    event_type VARCHAR(50) NOT NULL, -- 'CREATED', 'UPDATED', 'APPROVED', 'QUESTIONED', 'AMENDED'

    previous_value NUMERIC(10, 2),
    new_value NUMERIC(10, 2),

    reason_for_change TEXT NOT NULL,
    justification TEXT,

    -- DCAA Audit Info
    dcaa_audit_flag BOOLEAN DEFAULT FALSE, -- Flagged during DCAA audit
    dcaa_audit_comments TEXT,

    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Compliance Sign-off
    approved_by VARCHAR(100),
    approval_date DATE,

    CONSTRAINT valid_event_type CHECK (event_type IN ('CREATED', 'UPDATED', 'APPROVED', 'QUESTIONED', 'AMENDED')),
    CONSTRAINT valid_entity_type CHECK (entity_type IN ('LABOR_RATE', 'OVERHEAD_GA', 'INDIRECT_COST', 'VOLUME_PRICING'))
);

CREATE INDEX idx_audit_trail_entity ON rate_audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_trail_date ON rate_audit_trail(changed_at);

-- ============================================================================
-- 10. COST ANALYSIS TEMPLATES (SF 1411 Export)
-- ============================================================================

CREATE TABLE cost_analysis_export_history (
    export_id SERIAL PRIMARY KEY,
    contract_id VARCHAR(100) NOT NULL,
    export_type VARCHAR(50) NOT NULL, -- 'SF_1411', 'COST_SUMMARY', 'RATE_JUSTIFICATION'

    export_filename VARCHAR(255),
    export_format VARCHAR(20), -- 'PDF', 'EXCEL', 'XML'
    export_path VARCHAR(500),

    export_data JSONB, -- Serialized form data

    exported_by VARCHAR(100),
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Signature Block (for PDF)
    authorized_signatory VARCHAR(255),
    signature_date DATE,

    is_official_submission BOOLEAN DEFAULT FALSE,

    CONSTRAINT valid_export_type CHECK (export_type IN ('SF_1411', 'COST_SUMMARY', 'RATE_JUSTIFICATION')),
    CONSTRAINT valid_format CHECK (export_format IN ('PDF', 'EXCEL', 'XML'))
);

CREATE INDEX idx_cost_analysis_contract ON cost_analysis_export_history(contract_id);
CREATE INDEX idx_cost_analysis_export_type ON cost_analysis_export_history(export_type);

-- ============================================================================
-- 11. MATERIALIZED VIEW: Competitive Rate Summary
-- ============================================================================

-- This view provides a comprehensive snapshot of current rates across all categories
CREATE MATERIALIZED VIEW competitive_rate_summary AS
SELECT
    lc.labor_category_id,
    lc.category_code,
    lc.category_name,
    lc.skill_level,
    lc.industry_segment,
    lr.fiscal_year,
    lr.contract_type,

    -- Rate Components
    lr.base_rate_usd,
    lr.direct_labor_cost_usd,
    lr.billable_rate_usd,
    lr.loaded_cost_usd,

    -- Burden Breakdown
    COALESCE(SUM(CASE WHEN br.burden_type = 'FICA' THEN br.rate_percent ELSE 0 END), 0) AS fica_percent,
    COALESCE(SUM(CASE WHEN br.burden_type = 'HEALTH_INSURANCE' THEN br.rate_percent ELSE 0 END), 0) AS health_insurance_percent,
    COALESCE(SUM(CASE WHEN br.burden_type = 'PENSION' THEN br.rate_percent ELSE 0 END), 0) AS pension_percent,
    COALESCE(SUM(CASE WHEN br.burden_type = 'FACILITIES' THEN br.rate_percent ELSE 0 END), 0) AS facilities_percent,

    -- Overhead & G&A
    ogr.overhead_percent,
    ogr.gna_percent,
    ogr.profit_percent,

    -- Profit Margin
    lr.profit_margin_percent,
    lr.profit_margin_usd,

    -- Compliance Status
    lr.rate_status,
    ogr.provisional_rate,

    -- Effective Dates
    lr.effective_date,
    lr.expiration_date,

    -- Audit Trail
    lr.rate_justification

FROM labor_categories lc
JOIN labor_rates lr ON lc.labor_category_id = lr.labor_category_id
LEFT JOIN burden_rates br ON lr.fiscal_year = br.fiscal_year AND br.is_active = TRUE
LEFT JOIN overhead_ga_rates ogr ON lr.fiscal_year = ogr.fiscal_year AND ogr.is_active = TRUE
WHERE lc.is_active = TRUE AND lr.is_active = TRUE
GROUP BY
    lc.labor_category_id, lc.category_code, lc.category_name, lc.skill_level, lc.industry_segment,
    lr.fiscal_year, lr.contract_type, lr.base_rate_usd, lr.direct_labor_cost_usd, lr.billable_rate_usd,
    lr.loaded_cost_usd, lr.profit_margin_percent, lr.profit_margin_usd, lr.rate_status,
    lr.effective_date, lr.expiration_date, lr.rate_justification,
    ogr.overhead_percent, ogr.gna_percent, ogr.profit_percent, ogr.provisional_rate
ORDER BY lc.category_code, lr.fiscal_year DESC, lr.contract_type;

CREATE INDEX idx_competitive_rate_summary_category ON competitive_rate_summary(category_code);
CREATE INDEX idx_competitive_rate_summary_fy_type ON competitive_rate_summary(fiscal_year, contract_type);

-- ============================================================================
-- 12. RATE CALCULATION QUERIES & FUNCTIONS
-- ============================================================================

-- Function: Calculate Loaded Cost (Direct Labor + Burdens)
CREATE OR REPLACE FUNCTION calculate_loaded_cost(
    p_direct_labor_cost NUMERIC,
    p_fiscal_year INT
)
RETURNS NUMERIC AS $$
DECLARE
    v_total_burden NUMERIC := 0;
    v_burden_record RECORD;
BEGIN
    -- Sum all burden percentages for the fiscal year
    FOR v_burden_record IN
        SELECT rate_percent FROM burden_rates
        WHERE fiscal_year = p_fiscal_year AND is_active = TRUE
            AND allocation_method = '%_OF_LABOR'
    LOOP
        v_total_burden := v_total_burden + v_burden_record.rate_percent;
    END LOOP;

    -- Return direct labor + (direct labor * total burden %)
    RETURN p_direct_labor_cost * (1 + v_total_burden / 100);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Calculate Billable Rate (Loaded Cost + Overhead + G&A + Profit)
CREATE OR REPLACE FUNCTION calculate_billable_rate(
    p_loaded_cost NUMERIC,
    p_contract_type VARCHAR,
    p_fiscal_year INT
)
RETURNS NUMERIC AS $$
DECLARE
    v_overhead_percent NUMERIC;
    v_gna_percent NUMERIC;
    v_profit_percent NUMERIC;
    v_billable_rate NUMERIC;
BEGIN
    -- Get overhead, G&A, and profit rates for this contract type
    SELECT overhead_percent, gna_percent, profit_percent INTO
        v_overhead_percent, v_gna_percent, v_profit_percent
    FROM overhead_ga_rates
    WHERE fiscal_year = p_fiscal_year
        AND (contract_type = p_contract_type OR contract_type IS NULL)
        AND is_active = TRUE
    LIMIT 1;

    -- Fallback defaults if not found
    v_overhead_percent := COALESCE(v_overhead_percent, 65);
    v_gna_percent := COALESCE(v_gna_percent, 12);
    v_profit_percent := COALESCE(v_profit_percent, 10);

    -- Calculate: Loaded Cost * (1 + OH% + G&A% + Profit%)
    v_billable_rate := p_loaded_cost * (1 + (v_overhead_percent + v_gna_percent + v_profit_percent) / 100);

    RETURN v_billable_rate;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Apply Volume Discount
CREATE OR REPLACE FUNCTION apply_volume_discount(
    p_billable_rate NUMERIC,
    p_contract_type VARCHAR,
    p_contract_value NUMERIC,
    p_fiscal_year INT
)
RETURNS NUMERIC AS $$
DECLARE
    v_discount_percent NUMERIC := 0;
BEGIN
    SELECT discount_percent INTO v_discount_percent
    FROM volume_pricing_tiers
    WHERE fiscal_year = p_fiscal_year
        AND contract_type = p_contract_type
        AND p_contract_value >= min_contract_value_usd
        AND (max_contract_value_usd IS NULL OR p_contract_value < max_contract_value_usd)
        AND is_active = TRUE
    LIMIT 1;

    v_discount_percent := COALESCE(v_discount_percent, 0);

    -- Return rate after discount
    RETURN p_billable_rate * (1 - v_discount_percent / 100);
END;
$$ LANGUAGE plpgsql STABLE;

-- Function: Calculate Profit Margin USD
CREATE OR REPLACE FUNCTION calculate_profit_margin_usd(
    p_billable_rate NUMERIC,
    p_loaded_cost NUMERIC
)
RETURNS NUMERIC AS $$
BEGIN
    RETURN p_billable_rate - p_loaded_cost;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 13. RATE COMPLIANCE CHECK TRIGGER
-- ============================================================================

-- Prevent negative profit margins
CREATE OR REPLACE FUNCTION check_labor_rate_compliance()
RETURNS TRIGGER AS $$
BEGIN
    -- Check 1: Billable rate must be >= loaded cost
    IF NEW.billable_rate_usd < NEW.loaded_cost_usd THEN
        RAISE EXCEPTION 'Billable rate (%.2f) cannot be less than loaded cost (%.2f)',
            NEW.billable_rate_usd, NEW.loaded_cost_usd;
    END IF;

    -- Check 2: Profit margin cannot exceed 30%
    IF ((NEW.billable_rate_usd - NEW.loaded_cost_usd) / NEW.loaded_cost_usd * 100) > 30 THEN
        RAISE EXCEPTION 'Profit margin exceeds maximum allowed 30%%';
    END IF;

    -- Check 3: Base rate cannot exceed billable rate
    IF NEW.base_rate_usd > NEW.billable_rate_usd THEN
        RAISE EXCEPTION 'Base rate cannot exceed billable rate';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_labor_rate_compliance
BEFORE INSERT OR UPDATE ON labor_rates
FOR EACH ROW
EXECUTE FUNCTION check_labor_rate_compliance();

-- ============================================================================
-- 14. AUDIT TRAIL TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION log_rate_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.billable_rate_usd != OLD.billable_rate_usd THEN
            INSERT INTO rate_audit_trail
                (entity_type, entity_id, event_type, previous_value, new_value,
                 reason_for_change, changed_by, changed_at)
            VALUES
                ('LABOR_RATE', NEW.labor_rate_id, 'UPDATED',
                 OLD.billable_rate_usd, NEW.billable_rate_usd,
                 COALESCE(NEW.adjustment_reason, 'Rate update'),
                 COALESCE(NEW.created_by, 'SYSTEM'), CURRENT_TIMESTAMP);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_labor_rate_audit
AFTER UPDATE ON labor_rates
FOR EACH ROW
EXECUTE FUNCTION log_rate_changes();

-- ============================================================================
-- 15. SAMPLE DATA: Labor Categories & Rates
-- ============================================================================

INSERT INTO labor_categories
    (category_code, category_name, category_type, description, min_experience_years, skill_level, industry_segment, created_by)
VALUES
    ('DEV-SR', 'Senior Software Developer', 'CLIN', 'Leads development initiatives', 8, 'Senior', 'IT', 'SYSTEM'),
    ('DEV-JR', 'Junior Software Developer', 'CLIN', 'Entry-level development', 1, 'Entry', 'IT', 'SYSTEM'),
    ('PM-001', 'Program Manager', 'GSA_SCHEDULE', 'Overall program oversight', 10, 'Senior', 'Management', 'SYSTEM'),
    ('QA-001', 'QA Specialist', 'CLIN', 'Testing and validation', 3, 'Intermediate', 'IT', 'SYSTEM'),
    ('ENG-HW', 'Hardware Engineer', 'CLIN', 'Hardware design and integration', 7, 'Senior', 'Engineering', 'SYSTEM'),
    ('ADMIN-001', 'Administrative Assistant', 'CLIN', 'Administrative support', 1, 'Entry', 'Admin', 'SYSTEM');

-- ============================================================================
-- 16. SAMPLE LABOR RATES (FY 2026)
-- ============================================================================

INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type, base_rate_usd, direct_labor_cost_usd,
     billable_rate_usd, loaded_cost_usd, profit_margin_percent, effective_date, rate_status,
     rate_justification, created_by)
SELECT
    lc.labor_category_id,
    2026,
    'FFP',
    CASE
        WHEN lc.skill_level = 'Senior' THEN 95.00
        WHEN lc.skill_level = 'Intermediate' THEN 75.00
        ELSE 50.00
    END AS base_rate,
    CASE
        WHEN lc.skill_level = 'Senior' THEN 95.00
        WHEN lc.skill_level = 'Intermediate' THEN 75.00
        ELSE 50.00
    END AS direct_labor_cost,
    CASE
        WHEN lc.skill_level = 'Senior' THEN 215.00
        WHEN lc.skill_level = 'Intermediate' THEN 165.00
        ELSE 110.00
    END AS billable_rate,
    CASE
        WHEN lc.skill_level = 'Senior' THEN 155.00
        WHEN lc.skill_level = 'Intermediate' THEN 122.00
        ELSE 82.00
    END AS loaded_cost,
    CASE
        WHEN lc.skill_level = 'Senior' THEN 10.0
        WHEN lc.skill_level = 'Intermediate' THEN 8.5
        ELSE 7.0
    END AS profit_margin,
    '2026-01-01'::DATE,
    'APPROVED',
    'FY 2026 standard rate approved by Finance; compliant with DCAA burden & overhead standards',
    'SYSTEM'
FROM labor_categories lc
WHERE lc.is_active = TRUE;

-- ============================================================================
-- 17. SAMPLE CONTRACT RATE AGREEMENT
-- ============================================================================

INSERT INTO contract_rate_agreements
    (contract_id, contract_number, contract_name, customer_name, fiscal_year, contract_type,
     rate_lock_date, rate_lock_status, contract_ceiling_usd, target_profit_percent,
     dcaa_compliant, created_by)
VALUES
    ('DOD-2026-001', 'N6500123456789', 'Integrated IT Solutions Contract', 'U.S. Department of Defense',
     2026, 'FFP', '2026-01-15'::DATE, 'LOCKED', 5000000.00, 10.00, TRUE, 'SYSTEM'),
    ('GSA-2026-001', 'GS-07F-0123K', 'GSA Schedule IT Services', 'General Services Administration',
     2026, 'GSA_SCHEDULE', '2026-02-01'::DATE, 'AGREED', NULL, 8.00, TRUE, 'SYSTEM');

-- ============================================================================
-- 18. QUERY: Rate Justification Report (DCAA Compliance)
-- ============================================================================

CREATE OR REPLACE VIEW rate_justification_report AS
SELECT
    lc.category_code,
    lc.category_name,
    lc.skill_level,
    lr.fiscal_year,
    lr.contract_type,
    lr.base_rate_usd,
    lr.direct_labor_cost_usd,

    -- Burden Components
    lr.loaded_cost_usd - lr.direct_labor_cost_usd AS total_burden_usd,
    ROUND(((lr.loaded_cost_usd - lr.direct_labor_cost_usd) / lr.direct_labor_cost_usd * 100), 2) AS total_burden_percent,

    -- Overhead & G&A
    ogr.overhead_percent,
    ogr.gna_percent,
    ogr.profit_percent,

    -- Final Billable Rate
    lr.billable_rate_usd,
    lr.profit_margin_usd,
    lr.profit_margin_percent,

    -- Compliance
    lr.rate_status,
    ogr.dcaa_approval_date,
    lr.rate_justification,

    -- Date Info
    lr.effective_date,
    lr.expiration_date,
    lr.updated_at

FROM labor_categories lc
JOIN labor_rates lr ON lc.labor_category_id = lr.labor_category_id
LEFT JOIN overhead_ga_rates ogr ON lr.fiscal_year = ogr.fiscal_year AND ogr.is_active = TRUE
WHERE lc.is_active = TRUE AND lr.is_active = TRUE
ORDER BY lc.category_code, lr.fiscal_year DESC;

-- ============================================================================
-- 19. QUERY: FFP Contract Rate Lock Verification
-- ============================================================================

CREATE OR REPLACE VIEW ffp_rate_lock_verification AS
SELECT
    cra.contract_number,
    cra.contract_name,
    cra.customer_name,
    cra.rate_lock_date,
    cra.rate_lock_status,

    lc.category_code,
    lc.category_name,
    crli.negotiated_rate_usd,
    crli.negotiated_billable_rate_usd,

    -- Profit Check
    (crli.negotiated_billable_rate_usd - crli.negotiated_rate_usd) AS profit_usd,
    ROUND(((crli.negotiated_billable_rate_usd - crli.negotiated_rate_usd) / crli.negotiated_rate_usd * 100), 2) AS profit_percent,

    crli.rate_justification,
    crli.approval_date,
    crli.approved_by

FROM contract_rate_agreements cra
JOIN contract_rate_line_items crli ON cra.contract_rate_agreement_id = crli.contract_rate_agreement_id
JOIN labor_categories lc ON crli.labor_category_id = lc.labor_category_id
WHERE cra.contract_type = 'FFP' AND cra.rate_lock_status = 'LOCKED'
ORDER BY cra.contract_number, lc.category_code;

-- ============================================================================
-- 20. QUERY: DCAA Compliance Checklist
-- ============================================================================

CREATE OR REPLACE VIEW dcaa_compliance_checklist AS
WITH rate_checks AS (
    SELECT
        'Labor Rates Approved' AS check_item,
        COUNT(*) AS total_rates,
        SUM(CASE WHEN rate_status = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
        SUM(CASE WHEN rate_status = 'LOCKED' THEN 1 ELSE 0 END) AS locked_count,
        SUM(CASE WHEN rate_status IN ('PROVISIONAL', 'NEGOTIATED') THEN 1 ELSE 0 END) AS pending_count
    FROM labor_rates
    WHERE is_active = TRUE AND fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
),
overhead_checks AS (
    SELECT
        'Overhead & G&A Approved' AS check_item,
        COUNT(*) AS total_rates,
        SUM(CASE WHEN provisional_rate = FALSE THEN 1 ELSE 0 END) AS approved_count,
        0 AS locked_count,
        SUM(CASE WHEN provisional_rate = TRUE THEN 1 ELSE 0 END) AS pending_count
    FROM overhead_ga_rates
    WHERE is_active = TRUE AND fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
),
indirect_checks AS (
    SELECT
        'Indirect Cost Rates Approved' AS check_item,
        COUNT(*) AS total_rates,
        SUM(CASE WHEN rate_type = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
        0 AS locked_count,
        SUM(CASE WHEN rate_type IN ('PROVISIONAL', 'TENTATIVE') THEN 1 ELSE 0 END) AS pending_count
    FROM indirect_cost_rates
    WHERE is_active = TRUE AND fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
)
SELECT * FROM rate_checks
UNION ALL
SELECT * FROM overhead_checks
UNION ALL
SELECT * FROM indirect_checks;

-- ============================================================================
-- 21. QUERY: Volume Discount Impact Analysis
-- ============================================================================

CREATE OR REPLACE VIEW volume_discount_impact AS
WITH rate_data AS (
    SELECT
        lc.category_code,
        lc.category_name,
        lr.contract_type,
        lr.billable_rate_usd AS base_rate,
        vpt.min_contract_value_usd,
        vpt.max_contract_value_usd,
        vpt.discount_percent,
        lr.billable_rate_usd * (1 - vpt.discount_percent / 100) AS discounted_rate,
        (lr.billable_rate_usd * vpt.discount_percent / 100) AS discount_amount_per_hour
    FROM labor_rates lr
    JOIN labor_categories lc ON lr.labor_category_id = lc.labor_category_id
    JOIN volume_pricing_tiers vpt ON lr.contract_type = vpt.contract_type
        AND lr.fiscal_year = vpt.fiscal_year
    WHERE lr.is_active = TRUE AND vpt.is_active = TRUE
        AND lr.fiscal_year = EXTRACT(YEAR FROM CURRENT_DATE)
)
SELECT
    category_code,
    category_name,
    contract_type,
    base_rate,
    min_contract_value_usd,
    max_contract_value_usd,
    discount_percent,
    discounted_rate,
    discount_amount_per_hour,
    -- Annual savings at 2000 billable hours per category
    (discount_amount_per_hour * 2000) AS annual_savings_per_category
FROM rate_data
ORDER BY contract_type, base_rate DESC;

-- ============================================================================
-- 22. REFRESH STRATEGY FOR MATERIALIZED VIEW
-- ============================================================================

-- Run this periodically (e.g., daily or after rate changes):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY competitive_rate_summary;

-- ============================================================================
-- 23. EXPORT QUERY: SF 1411 Cost Analysis Form Data
-- ============================================================================

CREATE OR REPLACE VIEW sf_1411_export_data AS
SELECT
    cra.contract_number,
    cra.contract_name,
    cra.customer_name,
    cra.fiscal_year,
    cra.contract_type,
    cra.contract_ceiling_usd,
    cra.target_profit_percent,

    lc.category_code,
    lc.category_name,
    lc.skill_level,

    crli.negotiated_rate_usd AS proposed_rate,

    -- Cost Build-up
    crli.negotiated_rate_usd AS direct_labor,
    ROUND(crli.negotiated_rate_usd * 0.5065, 2) AS fringes, -- 50.65% avg burden
    ROUND(crli.negotiated_rate_usd * 0.65, 2) AS overhead,
    ROUND(crli.negotiated_rate_usd * 0.12, 2) AS gna,
    crli.negotiated_billable_rate_usd AS total_cost_plus_profit,

    -- Profit Analysis
    ROUND((crli.negotiated_billable_rate_usd - crli.negotiated_rate_usd), 2) AS profit,
    ROUND(((crli.negotiated_billable_rate_usd - crli.negotiated_rate_usd) / crli.negotiated_rate_usd * 100), 2) AS profit_percent,

    crli.rate_justification,
    crli.approved_by,
    crli.approval_date

FROM contract_rate_agreements cra
JOIN contract_rate_line_items crli ON cra.contract_rate_agreement_id = crli.contract_rate_agreement_id
JOIN labor_categories lc ON crli.labor_category_id = lc.labor_category_id
WHERE cra.is_active = TRUE AND crli.is_active = TRUE
ORDER BY cra.contract_number, lc.category_code;

-- ============================================================================
-- 24. CONSTRAINTS & INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_labor_rates_fy_category ON labor_rates(fiscal_year, labor_category_id);
CREATE INDEX idx_overhead_ga_fy_contract ON overhead_ga_rates(fiscal_year, contract_type);
CREATE INDEX idx_volume_pricing_fy_type_value ON volume_pricing_tiers(fiscal_year, contract_type, min_contract_value_usd);
CREATE INDEX idx_contract_rate_line_items_rate ON contract_rate_line_items(labor_rate_id);
CREATE INDEX idx_audit_trail_changed_at ON rate_audit_trail(changed_at DESC);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
