"""
APScheduler integration for ProfitEngine automated workflows.
Replaces n8n with native Python scheduling using AsyncIOScheduler.

Architecture:
  - Uses AsyncIOScheduler (not BackgroundScheduler) to support async jobs
  - Runs natively in FastAPI's event loop for proper async/await execution
  - Jobs execute in the same process as the API (no HTTP overhead)

Workflows:
  - Daily content pipeline at 7am UTC (content-pipeline agent + error recovery)
  - Webhook endpoints for external triggers (blog crosspost, call logging, etc.)

Why AsyncIOScheduler?
  - The scheduler must execute async functions (run_daily_content_pipeline)
  - BackgroundScheduler only supports sync functions → would silently fail
  - AsyncIOScheduler integrates with FastAPI's event loop perfectly
  - No separate thread pool or process needed → simpler deployment
  - Lower memory footprint than thread-pool alternatives
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance."""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.configure(
            job_defaults={'coalesce': True, 'max_instances': 1},
            timezone='UTC'
        )
    return scheduler


async def execute_agent(
    objective: str,
    agent_id: str = "local-research",
    namespace: str = "scheduler",
    system_declaration: str = "Registry-governed scheduled execution.",
) -> Dict[str, Any]:
    """
    Execute an agent via the registry (scheduler context, no HTTP).
    Imported locally to avoid circular dependencies at module load time.
    """
    from .api import _execute_agent_internal, ExecuteRequest

    req = ExecuteRequest(
        objective=objective,
        agent_id=agent_id,
        namespace=namespace,
        system_declaration=system_declaration,
        actor="scheduler",
    )
    return await _execute_agent_internal(req)


async def run_daily_content_pipeline() -> None:
    """
    Daily content pipeline at 7am UTC.
    1. Run content-pipeline agent (scan trends, publish monetized article)
    2. If failed, run lifelong-catch-correct to review and fix errors
    """
    logger.info(f"[scheduler] Starting daily content pipeline at {datetime.now(timezone.utc)}")

    try:
        result = await execute_agent(
            objective="scan trending topics and publish one monetized article",
            agent_id="content-pipeline",
            namespace="scheduler-daily-pipeline",
        )

        logger.info(f"[scheduler] Content pipeline result: {result.get('status')}")

        if result.get("status") != "success":
            logger.warning("[scheduler] Content pipeline failed, running error recovery")
            recovery = await execute_agent(
                objective="review yesterday content pipeline run and correct any errors",
                agent_id="lifelong-catch-correct",
                namespace="scheduler-daily-recovery",
            )
            logger.info(f"[scheduler] Error recovery completed: {recovery.get('status')}")
        else:
            logger.info("[scheduler] Content pipeline succeeded")

    except Exception as e:
        logger.error(f"[scheduler] Daily content pipeline error: {e}", exc_info=True)


def add_daily_content_pipeline(sched: AsyncIOScheduler) -> None:
    """Register the 7am UTC daily content pipeline job."""
    sched.add_job(
        run_daily_content_pipeline,
        CronTrigger(hour=7, minute=0, timezone='UTC'),
        id='content-pipeline-daily',
        name='Daily Content Pipeline (7am UTC)',
        replace_existing=True,
    )
    logger.info("[scheduler] Registered: Daily Content Pipeline at 07:00 UTC")


def start_scheduler() -> None:
    """Start the AsyncIOScheduler and register all jobs."""
    sched = get_scheduler()

    if sched.running:
        logger.warning("[scheduler] Scheduler already running")
        return

    logger.info("[scheduler] Starting AsyncIOScheduler...")

    add_daily_content_pipeline(sched)

    sched.start()
    logger.info(f"[scheduler] AsyncIOScheduler started. Jobs: {len(sched.get_jobs())}")

    for job in sched.get_jobs():
        logger.info(f"  - {job.id}: {job.name} → {job.trigger}")


def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    sched = get_scheduler()
    if sched.running:
        logger.info("[scheduler] Stopping scheduler...")
        sched.shutdown(wait=True)
        logger.info("[scheduler] Scheduler stopped")


def get_jobs_status() -> Dict[str, Any]:
    """Return status of all scheduled jobs."""
    sched = get_scheduler()
    jobs = []
    for job in sched.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "trigger": str(job.trigger),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {
        "scheduler_running": sched.running,
        "jobs_count": len(jobs),
        "jobs": jobs,
    }
