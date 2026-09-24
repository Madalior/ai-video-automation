"""
Going Merry — Dashboard Routes
Handles Multi-Account Persona Fleet, Viral View Tracking, Telegram Notifications,
and 1-Click Viral Whop Submissions.
"""
import os
import asyncio
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import (
    Clip, UploadJob, SocialAccount, MonitoredInfluencer, 
    ProcessedStream, AccountPersona, SystemSetting
)
from clipper.core.viral_detector import ViralDetector
from clipper.core.telegram_notifier import TelegramNotifier

dash_bp = Blueprint("dash", __name__)


@dash_bp.route("/dashboard")
@login_required
def dashboard():
    # 1. Fetch user system settings (viral threshold & Telegram config)
    # 1. Fetch system settings (viral threshold & Telegram config)
    settings_rows = SystemSetting.query.all()
    settings = {s.key: s.value for s in settings_rows}
    
    # Criteria views threshold
    raw_criteria = settings.get("viral_views_criteria", "1000")
    try:
        criteria_views = int(raw_criteria)
    except (ValueError, TypeError):
        criteria_views = 1000

    # 2. Fetch Unified 30+ Account Fleet
    personas = AccountPersona.query.order_by(AccountPersona.created_at.desc()).all()
    whop_count = sum(1 for p in personas if getattr(p, 'content_type', 'whop_content') == 'whop_content')
    upload_count = sum(1 for p in personas if getattr(p, 'content_type', 'whop_content') == 'upload_based')

    # 3. Fetch Clips and Viral Clips across Fleet
    clips = Clip.query.order_by(Clip.created_at.desc()).limit(50).all()
    viral_clips = Clip.query.filter(
        (Clip.is_viral == True) | (Clip.views >= criteria_views)
    ).order_by(Clip.views.desc()).all()

    # 4. Aggregated Statistics
    total_clips     = Clip.query.count()
    posted_clips    = Clip.query.filter_by(status="posted").count()
    pending_clips   = Clip.query.filter_by(status="ready").count()
    monitoring_clips= Clip.query.filter_by(status="monitoring").count()
    total_views     = sum((c.views or 0) for c in clips)
    
    # Calculate estimated bounty earned from viral videos ($5.00 Whop CPM rate)
    est_viral_bounty = sum(((c.views or 0) / 1000.0) * 5.0 for c in viral_clips)

    followed_creators = MonitoredInfluencer.query.filter_by(is_active=True).count()
    auto_detected_streams = ProcessedStream.query.count()

    stats = {
        "total_accounts": len(personas),
        "whop_accounts": whop_count,
        "upload_accounts": upload_count,
        "total_clips": total_clips,
        "posted_clips": posted_clips,
        "pending_clips": pending_clips,
        "monitoring_clips": monitoring_clips,
        "viral_count": len(viral_clips),
        "total_views": total_views,
        "est_viral_bounty": round(est_viral_bounty, 2),
        "criteria_views": criteria_views,
        "followed_creators": followed_creators,
        "auto_detected_streams": auto_detected_streams,
    }

    from clipper.uploader.platform_auth_manager import PlatformAuthManager
    auth_mgr = PlatformAuthManager()
    fleet_platform_status = {p.id: auth_mgr.get_account_platform_status(p.id) for p in personas}

    return render_template(
        "dashboard.html",
        clips=clips,
        viral_clips=viral_clips,
        personas=personas,
        fleet_platform_status=fleet_platform_status,
        settings=settings,
        criteria_views=criteria_views,
        stats=stats
    )


# ─── API: Save Viral Criteria & Telegram Settings ───────────────────────────
@dash_bp.route("/api/viral/settings", methods=["POST"])
@login_required
def save_viral_settings():
    data = request.get_json() or request.form
    criteria = data.get("viral_views_criteria", "1000").strip()
    bot_token = data.get("telegram_bot_token", "").strip()
    chat_id = data.get("telegram_chat_id", "").strip()

    def set_val(key, val):
        setting = SystemSetting.query.filter_by(user_id=current_user.id, key=key).first()
        if not setting:
            setting = SystemSetting(user_id=current_user.id, key=key, value=val)
            db.session.add(setting)
        else:
            setting.value = val

    set_val("viral_views_criteria", criteria)
    set_val("telegram_bot_token", bot_token)
    set_val("telegram_chat_id", chat_id)

    db.session.commit()
    return jsonify({
        "success": True, 
        "message": f"Settings saved. Viral threshold updated to {criteria} views."
    })


# ─── API: Test Telegram Notification ─────────────────────────────────────────
@dash_bp.route("/api/telegram/test", methods=["POST"])
@login_required
def test_telegram():
    data = request.get_json() or {}
    token = data.get("bot_token")
    chat_id = data.get("chat_id")

    if not token or not chat_id:
        token_setting = SystemSetting.query.filter_by(user_id=current_user.id, key="telegram_bot_token").first()
        chat_setting = SystemSetting.query.filter_by(user_id=current_user.id, key="telegram_chat_id").first()
        token = token or (token_setting.value if token_setting else "")
        chat_id = chat_id or (chat_setting.value if chat_setting else "")

    if not token or not chat_id:
        return jsonify({"success": False, "message": "Telegram Bot Token and Chat ID must be configured."}), 400

    notifier = TelegramNotifier(bot_token=token, chat_id=chat_id)
    res = notifier.test_connection()
    return jsonify({"success": res.get("success", False), "message": res.get("message", "")})


