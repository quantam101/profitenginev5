# Federal Contract Pricing & Wrap-Rate Schema
## DCAA-Compliant Labor Rate Management & Federal Bidding

---

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Core Data Models](#core-data-models)
3. [Rate Calculation Examples](#rate-calculation-examples)
4. [DCAA Compliance Framework](#dcaa-compliance-framework)
5. [Contract Type Variations](#contract-type-variations)
6. [Volume Pricing Strategy](#volume-pricing-strategy)
7. [Audit Trail & Justification](#audit-trail--justification)
8. [SF 1411 Cost Analysis Export](#sf-1411-cost-analysis-export)
9. [Queries & Reports](#queries--reports)
10. [Implementation Checklist](#implementation-checklist)

---

## Schema Overview

This schema implements a **three-tier federal contracting pricing model**:

### Tier 1: Labor Categories & Base Rates
- Classify labor by GSA schedule, CLIN, custom, or SOW
- Track skill level, experience requirements, industry segment
- Support all contract types (FFP, T&M, IDIQ, GSA Schedule)

### Tier 2: Burden & Overhead Allocation
- FICA, insurance, pension, training, facilities, admin
- Overhead & G&A rates per contract type
- Indirect cost rates (DCAA-approved, provisional, negotiated)

### Tier 3: Billable Rate & Profit Margin
- Loaded cost = Direct Labor + Burdens
- Billable Rate = Loaded Cost × (1 + OH% + G&A% + Profit%)
- Volume discounts for IDIQ (>$1M, >$5M, >$10M)
- Profit margin validation (0–30% max)

---

## Core Data Models

### 1. labor_categories
Defines job classifications for federal contracts.

| Field | Type | Purpose |
|-------|------|---------|
| category_code | VARCHAR(50) | Unique identifier (e.g., 'DEV-SR', 'PM-001') |
| category_name | VARCHAR(255) | Human-readable name |
| category_type | VARCHAR(50) | GSA_SCHEDULE, CLIN, CUSTOM, SOW |
| skill_level | VARCHAR(50) | Entry, Intermediate, Senior, Expert |
| min_experience_years | INT | Minimum experience requirement |
| industry_segment | VARCHAR(100) | IT, Engineering, Management, Admin |

**Example:**
```
INSERT INTO labor_categories (category_code, category_name, category_type, skill_level, min_experience_years)
VALUES ('DEV-SR', 'Senior Software Developer', 'CLIN', 'Senior', 8);
```

### 2. labor_rates
Hourly or per-unit rates tied to labor categories and fiscal years.

| Field | Type | Purpose |
|-------|------|---------|
| base_rate_usd | NUMERIC(10,2) | Base labor rate (no overhead/profit) |
| direct_labor_cost_usd | NUMERIC(10,2) | Labor cost w/o overhead |
| billable_rate_usd | NUMERIC(10,2) | **What customer pays (per hour)** |
| loaded_cost_usd | NUMERIC(10,2) | Direct Labor + Burdens |
| profit_margin_percent | NUMERIC(5,2) | Margin as % (0–30%) |
| profit_margin_usd | Generated | Billable Rate - Loaded Cost |
| rate_status | VARCHAR(50) | PROVISIONAL, APPROVED, NEGOTIATED, LOCKED |
| effective_date | DATE | Rate effective from this date |

**Key Constraint:** `billable_rate_usd >= loaded_cost_usd` (always enforced by trigger)

### 3. burden_rates
Recurring costs per employee: FICA, insurance, pension, training, facilities.

| Field | Type | Purpose |
|-------|------|---------|
| burden_type | VARCHAR(100) | FICA, HEALTH_INSURANCE, PENSION, TRAINING, FACILITIES, ADMIN |
| rate_percent | NUMERIC(5,2) | % of labor cost (e.g., 7.65 for FICA) |
| allocation_method | VARCHAR(50) | %_OF_LABOR, %_OF_COST, PER_HOUR, FIXED |
| dcaa_compliant | BOOLEAN | Whether DCAA accepts this burden type |

**Typical Burden Stack (FY 2026):**
- FICA: 7.65%
- Health Insurance: 15.50%
- Pension: 8.00%
- Training: 2.50%
- Facilities: 12.00%
- Admin: 5.00%
- **Total Burden: ~50.65%**

### 4. overhead_ga_rates
Overhead (OH) and General & Administrative (G&A) allocations by contract type.

| Field | Type | Purpose |
|-------|------|---------|
| overhead_percent | NUMERIC(5,2) | OH as % of direct labor (typically 55–75%) |
| gna_percent | NUMERIC(5,2) | G&A as % of direct labor (typically 10–15%) |
| profit_percent | NUMERIC(5,2) | Target profit margin (typically 8–12%) |
| contract_type | VARCHAR(50) | FFP, T&M, IDIQ, GSA_SCHEDULE (NULL = all types) |
| dcaa_rate_approval_date | DATE | When DCAA approved these rates |
| provisional_rate | BOOLEAN | TRUE = pending DCAA negotiation |

**Example: FFP Rates (DCAA Approved)**
```
overhead_percent = 65%
gna_percent = 12%
profit_percent = 10%
dcaa_rate_approval_date = 2025-10-15
```

### 5. volume_pricing_tiers
Discounts for large IDIQ contracts.

| Field | Type | Purpose |
|-------|------|---------|
| min_contract_value_usd | NUMERIC(15,2) | Minimum contract value for tier |
| max_contract_value_usd | NUMERIC(15,2) | Maximum contract value (NULL = unlimited) |
| discount_percent | NUMERIC(5,2) | % reduction in billable rate |
| contract_type | VARCHAR(50) | Applied only to FFP, T&M, IDIQ, etc. |

**Example: IDIQ Pricing (FY 2026)**
| Min | Max | Discount |
|-----|-----|----------|
| $0 | $999,999 | 0% |
| $1M | $4,999,999 | 2.5% |
| $5M | $9,999,999 | 5.0% |
| $10M+ | N/A | 7.5% |

### 6. contract_rate_agreements
Master contract record with rate locks and compliance status.

| Field | Type | Purpose |
|-------|------|---------|
| contract_id | VARCHAR(100) | Unique contract identifier |
| contract_number | VARCHAR(50) | CAGE code, GSA#, contract#, etc. |
| contract_type | VARCHAR(50) | FFP, T&M, IDIQ, GSA_SCHEDULE |
| rate_lock_date | DATE | When rates became locked (FFP only) |
| rate_lock_status | VARCHAR(50) | PROPOSED, AGREED, LOCKED |
| contract_ceiling_usd | NUMERIC(15,2) | Contract not-to-exceed amount |
| target_profit_percent | NUMERIC(5,2) | Desired profit margin for bid |
| dcaa_compliant | BOOLEAN | Whether contract passes DCAA audit |

### 7. contract_rate_line_items
Individual labor category rates for a specific contract.

| Field | Type | Purpose |
|-------|------|---------|
| contract_rate_agreement_id | INT | FK to contract_rate_agreements |
| labor_category_id | INT | FK to labor_categories |
| labor_rate_id | INT | FK to labor_rates (can differ from standard) |
| negotiated_rate_usd | NUMERIC(10,2) | Rate for THIS contract (may differ from standard) |
| negotiated_billable_rate_usd | NUMERIC(10,2) | Billable rate for this contract |
| rate_justification | TEXT | Why this rate was negotiated |
| approved_by | VARCHAR(100) | Who approved this rate |
| approval_date | DATE | When approved |

**Example:**
```
contract_number = N6500123456789 (DOD)
labor_category = DEV-SR (Senior Developer)
negotiated_rate_usd = 95.00
negotiated_billable_rate_usd = 215.00
```

### 8. rate_audit_trail
Complete change history for compliance & DCAA audit.

| Field | Type | Purpose |
|-------|------|---------|
| entity_type | VARCHAR(50) | LABOR_RATE, OVERHEAD_GA, INDIRECT_COST, VOLUME_PRICING |
| event_type | VARCHAR(50) | CREATED, UPDATED, APPROVED, QUESTIONED, AMENDED |
| previous_value | NUMERIC(10,2) | Old rate value |
| new_value | NUMERIC(10,2) | New rate value |
| reason_for_change | TEXT | Why was this changed? |
| dcaa_audit_flag | BOOLEAN | Flagged during audit? |
| changed_by | VARCHAR(100) | Who made the change |
| changed_at | TIMESTAMP | When changed |

**Auto-populated by triggers after rate updates.**

---

## Rate Calculation Examples

### Scenario: Senior Developer (FY 2026, FFP Contract)

**Step 1: Direct Labor Cost**
```
Base Rate (no overhead): $95.00/hour
Direct Labor Cost = $95.00
```

**Step 2: Add Burdens → Loaded Cost**
```
Burden Stack (Total: 50.65%)
  - FICA:             7.65%
  - Health Insurance: 15.50%
  - Pension:          8.00%
  - Training:         2.50%
  - Facilities:       12.00%
  - Admin:            5.00%
  Total Burden:       50.65%

Loaded Cost = $95.00 × (1 + 0.5065) = $95.00 × 1.5065 = $143.12/hour
```

**Step 3: Add Overhead & G&A → Pre-Profit Rate**
```
OH & G&A (Total: 77%)
  - Overhead:  65%
  - G&A:       12%
  Total:       77%

Pre-Profit Rate = $143.12 × (1 + 0.77) = $143.12 × 1.77 = $253.32/hour
```

**Step 4: Add Profit → Billable Rate**
```
Target Profit: 10%

Billable Rate = $253.32 × (1 + 0.10) = $253.32 × 1.10 = $278.65/hour
```

**Step 5: Calculate Profit Margin**
```
Profit Margin USD = Billable Rate - Loaded Cost
                  = $278.65 - $143.12
                  = $135.53/hour

Profit Margin % = ($135.53 / $143.12) × 100 = 94.7% markup
                ≈ 48.6% margin on loaded cost
```

### Using SQL Functions

```sql
-- Calculate loaded cost with burdens
SELECT calculate_loaded_cost(95.00, 2026);
-- Returns: 143.12

-- Calculate billable rate
SELECT calculate_billable_rate(143.12, 'FFP', 2026);
-- Returns: 278.65

-- Apply volume discount (IDIQ, $2.5M contract value)
SELECT apply_volume_discount(278.65, 'IDIQ', 2500000, 2026);
-- Returns: 271.23 (2.5% discount)

-- Calculate profit margin
SELECT calculate_profit_margin_usd(278.65, 143.12);
-- Returns: 135.53
```

---

## DCAA Compliance Framework

### DCAA Indirect Cost Rate Certificate

The schema tracks three types of indirect cost rates per DCAA regulations (FAR 42.704):

| Rate Type | Status | Description |
|-----------|--------|-------------|
| APPROVED | Final | Negotiated & accepted by DCAA (used in proposals) |
| NEGOTIATED | Provisional | Recently negotiated, awaiting final approval |
| PROVISIONAL | Tentative | Company estimate pending DCAA audit |
| TENTATIVE | Initial | First submission to DCAA |

### Required Audit Trail for DCAA

The `rate_audit_trail` table captures all changes:

**Event Log Example:**
```
Date        | Event      | Item       | Old Value | New Value | Reason
2026-01-15  | CREATED    | DEV-SR     | NULL      | 95.00     | FY 2026 rate initialization
2026-03-20  | QUESTIONED | DEV-SR     | 95.00     | 95.00     | DCAA audit: ✓ approved (no change)
2026-06-01  | AMENDED    | OVERHEAD   | 65%       | 68%       | COLA adjustment + facilities increase
2026-06-02  | APPROVED   | OVERHEAD   | 68%       | 68%       | Finance Director approval
```

### DCAA Compliance Checklist (Query)

```sql
SELECT * FROM dcaa_compliance_checklist;

-- Output:
-- ┌──────────────────────────┬──────────────┬───────────────┬─────────────┬──────────────┐
-- │ check_item               │ total_rates  │ approved_count│ locked_count│ pending_count│
-- ├──────────────────────────┼──────────────┼───────────────┼─────────────┼──────────────┤
-- │ Labor Rates Approved     │ 6            │ 6             │ 2           │ 0            │
-- │ Overhead & G&A Approved  │ 3            │ 2             │ 0           │ 1            │
-- │ Indirect Cost Approved   │ 2            │ 1             │ 0           │ 1            │
-- └──────────────────────────┴──────────────┴───────────────┴─────────────┴──────────────┘
```

### Provisioning Indirect Cost Rates

```sql
INSERT INTO indirect_cost_rates
    (fiscal_year, rate_type, rate_value, allocation_base, dcaa_rate_id,
     effective_date, includes_overhead, includes_gna, includes_profit,
     rate_justification, created_by)
VALUES
    (2026, 'PROVISIONAL', 1.77, 'DIRECT_LABOR', 'DCAA-2026-001-PROV',
     '2026-01-01'::DATE, TRUE, TRUE, FALSE,
     'Provisional rate pending DCAA negotiation (OH 65% + G&A 12%)',
     'SYSTEM');
```

---

## Contract Type Variations

### 1. Fixed Price (FFP) — Rates Locked at Proposal

**Characteristics:**
- Rates locked on `rate_lock_date` (cannot change)
- Status: `rate_lock_status = 'LOCKED'`
- If cost exceeds estimate, company absorbs loss
- Profit margin typically 8–12%

**Rate Setting:**
```sql
INSERT INTO contract_rate_agreements
    (contract_id, contract_number, contract_name, customer_name, fiscal_year,
     contract_type, rate_lock_date, rate_lock_status, contract_ceiling_usd,
     target_profit_percent, dcaa_compliant, created_by)
VALUES
    ('DOD-2026-001', 'N6500123456789', 'Integrated IT Solutions', 'U.S. DoD',
     2026, 'FFP', '2026-01-15'::DATE, 'LOCKED', 5000000.00, 10.00, TRUE, 'SYSTEM');
```

**Verification Query:**
```sql
SELECT * FROM ffp_rate_lock_verification
WHERE contract_number = 'N6500123456789';
```

### 2. Time & Materials (T&M) — Rates Variable

**Characteristics:**
- Rates adjust annually (COLA applies)
- `rate_lock_status = 'PROPOSED'` (not locked)
- Profit margin typically 4–8% (lower risk)
- Overhead & G&A passed through to customer

**Rate Adjustment:**
```sql
UPDATE labor_rates
SET billable_rate_usd = billable_rate_usd * 1.03,  -- 3% COLA
    cola_percent = 3.00,
    adjustment_reason = 'FY 2027 COLA adjustment (3%)',
    updated_at = CURRENT_TIMESTAMP
WHERE fiscal_year = 2027 AND contract_type = 'T&M'
  AND is_active = TRUE;

-- Log change
INSERT INTO rate_audit_trail (entity_type, entity_id, event_type, reason_for_change, changed_by, changed_at)
SELECT 'LABOR_RATE', labor_rate_id, 'UPDATED', 'FY 2027 COLA (3%)', 'SYSTEM', CURRENT_TIMESTAMP
FROM labor_rates WHERE fiscal_year = 2027 AND contract_type = 'T&M';
```

### 3. IDIQ (Indefinite Delivery/Indefinite Quantity) — Volume Discounts

**Characteristics:**
- Base contract with task orders issued as needed
- Volume discounts kick in at >$1M, $5M, $10M
- Profit margin 6–10% (depends on volume tier)

**Volume Discount Calculation:**
```sql
-- Contract value: $2.5M
SELECT apply_volume_discount(278.65, 'IDIQ', 2500000, 2026);
-- Result: 271.23 (2.5% discount applied)

-- Contract value: $7M
SELECT apply_volume_discount(278.65, 'IDIQ', 7000000, 2026);
-- Result: 264.72 (5% discount applied)
```

### 4. GSA Schedule — Pre-Set Rates

**Characteristics:**
- Rates published on GSA schedule (publicly visible)
- 1–3% volume discount only
- Profit margin 8% (locked by GSA contract)
- Annual update allowed

**GSA Rate Setup:**
```sql
INSERT INTO labor_rates
    (labor_category_id, fiscal_year, contract_type, base_rate_usd, direct_labor_cost_usd,
     billable_rate_usd, loaded_cost_usd, profit_margin_percent, effective_date,
     rate_status, rate_justification, created_by)
VALUES
    (1, 2026, 'GSA_SCHEDULE', 95.00, 95.00, 185.00, 143.12, 8.00, '2026-01-01'::DATE,
     'APPROVED', 'GSA Schedule 2026 approved rate (Item #2025-0001)', 'SYSTEM');
```

---

## Volume Pricing Strategy

### Discount Tiers (IDIQ)

```sql
SELECT * FROM volume_pricing_tiers
WHERE contract_type = 'IDIQ' AND fiscal_year = 2026
ORDER BY min_contract_value_usd;

-- Output:
-- ┌────────┬──────────────────┬──────────────────┬─────────────┐
-- │ Min    │ Max              │ Discount %       │ Description │
-- ├────────┼──────────────────┼──────────────────┼─────────────┤
-- │ $0     │ $999,999         │ 0%               │ Base        │
-- │ $1M    │ $4,999,999       │ 2.5%             │ $1M–$5M     │
-- │ $5M    │ $9,999,999       │ 5.0%             │ $5M–$10M    │
-- │ $10M   │ NULL (no max)    │ 7.5%             │ $10M+       │
-- └────────┴──────────────────┴──────────────────┴─────────────┘
```

### Annual Savings Analysis

```sql
SELECT * FROM volume_discount_impact
WHERE contract_type = 'IDIQ'
ORDER BY base_rate DESC;

-- Output:
-- ┌──────────┬────────────────────┬──────────┬──────────┬──────────────┐
-- │ Category │ Base Rate          │ Discount │ Disc.Amt │ Annual Saving│
-- ├──────────┼────────────────────┼──────────┼──────────┼──────────────┤
-- │ DEV-SR   │ $278.65            │ 5.0%     │ $13.93   │ $27,860      │
-- │ DEV-JR   │ $156.00            │ 5.0%     │ $7.80    │ $15,600      │
-- │ QA-001   │ $165.00            │ 5.0%     │ $8.25    │ $16,500      │
-- └──────────┴────────────────────┴──────────┴──────────┴──────────────┘
```

---

## Audit Trail & Justification

### Recording Rate Changes

```sql
-- When a rate is updated, triggers auto-log to rate_audit_trail
UPDATE labor_rates
SET billable_rate_usd = 290.00,
    adjustment_reason = 'Market rate adjustment - Senior Developer shortage',
    created_by = 'john.smith@company.com'
WHERE labor_rate_id = 1
  AND fiscal_year = 2026;

-- Verify change was logged:
SELECT * FROM rate_audit_trail
WHERE entity_id = 1 AND entity_type = 'LABOR_RATE'
ORDER BY changed_at DESC;
```

### Rate Justification Report

```sql
SELECT * FROM rate_justification_report
WHERE fiscal_year = 2026 AND contract_type = 'FFP'
ORDER BY category_code;

-- Output:
-- ┌──────────┬──────────────────┬───────┬──────────┬──────────┬──────────────┐
-- │ Category │ Name             │ Level │ Base     │ Billable │ Profit%      │
-- ├──────────┼──────────────────┼───────┼──────────┼──────────┼──────────────┤
-- │ DEV-JR   │ Junior Dev       │ Entry │ $50.00   │ $110.00  │ 7.0%         │
-- │ DEV-SR   │ Senior Dev       │ Senior│ $95.00   │ $278.65  │ 10.0%        │
-- │ PM-001   │ Program Manager  │ Senior│ $110.00  │ $320.00  │ 10.5%        │
-- └──────────┴──────────────────┴───────┴──────────┴──────────┴──────────────┘
```

### DCAA Audit Review Points

When DCAA audits, they check:

1. **Reasonable Relationship** — Are burden rates within industry norms?
2. **Allocable Costs** — Are all costs traceable to contracts?
3. **Allowable Costs** — Do rates comply with FAR 31.2 (allowable cost principles)?
4. **Segregation** — Is unallowable cost (entertainment, etc.) excluded?
5. **Documentation** — Can you prove the rate with timesheets, vendor invoices, etc.?

**Query to prepare for DCAA audit:**
```sql
SELECT entity_type, event_type, changed_by, changed_at, reason_for_change
FROM rate_audit_trail
WHERE fiscal_year = 2026 AND dcaa_audit_flag IS NOT TRUE
ORDER BY changed_at ASC;
-- Produces: Complete change log for DCAA review
```

---

## SF 1411 Cost Analysis Export

The **Standard Form 1411** (Cost Justification) is required for federal proposals >$100K.

### Export Query

```sql
SELECT * FROM sf_1411_export_data
WHERE contract_number = 'N6500123456789';

-- Output (per labor category):
-- ┌─────────────┬────────────┬──────────┬───────────┬──────────┬──────────┐
-- │ Category    │ Direct Lab │ Fringes  │ Overhead  │ G&A      │ Total    │
-- ├─────────────┼────────────┼──────────┼───────────┼──────────┼──────────┤
-- │ Senior Dev  │ $95.00     │ $48.11   │ $61.75    │ $11.40   │ $216.26  │
-- │ Junior Dev  │ $50.00     │ $25.33   │ $32.50    │ $6.00    │ $113.83  │
-- │ PM          │ $110.00    │ $55.72   │ $71.50    │ $13.20   │ $250.42  │
-- └─────────────┴────────────┴──────────┴───────────┴──────────┴──────────┘
```

### Exporting to PDF/Excel

```sql
INSERT INTO cost_analysis_export_history
    (contract_id, export_type, export_format, export_filename, export_path,
     exported_by, authorized_signatory, signature_date, is_official_submission)
VALUES
    ('DOD-2026-001', 'SF_1411', 'PDF', 'DOD_2026_001_SF_1411_SIGNED.pdf',
     '/exports/2026/DOD_2026_001_SF_1411_SIGNED.pdf',
     'john.smith@company.com', 'Jane Doe, CFO', '2026-01-10'::DATE, TRUE);
```

---

## Queries & Reports

### 1. Competitive Rate Summary (Materialized View)

**Purpose:** Quick snapshot of all current rates for competitive bidding.

```sql
REFRESH MATERIALIZED VIEW competitive_rate_summary;

SELECT category_code, category_name, contract_type, billable_rate_usd,
       profit_margin_usd, rate_status
FROM competitive_rate_summary
WHERE fiscal_year = 2026
ORDER BY contract_type, billable_rate_usd DESC;
```

### 2. FFP Rate Lock Verification

**Purpose:** Verify all FFP contract rates are locked and justified.

```sql
SELECT * FROM ffp_rate_lock_verification
WHERE rate_lock_status != 'LOCKED'
-- Alert: Any PROPOSED or AGREED rates need lock before award
```

### 3. DCAA Compliance Checklist

**Purpose:** Monthly compliance status report.

```sql
SELECT * FROM dcaa_compliance_checklist;
-- Confirms: # of approved rates, # pending, # locked
```

### 4. Volume Discount Impact

**Purpose:** Estimate savings from IDIQ volume tiers.

```sql
SELECT * FROM volume_discount_impact
WHERE contract_type = 'IDIQ'
ORDER BY discount_percent DESC;
-- Shows: Annual savings per category per discount tier
```

---

## Implementation Checklist

### Phase 1: Schema Setup
- [ ] Create all tables (labor_categories, labor_rates, burden_rates, etc.)
- [ ] Create indexes for performance
- [ ] Create materialized view (competitive_rate_summary)
- [ ] Create triggers (compliance check, audit logging)
- [ ] Create functions (calculate_loaded_cost, calculate_billable_rate, etc.)

### Phase 2: Initial Data Load
- [ ] Insert labor categories (GSA Schedule + CLIN-aligned)
- [ ] Insert burden rates (FICA, insurance, pension, etc.)
- [ ] Insert overhead & G&A rates by contract type
- [ ] Insert volume pricing tiers for IDIQ
- [ ] Insert sample indirect cost rates (approved + provisional)

### Phase 3: Contract Setup
- [ ] Create contract_rate_agreement for each active contract
- [ ] Create contract_rate_line_items (rates for each labor category)
- [ ] Lock rates for FFP contracts on `rate_lock_date`
- [ ] Export SF 1411 forms for proposals >$100K

### Phase 4: Compliance & Audits
- [ ] Set up audit trail logging (auto via triggers)
- [ ] Document rate justifications in rate_audit_trail
- [ ] Generate monthly DCAA compliance reports
- [ ] Conduct quarterly rate review (cost increases, market changes)

### Phase 5: Ongoing Operations
- [ ] Monitor profit margins (stay 0–30% range)
- [ ] Track COLA adjustments (T&M contracts)
- [ ] Apply volume discounts for large IDIQ orders
- [ ] Export cost analysis templates as needed
- [ ] Refresh materialized view weekly

---

## Sample SQL Inserts

### Insert FY 2026 Labor Rates

```sql
-- Senior Developer
INSERT INTO labor_rates (labor_category_id, fiscal_year, contract_type, 
    base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
    profit_margin_percent, effective_date, rate_status, rate_justification, created_by)
SELECT 1, 2026, 'FFP', 95.00, 95.00, 278.65, 143.12, 10.00, '2026-01-01', 
    'APPROVED', 'FY 2026 standard rate (DCAA-compliant)', 'SYSTEM';

-- Junior Developer
INSERT INTO labor_rates (labor_category_id, fiscal_year, contract_type, 
    base_rate_usd, direct_labor_cost_usd, billable_rate_usd, loaded_cost_usd,
    profit_margin_percent, effective_date, rate_status, rate_justification, created_by)
SELECT 2, 2026, 'FFP', 50.00, 50.00, 110.00, 75.33, 7.00, '2026-01-01',
    'APPROVED', 'FY 2026 standard rate (entry-level)', 'SYSTEM';
```

### Insert DCAA-Approved Overhead & G&A

```sql
INSERT INTO overhead_ga_rates 
    (fiscal_year, overhead_percent, gna_percent, profit_percent, 
     overhead_allocation_method, gna_allocation_method,
     dcaa_rate_approval_date, provisional_rate, description, created_by)
VALUES (2026, 65.00, 12.00, 10.00, '%_OF_LABOR', '%_OF_LABOR',
    '2025-10-15'::DATE, FALSE,
    'Standard FFP rates - DCAA approved 2025-10-15 (CertIF# 2025-1234)', 'SYSTEM');
```

### Insert Volume Pricing Tiers

```sql
INSERT INTO volume_pricing_tiers 
    (fiscal_year, contract_type, min_contract_value_usd, max_contract_value_usd,
     discount_percent, description, created_by)
VALUES 
    (2026, 'IDIQ', 0, 999999.99, 0, 'Base rate (no volume discount)', 'SYSTEM'),
    (2026, 'IDIQ', 1000000, 4999999.99, 2.5, 'Volume discount: $1M–$5M', 'SYSTEM'),
    (2026, 'IDIQ', 5000000, 9999999.99, 5.0, 'Volume discount: $5M–$10M', 'SYSTEM'),
    (2026, 'IDIQ', 10000000, NULL, 7.5, 'Volume discount: $10M+', 'SYSTEM');
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **FFP** | Fixed Price — rates locked at proposal award |
| **T&M** | Time & Materials — rates variable, adjusted annually |
| **IDIQ** | Indefinite Delivery/Indefinite Quantity — master contract with task orders |
| **CLIN** | Contract Line Item Number — individual line item in proposal |
| **Burden** | Recurring employee costs (FICA, insurance, pension) |
| **Overhead** | Indirect costs allocated to contracts (facilities, utilities, admin) |
| **G&A** | General & Administrative — company-wide overhead (legal, HR, exec) |
| **Loaded Cost** | Direct labor + burdens (what it actually costs to employ someone) |
| **Billable Rate** | What customer pays (loaded cost + overhead + G&A + profit) |
| **Profit Margin** | Billable rate minus loaded cost (typically 0–30%) |
| **DCAA** | Defense Contract Audit Agency — audits federal contractor costs |
| **COLA** | Cost of Living Adjustment — annual rate increase (typically 2–5%) |
| **GSA Schedule** | General Services Administration — pre-negotiated federal rates |
| **SF 1411** | Standard Form 1411 — Cost Justification form (required for large proposals) |

---

## References

- FAR (Federal Acquisition Regulation) Part 31 — Allowable Costs
- FAR Part 42.704 — Indirect Cost Rate Certificate
- DCAA Contract Audit Manual (CAM)
- GSA Schedule Ordering Guide
- SF 1411 Form Instructions

---

**Schema Version:** 1.0 | **Last Updated:** 2026-06-28 | **Author:** Federal Pricing Team
