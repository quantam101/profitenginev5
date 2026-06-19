# Content Quality Gate System — Usage Guide

## Overview

The Content Quality Gate is a pre-publish validation system that ensures all articles meet ProfitEngine's editorial and compliance standards before distribution.

**7 Independent Validator Agents** run in parallel to assess:
1. **Technical Accuracy** — Free claims, setup steps accuracy
2. **Affiliate Relevance** — Link relevance, no stuffing
3. **Zero-Cost Compliance** — Free/unlimited claims qualified
4. **Offer Alignment** — Already Here LLC alignment
5. **Proof-of-Work Status** — Proof language, no "guaranteed"
6. **Security Quality** — Security for API/cloud content
7. **Content Structure** — Required sections present

## Scoring Thresholds

- **Minimum category score**: 7/10 (all categories must pass)
- **Minimum average score**: 8/10 (overall quality threshold)
- **Publication decision**: PUBLISH or HOLD_FOR_REVIEW

## Quick Start

### Standalone Validation

```bash
# Test the quality gate directly
python content_quality_gate.py

# You'll see:
# - Validation report with all 7 agents
# - JSON output for integration
# - Clear PASS/FAIL decision
```

### Integration with publish_article_resilient.py

The quality gate automatically runs as a pre-publish gate when enabled:

```bash
# Enable quality gate (default)
QUALITY_GATE_ENABLED=true QUALITY_GATE_VERBOSE=true python publish_article_resilient.py

# Disable quality gate (bypass validation)
QUALITY_GATE_ENABLED=false python publish_article_resilient.py

# Run with verbose reporting
QUALITY_GATE_VERBOSE=true python publish_article_resilient.py
```

## Validator Details

### 1. TechnicalAccuracyAgent

Validates technical claims and setup instructions.

**Checks:**
- No unqualified "free forever" or "unlimited free" claims
- Free claims are properly qualified ("free tier", "within limits")
- No generic filler phrases ("in today's digital world", "revolutionary")
- Setup steps are specific and actionable

**Scoring:** -2 per unqualified claim, -1 per generic filler

### 2. AffiliateRelevanceAgent

Ensures affiliate links are relevant and not oversold.

**Checks:**
- Link density not excessive (max 8 links recommended)
- No blocked affiliate patterns (VPN, Grammarly with Cloudflare article, etc.)
- Affiliate products not marked as "required" without qualification

**Scoring:** -3 for high link density, -2 per blocked pattern

### 3. ZeroCostComplianceAgent

Validates that free and zero-cost claims are truthful and qualified.

**Blocked phrases:**
- "free forever", "unlimited free", "no cost", "zero cost"
- "passive income", "guaranteed", "proven system"

**Required qualifications:**
- "free tier", "within limits", "no new spend", "testing", "being built"

**Scoring:** -1 per blocked phrase, -2 if free mentioned but not qualified

### 4. OfferAlignmentAgent

Ensures articles tie to specific Already Here LLC offers.

**Valid offers:**
- Prime/Sub Protection Pack
- Field Intake & Proof Pack
- Google Forms-to-Sheets Intake Setup
- Cloudflare Workers Edge Intake Worker
- Contractor Proof-to-Invoice Workflow
- AI Workflow Setup Service
- Field Tech Toolkit Guide
- CRM Follow-Up Workflow

**Checks:**
- Article mentions "Already Here" or specific offer
- Clear monetization angle (sell, service, offer, implementation)

**Scoring:** -3 for no mention, -2 for unclear offer mapping, -1 for weak monetization

### 5. ProofOfWorkAgent

Validates that language matches the actual development status.

**Blocked pre-proof language:**
- "proven system", "guaranteed to", "will increase"
- "fully automated", "passive income system", "results in"
- "100% effective", "zero effort"

**Allowed development-stage language:**
- "testing", "being built", "proof-of-work version"
- "in development", "client validation", "internal test"

**Scoring:** -2 per blocked phrase, -1 if proof status unclear

