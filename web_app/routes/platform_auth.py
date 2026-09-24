"""
Going Merry — Platform Authentication API Routes
================================================
Handles real, physical multi-platform connection (YouTube Google OAuth,
Instagram, TikTok, Facebook Playwright persistent browser sessions)
across all 30+ creator personas.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import AccountPersona
from clipper.uploader.platform_auth_manager import PlatformAuthManager

platform_auth_bp = Blueprint("platform_auth", __name__)
auth_mgr = PlatformAuthManager()


# ── 1. GET Real Platform Status (Disk Truth, Zero Fantasy) ────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/platform-status", methods=["GET"])
@login_required
def get_platform_status(acc_id):
    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account persona not found"}), 404

    status = auth_mgr.get_account_platform_status(acc_id)
    return jsonify({
        "success": True,
        "account_id": acc_id,
        "username": persona.username,
        "platforms": status
    })


# ── 2. POST Initiate Real Login (Opens Browser / OAuth) ───────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/connect/<string:platform>", methods=["POST"])
@login_required
def connect_platform(acc_id, platform):
    import os
    from pathlib import Path

    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account persona not found"}), 404

    platform = platform.lower().strip()
    if platform not in ("youtube", "instagram", "tiktok", "facebook"):
        return jsonify({"success": False, "message": f"Unsupported platform: {platform}"}), 400

    # For YouTube, use the in-process OAuth flow (opens user's default browser via webbrowser module)
    if platform == "youtube":
        result = auth_mgr.start_login(account_id=acc_id, platform=platform)
        return jsonify(result)

    # For browser-based platforms (IG/TT/FB), use os.startfile() on a generated batch file.
    # os.startfile() uses Windows ShellExecuteW which renders in the user's desktop session,
    # even when the Flask dashboard is running from a background/IDE process.
    from clipper.uploader.platform_auth_manager import PROJECT_ROOT, SESSIONS_DIR
    import json as _json
    import time as _time

    # Prepare profile directories and initial status
    profile_dir = SESSIONS_DIR / acc_id / f"{platform}_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
    safe_profile = Path(local_app_data) / "GoingMerry" / "profiles" / acc_id / f"{platform}_profile"
    safe_profile.mkdir(parents=True, exist_ok=True)

    init_status = {
        "status": "in_progress",
        "phase": "launching",
        "connected": False,
        "platform": platform,
        "account_id": acc_id,
        "message": f"Opening Chrome window for {platform.title()} login..."
    }
    for pdir in (profile_dir, safe_profile):
        try:
            with open(pdir / "status.json", "w", encoding="utf-8") as f:
                _json.dump(init_status, f, indent=2)
        except Exception:
            pass

    worker_script = PROJECT_ROOT / "clipper" / "uploader" / "platform_login_worker.py"
    
    # Check if running in Cloud / Linux / Docker or with VNC
    import sys
    is_linux_or_cloud = sys.platform != "win32" or bool(os.environ.get("DISPLAY"))
    
    # Calculate VNC URL for mobile streaming
    host = request.host.split(":")[0]
    vnc_url = f"http://{host}:6080/vnc.html?autoconnect=true&resize=scale"
    
    if is_linux_or_cloud:
        # Launch worker in background with virtual display (Xvfb)
        import subprocess
        python_bin = sys.executable
        cmd = [
            python_bin, "-u", str(worker_script),
            "--account-id", acc_id,
            "--platform", platform,
            "--profile-dir", str(profile_dir),
            "--timeout", "300"
        ]
        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":99"
        try:
            log_path = PROJECT_ROOT / "instance" / f"login_{acc_id}_{platform}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file = open(log_path, "a", encoding="utf-8")
            subprocess.Popen(cmd, env=env, cwd=str(PROJECT_ROOT), stdout=log_file, stderr=log_file)
        except Exception:
            subprocess.Popen(cmd, env=env, cwd=str(PROJECT_ROOT))
        
        return jsonify({
            "success": True,
            "status": "started",
            "platform": platform,
            "account_id": acc_id,
            "vnc_url": vnc_url,
            "auth_url": None,
            "message": f"Cloud browser live for {platform.title()}! Showing interactive screen..."
        })
    else:
        # Windows Desktop testing
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        bat_content = f'''@echo off
title Going Merry - {platform.title()} Login ({acc_id})
cd /d "{PROJECT_ROOT}"
echo ========================================================
echo   Going Merry - {platform.title()} Login for {persona.username}
echo   Account: {acc_id}
echo ========================================================
echo.
echo Browser will open {platform.title()} login page...
echo Log in with your account credentials.
echo When done, this window will close automatically.
echo.
"{venv_python}" -u "{worker_script}" --account-id {acc_id} --platform {platform} --profile-dir "{profile_dir}" --timeout 300
echo.
echo Done! Refresh your dashboard.
timeout /t 3
'''
        bat_path = PROJECT_ROOT / f"_temp_connect_{acc_id}_{platform}.bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        try:
            os.startfile(str(bat_path))
            return jsonify({
                "success": True,
                "status": "started",
                "platform": platform,
                "account_id": acc_id,
                "auth_url": None,
                "vnc_url": None,
                "message": f"Clean browser window launched for {platform.title()}! Complete sign-in on your screen."
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Could not open login window: {str(e)}. Run: python -m clipper.uploader.cli login --id {acc_id} --platform {platform}"
            }), 500


# ── 3. GET Active Login Progress (Polling) ────────────────────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/login-status/<string:platform>", methods=["GET"])
@login_required
def check_login_progress(acc_id, platform):
    platform = platform.lower().strip()
    result = auth_mgr.get_login_progress(account_id=acc_id, platform=platform)
    
    # If connected, ensure DB is in sync
    if result.get("connected"):
        persona = AccountPersona.query.filter_by(id=acc_id).first()
        if persona:
            setattr(persona, f"{platform}_status", "connected")
            db.session.commit()

    return jsonify(result)


# ── 4. POST Force Verification / Manual "Done" ────────────────────────────────
# ── 4. POST Force Verification / Manual "Done" ────────────────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/confirm-login/<string:platform>", methods=["POST"])
@login_required
def confirm_login(acc_id, platform):
    import os, json, time, shutil
    from pathlib import Path
    from web_app.models import SocialAccount

    platform = platform.lower().strip()
    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account persona not found"}), 404

    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
    safe_profile = Path(local_app_data) / "GoingMerry" / "profiles" / acc_id / f"{platform}_profile"
    from clipper.uploader.platform_auth_manager import SESSIONS_DIR, PROJECT_ROOT
    ws_profile = SESSIONS_DIR / acc_id / f"{platform}_profile"
    ws_session_root = SESSIONS_DIR / acc_id
    accounts_dir = PROJECT_ROOT / "uploader_profiles" / "accounts"

    # Signal worker to flush and finish
    for pdir in (safe_profile, ws_profile):
        st_file = pdir / "status.json"
        if st_file.exists() or pdir.exists():
            try:
                pdir.mkdir(parents=True, exist_ok=True)
                with open(st_file, "w", encoding="utf-8") as f:
                    json.dump({"verified_by": "user_confirmation", "status": "connected", "connected": True}, f)
            except Exception:
                pass

    # Give worker a moment to flush if still running
    time.sleep(1.5)

    # Sync any cookies found in safe_profile to workspace
    src_ck = safe_profile / "cookies.json"
    if src_ck.exists():
        for dst_ck in [
            ws_profile / "cookies.json",
            ws_session_root / "cookies.json",
            accounts_dir / f"{acc_id}_cookies.json",
            accounts_dir / f"{acc_id}_{platform}_cookies.json"
        ]:
            try:
                dst_ck.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_ck, dst_ck)
            except Exception:
                pass

    # Check true physical status
    status = auth_mgr.get_account_platform_status(acc_id).get(platform, {})

    if not status.get("connected"):
        return jsonify({
            "success": False,
            "connected": False,
            "message": f"Could not detect an active {platform.title()} login session. Please ensure you are logged in in the Chrome window."
        }), 400

    handle = status.get("handle") or getattr(persona, f"{platform}_handle", "") or f"@{platform.capitalize()} Profile"
    setattr(persona, f"{platform}_status", "connected")
    setattr(persona, f"{platform}_handle", handle)

    # Update or create SocialAccount record
    soc = SocialAccount.query.filter_by(user_id=persona.user_id, platform=platform).first()
    if not soc:
        soc = SocialAccount(
            user_id=persona.user_id,
            platform=platform,
            channel_name=handle,
            is_active=True
        )
        db.session.add(soc)
    else:
        soc.channel_name = handle
        soc.is_active = True

    db.session.commit()
    auth_mgr.cancel_login(acc_id, platform)
    return jsonify({
        "success": True,
        "connected": True,
        "message": f"Verified! {platform.title()} session saved for {handle}.",
        "details": status
    })


# ── 4b. POST Sync All Existing Sessions (from sessions/ directory) ────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/sync-existing-sessions", methods=["POST"])
@login_required
def sync_existing_sessions(acc_id):
    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account persona not found"}), 404

    # Trigger disk check on all platforms which auto-copies from sessions/
    status = auth_mgr.get_account_platform_status(acc_id)
    updated = []

    for plat in ("instagram", "tiktok", "facebook"):
        if status.get(plat, {}).get("connected"):
            setattr(persona, f"{plat}_status", "connected")
            updated.append(plat)

    db.session.commit()
    return jsonify({
        "success": True,
        "updated_platforms": updated,
        "platforms": status,
        "message": f"Synced existing sessions for {persona.username}! Connected: {', '.join(updated) if updated else 'None found on disk'}"
    })


# ── 5. POST Cancel Active Login ───────────────────────────────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/cancel-login/<string:platform>", methods=["POST"])
@login_required
def cancel_login(acc_id, platform):
    platform = platform.lower().strip()
    auth_mgr.cancel_login(acc_id, platform)
    return jsonify({
        "success": True,
        "message": f"Cancelled login window for {platform.title()}."
    })


# ── 6. POST Disconnect Platform ───────────────────────────────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/disconnect/<string:platform>", methods=["POST"])
@login_required
def disconnect_platform(acc_id, platform):
    platform = platform.lower().strip()
    persona = AccountPersona.query.filter_by(id=acc_id).first()
    if not persona:
        return jsonify({"success": False, "message": "Account persona not found"}), 404

    result = auth_mgr.disconnect_platform(account_id=acc_id, platform=platform)
    setattr(persona, f"{platform}_status", "not_connected")
    db.session.commit()
    return jsonify(result)


# ── 7. POST Live Connection Test ──────────────────────────────────────────────
@platform_auth_bp.route("/api/accounts/<string:acc_id>/test/<string:platform>", methods=["POST"])
@login_required
def test_platform_connection(acc_id, platform):
    platform = platform.lower().strip()
    result = auth_mgr.test_connection(account_id=acc_id, platform=platform)
    return jsonify(result)
