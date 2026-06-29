-- ============================================================================
-- FEDERAL CONTRACT PRICING — SAMPLE DATA & DCAA-COMPLIANT INSERTS
-- FY 2026 Configuration with Real-World Rates & Compliance
-- ============================================================================

-- This file contains ready-to-use sample data for:
-- - Labor categories (6 categories, 3 skill levels)
-- - Labor rates by contract type (FFP, T&M, IDIQ, GSA Schedule)
-- - Burden rates (8 burden types, DCAA-approved)
-- - Overhead & G&A (3 rate structures, all DCAA-approved)
-- - Volume pricing (IDIQ discounts)
-- - Sample contracts (2 active contracts)
-- - Rate justifications & audit trails

-- ============================================================================
-- 1. LABOR CATEGORIES (6 Categories)
-- ============================================================================

-- IT Categories
INSERT INTO labor_categories
    (category_code, category_name, category_type, description, min_experience_years, skill_level, industry_segment, created_by)
VALUES
    ('DEV-JR', 'Junior Software Developer', 'CLIN', 'Entry-level development; supports senior developers; limited independent responsibility', 1, 'Entry', 'IT', 'SYSTEM'),
    ('DEV-SR', 'Senior Software Developer', 'CLIN', 'Leads development initiatives; architecture design; code review; mentors junior staff', 8, 'Senior', 'IT', 'SYSTEM'),
    ('QA-001', 'QA Specialist / Test Engineer', 'CLIN', 'Test planning, execution, automation; quality assurance; defect management', 3, 'Intermediate', 'IT', 'SYSTEM');

-- Management & Engineering
INSERT INTO labor_categories
    (category_code, category_name, category_type, description, min_experience_years, skill_level, industry_segment, created_by)
VALUES
    ('PM-001', 'Program Manager (Level 1)', 'GSA_SCHEDULE', 'Overall program oversight; schedule/budget management; stakeholder coordination', 10, 'Senior', 'Management', 'SYSTEM'),
    ('ENG-HW', 'Hardware Engineer', 'CLIN', 'Hardware design, integration, testing; FPGA/systems integration', 7, 'Senior', 'Engineering', 'SYSTEM');

-- Administrative
INSERT INTO labor_categories
    (category_code, category_name, category_type, description, min_experience_years, skill_level, industry_segment, created_by)
VALUES
    ('ADMIN-001', 'Administrative Assistant', 'CLIN', 'Administrative support; scheduling; document management', 1, 'Entry', 'Admin', 'SYSTEM');

-- ============================================================================
-- 2. BURDEN RATES (FY 2026, DCAA-Approved)
-- ============================================================================

-- FICA Payroll Tax (7.65% federal + 1.45% Medicare = 9.1% total, but we use 7.65% federal)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'FICA', 7.65, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-001-FICA', 'Federal payroll tax (Social Security 6.2% + Medicare 1.45%)', TRUE, 'SYSTEM');

-- Health Insurance (assumed 15.5% of salary for company-paid portion)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'HEALTH_INSURANCE', 15.50, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-002-HEALTH', 'Group health insurance (medical, dental, vision)', TRUE, 'SYSTEM');

-- Pension / 401(k) Contribution
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'PENSION', 8.00, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-003-PENSION', 'Defined benefit pension + 401(k) match (8%)', TRUE, 'SYSTEM');

-- Training & Development
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'TRAINING', 2.50, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-004-TRAINING', 'Professional development, certifications, training', TRUE, 'SYSTEM');

-- Facilities (allocated to direct labor hours)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'FACILITIES', 12.00, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-005-FACILITIES', 'Rent, utilities, maintenance, depreciation', TRUE, 'SYSTEM');

-- Administrative Labor (HR, Finance, IT ops, etc.)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'ADMIN', 5.00, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-006-ADMIN', 'HR, Finance, IT operations, legal support', TRUE, 'SYSTEM');

-- Worker's Compensation (avg ~2% for IT/professional services)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'WORKERS_COMP', 2.00, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-007-WCOMP', "Workers' compensation insurance", TRUE, 'SYSTEM');

