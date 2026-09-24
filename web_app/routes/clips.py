"""
Clip routes — create new clip jobs, follow influencers, view clip details
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import Clip, MonitoredInfluencer
from clipper.core.stream_monitor import StreamMonitor

clips_bp = Blueprint("clips", __name__)


@clips_bp.route("/clips/new", methods=["GET", "POST"])
@login_required
def new_clip():
    if request.method == "POST":
        source_url        = request.form.get("source_url", "").strip()
        num_clips         = int(request.form.get("num_clips", 5))
        platform          = request.form.get("platform", "all")
        follow_influencer = request.form.get("follow_influencer") in ["on", "true", "1"]
        auto_upload       = request.form.get("auto_upload") in ["on", "true", "1"]

        if not source_url:
            flash("Please enter a valid YouTube or Twitch URL.", "error")
            return render_template("new_clip.html")

        # 1. If Follow Influencer is enabled, register the creator
        if follow_influencer:
            monitor = StreamMonitor()
            meta = monitor.resolve_channel_metadata(source_url)
            
            existing = MonitoredInfluencer.query.filter_by(
                user_id=current_user.id,
                channel_url=meta["channel_url"]
            ).first()

            if not existing:
                influencer = MonitoredInfluencer(
                    user_id=current_user.id,
                    channel_name=meta["channel_name"],
                    channel_handle=meta["channel_handle"],
                    channel_url=meta["channel_url"],
                    platform=meta["platform"],
                    num_clips=num_clips,
                    target_platform=platform,
                    auto_upload=auto_upload,
                    is_active=True
                )
                db.session.add(influencer)
                db.session.commit()
                flash(f"🌟 Following {meta['channel_name']}! Completed streams will be auto-clipped daily.", "success")
            else:
                existing.is_active = True
                existing.num_clips = num_clips
                existing.target_platform = platform
                existing.auto_upload = auto_upload
                db.session.commit()
                flash(f"Updated auto-monitoring settings for {meta['channel_name']}.", "info")

        # 2. If the user provided an individual video/stream URL, queue it immediately
        is_direct_video = ("watch?v=" in source_url or "youtu.be/" in source_url or "/videos/" in source_url)
        if is_direct_video or not follow_influencer:
            clip = Clip(
                user_id=current_user.id,
                source_url=source_url,
                title=f"Processing {num_clips} viral moments...",
                status="processing",
            )
            db.session.add(clip)
            db.session.commit()

            # Enqueue to Task Broker (Flowchart: UI --> REDIS)
            try:
                from clipper.core.queue_manager import queue_manager
                queue_manager.enqueue("clip_job", {
                    "source_url": source_url,
                    "num_clips": num_clips,
                    "platform": platform,
                    "auto_upload": auto_upload,
                    "user_id": current_user.id,
                    "clip_id": clip.id
                })
            except Exception as q_err:
                print(f"[CLIPS ROUTE] [WARN] Could not enqueue job: {q_err}")

            flash(f"🚀 Started pipeline! Extracting top {num_clips} viral moments.", "success")

        return redirect(url_for("dash.dashboard"))

    return render_template("new_clip.html")


@clips_bp.route("/clips/<int:clip_id>")
@login_required
def clip_detail(clip_id):
    clip = Clip.query.filter_by(id=clip_id, user_id=current_user.id).first_or_404()
    return render_template("clip_detail.html", clip=clip)