# ─── API: Run Live Viral Views Check across all clips ─────────────────────────
@dash_bp.route("/api/viral/check-now", methods=["POST"])
@login_required
def check_viral_now():
    # Fetch user criteria
    setting = SystemSetting.query.filter_by(user_id=current_user.id, key="viral_views_criteria").first()
    criteria = int(setting.value) if setting and setting.value.isdigit() else 1000

    token_s = SystemSetting.query.filter_by(user_id=current_user.id, key="telegram_bot_token").first()
    chat_s = SystemSetting.query.filter_by(user_id=current_user.id, key="telegram_chat_id").first()
    bot_token = token_s.value if token_s else None
    chat_id = chat_s.value if chat_s else None

    detector = ViralDetector(
        default_criteria_views=criteria,
        telegram_bot_token=bot_token,
        telegram_chat_id=chat_id
    )

    results = detector.scan_all_clips(db_session=db.session)
    viral_found = [r for r in results if r.get("is_viral")]

    return jsonify({
        "success": True,
        "total_scanned": len(results),
        "viral_count": len(viral_found),
        "results": results
    })


# ─── API: Manual 1-Click Whop Submission for Viral Clip ───────────────────────
@dash_bp.route("/api/clips/<int:clip_id>/submit-whop", methods=["POST"])
@login_required
def manual_submit_whop(clip_id):
    clip = Clip.query.filter_by(id=clip_id, user_id=current_user.id).first()
    if not clip:
        return jsonify({"success": False, "message": "Clip not found"}), 404

    target_url = clip.post_url or clip.source_url
    if not target_url:
        return jsonify({"success": False, "message": "Clip has no live public post URL"}), 400

    try:
        from whop_link_submission import submit_link
        # Run asynchronous submit_link in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sub_res = loop.run_until_complete(
            submit_link(
                video_url=target_url,
                platform="youtube",
                headless=True
            )
        )
        loop.close()

        # Update clip note or status
        clip.status = "submitted_whop"
        db.session.commit()

        return jsonify({
            "success": True, 
            "status": sub_res.get("status"), 
            "message": f"Successfully submitted viral clip to Whop! Link: {target_url}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Whop submission error: {str(e)}"}), 500


# ─── API: Manage Multi-Platform Account Personas ─────────────────────────────
@dash_bp.route("/api/accounts/new", methods=["POST"])
@login_required
def create_account_persona():
    data = request.get_json() or request.form
    gmail = data.get("gmail", "").strip()
    username = data.get("username", "").strip()
    
    # If username not provided, auto-derive from gmail e.g. creator25@gmail.com -> @creator25
    if not username and gmail:
        username = f"@{gmail.split('@')[0]}"
    
    name = data.get("name", "").strip() or (username.lstrip("@") if username else "Creator Account")
    niche = data.get("niche", "general").strip()
    content_type = data.get("content_type", "whop_content").strip() # whop_content | upload_based
    fleet = data.get("fleet", "whop" if content_type == "whop_content" else "general").strip()

    if not username and not gmail:
        return jsonify({"success": False, "message": "Either Gmail address or Username is required"}), 400

    clean_user = username if username.startswith("@") else f"@{username}"
    # Generate globally unique id
    import uuid
    persona_id = f"acc_{uuid.uuid4().hex[:8]}"

    persona = AccountPersona(
        id=persona_id,
        user_id=current_user.id,
        username=clean_user,
        name=name,
        gmail=gmail,
        content_type=content_type,
        niche=niche,
        fleet=fleet,
        youtube_handle=data.get("youtube_handle", "").strip(),
        instagram_handle=data.get("instagram_handle", "").strip(),
        facebook_handle=data.get("facebook_handle", "").strip(),
        tiktok_handle=data.get("tiktok_handle", "").strip(),
        youtube_status="not_connected",
        instagram_status="not_connected",
        facebook_status="not_connected",
        tiktok_status="not_connected",
    )
    db.session.add(persona)
    db.session.commit()

    # Sync to real uploader profile manager for browser sessions
    try:
        from clipper.uploader.profiles_manager import ProfileManager
        pm = ProfileManager()
        platforms_list = []
        if persona.youtube_handle: platforms_list.append("youtube")
        if persona.instagram_handle: platforms_list.append("instagram")
        if persona.facebook_handle: platforms_list.append("facebook")
        if persona.tiktok_handle: platforms_list.append("tiktok")
        if not platforms_list: platforms_list = ["youtube", "tiktok", "instagram"]
        
        pm.add_account(
            account_id=persona.id,
            name=persona.name,
            platforms=platforms_list,
            fleet=persona.fleet,
            niche=persona.niche,
            notes=f"Gmail: {persona.gmail} | Type: {persona.content_type}"
        )
    except Exception as pm_err:
        print(f"[PROFILE_MGR] Notice: {pm_err}")

    return jsonify({
        "success": True, 
        "persona": persona.to_dict(),
        "message": f"Account '{clean_user}' ({gmail or 'No Gmail'}) saved as {content_type.replace('_', ' ').title()}."
    })


@dash_bp.route("/api/accounts/<string:acc_id>/delete", methods=["POST"])
@login_required
def delete_account_persona(acc_id):
    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account not found"}), 404

    db.session.delete(persona)
    db.session.commit()

    # Sync deletion to ProfileManager
    try:
        from clipper.uploader.profiles_manager import ProfileManager
        pm = ProfileManager()
        reg = pm._load_registry()
        if acc_id in reg.get("accounts", {}):
            del reg["accounts"][acc_id]
            pm._save_registry(reg)
    except Exception:
        pass

    return jsonify({"success": True, "message": f"Account {acc_id} deleted."})
