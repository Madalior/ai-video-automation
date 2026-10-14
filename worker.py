"""
Going Merry — Background Queue Worker Daemon
============================================
Corresponds to the WORKERS layer in architecture_flowchart.md.

Listens to the task broker (REDIS / SQLite QueueManager) and executes:
1. 'clip_job': Individual video / stream clipping via going_merry.sail()
2. 'stream_job': Newly finished livestreams detected by StreamMonitor
3. 'whop_job': Whop Content Rewards end-to-end ingestion & submission

Usage:
  python worker.py              # Run worker (continuous polling)
  python worker.py --once       # Process exactly one pending job and exit
  python worker.py --stats      # Inspect current queue status
"""

import os
import sys
import time
import argparse
import traceback
from datetime import datetime
from pathlib import Path

# Add project root
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from clipper.core.queue_manager import queue_manager

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def process_clip_job(payload: dict) -> dict:
    """Executes a standard URL or video clip job."""
    from going_merry import sail

    source_url   = payload.get("source_url")
    video_file   = payload.get("video_file")
    num_clips    = int(payload.get("num_clips", 1))
    platform     = payload.get("platform", "all")
    auto_upload  = bool(payload.get("auto_upload", False))
    preview      = bool(payload.get("preview", False))
    user_id      = payload.get("user_id", 1)
    clip_id      = payload.get("clip_id")

    print(f"\n[WORKER] 🚀 Processing clip job: url={source_url or video_file} | clips={num_clips} | upload={auto_upload}")

    generated_clips = sail(
        url          = source_url,
        video_file   = video_file,
        num_clips    = num_clips,
        platform     = platform,
        upload       = auto_upload,
        preview      = preview,
        user_id      = user_id,
        clip_id      = clip_id,
    )

    return {
        "clips_generated": len(generated_clips),
        "files": generated_clips,
        "completed_at": datetime.utcnow().isoformat()
    }


def process_stream_job(payload: dict) -> dict:
    """Executes an influencer completed stream job."""
    from going_merry import sail
    from web_app.app import app, db
    from web_app.models import ProcessedStream

    stream_url    = payload.get("stream_url")
    stream_id     = payload.get("stream_id")
    influencer_id = payload.get("influencer_id")
    channel_name  = payload.get("channel_name", "Influencer")
    num_clips     = int(payload.get("num_clips", 3))
    platform      = payload.get("target_platform", "all")
    account_id    = payload.get("account_id") or payload.get("account_persona_id")

    print(f"\n[WORKER] 📡 Processing detected stream for '{channel_name}': {stream_url} (ID: {stream_id}) | Account: [{account_id or 'default'}]")

    with app.app_context():
        stream_rec = ProcessedStream.query.filter_by(stream_id=stream_id).first()
        if stream_rec:
            stream_rec.status = "processing"
            if not account_id and stream_rec.account_persona_id:
                account_id = stream_rec.account_persona_id
            db.session.commit()

    try:
        generated = sail(
            url          = stream_url,
            num_clips    = num_clips,
            platform     = platform,
            upload       = auto_upload,
            split_screen = True,  # autonomous smart reframing
            add_blur_bg  = True,
            account_id   = account_id or "acc_01",
        )

        with app.app_context():
            stream_rec = ProcessedStream.query.filter_by(stream_id=stream_id).first()
            if stream_rec:
                stream_rec.status = "completed"
                stream_rec.clip_count = len(generated)
                stream_rec.completed_at = datetime.utcnow()
                db.session.commit()

        return {
            "stream_id": stream_id,
            "clips_generated": len(generated),
            "files": generated
        }

    except Exception as e:
        with app.app_context():
            stream_rec = ProcessedStream.query.filter_by(stream_id=stream_id).first()
            if stream_rec:
                stream_rec.status = "failed"
                db.session.commit()
        raise e


def process_whop_job(payload: dict) -> dict:
    """Executes a Whop Content Rewards pipeline job."""
    from whop_full_pipeline import run_full_whop_pipeline

    auto_mode   = bool(payload.get("auto_mode", True))
    submit_now  = bool(payload.get("submit_now", True))
    skip_render = bool(payload.get("skip_render", False))

    print(f"\n[WORKER] 💰 Processing Whop Content Rewards bounty job...")
    result = run_full_whop_pipeline(
        auto_mode=auto_mode,
        submit_now=submit_now,
        skip_render=skip_render
    )
    return result


def execute_job(job: dict) -> bool:
    """Dispatches a single job to its respective runner."""
    job_id   = job["job_id"]
    job_type = job["job_type"]
    payload  = job.get("payload", {})

    print(f"\n{'=' * 60}")
    print(f"[WORKER] Starting Job: {job_id} [{job_type}]")
    print(f"{'=' * 60}")

    try:
        if job_type == "clip_job":
            res = process_clip_job(payload)
        elif job_type == "stream_job":
            res = process_stream_job(payload)
        elif job_type == "whop_job":
            res = process_whop_job(payload)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        queue_manager.complete_job(job_id, res)
        print(f"[WORKER] ✅ Job {job_id} completed successfully.")
        return True

    except Exception as e:
        err = f"{e}\n{traceback.format_exc()}"
        print(f"[WORKER] ❌ Job {job_id} failed: {e}")
        queue_manager.fail_job(job_id, err)
        return False


def run_worker_loop(poll_interval: float = 3.0, once: bool = False):
    """Continuously pulls jobs from QueueManager and processes them."""
    print("\n" + "═" * 60)
    print("  GOING MERRY — BACKGROUND WORKER DAEMON")
    print(f"  Backend: {queue_manager.mode.upper()} | Polling: {poll_interval}s | PID: {os.getpid()}")
    print("═" * 60)

    stats = queue_manager.get_queue_stats()
    print(f"[WORKER] Queue Status: {stats.get('queued', 0)} queued | {stats.get('total', 0)} total jobs.")
    print("[WORKER] Waiting for jobs... (Press Ctrl+C to stop)\n")

    try:
        while True:
            job = queue_manager.dequeue(timeout=int(poll_interval))

            if job:
                execute_job(job)
                if once:
                    print("[WORKER] Processed single job (--once). Exiting.")
                    break
            else:
                if once:
                    print("[WORKER] No pending jobs found. Exiting.")
                    break
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\n[WORKER] Stopping worker gracefully...")


def main():
    parser = argparse.ArgumentParser(description="Going Merry — Background Queue Worker")
    parser.add_argument("--once", action="store_true", help="Process one job and exit")
    parser.add_argument("--interval", type=float, default=3.0, help="Polling interval in seconds (default: 3.0)")
    parser.add_argument("--stats", action="store_true", help="Display queue statistics and recent jobs")

    args = parser.parse_args()

    if args.stats:
        stats = queue_manager.get_queue_stats()
        print("\n" + "═" * 50)
        print("  GOING MERRY — QUEUE STATISTICS")
        print("═" * 50)
        print(f"  Mode:       {stats.get('mode')}")
        print(f"  Queued:     {stats.get('queued')}")
        print(f"  Processing: {stats.get('processing')}")
        print(f"  Completed:  {stats.get('completed')}")
        print(f"  Failed:     {stats.get('failed')}")
        print(f"  Total:      {stats.get('total')}")
        print("\nRecent Jobs:")
        recent = queue_manager.list_recent_jobs(limit=10)
        for r in recent:
            print(f"  [{r['status'].upper():<10}] {r['job_id']} | {r['job_type']} | {r['created_at']}")
        print("═" * 50)
        return

    run_worker_loop(poll_interval=args.interval, once=args.once)


if __name__ == "__main__":
    main()
