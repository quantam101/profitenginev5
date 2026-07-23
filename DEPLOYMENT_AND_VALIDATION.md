# Federal Past Performance Database — Deployment & Validation Guide

---

## Pre-Deployment Checklist

### Database Environment Preparation

- [ ] MySQL Server 5.7+ (or MariaDB 10.2+) installed
- [ ] Database user created with appropriate permissions
- [ ] Disk space available: minimum 500MB initially
- [ ] Backup system configured for nightly incremental + weekly full
- [ ] Network connectivity verified to database server

### Security Pre-Deployment

- [ ] Database running over SSL/TLS in production
- [ ] User roles created (proposal_writer, data_mgr, auditor, admin)
- [ ] Row-level security policies defined (if required)
- [ ] IP whitelist configured for database access
- [ ] Audit logging enabled at OS/DB level

### Performance Pre-Deployment

- [ ] Query cache enabled (if MySQL 5.7)
- [ ] InnoDB buffer pool sized to 50-75% of available RAM
- [ ] Max connections configured appropriately
- [ ] Slow query log enabled (>500ms threshold)

---

## Deployment Steps

### Step 1: Create Database Schema

```bash
# Connect to MySQL as admin
mysql -h your-host.com -u admin -p

# Run schema creation
USE mysql;
SOURCE federal_past_performance_schema.sql;

# Verify tables created
USE federal_past_performance;
SHOW TABLES;
```

**Expected Output** (12 tables):
```
+---------------------------------+
| Tables_in_federal_past_performance |
+---------------------------------+
| contacts                        |
| contract_deliverables           |
| contract_team_members           |
| contract_vehicles               |
| customer_types                  |
| federal_agencies                |
| naics_codes                     |
| past_performance_audit_log      |
| past_performance_contracts      |
| performance_metrics             |
| proposal_past_performance_refs   |
| psc_codes                       |
+---------------------------------+
12 rows in set (0.00 sec)
```

### Step 2: Verify Views

```sql
USE federal_past_performance;
SHOW FULL TABLES WHERE TABLE_TYPE LIKE 'VIEW';
```

**Expected Output** (3 views):
```
+-----------------------------+------------+
| Tables_in_federal_past_performance | Table_type |
+-----------------------------+------------+
| past_performance_10year     | VIEW       |
| past_performance_7year      | VIEW       |
| proposal_narrative_ready    | VIEW       |
+---------------------------------+--------+
```

### Step 3: Verify Stored Procedures

```sql
SHOW PROCEDURE STATUS WHERE DB='federal_past_performance';
```

**Expected Output** (3 procedures):
```
+------------------------------------+---------------------------+
| Db | Name                           | Type      |
+------------------------------------+---------------------------+
| federal_past_performance | sp_generate_proposal_narrative | PROCEDURE |
| federal_past_performance | sp_insert_past_performance    | PROCEDURE |
| federal_past_performance | sp_search_past_performance    | PROCEDURE |
+------------------------------------+---------------------------+
```

### Step 4: Create Database Users

```sql
-- Proposal Writer Role (SELECT only)
CREATE USER 'proposal_writer'@'%' IDENTIFIED BY 'secure_password_here';
GRANT SELECT ON federal_past_performance.* TO 'proposal_writer'@'%';

-- Data Manager Role (SELECT, INSERT, UPDATE)
CREATE USER 'data_mgr'@'%' IDENTIFIED BY 'secure_password_here';
GRANT SELECT, INSERT, UPDATE ON federal_past_performance.* TO 'data_mgr'@'%';
GRANT SELECT ON federal_past_performance.past_performance_audit_log TO 'data_mgr'@'%';

-- Auditor Role (SELECT audit_log only)
CREATE USER 'auditor'@'%' IDENTIFIED BY 'secure_password_here';
GRANT SELECT ON federal_past_performance.past_performance_audit_log TO 'auditor'@'%';

-- Refresh privileges
FLUSH PRIVILEGES;
```

### Step 5: Verify Indexes

```sql
-- Check all indexes created
SELECT 
   TABLE_NAME, 
   INDEX_NAME, 
   COLUMN_NAME, 
   SEQ_IN_INDEX
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'federal_past_performance'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
```

**Expected Output**: 30+ indexes across tables

### Step 6: Test Example Data

Verify the 5 example contracts loaded:

```sql
SELECT COUNT(*) AS total_contracts FROM past_performance_contracts;
```

**Expected Output**: `5`

```sql
SELECT 
   contract_number, 
   contract_title, 
   customer_name 
FROM past_performance_contracts 
ORDER BY contract_value_usd DESC;
```

