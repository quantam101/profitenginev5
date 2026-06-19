#!/usr/bin/env python3
"""
ProfitEngine v5 — Centralized Sync Engine

Pushes all content, metrics, and updates to the profitenginev5 main repository
for centralized distribution. This is the hub for syncing:
  1. Blog posts (from content_generator.py)
  2. Daily metrics (P&L, win rates, customer count)
  3. Case studies (customer success stories)
  4. Social performance (engagement metrics)
  5. Landing page data (hero section numbers, testimonials)
  6. Email templates and campaign tracking

Configuration (set in .env or on the server):
  PROFITENGINEV5_REPO_URL     — GitHub repo URL (git clone source)
  PROFITENGINEV5_LOCAL_PATH   — Where to clone/manage the repo locally
  GITHUB_PROFITENGINEV5_TOKEN — Personal access token (repo scope)
  GITHUB_PROFITENGINEV5_USER  — GitHub username for commits
  GITHUB_PROFITENGINEV5_EMAIL — Email for commits
  PROFITENGINEV5_BRANCH       — Branch to commit to (default: main)

Sync Flow:
  1. Clone or fetch profitenginev5 repo (if needed)
  2. Generate/collect content and metrics
  3. Commit to local repo with standardized message
  4. Push to GitHub
  5. GitHub Actions auto-deploys the site
  6. Log sync event

This engine handles merge conflicts gracefully and maintains 2-way sync
by checking for remote changes before pushing.
"""

import os
import json
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List
import hashlib
import base64

import httpx

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────


def _cfg() -> Dict[str, str]:
    """Load sync engine config from environment."""
    return {
        "repo_url": os.getenv(
            "PROFITENGINEV5_REPO_URL",
            "https://github.com/quantam101/profitenginev5.git"
        ).strip(),
        "local_path": os.getenv(
            "PROFITENGINEV5_LOCAL_PATH",
            "/tmp/profitenginev5"
        ).strip(),
        "token": os.getenv("GITHUB_PROFITENGINEV5_TOKEN", "").strip(),
        "username": os.getenv("GITHUB_PROFITENGINEV5_USER", "profitengine-sync").strip(),
        "email": os.getenv("GITHUB_PROFITENGINEV5_EMAIL", "sync@profitengine.local").strip(),
        "branch": os.getenv("PROFITENGINEV5_BRANCH", "main").strip(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────────────────

def _init_logger(name: str = "profitenginev5_sync") -> logging.Logger:
    """Initialize logger for sync engine."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = _init_logger()


# ──────────────────────────────────────────────────────────────────────────────
# GIT OPERATIONS
# ──────────────────────────────────────────────────────────────────────────────

class GitSyncManager:
    """Manages git operations for the profitenginev5 repo."""

    def __init__(self, cfg: Dict[str, str]):
        self.cfg = cfg
        self.repo_path = Path(cfg["local_path"])
        self.logger = _init_logger()

    def _run_git(self, *args: str, check: bool = True) -> str:
        """Run a git command in the repo directory."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                timeout=30,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            self.logger.error(f"Git error: {exc.stderr}")
            raise

    def ensure_cloned(self) -> bool:
        """Clone repo if not already present."""
        if self.repo_path.exists():
            self.logger.info(f"Repo already exists at {self.repo_path}")
            return True

        try:
            self.logger.info(f"Cloning {self.cfg['repo_url']} to {self.repo_path}")
            self.repo_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", self.cfg["repo_url"], str(self.repo_path)],
                check=True,
                capture_output=True,
                timeout=60,
            )
            # Configure git user for this repo
            self._run_git("config", "user.name", self.cfg["username"])
            self._run_git("config", "user.email", self.cfg["email"])
            self.logger.info("Repo cloned and configured successfully")
            return True
        except subprocess.CalledProcessError as exc:
            self.logger.error(f"Failed to clone repo: {exc.stderr}")
            return False

    def fetch_latest(self) -> bool:
        """Fetch latest changes from origin."""
        try:
            self.logger.info("Fetching latest from origin")
            self._run_git("fetch", "origin")
            return True
        except subprocess.CalledProcessError:
            self.logger.warning("Fetch failed (repo may be offline)")
            return False

    def has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            status = self._run_git("status", "--porcelain")
            return bool(status)
        except subprocess.CalledProcessError:
            return False

    def add_file(self, relative_path: str) -> bool:
        """Stage a file for commit."""
        try:
            self._run_git("add", relative_path)
            return True
        except subprocess.CalledProcessError:
            return False

    def commit(self, message: str) -> bool:
        """Commit staged changes."""
        try:
            self._run_git("commit", "-m", message)
            self.logger.info(f"Committed: {message}")
            return True
        except subprocess.CalledProcessError as exc:
            # "nothing to commit" is not really an error
            if "nothing to commit" in exc.stderr:
                self.logger.info("No changes to commit")
                return True
            self.logger.error(f"Commit failed: {exc.stderr}")
            return False

    def push(self, branch: str = "main") -> bool:
        """Push to origin with conflict handling."""
        try:
            self.logger.info(f"Pushing to origin/{branch}")
            self._run_git("push", "origin", branch)
            self.logger.info("Push successful")
            return True
        except subprocess.CalledProcessError as exc:
            if "non-fast-forward" in exc.stderr or "rejected" in exc.stderr:
                self.logger.warning(f"Push rejected (non-fast-forward). Attempting rebase.")
                return self._resolve_conflict()
            self.logger.error(f"Push failed: {exc.stderr}")
            return False

    def _resolve_conflict(self) -> bool:
        """Resolve conflicts by pulling and rebasing."""
        try:
            self.logger.info("Attempting to resolve conflict via pull --rebase")
            self._run_git("pull", "--rebase", "origin", self.cfg["branch"])
            return self.push()
        except subprocess.CalledProcessError as exc:
            self.logger.error(f"Conflict resolution failed: {exc.stderr}")
            return False

    def get_file_path(self, rel_path: str) -> Path:
        """Get absolute path for a relative path in the repo."""
        return self.repo_path / rel_path


# ──────────────────────────────────────────────────────────────────────────────
# CONTENT SYNC
# ──────────────────────────────────────────────────────────────────────────────

class ContentSyncModule:
    """Syncs blog posts and content to profitenginev5."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_blog_post(self, title: str, content: str, date: Optional[str] = None) -> bool:
        """
        Sync a blog post to profitenginev5/content/trading-results/.

        Args:
            title: Blog post title
            content: Markdown content
            date: Date string (YYYY-MM-DD); defaults to today
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Create filename from title
        slug = title.lower().replace(" ", "-")[:50]
        filename = f"{date}-{slug}.md"
        rel_path = f"content/trading-results/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info(f"Synced blog post: {rel_path}")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync blog post {rel_path}: {exc}")
            return False

        return False

    def sync_blog_posts_batch(self, posts: List[Dict[str, str]]) -> int:
        """
        Sync multiple blog posts.

        Args:
            posts: List of dicts with 'title', 'content', optional 'date'

        Returns:
            Number of successfully synced posts
        """
        count = 0
        for post in posts:
            if self.sync_blog_post(
                post.get("title", "Untitled"),
                post.get("content", ""),
                post.get("date")
            ):
                count += 1
        return count


