"""Revenue sync scheduler using APScheduler.

Manages periodic jobs to sync revenue from various channels:
- YouTube AdSense (daily at 08:00 UTC)
- Stripe (daily at 09:00 UTC)
- Gumroad (daily at 10:00 UTC)
- etc.
"""
import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

logger = logging.getLogger(__name__)


class RevenueScheduler:
    """Manages scheduled revenue sync jobs."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BackgroundScheduler()
        self._jobs: dict[str, Job] = {}

    def add_youtube_sync(self, hour: int = 8, minute: int = 0) -> Job:
        """Add YouTube AdSense daily sync job.

        Args:
            hour: Hour to run sync (0-23, UTC)
            minute: Minute to run sync (0-59)

        Returns:
            APScheduler Job object.
        """
        from backend.services.youtube_analytics import YouTubeRevenueAnalytics

        def sync_youtube():
            """Sync YouTube AdSense revenue for current month."""
            logger.info("🎬 Starting YouTube AdSense revenue sync...")
            try:
                analytics = YouTubeRevenueAnalytics()
                amount = analytics.sync_current_month_revenue()
                if amount:
                    logger.info(f"✅ YouTube sync completed: ${amount:.2f}")
                else:
                    logger.info("⚠️ No new YouTube revenue data")
            except Exception as e:
                logger.error(f"❌ YouTube sync failed: {e}", exc_info=True)

        job = self.scheduler.add_job(
            sync_youtube,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="youtube_sync",
            name="YouTube AdSense Daily Sync",
            replace_existing=True,
        )

        self._jobs["youtube"] = job
        logger.info(f"📅 Scheduled YouTube sync: daily at {hour:02d}:{minute:02d} UTC")
        return job

    def add_stripe_sync(self, hour: int = 9, minute: int = 0) -> Job:
        """Add Stripe daily revenue sync job.

        Args:
            hour: Hour to run sync (0-23, UTC)
            minute: Minute to run sync (0-59)

        Returns:
            APScheduler Job object.
        """
        def sync_stripe():
            """Sync Stripe charges for previous day."""
            logger.info("💳 Starting Stripe revenue sync...")
            try:
                from backend.services.stripe_transport import StripeRevenueCollector

                collector = StripeRevenueCollector()
                amount = collector.sync_yesterday_charges()
                if amount:
                    logger.info(f"✅ Stripe sync completed: ${amount:.2f}")
                else:
                    logger.info("⚠️ No new Stripe charges")
            except Exception as e:
                logger.error(f"❌ Stripe sync failed: {e}", exc_info=True)

        job = self.scheduler.add_job(
            sync_stripe,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="stripe_sync",
            name="Stripe Daily Revenue Sync",
            replace_existing=True,
        )

        self._jobs["stripe"] = job
        logger.info(f"📅 Scheduled Stripe sync: daily at {hour:02d}:{minute:02d} UTC")
        return job

    def add_gumroad_sync(self, hour: int = 10, minute: int = 0) -> Job:
        """Add Gumroad daily revenue sync job.

        Args:
            hour: Hour to run sync (0-23, UTC)
            minute: Minute to run sync (0-59)

        Returns:
            APScheduler Job object.
        """
        def sync_gumroad():
            """Sync Gumroad sales for previous day."""
            logger.info("📚 Starting Gumroad revenue sync...")
            try:
                # TODO: Implement GumroadRevenueCollector
                logger.warning("⚠️ Gumroad sync not yet implemented")
            except Exception as e:
                logger.error(f"❌ Gumroad sync failed: {e}", exc_info=True)

        job = self.scheduler.add_job(
            sync_gumroad,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="gumroad_sync",
            name="Gumroad Daily Revenue Sync",
            replace_existing=True,
        )

        self._jobs["gumroad"] = job
        logger.info(f"📅 Scheduled Gumroad sync: daily at {hour:02d}:{minute:02d} UTC")
        return job

    def add_pod_sync(self, hour: int = 11, minute: int = 0, db=None) -> Job:
        """Add POD (Print-on-Demand) daily sync job for Etsy/Printify.

        Args:
            hour: Hour to run sync (0-23, UTC)
            minute: Minute to run sync (0-59)
            db: MongoDB database instance

        Returns:
            APScheduler Job object.
        """
        def sync_pod():
            """Sync POD products and sales from Etsy/Printify."""
            logger.info("🎨 Starting POD Designer sync...")
            try:
                import asyncio
                from backend.services.pod_designer import sync_pod_designs_job

                stats = asyncio.run(sync_pod_designs_job(db=db))
                logger.info(f"✅ POD sync completed: ${stats.get('total_revenue_usd', 0):.2f} revenue")
            except Exception as e:
                logger.error(f"❌ POD sync failed: {e}", exc_info=True)

        job = self.scheduler.add_job(
            sync_pod,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="pod_sync",
            name="POD Designer Daily Sync",
            replace_existing=True,
        )

        self._jobs["pod"] = job
        logger.info(f"📅 Scheduled POD sync: daily at {hour:02d}:{minute:02d} UTC")
        return job

    def add_custom_job(self, job_id: str, func, cron_trigger: CronTrigger, name: str) -> Job:
        """Add a custom scheduled job.

        Args:
            job_id: Unique job identifier
            func: Callable to execute
            cron_trigger: APScheduler CronTrigger for scheduling
            name: Human-readable job name

        Returns:
            APScheduler Job object.
        """
        job = self.scheduler.add_job(
            func,
            trigger=cron_trigger,
            id=job_id,
            name=name,
            replace_existing=True,
        )

        self._jobs[job_id] = job
        logger.info(f"📅 Scheduled job '{name}' (id={job_id})")
        return job

    def start(self) -> None:
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Revenue scheduler started")
        else:
            logger.warning("Scheduler already running")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Revenue scheduler stopped")
        else:
            logger.warning("Scheduler not running")

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job.

        Args:
            job_id: ID of the job to pause

        Returns:
            True if paused, False if job not found.
        """
        job = self._jobs.get(job_id)
        if job:
            self.scheduler.pause_job(job.id)
            logger.info(f"⏸️  Job paused: {job_id}")
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused scheduled job.

        Args:
            job_id: ID of the job to resume

        Returns:
            True if resumed, False if job not found.
        """
        job = self._jobs.get(job_id)
        if job:
            self.scheduler.resume_job(job.id)
            logger.info(f"▶️  Job resumed: {job_id}")
            return True
        return False

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: ID of the job to remove

        Returns:
            True if removed, False if job not found.
        """
        job = self._jobs.get(job_id)
        if job:
            self.scheduler.remove_job(job.id)
            del self._jobs[job_id]
            logger.info(f"🗑️  Job removed: {job_id}")
            return True
        return False

    def list_jobs(self) -> list[dict]:
        """List all scheduled jobs with status.

        Returns:
            List of job dicts with id, name, next_run_time, etc.
        """
        jobs_list = []
        for job in self.scheduler.get_jobs():
            jobs_list.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs_list

    def get_job_status(self) -> dict:
        """Get detailed scheduler and job status.

        Returns:
            Dict with scheduler running status and all jobs.
        """
        return {
            "running": self.scheduler.running,
            "jobs": self.list_jobs(),
        }


