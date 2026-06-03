"""
EAOS Cluster Master — Central task orchestrator.
Manages VIDEO / SOCIAL / POD lanes with SQLite queue + async workers.
"""
import os
import sys
import json
import sqlite3
import asyncio
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("EAOS.ClusterMaster")

DB_PATH = os.environ.get("EAOS_DB_PATH", "./datacenter/cluster_queue.db")


@dataclass
class ClusterTask:
    task_id: int
    agent_type: str
    payload: Dict[str, Any]
    priority: int
    retry_count: int


class ClusterTaskQueue:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cluster_tasks (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_type    TEXT    NOT NULL,
                    payload       TEXT    NOT NULL,
                    priority      INTEGER DEFAULT 1,
                    retry_count   INTEGER DEFAULT 0,
                    status        TEXT    DEFAULT 'PENDING',
                    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def enqueue(self, agent_type: str, payload: Dict[str, Any], priority: int = 1) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO cluster_tasks (agent_type, payload, priority) VALUES (?, ?, ?)",
                (agent_type, json.dumps(payload), priority),
            )
            conn.commit()
            task_id = cur.lastrowid
        logger.info(f"[Queue] Task #{task_id} registered → {agent_type} (priority={priority})")
        return task_id

    def fetch_pending(self, batch: int = 5) -> List[ClusterTask]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """SELECT id, agent_type, payload, priority, retry_count
                   FROM cluster_tasks
                   WHERE status = 'PENDING' AND retry_count < 3
                   ORDER BY priority DESC, id ASC LIMIT ?""",
                (batch,),
            ).fetchall()
        return [ClusterTask(r[0], r[1], json.loads(r[2]), r[3], r[4]) for r in rows]

    def set_status(self, task_id: int, status: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE cluster_tasks SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (status, task_id),
            )
            conn.commit()

    def increment_retry(self, task_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE cluster_tasks SET retry_count=retry_count+1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (task_id,),
            )
            conn.commit()


class GlobalClusterMaster:
    def __init__(self):
        self.queue = ClusterTaskQueue()
        self.vram_semaphore = asyncio.Semaphore(1)

    async def _run_video_lane(self, task: ClusterTask) -> bool:
        async with self.vram_semaphore:
            logger.info(f"[VIDEO Lane] Task #{task.task_id} — acquiring VRAM slot")
            from runtime.eaos.video_engine import UltimateVideoEngine
            engine = UltimateVideoEngine()
            result = await engine.render_isolated_scene(task.task_id, task.payload)
            logger.info(f"[VIDEO Lane] Output: {result}")
            return True

    async def _run_social_lane(self, task: ClusterTask) -> bool:
        logger.info(f"[SOCIAL Lane] Task #{task.task_id} — dispatching to Social Engine")
        from runtime.eaos.social_engine import ProductionSocialEngine, SocialPost
        engine = ProductionSocialEngine()
        post = SocialPost(
            db_id=None,
            platform=task.payload.get("platform", "X"),
            text_content=task.payload.get("text", ""),
            media_path=task.payload.get("media_path"),
        )
        await engine.publish(post)
        return True

    async def _run_pod_lane(self, task: ClusterTask) -> bool:
        logger.info(f"[POD Lane] Task #{task.task_id} — rendering apparel asset")
        from runtime.eaos.image_factory import ProductionImageFactory
        factory = ProductionImageFactory()
        path = factory.construct_apparel_artwork(
            sku=task.payload.get("sku", f"SKU-{task.task_id}"),
            title=task.payload.get("title", "ALREADY HERE"),
            subtitle=task.payload.get("subtitle", "AI-Powered Profit Engine"),
        )
        logger.info(f"[POD Lane] Artwork compiled → {path}")
        # Auto-push to Printify if credentials available
        printify_token = os.environ.get("PRINTIFY_API_TOKEN", "")
        if printify_token:
            from runtime.eaos.printify_client import push_product
            await push_product(path, task.payload, printify_token)
        return True

    async def _process(self, task: ClusterTask) -> None:
        try:
            dispatch = {
                "VIDEO": self._run_video_lane,
                "SOCIAL": self._run_social_lane,
                "POD": self._run_pod_lane,
            }
            fn = dispatch.get(task.agent_type)
            if not fn:
                logger.warning(f"Unknown agent_type: {task.agent_type}")
                self.queue.set_status(task.task_id, "FAILED")
                return
            ok = await fn(task)
            self.queue.set_status(task.task_id, "COMPLETED" if ok else "FAILED")
            logger.info(f"[Master] Task #{task.task_id} → {'COMPLETED' if ok else 'FAILED'}")
        except Exception as exc:
            logger.error(f"[Master] Task #{task.task_id} error: {exc}")
            self.queue.increment_retry(task.task_id)

    async def run_loop(self) -> None:
        logger.info("EAOS Cluster Master ONLINE — status: 100% NOMINAL")
        while True:
            tasks = self.queue.fetch_pending(batch=3)
            if not tasks:
                await asyncio.sleep(2.0)
                continue
            logger.info(f"[Master] Dispatching {len(tasks)} tasks across lanes")
            await asyncio.gather(*[self._process(t) for t in tasks])


if __name__ == "__main__":
    master = GlobalClusterMaster()
    master.queue.enqueue("SOCIAL", {"platform": "X", "text": "EAOS system operational."}, priority=1)
    master.queue.enqueue("POD", {"sku": "EAOS-001", "title": "ALREADY HERE LLC", "subtitle": "AI-Powered Profit Engine 2026"}, priority=2)
    try:
        asyncio.run(master.run_loop())
    except KeyboardInterrupt:
        logger.info("Cluster Master suspended by operator.")