-- -- Bonus/Incentive Pool (avg 2-5%, we'll use 2% conservative)
INSERT INTO burden_rates
    (fiscal_year, burden_type, rate_percent, allocation_method, dcaa_compliant, dcaa_rate_id, description, is_active, created_by)
VALUES
    (2026, 'BONUS', 2.00, '%_OF_LABOR', TRUE, 'DCAA-BURDEN-008-BONUS', 'Annual performance bonus / incentive pool', TRUE, 'SYSTEM');

-- Total Burden Rate: 7.65 + 15.5 + 8 + 2.5 + 12 + 5 + 2 + 2 = 54.65% (close to real-world 50-60%)

-- ============================================================================
-- 3. OVERHEAD & G&A RATES (FY 2026, DCAA-Approved)
-- ============================================================================

-- Standard FFP/T&M Rates (DCAA-Approved)
INSERT INTO overhead_ga_rates
    (fiscal_year, overhead_percent, gna_percent, profit_percent,
     overhead_allocation_method, gna_allocation_method,
     dcaa_rate_approval_date, dcaa_approval_number, provisional_rate,
     contract_type, description, audit_trail, is_active, created_by)
VALUES
    (2026, 65.00, 12.00, 10.00,
     '%_OF_LABOR', '%_OF_LABOR',
     '2025-10-15'::DATE, 'DCAA-2026-FFP-APPROVED',
     FALSE, 'FFP',
     'Standard FFP rates - DCAA final approval 2025-10-15',
     'DCAA Audit 2025-10-15: Approved; Facilities adjustment 2025-09-30 (+2%)',
     TRUE, 'SYSTEM');

-- T&M Rates (lower profit margin, higher OH for variable staffing)
INSERT INTO overhead_ga_rates
    (fiscal_year, overhead_percent, gna_percent, profit_percent,
     overhead_allocation_method, gna_allocation_method,
     dcaa_rate_approval_date, dcaa_approval_number, provisional_rate,
     contract_type, description, is_active, created_by)
VALUES
    (2026, 68.00, 14.00, 6.00,
     '%_OF_LABOR', '%_OF_LABOR',
     '2025-10-01'::DATE, 'DCAA-2026-TM-APPROVED',
     FALSE, 'T&M',
     'T&M rates (higher OH for variable staffing, lower profit)',
     TRUE, 'SYSTEM');

-- IDIQ Rates (provisional, pending negotiation)
INSERT INTO overhead_ga_rates
    (fiscal_year, overhead_percent, gna_percent, profit_percent,
     overhead_allocation_method, gna_allocation_method,
     dcaa_rate_approval_date, provisional_rate,
     contract_type, description, is_active, created_by)
VALUES
    (2026, 75.00, 15.00, 12.00,
     '%_OF_LABOR', '%_OF_LABOR',
     NULL, TRUE,
     'IDIQ',
     'IDIQ provisional rates - pending DCAA negotiation',
     TRUE, 'SYSTEM');

-- GSA Schedule Rates (approved, 1–3% volume discount only per GSA terms)
INSERT INTO overhead_ga_rates
    (fiscal_year, overhead_percent, gna_percent, profit_percent,
     overhead_allocation_method, gna_allocation_method,
     dcaa_rate_approval_date, dcaa_approval_number, provisional_rate,
     contract_type, description, is_active, created_by)
VALUES
    (2026, 55.00, 10.00, 8.00,
     '%_OF_LABOR', '%_OF_LABOR',
     '2025-06-01'::DATE, 'GSA-2025-SCHEDULE-APPROVED',
     FALSE, 'GSA_SCHEDULE',
     'GSA Schedule rates (lower profit due to GSA terms & volume)',
     TRUE, 'SYSTEM');

-- ============================================================================
-- 4. INDIRECT COST RATES (DCAA-Compliant)
-- ============================================================================

-- Approved Indirect Cost Rate (based on Overhead + G&A)
INSERT INTO indirect_cost_rates
    (fiscal_year, rate_type, rate_value, allocation_base,
     dcaa_rate_id, dcaa_approval_date, negotiated_with_agency,
     effective_date, expiration_date,
     includes_overhead, includes_gna, includes_profit,
     rate_justification, is_active, created_by)
VALUES
    (2026, 'APPROVED', 1.77, 'DIRECT_LABOR',
     'DCAA-2026-ICR-FINAL', '2025-10-15'::DATE, 'DCAA',
     '2026-01-01'::DATE, '2026-12-31'::DATE,
     TRUE, TRUE, FALSE,
     'Approved rate: (65% OH + 12% G&A) = 77% on direct labor; Negotiated final 2025-10-15',
     TRUE, 'SYSTEM');

-- Provisional Rate (pending negotiation)
INSERT INTO indirect_cost_rates
    (fiscal_year, rate_type, rate_value, allocation_base,
     dcaa_rate_id, effective_date,
     includes_overhead, includes_gna, includes_profit,
     rate_justification, is_active, created_by)
VALUES
    (2026, 'PROVISIONAL', 1.85, 'DIRECT_LABOR',
     'DCAA-2026-ICR-PROV', '2026-01-01'::DATE,
     TRUE, TRUE, FALSE,
     'Provisional rate pending DCAA negotiations; subject to adjustment in audit',
     TRUE, 'SYSTEM');

-- ============================================================================
-- 5. VOLUME PRICING TIERS (IDIQ)
-- ============================================================================

-- Base pricing (no volume discount)
INSERT INTO volume_pricing_tiers
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, discount_type, description, is_active, created_by)
VALUES
    (2026, 'IDIQ', 0.00, 999999.99, 0.0, 'PERCENTAGE', 'Base rate - no volume discount', TRUE, 'SYSTEM');

