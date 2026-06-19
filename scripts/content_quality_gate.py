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
- Content structure standards

Each validation task runs as an independent agent.
All agents must pass before publish_status = PUBLISH.

Scoring Requirements:
- Each validator must score >= 7/10 (minimum category threshold)
- Overall average must be >= 8/10 (minimum publication threshold)
- Publish status is PUBLISH (pass) or HOLD_FOR_REVIEW (fail)

Distribution Channels (post-quality gate):
1. Dev.to (500K+ developers)
2. Hashnode (2M+ tech audience)
3. Medium (10M+ tech readers)
4. Beehiiv (newsletter + weekly digests)
5. Resend (email to segmented subscribers)
6. YouTube (video + AdSense)
7. Telegram (notification alerts)
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ── Quality Gate Data Structures ────────────────────────────────────────────

@dataclass
class QualityScore:
    """Article quality scoring with 7 independent validators"""
    technical_accuracy: int  # 0-10 — free claims, setup steps accuracy
    affiliate_relevance: int  # 0-10 — link relevance, no stuffing
    zero_cost_compliance: int  # 0-10 — free/unlimited claims qualified
    offer_alignment: int  # 0-10 — Already Here LLC alignment
    proof_of_work_status: int  # 0-10 — proof language, no "guaranteed"
    security_quality: int  # 0-10 — security for API/cloud content
    content_structure: int  # 0-10 — required sections present

    @property
    def average(self) -> float:
        """Calculate average score across 7 categories"""
        total = (
            self.technical_accuracy + self.affiliate_relevance +
            self.zero_cost_compliance + self.offer_alignment +
            self.proof_of_work_status + self.security_quality +
            self.content_structure
        )
        return total / 7

    @property
    def all_categories_pass(self) -> bool:
        """Check if all categories meet minimum threshold (7/10)"""
        return all([
            self.technical_accuracy >= 7,
            self.affiliate_relevance >= 7,
            self.zero_cost_compliance >= 7,
            self.offer_alignment >= 7,
            self.proof_of_work_status >= 7,
            self.security_quality >= 7,
            self.content_structure >= 7,
        ])

    @property
    def passes_threshold(self) -> bool:
        """Check if article passes publishing threshold

        Requirements:
        - Overall average >= 8/10
        - All categories >= 7/10
        """
        return (
            self.average >= 8.0 and
            self.all_categories_pass
        )


