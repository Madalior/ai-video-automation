"""
Influencer Management Routes
============================
Allows users to view, toggle, configure, and scan their followed influencers.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import MonitoredInfluencer, ProcessedStream
from clipper.core.stream_monitor import StreamMonitor

influencers_bp = Blueprint("influencers", __name__)


@influencers_bp.route("/influencers")
@login_required
def list_influencers():
    followed = MonitoredInfluencer.query.filter_by(user_id=current_user.id).order_by(MonitoredInfluencer.created_at.desc()).all()
    
    # Calculate stream stats for each influencer
    streams = ProcessedStream.query.join(MonitoredInfluencer).filter(
        MonitoredInfluencer.user_id == current_user.id
    ).order_by(ProcessedStream.created_at.desc()).limit(15).all()

    return render_template("influencers.html", influencers=followed, recent_streams=streams)


@influencers_bp.route("/influencers/<int:influencer_id>/toggle", methods=["POST"])
@login_required
def toggle_influencer(influencer_id):
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    influencer.is_active = not influencer.is_active
    db.session.commit()
    status_str = "Resumed monitoring" if influencer.is_active else "Paused monitoring"
    flash(f"{status_str} for {influencer.channel_name}.", "info")
    return redirect(url_for("influencers.list_influencers"))


@influencers_bp.route("/influencers/<int:influencer_id>/scan", methods=["POST"])
@login_required
def scan_influencer(influencer_id):
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    monitor = StreamMonitor()
    streams = monitor.fetch_completed_streams(influencer.channel_url, limit=3)
    
    new_found = 0
    for s in streams:
        existing = ProcessedStream.query.filter_by(
            influencer_id=influencer.id,
            stream_id=s["stream_id"]
        ).first()

        if not existing:
            new_stream = ProcessedStream(
                influencer_id=influencer.id,
                stream_id=s["stream_id"],
                stream_title=s["title"],
                stream_url=s["url"],
                duration=s["duration"],
                status="queued"
            )
            db.session.add(new_stream)
            new_found += 1

    db.session.commit()
    if new_found > 0:
        flash(f"🎉 Discovered {new_found} new completed stream(s) for {influencer.channel_name}! Queued for clipping.", "success")
    else:
        flash(f"No new completed streams found for {influencer.channel_name}.", "info")

    return redirect(url_for("influencers.list_influencers"))


@influencers_bp.route("/influencers/<int:influencer_id>/delete", methods=["POST"])
@login_required
def delete_influencer(influencer_id):
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    channel_name = influencer.channel_name
    db.session.delete(influencer)
    db.session.commit()
    flash(f"Unfollowed and removed {channel_name}.", "warning")
    return redirect(url_for("influencers.list_influencers"))


@influencers_bp.route("/influencers/add", methods=["POST"])
@login_required
def add_influencer():
    channel_url = request.form.get("channel_url", "").strip()
    if not channel_url:
        flash("Please enter a valid creator or channel URL.", "error")
        return redirect(url_for("influencers.list_influencers"))

    monitor = StreamMonitor()
    meta = monitor.resolve_channel_metadata(channel_url)

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
            num_clips=int(request.form.get("num_clips", 5)),
            target_platform=request.form.get("target_platform", "all"),
            auto_upload=True,
            is_active=True
        )
        db.session.add(influencer)
        db.session.commit()
        flash(f"Started monitoring {meta['channel_name']} ({meta['platform'].title()})!", "success")
    else:
        flash(f"Already monitoring {existing.channel_name}.", "info")

    return redirect(url_for("influencers.list_influencers"))