-- Tier 1: $1M–$5M (2.5% discount)
INSERT INTO volume_pricing_tiers
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, discount_type, description, is_active, created_by)
VALUES
    (2026, 'IDIQ', 1000000.00, 4999999.99, 2.5, 'PERCENTAGE', 'Volume discount: $1M–$5M', TRUE, 'SYSTEM');

-- Tier 2: $5M–$10M (5.0% discount)
INSERT INTO volume_pricing_tiers
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, discount_type, description, is_active, created_by)
VALUES
    (2026, 'IDIQ', 5000000.00, 9999999.99, 5.0, 'PERCENTAGE', 'Volume discount: $5M–$10M', TRUE, 'SYSTEM');

-- Tier 3: $10M+ (7.5% discount)
INSERT INTO volume_pricing_tiers
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, discount_type, description, is_active, created_by)
VALUES
    (2026, 'IDIQ', 10000000.00, NULL, 7.5, 'PERCENTAGE', 'Volume discount: $10M+', TRUE, 'SYSTEM');

-- No volume discount for GSA Schedule (GSA terms prohibit)
INSERT INTO volume_pricing_tiers
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, discount_type, description, is_active, created_by)
VALUES
    (2026, 'GSA_SCHEDULE', 0.00, NULL, 0.0, 'PERCENTAGE', 'GSA Schedule - no additional volume discounts', TRUE, 'SYSTEM');

-- ============================================================================
-- 6. LABOR RATES (FY 2026, All Contract Types)
-- ============================================================================

-- FFP Contract Rates
-- Junior Developer (Entry Level)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    50.00, 50.00, 110.00, 76.83,
    7.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 entry-level rate; market research shows $48–52 range; DCAA-compliant burden (54.65%) + approved OH/G&A (77%) + 7% profit margin',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-JR';

-- Senior Developer (FFP)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    95.00, 95.00, 215.00, 146.42,
    10.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 senior-level rate; market data $90–100 range; DCAA-approved burden (54.65%) + overhead (65%) + G&A (12%) + 10% profit = $215/hr',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-SR';

-- QA Specialist (FFP)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    65.00, 65.00, 147.00, 100.52,
    8.5, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 QA specialist rate; intermediate skill level; market $62–68 range; loaded with DCAA burdens + standard overhead',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'QA-001';

-- Program Manager (FFP, GSA Schedule version)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    110.00, 110.00, 250.00, 169.11,
    10.5, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 PM (senior management); 10+ years experience; market rate $105–115; DCAA-compliant with 54.65% burden + 77% OH/G&A',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'PM-001';

-- Hardware Engineer (FFP)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    105.00, 105.00, 238.00, 161.89,
    10.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 hardware engineer; 7+ years FPGA/integration experience; specialized role; market $100–110; DCAA-compliant burden + OH/G&A',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'ENG-HW';

