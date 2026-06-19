#!/usr/bin/env python3
"""
Content Distribution System - Integration Test & Verification Script

Tests the complete distribution network for ProfitEngine content:
- Social media publishers (Twitter, Reddit, LinkedIn, Facebook, Instagram, TikTok, YouTube)
- E-commerce platforms (Etsy, Gumroad, Printify)

Performs credential validation, dry-run tests, and generates a production readiness report.

Usage:
    python scripts/test_distribution.py              # Full test with report
    python scripts/test_distribution.py --verbose    # Detailed output
    python scripts/test_distribution.py --check-only # Just check credentials
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import traceback

# Try importing the publisher modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from social_media_publishers import (
        SOCIAL_PUBLISHERS,
        publish_to_all_platforms,
        # Credential vars
        TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET,
        REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD,
        LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN,
        FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN,
        IG_USER_ID,
        TIKTOK_ACCESS_TOKEN,
        YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN,
    )
except ImportError as e:
    print(f"ERROR: Could not import social_media_publishers: {e}")
    sys.exit(1)

try:
    from ecommerce_publishers import (
        ECOMMERCE_PUBLISHERS,
        publish_to_all_ecommerce,
        # Credential vars
        ETSY_SHOP_ID, ETSY_API_KEY,
        GUMROAD_API_TOKEN, GUMROAD_CREATOR_ID,
        PRINTIFY_API_KEY, PRINTIFY_SHOP_ID,
    )
except ImportError as e:
    print(f"ERROR: Could not import ecommerce_publishers: {e}")
    sys.exit(1)


# ── Test Article (Mock) ────────────────────────────────────────────────────────

MOCK_ARTICLE = {
    "title": "10 Profit Secrets Every Entrepreneur Must Know",
    "body": "This comprehensive guide covers the essential strategies and techniques that top entrepreneurs use to maximize profit margins and scale their businesses sustainably. Learn about pricing psychology, cost optimization, revenue diversification, and more.",
    "meta_description": "Discover the top 10 profit-maximizing strategies used by successful entrepreneurs. Practical tips for improving margins and scaling revenue.",
    "tags": ["profit", "entrepreneurship", "business-strategy", "finance"],
    "author": "Stephen Franklin",
    "published_at": datetime.now().isoformat(),
    "canonical_url": "https://alreadyherellc.com/blog/10-profit-secrets",
}

MOCK_IMAGE_URL = "https://alreadyherellc.com/images/profit-secrets.jpg"
MOCK_VIDEO_URL = "https://alreadyherellc.com/videos/profit-secrets.mp4"


# ── Platform Credential Registry ───────────────────────────────────────────────

PLATFORM_CREDENTIALS = {
    # Social Media Platforms
    "twitter": {
        "display_name": "Twitter/X",
        "type": "social",
        "required_vars": [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_SECRET",
        ],
        "values": {
            "TWITTER_API_KEY": TWITTER_API_KEY,
            "TWITTER_API_SECRET": TWITTER_API_SECRET,
            "TWITTER_ACCESS_TOKEN": TWITTER_ACCESS_TOKEN,
            "TWITTER_ACCESS_SECRET": TWITTER_ACCESS_SECRET,
        },
        "notes": "Requires API v2 credentials with tweet.write permissions",
    },
    "reddit": {
        "display_name": "Reddit",
        "type": "social",
        "required_vars": [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "REDDIT_USERNAME",
            "REDDIT_PASSWORD",
        ],
        "values": {
            "REDDIT_CLIENT_ID": REDDIT_CLIENT_ID,
            "REDDIT_CLIENT_SECRET": REDDIT_CLIENT_SECRET,
            "REDDIT_USERNAME": REDDIT_USERNAME,
            "REDDIT_PASSWORD": REDDIT_PASSWORD,
        },
        "notes": "Requires OAuth app registration + REDDIT_SUBREDDIT env var",
    },
    "linkedin": {
        "display_name": "LinkedIn",
        "type": "social",
        "required_vars": [
            "LINKEDIN_ACCESS_TOKEN",
            "LINKEDIN_PERSON_URN",
        ],
        "values": {
            "LINKEDIN_ACCESS_TOKEN": LINKEDIN_ACCESS_TOKEN,
            "LINKEDIN_PERSON_URN": LINKEDIN_PERSON_URN,
        },
        "notes": "Access token expires every 60 days - requires monthly refresh",
    },
    "facebook": {
        "display_name": "Facebook",
        "type": "social",
        "required_vars": [
            "FB_PAGE_ID",
            "FB_PAGE_ACCESS_TOKEN",
        ],
        "values": {
            "FB_PAGE_ID": FB_PAGE_ID,
            "FB_PAGE_ACCESS_TOKEN": FB_PAGE_ACCESS_TOKEN,
        },
        "notes": "Page access token (not user token) - expires if you change password",
    },
    "instagram": {
        "display_name": "Instagram",
        "type": "social",
        "required_vars": [
            "IG_USER_ID",
            "FB_PAGE_ACCESS_TOKEN",  # Shared with Facebook
        ],
        "values": {
            "IG_USER_ID": IG_USER_ID,
            "FB_PAGE_ACCESS_TOKEN": FB_PAGE_ACCESS_TOKEN,
        },
        "notes": "Requires business/creator account + Facebook Page access token",
    },
    "tiktok": {
        "display_name": "TikTok",
        "type": "social",
        "required_vars": [
            "TIKTOK_ACCESS_TOKEN",
        ],
        "values": {
            "TIKTOK_ACCESS_TOKEN": TIKTOK_ACCESS_TOKEN,
        },
        "notes": "Requires TikTok for Creators account + OAuth approval",
    },
    "youtube": {
        "display_name": "YouTube",
        "type": "social",
        "required_vars": [
            "YOUTUBE_CLIENT_ID",
            "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REFRESH_TOKEN",
        ],
        "values": {
            "YOUTUBE_CLIENT_ID": YOUTUBE_CLIENT_ID,
            "YOUTUBE_CLIENT_SECRET": YOUTUBE_CLIENT_SECRET,
            "YOUTUBE_REFRESH_TOKEN": YOUTUBE_REFRESH_TOKEN,
        },
        "notes": "Requires OAuth 2.0 setup with 'youtube.upload' scope",
    },
    # E-Commerce Platforms
    "etsy": {
        "display_name": "Etsy",
        "type": "ecommerce",
        "required_vars": [
            "ETSY_SHOP_ID",
            "ETSY_API_KEY",
        ],
        "values": {
            "ETSY_SHOP_ID": ETSY_SHOP_ID,
            "ETSY_API_KEY": ETSY_API_KEY,
        },
        "notes": "API key from https://www.etsy.com/developers/your-apps",
    },
    "gumroad": {
        "display_name": "Gumroad",
        "type": "ecommerce",
        "required_vars": [
            "GUMROAD_API_TOKEN",
        ],
        "values": {
            "GUMROAD_API_TOKEN": GUMROAD_API_TOKEN,
        },
        "notes": "API token from https://app.gumroad.com/creator/settings/security",
    },
    "printify": {
        "display_name": "Printify",
        "type": "ecommerce",
        "required_vars": [
            "PRINTIFY_API_KEY",
            "PRINTIFY_SHOP_ID",
        ],
        "values": {
            "PRINTIFY_API_KEY": PRINTIFY_API_KEY,
            "PRINTIFY_SHOP_ID": PRINTIFY_SHOP_ID,
        },
        "notes": "API key from https://printify.com/user/account/api-access",
    },
}


# ── Credential Validation ──────────────────────────────────────────────────────

class CredentialValidator:
    """Validates platform credentials"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}

    def check_all_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Check credentials for all platforms"""
        for platform_key, platform_info in PLATFORM_CREDENTIALS.items():
            self.results[platform_key] = self._validate_platform(platform_key, platform_info)
        return self.results

    def _validate_platform(self, platform_key: str, platform_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single platform"""
        required_vars = platform_info["required_vars"]
        values = platform_info["values"]

        # Check which vars are configured
        configured = {}
        missing = {}

        for var_name in required_vars:
            value = values.get(var_name, "")
            if value and len(value) > 0:
                # Mask the actual value for security
                configured[var_name] = "CONFIGURED" if len(value) > 20 else f"SHORT({len(value)})"
            else:
                missing[var_name] = "MISSING"

        # Determine status
        if not missing:
            status = "READY"
            action = "WILL ATTEMPT POST"
        elif len(configured) > 0:
            status = "PARTIAL"
            action = "WILL SKIP (credentials incomplete)"
        else:
            status = "UNCONFIGURED"
            action = "WILL SKIP (no credentials)"

        result = {
            "platform_name": platform_info["display_name"],
            "platform_type": platform_info["type"],
            "status": status,
            "action": action,
            "configured": configured,
            "missing": missing,
            "required_count": len(required_vars),
            "configured_count": len(configured),
            "missing_count": len(missing),
            "notes": platform_info["notes"],
        }

        if self.verbose:
            self._print_platform_detail(platform_key, result)

        return result

    def _print_platform_detail(self, platform_key: str, result: Dict[str, Any]) -> None:
        """Print detailed info for a platform"""
        print(f"\n  [{result['platform_name']}]")
        print(f"    Status: {result['status']}")
        print(f"    Action: {result['action']}")
        if result['configured']:
            print(f"    Configured: {', '.join(result['configured'].keys())}")
        if result['missing']:
            print(f"    Missing:    {', '.join(result['missing'].keys())}")


