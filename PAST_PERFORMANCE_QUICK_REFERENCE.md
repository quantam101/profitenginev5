# Past Performance Database — Quick Reference for Proposal Teams

## 60-Second Search (When RFQ Lands)

### Step 1: Copy the NAICS and PSC codes from RFQ
```
NAICS: 541512 (IT Systems Design)
PSC: D301 (ADP & Telecom)
```

### Step 2: Run this search
```sql
CALL sp_search_past_performance(
   NULL,              -- Leave blank for all agencies
   '541512',          -- Paste NAICS code
   'D301',            -- Paste PSC code
   NULL,              -- Leave blank for all vehicle types
   7                  -- Use 7 for typical RFQ (10 for extended)
);
```

### Step 3: Review Results
- Look for "Excellent" or "Very Good" quality ratings
- Prioritize contracts with >95% on-time delivery
- Note re-award percentages (higher = customer satisfaction)

---

## Generate Proposal Narrative (1-2 minute per contract)

### For each contract in search results:

```sql
CALL sp_generate_proposal_narrative(1);  -- Replace 1 with contract_id
```

### Copy this template and fill in:

```
[Company Name] has performed similar work under contract [contract_number] 
with [customer_name], a $[contract_value] [vehicle_type] from [start_date] 
through [end_date]. 

The project involved [key_deliverables]. We successfully [outcomes_summary] 
achieving [on_time_delivery_pct]% on-time delivery with a [quality_rating] 
performance rating. 

Key team members included [key_personnel]. 

Contact: [agency_poc_name], [agency_poc_email]
```

---

## Find All Contracts in Your Portfolio

### By Agency
```sql
SELECT * FROM past_performance_7year 
WHERE customer_name LIKE '%Department of Defense%'
ORDER BY end_date DESC;
```

### By Contract Type (Vehicle)
```sql
SELECT * FROM past_performance_7year 
WHERE vehicle_type = 'IDIQ'
ORDER BY contract_value_usd DESC;
```

### By NAICS Code
```sql
SELECT * FROM past_performance_7year 
WHERE naics_code = '541512'
ORDER BY quality_rating DESC;
```

### By Quality Rating
```sql
SELECT * FROM past_performance_7year 
WHERE quality_rating = 'Excellent'
ORDER BY re_award_pct DESC;
```

---

## Export Data for Proposal

### As comma-separated values (for Excel)
```sql
SELECT 
   contract_number,
   customer_name,
   vehicle_type,
   CONTRACT_VALUE_USD,
   on_time_delivery_pct,
   quality_rating,
   outcomes_summary
FROM proposal_narrative_ready
WHERE naics_code = '541512'
INTO OUTFILE '/tmp/past_performance_export.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

### As formatted text for narrative
```sql
SELECT 
   contract_number,
   CONCAT(customer_name, ' ($', FORMAT(contract_value_usd, 0), ')') AS contract_info,
   start_date,
   end_date,
   CONCAT(on_time_delivery_pct, '% on-time, ', quality_rating, ' rating') AS performance,
   key_deliverables,
   outcomes_summary
FROM proposal_narrative_ready
WHERE naics_code = '541512'
LIMIT 10;
```

---

## Checklist: Before Submitting Past Performance Section

- [ ] All contract numbers verified (cross-check against internal records)
- [ ] Customer names spelled correctly
- [ ] Dates accurate (start and end match contract documents)
- [ ] Performance metrics realistic (on-time % ≤100%, variance ±range)
- [ ] Quality ratings matched to narrative content
- [ ] Contact names and emails current
- [ ] Document links/references available and working
- [ ] No sensitive/classified information disclosed
- [ ] Past performance directly relevant to RFQ scope
- [ ] Enough contracts (3-5 typical; look for breadth not just volume)

---

## Common Questions

**Q: Can I search for contracts older than 10 years?**  
A: Not recommended. Federal RFQs typically value contracts from past 7 years (recent relevance). 10-year window is maximum suggested.

**Q: What if I don't know the NAICS/PSC codes?**  
A: Ask your capture manager or leave blank in the search — it will return ALL relevant contracts across codes.

**Q: How do I find the right agency POC contact?**  
A: Run the search procedure — it returns contact info (name, email, phone) in the results.

**Q: Can I modify past performance narrative?**  
A: Yes! The generated narrative is a template. Customize it with specific metrics, outcomes, and team details. Keep it factual.

**Q: What if we don't have a specific metric (e.g., re-award %)?**  
A: That's okay. Leave it blank in the database. The search/narrative procedures handle NULL values gracefully.

**Q: How often should I update this database?**  
A: After project completion or major milestone. Quarterly minimum to stay current for rapid RFQ responses.

---

## Database Connection Info

**Database Name**: `federal_past_performance`  
**Host**: [Your Database Host]  
**Port**: 3306 (default MySQL)  
**Username**: `proposal_writer` (read-only recommended)  

**Connection String (MySQL Workbench)**:
```
Host: [YOUR_HOST]
Port: 3306
Username: proposal_writer
Database: federal_past_performance
```

**Connection String (Python)**:
```python
import mysql.connector
conn = mysql.connector.connect(
    host="[YOUR_HOST]",
    user="proposal_writer",
    password="[PASSWORD]",
    database="federal_past_performance"
)
cursor = conn.cursor()
cursor.callproc('sp_search_past_performance', [None, '541512', 'D301', None, 7])
```

---

## Performance Metrics Glossary

| Metric | Target | Meaning |
|--------|--------|---------|
| **On-Time Delivery %** | 95%+ | Percent of deliverables delivered on or before scheduled date |
| **Cost Variance %** | -5% to +5% | Actual cost vs. budgeted cost (negative = under budget) |
| **Quality Rating** | Excellent | Customer satisfaction with quality of work/deliverables |
| **Re-Award %** | 90%+ | Percent of contract options exercised by customer |

---

## Emergency: Accessing Data Without Database

**If database is down**, contact [Database Administrator] with:
1. **What you need**: Agency name, NAICS code, PSC code
2. **Timeframe**: 7-year or 10-year window
3. **How urgently**: Proposal deadline date

**Backup search**: Check internal past performance spreadsheet in SharePoint  
**Fallback**: Historical proposal documents folder

---

## Getting Help

**Database Issues**: Contact [DBA Email]  
**Proposal Writing Help**: Contact [Capture Manager]  
**Data Accuracy Questions**: Contact [Contracts Team Lead]  
**NAICS/PSC Code Help**: Contact [Compliance Officer]

---

**Last Updated**: 2026  
**Version**: 1.0