-- Admin Assistant (FFP)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'FFP',
    35.00, 35.00, 79.00, 53.98,
    6.5, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'FY 2026 administrative support; entry level; market $33–38; lower profit margin due to commodity labor',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'ADMIN-001';

-- ============================================================================
-- 7. T&M CONTRACT RATES (FY 2026)
-- ============================================================================

-- T&M rates have slightly higher base due to staffing variability
-- Profit margin 6% (lower than FFP) due to pass-through model
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'T&M',
    95.00, 95.00, 204.00, 146.42,
    6.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'T&M senior developer rate; higher OH (68%) for variable staffing; lower profit (6%) due to pass-through model; subject to annual COLA adjustment',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-SR';

-- Remaining T&M rates (abbreviated)
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'T&M',
    50.00, 50.00, 107.00, 76.83,
    4.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'T&M junior developer; lower skill level; minimal profit margin',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-JR';

-- ============================================================================
-- 8. IDIQ CONTRACT RATES (FY 2026, Provisional)
-- ============================================================================

-- IDIQ rates are higher due to longer-term commitment + volume discounts
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'IDIQ',
    95.00, 95.00, 224.00, 161.89,
    12.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'IDIQ senior developer; provisional rates pending DCAA negotiation; higher OH (75%) + G&A (15%) + 12% profit; subject to volume discounts',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-SR';

-- IDIQ junior developer
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'IDIQ',
    50.00, 50.00, 118.00, 76.83,
    8.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'IDIQ junior developer; provisional rates',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'DEV-JR';

-- ============================================================================
-- 9. GSA SCHEDULE RATES (FY 2026)
-- ============================================================================

-- GSA Schedule rates are published, lower profit margin (8%)
-- Overhead & G&A lower due to GSA terms
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type,
     base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
     profit_margin_percent, effective_date, expiration_date, rate_status,
     rate_justification, cola_percent, created_by)
SELECT
    lc.labor_category_id, 2026, 'GSA_SCHEDULE',
    110.00, 110.00, 185.00, 169.11,
    8.0, '2026-01-01'::DATE, '2026-12-31'::DATE, 'APPROVED',
    'GSA Schedule Program Manager; published rates; lower OH (55%) + G&A (10%) + 8% profit per GSA 2025-0001 contract',
    0, 'SYSTEM'
FROM labor_categories lc
WHERE lc.category_code = 'PM-001';

-- ============================================================================
-- 10. SAMPLE CONTRACT RATE AGREEMENTS
-- ============================================================================

-- DOD FFP Contract (Locked Rates)
INSERT INTO contract_rate_agreements
    (contract_id, contract_number, contract_name, customer_name, fiscal_year, contract_type,
     rate_lock_date, rate_lock_status, contract_ceiling_usd, not_to_exceed_usd,
     target_profit_percent, minimum_profit_percent, escalation_percent, escalation_type,
     dcaa_compliant, audit_status, created_by)
VALUES
    ('DOD-2026-001', 'N6500123456789', 'Integrated IT Solutions Contract', 'U.S. Department of Defense',
     2026, 'FFP',
     '2026-01-15'::DATE, 'LOCKED',
     5000000.00, 4950000.00,
     10.00, 8.00,
     0.00, NULL,
     TRUE, 'APPROVED',
     'SYSTEM');

-- GSA Schedule Contract (Agreed Rates)
INSERT INTO contract_rate_agreements
    (contract_id, contract_number, contract_name, customer_name, fiscal_year, contract_type,
     rate_lock_date, rate_lock_status, contract_ceiling_usd, not_to_exceed_usd,
     target_profit_percent, minimum_profit_percent, escalation_percent, escalation_type,
     dcaa_compliant, audit_status, created_by)
VALUES
    ('GSA-2026-001', 'GS-07F-0123K', 'GSA Schedule IT Services', 'General Services Administration',
     2026, 'GSA_SCHEDULE',
     '2026-02-01'::DATE, 'AGREED',
     NULL, NULL,
     8.00, 7.00,
     2.50, 'COLA',
     TRUE, 'APPROVED',
     'SYSTEM');

-- ============================================================================
-- 11. CONTRACT RATE LINE ITEMS (DOD FFP Contract)
-- ============================================================================