**Expected Output**:
```
+------------------+--------------------------------------------------+------------------------------+
| contract_number  | contract_title                                   | customer_name                |
+------------------+--------------------------------------------------+------------------------------+
| DOD-2021-003451  | Defense Advanced Analytics Platform - Phase II   | Department of Defense        |
| VA-2019-556234   | Veterans Benefits System Enhancement             | Department of Veterans Affairs |
| GSA-2020-081923  | IT Infrastructure Modernization - GSA Multiple   | General Services Admin       |
| DOT-2022-0012847 | Transportation Data Integration System           | Department of Transportation |
| EPA-2023-00987   | Environmental Monitoring Network Modernization   | Environmental Protection Agency |
+------------------+--------------------------------------------------+------------------------------+
```

---

## Post-Deployment Validation

### Test 1: Search Stored Procedure

```sql
CALL sp_search_past_performance(NULL, '541512', NULL, NULL, 7);
```

**Expected**: Returns 2 contracts (DoD and DOT with NAICS 541512)

### Test 2: Narrative Generation

```sql
CALL sp_generate_proposal_narrative(1);
```

**Expected**: Returns detailed narrative data for contract ID 1 (DoD)

### Test 3: View Query Performance

```sql
SELECT SQL_CALC_FOUND_ROWS * 
FROM past_performance_7year 
WHERE quality_rating = 'Excellent' 
LIMIT 10;

SELECT FOUND_ROWS();
```

**Expected**: Completes in <100ms, returns 4 records

### Test 4: Verify Audit Trail

```sql
SELECT COUNT(*) FROM past_performance_audit_log;
```

**Expected**: 5 audit records (one INSERT per sample contract)

```sql
SELECT 
   contract_id, 
   change_type, 
   changed_by, 
   changed_at 
FROM past_performance_audit_log 
ORDER BY changed_at DESC;
```

**Expected Output**:
```
+-------------+-------------+------------+---------------------+
| contract_id | change_type | changed_by | changed_at          |
+-------------+-------------+------------+---------------------+
|           5 | INSERT      | admin      | 2024-xx-xx xx:xx:xx |
|           4 | INSERT      | admin      | 2024-xx-xx xx:xx:xx |
|           3 | INSERT      | admin      | 2024-xx-xx xx:xx:xx |
|           2 | INSERT      | admin      | 2024-xx-xx xx:xx:xx |
|           1 | INSERT      | admin      | 2024-xx-xx xx:xx:xx |
+-------------+-------------+------------+---------------------+
```

### Test 5: Verify Foreign Key Constraints

```sql
-- This should work (valid customer type)
INSERT INTO past_performance_contracts (
   contract_number, contract_title, customer_name, customer_type,
   vehicle_type, naics_code, psc_code, start_date, end_date,
   contract_value_usd, on_time_delivery_pct, quality_rating,
   created_by, record_status
) VALUES (
   'TEST-2024-001234', 'Test Contract', 'Test Agency', 'Federal Agency',
   'IDIQ', '541512', 'D301', '2024-01-01', '2025-01-01',
   500000.00, 95.0, 'Good',
   'test_user', 'active'
);

-- This should FAIL (invalid customer type)
INSERT INTO past_performance_contracts (
   contract_number, contract_title, customer_name, customer_type,
   vehicle_type, naics_code, psc_code, start_date, end_date,
   contract_value_usd, on_time_delivery_pct, quality_rating,
   created_by, record_status
) VALUES (
   'TEST-2024-005678', 'Test Contract 2', 'Test Agency', 'Invalid Type',
   'IDIQ', '541512', 'D301', '2024-01-01', '2025-01-01',
   500000.00, 95.0, 'Good',
   'test_user', 'active'
);
-- ERROR: Foreign key constraint fails
```

### Test 6: Performance Baseline

Run these queries and record execution times:

```sql
-- Query 1: Simple agency search
SELECT * FROM past_performance_7year 
WHERE customer_name LIKE '%Defense%';
-- Target: <50ms

-- Query 2: Multi-criteria search
SELECT * FROM past_performance_contracts
WHERE quality_rating = 'Excellent'
AND vehicle_type = 'IDIQ'
AND end_date >= DATE_SUB(CURDATE(), INTERVAL 7 YEAR);
-- Target: <100ms

-- Query 3: Narrative export
SELECT * FROM proposal_narrative_ready
WHERE naics_code = '541512';
-- Target: <100ms
```

---

## Migration from Legacy System

### If You Have Existing Past Performance Data

**Step 1: Export from legacy system to CSV**

Required fields:
```csv
contract_number,contract_title,customer_name,customer_type,vehicle_type,
naics_code,psc_code,start_date,end_date,contract_value_usd,
on_time_delivery_pct,cost_variance_pct,quality_rating,re_award_pct,
program_manager_name,agency_poc_name,ordering_officer_name,
key_deliverables,outcomes_summary,challenges_overcome
```

