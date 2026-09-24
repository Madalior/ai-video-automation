"""
Going Merry — Task Broker & Message Queue Manager
=================================================
Corresponds to the REDIS layer in architecture_flowchart.md.

Decouples ingestion (Web App URL input, Stream Monitor completed streams, Whop Scout)
from heavy AI rendering (going_merry.py) and social distribution (Postiz).

Dual-Mode Operation:
1. Cloud / Docker Mode: Uses Redis queue (via REDIS_URL) for distributed workers.
2. Local / Standalone Mode: Falls back to persistent SQLite/SQLAlchemy table (TaskQueueItem)
   with thread-safe concurrency.
"""

import os
import sys
import json
import time
import uuid
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class QueueManager:
    """
    Message Broker and Job Queue interface.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._redis_client = None
        self._lock = threading.Lock()
        self.mode = "sqlite"

        self._init_backend()

    def _init_backend(self):
        """Attempts to connect to Redis if available, else falls back to SQLite."""
        if self.redis_url:
            try:
                import redis
                client = redis.Redis.from_url(self.redis_url, decode_responses=True, socket_timeout=2)
                client.ping()
                self._redis_client = client
                self.mode = "redis"
                print(f"[QUEUE MANAGER] Connected to Redis queue at {self.redis_url}")
                return
            except Exception as e:
                print(f"[QUEUE MANAGER] [INFO] Redis not reachable ({e}). Using persistent DB queue fallback.")

        self.mode = "sqlite"
        print("[QUEUE MANAGER] Active backend: Persistent SQLite Queue (Zero External Dependency)")

    def enqueue(self, job_type: str, payload: Dict[str, Any], priority: int = 0) -> str:
        """
        Pushes a new job into the queue.
        Returns the generated job_id.
        """
        job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "payload": payload,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "status": "queued"
        }

        if self.mode == "redis" and self._redis_client:
            try:
                self._redis_client.rpush("going_merry:task_queue", json.dumps(job_data))
                self._redis_client.hset("going_merry:jobs", job_id, json.dumps(job_data))
                return job_id
            except Exception as e:
                print(f"[QUEUE MANAGER] [WARN] Redis push failed: {e}. Falling back to DB queue.")

        # SQLite Fallback
        with self._lock:
            try:
                from web_app.app import app, db
                from web_app.models import TaskQueueItem
                with app.app_context():
                    item = TaskQueueItem(
                        job_id=job_id,
                        job_type=job_type,
                        payload_json=json.dumps(payload),
                        status="queued",
                        priority=priority,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(item)
                    db.session.commit()
            except Exception as e:
                print(f"[QUEUE MANAGER] [ERROR] Failed to enqueue into DB: {e}")

        return job_id

    def dequeue(self, timeout: int = 2) -> Optional[Dict[str, Any]]:
        """
        Pulls the next available job from the queue (FIFO, prioritized).
        Sets job status to 'processing'.
        """
        if self.mode == "redis" and self._redis_client:
            try:
                item = self._redis_client.blpop("going_merry:task_queue", timeout=timeout)
                if item:
                    _, raw_data = item
                    job = json.loads(raw_data)
                    job["status"] = "processing"
                    job["started_at"] = datetime.utcnow().isoformat()
                    self._redis_client.hset("going_merry:jobs", job["job_id"], json.dumps(job))
                    return job
            except Exception as e:
                print(f"[QUEUE MANAGER] [WARN] Redis dequeue error: {e}")

        # SQLite Fallback
        with self._lock:
            try:
                from web_app.app import app, db
                from web_app.models import TaskQueueItem
                with app.app_context():
                    # Pick highest priority, oldest queued item
                    item = TaskQueueItem.query.filter_by(status="queued")\
                        .order_by(TaskQueueItem.priority.desc(), TaskQueueItem.created_at.asc())\
                        .first()

                    if item:
                        item.status = "processing"
                        item.started_at = datetime.utcnow()
                        db.session.commit()

                        payload = json.loads(item.payload_json) if item.payload_json else {}
                        return {
                            "job_id": item.job_id,
                            "job_type": item.job_type,
                            "payload": payload,
                            "priority": item.priority,
                            "created_at": item.created_at.isoformat() if item.created_at else None,
                            "status": "processing"
                        }
            except Exception as e:
                print(f"[QUEUE MANAGER] [ERROR] DB dequeue error: {e}")

        return None

    def complete_job(self, job_id: str, result: Dict[str, Any] = None):
        """Marks a job as completed and stores the result."""
        result = result or {}
        if self.mode == "redis" and self._redis_client:
            try:
                raw = self._redis_client.hget("going_merry:jobs", job_id)
                if raw:
                    job = json.loads(raw)
                    job["status"] = "completed"
                    job["completed_at"] = datetime.utcnow().isoformat()
                    job["result"] = result
                    self._redis_client.hset("going_merry:jobs", job_id, json.dumps(job))
            except Exception:
                pass

        with self._lock:
            try:
                from web_app.app import app, db
                from web_app.models import TaskQueueItem
                with app.app_context():
                    item = TaskQueueItem.query.filter_by(job_id=job_id).first()
                    if item:
                        item.status = "completed"
                        item.completed_at = datetime.utcnow()
                        item.result_json = json.dumps(result)
                        db.session.commit()
            except Exception as e:
                print(f"[QUEUE MANAGER] [ERROR] Failed to complete job in DB: {e}")

    def fail_job(self, job_id: str, error_msg: str):
        """Marks a job as failed and stores error diagnostics."""
        if self.mode == "redis" and self._redis_client:
            try:
                raw = self._redis_client.hget("going_merry:jobs", job_id)
                if raw:
                    job = json.loads(raw)
                    job["status"] = "failed"
                    job["completed_at"] = datetime.utcnow().isoformat()
                    job["error"] = error_msg
                    self._redis_client.hset("going_merry:jobs", job_id, json.dumps(job))
            except Exception:
                pass

        with self._lock:
            try:
                from web_app.app import app, db
                from web_app.models import TaskQueueItem
                with app.app_context():
                    item = TaskQueueItem.query.filter_by(job_id=job_id).first()
                    if item:
                        item.status = "failed"
                        item.completed_at = datetime.utcnow()
                        item.error_msg = str(error_msg)
                        db.session.commit()
            except Exception as e:
                print(f"[QUEUE MANAGER] [ERROR] Failed to fail job in DB: {e}")

    def get_queue_stats(self) -> Dict[str, Any]:
        """Returns counts of queued, processing, completed, and failed jobs."""
        stats = {"mode": self.mode, "queued": 0, "processing": 0, "completed": 0, "failed": 0, "total": 0}

        try:
            from web_app.app import app, db
            from web_app.models import TaskQueueItem
            with app.app_context():
                stats["queued"]     = TaskQueueItem.query.filter_by(status="queued").count()
                stats["processing"] = TaskQueueItem.query.filter_by(status="processing").count()
                stats["completed"]  = TaskQueueItem.query.filter_by(status="completed").count()
                stats["failed"]     = TaskQueueItem.query.filter_by(status="failed").count()
                stats["total"]      = TaskQueueItem.query.count()
        except Exception as e:
            stats["error"] = str(e)

        return stats

    def list_recent_jobs(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Lists recent jobs with their statuses and types."""
        jobs = []
        try:
            from web_app.app import app, db
            from web_app.models import TaskQueueItem
            with app.app_context():
                items = TaskQueueItem.query.order_by(TaskQueueItem.created_at.desc()).limit(limit).all()
                for item in items:
                    jobs.append({
                        "job_id": item.job_id,
                        "job_type": item.job_type,
                        "status": item.status,
                        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
                        "completed_at": item.completed_at.strftime("%Y-%m-%d %H:%M:%S") if item.completed_at else "",
                        "error": item.error_msg or ""
                    })
        except Exception as e:
            print(f"[QUEUE MANAGER] [WARN] list_recent_jobs error: {e}")

        return jobs


# Global Singleton Instance
queue_manager = QueueManager()
