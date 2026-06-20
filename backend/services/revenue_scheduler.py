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


def init_revenue_scheduler() -> RevenueScheduler:
    """Initialize and start the revenue scheduler.

    Adds default sync jobs and starts the scheduler.

    Returns:
        Initialized RevenueScheduler instance.
    """
    scheduler = get_scheduler()

    # Add default jobs
    scheduler.add_youtube_sync(hour=8, minute=0)    # 08:00 UTC
    scheduler.add_stripe_sync(hour=9, minute=0)     # 09:00 UTC
    scheduler.add_gumroad_sync(hour=10, minute=0)   # 10:00 UTC

    scheduler.start()

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
