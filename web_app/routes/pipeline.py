"""
Going Merry — Autonomous Shorts Factory Pipeline Route
======================================================
Stitches going_merry.sail() and clipper directly into the Web Dashboard.
Provides:
  - POST /api/pipeline/start     : Launch end-to-end production with live persona routing
  - GET  /api/pipeline/status    : Query real-time status and logs of a running job
  - GET  /api/pipeline/events    : Poll buffered events since last seen event ID
  - GET  /api/pipeline/stream    : Server-Sent Events (SSE) live telemetry stream
  - POST /api/pipeline/stop      : Abort or reset an active job
"""

import os
import sys
import json
import time
import uuid
import queue
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, Response, current_app
from flask_login import login_required, current_user

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from clipper.core.event_bus import bus
from web_app.app import db
from web_app.models import Clip as ClipModel, AccountPersona, UploadJob

pipeline_bp = Blueprint("pipeline", __name__)

# Active job tracker: job_id -> dict
ACTIVE_JOBS: dict[str, dict] = {}
ACTIVE_JOBS_LOCK = threading.Lock()


@pipeline_bp.route("/api/pipeline/start", methods=["POST"])
@login_required
def start_pipeline():
    """
    Launches Going Merry autonomous pipeline in background thread.
    Routes dispatches to the specified AccountPersona.
    """
    data = request.get_json() or request.form

    source_url   = data.get("source_url", "").strip()
    video_file   = data.get("video_file", "").strip()
    account_id   = data.get("account_id", "").strip() or "acc_01"
    num_clips    = int(data.get("num_clips", 3))
    platform     = data.get("platform", "all").strip().lower()
    content_mode = data.get("mode", "whop").strip().lower() # 'whop' | 'url'
    campaign     = data.get("campaign", "").strip() or None
    overlay      = data.get("overlay", "").strip() or None
    
    # Feature toggles
    split_screen = data.get("split_screen", True) in [True, "true", "1", 1, "on"]
    music        = data.get("music", True) in [True, "true", "1", 1, "on"]
    music_query  = data.get("music_query", "lofi hip hop chill no copyright").strip()
    auto_upload  = data.get("auto_upload", True) in [True, "true", "1", 1, "on"]
    preview      = data.get("preview", False) in [True, "true", "1", 1, "on"]
    resume       = data.get("resume", False) in [True, "true", "1", 1, "on"]
    workers      = int(data.get("workers", 1))

    # Resolve local file vs URL
    if not source_url and not video_file:
        return jsonify({"success": False, "message": "Please provide a video URL or local file path."}), 400

    if source_url and not source_url.startswith(("http://", "https://")):
        full_p = (PROJECT_ROOT / source_url).resolve()
        if full_p.exists():
            video_file = str(full_p)
            source_url = None
        elif os.path.exists(source_url):
            video_file = os.path.abspath(source_url)
            source_url = None

    # Verify persona exists
    persona = AccountPersona.query.filter_by(id=account_id).first()
    persona_username = persona.username if persona else "@Default"

    # Whop mode automatic configuration
    whop_flag = (content_mode == "whop")
    if whop_flag and not campaign:
        campaign = "FundingPips"

    # Generate unique job ID
    job_id = f"gm_{uuid.uuid4().hex[:8]}"

    user_id_val = current_user.id if current_user and hasattr(current_user, 'id') else 1

    # Initial DB stub so user sees processing state in feed immediately
    try:
        initial_clip = ClipModel(
            user_id=user_id_val,
            source_url=source_url or (os.path.basename(video_file) if video_file else "local_file"),
            title=f"Going Merry // {num_clips} Viral Shorts ({persona_username})",
            status="processing",
            score=90
        )
        db.session.add(initial_clip)
        db.session.commit()
        clip_db_id = initial_clip.id
    except Exception as db_err:
        print(f"[PIPELINE_ROUTE] DB initial notice: {db_err}")
        clip_db_id = None

    # Track active job
    job_meta = {
        "job_id": job_id,
        "user_id": user_id_val,
        "clip_db_id": clip_db_id,
        "source_url": source_url,
        "video_file": video_file,
        "account_id": account_id,
        "persona_username": persona_username,
        "num_clips": num_clips,
        "platform": platform,
        "status": "running",
        "current_stage": 1,
        "stage_name": "Transcribing audio",
        "completed_clips": [],
        "started_at": time.time(),
        "error": None
    }
    with ACTIVE_JOBS_LOCK:
        ACTIVE_JOBS[job_id] = job_meta

    # Emit initial pipeline start event
    bus.emit("pipeline.start", {
        "job_id": job_id,
        "url": source_url,
        "video_file": video_file,
        "account_id": account_id,
        "persona": persona_username,
        "num_clips": num_clips,
        "platform": platform,
        "timestamp": time.time()
    })

    # Background executor
    flask_app = current_app._get_current_object()

    def run_worker():
        try:
            from going_merry import sail
            with flask_app.app_context():
                print(f"\n[PIPELINE] 🚀 Launching Going Merry [{job_id}] for Persona {persona_username} ({account_id})...")
                results = sail(
                    url          = source_url,
                    video_file   = video_file,
                    whop         = whop_flag,
                    campaign     = campaign,
                    overlay      = overlay,
                    num_clips    = num_clips,
                    platform     = platform,
                    upload       = auto_upload,
                    split_screen = split_screen,
                    music        = music,
                    music_query  = music_query,
                    preview      = preview,
                    user_id      = user_id_val,
                    clip_id      = clip_db_id,
                    job_id       = job_id,
                    resume       = resume,
                    workers      = workers,
                    account_id   = account_id
                )

                with ACTIVE_JOBS_LOCK:
                    if job_id in ACTIVE_JOBS:
                        ACTIVE_JOBS[job_id]["status"] = "completed"
                        ACTIVE_JOBS[job_id]["completed_clips"] = results
                        ACTIVE_JOBS[job_id]["current_stage"] = 7
                        ACTIVE_JOBS[job_id]["stage_name"] = "Production Complete"

                print(f"[PIPELINE] ✅ Finished job {job_id}: {len(results)} clips generated.")

        except Exception as e:
            import traceback
            err_trace = traceback.format_exc()
            print(f"[PIPELINE] ❌ Error in job {job_id}: {e}\n{err_trace}")
            with ACTIVE_JOBS_LOCK:
                if job_id in ACTIVE_JOBS:
                    ACTIVE_JOBS[job_id]["status"] = "failed"
                    ACTIVE_JOBS[job_id]["error"] = str(e)
            bus.emit("pipeline.error", {"job_id": job_id, "error": str(e)})

    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()

    return jsonify({
        "success": True,
        "job_id": job_id,
        "persona": persona_username,
        "account_id": account_id,
        "clips": num_clips,
        "message": f"Going Merry engaged! Producing {num_clips} viral shorts for {persona_username}."
    })