# ──────────────────────────────────────────────────────────────────────────────
# METRICS SYNC
# ──────────────────────────────────────────────────────────────────────────────

class MetricsSyncModule:
    """Syncs trading metrics and performance data to profitenginev5."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_daily_metrics(
        self,
        pnl_dollars: float,
        win_rate: float,
        trades_count: int,
        customer_count: int,
        revenue_dollars: float,
        date: Optional[str] = None,
    ) -> bool:
        """
        Sync daily metrics to profitenginev5/metrics/.

        Args:
            pnl_dollars: Daily P&L in dollars
            win_rate: Win rate percentage (0-100)
            trades_count: Number of trades executed
            customer_count: Total active customers
            revenue_dollars: Daily revenue
            date: Date string (YYYY-MM-DD); defaults to today
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metrics = {
            "date": date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trading": {
                "pnl_dollars": float(pnl_dollars),
                "win_rate_percent": float(win_rate),
                "trades_count": int(trades_count),
            },
            "business": {
                "customer_count": int(customer_count),
                "revenue_dollars": float(revenue_dollars),
            },
        }

        filename = f"{date}-metrics.json"
        rel_path = f"metrics/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info(f"Synced metrics: {rel_path}")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync metrics {rel_path}: {exc}")
            return False

        return False

    def sync_metrics_batch(self, metrics_list: List[Dict[str, Any]]) -> int:
        """
        Sync multiple days of metrics.

        Args:
            metrics_list: List of metric dicts with keys:
                          pnl_dollars, win_rate, trades_count, customer_count, revenue_dollars, date

        Returns:
            Number of successfully synced metric files
        """
        count = 0
        for metric in metrics_list:
            if self.sync_daily_metrics(
                metric.get("pnl_dollars", 0),
                metric.get("win_rate", 0),
                metric.get("trades_count", 0),
                metric.get("customer_count", 0),
                metric.get("revenue_dollars", 0),
                metric.get("date"),
            ):
                count += 1
        return count