**Step 2: Validate data**

```bash
# Check for required fields
awk -F',' '{
   if ($1 == "" || $3 == "" || $8 == "" || $9 == "") 
      print "Missing required field on line", NR
}' past_performance_import.csv

# Count rows
wc -l past_performance_import.csv
```

**Step 3: Import to MySQL**

```sql
LOAD DATA LOCAL INFILE '/tmp/past_performance_import.csv'
INTO TABLE past_performance_contracts
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(contract_number, contract_title, customer_name, customer_type, vehicle_type,
 naics_code, psc_code, start_date, end_date, contract_value_usd,
 on_time_delivery_pct, cost_variance_pct, quality_rating, re_award_pct,
 program_manager_name, agency_poc_name, ordering_officer_name,
 key_deliverables, outcomes_summary, challenges_overcome)
SET created_by = 'data_migration', created_at = NOW();
```

**Step 4: Verify import counts**

```sql
-- Count imported contracts
SELECT COUNT(*) FROM past_performance_contracts 
WHERE created_by = 'data_migration';

-- Spot-check sample record
SELECT * FROM past_performance_contracts 
WHERE created_by = 'data_migration' 
LIMIT 1\G
```

**Step 5: Audit trail for migration**

```sql
INSERT INTO past_performance_audit_log 
(contract_id, change_type, change_reason, changed_by)
SELECT contract_id, 'IMPORT', 'Migrated from legacy system', 'migration_admin'
FROM past_performance_contracts 
WHERE created_by = 'data_migration';
```

---

## Backup & Disaster Recovery

### Daily Incremental Backup Script

```bash
#!/bin/bash
# File: /opt/backups/daily_backup.sh

BACKUP_DIR="/backups/federal_past_performance"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="federal_past_performance"
DB_USER="backup_user"
DB_PASSWORD="[SECURE_PASSWORD]"

# Create daily directory
mkdir -p $BACKUP_DIR/$DATE

# Backup schema
mysqldump -h localhost -u $DB_USER -p$DB_PASSWORD \
   --no-data $DB_NAME \
   > $BACKUP_DIR/$DATE/schema.sql

# Backup data (incremental — last 24 hours only)
mysqldump -h localhost -u $DB_USER -p$DB_PASSWORD \
   --where="updated_at > DATE_SUB(NOW(), INTERVAL 1 DAY)" \
   $DB_NAME \
   > $BACKUP_DIR/$DATE/incremental_data.sql

# Backup audit log (all changes last 24 hours)
mysqldump -h localhost -u $DB_USER -p$DB_PASSWORD \
   --tables $DB_NAME past_performance_audit_log \
   --where="changed_at > DATE_SUB(NOW(), INTERVAL 1 DAY)" \
   > $BACKUP_DIR/$DATE/audit_log.sql

# Compress
gzip $BACKUP_DIR/$DATE/*.sql

# Upload to S3 (optional)
aws s3 sync $BACKUP_DIR/$DATE s3://backups-federal-contracts/$DB_NAME/$DATE

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -mtime +30 -delete

echo "Backup completed: $DATE" >> /var/log/backup.log
```

### Weekly Full Backup Script

```bash
#!/bin/bash
# File: /opt/backups/weekly_backup.sh

BACKUP_DIR="/backups/federal_past_performance"
DATE=$(date +%Y%m%d)
DB_NAME="federal_past_performance"
DB_USER="backup_user"
DB_PASSWORD="[SECURE_PASSWORD]"

# Full backup
mysqldump -h localhost -u $DB_USER -p$DB_PASSWORD \
   --all-databases --single-transaction \
   > $BACKUP_DIR/full_backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/full_backup_$DATE.sql

# Verify backup integrity
mysql -h localhost -u $DB_USER -p$DB_PASSWORD \
   < $BACKUP_DIR/full_backup_$DATE.sql.gz > /dev/null 2>&1

if [ $? -eq 0 ]; then
   echo "Full backup verified: $DATE" >> /var/log/backup.log
   # Upload to S3
   aws s3 cp $BACKUP_DIR/full_backup_$DATE.sql.gz \
      s3://backups-federal-contracts/full/full_backup_$DATE.sql.gz
else
   echo "Backup verification FAILED: $DATE" >> /var/log/backup.log
fi
```

### Restore from Backup

```bash
# Restore from daily incremental
gunzip < /backups/federal_past_performance/20240115_143022/incremental_data.sql.gz | \
   mysql -h localhost -u admin -p federal_past_performance

# Restore from full backup
gunzip < /backups/federal_past_performance/full_backup_20240115.sql.gz | \
   mysql -h localhost -u admin -p

# Verify restored data
mysql -h localhost -u admin -p federal_past_performance -e \
   "SELECT COUNT(*) AS contract_count FROM past_performance_contracts;"
```

