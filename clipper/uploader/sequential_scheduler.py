"""
Sequential Queue Scheduler
==========================
Anti-detection staggered uploader for cloud environments with single datacenter IP.
Enforces a 20-30 minute human-like jitter between consecutive posts to prevent
social platform rate limits and shadowbans across multi-account setups.
"""

import time
import random
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger("SequentialScheduler")
logger.setLevel(logging.INFO)

class SequentialUploadScheduler:
    """
    Manages an asynchronous, sequential queue for publishing videos
    with configurable delays between uploads.
    """

    def __init__(self, min_delay_minutes: int = 20, max_delay_minutes: int = 35):
        self.min_delay_seconds = min_delay_minutes * 60
        self.max_delay_seconds = max_delay_minutes * 60
        self.queue: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.current_job: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_upload_time: Dict[str, datetime] = {}

    def add_to_queue(
        self,
        account_id: str,
        platform: str,
        video_path: str,
        title: str = "",
        caption: str = "",
        tags: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> str:
        """Adds a video task to the sequential queue."""
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "account_id": account_id,
            "platform": platform.lower(),
            "video_path": str(video_path),
            "title": title,
            "caption": caption,
            "tags": tags or [],
            "status": "queued",
            "enqueued_at": datetime.utcnow().isoformat(),
            "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
            "completed_at": None,
            "error": None
        }

        with self._lock:
            self.queue.append(task)
            logger.info(f"[SCHEDULER] Enqueued task {task_id} for account={account_id}, platform={platform}")

        self.ensure_running()
        return task_id

    def get_status(self) -> Dict[str, Any]:
        """Returns the current queue status and active job."""
        with self._lock:
            return {
                "active_job": self.current_job,
                "queued_count": len(self.queue),
                "queue": list(self.queue),
                "history_count": len(self.history),
                "recent_history": list(self.history[-10:])
            }

    def start(self):
        """Starts the background sequential upload thread."""
        with self._lock:
            if not self._running:
                self._running = True
                self._worker_thread = threading.Thread(target=self._process_queue_loop, daemon=True)
                self._worker_thread.start()
                logger.info("[SCHEDULER] Sequential worker thread started.")

    def ensure_running(self):
        """Ensures worker thread is running if queue has pending items."""
        if not self._running or self._worker_thread is None or not self._worker_thread.is_alive():
            self.start()

    def stop(self):
        """Signals worker loop to terminate."""
        self._running = False

    def _process_queue_loop(self):
        """Main loop that continuously pulls tasks and processes them sequentially."""
        from clipper.uploader.bulk_dispatcher import BulkDispatcher

        dispatcher = None
        try:
            dispatcher = BulkDispatcher()
        except Exception as e:
            logger.warning(f"[SCHEDULER] Could not initialize BulkDispatcher: {e}")

        while self._running:
            task = None
            with self._lock:
                if self.queue:
                    task = self.queue.pop(0)
                    self.current_job = task
                    task["status"] = "processing"
                    task["started_at"] = datetime.utcnow().isoformat()

            if not task:
                time.sleep(5)
                continue

            # Execute the upload
            logger.info(f"[SCHEDULER] Processing task {task['id']} for {task['account_id']} on {task['platform']}...")
            success = False
            error_msg = None

            try:
                if dispatcher:
                    if task["platform"] == "instagram":
                        res = dispatcher.upload_instagram_reel(
                            account_id=task["account_id"],
                            video_path=task["video_path"],
                            caption=task["caption"] or task["title"],
                            hashtags=task["tags"]
                        )
                        success = (res.get("status") == "success")
                        if not success:
                            error_msg = res.get("message", "Upload failed")
                    elif task["platform"] == "youtube":
                        res = dispatcher.upload_youtube_short(
                            account_id=task["account_id"],
                            video_path=task["video_path"],
                            title=task["title"],
                            description=task["caption"],
                            tags=task["tags"]
                        )
                        success = (res.get("status") == "success")
                        if not success:
                            error_msg = res.get("message", "Upload failed")
                    else:
                        error_msg = f"Unsupported platform: {task['platform']}"
                else:
                    error_msg = "Dispatcher unavailable"
            except Exception as ex:
                error_msg = str(ex)
                logger.error(f"[SCHEDULER] Upload error on {task['id']}: {ex}")

            # Record completion
            task["completed_at"] = datetime.utcnow().isoformat()
            task["status"] = "success" if success else "failed"
            task["error"] = error_msg

            with self._lock:
                self.history.append(task)
                self.current_job = None

            # Enforce sequential anti-flag delay before allowing the next item to run
            if self.queue:
                delay = random.randint(self.min_delay_seconds, self.max_delay_seconds)
                logger.info(f"[SCHEDULER] Anti-flag cooling period: sleeping for {delay // 60}m {delay % 60}s before next task...")
                elapsed = 0
                while self._running and elapsed < delay:
                    time.sleep(2)
                    elapsed += 2

# Global singleton
scheduler = SequentialUploadScheduler()