### 6. SecurityAgent

Checks security practices for sensitive content (API, cloud, automation, webhooks).

**Checks (if article is security-sensitive):**
- Security section present (environment variables, API keys, secrets)
- No hardcoded credentials
- Webhooks include request validation

**Scoring:** -3 for missing security section, -2 per security violation

### 7. ContentStructureAgent

Ensures all required sections are present.

**Required sections:**
- Reader problem
- Technical explanation
- Use case
- Already Here angle
- Zero-cost path
- Next step
- Affiliate disclosure

**Additional checks:**
- No article starts with generic filler
- Problem statement appears in opening

**Scoring:** -1 per missing section, -2 if opening is filler

## API Usage

### Python: Validate in Code

```python
from content_quality_gate import validate_before_publish, get_quality_gate_json

article = {
    "title": "My Article Title",
    "body": "Article content...",
    "target_buyer": "Small business owner",
    "primary_offer": "Edge Intake Worker"
}

# Get validation result
should_publish, validation = validate_before_publish(article, verbose=True)

if should_publish:
    print("Ready to publish!")
else:
    print("Issues found:")
    for change in validation.required_changes:
        print(f"  - {change}")

# Get JSON output
json_result = get_quality_gate_json(article)
print(json_result)
```

### JSON Output Format

```json
{
  "article_title": "Article Title",
  "publish_status": "publish",
  "quality_score": 9.6,
  "average_threshold": 8.0,
  "category_threshold": 7.0,
  "passes_all_categories": true,
  "category_scores": {
    "TechnicalAccuracyAgent": {
      "score": 10,
      "passed": true,
      "findings": []
    },
    "AffiliateRelevanceAgent": {
      "score": 10,
      "passed": true,
      "findings": []
    },
    "ZeroCostComplianceAgent": {
      "score": 10,
      "passed": true,
      "findings": []
    },
    "OfferAlignmentAgent": {
      "score": 8,
      "passed": true,
      "findings": ["Article does not map to specific offer"]
    },
    "ProofOfWorkAgent": {
      "score": 10,
      "passed": true,
      "findings": []
    },
    "SecurityAgent": {
      "score": 10,
      "passed": true,
      "findings": []
    },
    "ContentStructureAgent": {
      "score": 9,
      "passed": true,
      "findings": ["Missing section: use case"]
    }
  },
  "issues": [...],
  "required_changes": [
    "Tie to one of: Prime/Sub Protection Pack, ...",
    "Add 'use case' section to article"
  ],
  "final_notes": "Quality score: 9.6/10",
  "timestamp": "2026-06-19T11:32:02.321970"
}
```

## Integration Points

### publish_article_resilient.py

The quality gate is integrated as a **pre-publish gate**:

1. **After** article is generated
2. **Before** distribution to any platform
3. **Blocking** — article cannot be published without passing

**Flow:**
```
generate_article()
  ↓
validate_before_publish() ← QUALITY GATE HERE
  ↓
  ├─ PASS → distribute to all platforms
  └─ FAIL → exit with required changes
```

### Environment Variables

```bash
# Enable/disable quality gate (default: true)
QUALITY_GATE_ENABLED=true

# Show detailed validation report (default: true)
QUALITY_GATE_VERBOSE=true
```

### Exit Behavior

**On PASS:**
- Article proceeds to distribution
- Quality gate report saved to `publish_state`
- Distribution to all platforms begins

**On FAIL:**
- Article is NOT published
- Script exits with error message
- Required changes listed in output
- User must fix and re-run

## Example Validation Reports

### PASSING Article (9.6/10)

```
[VALIDATE] TechnicalAccuracyAgent: 10/10 - PASS
[VALIDATE] AffiliateRelevanceAgent: 10/10 - PASS
[VALIDATE] ZeroCostComplianceAgent: 10/10 - PASS
[VALIDATE] OfferAlignmentAgent: 8/10 - PASS
[VALIDATE] ProofOfWorkAgent: 10/10 - PASS
[VALIDATE] SecurityAgent: 10/10 - PASS
[VALIDATE] ContentStructureAgent: 9/10 - PASS

Status: PUBLISH
Quality Score: 9.6/10 (threshold: 8.0/10)
Required Changes: 2 (non-blocking, for quality improvement)
```

