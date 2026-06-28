# Proposal Templates & Customization Guide

## Standard Template Structure

The AH-POS proposal generator creates 80% complete federal proposals with automatic population from:
- **Past Performance** — 3-5 best matching contracts (NAICS-matched, recent)
- **Labor Categories** — GSA schedule rates with 2026 COLA
- **Cost Analysis** — SF 1411 compliant pricing (labor + burden + overhead + G&A + profit)
- **Agency Statistics** — Performance trends (on-time %, quality ratings)

## Generated Content (80%)

✅ Executive Summary  
✅ Company Qualifications & Relevant Experience (3-5 case studies)  
✅ Pricing & Cost Analysis (SF 1411 format)  
✅ CPARS Ratings & Past Performance Summary  
✅ Compliance & Certifications  
✅ Automated estimates of labor hours, rates, totals  

## Manual Completion Required (20%)

⚠️ Technical Approach — Detailed methodology, timeline, implementation plan  
⚠️ Key Personnel — Resumes, clearances, role assignments  
⚠️ Subcontractor Management — Flow-down requirements, qualifications  
⚠️ Risk Mitigation — Contingency planning, risk management  
⚠️ References — 3-5 customer references for similar work  
⚠️ Proposal Cover Letter — Executive summary and unique value proposition  
⚠️ Appendices — Resumes, certifications, supporting documentation  

**Estimated Manual Completion Time:** 4-8 hours (depending on proposal complexity)

---

## Usage Examples

### Generate HTML Draft
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.proposal_generator import ProposalGenerator

engine = create_engine("postgresql://user:pass@host/ah_pos")
Session = sessionmaker(bind=engine)
session = Session()

generator = ProposalGenerator(session)
result = generator.generate(opportunity_id=12345, output_format="html")

# View in browser
print(result['content'])  # Raw HTML
```

### Generate PDF
```python
result = generator.generate(
    opportunity_id=12345,
    output_format="pdf",
    output_path=Path("./proposal_draft.pdf")
)
# Output: {"format": "pdf", "path": "./proposal_draft.pdf", "size_bytes": 245872}
```

### Generate DOCX (Microsoft Word)
```python
result = generator.generate(
    opportunity_id=12345,
    output_format="docx",
    output_path=Path("./proposal_draft.docx")
)
# Can edit directly in Microsoft Word, Google Docs, etc.
```

### Generate Plaintext
```python
result = generator.generate(
    opportunity_id=12345,
    output_format="txt"
)
print(result['content'])  # Clean text, no HTML tags
```

---

## Customization

### Override Executive Summary
```python
generator.executive_summary = """
We are pleased to propose [custom text]. Our company brings [custom details].
"""
```

### Adjust Labor Hours Estimation
```python
# Default: 2,000 hours (1 FTE-year)
# Adjust in _generate_cost_analysis() based on proposal scope
total_labor_hours = 3000  # Modify this value
```

### Modify Cost Burden Rates
```python
# Default rates:
burden_rate = 0.25       # 25% (FICA, benefits)
overhead_rate = 0.50     # 50% (facilities, admin)
ga_rate = 0.10           # 10% (general & administrative)
profit_rate = 0.12       # 12% (profit margin)

# Adjust in _generate_cost_analysis() to match your company's rates
```

### Include Subcontractor Information
```python
# Add to template:
{% for subcontractor in subcontractors %}
  <h3>Subcontractor: {{ subcontractor.name }}</h3>
  <p>{{ subcontractor.qualifications }}</p>
{% endfor %}
```

### Limit Past Performance to Specific Agencies
```python
# In _find_past_performance(), filter by agency:
contracts = self.session.query(PastPerformanceContract).filter(
    PastPerformanceContract.agency_name == "Department of Defense",
    PastPerformanceContract.naics_code.in_(opportunity.naics_codes)
).limit(5).all()
```

---

## Export Quality Notes

### HTML
- Browser-viewable, print-to-PDF capable
- **Best for:** Quick review, internal circulation
- **File size:** 50-150 KB

### PDF (requires `weasyprint`)
- Professional formatting, embedded fonts
- **Best for:** Final submission, archive
- **File size:** 200-500 KB
- **Setup:** `pip install weasyprint`

### DOCX (requires `python-docx`)
- Microsoft Word editable
- **Best for:** Customer-specific customization
- **File size:** 100-300 KB
- **Setup:** `pip install python-docx`

### Plaintext
- No special dependencies
- **Best for:** Email circulation, accessibility
- **File size:** 20-50 KB

---

## Quality Checklist Before Submission

### Auto-Generated (Verified ✓)
- [x] Past performance contracts matched to NAICS codes
- [x] Labor categories populated from GSA schedule
- [x] Cost analysis (SF 1411 format) calculated
- [x] CPARS ratings included
- [x] Agency performance statistics aggregated
- [x] 80% completion status clearly marked

### Manual Review Required
- [ ] Executive summary captures unique value
- [ ] Case studies align with solicitation requirements
- [ ] Technical approach is realistic and detailed
- [ ] Labor hour estimates match proposal scope
- [ ] Cost rates reflect current GSA/DCAA rates
- [ ] Key personnel qualifications are strong
- [ ] Risk mitigation strategies are credible
- [ ] References are recent and relevant
- [ ] No placeholder text remaining
- [ ] Formatting is consistent and professional
- [ ] All appendices included
- [ ] Signatures obtained

---

## Next Steps (Phase 3: Web Dashboard)

**Future Enhancement:** Web UI for:
- Proposal generation workflow (wizard)
- Real-time preview (HTML → PDF)
- Team collaboration (comments, edits, approvals)
- Version control & audit trail
- Template customization (drag-drop)
- Direct submission to SAM.gov (future)

---

## Support & Troubleshooting

### "ModuleNotFoundError: No module named 'weasyprint'"
```bash
pip install weasyprint
# Or use HTML output instead (no PDF export needed)
```

### "PDF export failed: font error"
```bash
# Install system fonts
# macOS: brew install freetype
# Linux: sudo apt-get install libfreetype6
# Windows: Fonts are built-in
```

### "Generated proposal is too long"
Adjust the following in proposal_generator.py:
```python
# Reduce past performance contracts shown:
.limit(3)  # Instead of 5

# Reduce labor categories shown:
.limit(3)  # Instead of 5
```

### "Cost analysis numbers seem wrong"
Verify labor rates in database:
```sql
SELECT * FROM labor_categories WHERE loaded_rate_2026 IS NOT NULL;
```

---

**Proposal Generator Version:** 1.0  
**Status:** Production Ready  
**Dependencies:** SQLAlchemy, Jinja2, optional (weasyprint, python-docx)