@pipeline_bp.route("/api/pipeline/status/<string:job_id>", methods=["GET"])
@login_required
def get_pipeline_status(job_id):
    """Returns current stage, percentage, completed clips, and logs for a job."""
    with ACTIVE_JOBS_LOCK:
        job = ACTIVE_JOBS.get(job_id)

    if not job:
        # Check if events exist in event bus
        events = [e for e in bus.get_events() if e.get("data", {}).get("job_id") == job_id]
        if events:
            return jsonify({
                "success": True,
                "job_id": job_id,
                "status": "completed" if any(e.get("type") == "pipeline.complete" for e in events) else "running",
                "events": events[-30:]
            })
        return jsonify({"success": False, "message": "Job not found"}), 404

    # Extract all events related to this job
    job_events = [e for e in bus.get_events() if e.get("data", {}).get("job_id") == job_id]

    return jsonify({
        "success": True,
        "job": job,
        "events": job_events[-40:]
    })


@pipeline_bp.route("/api/pipeline/events", methods=["GET"])
@login_required
def get_pipeline_events():
    """Polls recent buffered events since a given event ID."""
    since_id = int(request.args.get("since_id", 0))
    events = bus.get_events(since_id=since_id)
    return jsonify({
        "success": True,
        "events": events
    })


@pipeline_bp.route("/api/pipeline/stream")
@login_required
def stream_pipeline_events():
    """
    Server-Sent Events (SSE) live pipeline telemetry stream.
    Browser subscribes via: const es = new EventSource('/api/pipeline/stream');
    """
    def event_generator():
        client_queue = bus.register_queue()
        try:
            # Yield initial connection confirmation
            yield f"data: {json.dumps({'type': 'connection.established', 'timestamp': time.time()})}\n\n"
            while True:
                try:
                    event = client_queue.get(timeout=15)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                except queue.Empty:
                    # Heartbeat
                    yield f": heartbeat {time.time()}\n\n"
        except GeneratorExit:
            pass
        finally:
            bus.unregister_queue(client_queue)

    return Response(
        event_generator(),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )


@pipeline_bp.route("/api/pipeline/stop/<string:job_id>", methods=["POST"])
@login_required
def stop_pipeline(job_id):
    """Marks job as cancelled in active tracker."""
    with ACTIVE_JOBS_LOCK:
        if job_id in ACTIVE_JOBS:
            ACTIVE_JOBS[job_id]["status"] = "cancelled"
            bus.emit("pipeline.error", {"job_id": job_id, "error": "Cancelled by operator"})
            return jsonify({"success": True, "message": f"Job {job_id} cancelled."})
    return jsonify({"success": False, "message": "Job not found or already completed."}), 404
