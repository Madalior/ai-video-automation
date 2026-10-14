"""
Influencer Management Routes
============================
Allows users to view, toggle, configure, and scan their followed influencers.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import MonitoredInfluencer, ProcessedStream, AccountPersona
from clipper.core.stream_monitor import StreamMonitor

influencers_bp = Blueprint("influencers", __name__)


@influencers_bp.route("/influencers")
@login_required
def list_influencers():
    persona_id = request.args.get("persona_id", "").strip() or None
    active_persona = None
    if persona_id:
        active_persona = AccountPersona.query.filter_by(id=persona_id, user_id=current_user.id).first()

    personas = AccountPersona.query.filter_by(user_id=current_user.id).all()
    all_influencers_count = MonitoredInfluencer.query.filter_by(user_id=current_user.id).count()

    query = MonitoredInfluencer.query.filter_by(user_id=current_user.id)
    if active_persona:
        followed = query.filter_by(account_persona_id=active_persona.id).order_by(MonitoredInfluencer.created_at.desc()).all()
    else:
        followed = query.order_by(MonitoredInfluencer.created_at.desc()).all()
    
    # Calculate stream stats for each influencer
    stream_query = ProcessedStream.query.join(MonitoredInfluencer).filter(
        MonitoredInfluencer.user_id == current_user.id
    )
    if active_persona:
        stream_query = stream_query.filter(
            (ProcessedStream.account_persona_id == active_persona.id) | (MonitoredInfluencer.account_persona_id == active_persona.id)
        )
    streams = stream_query.order_by(ProcessedStream.created_at.desc()).limit(15).all()

    return render_template(
        "influencers.html",
        influencers=followed,
        recent_streams=streams,
        personas=personas,
        active_persona=active_persona,
        persona_id=persona_id,
        all_influencers_count=all_influencers_count
    )


@influencers_bp.route("/influencers/<int:influencer_id>/toggle", methods=["POST"])
@login_required
def toggle_influencer(influencer_id):
    persona_id = request.form.get("persona_id", "").strip() or request.args.get("persona_id", "").strip() or None
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    influencer.is_active = not influencer.is_active
    db.session.commit()
    status_str = "Resumed monitoring" if influencer.is_active else "Paused monitoring"
    flash(f"{status_str} for {influencer.channel_name}.", "info")
    return redirect(url_for("influencers.list_influencers", persona_id=persona_id))


@influencers_bp.route("/influencers/<int:influencer_id>/scan", methods=["POST"])
@login_required
def scan_influencer(influencer_id):
    from datetime import datetime
    persona_id = request.form.get("persona_id", "").strip() or request.args.get("persona_id", "").strip() or None
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
                account_persona_id=influencer.account_persona_id,
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

    return redirect(url_for("influencers.list_influencers", persona_id=persona_id))


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
        account_persona_id=inf_a.account_persona_id or inf_b.account_persona_id,
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
    persona_id = request.form.get("persona_id", "").strip() or request.args.get("persona_id", "").strip() or None
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    channel_name = influencer.channel_name
    db.session.delete(influencer)
    db.session.commit()
    flash(f"Unfollowed and removed {channel_name}.", "warning")
    return redirect(url_for("influencers.list_influencers", persona_id=persona_id))


@influencers_bp.route("/influencers/add", methods=["POST"])
@login_required
def add_influencer():
    from datetime import datetime
    channel_url = request.form.get("channel_url", "").strip()
    persona_id = request.form.get("persona_id", "").strip() or request.args.get("persona_id", "").strip() or None
    account_persona_id = request.form.get("account_persona_id", "").strip() or persona_id or None

    if not channel_url:
        flash("Please enter a valid creator or channel URL.", "error")
        return redirect(url_for("influencers.list_influencers", persona_id=persona_id))

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
            account_persona_id=account_persona_id,
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
                account_persona_id=influencer.account_persona_id,
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
        if account_persona_id and existing.account_persona_id != account_persona_id:
            existing.account_persona_id = account_persona_id
            db.session.commit()
            flash(f"Updated upload persona for {existing.channel_name}.", "success")
        else:
            flash(f"Already monitoring {existing.channel_name}.", "info")

    return redirect(url_for("influencers.list_influencers", persona_id=account_persona_id or persona_id))


@influencers_bp.route("/influencers/<int:influencer_id>/assign_persona", methods=["POST"])
@login_required
def assign_persona(influencer_id):
    influencer = MonitoredInfluencer.query.filter_by(id=influencer_id, user_id=current_user.id).first_or_404()
    persona_id = request.form.get("account_persona_id", "").strip()
    return_persona_id = request.form.get("return_persona_id", "").strip() or None
    
    if persona_id:
        persona = AccountPersona.query.filter_by(id=persona_id, user_id=current_user.id).first()
        if persona:
            influencer.account_persona_id = persona.id
            flash(f"Assigned {influencer.channel_name} to @{persona.username} upload node.", "success")
        else:
            flash("Persona node not found.", "error")
    else:
        influencer.account_persona_id = None
        flash(f"Unassigned upload persona for {influencer.channel_name}.", "info")

    db.session.commit()
    return redirect(url_for("influencers.list_influencers", persona_id=return_persona_id or persona_id))



@influencers_bp.route("/api/influencers/chat", methods=["POST"])
@login_required
def chat_command():
    """
    Conversational AI Assistant Endpoint for Influencer & Telegram Content
    Handles natural language commands like:
    - 'download ep1' / 'download episode 5'
    - 'look for high viewed stream' / 'find viral stream of ishowspeed'
    - 'scan latest streams'
    """
    from datetime import datetime
    import re

    data = request.get_json(silent=True) or request.form
    prompt = (data.get("prompt") or data.get("message") or "").strip()
    persona_id = (data.get("persona_id") or "").strip()
    active_persona = None
    if persona_id:
        active_persona = AccountPersona.query.filter_by(id=persona_id, user_id=current_user.id).first()

    if not prompt:
        return jsonify({"success": False, "reply": "Please type a command (e.g., 'download ep1' or 'look for high viewed stream')."}), 400

    prompt_lower = prompt.lower()
    base_query = MonitoredInfluencer.query.filter_by(user_id=current_user.id, is_active=True)
    if active_persona:
        followed = base_query.filter_by(account_persona_id=active_persona.id).all()
        if not followed:
            followed = base_query.all()
    else:
        followed = base_query.all()

    if not followed:
        node_msg = f" for @{active_persona.username.lstrip('@')}" if active_persona else ""
        return jsonify({
            "success": False,
            "reply": f"⚠️ No active creators or Telegram channels assigned{node_msg} yet! Use the box above to link a channel."
        })

    target_account_id = active_persona.id if active_persona else None
    monitor = StreamMonitor()

    # 1. COMMAND: "download ep<N>" or "episode <N>" or "post <N>"
    ep_match = re.search(r"(?:download|get|pull|find|cut|fetch)?\s*(?:ep|episode|post)\s*#?\s*(\d+)", prompt_lower)
    if ep_match:
        ep_num = int(ep_match.group(1))

        # Target Telegram channel if present, or creator mentioned
        target_channel = None
        for inf in followed:
            if inf.platform == "telegram":
                target_channel = inf
                break
            if inf.channel_name.lower() in prompt_lower or (inf.channel_handle and inf.channel_handle.lower() in prompt_lower):
                target_channel = inf
                break

        if not target_channel:
            target_channel = followed[0]

        streams = monitor.fetch_archive_or_viral_streams(
            target_channel.channel_url,
            mode="old_archive",
            limit=1,
            offset_or_post_id=ep_num
        )

        stream_data = streams[0] if streams else {
            "stream_id": f"tg_ep_{ep_num}",
            "title": f"Episode #{ep_num} ({target_channel.channel_name})",
            "url": f"{target_channel.channel_url}/{ep_num}",
            "duration": 180.0
        }

        existing = ProcessedStream.query.filter_by(
            influencer_id=target_channel.id,
            stream_id=stream_data["stream_id"]
        ).first()

        dest_persona_id = target_account_id or target_channel.account_persona_id
        if not existing:
            new_stream = ProcessedStream(
                influencer_id=target_channel.id,
                account_persona_id=dest_persona_id,
                stream_id=stream_data["stream_id"],
                stream_title=stream_data["title"],
                stream_url=stream_data["url"],
                duration=stream_data.get("duration", 180.0),
                status="queued"
            )
            db.session.add(new_stream)
            target_channel.last_checked_at = datetime.utcnow()
            db.session.commit()

        clean_title = stream_data["title"].replace("📜 [OLD EPISODE]", "").replace("🔥 [VIRAL TG]", "").strip()
        node_tag = f" for @{active_persona.username.lstrip('@')}" if active_persona else ""
        return jsonify({
            "success": True,
            "reply": f"🎬 Discovered & queued Episode #{ep_num}{node_tag} from {target_channel.channel_name}: '{clean_title}'! Ready for clipping into 9:16 vertical shorts.",
            "stream": {
                "creator": target_channel.channel_name,
                "title": clean_title,
                "url": stream_data["url"],
                "duration": f"{round(stream_data.get('duration', 180)/60)} min",
                "status": "queued"
            }
        })

    # 2. COMMAND: "look for high viewed stream" or "viral stream"
    if any(k in prompt_lower for k in ["high viewed", "viral", "most viewed", "top stream", "popular", "trending", "highest view"]):
        target_channel = None
        for inf in followed:
            if inf.channel_name.lower() in prompt_lower or (inf.channel_handle and inf.channel_handle.lower() in prompt_lower):
                target_channel = inf
                break
        if not target_channel:
            target_channel = next((inf for inf in followed if inf.platform == "youtube"), followed[0])

        streams = monitor.fetch_archive_or_viral_streams(
            target_channel.channel_url,
            mode="viral",
            limit=2
        )

        dest_persona_id = target_account_id or target_channel.account_persona_id
        for s in streams:
            existing = ProcessedStream.query.filter_by(
                influencer_id=target_channel.id,
                stream_id=s["stream_id"]
            ).first()
            if not existing:
                new_stream = ProcessedStream(
                    influencer_id=target_channel.id,
                    account_persona_id=dest_persona_id,
                    stream_id=s["stream_id"],
                    stream_title=s["title"],
                    stream_url=s["url"],
                    duration=s["duration"],
                    status="queued"
                )
                db.session.add(new_stream)

        target_channel.last_checked_at = datetime.utcnow()
        db.session.commit()

        if streams:
            top_title = streams[0]["title"]
            top_views = streams[0].get("view_count", 0)
            views_str = f" ({top_views:,} views)" if top_views else ""
            clean_title = top_title.replace("🔥", "").strip()
            node_tag = f" for @{active_persona.username.lstrip('@')}" if active_persona else ""
            return jsonify({
                "success": True,
                "reply": f"🔥 Found high-viewed viral stream{node_tag} from {target_channel.channel_name}: '{clean_title}'{views_str}! Queued for AI highlight extraction.",
                "stream": {
                    "creator": target_channel.channel_name,
                    "title": clean_title,
                    "url": streams[0]["url"],
                    "duration": f"{round(streams[0].get('duration', 300)/60)} min",
                    "status": "queued"
                }
            })

    # 3. COMMAND: "scan" or "latest" or "check"
    if any(k in prompt_lower for k in ["scan", "latest", "new", "check"]):
        new_count = 0
        dest_persona_id = target_account_id
        for inf in followed:
            st = monitor.fetch_completed_streams(inf.channel_url, limit=2)
            for s in st:
                if not ProcessedStream.query.filter_by(influencer_id=inf.id, stream_id=s["stream_id"]).first():
                    db.session.add(ProcessedStream(
                        influencer_id=inf.id,
                        account_persona_id=dest_persona_id or inf.account_persona_id,
                        stream_id=s["stream_id"],
                        stream_title=s["title"],
                        stream_url=s["url"],
                        duration=s["duration"],
                        status="queued"
                    ))
                    new_count += 1
            inf.last_checked_at = datetime.utcnow()
        db.session.commit()
        node_tag = f" for @{active_persona.username.lstrip('@')}" if active_persona else ""
        return jsonify({
            "success": True,
            "reply": f"⚡ Scanned feeds{node_tag}. Found {new_count} newly finished stream(s) queued for clipping!"
        })

    # 4. GENERAL CONVERSATIONAL RESPONSE
    target_info = f"locked to node @{active_persona.username.lstrip('@')}" if active_persona else "active for all nodes"
    return jsonify({
        "success": True,
        "reply": f"🤖 Fleet Director ({target_info})! You can say:\n• 'download ep1' (pulls Episode 1 from your Telegram channel)\n• 'look for high viewed stream' (scans viral streams with millions of views)\n• 'scan latest streams' (checks for recent streams)"
    })