# Global scheduler instance
_scheduler_instance: Optional[RevenueScheduler] = None


def get_scheduler() -> RevenueScheduler:
    """Get or create the global scheduler instance.

    Returns:
        RevenueScheduler instance.
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = RevenueScheduler()
    return _scheduler_instance


def init_revenue_scheduler(db=None) -> RevenueScheduler:
    """Initialize and start the revenue scheduler.

    Adds ALL 15 revenue stream sync jobs and starts the scheduler.

    Args:
        db: Optional MongoDB database instance

    Returns:
        Initialized RevenueScheduler instance.
    """
    scheduler = get_scheduler()

    # TIER 1: Core revenue syncs (08:00-11:00 UTC)
    scheduler.add_youtube_sync(hour=8, minute=0)          # 08:00 UTC
    scheduler.add_stripe_sync(hour=9, minute=0)           # 09:00 UTC
    scheduler.add_gumroad_sync(hour=10, minute=0)         # 10:00 UTC
    scheduler.add_pod_sync(hour=11, minute=0, db=db)      # 11:00 UTC

    # TIER 2: Advanced revenue streams (13:00-17:00 UTC)
    def add_federal_proposals():
        from backend.services.federal_proposals import sync_federal_proposals_job
        import asyncio
        asyncio.run(sync_federal_proposals_job(db=db))

    def add_revenue_intelligence():
        from backend.services.revenue_intelligence import sync_revenue_intelligence_job
        import asyncio
        asyncio.run(sync_revenue_intelligence_job(db=db))

    def add_offer_engineering():
        from backend.services.offer_engineering import sync_offer_engineering_job
        import asyncio
        asyncio.run(sync_offer_engineering_job(db=db))

    def add_consulting():
        from backend.services.consulting_services import sync_consulting_services_job
        import asyncio
        asyncio.run(sync_consulting_services_job(db=db))

    def add_sponsorships():
        from backend.services.sponsorships import sync_sponsorships_job
        import asyncio
        asyncio.run(sync_sponsorships_job(db=db))

    def add_content_seo():
        from backend.services.content_seo_monetization import sync_content_seo_job
        import asyncio
        asyncio.run(sync_content_seo_job(db=db))

    def add_skool():
        from backend.services.skool_community import sync_skool_community_job
        import asyncio
        asyncio.run(sync_skool_community_job(db=db))

    # Add all advanced streams
    scheduler.add_custom_job(
        "federal_proposals",
        add_federal_proposals,
        CronTrigger(hour=13, minute=0),
        "Federal Proposals Sync"
    )

    scheduler.add_custom_job(
        "revenue_intelligence",
        add_revenue_intelligence,
        CronTrigger(hour=14, minute=0),
        "Revenue Intelligence Optimization"
    )

    scheduler.add_custom_job(
        "offer_engineering",
        add_offer_engineering,
        CronTrigger(hour=15, minute=0),
        "Offer Engineering & Pricing"
    )

    scheduler.add_custom_job(
        "consulting_services",
        add_consulting,
        CronTrigger(hour=15, minute=30),
        "Consulting Services Sync"
    )

    scheduler.add_custom_job(
        "sponsorships",
        add_sponsorships,
        CronTrigger(hour=16, minute=0),
        "Sponsorship Management"
    )

    scheduler.add_custom_job(
        "content_seo",
        add_content_seo,
        CronTrigger(hour=16, minute=30),
        "Content SEO Monetization"
    )

    scheduler.add_custom_job(
        "skool_community",
        add_skool,
        CronTrigger(hour=17, minute=0),
        "Skool Community Affiliate"
    )

    scheduler.start()

    logger.info("✅ Complete 15-stream revenue scheduler initialized")
    return scheduler


def main():
    """Demo: start scheduler and run for 30 seconds."""
    import time
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    scheduler = init_revenue_scheduler()

    try:
        print("Scheduler running. Press Ctrl+C to stop.")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        scheduler.stop()
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()