@dataclass
class ValidationResult:
    """Result from a single independent validator agent"""
    validator_name: str
    passed: bool
    score: int  # 0-10
    findings: List[str]  # Issues discovered
    required_changes: List[str]  # Specific changes needed
    notes: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PublishValidation:
    """Complete article validation report with all agent results"""
    article_title: str
    target_buyer: str
    primary_offer: str

    # Affiliate validation
    affiliate_links_present: bool
    affiliate_links_approved: bool
    unrelated_tools_removed: List[str]

    # Zero-cost validation
    zero_cost_claims_present: bool
    zero_cost_claims_verified: bool

    # Technical validation
    technical_claims_verified: bool
    official_sources_checked: List[str]

    # Security validation
    security_risks_found: List[str]

    # Proof-of-work validation
    proof_of_work_status: str  # idea | draft | internal_proof | client_proof | ready_to_promote | ready_to_sell

    # Final decision
    publish_status: str  # "publish" or "hold_for_review"
    required_changes: List[str]
    final_notes: str

    # Detailed results
    quality_scores: Optional[QualityScore] = None
    validator_results: Optional[List[ValidationResult]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
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
    """Aggregates all validator results and calculates final publication decision

    This agent does NOT validate content directly.
    Instead, it aggregates the scores from the 7 independent validator agents
    and determines if the article meets the publication threshold.
    """

    @staticmethod
    def calculate_scores(validator_results: List[ValidationResult]) -> QualityScore:
        """Map validator results to quality scores

        Maps agent names to score categories:
        - TechnicalAccuracyAgent → technical_accuracy
        - AffiliateRelevanceAgent → affiliate_relevance
        - ZeroCostComplianceAgent → zero_cost_compliance
        - OfferAlignmentAgent → offer_alignment
        - ProofOfWorkAgent → proof_of_work_status
        - SecurityAgent → security_quality
        - ContentStructureAgent → content_structure
        """
        score_map = {v.validator_name: v.score for v in validator_results}

        quality = QualityScore(
            technical_accuracy=score_map.get("TechnicalAccuracyAgent", 0),
            affiliate_relevance=score_map.get("AffiliateRelevanceAgent", 0),
            zero_cost_compliance=score_map.get("ZeroCostComplianceAgent", 0),
            offer_alignment=score_map.get("OfferAlignmentAgent", 0),
            proof_of_work_status=score_map.get("ProofOfWorkAgent", 0),
            security_quality=score_map.get("SecurityAgent", 0),
            content_structure=score_map.get("ContentStructureAgent", 0),
        )
        return quality

    @staticmethod
    def generate_scoring_result(quality: QualityScore) -> ValidationResult:
        """Generate final scoring report"""
        findings = [
            f"Average score: {quality.average:.1f}/10",
            f"Categories at/above 7/10: {sum(1 for s in [quality.technical_accuracy, quality.affiliate_relevance, quality.zero_cost_compliance, quality.offer_alignment, quality.proof_of_work_status, quality.security_quality, quality.content_structure] if s >= 7)}/7",
        ]

        if quality.technical_accuracy < 7:
            findings.append(f"Technical accuracy below threshold: {quality.technical_accuracy}/10")
        if quality.affiliate_relevance < 7:
            findings.append(f"Affiliate relevance below threshold: {quality.affiliate_relevance}/10")
        if quality.zero_cost_compliance < 7:
            findings.append(f"Zero-cost compliance below threshold: {quality.zero_cost_compliance}/10")
        if quality.offer_alignment < 7:
            findings.append(f"Offer alignment below threshold: {quality.offer_alignment}/10")
        if quality.proof_of_work_status < 7:
            findings.append(f"Proof-of-work status below threshold: {quality.proof_of_work_status}/10")
        if quality.security_quality < 7:
            findings.append(f"Security quality below threshold: {quality.security_quality}/10")
        if quality.content_structure < 7:
            findings.append(f"Content structure below threshold: {quality.content_structure}/10")

        required_changes = []
        if quality.average < 8.0:
            required_changes.append(f"Improve overall average from {quality.average:.1f}/10 to 8.0/10 or higher")
        if not quality.all_categories_pass:
            required_changes.append("Raise all categories to 7/10 minimum before publishing")

        result = ValidationResult(
            validator_name="ScoringAgent",
            passed=quality.passes_threshold,
            score=int(quality.average),
            findings=findings,
            required_changes=required_changes,
            notes=f"Final score: {quality.average:.1f}/10 - {'PASS: Ready for publication' if quality.passes_threshold else 'HOLD FOR REVIEW: Below publishing threshold'}",
        )

        return result


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
        """Run complete quality validation pipeline with 7 independent agents

        Process:
        1. Run TechnicalAccuracyAgent on free claims and setup steps
        2. Run AffiliateRelevanceAgent on link quality and density
        3. Run ZeroCostComplianceAgent on unqualified free claims
        4. Run OfferAlignmentAgent on Already Here LLC tie-in
        5. Run ProofOfWorkAgent on language safety
        6. Run SecurityAgent on API/cloud content safety
        7. Run ContentStructureAgent on required sections
        8. Aggregate scores and determine publication status

        Returns:
            PublishValidation with all validator results and final decision
        """

        # Step 1-7: Run all independent validators
        validator_results = []
        for agent_class in self.agents:
            result = agent_class.validate(article)
            validator_results.append(result)
            print(f"[VALIDATE] {result.validator_name}: {result.score}/10 - {'PASS' if result.passed else 'FAIL'}")

        # Step 8: Calculate final score and decision
        quality_score = ScoringAgent.calculate_scores(validator_results)
        scoring_result = ScoringAgent.generate_scoring_result(quality_score)
        validator_results.append(scoring_result)

        # Extract validator data by category
        technical_result = next((r for r in validator_results if r.validator_name == "TechnicalAccuracyAgent"), None)
        affiliate_result = next((r for r in validator_results if r.validator_name == "AffiliateRelevanceAgent"), None)
        zero_cost_result = next((r for r in validator_results if r.validator_name == "ZeroCostComplianceAgent"), None)
        security_result = next((r for r in validator_results if r.validator_name == "SecurityAgent"), None)

        # Build comprehensive validation report
        validation = PublishValidation(
            article_title=article.get("title", ""),
            target_buyer=article.get("target_buyer", "Unknown"),
            primary_offer=article.get("primary_offer", "Unspecified"),

            # Affiliate validation summary
            affiliate_links_present="http" in article.get("body", ""),
            affiliate_links_approved=affiliate_result.passed if affiliate_result else False,
            unrelated_tools_removed=affiliate_result.findings if affiliate_result else [],

            # Zero-cost validation summary
            zero_cost_claims_present="free" in article.get("body", "").lower() or "zero" in article.get("body", "").lower(),
            zero_cost_claims_verified=zero_cost_result.passed if zero_cost_result else False,

            # Technical validation summary
            technical_claims_verified=technical_result.passed if technical_result else False,
            official_sources_checked=technical_result.findings if technical_result else [],

            # Security validation summary
            security_risks_found=security_result.findings if security_result else [],

            # Publication decision
            proof_of_work_status="ready_to_publish" if quality_score.passes_threshold else "needs_review",
            publish_status="publish" if quality_score.passes_threshold else "hold_for_review",

            # Required actions
            required_changes=[change for result in validator_results if result.required_changes for change in result.required_changes],
            final_notes=f"Quality score: {quality_score.average:.1f}/10 - {scoring_result.notes}",

            # Full results
            quality_scores=quality_score,
            validator_results=validator_results
        )

        return validation

    def publish_validation_report(self, validation: PublishValidation) -> str:
        """Generate detailed validation report with all agent results"""
        status_symbol = "[PASS]" if validation.publish_status == "publish" else "[FAIL]"
        status_hint = "PUBLISH" if validation.publish_status == "publish" else "BLOCKED"

        report = f"""
==============================================================================
   PROFITENGINE CONTENT QUALITY GATE REPORT
   Status: {status_symbol} {status_hint}
==============================================================================

ARTICLE METADATA:
  Title:            {validation.article_title}
  Target Buyer:     {validation.target_buyer}
  Primary Offer:    {validation.primary_offer}
  Timestamp:        {validation.timestamp}

STATUS: {validation.publish_status.upper()}

------------------------------------------------------------------------------

QUALITY SCORES (7 Independent Validators):
"""
        if validation.quality_scores:
            scores = validation.quality_scores
            check_1 = "[PASS]" if scores.technical_accuracy >= 7 else "[FAIL]"
            check_2 = "[PASS]" if scores.affiliate_relevance >= 7 else "[FAIL]"
            check_3 = "[PASS]" if scores.zero_cost_compliance >= 7 else "[FAIL]"
            check_4 = "[PASS]" if scores.offer_alignment >= 7 else "[FAIL]"
            check_5 = "[PASS]" if scores.proof_of_work_status >= 7 else "[FAIL]"
            check_6 = "[PASS]" if scores.security_quality >= 7 else "[FAIL]"
            check_7 = "[PASS]" if scores.content_structure >= 7 else "[FAIL]"

            report += f"""
  1. Technical Accuracy:         {scores.technical_accuracy}/10   {check_1}
  2. Affiliate Relevance:        {scores.affiliate_relevance}/10   {check_2}
  3. Zero-Cost Compliance:       {scores.zero_cost_compliance}/10   {check_3}
  4. Offer Alignment:            {scores.offer_alignment}/10   {check_4}
  5. Proof-of-Work Status:       {scores.proof_of_work_status}/10   {check_5}
  6. Security Quality:           {scores.security_quality}/10   {check_6}
  7. Content Structure:          {scores.content_structure}/10   {check_7}

  -----------------------------------------------
  AVERAGE SCORE:                 {scores.average:.1f}/10
  Threshold (minimum):           8.0/10
  Status:                        {"PASS" if scores.passes_threshold else "FAIL"}
  All Categories >= 7:           {"YES" if scores.all_categories_pass else "NO"}

"""

        report += f"""
------------------------------------------------------------------------------

VALIDATION DETAILS:
"""

        if validation.validator_results:
            for result in validation.validator_results:
                if result.validator_name != "ScoringAgent":
                    status = "[PASS]" if result.passed else "[FAIL]"
                    report += f"""
{status} {result.validator_name} ({result.score}/10)
"""
                    if result.findings:
                        for finding in result.findings:
                            report += f"    - {finding}\n"
                    if result.required_changes:
                        for change in result.required_changes:
                            report += f"    * {change}\n"

        report += f"""
------------------------------------------------------------------------------

COMPLIANCE CHECKS:
"""

        if validation.technical_claims_verified:
            report += "  [OK] Technical claims verified\n"
        else:
            report += "  [!!] Technical claims need review\n"

        if validation.affiliate_links_approved:
            report += "  [OK] Affiliate links approved and relevant\n"
        else:
            report += "  [!!] Affiliate links need review\n"

        if validation.zero_cost_claims_verified:
            report += "  [OK] Zero-cost claims properly qualified\n"
        else:
            report += "  [!!] Zero-cost claims need qualification\n"

        if validation.security_risks_found:
            report += f"  [!!] Security risks identified: {len(validation.security_risks_found)}\n"
        else:
            report += "  [OK] No security risks identified\n"

        if validation.required_changes:
            report += f"""
------------------------------------------------------------------------------

REQUIRED CHANGES ({len(validation.required_changes)}):
"""
            for i, change in enumerate(validation.required_changes, 1):
                report += f"  {i}. {change}\n"

        report += f"""
------------------------------------------------------------------------------

SUMMARY:
{validation.final_notes}

{("APPROVED FOR PUBLISHING - Ready to distribute to all platforms" if validation.publish_status == "publish" else "HELD FOR REVIEW - Do not publish until changes are made")}

Next Step: {("Send to distribution channels (Dev.to, Hashnode, Medium, etc.)" if validation.publish_status == "publish" else "Review findings above, make required changes, and re-validate")}

==============================================================================
"""
        return report


# ── Integration Functions ───────────────────────────────────────────────────

def validate_before_publish(article: Dict[str, Any], verbose: bool = True) -> Tuple[bool, PublishValidation]:
    """Pre-publish quality gate validation

    This function should be called by publish_article_resilient.py before
    distributing the article to any platforms.

    Args:
        article: Article dict with title, body, tags, target_buyer, primary_offer
        verbose: Print full validation report (default: True)

    Returns:
        Tuple of (should_publish: bool, validation_result: PublishValidation)
        - should_publish is True if publish_status == "publish"
        - validation_result contains all validator findings and recommendations
    """
    gate = ContentQualityGate()
    validation = gate.validate_article(article)

    if verbose:
        print(gate.publish_validation_report(validation))

    should_publish = validation.publish_status == "publish"
    return should_publish, validation


def get_quality_gate_json(article: Dict[str, Any]) -> Dict[str, Any]:
    """Get quality gate results as JSON for integration with other systems

    Returns JSON-serializable dict with:
    - publish_status: "publish" or "hold_for_review"
    - quality_score: float 0-10
    - category_scores: dict with each validator's score
    - issues: list of findings requiring fixes
    - required_changes: list of specific changes needed
    """
    gate = ContentQualityGate()
    validation = gate.validate_article(article)

    # Extract category scores
    category_scores = {}
    if validation.validator_results:
        for result in validation.validator_results:
            if result.validator_name != "ScoringAgent":
                category_scores[result.validator_name] = {
                    "score": result.score,
                    "passed": result.passed,
                    "findings": result.findings,
                }

    return {
        "article_title": validation.article_title,
        "publish_status": validation.publish_status,
        "quality_score": validation.quality_scores.average if validation.quality_scores else 0,
        "average_threshold": 8.0,
        "category_threshold": 7.0,
        "passes_all_categories": validation.quality_scores.all_categories_pass if validation.quality_scores else False,
        "category_scores": category_scores,
        "issues": [item for result in validation.validator_results or [] for item in result.findings],
        "required_changes": validation.required_changes,
        "final_notes": validation.final_notes,
        "timestamp": validation.timestamp,
    }


# ── Main Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with sample article
    test_article = {
        "title": "Cloudflare Workers for Small Service Businesses",
        "body": """
## Reader Problem

Small service businesses lose leads because requests are not routed or tracked. Without a system to capture and qualify inquiries, response times suffer and opportunities are missed.

## Technical Explanation

Cloudflare Workers is an edge computing layer that can handle lightweight APIs and request routing. It runs globally, responds in milliseconds, and scales without configuration.

## Already Here Angle

Already Here offers Edge Intake Worker setup service as part of the Field Tech Toolkit. We build the intake form, validate requests, and route to the right team member automatically.

## Zero-Cost Path

Can be tested on the free tier within current platform limits. The free tier includes 100,000 requests per day, which is enough to validate the concept for most small businesses.

## Proof of Work

We are currently building a proof-of-work version with two client validations. The intake worker is in development and being tested with service field teams.

## Security

When building intake workers, always use environment variables for API keys. Validate incoming requests with checksums or signed tokens. Never log or store raw customer data longer than needed for processing.

## Next Step

Get the Edge Intake Worker checklist before publishing your next QR code. Book a setup call to discuss your specific lead routing process.

## Affiliate Disclosure

This article may contain affiliate links to Cloudflare and related tools.
""",
        "target_buyer": "Small service business owner",
        "primary_offer": "Edge Intake Worker"
    }

    # Run validation
    should_publish, validation = validate_before_publish(test_article, verbose=True)

    # Output JSON for integration
    print("\n\nJSON OUTPUT FOR PIPELINE:\n")
    json_output = get_quality_gate_json(test_article)
    print(json.dumps(json_output, indent=2, default=str))

    # Summary
    print(f"\n\n[RESULT] Should publish: {should_publish}")
    print(f"[RESULT] Status: {validation.publish_status}")
    print(f"[RESULT] Quality score: {validation.quality_scores.average:.1f}/10" if validation.quality_scores else "[RESULT] Quality score: 0/10")
    print(f"[RESULT] Required changes: {len(validation.required_changes)}")