-- Senior Developer for DOD Contract
INSERT INTO contract_rate_line_items
    (contract_rate_agreement_id, labor_category_id, labor_rate_id,
     negotiated_rate_usd, negotiated_billable_rate_usd,
     rate_justification, negotiation_notes,
     approved_by, approval_date, created_by)
SELECT
    cra.contract_rate_agreement_id,
    lc.labor_category_id,
    lr.labor_rate_id,
    95.00, 215.00,
    'Senior Developer - FFP rate locked per proposal 2026-01-15; matches market data + DCAA-approved overhead structure',
    'Negotiated with DOD CPARS team; rates locked at contract award.',
    'Jane Doe, CFO',
    '2026-01-15'::DATE,
    'SYSTEM'
FROM contract_rate_agreements cra
JOIN labor_categories lc ON lc.category_code = 'DEV-SR'
JOIN labor_rates lr ON lr.labor_category_id = lc.labor_category_id
    AND lr.fiscal_year = 2026
    AND lr.contract_type = 'FFP'
WHERE cra.contract_number = 'N6500123456789';

-- Junior Developer for DOD Contract
INSERT INTO contract_rate_line_items
    (contract_rate_agreement_id, labor_category_id, labor_rate_id,
     negotiated_rate_usd, negotiated_billable_rate_usd,
     rate_justification, approved_by, approval_date, created_by)
SELECT
    cra.contract_rate_agreement_id,
    lc.labor_category_id,
    lr.labor_rate_id,
    50.00, 110.00,
    'Junior Developer - FFP entry-level rate; locked per proposal',
    'Jane Doe, CFO',
    '2026-01-15'::DATE,
    'SYSTEM'
FROM contract_rate_agreements cra
JOIN labor_categories lc ON lc.category_code = 'DEV-JR'
JOIN labor_rates lr ON lr.labor_category_id = lc.labor_category_id
    AND lr.fiscal_year = 2026
    AND lr.contract_type = 'FFP'
WHERE cra.contract_number = 'N6500123456789';

-- Program Manager for DOD Contract
INSERT INTO contract_rate_line_items
    (contract_rate_agreement_id, labor_category_id, labor_rate_id,
     negotiated_rate_usd, negotiated_billable_rate_usd,
     rate_justification, approved_by, approval_date, created_by)
SELECT
    cra.contract_rate_agreement_id,
    lc.labor_category_id,
    lr.labor_rate_id,
    110.00, 250.00,
    'Program Manager (Senior) - FFP rate; senior management oversight',
    'Jane Doe, CFO',
    '2026-01-15'::DATE,
    'SYSTEM'
FROM contract_rate_agreements cra
JOIN labor_categories lc ON lc.category_code = 'PM-001'
JOIN labor_rates lr ON lr.labor_category_id = lc.labor_category_id
    AND lr.fiscal_year = 2026
    AND lr.contract_type = 'FFP'
WHERE cra.contract_number = 'N6500123456789';

-- ============================================================================
-- 12. CONTRACT RATE LINE ITEMS (GSA Schedule)
-- ============================================================================

-- Program Manager for GSA Schedule
INSERT INTO contract_rate_line_items
    (contract_rate_agreement_id, labor_category_id, labor_rate_id,
     negotiated_rate_usd, negotiated_billable_rate_usd,
     rate_justification, approved_by, approval_date, created_by)
SELECT
    cra.contract_rate_agreement_id,
    lc.labor_category_id,
    lr.labor_rate_id,
    110.00, 185.00,
    'Program Manager - GSA Schedule rate per contract GS-07F-0123K; published rate',
    'Jane Doe, CFO',
    '2026-02-01'::DATE,
    'SYSTEM'
FROM contract_rate_agreements cra
JOIN labor_categories lc ON lc.category_code = 'PM-001'
JOIN labor_rates lr ON lr.labor_category_id = lc.labor_category_id
    AND lr.fiscal_year = 2026
    AND lr.contract_type = 'GSA_SCHEDULE'
WHERE cra.contract_number = 'GS-07F-0123K';

-- ============================================================================
-- 13. AUDIT TRAIL ENTRIES (Sample DCAA Audit Events)
-- ============================================================================

