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
    from datetime import datetime
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    scan_mode = request.form.get("scan_mode", "latest").strip()
    offset_raw = request.form.get("offset_or_post_id", "").strip()
    offset_val = int(offset_raw) if offset_raw.isdigit() else None

    monitor = StreamMonitor()
    streams = monitor.fetch_archive_or_viral_streams(
        influencer.channel_url,
        mode=scan_mode,
        limit=3,
        offset_or_post_id=offset_val
    )
    
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

    influencer.last_checked_at = datetime.utcnow()
    db.session.commit()
    mode_label = {"viral": "viral stream(s)", "old_archive": "archived episode(s)/video(s)", "latest": "recent stream(s)/episode(s)"}.get(scan_mode, "video(s)")
    if new_found > 0:
        flash(f"🎉 Discovered {new_found} {mode_label} for {influencer.channel_name}! Queued for clipping.", "success")
    else:
        flash(f"Scan ({scan_mode}) complete for {influencer.channel_name}.", "info")

    return redirect(url_for("influencers.list_influencers"))


@influencers_bp.route("/influencers/conversation", methods=["POST"])
@login_required
def build_channel_conversation():
    """
    Creates a Cross-Channel Conversation / Mashup / Reaction job combining old episodes,
    past viral streams, or old videos from two followed channels.
    """
    from datetime import datetime
    import time

    ch_a_id = request.form.get("channel_a_id", type=int)
    ch_b_id = request.form.get("channel_b_id", type=int)
    source_mode = request.form.get("source_mode", "viral").strip()  # viral | old_archive | latest
    conv_style = request.form.get("conversation_style", "alternating_dialogue").strip()
    offset_raw = request.form.get("episode_offset", "").strip()
    offset_val = int(offset_raw) if offset_raw.isdigit() else None

    if not ch_a_id or not ch_b_id:
        flash("Please select both Channel A and Channel B to build a conversation.", "error")
        return redirect(url_for("influencers.list_influencers"))

    inf_a = MonitoredInfluencer.query.filter_by(id=ch_a_id, user_id=current_user.id).first_or_404()
    inf_b = MonitoredInfluencer.query.filter_by(id=ch_b_id, user_id=current_user.id).first_or_404()

    monitor = StreamMonitor()
    streams_a = monitor.fetch_archive_or_viral_streams(inf_a.channel_url, mode=source_mode, limit=1, offset_or_post_id=offset_val)
    streams_b = monitor.fetch_archive_or_viral_streams(inf_b.channel_url, mode=source_mode, limit=1, offset_or_post_id=offset_val)

    clip_a = streams_a[0] if streams_a else {"stream_id": f"a_{int(time.time())}", "title": f"{inf_a.channel_name} Archive", "url": inf_a.channel_url, "duration": 300.0}
    clip_b = streams_b[0] if streams_b else {"stream_id": f"b_{int(time.time())}", "title": f"{inf_b.channel_name} Archive", "url": inf_b.channel_url, "duration": 300.0}

    style_labels = {
        "alternating_dialogue": "🗣️ Dialogue Cut",
        "split_screen_reaction": "📱 9:16 Split-Screen",
        "viral_hook_crossover": "⚡ Viral Crossover",
    }
    style_tag = style_labels.get(conv_style, "🗣️ Conversation")

    # Strip existing prefix tags for cleaner combined title
    clean_a = clip_a["title"].replace("🔥 [VIRAL TG]", "").replace("📜 [OLD EPISODE]", "").replace("📜 [OLD STREAM]", "").strip()[:32]
    clean_b = clip_b["title"].replace("🔥 [VIRAL TG]", "").replace("📜 [OLD EPISODE]", "").replace("📜 [OLD STREAM]", "").strip()[:32]

    conv_stream_id = f"conv_{inf_a.id}x{inf_b.id}_{int(time.time()) % 100000}"
    conv_title = f"{style_tag}: {inf_a.channel_name} ({clean_a}) × {inf_b.channel_name} ({clean_b})"

    conv_stream = ProcessedStream(
        influencer_id=inf_a.id,
        stream_id=conv_stream_id,
        stream_title=conv_title[:240],
        stream_url=clip_a["url"],
        duration=float(clip_a.get("duration", 180.0)) + float(clip_b.get("duration", 180.0)),
        status="queued"
    )
    db.session.add(conv_stream)
    inf_a.last_checked_at = datetime.utcnow()
    inf_b.last_checked_at = datetime.utcnow()
    db.session.commit()

    flash(
        f"🎬 Queued {style_tag} between {inf_a.channel_name} & {inf_b.channel_name} using {source_mode.replace('_', ' ')} footage!",
        "success"
    )
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
    from datetime import datetime
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
            is_active=True,
            last_checked_at=datetime.utcnow()
        )
        db.session.add(influencer)
        db.session.commit()

        # Perform immediate initial scan so streams/episodes appear right away
        streams = monitor.fetch_completed_streams(influencer.channel_url, limit=3)
        new_found = 0
        for s in streams:
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

        flash(f"Started monitoring {meta['channel_name']} ({meta['platform'].title()}) — discovered & queued {new_found} recent video(s)!", "success")
    else:
        flash(f"Already monitoring {existing.channel_name}.", "info")

    return redirect(url_for("influencers.list_influencers"))
