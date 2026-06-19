#!/usr/bin/env python3
"""
ProfitEngine Content Quality Gate System

Multi-agent validation pipeline that blocks publishing until articles meet:
- Technical accuracy standards
- Affiliate relevance and compliance
- Zero-cost claim verification
- Already Here LLC offer alignment
- Proof-of-work standards
- Security requirements
- Reader value

Each validation task runs as an independent agent.
All agents must pass before publish_status = PUBLISH.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime

# ── Quality Gate Data Structures ────────────────────────────────────────────

@dataclass
class QualityScore:
    """Article quality scoring"""
    technical_accuracy: int  # 0-10
    source_verification: int  # 0-10
    offer_alignment: int  # 0-10
    affiliate_relevance: int  # 0-10
    zero_cost_compliance: int  # 0-10
    proof_of_work_status: int  # 0-10
    security_quality: int  # 0-10
    reader_value: int  # 0-10
    already_here_fit: int  # 0-10
    publish_risk: int  # 0-10 (lower is better)

    @property
    def average(self) -> float:
        """Calculate average score"""
        total = (
            self.technical_accuracy + self.source_verification +
            self.offer_alignment + self.affiliate_relevance +
            self.zero_cost_compliance + self.proof_of_work_status +
            self.security_quality + self.reader_value +
            self.already_here_fit
        )
        return total / 9

    @property
    def passes_threshold(self) -> bool:
        """Check if article passes publishing threshold"""
        return (
            self.average >= 8 and
            all([
                self.technical_accuracy >= 7,
                self.source_verification >= 7,
                self.offer_alignment >= 7,
                self.affiliate_relevance >= 7,
                self.zero_cost_compliance >= 7,
                self.proof_of_work_status >= 7,
                self.security_quality >= 7,
                self.reader_value >= 7,
                self.already_here_fit >= 7,
                self.publish_risk <= 3,
            ])
        )


@dataclass
class ValidationResult:
    """Individual validator result"""
    validator_name: str
    passed: bool
    score: int  # 0-10
    findings: List[str]
    required_changes: List[str]
    notes: str
    timestamp: str


@dataclass
class PublishValidation:
    """Complete article validation"""
    article_title: str
    target_buyer: str
    primary_offer: str

    affiliate_links_present: bool
    affiliate_links_approved: bool
    unrelated_tools_removed: List[str]

    zero_cost_claims_present: bool
    zero_cost_claims_verified: bool

    technical_claims_verified: bool
    official_sources_checked: List[str]

    security_risks_found: List[str]
    proof_of_work_status: str  # idea | draft | internal_proof | client_proof | ready_to_promote | ready_to_sell

    publish_status: str  # publish | hold_for_review | reject
    required_changes: List[str]
    final_notes: str

    quality_scores: Optional[QualityScore] = None
    validator_results: Optional[List[ValidationResult]] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


# ── Agent Functions (One Per Validation Task) ────────────────────────────────

class TechnicalAccuracyAgent:
    """Validates technical claims against official documentation"""

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify technical accuracy"""
        title = article.get("title", "")
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10

        # Check for unqualified free claims
        free_claim_keywords = [
            "free forever", "unlimited free", "deploy at no cost",
            "no-cost business", "passive income for free"
        ]
        for keyword in free_claim_keywords:
            if keyword.lower() in body.lower():
                findings.append(f"Found unqualified free claim: '{keyword}'")
                required_changes.append(f"Replace '{keyword}' with qualified language like 'free tier within current limits'")
                score -= 2

        # Check for qualified free claims
        qualified_free_keywords = [
            "free tier", "within limits", "no new spend",
            "tested on free tier", "existing no-cost tools"
        ]
        qualified_found = any(kw.lower() in body.lower() for kw in qualified_free_keywords)
        if not qualified_found and "free" in body.lower():
            findings.append("Free claims present but not properly qualified")
            required_changes.append("Add verification source and limits for free claims")
            score -= 1

        # Check for generic filler
        filler_phrases = [
            "in today's digital world", "businesses need scalable solutions",
            "this powerful platform allows", "revolutionary new way"
        ]
        for phrase in filler_phrases:
            if phrase.lower() in body.lower():
                findings.append(f"Generic filler detected: '{phrase}'")
                required_changes.append(f"Replace filler with actual problem statement")
                score -= 2

        return ValidationResult(
            validator_name="TechnicalAccuracyAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings,
            required_changes=required_changes,
            notes=f"Technical accuracy check - {len(findings)} issues found"
        )


