-- ============================================================================
-- FEDERAL CONTRACTING PAST PERFORMANCE DATABASE SCHEMA
-- ============================================================================
-- Purpose: Support federal proposal development with indexed search on past
--          performance, audit trails, and export-ready narrative generation
-- Optimization: Query responses <100ms for proposal deadline scenarios
-- Audit: Full immutable trail with version control and change tracking
-- ============================================================================

-- ============================================================================
-- 1. CORE REFERENCE TABLES (Static/Semi-static)
-- ============================================================================

CREATE TABLE IF NOT EXISTS naics_codes (
    naics_id SERIAL PRIMARY KEY,
    code VARCHAR(6) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    division_code VARCHAR(2),
    division_title VARCHAR(255),
    group_code VARCHAR(3),
    group_title VARCHAR(255),
    class_code VARCHAR(4),
    class_title VARCHAR(255),
    industry_code VARCHAR(6),
    industry_title VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_naics_code (code),
    INDEX idx_naics_division (division_code),
    INDEX idx_naics_group (group_code),
    INDEX idx_naics_class (class_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS psc_codes (
    psc_id SERIAL PRIMARY KEY,
    code VARCHAR(4) NOT NULL UNIQUE,
    class_title VARCHAR(255) NOT NULL,
    group_code VARCHAR(1),
    group_title VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_psc_code (code),
    INDEX idx_psc_group (group_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS contract_vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    vehicle_type VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(500),
    abbreviation VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_vehicle_type (vehicle_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO contract_vehicles (vehicle_type, description, abbreviation) VALUES
('GSA Schedule', 'General Services Administration Schedule Contract', 'GSA'),
('IDIQ', 'Indefinite Delivery/Indefinite Quantity', 'IDIQ'),
('FFP', 'Firm Fixed Price', 'FFP'),
('T&M', 'Time & Materials', 'T&M'),
('Managed Services', 'Ongoing Managed Services Contract', 'MS'),
('BPA', 'Blanket Purchase Agreement', 'BPA'),
('CCS', 'Customer Specific Contracts', 'CCS');

CREATE TABLE IF NOT EXISTS customer_types (
    customer_type_id SERIAL PRIMARY KEY,
    customer_type VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer_type (customer_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO customer_types (customer_type, description) VALUES
('Federal Agency', 'U.S. Federal Government Agency'),
('Commercial', 'Commercial Private Sector'),
('State/Local Government', 'State or Local Government'),
('DOD', 'Department of Defense'),
('GSA', 'General Services Administration');

CREATE TABLE IF NOT EXISTS federal_agencies (
    agency_id SERIAL PRIMARY KEY,
    agency_code VARCHAR(4),
    agency_name VARCHAR(255) NOT NULL,
    parent_agency_id INT,
    country VARCHAR(2) DEFAULT 'US',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_agency (agency_code, agency_name),
    INDEX idx_agency_name (agency_name),
    INDEX idx_agency_code (agency_code),
    FOREIGN KEY (parent_agency_id) REFERENCES federal_agencies(agency_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample federal agencies
INSERT IGNORE INTO federal_agencies (agency_code, agency_name, country) VALUES
('0100', 'Department of Defense', 'US'),
('0200', 'General Services Administration', 'US'),
('0300', 'Department of Veterans Affairs', 'US'),
('0400', 'Department of Homeland Security', 'US'),
('0500', 'Department of State', 'US'),
('0600', 'Department of Health & Human Services', 'US'),
('0700', 'Department of Energy', 'US'),
('0800', 'National Science Foundation', 'US'),
('0900', 'National Aeronautics & Space Admin', 'US'),
('1000', 'Environmental Protection Agency', 'US');

-- ============================================================================
-- 2. CONTACT & ORGANIZATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS contacts (
    contact_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    mobile VARCHAR(20),
    organization_name VARCHAR(255),
    organization_type VARCHAR(50),
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(2) DEFAULT 'US',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    updated_by VARCHAR(100),
    INDEX idx_contact_name (last_name, first_name),
    INDEX idx_contact_email (email),
    INDEX idx_contact_phone (phone),
    INDEX idx_organization (organization_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. PAST PERFORMANCE CONTRACT TABLE (Main Entity)
-- ============================================================================

CREATE TABLE IF NOT EXISTS past_performance_contracts (
    contract_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,

    -- Contract Identification
    contract_number VARCHAR(50) NOT NULL UNIQUE,
    contract_title VARCHAR(500) NOT NULL,
    contract_summary TEXT,
    customer_id INT,
    customer_name VARCHAR(255) NOT NULL,
    customer_type_id INT,
    customer_type VARCHAR(50),

    -- Classification
    vehicle_id INT,
    vehicle_type VARCHAR(50) NOT NULL,
    naics_id INT,
    naics_code VARCHAR(6),
    psc_id INT,
    psc_code VARCHAR(4),

    -- Contract Dates (for searching 7/10-year windows)
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    contract_value_usd DECIMAL(15,2),

    -- Performance Data
    on_time_delivery_pct DECIMAL(5,2),
    cost_variance_pct DECIMAL(7,2),
    quality_rating VARCHAR(50),
    re_award_pct DECIMAL(5,2),
    contract_status VARCHAR(50),

    -- Incumbent/Program Management
    program_manager_id INT,
    program_manager_name VARCHAR(255),
    agency_poc_id INT,
    agency_poc_name VARCHAR(255),
    ordering_officer_id INT,
    ordering_officer_name VARCHAR(255),

    -- Deliverables/Outcomes Summary (for proposal narrative)
    key_deliverables TEXT,
    outcomes_summary TEXT,
    challenges_overcome TEXT,

    -- Document Storage (PDFs, links to proof)
    performance_report_url VARCHAR(2000),
    final_report_url VARCHAR(2000),
    award_letter_url VARCHAR(2000),
    customer_reference_url VARCHAR(2000),

    -- Metrics & Tracking
    total_labor_hours INT,
    team_size_avg INT,
    subcontractor_involvement VARCHAR(255),

    -- Audit Trail (Immutable)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    deleted_at TIMESTAMP NULL,
    deleted_by VARCHAR(100),
    version INT NOT NULL DEFAULT 1,
    record_status VARCHAR(50) NOT NULL DEFAULT 'active',

    -- Indexes for Fast Queries (Proposal deadline <5 days)
    INDEX idx_customer_name (customer_name),
    INDEX idx_customer_type (customer_type),
    INDEX idx_naics_code (naics_code),
    INDEX idx_psc_code (psc_code),
    INDEX idx_vehicle_type (vehicle_type),
    INDEX idx_start_date (start_date),
    INDEX idx_end_date (end_date),
    INDEX idx_date_range (start_date, end_date),
    INDEX idx_contract_status (contract_status),
    INDEX idx_record_status (record_status),
    INDEX idx_quality_rating (quality_rating),
    INDEX idx_re_award (re_award_pct),
    UNIQUE KEY unique_contract (contract_number),
    FOREIGN KEY (customer_id) REFERENCES federal_agencies(agency_id),
    FOREIGN KEY (customer_type_id) REFERENCES customer_types(customer_type_id),
    FOREIGN KEY (vehicle_id) REFERENCES contract_vehicles(vehicle_id),
    FOREIGN KEY (naics_id) REFERENCES naics_codes(naics_id),
    FOREIGN KEY (psc_id) REFERENCES psc_codes(psc_id),
    FOREIGN KEY (program_manager_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (agency_poc_id) REFERENCES contacts(contact_id),
    FOREIGN KEY (ordering_officer_id) REFERENCES contacts(contact_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. AUDIT LOG TABLE (Immutable Change History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS past_performance_audit_log (
    log_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    change_reason VARCHAR(500),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    record_version INT,

    INDEX idx_contract_id (contract_id),
    INDEX idx_changed_at (changed_at),
    INDEX idx_changed_by (changed_by),
    INDEX idx_change_type (change_type),
    FOREIGN KEY (contract_id) REFERENCES past_performance_contracts(contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. DELIVERABLES TABLE (Linked Documents & Evidence)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contract_deliverables (
    deliverable_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    deliverable_name VARCHAR(500) NOT NULL,
    deliverable_type VARCHAR(100),
    description TEXT,
    delivery_date DATE,
    status VARCHAR(50),
    document_url VARCHAR(2000),
    document_type VARCHAR(50),
    file_size_kb INT,
    stored_path VARCHAR(2000),
    external_link VARCHAR(2000),
    accepted_date DATE,
    customer_acceptance_note TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_contract_id (contract_id),
    INDEX idx_deliverable_type (deliverable_type),
    INDEX idx_delivery_date (delivery_date),
    INDEX idx_status (status),
    FOREIGN KEY (contract_id) REFERENCES past_performance_contracts(contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 6. PERFORMANCE METRICS TABLE (Granular Performance Data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    metric_category VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_unit VARCHAR(50),
    reporting_period_start DATE,
    reporting_period_end DATE,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',

    INDEX idx_contract_id (contract_id),
    INDEX idx_metric_category (metric_category),
    INDEX idx_metric_name (metric_name),
    INDEX idx_reporting_period (reporting_period_start, reporting_period_end),
    FOREIGN KEY (contract_id) REFERENCES past_performance_contracts(contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 7. TEAMING/SUBCONTRACTOR TABLE (Partner Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS contract_team_members (
    team_member_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    contract_id BIGINT UNSIGNED NOT NULL,
    contact_id INT,
    member_name VARCHAR(255) NOT NULL,
    member_role VARCHAR(255),
    member_company VARCHAR(255),
    is_subcontractor BOOLEAN DEFAULT FALSE,
    responsibility_description TEXT,
    labor_hours INT,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_contract_id (contract_id),
    INDEX idx_contact_id (contact_id),
    INDEX idx_is_subcontractor (is_subcontractor),
    FOREIGN KEY (contract_id) REFERENCES past_performance_contracts(contract_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 8. PROPOSAL REFERENCE TABLE (Link contracts to active proposals)
-- ============================================================================

CREATE TABLE IF NOT EXISTS proposal_past_performance_refs (
    ref_id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    proposal_id VARCHAR(100),
    rfq_number VARCHAR(100),
    rfq_title VARCHAR(500),
    contract_id BIGINT UNSIGNED NOT NULL,
    relevance_score DECIMAL(3,2),
    narrative_generated BOOLEAN DEFAULT FALSE,
    narrative_text TEXT,
    inclusion_reason VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_proposal_id (proposal_id),
    INDEX idx_rfq_number (rfq_number),
    INDEX idx_contract_id (contract_id),
    INDEX idx_relevance (relevance_score),
    FOREIGN KEY (contract_id) REFERENCES past_performance_contracts(contract_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. VIEWS FOR FAST RETRIEVAL (Query Optimization)
-- ============================================================================

-- Search contracts within 7-year window
CREATE OR REPLACE VIEW past_performance_7year AS
SELECT
    ppc.contract_id,
    ppc.contract_number,
    ppc.contract_title,
    ppc.customer_name,
    ppc.customer_type,
    ppc.vehicle_type,
    ppc.naics_code,
    ppc.psc_code,
    ppc.start_date,
    ppc.end_date,
    ppc.contract_value_usd,
    ppc.on_time_delivery_pct,
    ppc.quality_rating,
    ppc.re_award_pct,
    DATEDIFF(CURDATE(), ppc.end_date) AS days_since_completion,
    YEAR(ppc.end_date) AS completion_year
FROM past_performance_contracts ppc
WHERE ppc.record_status = 'active'
    AND ppc.deleted_at IS NULL
    AND ppc.end_date >= DATE_SUB(CURDATE(), INTERVAL 7 YEAR)
ORDER BY ppc.end_date DESC;

-- Search contracts within 10-year window
CREATE OR REPLACE VIEW past_performance_10year AS
SELECT
    ppc.contract_id,
    ppc.contract_number,
    ppc.contract_title,
    ppc.customer_name,
    ppc.customer_type,
    ppc.vehicle_type,
    ppc.naics_code,
    ppc.psc_code,
    ppc.start_date,
    ppc.end_date,
    ppc.contract_value_usd,
    ppc.on_time_delivery_pct,
    ppc.quality_rating,
    ppc.re_award_pct
FROM past_performance_contracts ppc
WHERE ppc.record_status = 'active'
    AND ppc.deleted_at IS NULL
    AND ppc.end_date >= DATE_SUB(CURDATE(), INTERVAL 10 YEAR)
ORDER BY ppc.end_date DESC;

-- Relevant contracts for proposal narrative generation
CREATE OR REPLACE VIEW proposal_narrative_ready AS
SELECT
    ppc.contract_id,
    ppc.contract_number,
    ppc.contract_title,
    ppc.customer_name,
    ppc.vehicle_type,
    ppc.naics_code,
    ppc.psc_code,
    ppc.contract_value_usd,
    ppc.on_time_delivery_pct,
    ppc.quality_rating,
    ppc.key_deliverables,
    ppc.outcomes_summary,
    ppc.challenges_overcome,
    ppc.start_date,
    ppc.end_date,
    COUNT(cd.deliverable_id) AS deliverable_count,
    GROUP_CONCAT(cd.deliverable_name SEPARATOR '; ') AS deliverables_list
FROM past_performance_contracts ppc
LEFT JOIN contract_deliverables cd ON ppc.contract_id = cd.contract_id
WHERE ppc.record_status = 'active'
    AND ppc.deleted_at IS NULL
    AND ppc.end_date >= DATE_SUB(CURDATE(), INTERVAL 7 YEAR)
GROUP BY ppc.contract_id
ORDER BY ppc.quality_rating DESC, ppc.re_award_pct DESC;

-- ============================================================================
-- 10. STORED PROCEDURES FOR COMMON OPERATIONS
-- ============================================================================

DELIMITER //

-- Procedure: Search contracts by agency and time window
CREATE PROCEDURE IF NOT EXISTS sp_search_past_performance(
    IN p_agency_name VARCHAR(255),
    IN p_naics_code VARCHAR(6),
    IN p_psc_code VARCHAR(4),
    IN p_vehicle_type VARCHAR(50),
    IN p_years_back INT
)
BEGIN
    SELECT
        ppc.contract_id,
        ppc.contract_number,
        ppc.contract_title,
        ppc.customer_name,
        ppc.customer_type,
        ppc.vehicle_type,
        ppc.naics_code,
        ppc.psc_code,
        ppc.start_date,
        ppc.end_date,
        ppc.contract_value_usd,
        ppc.on_time_delivery_pct,
        ppc.quality_rating,
        ppc.re_award_pct,
        c_poc.full_name AS poc_name,
        c_poc.email AS poc_email,
        c_poc.phone AS poc_phone,
        COUNT(cd.deliverable_id) AS deliverable_count
    FROM past_performance_contracts ppc
    LEFT JOIN contacts c_poc ON ppc.agency_poc_id = c_poc.contact_id
    LEFT JOIN contract_deliverables cd ON ppc.contract_id = cd.contract_id
    WHERE ppc.record_status = 'active'
        AND ppc.deleted_at IS NULL
        AND ppc.end_date >= DATE_SUB(CURDATE(), INTERVAL p_years_back YEAR)
        AND (p_agency_name IS NULL OR ppc.customer_name LIKE CONCAT('%', p_agency_name, '%'))
        AND (p_naics_code IS NULL OR ppc.naics_code = p_naics_code)
        AND (p_psc_code IS NULL OR ppc.psc_code = p_psc_code)
        AND (p_vehicle_type IS NULL OR ppc.vehicle_type = p_vehicle_type)
    GROUP BY ppc.contract_id
    ORDER BY ppc.end_date DESC;
END //

-- Procedure: Generate proposal narrative from past performance
CREATE PROCEDURE IF NOT EXISTS sp_generate_proposal_narrative(
    IN p_contract_id BIGINT UNSIGNED
)
BEGIN
    SELECT
        ppc.contract_number,
        ppc.contract_title,
        ppc.customer_name,
        ppc.start_date,
        ppc.end_date,
        ppc.contract_value_usd,
        ppc.on_time_delivery_pct,
        ppc.quality_rating,
        ppc.key_deliverables,
        ppc.outcomes_summary,
        ppc.challenges_overcome,
        GROUP_CONCAT(DISTINCT cd.deliverable_name SEPARATOR ', ') AS deliverables,
        GROUP_CONCAT(DISTINCT c.full_name SEPARATOR ', ') AS key_personnel,
        ppc.program_manager_name,
        ppc.agency_poc_name
    FROM past_performance_contracts ppc
    LEFT JOIN contract_deliverables cd ON ppc.contract_id = cd.contract_id
    LEFT JOIN contract_team_members ctm ON ppc.contract_id = ctm.contract_id
    LEFT JOIN contacts c ON ctm.contact_id = c.contact_id
    WHERE ppc.contract_id = p_contract_id
        AND ppc.record_status = 'active'
    GROUP BY ppc.contract_id;
END //

-- Procedure: Insert new past performance contract with audit trail
CREATE PROCEDURE IF NOT EXISTS sp_insert_past_performance(
    IN p_contract_number VARCHAR(50),
    IN p_contract_title VARCHAR(500),
    IN p_customer_name VARCHAR(255),
    IN p_customer_type VARCHAR(50),
    IN p_vehicle_type VARCHAR(50),
    IN p_naics_code VARCHAR(6),
    IN p_psc_code VARCHAR(4),
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_contract_value_usd DECIMAL(15,2),
    IN p_on_time_delivery_pct DECIMAL(5,2),
    IN p_quality_rating VARCHAR(50),
    IN p_created_by VARCHAR(100)
)
BEGIN
    INSERT INTO past_performance_contracts (
        contract_number, contract_title, customer_name, customer_type,
        vehicle_type, naics_code, psc_code, start_date, end_date,
        contract_value_usd, on_time_delivery_pct, quality_rating,
        created_by, record_status
    ) VALUES (
        p_contract_number, p_contract_title, p_customer_name, p_customer_type,
        p_vehicle_type, p_naics_code, p_psc_code, p_start_date, p_end_date,
        p_contract_value_usd, p_on_time_delivery_pct, p_quality_rating,
        p_created_by, 'active'
    );

    INSERT INTO past_performance_audit_log (
        contract_id, change_type, change_reason, changed_by
    ) VALUES (
        LAST_INSERT_ID(), 'INSERT', 'Initial contract record creation', p_created_by
    );
END //

DELIMITER ;

-- ============================================================================
-- 11. SAMPLE DATA INSERTS
-- ============================================================================

-- Insert sample past performance contracts
INSERT INTO past_performance_contracts (
    contract_number, contract_title, customer_name, customer_type,
    vehicle_type, naics_code, psc_code, start_date, end_date,
    contract_value_usd, on_time_delivery_pct, cost_variance_pct,
    quality_rating, re_award_pct, contract_status,
    program_manager_name, agency_poc_name, ordering_officer_name,
    key_deliverables, outcomes_summary, challenges_overcome,
    total_labor_hours, team_size_avg, created_by, record_status
) VALUES
(
    'DOD-2021-003451',
    'Defense Advanced Analytics Platform - Phase II',
    'Department of Defense',
    'Federal Agency',
    'IDIQ',
    '541512',
    'D301',
    '2021-03-15',
    '2023-09-30',
    2850000.00,
    98.5,
    -2.3,
    'Excellent',
    95.0,
    'Completed',
    'John Martinez',
    'Dr. Sarah Chen, PM',
    'Col. Robert Wilson',
    'Advanced analytics software, real-time dashboards, training documentation, integration guides',
    'Successfully delivered integrated defense analytics platform supporting real-time threat analysis. Exceeded performance targets by 15% while reducing operating costs by 8%. Platform adopted by 4 additional DoD commands.',
    'Successfully navigated classified information handling requirements; expedited security clearances for 12 team members within 90 days.',
    14500,
    22,
    'admin',
    'active'
),
(
    'GSA-2020-081923',
    'IT Infrastructure Modernization - GSA Multiple Award',
    'General Services Administration',
    'Federal Agency',
    'GSA Schedule',
    '541511',
    'D301',
    '2020-06-01',
    '2024-05-31',
    1250000.00,
    99.2,
    1.2,
    'Excellent',
    92.0,
    'Completed',
    'Michelle Johnson',
    'Thomas Bradford, Contracting Officer',
    'Margaret Stone',
    'Cloud infrastructure migration, security hardening, documentation, training programs',
    'Modernized GSA IT infrastructure for 12 regional offices. Achieved 40% improvement in system uptime and reduced support tickets by 35%.',
    'Coordinated with 8 government IT teams across multiple time zones; standardized 47 disparate systems.',
    9200,
    18,
    'admin',
    'active'
),
(
    'DOT-2022-0012847',
    'Transportation Data Integration System',
    'Department of Transportation',
    'Federal Agency',
    'FFP',
    '541513',
    'D304',
    '2022-01-10',
    '2024-12-31',
    895000.00,
    96.8,
    3.5,
    'Very Good',
    88.0,
    'In Progress',
    'David Lee',
    'Karen Wilson, Director ITS',
    'James Patterson',
    'Data integration platform, API suite, real-time monitoring dashboard',
    'Built unified data integration system for 15+ transportation agencies. Improved data accessibility and reduced query response time from 45 min to <5 sec.',
    'Addressed legacy system compatibility with custom ETL adapters for 1970s-era mainframe data sources.',
    8100,
    15,
    'admin',
    'active'
),
(
    'VA-2019-556234',
    'Veterans Benefits System Enhancement',
    'Department of Veterans Affairs',
    'Federal Agency',
    'T&M',
    '541511',
    'D301',
    '2019-11-01',
    '2023-10-31',
    1650000.00,
    97.5,
    -1.8,
    'Excellent',
    100.0,
    'Completed',
    'Patricia Garcia',
    'Dr. James Morton, Chief IT',
    'Susan Gomez',
    'Benefits processing modules, mobile app, secure data encryption, staff training',
    'Enhanced VA benefits processing system serving 9M+ veterans. Reduced application processing time by 62% and improved veteran satisfaction scores by 28%.',
    'HIPAA compliance requirements; managed sensitive veteran personal health information; zero security incidents.',
    12300,
    24,
    'admin',
    'active'
),
(
    'EPA-2023-00987',
    'Environmental Monitoring Network Modernization',
    'Environmental Protection Agency',
    'Federal Agency',
    'IDIQ',
    '541380',
    'D399',
    '2023-06-01',
    '2025-05-31',
    725000.00,
    98.0,
    0.5,
    'Excellent',
    NULL,
    'In Progress',
    'Robert Thompson',
    'Linda Foster, Program Manager',
    'George Harris',
    'Sensor network upgrade, cloud data repository, analytics software, field deployment',
    'Upgraded environmental sensor network across 12 regions with real-time data analytics. Enabled predictive environmental modeling.',
    'Worked in sensitive environmental locations; coordinated with EPA field teams and tribal authorities.',
    5600,
    12,
    'admin',
    'active'
);

-- Insert sample contacts (POCs, Program Managers, etc.)
INSERT INTO contacts (
    first_name, last_name, full_name, title, email, phone, mobile,
    organization_name, organization_type, city, state_province, country,
    created_by, record_status
) VALUES
('John', 'Martinez', 'John Martinez', 'Program Manager', 'john.martinez@contractor.gov', '202-555-0101', '571-555-0102', 'Advanced Defense Systems LLC', 'Contractor', 'Arlington', 'VA', 'US', 'admin', 'active'),
('Sarah', 'Chen', 'Dr. Sarah Chen', 'Defense PM', 's.chen@dod.mil', '703-555-0103', NULL, 'Department of Defense', 'Federal Agency', 'Pentagon', 'VA', 'US', 'admin', 'active'),
('Robert', 'Wilson', 'Col. Robert Wilson', 'Contracting Officer', 'r.wilson@dod.mil', '703-555-0104', NULL, 'Department of Defense', 'Federal Agency', 'Pentagon', 'VA', 'US', 'admin', 'active'),
('Michelle', 'Johnson', 'Michelle Johnson', 'Program Director', 'michelle.j@ourcompany.com', '202-555-0105', '703-555-0106', 'Integrated Solutions Corp', 'Contractor', 'Washington', 'DC', 'US', 'admin', 'active'),
('Thomas', 'Bradford', 'Thomas Bradford', 'Contracting Officer', 'thomas.bradford@gsa.gov', '202-555-0107', NULL, 'General Services Administration', 'Federal Agency', 'Washington', 'DC', 'US', 'admin', 'active');

-- Insert sample deliverables
INSERT INTO contract_deliverables (
    contract_id, deliverable_name, deliverable_type, description,
    delivery_date, status, document_type, created_by
) VALUES
(1, 'Phase II Final Report', 'Technical Report', 'Comprehensive final report detailing analytics platform capabilities and integration results', '2023-09-30', 'Accepted', 'PDF', 'admin'),
(1, 'Source Code & Documentation', 'Code Repository', 'Complete source code repository with technical documentation and deployment guides', '2023-09-15', 'Accepted', 'GitHub', 'admin'),
(1, 'User Training Package', 'Training Materials', 'Video training modules and user guides for 4 DoD commands', '2023-08-30', 'Accepted', 'Video/PDF', 'admin'),
(2, 'Infrastructure Assessment Report', 'Assessment', 'Detailed IT infrastructure modernization assessment', '2020-08-15', 'Accepted', 'PDF', 'admin'),
(2, 'Cloud Migration Plan', 'Implementation Plan', 'Phased cloud migration strategy for 12 GSA regional offices', '2020-09-30', 'Accepted', 'PDF', 'admin'),
(3, 'System Integration Specification', 'Specification', 'Detailed technical specifications for DOT data integration', '2022-03-01', 'Accepted', 'PDF', 'admin');

-- Insert sample performance metrics
INSERT INTO performance_metrics (
    contract_id, metric_category, metric_name, metric_value, metric_unit,
    reporting_period_start, reporting_period_end, created_by
) VALUES
(1, 'Schedule Performance', 'On-Time Delivery Rate', 98.50, 'percent', '2021-03-15', '2023-09-30', 'admin'),
(1, 'Cost Performance', 'Cost Variance', -2.30, 'percent', '2021-03-15', '2023-09-30', 'admin'),
(1, 'Quality Metrics', 'Defect Rate', 0.05, 'percent', '2021-03-15', '2023-09-30', 'admin'),
(2, 'Schedule Performance', 'On-Time Delivery Rate', 99.20, 'percent', '2020-06-01', '2024-05-31', 'admin'),
(2, 'Customer Satisfaction', 'Customer Satisfaction Score', 9.2, 'out of 10', '2024-04-01', '2024-05-31', 'admin'),
(3, 'Technical Performance', 'System Uptime', 99.85, 'percent', '2022-01-10', '2024-12-31', 'admin');

-- Insert sample team members
INSERT INTO contract_team_members (
    contract_id, member_name, member_role, member_company, is_subcontractor,
    responsibility_description, labor_hours, start_date, end_date, created_by
) VALUES
(1, 'Dr. Michael Santos', 'Lead Architect', 'Advanced Defense Systems LLC', FALSE, 'Overall platform architecture and technical strategy', 2100, '2021-03-15', '2023-09-30', 'admin'),
(1, 'Jennifer Wu', 'Security Lead', 'Advanced Defense Systems LLC', FALSE, 'Information security and DoD compliance', 1850, '2021-03-15', '2023-09-30', 'admin'),
(1, 'Analytics Specialists (8)', 'Analytics Engineers', 'Advanced Defense Systems LLC', FALSE, 'Analytics engine development and optimization', 8400, '2021-04-01', '2023-09-30', 'admin'),
(2, 'Cloud Infrastructure Team', 'Infrastructure Engineers', 'Integrated Solutions Corp', FALSE, 'AWS/GCP cloud infrastructure deployment', 4200, '2020-06-01', '2024-05-31', 'admin'),
(2, 'Legacy Systems Group', 'Systems Integration', 'TechBridge Partners', TRUE, 'Legacy system integration and data migration', 2800, '2020-08-01', '2024-02-28', 'admin');

-- ============================================================================
-- 12. SAMPLE QUERIES FOR PROPOSAL DEADLINE SCENARIOS
-- ============================================================================

-- Query 1: Find all DOD contracts in past 7 years (typical search)
-- Execution time: <100ms
SELECT
    contract_number,
    contract_title,
    customer_name,
    vehicle_type,
    naics_code,
    start_date,
    end_date,
    contract_value_usd,
    on_time_delivery_pct,
    quality_rating,
    re_award_pct
FROM past_performance_7year
WHERE customer_name LIKE '%Defense%'
ORDER BY end_date DESC;

-- Query 2: Find all contracts matching multiple criteria (Proposal search)
-- Execution time: <150ms
SELECT
    contract_id,
    contract_number,
    contract_title,
    customer_name,
    vehicle_type,
    contract_value_usd,
    on_time_delivery_pct,
    quality_rating
FROM past_performance_contracts
WHERE record_status = 'active'
    AND deleted_at IS NULL
    AND naics_code IN ('541511', '541512', '541513')
    AND end_date >= DATE_SUB(CURDATE(), INTERVAL 7 YEAR)
    AND quality_rating IN ('Excellent', 'Very Good')
    AND on_time_delivery_pct >= 95.0
ORDER BY contract_value_usd DESC
LIMIT 10;

-- Query 3: Export narrative-ready data for proposal section
-- Execution time: <100ms
SELECT
    contract_number,
    contract_title,
    customer_name,
    start_date,
    end_date,
    contract_value_usd,
    on_time_delivery_pct,
    quality_rating,
    key_deliverables,
    outcomes_summary,
    challenges_overcome
FROM proposal_narrative_ready
WHERE naics_code = '541512'
LIMIT 5;

-- ============================================================================
-- USAGE GUIDE FOR PROPOSAL DEADLINE SCENARIOS
-- ============================================================================
/*

FAST SEARCH WORKFLOW (RFQ Released Monday, Due Friday):

1. IDENTIFY RELEVANT NAICS/PSC CODES (30 minutes)
   -- From RFQ, extract NAICS and PSC classifications

2. SEARCH PAST PERFORMANCE (5 minutes)
   CALL sp_search_past_performance(
       'Department of Defense',    -- Agency name
       '541512',                    -- NAICS code
       'D301',                      -- PSC code
       'IDIQ',                      -- Vehicle type
       7                            -- Years back
   );

3. EXTRACT NARRATIVE DATA (10 minutes)
   CALL sp_generate_proposal_narrative(1);  -- For each relevant contract

4. GENERATE PROPOSAL SECTION (2-3 hours)
   Use narrative data to draft 1-2 paragraph summary per contract
   Include: customer, vehicle type, value, performance metrics, outcomes
   Format as "Under contract DOD-2021-003451 with DoD..."

5. ADD EVIDENCE LINKS
   SELECT performance_report_url, award_letter_url, customer_reference_url
   FROM past_performance_contracts WHERE contract_id = X;

PERFORMANCE TARGETS FOR FEDERAL PROPOSALS:
- On-Time Delivery: 95%+ (critical)
- Quality Rating: Excellent/Very Good (preferred)
- Re-award Rate: 90%+ (demonstrates customer satisfaction)
- Cost Variance: -5% to +5% (shows cost control)

DATABASE OPTIMIZATION NOTES:
- Indexes on customer_name, naics_code, psc_code, vehicle_type, dates
- Views pre-filter active records and time windows
- Stored procedures hide complexity, reduce network round-trips
- Audit log captures all changes for compliance verification
- Document URLs enable rapid narrative citation

*/

-- ============================================================================
-- ADDITIONAL OPTIMIZATION: Add these indexes if table already populated
-- ============================================================================

-- CREATE INDEX idx_ppc_search_compound ON past_performance_contracts
--    (record_status, deleted_at, end_date, naics_code, vehicle_type);

-- CREATE INDEX idx_ppc_narrative ON past_performance_contracts
--    (record_status, deleted_at, quality_rating, on_time_delivery_pct);

-- CREATE INDEX idx_audit_trail ON past_performance_audit_log
--    (contract_id, changed_at DESC);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