# ── Dry-Run Test ──────────────────────────────────────────────────────────────

class DistributionDryRun:
    """Perform dry-run tests without posting"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}

    def test_all_platforms(self) -> Dict[str, Dict[str, Any]]:
        """Test all platforms without posting"""
        print("\n[DRY-RUN] Testing distribution without posting...")

        for platform_key, platform_info in PLATFORM_CREDENTIALS.items():
            self.results[platform_key] = self._test_platform(platform_key, platform_info)

        return self.results

    def _test_platform(self, platform_key: str, platform_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single platform"""
        platform_name = platform_info["display_name"]
        required_vars = platform_info["required_vars"]
        values = platform_info["values"]

        # Check if all required vars are configured
        all_configured = all(values.get(var_name, "") for var_name in required_vars)

        if not all_configured:
            return {
                "platform": platform_name,
                "can_test": False,
                "reason": "Credentials incomplete - skipping test",
                "would_post": False,
            }

        # For platforms that ARE configured, we do a dry-run validation
        # Without actually posting to the real API
        try:
            test_result = self._validate_api_availability(platform_key, platform_name)
            return {
                "platform": platform_name,
                "can_test": True,
                "reason": "Credentials present, would attempt post",
                "would_post": True,
                "api_check": test_result,
            }
        except Exception as e:
            return {
                "platform": platform_name,
                "can_test": True,
                "reason": "Credentials present, but validation failed",
                "would_post": False,
                "error": str(e),
            }

    def _validate_api_availability(self, platform_key: str, platform_name: str) -> Dict[str, Any]:
        """Validate API endpoint availability (dry-run)"""
        # This method checks if the API endpoint would be reachable
        # without actually sending data

        import httpx

        api_endpoints = {
            "twitter": "https://api.twitter.com/2/tweets",
            "reddit": "https://www.reddit.com/api/v1/",
            "linkedin": "https://api.linkedin.com/rest/posts",
            "facebook": "https://graph.facebook.com/v18.0/me",
            "instagram": "https://graph.instagram.com/v18.0/me",
            "tiktok": "https://open-api.tiktok.com/v1/oauth/token",
            "youtube": "https://www.googleapis.com/youtube/v3/videos",
            "etsy": "https://openapi.etsy.com/v3/",
            "gumroad": "https://api.gumroad.com/v2/",
            "printify": "https://api.printify.com/v1/",
        }

        endpoint = api_endpoints.get(platform_key)
        if not endpoint:
            return {"endpoint": "UNKNOWN", "reachable": False}

        try:
            response = httpx.head(endpoint, timeout=5, follow_redirects=True)
            reachable = response.status_code < 500
            return {
                "endpoint": endpoint,
                "reachable": reachable,
                "status_code": response.status_code,
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "reachable": False,
                "error": str(e),
            }