# ──────────────────────────────────────────────────────────────────────────────
# CASE STUDY SYNC
# ──────────────────────────────────────────────────────────────────────────────

class CaseStudySyncModule:
    """Syncs customer success stories and case studies to profitenginev5."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_case_study(
        self,
        customer_id: str,
        anonymized_name: str,
        roi_percent: float,
        strategy: str,
        testimonial: str,
        results: Dict[str, Any],
    ) -> bool:
        """
        Sync a customer case study to profitenginev5/case-studies/.

        Args:
            customer_id: Unique customer identifier
            anonymized_name: Anonymized customer name
            roi_percent: Return on investment percentage
            strategy: Strategy used (e.g., "Day Trading", "Swing Trading")
            testimonial: Customer quote
            results: Dict with performance metrics
        """
        case_study = {
            "customer_id": customer_id,
            "name": anonymized_name,
            "roi_percent": float(roi_percent),
            "strategy": strategy,
            "testimonial": testimonial,
            "results": results,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }

        # Create markdown content
        content = f"""# {anonymized_name} — {strategy}

**ROI:** {roi_percent}%

## Testimonial

> {testimonial}

## Results

"""
        for key, value in results.items():
            content += f"- **{key}:** {value}\n"

        filename = f"{customer_id}.md"
        rel_path = f"case-studies/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            # Also store JSON metadata
            json_rel_path = f"case-studies/{customer_id}.json"
            json_file_path = self.git.get_file_path(json_rel_path)
            json_file_path.write_text(json.dumps(case_study, indent=2), encoding="utf-8")

            self.git.add_file(rel_path)
            self.git.add_file(json_rel_path)
            self.logger.info(f"Synced case study: {rel_path}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to sync case study {rel_path}: {exc}")
            return False

        return False


# ──────────────────────────────────────────────────────────────────────────────
# SOCIAL PERFORMANCE SYNC
# ──────────────────────────────────────────────────────────────────────────────

class SocialPerformanceSyncModule:
    """Syncs social media engagement and performance to profitenginev5."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_social_metrics(
        self,
        platform: str,
        post_id: str,
        title: str,
        engagement: Dict[str, int],
        date: Optional[str] = None,
    ) -> bool:
        """
        Sync social media engagement metrics.

        Args:
            platform: Platform name (twitter, linkedin, youtube, etc.)
            post_id: Unique post identifier on the platform
            title: Post title
            engagement: Dict with likes, shares, comments, views
            date: Date string; defaults to today
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        metrics = {
            "platform": platform,
            "post_id": post_id,
            "title": title,
            "date": date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engagement": engagement,
        }

        # Append to engagement log
        rel_path = "analytics/social-engagement.jsonl"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Append JSONL format (one JSON object per line)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics) + "\n")

            self.git.add_file(rel_path)
            self.logger.info(f"Synced social metrics for {platform}:{post_id}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to sync social metrics: {exc}")
            return False

        return False

    def sync_engagement_summary(
        self,
        summary: Dict[str, Any],
        date: Optional[str] = None,
    ) -> bool:
        """
        Sync aggregated social engagement summary.

        Args:
            summary: Dict with platform-level aggregations
            date: Date string; defaults to today
        """
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        data = {
            "date": date,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **summary,
        }

        filename = f"{date}-summary.json"
        rel_path = f"analytics/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info(f"Synced engagement summary: {rel_path}")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync engagement summary: {exc}")
            return False

        return False


# ──────────────────────────────────────────────────────────────────────────────
# LANDING PAGE DATA SYNC
# ──────────────────────────────────────────────────────────────────────────────

class LandingPageSyncModule:
    """Syncs landing page data (hero numbers, testimonials, conversion data)."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_hero_metrics(
        self,
        customers_active: int,
        trades_executed: int,
        dollars_managed: float,
        success_rate: float,
    ) -> bool:
        """
        Sync hero section metrics for landing page.

        Args:
            customers_active: Number of active customers
            trades_executed: Total trades executed
            dollars_managed: Total AUM
            success_rate: Success/win rate percentage
        """
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "customers_active": int(customers_active),
            "trades_executed": int(trades_executed),
            "dollars_managed": float(dollars_managed),
            "success_rate_percent": float(success_rate),
        }

        rel_path = "landing-page/hero-metrics.json"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info("Synced hero metrics")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync hero metrics: {exc}")
            return False

        return False

    def sync_testimonials(self, testimonials: List[Dict[str, str]]) -> bool:
        """
        Sync customer testimonials.

        Args:
            testimonials: List of dicts with 'name', 'quote', 'role', 'image_url'
        """
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "testimonials": testimonials,
        }

        rel_path = "landing-page/testimonials.json"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info("Synced testimonials")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync testimonials: {exc}")
            return False

        return False

    def sync_conversion_data(self, conversion_data: Dict[str, Any]) -> bool:
        """
        Sync landing page conversion analytics.

        Args:
            conversion_data: Dict with metrics, funnels, etc.
        """
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **conversion_data,
        }

        filename = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-conversions.json"
        rel_path = f"landing-page/conversions/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info(f"Synced conversion data: {rel_path}")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync conversion data: {exc}")
            return False

        return False