---

## Ongoing Maintenance

### Weekly Tasks

- [ ] Check slow query log for performance issues
- [ ] Verify backup completion in logs
- [ ] Review audit log for unauthorized changes
- [ ] Run integrity check: `ANALYZE TABLE past_performance_contracts;`

### Monthly Tasks

- [ ] Full backup integrity test (restore to test environment)
- [ ] Review index usage and disk space
- [ ] Update NAICS/PSC reference tables if new codes added
- [ ] Review user access logs

### Quarterly Tasks

- [ ] Archive old audit logs (>90 days) to archive DB
- [ ] Performance baseline comparison
- [ ] Security audit (user roles, permissions)
- [ ] Disaster recovery drill

### Annual Tasks

- [ ] Major version upgrade testing
- [ ] Capacity planning review
- [ ] Archive historical audit logs to cold storage

---

## Troubleshooting

### Problem: Slow Queries After Data Import

**Solution**:
```sql
-- Analyze tables
ANALYZE TABLE past_performance_contracts;
ANALYZE TABLE past_performance_audit_log;
ANALYZE TABLE contract_deliverables;

-- Check index statistics
SHOW INDEX FROM past_performance_contracts\G

-- Run OPTIMIZE (maintenance mode recommended)
OPTIMIZE TABLE past_performance_contracts;
```

### Problem: Disk Space Full

**Solution**:
```sql
-- Check table sizes
SELECT 
   TABLE_NAME,
   ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'federal_past_performance'
ORDER BY (data_length + index_length) DESC;

-- Archive old audit logs
INSERT INTO archive_db.past_performance_audit_log
SELECT * FROM federal_past_performance.past_performance_audit_log
WHERE changed_at < DATE_SUB(CURDATE(), INTERVAL 1 YEAR);

-- Delete archived records
DELETE FROM past_performance_audit_log
WHERE changed_at < DATE_SUB(CURDATE(), INTERVAL 1 YEAR);
```

### Problem: Connection Timeout in Proposal Tool

**Solution**:
```sql
-- Increase wait_timeout
SET GLOBAL wait_timeout = 28800;  -- 8 hours

-- Increase max_connections
SET GLOBAL max_connections = 500;

-- Check active connections
SHOW PROCESSLIST;
```

---

## Performance Monitoring

### Enable Performance Schema

```sql
-- Check if enabled
SHOW VARIABLES LIKE 'performance_schema';

-- If OFF, add to /etc/mysql/my.cnf and restart:
# [mysqld]
# performance_schema=ON
# performance_schema_max_table_instances=12500
```

### Monitor Query Performance

```sql
-- Top 10 slowest queries
SELECT 
   digest_text,
   COUNT_STAR,
   SUM_TIMER_WAIT,
   AVG_TIMER_WAIT
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10\G
```

---

## Compliance & Audit Reporting

### Generate FAR 42.15 Compliance Report

```sql
SELECT 
   DATE_FORMAT(NOW(), '%Y-%m-%d') AS report_date,
   COUNT(*) AS total_contracts,
   SUM(CASE WHEN quality_rating = 'Excellent' THEN 1 ELSE 0 END) AS excellent_count,
   AVG(on_time_delivery_pct) AS avg_on_time_pct,
   AVG(re_award_pct) AS avg_re_award_pct,
   COUNT(DISTINCT customer_name) AS unique_agencies,
   SUM(contract_value_usd) AS total_contract_value
FROM past_performance_contracts
WHERE record_status = 'active'
AND deleted_at IS NULL
AND end_date >= DATE_SUB(CURDATE(), INTERVAL 7 YEAR);
```

### Generate Audit Trail Report

```sql
SELECT 
   DATE(changed_at) AS change_date,
   change_type,
   COUNT(*) AS change_count,
   GROUP_CONCAT(DISTINCT changed_by) AS changed_by_users
FROM past_performance_audit_log
WHERE changed_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(changed_at), change_type
ORDER BY change_date DESC, change_count DESC;
```

---

## Success Criteria

Your deployment is complete when:

- [x] All 12 tables created successfully
- [x] All 3 views query without error
- [x] All 3 stored procedures callable
- [x] 5 sample contracts loaded
- [x] User roles created and verified
- [x] Search queries return results <100ms
- [x] Narrative generation tested end-to-end
- [x] Backup scripts running successfully
- [x] Proposal team trained on usage
- [x] First RFQ completed using database

---

**Deployment Complete!** Your Federal Past Performance Database is ready for high-velocity proposal development.

**Support Contact**: [Database Administrator Email]