### FAILING Article (6.4/10)

```
[VALIDATE] TechnicalAccuracyAgent: 5/10 - FAIL
[VALIDATE] AffiliateRelevanceAgent: 7/10 - PASS
[VALIDATE] ZeroCostComplianceAgent: 6/10 - FAIL
[VALIDATE] OfferAlignmentAgent: 4/10 - FAIL
[VALIDATE] ProofOfWorkAgent: 8/10 - PASS
[VALIDATE] SecurityAgent: 9/10 - PASS
[VALIDATE] ContentStructureAgent: 6/10 - FAIL

Status: HOLD_FOR_REVIEW
Quality Score: 6.4/10 (threshold: 8.0/10)
Required Changes: 5 (BLOCKING - must fix before publish)
```

## Troubleshooting

### Article passes manually but fails gate

Check:
1. Affiliate link density (max 8 recommended)
2. Unqualified "free" claims
3. Missing required sections
4. Blocked phrases (e.g., "guaranteed", "proven system")

### Gate rejecting valid content

The validators are conservative by design. If an article is being over-penalized:
1. Check the specific findings in the report
2. Review the validator logic in `content_quality_gate.py`
3. Consider adjusting thresholds (currently 7/10 minimum per category)

### False positives on offer alignment

The OfferAlignmentAgent requires explicit mention of "Already Here" or a specific offer. To fix:
1. Add a dedicated "Already Here Angle" or "Service Offering" section
2. Mention one of the valid offers explicitly
3. Include clear implementation/service details

## Best Practices

### Before Publishing

1. **Run validation early** — catch issues before full generation
2. **Check JSON output** — programmatic errors are easier to fix
3. **Review required changes** — they're recommendations for quality improvement
4. **Verify offer alignment** — always tie to specific Already Here service

### Common Issues to Avoid

1. **Unqualified free claims** — "free forever" fails; "free tier within current limits" passes
2. **Affiliate stuffing** — too many links reduce relevance score
3. **No offer tie-in** — articles must connect to Already Here services
4. **Missing structure** — all 7 sections are required
5. **Generic language** — avoid marketing fluff, use specific examples

### After Publishing

1. **Monitor engagement** — which articles drive most conversions?
2. **Update patterns** — if certain articles fail validation, adjust content
3. **Iterate quickly** — validation takes ~1 second, refine in seconds
4. **Build validation into workflow** — make quality gate part of editorial process

## Advanced: Custom Thresholds

To modify scoring thresholds, edit `content_quality_gate.py`:

```python
# In QualityScore.passes_threshold property:
# Current: average >= 8.0 and all categories >= 7.0
# Custom: adjust to your standards
```

## API Reference

### `validate_before_publish(article, verbose=True)`

Validates article and returns decision.

**Parameters:**
- `article: Dict[str, Any]` — article with title, body, target_buyer, primary_offer
- `verbose: bool` — print full validation report (default: True)

**Returns:**
- `Tuple[bool, PublishValidation]` — (should_publish, validation_result)

### `get_quality_gate_json(article)`

Validates article and returns JSON-serializable result.

**Parameters:**
- `article: Dict[str, Any]` — article dict

**Returns:**
- `Dict[str, Any]` — JSON-compatible result with all scores and findings

### `ContentQualityGate.validate_article(article)`

Core validation pipeline.

**Parameters:**
- `article: Dict[str, Any]` — article dict

**Returns:**
- `PublishValidation` — complete validation with all agent results

## Support

For questions or issues:
1. Check the example validation output in this file
2. Review validator logic in `content_quality_gate.py`
3. Check environment variable configuration
4. Run with `QUALITY_GATE_VERBOSE=true` for detailed output