-- DCAA Review of Senior Developer FFP Rate
INSERT INTO rate_audit_trail
    (entity_type, entity_id, event_type, previous_value, new_value,
     reason_for_change, dcaa_audit_flag, dcaa_audit_comments,
     changed_by, changed_at, approval_date, approved_by)
SELECT
    'LABOR_RATE',
    lr.labor_rate_id,
    'APPROVED',
    NULL, 215.00,
    'DCAA audited FY 2026 labor rates; Senior Developer FFP rate approved as reasonable per market data',
    TRUE,
    'Rate approved; burden components validated (54.65% total); overhead (65%) + G&A (12%) within DCAA guidelines; profit margin (10%) acceptable',
    'DCAA_AUDITOR',
    '2025-10-15'::TIMESTAMP,
    '2025-10-15'::DATE,
    'DCAA Contract Audit Agency'
FROM labor_rates lr
WHERE lr.labor_category_id = (SELECT labor_category_id FROM labor_categories WHERE category_code = 'DEV-SR')
  AND lr.fiscal_year = 2026
  AND lr.contract_type = 'FFP'
LIMIT 1;

-- DCAA Question about Overhead Allocation
INSERT INTO rate_audit_trail
    (entity_type, entity_id, event_type, previous_value, new_value,
     reason_for_change, dcaa_audit_flag, dcaa_audit_comments,
     changed_by, changed_at, approval_date)
SELECT
    'OVERHEAD_GA',
    ogr.overhead_ga_rate_id,
    'QUESTIONED',
    65.00, 65.00,
    'DCAA audit question: Justify 65% overhead allocation vs. DCAA database (avg 62-68%)',
    TRUE,
    'Response provided 2025-10-12: Facilities costs increased 2%; detailed cost substantiation provided; DCAA concurred; approved 2025-10-15',
    'COMPANY_CFO',
    '2025-10-12'::TIMESTAMP,
    '2025-10-15'::DATE
FROM overhead_ga_rates ogr
WHERE ogr.fiscal_year = 2026
  AND ogr.contract_type = 'FFP'
  AND ogr.is_active = TRUE
LIMIT 1;

-- ============================================================================
-- 14. COST ANALYSIS EXPORT (SF 1411 Export)
-- ============================================================================

INSERT INTO cost_analysis_export_history
    (contract_id, export_type, export_format, export_filename, export_path,
     exported_by, authorized_signatory, signature_date, is_official_submission)
VALUES
    ('DOD-2026-001', 'SF_1411', 'PDF', 'DOD_2026_001_SF_1411_SIGNED.pdf',
     '/exports/2026/DOD/DOD_2026_001_SF_1411_SIGNED.pdf',
     'john.smith@company.com',
     'Jane Doe, Chief Financial Officer',
     '2026-01-14'::DATE,
     TRUE);

INSERT INTO cost_analysis_export_history
    (contract_id, export_type, export_format, export_filename, export_path,
     exported_by, authorized_signatory, signature_date, is_official_submission)
VALUES
    ('GSA-2026-001', 'COST_SUMMARY', 'EXCEL', 'GSA_2026_001_COST_SUMMARY.xlsx',
     '/exports/2026/GSA/GSA_2026_001_COST_SUMMARY.xlsx',
     'john.smith@company.com',
     'Jane Doe, Chief Financial Officer',
     '2026-02-01'::DATE,
     FALSE);

-- ============================================================================
-- 15. COMPLIANCE VERIFICATION QUERIES
-- ============================================================================

-- Verify all rates are compliant (profit margin 0-30%)
-- SELECT lr.labor_rate_id, lc.category_code, lr.profit_margin_percent,
--        CASE WHEN lr.profit_margin_percent < 0 OR lr.profit_margin_percent > 30
--            THEN 'NON-COMPLIANT' ELSE 'COMPLIANT' END AS status
-- FROM labor_rates lr
-- JOIN labor_categories lc ON lr.labor_category_id = lc.labor_category_id
-- WHERE lr.fiscal_year = 2026;

-- Verify FFP contract rates are locked
-- SELECT * FROM ffp_rate_lock_verification
-- WHERE rate_lock_status != 'LOCKED';

-- Verify DCAA compliance checklist
-- SELECT * FROM dcaa_compliance_checklist;

-- ============================================================================
-- END OF SAMPLE DATA
-- ============================================================================