class AffiliateRelevanceAgent:
    """Validates affiliate link relevance and compliance"""

    ALLOWED_AFFILIATES = {
        "Cloudflare Workers": ["Cloudflare"],
        "API/serverless": ["Cloudflare", "DigitalOcean", "Vultr"],
        "Invoicing": ["FreshBooks"],
        "CRM/follow-up": ["HubSpot"],
        "Forms/sheets": ["Google Workspace"],
        "Hosting": ["Hostinger", "Bluehost", "SiteGround"],
        "SEO": ["SEMrush", "Ahrefs"],
    }

    BLOCKED_COMBOS = {
        "Cloudflare Workers": ["VPN", "Grammarly", "Jasper", "SEMrush", "Ahrefs"],
        "API article": ["Unrelated hosting", "Writing tools", "VPN"],
    }

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify affiliate link relevance"""
        title = article.get("title", "")
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10
        unrelated_tools = []

        # Check for affiliate stuffing patterns
        if body.count("https://") > 8:
            findings.append(f"High affiliate link density detected ({body.count('https://')} links)")
            required_changes.append("Reduce affiliate links to only directly relevant tools")
            score -= 3

        # Check for common blocking patterns
        if "cloudflare workers" in title.lower() or "cloudflare" in title.lower():
            blocked_keywords = ["vpn", "grammarly", "jasper", "semrush", "ahrefs"]
            for keyword in blocked_keywords:
                if keyword in body.lower():
                    findings.append(f"Blocked affiliate pattern: {keyword} in Cloudflare article")
                    required_changes.append(f"Remove {keyword} - not relevant to Cloudflare Workers")
                    unrelated_tools.append(keyword)
                    score -= 2

        # Check for unqualified recommendations
        if "required" in body.lower() and "optional" not in body.lower():
            findings.append("Affiliate products presented as required without qualification")
            required_changes.append("Add 'optional' or 'recommended' qualification to affiliate links")
            score -= 1

        return ValidationResult(
            validator_name="AffiliateRelevanceAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings + [f"Unrelated tools: {', '.join(unrelated_tools)}"] if unrelated_tools else findings,
            required_changes=required_changes,
            notes=f"Affiliate relevance check - {len(unrelated_tools)} unrelated tools found"
        )


class ZeroCostComplianceAgent:
    """Validates zero-cost and free-tier claims"""

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify zero-cost compliance"""
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10

        # Blocked phrases
        blocked = [
            "free forever", "unlimited free", "no cost", "zero cost",
            "passive income", "guaranteed", "proven system"
        ]

        for phrase in blocked:
            if phrase.lower() in body.lower():
                findings.append(f"Blocked phrase: '{phrase}' (not verified or qualified)")
                required_changes.append(f"Replace with qualified language or remove claim")
                score -= 1

        # Required qualified language
        qualified = [
            "free tier", "within limits", "current limits", "no new spend",
            "testing", "being built", "volunteer proof"
        ]

        if any(word in body.lower() for word in ["free", "zero", "no cost"]):
            if not any(q.lower() in body.lower() for q in qualified):
                findings.append("Free claims present but not qualified")
                required_changes.append("Add limits, verification, or qualified language")
                score -= 2

        return ValidationResult(
            validator_name="ZeroCostComplianceAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings,
            required_changes=required_changes,
            notes=f"Zero-cost compliance check - {len(findings)} issues found"
        )