# ──────────────────────────────────────────────────────────────────────────────
# EMAIL TEMPLATE SYNC
# ──────────────────────────────────────────────────────────────────────────────

class EmailTemplateSyncModule:
    """Syncs email templates, segments, and engagement tracking."""

    def __init__(self, git_manager: GitSyncManager):
        self.git = git_manager
        self.logger = _init_logger()

    def sync_template(
        self,
        template_name: str,
        html_content: str,
        text_content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Sync an email template.

        Args:
            template_name: Template name (e.g., 'daily-alert')
            html_content: HTML version
            text_content: Plain text version
            metadata: Template metadata (subject, preview, etc.)
        """
        rel_path_html = f"emails/{template_name}.html"
        rel_path_txt = f"emails/{template_name}.txt"
        rel_path_json = f"emails/{template_name}.json"

        try:
            # HTML
            html_file = self.git.get_file_path(rel_path_html)
            html_file.parent.mkdir(parents=True, exist_ok=True)
            html_file.write_text(html_content, encoding="utf-8")

            # Text
            txt_file = self.git.get_file_path(rel_path_txt)
            txt_file.write_text(text_content, encoding="utf-8")

            # Metadata
            meta = {
                **metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            json_file = self.git.get_file_path(rel_path_json)
            json_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

            self.git.add_file(rel_path_html)
            self.git.add_file(rel_path_txt)
            self.git.add_file(rel_path_json)
            self.logger.info(f"Synced email template: {template_name}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to sync email template {template_name}: {exc}")
            return False

        return False

    def sync_segments(self, segments: Dict[str, List[str]]) -> bool:
        """
        Sync customer segments for email campaigns.

        Args:
            segments: Dict mapping segment name to customer IDs
        """
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "segments": segments,
        }

        rel_path = "emails/segments.json"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info("Synced customer segments")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync segments: {exc}")
            return False

        return False

    def sync_engagement_tracking(
        self,
        campaign_id: str,
        opens: int,
        clicks: int,
        conversions: int,
        unsubscribes: int,
    ) -> bool:
        """
        Sync email engagement metrics.

        Args:
            campaign_id: Campaign identifier
            opens: Number of opens
            clicks: Number of clicks
            conversions: Number of conversions
            unsubscribes: Number of unsubscribes
        """
        metrics = {
            "campaign_id": campaign_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opens": int(opens),
            "clicks": int(clicks),
            "conversions": int(conversions),
            "unsubscribes": int(unsubscribes),
        }

        filename = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{campaign_id}.json"
        rel_path = f"emails/engagement/{filename}"

        try:
            file_path = self.git.get_file_path(rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

            if self.git.add_file(rel_path):
                self.logger.info(f"Synced engagement tracking for campaign {campaign_id}")
                return True
        except Exception as exc:
            self.logger.error(f"Failed to sync engagement tracking: {exc}")
            return False

        return False


# ──────────────────────────────────────────────────────────────────────────────
# MAIN SYNC ORCHESTRATOR
# ──────────────────────────────────────────────────────────────────────────────

class ProfitEngineV5Sync:
    """Main orchestrator for syncing all content and metrics to profitenginev5."""

    def __init__(self, cfg: Optional[Dict[str, str]] = None):
        self.cfg = cfg or _cfg()
        self.logger = _init_logger()
        self.git = GitSyncManager(self.cfg)

        # Module instances
        self.content = ContentSyncModule(self.git)
        self.metrics = MetricsSyncModule(self.git)
        self.case_studies = CaseStudySyncModule(self.git)
        self.social = SocialPerformanceSyncModule(self.git)
        self.landing_page = LandingPageSyncModule(self.git)
        self.email = EmailTemplateSyncModule(self.git)

    def initialize(self) -> bool:
        """Initialize sync engine (clone repo if needed, configure git)."""
        if not self.git.ensure_cloned():
            self.logger.error("Failed to initialize git repository")
            return False
        return True

    def sync(
        self,
        commit_message: str = "chore: sync daily trading results and metrics",
        push: bool = True,
    ) -> bool:
        """
        Execute sync: commit all staged changes and push to origin.

        Args:
            commit_message: Commit message to use
            push: Whether to push after commit

        Returns:
            True if sync succeeded
        """
        # Fetch latest first
        self.git.fetch_latest()

        # Check for changes
        if not self.git.has_changes():
            self.logger.info("No changes to sync")
            return True

        # Commit
        if not self.git.commit(commit_message):
            self.logger.error("Commit failed")
            return False

        # Push (if requested)
        if push:
            if not self.git.push(self.cfg["branch"]):
                self.logger.error("Push failed")
                return False

        # Log sync event
        self._log_sync_event("success", commit_message)
        return True

    def _log_sync_event(self, status: str, message: str) -> None:
        """Log a sync event for audit trail."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "message": message,
            "repo_url": self.cfg["repo_url"],
            "branch": self.cfg["branch"],
        }
        self.logger.info(f"Sync event: {json.dumps(log_entry)}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI & EXAMPLES
# ──────────────────────────────────────────────────────────────────────────────

def example_full_daily_sync() -> None:
    """Example: Full daily sync with all data types."""
    sync = ProfitEngineV5Sync()

    if not sync.initialize():
        logger.error("Failed to initialize sync")
        return

    # Sync a blog post
    sync.content.sync_blog_post(
        title="Markets Hit Record High Today",
        content="# Markets Hit Record High\n\nToday was a great day for trading...",
    )

    # Sync metrics
    sync.metrics.sync_daily_metrics(
        pnl_dollars=1250.50,
        win_rate=67.5,
        trades_count=12,
        customer_count=450,
        revenue_dollars=8900.00,
    )

    # Sync case study
    sync.case_studies.sync_case_study(
        customer_id="cust_001",
        anonymized_name="Client A",
        roi_percent=45.5,
        strategy="Day Trading",
        testimonial="ProfitEngine helped me increase my returns by 45%!",
        results={
            "Starting Balance": "$10,000",
            "Ending Balance": "$14,550",
            "Trades": "125",
            "Avg Win": "$45.50",
        },
    )

    # Sync social metrics
    sync.social.sync_social_metrics(
        platform="twitter",
        post_id="tweet_12345",
        title="New trading strategy",
        engagement={"likes": 250, "retweets": 75, "replies": 30},
    )

    # Sync landing page data
    sync.landing_page.sync_hero_metrics(
        customers_active=450,
        trades_executed=8900,
        dollars_managed=4500000.00,
        success_rate=67.5,
    )

    sync.landing_page.sync_testimonials([
        {
            "name": "Client A",
            "quote": "This tool changed my trading",
            "role": "Day Trader",
            "image_url": "/images/client-a.jpg",
        }
    ])

    # Sync email template
    sync.email.sync_template(
        template_name="daily-alert",
        html_content="<h1>Daily Trading Alert</h1>",
        text_content="Daily Trading Alert",
        metadata={
            "subject": "Your Daily Trading Alert",
            "preview": "Check your daily results",
        },
    )

    # Commit and push
    if sync.sync():
        logger.info("Daily sync completed successfully")
    else:
        logger.error("Daily sync failed")


def example_metrics_only() -> None:
    """Example: Sync metrics only."""
    sync = ProfitEngineV5Sync()

    if not sync.initialize():
        return

    sync.metrics.sync_daily_metrics(
        pnl_dollars=1250.50,
        win_rate=67.5,
        trades_count=12,
        customer_count=450,
        revenue_dollars=8900.00,
    )

    if sync.sync():
        logger.info("Metrics sync completed")


if __name__ == "__main__":
    # Example usage
    example_full_daily_sync()
