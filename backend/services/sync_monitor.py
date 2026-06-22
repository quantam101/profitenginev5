"""
Daily Sync Monitoring & Health Check

Real-time monitoring of all 9 daily revenue syncs with:
- Health status tracking
- Failure alerts
- Performance metrics
- Auto-recovery triggers
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from enum import Enum


class SyncStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    FAILED = "failed"
    RECOVERING = "recovering"


class SyncMonitor:
    """Monitor all daily sync jobs"""

    def __init__(self, db=None):
        self.db = db
        self.syncs = [
            {"time": "08:00", "name": "YouTube AdSense", "critical": True},
            {"time": "09:00", "name": "Stripe Payments", "critical": True},
            {"time": "10:00", "name": "Gumroad Sales", "critical": True},
            {"time": "11:00", "name": "POD Designer", "critical": True},
            {"time": "13:00", "name": "Federal Proposals", "critical": False},
            {"time": "14:00", "name": "Revenue Intelligence", "critical": False},
            {"time": "15:00", "name": "Offer Engineering", "critical": False},
            {"time": "15:30", "name": "Consulting Services", "critical": False},
            {"time": "16:00", "name": "Sponsorships", "critical": False},
            {"time": "16:30", "name": "Content SEO", "critical": False},
            {"time": "17:00", "name": "Skool Community", "critical": False},
        ]

    async def check_sync_health(self) -> Dict[str, Any]:
        """Check health of all syncs"""

        if not self.db:
            return {"status": "offline", "syncs": []}

        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "syncs": [],
            "critical_failures": [],
            "warnings": [],
            "recovery_needed": []
        }

        for sync in self.syncs:
            # Get last sync result
            sync_log = await self.db.sync_logs.find_one(
                {"sync_name": sync["name"]},
                sort=[("timestamp", -1)]
            )

            status_obj = {
                "name": sync["name"],
                "scheduled_time": sync["time"],
                "critical": sync["critical"],
                "status": "unknown",
                "last_run": None,
                "next_run": None,
                "health": 100
            }

            if sync_log:
                status_obj["last_run"] = sync_log.get("timestamp")
                status_obj["status"] = sync_log.get("status", "unknown")

                # Calculate health score
                if sync_log.get("status") == "success":
                    status_obj["health"] = 100
                    status_obj["status"] = SyncStatus.HEALTHY.value
                elif sync_log.get("status") == "failed":
                    status_obj["health"] = 0
                    status_obj["status"] = SyncStatus.FAILED.value
                    health_report["overall_status"] = "warning"

                    if sync["critical"]:
                        health_report["critical_failures"].append(sync["name"])
                        health_report["recovery_needed"].append(sync["name"])
                    else:
                        health_report["warnings"].append(sync["name"])

            health_report["syncs"].append(status_obj)

        return health_report

    async def log_sync_result(
        self,
        sync_name: str,
        status: str,
        duration_seconds: float,
        records_processed: int = 0,
        error_message: str = None
    ) -> None:
        """Log sync execution result"""

        if not self.db:
            return

        log_entry = {
            "sync_name": sync_name,
            "timestamp": datetime.utcnow(),
            "status": status,
            "duration_seconds": duration_seconds,
            "records_processed": records_processed,
            "error_message": error_message,
            "revenue_collected_usd": 0  # Will be updated by actual sync
        }

        await self.db.sync_logs.insert_one(log_entry)

    async def trigger_recovery(self, sync_name: str) -> Dict[str, Any]:
        """Trigger auto-recovery for failed sync"""

        recovery = {
            "sync_name": sync_name,
            "triggered_at": datetime.utcnow().isoformat(),
            "status": "initiated",
            "retry_count": 0,
            "max_retries": 3
        }

        if self.db:
            await self.db.recovery_jobs.insert_one(recovery)

        return recovery

    async def get_sync_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get sync performance metrics"""

        if not self.db:
            return {}

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get success rate
        total_syncs = await self.db.sync_logs.count_documents(
            {"timestamp": {"$gte": start_date}}
        )

        successful = await self.db.sync_logs.count_documents(
            {"timestamp": {"$gte": start_date}, "status": "success"}
        )

        # Get average duration
        pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": None,
                "avg_duration": {"$avg": "$duration_seconds"},
                "total_records": {"$sum": "$records_processed"}
            }}
        ]

        agg_result = await self.db.sync_logs.aggregate(pipeline).to_list(None)

        metrics = {
            "period_days": days,
            "total_sync_runs": total_syncs,
            "successful_runs": successful,
            "success_rate": (successful / total_syncs * 100) if total_syncs > 0 else 0,
            "avg_duration_seconds": agg_result[0]["avg_duration"] if agg_result else 0,
            "total_records_processed": agg_result[0]["total_records"] if agg_result else 0
        }

        return metrics


async def monitor_daily_syncs_job(db=None):
    """Background job to monitor all syncs and alert on failures"""

    monitor = SyncMonitor(db=db)

    health = await monitor.check_sync_health()
    metrics = await monitor.get_sync_metrics(days=1)

    print(f"Sync Health Check: {health['overall_status']}")
    print(f"Success Rate: {metrics.get('success_rate', 0):.1f}%")

    # Trigger recovery for critical failures
    for failed_sync in health.get("critical_failures", []):
        await monitor.trigger_recovery(failed_sync)
        print(f"Recovery triggered for: {failed_sync}")

    return {
        "health": health,
        "metrics": metrics
    }