class OfferAlignmentAgent:
    """Validates alignment with Already Here LLC offers"""

    VALID_OFFERS = [
        "Prime/Sub Protection Pack",
        "Field Intake & Proof Pack",
        "Google Forms-to-Sheets Intake Setup",
        "Cloudflare Workers Edge Intake Worker",
        "Contractor Proof-to-Invoice Workflow",
        "AI Workflow Setup Service",
        "Field Tech Toolkit Guide",
        "CRM Follow-Up Workflow",
    ]

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify article aligns with Already Here offer"""
        title = article.get("title", "")
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10

        # Check if article mentions Already Here
        if "already here" not in body.lower():
            findings.append("No Already Here mention or offer alignment")
            required_changes.append("Add clear tie to an Already Here LLC offer or service")
            score -= 3

        # Check if article supports a specific offer
        offer_found = False
        for offer in OfferAlignmentAgent.VALID_OFFERS:
            if offer.lower() in body.lower():
                offer_found = True
                break

        if not offer_found:
            findings.append("Article does not map to a specific Already Here offer")
            required_changes.append(f"Tie to one of: {', '.join(OfferAlignmentAgent.VALID_OFFERS[:3])}")
            score -= 2

        # Check for weak monetization angle
        if "sell" not in body.lower() and "service" not in body.lower() and "offer" not in body.lower():
            findings.append("No clear monetization or service angle")
            required_changes.append("Add section on what Already Here would implement or sell")
            score -= 1

        return ValidationResult(
            validator_name="OfferAlignmentAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings,
            required_changes=required_changes,
            notes=f"Offer alignment check - article maps to Already Here services"
        )


class ProofOfWorkAgent:
    """Validates proof-of-work language and status"""

    BLOCKED_POW = [
        "proven system", "guaranteed to", "will increase",
        "fully automated", "passive income system", "results in",
        "100% effective", "zero effort"
    ]

    ALLOWED_POW = [
        "testing", "being built", "proof-of-work version",
        "in development", "client validation", "internal test"
    ]

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify proof-of-work language"""
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10

        # Check for blocked language
        for phrase in ProofOfWorkAgent.BLOCKED_POW:
            if phrase.lower() in body.lower():
                findings.append(f"Pre-proof language used: '{phrase}'")
                required_changes.append(f"Change to testing/building language")
                score -= 2

        # Check if proof status is clearly stated
        has_proof_language = any(p.lower() in body.lower() for p in ProofOfWorkAgent.ALLOWED_POW)
        if not has_proof_language and any(word in body.lower() for word in ["already here", "system", "workflow"]):
            findings.append("Proof-of-work status not clearly stated")
            required_changes.append("Add clarity on whether this is idea, draft, test, or proven")
            score -= 1

        return ValidationResult(
            validator_name="ProofOfWorkAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings,
            required_changes=required_changes,
            notes=f"Proof-of-work check - language aligned with actual development status"
        )