# ── Report Generation ──────────────────────────────────────────────────────────

class DistributionReport:
    """Generate comprehensive distribution readiness report"""

    def __init__(self, validator_results: Dict, dryrun_results: Dict):
        self.validator_results = validator_results
        self.dryrun_results = dryrun_results
        self.timestamp = datetime.now().isoformat()

    def generate_text_report(self) -> str:
        """Generate text report"""
        lines = []

        lines.append("=" * 80)
        lines.append("PROFITENGINE CONTENT DISTRIBUTION SYSTEM - VERIFICATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.timestamp}")
        lines.append("")

        # Summary
        lines.extend(self._summary_section())
        lines.append("")

        # Platform Status
        lines.extend(self._platform_status_section())
        lines.append("")

        # Missing Credentials
        lines.extend(self._missing_credentials_section())
        lines.append("")

        # Required GitHub Secrets
        lines.extend(self._github_secrets_section())
        lines.append("")

        # Platforms Ready for Production
        lines.extend(self._production_readiness_section())
        lines.append("")

        # Next Steps
        lines.extend(self._next_steps_section())
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def _summary_section(self) -> List[str]:
        """Summary section"""
        lines = ["SUMMARY", "-" * 80]

        ready = sum(1 for r in self.validator_results.values() if r["status"] == "READY")
        partial = sum(1 for r in self.validator_results.values() if r["status"] == "PARTIAL")
        unconfigured = sum(1 for r in self.validator_results.values() if r["status"] == "UNCONFIGURED")
        total = len(self.validator_results)

        lines.append(f"Total Platforms: {total}")
        lines.append(f"  Ready (all credentials):     {ready} / {total}")
        lines.append(f"  Partial (some credentials):  {partial} / {total}")
        lines.append(f"  Unconfigured (no creds):     {unconfigured} / {total}")
        lines.append("")

        overall_status = "PRODUCTION READY" if ready > 0 else "BLOCKED - Missing Credentials"
        lines.append(f"Overall Status: {overall_status}")

        return lines

    def _platform_status_section(self) -> List[str]:
        """Platform status section"""
        lines = ["PLATFORM STATUS", "-" * 80]

        # Group by type
        social_platforms = {
            k: v for k, v in self.validator_results.items()
            if v["platform_type"] == "social"
        }
        ecommerce_platforms = {
            k: v for k, v in self.validator_results.items()
            if v["platform_type"] == "ecommerce"
        }

        lines.append("\nSOCIAL MEDIA PLATFORMS:")
        for platform_key, result in sorted(social_platforms.items()):
            lines.extend(self._format_platform_row(result))

        lines.append("\nE-COMMERCE PLATFORMS:")
        for platform_key, result in sorted(ecommerce_platforms.items()):
            lines.extend(self._format_platform_row(result))

        return lines

    def _format_platform_row(self, result: Dict[str, Any]) -> List[str]:
        """Format a single platform row"""
        status_icon = {
            "READY": "[OK]",
            "PARTIAL": "[~~]",
            "UNCONFIGURED": "[XX]",
        }.get(result["status"], "[??]")

        line = f"  {status_icon} {result['platform_name']:<20} {result['status']:<15} ({result['configured_count']}/{result['required_count']} vars)"

        lines = [line]

        if result["missing"]:
            missing_vars = ", ".join(result["missing"].keys())
            lines.append(f"      Missing: {missing_vars}")

        if result["notes"]:
            lines.append(f"      Note: {result['notes']}")

        return lines

    def _missing_credentials_section(self) -> List[str]:
        """Missing credentials section"""
        lines = ["MISSING CREDENTIALS", "-" * 80]

        all_missing = {}
        for platform_key, result in self.validator_results.items():
            if result["missing"]:
                for var_name in result["missing"].keys():
                    if var_name not in all_missing:
                        all_missing[var_name] = []
                    all_missing[var_name].append(result["platform_name"])

        if not all_missing:
            lines.append("No missing credentials - all platforms are fully configured!")
            return lines

        for var_name in sorted(all_missing.keys()):
            platforms = all_missing[var_name]
            lines.append(f"\n{var_name}")
            for platform in sorted(platforms):
                lines.append(f"  - {platform}")

        return lines

    def _github_secrets_section(self) -> List[str]:
        """GitHub Secrets setup section"""
        lines = ["GITHUB SECRETS SETUP", "-" * 80]
        lines.append("Add these secrets to GitHub (Settings > Secrets and variables > Actions):")
        lines.append("")

        # Collect all missing secrets
        all_missing_secrets = set()
        for result in self.validator_results.values():
            for var_name in result["missing"].keys():
                all_missing_secrets.add(var_name)

        if not all_missing_secrets:
            lines.append("All secrets are configured! No GitHub setup needed.")
            return lines

        lines.append("# Add to GitHub Secrets (one per line):")
        lines.append("")

        for secret_name in sorted(all_missing_secrets):
            lines.append(f"gh secret set {secret_name} --body 'YOUR_VALUE_HERE'")

        lines.append("")
        lines.append("Or use the GitHub web UI (Recommended for sensitive tokens)")

        return lines

    def _production_readiness_section(self) -> List[str]:
        """Production readiness section"""
        lines = ["PRODUCTION READINESS CHECKLIST", "-" * 80]

        ready_platforms = [
            result for result in self.validator_results.values()
            if result["status"] == "READY"
        ]

        if not ready_platforms:
            lines.append("No platforms are fully configured for production yet.")
            return lines

        lines.append("\nThe following platforms are ready for production:")
        lines.append("")

        for result in sorted(ready_platforms, key=lambda x: x["platform_name"]):
            lines.append(f"  [✓] {result['platform_name']}")
            lines.append(f"      All {result['required_count']} required credentials configured")

        return lines

    def _next_steps_section(self) -> List[str]:
        """Next steps section"""
        lines = ["NEXT STEPS", "-" * 80]

        missing_secrets = set()
        for result in self.validator_results.values():
            for var_name in result["missing"].keys():
                missing_secrets.add(var_name)

        if missing_secrets:
            lines.append("1. Add missing GitHub Secrets:")
            lines.append(f"   {len(missing_secrets)} secrets need to be configured")
            lines.append("")
            lines.append("2. For each platform, obtain credentials from:")

            credential_sources = {
                "TWITTER_*": "https://developer.twitter.com/en/portal/dashboard",
                "REDDIT_*": "https://www.reddit.com/prefs/apps",
                "LINKEDIN_*": "https://www.linkedin.com/developers/apps",
                "FB_PAGE_*": "https://developers.facebook.com/apps/",
                "IG_USER_ID": "https://business.facebook.com/",
                "TIKTOK_*": "https://developer.tiktok.com/",
                "YOUTUBE_*": "https://console.developers.google.com/",
                "ETSY_*": "https://www.etsy.com/developers/your-apps",
                "GUMROAD_*": "https://app.gumroad.com/creator/settings",
                "PRINTIFY_*": "https://printify.com/user/account/api-access",
            }

            for prefix, url in sorted(credential_sources.items()):
                lines.append(f"   {prefix}: {url}")

            lines.append("")
            lines.append("3. Test distribution after adding secrets:")
            lines.append("   python scripts/test_distribution.py")

        else:
            lines.append("All platforms have credentials configured!")
            lines.append("")
            lines.append("Next steps:")
            lines.append("1. Run smoke tests: npm run test")
            lines.append("2. Deploy to production: git push main")
            lines.append("3. Monitor first content distribution in GitHub Actions")
            lines.append("4. Verify posts appear on all configured platforms")

        return lines

    def generate_json_report(self) -> str:
        """Generate JSON report"""
        report_data = {
            "timestamp": self.timestamp,
            "summary": {
                "total_platforms": len(self.validator_results),
                "ready": sum(1 for r in self.validator_results.values() if r["status"] == "READY"),
                "partial": sum(1 for r in self.validator_results.values() if r["status"] == "PARTIAL"),
                "unconfigured": sum(1 for r in self.validator_results.values() if r["status"] == "UNCONFIGURED"),
            },
            "platforms": self.validator_results,
        }

        return json.dumps(report_data, indent=2)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ProfitEngine Content Distribution System - Verification Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_distribution.py              # Full test with text report
  python scripts/test_distribution.py --verbose    # Detailed credential output
  python scripts/test_distribution.py --json       # JSON report for CI/CD
  python scripts/test_distribution.py --check-only # Just check credentials
        """,
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed credential validation output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON report instead of text"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check credentials, skip dry-run tests"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save report to file (text or JSON)"
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("PROFITENGINE CONTENT DISTRIBUTION SYSTEM - VERIFICATION")
    print("=" * 80)
    print("")

    # Validate credentials
    print("[1/3] Validating platform credentials...")
    validator = CredentialValidator(verbose=args.verbose)
    validator_results = validator.check_all_platforms()

    # Count results
    ready = sum(1 for r in validator_results.values() if r["status"] == "READY")
    partial = sum(1 for r in validator_results.values() if r["status"] == "PARTIAL")
    unconfigured = sum(1 for r in validator_results.values() if r["status"] == "UNCONFIGURED")

    print(f"  Ready: {ready} | Partial: {partial} | Unconfigured: {unconfigured}")
    print("")

    # Run dry-run tests
    if not args.check_only:
        print("[2/3] Running dry-run distribution tests...")
        dryrun = DistributionDryRun(verbose=args.verbose)
        dryrun_results = dryrun.test_all_platforms()
        print("  Dry-run tests completed")
        print("")
    else:
        dryrun_results = {}
        print("[2/3] Skipping dry-run tests (--check-only)")
        print("")

    # Generate report
    print("[3/3] Generating verification report...")
    report = DistributionReport(validator_results, dryrun_results)

    if args.json:
        output = report.generate_json_report()
    else:
        output = report.generate_text_report()

    # Output
    print(output)

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"\nReport saved to: {args.output}")

    # Exit code
    if ready > 0:
        sys.exit(0)
    else:
        print("\nWARNING: No platforms fully configured for production")
        sys.exit(1)


if __name__ == "__main__":
    main()