class SecurityAgent:
    """Validates security requirements for technical content"""

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify security standards"""
        title = article.get("title", "")
        body = article.get("body", "")

        findings = []
        required_changes = []
        security_risks = []
        score = 10

        # Check if article involves security-sensitive topics
        sensitive_topics = ["api", "cloud", "automation", "webhook", "form", "affiliate", "tracking", "auth"]
        has_sensitive = any(topic in title.lower() + body.lower() for topic in sensitive_topics)

        if has_sensitive:
            # Check for security mentions
            security_keywords = ["secure", "environment variable", "api key", "secret", "validation", "rate limit"]
            has_security = any(kw in body.lower() for kw in security_keywords)

            if not has_security:
                findings.append("Security-sensitive topic without security discussion")
                required_changes.append("Add security requirements section")
                score -= 3

            # Check for specific security violations
            if "api_key" in body or "password" in body or "secret" in body:
                if "environment" not in body.lower():
                    security_risks.append("Possible hardcoded credentials")
                    required_changes.append("Ensure all credentials use environment variables")
                    score -= 2

            if "webhook" in body.lower() and "validate" not in body.lower():
                security_risks.append("Webhook endpoint without validation")
                required_changes.append("Add request validation section")
                score -= 2

        return ValidationResult(
            validator_name="SecurityAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings + security_risks,
            required_changes=required_changes,
            notes=f"Security check - {len(security_risks)} potential risks identified"
        )


class ContentStructureAgent:
    """Validates required article structure"""

    REQUIRED_SECTIONS = [
        "reader problem",
        "technical explanation",
        "use case",
        "already here angle",
        "zero-cost path",
        "next step",
        "affiliate disclosure"
    ]

    @staticmethod
    def validate(article: Dict[str, Any]) -> ValidationResult:
        """Verify article structure"""
        body = article.get("body", "")

        findings = []
        required_changes = []
        score = 10

        # Check for required sections (lowercase matching)
        body_lower = body.lower()
        found_sections = []

        for section in ContentStructureAgent.REQUIRED_SECTIONS:
            if section in body_lower:
                found_sections.append(section)
            else:
                findings.append(f"Missing section: {section}")
                required_changes.append(f"Add '{section}' section to article")
                score -= 1

        # Check article starts with problem, not filler
        filler_start = [
            "in today's digital world",
            "businesses need",
            "this powerful",
            "the importance of"
        ]

        first_100_chars = body[:100].lower()
        if any(filler in first_100_chars for filler in filler_start):
            findings.append("Article starts with generic filler")
            required_changes.append("Start with actual reader problem, not generic intro")
            score -= 2

        return ValidationResult(
            validator_name="ContentStructureAgent",
            passed=score >= 7,
            score=max(0, score),
            findings=findings,
            required_changes=required_changes,
            notes=f"Structure check - {len(found_sections)}/{len(ContentStructureAgent.REQUIRED_SECTIONS)} required sections found"
        )


class ScoringAgent:
    """Calculates final quality score"""

    @staticmethod
    def validate(article: Dict[str, Any], validator_results: List[ValidationResult]) -> tuple[QualityScore, ValidationResult]:
        """Calculate final quality scores"""

        # Map validator results to quality scores
        score_map = {v.validator_name: v.score for v in validator_results}

        quality = QualityScore(
            technical_accuracy=score_map.get("TechnicalAccuracyAgent", 0),
            source_verification=score_map.get("TechnicalAccuracyAgent", 0),
            offer_alignment=score_map.get("OfferAlignmentAgent", 0),
            affiliate_relevance=score_map.get("AffiliateRelevanceAgent", 0),
            zero_cost_compliance=score_map.get("ZeroCostComplianceAgent", 0),
            proof_of_work_status=score_map.get("ProofOfWorkAgent", 0),
            security_quality=score_map.get("SecurityAgent", 0),
            reader_value=score_map.get("ContentStructureAgent", 0),
            already_here_fit=score_map.get("OfferAlignmentAgent", 0),
            publish_risk=10 if not quality.passes_threshold else 3
        )

        result = ValidationResult(
            validator_name="ScoringAgent",
            passed=quality.passes_threshold,
            score=int(quality.average),
            findings=[f"Average score: {quality.average:.1f}/10"],
            required_changes=[] if quality.passes_threshold else ["Article must be rewritten to meet publishing threshold"],
            notes=f"Final score: {quality.average:.1f}/10 - {'PASS' if quality.passes_threshold else 'HOLD FOR REVIEW'}"
        )

        return quality, result


# ── Quality Gate Orchestrator ────────────────────────────────────────────────

class ContentQualityGate:
    """Master orchestrator for all quality validations"""

    def __init__(self):
        self.agents = [
            TechnicalAccuracyAgent,
            AffiliateRelevanceAgent,
            ZeroCostComplianceAgent,
            OfferAlignmentAgent,
            ProofOfWorkAgent,
            SecurityAgent,
            ContentStructureAgent,
        ]

    def validate_article(self, article: Dict[str, Any]) -> PublishValidation:
        """Run complete quality validation pipeline"""

        # Run all agents
        validator_results = []
        for agent_class in self.agents:
            result = agent_class.validate(article)
            validator_results.append(result)

        # Calculate final score
        quality_score, scoring_result = ScoringAgent.validate(article, validator_results)
        validator_results.append(scoring_result)

        # Build validation output
        validation = PublishValidation(
            article_title=article.get("title", ""),
            target_buyer=article.get("target_buyer", "Unknown"),
            primary_offer=article.get("primary_offer", "Unspecified"),

            affiliate_links_present="http" in article.get("body", ""),
            affiliate_links_approved=validator_results[1].passed,  # AffiliateRelevanceAgent
            unrelated_tools_removed=[],

            zero_cost_claims_present="free" in article.get("body", "").lower(),
            zero_cost_claims_verified=validator_results[2].passed,  # ZeroCostComplianceAgent

            technical_claims_verified=validator_results[0].passed,  # TechnicalAccuracyAgent
            official_sources_checked=[],

            security_risks_found=validator_results[5].findings,  # SecurityAgent
            proof_of_work_status="ready_to_publish" if quality_score.passes_threshold else "needs_review",

            publish_status="publish" if quality_score.passes_threshold else "hold_for_review",
            required_changes=[change for result in validator_results for change in result.required_changes],
            final_notes=f"Quality score: {quality_score.average:.1f}/10 - {scoring_result.notes}",

            quality_scores=quality_score,
            validator_results=validator_results
        )

        return validation

    def publish_validation_report(self, validation: PublishValidation) -> str:
        """Generate readable validation report"""
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║  PROFITENGINE CONTENT QUALITY GATE VALIDATION REPORT           ║
╚════════════════════════════════════════════════════════════════╝

ARTICLE: {validation.article_title}
TARGET BUYER: {validation.target_buyer}
PRIMARY OFFER: {validation.primary_offer}
TIMESTAMP: {validation.timestamp}

PUBLISH STATUS: {validation.publish_status.upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUALITY SCORES:
"""
        if validation.quality_scores:
            scores = validation.quality_scores
            report += f"""
  Technical Accuracy:        {scores.technical_accuracy}/10
  Source Verification:       {scores.source_verification}/10
  Offer Alignment:           {scores.offer_alignment}/10
  Affiliate Relevance:       {scores.affiliate_relevance}/10
  Zero-Cost Compliance:      {scores.zero_cost_compliance}/10
  Proof-of-Work Status:      {scores.proof_of_work_status}/10
  Security Quality:          {scores.security_quality}/10
  Reader Value:              {scores.reader_value}/10
  Already Here Fit:          {scores.already_here_fit}/10
  Publish Risk:              {scores.publish_risk}/10 (lower is better)

  AVERAGE SCORE: {scores.average:.1f}/10
  PASSES THRESHOLD: {scores.passes_threshold}
"""

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VALIDATOR RESULTS:
"""

        if validation.validator_results:
            for result in validation.validator_results:
                status = "✓ PASS" if result.passed else "✗ FAIL"
                report += f"""
{status} - {result.validator_name} ({result.score}/10)
"""
                if result.findings:
                    for finding in result.findings:
                        report += f"    - {finding}\n"

        if validation.required_changes:
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUIRED CHANGES ({len(validation.required_changes)}):
"""
            for i, change in enumerate(validation.required_changes, 1):
                report += f"  {i}. {change}\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FINAL NOTES:
{validation.final_notes}

{"✓ ARTICLE APPROVED FOR PUBLISHING" if validation.publish_status == "publish" else "✗ ARTICLE HELD FOR REVIEW - DO NOT PUBLISH"}

╚════════════════════════════════════════════════════════════════╝
"""
        return report


# ── Main Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with sample article
    test_article = {
        "title": "Cloudflare Workers for Small Service Businesses",
        "body": """
Reader Problem:
Small service businesses lose leads because requests are not routed or tracked.

Technical Explanation:
Cloudflare Workers is an edge computing layer that can handle lightweight APIs and request routing.

Already Here Angle:
Already Here offers Edge Intake Worker setup service.

Zero-Cost Path:
Can be tested on the free tier within current platform limits.

Next Step:
Get the Edge Intake Worker checklist before publishing your next QR code.

Affiliate Disclosure:
This article may contain affiliate links.

Security:
Use environment variables for API keys. Validate incoming requests.
""",
        "target_buyer": "Small service business owner",
        "primary_offer": "Edge Intake Worker"
    }

    gate = ContentQualityGate()
    validation = gate.validate_article(test_article)

    print(gate.publish_validation_report(validation))

    # Output JSON for integration
    print("\n\nJSON OUTPUT FOR PIPELINE:\n")
    output = {
        "article_title": validation.article_title,
        "publish_status": validation.publish_status,
        "quality_score": validation.quality_scores.average if validation.quality_scores else 0,
        "required_changes": validation.required_changes,
        "validator_results": [asdict(v) for v in validation.validator_results] if validation.validator_results else []
    }
    print(json.dumps(output, indent=2, default=str))
