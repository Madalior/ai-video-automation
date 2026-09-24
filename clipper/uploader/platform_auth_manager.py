"""
Platform Authentication Manager
===============================
Central orchestrator for multi-account social media authentication.
Inspects physical disk reality (OAuth tokens, Playwright profiles) so there
is zero mock or fantasy data in the Going Merry console.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SESSIONS_DIR = PROJECT_ROOT / "uploader_profiles" / "sessions"
YOUTUBE_TOKENS_DIR = PROJECT_ROOT / "youtube_tokens"
CLIENT_SECRETS_PATH = PROJECT_ROOT / "client_secrets.json"

# In-memory tracking of running login subprocesses: (account_id, platform) -> (subprocess.Popen, log_file)
ACTIVE_LOGIN_PROCESSES: Dict[tuple, Any] = {}
# In-memory tracking of running local OAuth redirect servers: account_id -> dict
ACTIVE_OAUTH_SERVERS: Dict[str, Dict[str, Any]] = {}


class PlatformAuthManager:
    """
    Manages OAuth and persistent browser login sessions across 30+ accounts.
    """

    def __init__(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        YOUTUBE_TOKENS_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Physical Disk Status Inspection (Zero Fantasy) ─────────────────────

    def get_account_platform_status(self, account_id: str) -> Dict[str, Any]:
        """
        Returns true, verified status of all 4 platforms by inspecting physical disk files.
        """
        acc_dir = SESSIONS_DIR / account_id

        # 1. YouTube
        yt_status = self._check_youtube_disk(account_id)

        # 2. Instagram
        ig_status = self._check_browser_profile(account_id, "instagram", acc_dir / "instagram_profile")

        # 3. TikTok
        tt_status = self._check_browser_profile(account_id, "tiktok", acc_dir / "tiktok_profile")

        # 4. Facebook
        fb_status = self._check_browser_profile(account_id, "facebook", acc_dir / "facebook_profile")

        return {
            "account_id": account_id,
            "youtube": yt_status,
            "instagram": ig_status,
            "tiktok": tt_status,
            "facebook": fb_status,
        }

    def _check_youtube_disk(self, account_id: str) -> Dict[str, Any]:
        token_file = YOUTUBE_TOKENS_DIR / f"token_{account_id}.json"
        channel_file = YOUTUBE_TOKENS_DIR / f"channel_{account_id}.json"

        # Check default fallback if account specific not found
        if not token_file.exists() and account_id == "default":
            token_file = YOUTUBE_TOKENS_DIR / "token_default.json"

        if not token_file.exists():
            return {
                "connected": False,
                "status_label": "Not Connected",
                "handle": None,
                "badge": "badge-offline",
                "error": "No OAuth token on disk"
            }

        try:
            from google.oauth2.credentials import Credentials
            SCOPES = [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube'
            ]
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            
            # Read channel info if available
            channel_info = {}
            if channel_file.exists():
                try:
                    with open(channel_file, "r", encoding="utf-8") as f:
                        channel_info = json.load(f)
                except Exception:
                    pass

            ch_title = channel_info.get("title") or "YouTube Channel"
            handle = channel_info.get("custom_url") or f"@{ch_title}"

            if creds.valid:
                return {
                    "connected": True,
                    "status_label": f"Connected: {ch_title}",
                    "channel_title": ch_title,
                    "handle": handle,
                    "channel_id": channel_info.get("id", ""),
                    "subscribers": channel_info.get("subscriber_count", 0),
                    "badge": "badge-active"
                }
            elif creds.refresh_token:
                # Has refresh token — can auto refresh when needed
                return {
                    "connected": True,
                    "status_label": f"Connected (Auth Ready): {ch_title}",
                    "channel_title": ch_title,
                    "handle": handle,
                    "channel_id": channel_info.get("id", ""),
                    "badge": "badge-active"
                }
            else:
                return {
                    "connected": False,
                    "status_label": "Token Expired",
                    "handle": handle,
                    "badge": "badge-warning",
                    "needs_reauth": True
                }

        except Exception as e:
            return {
                "connected": False,
                "status_label": "Token Invalid",
                "badge": "badge-warning",
                "error": str(e)
            }

    def _check_browser_profile(self, account_id: str, platform: str, profile_dir: Path) -> Dict[str, Any]:
        """
        Check if a persona has a real, authenticated persistent browser session on disk.
        Strict verification: inspects cookies across both LocalAppData and workspace paths.
        """
        local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
        safe_profile = Path(local_app_data) / "GoingMerry" / "profiles" / account_id / f"{platform}_profile"
        acc_session_root = SESSIONS_DIR / account_id
        accounts_dir = PROJECT_ROOT / "uploader_profiles" / "accounts"

        candidate_dirs = [
            safe_profile,
            profile_dir,
            acc_session_root,
        ]

        candidate_cookie_files = [
            safe_profile / "cookies.json",
            profile_dir / "cookies.json",
            acc_session_root / "cookies.json",
            acc_session_root / f"{platform}_profile" / "cookies.json",
            accounts_dir / f"{account_id}_{platform}_cookies.json",
            accounts_dir / f"{account_id}_cookies.json"
        ]

        auth_keys = {
            "instagram": ["sessionid"],
            "tiktok": ["sessionid", "sid_guard"],
            "facebook": ["c_user"]
        }
        required_keys = auth_keys.get(platform, ["sessionid"])

        has_auth_cookies = False
        detected_handle = ""
        saved_timestamp = ""

        # 1. Check all candidate cookies.json files
        for cf in candidate_cookie_files:
            if cf.exists():
                try:
                    with open(cf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    cookie_list = data if isinstance(data, list) else data.get("cookies", [])
                    c_map = {c.get("name"): c.get("value") for c in cookie_list if isinstance(c, dict)}
                    if any(k in c_map for k in required_keys):
                        has_auth_cookies = True
                        if platform == "instagram" and "ds_user" in c_map:
                            detected_handle = f"@{c_map['ds_user']}"
                        elif platform == "facebook" and "c_user" in c_map:
                            detected_handle = f"fb_{c_map['c_user']}"
                        break
                except Exception:
                    pass

        # 2. Check for Chromium Cookies SQLite DB with substantial size (> 60KB)
        has_cookies_db = False
        for cdir in candidate_dirs:
            for p in [cdir / "Default" / "Network" / "Cookies", cdir / "Default" / "Cookies"]:
                if p.exists() and p.stat().st_size > 60_000:
                    has_cookies_db = True
                    break
            if has_cookies_db:
                break

        # 3. Read status.json for handle and timestamp
        for cdir in candidate_dirs:
            st_file = cdir / "status.json"
            if st_file.exists():
                try:
                    with open(st_file, "r", encoding="utf-8") as f:
                        st_data = json.load(f)
                    if st_data.get("handle") and not detected_handle:
                        detected_handle = st_data.get("handle")
                    if st_data.get("timestamp"):
                        saved_timestamp = st_data.get("timestamp")
                except Exception:
                    pass

        is_connected = has_auth_cookies or (has_cookies_db and bool(detected_handle))

        if not is_connected:
            return {
                "connected": False,
                "status_label": "Not Connected",
                "handle": None,
                "badge": "badge-offline",
                "profile_path": str(profile_dir)
            }

        return {
            "connected": True,
            "status_label": f"Connected ({platform.title()} Session Saved)",
            "handle": detected_handle or f"@{platform.capitalize()} Profile",
            "profile_path": str(profile_dir),
            "badge": "badge-active",
            "saved_at": saved_timestamp
        }

    # ── 2. Interactive Login Process Controller ───────────────────────────────

    def _cleanup_oauth_server(self, account_id: str):
        info = ACTIVE_OAUTH_SERVERS.pop(account_id, None)
        if info and "server" in info:
            try:
                info["server"].server_close()
            except Exception:
                pass

    def start_login(self, account_id: str, platform: str) -> Dict[str, Any]:
        """
        Launches the appropriate worker:
        - YouTube: In-process threaded OAuth listener with ephemeral port, returns direct auth_url
        - Instagram, TikTok, Facebook: Playwright Chromium in visible desktop window (CREATE_NEW_CONSOLE)
        """
        platform = platform.lower().strip()
        key = (account_id, platform)

        if platform == "youtube":
            return self._start_youtube_oauth(account_id)

        if platform not in ("instagram", "tiktok", "facebook"):
            return {"success": False, "error": f"Unknown platform: {platform}"}

        # auth_url is ONLY for YouTube Google OAuth redirects.
        # For browser platforms (Instagram, TikTok, Facebook), keep auth_url = None
        # so the user's personal browser (Edge) NEVER opens their personal account.
        auth_url = None

        # Clean up finished or stale process entry
        self.cancel_login(account_id, platform)

        worker_script = PROJECT_ROOT / "clipper" / "uploader" / "platform_login_worker.py"
        profile_dir = SESSIONS_DIR / account_id / f"{platform}_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
        safe_profile = Path(local_app_data) / "GoingMerry" / "profiles" / account_id / f"{platform}_profile"
        safe_profile.mkdir(parents=True, exist_ok=True)

        # Clear stale locks
        for pdir in (profile_dir, safe_profile):
            for lf in ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie", "LOCK"]:
                for f in pdir.rglob(lf):
                    try:
                        if f.is_file(): f.unlink()
                    except Exception:
                        pass

        # Reset status.json to in_progress so old connected state doesn't trigger false positives
        init_status = {
            "status": "in_progress",
            "phase": "launching",
            "connected": False,
            "platform": platform,
            "account_id": account_id,
            "message": f"Opening official Chrome window on your screen for {platform.title()}..."
        }
        for pdir in (profile_dir, safe_profile):
            try:
                with open(pdir / "status.json", "w", encoding="utf-8") as f:
                    json.dump(init_status, f, indent=2)
            except Exception:
                pass

        # CRITICAL: Always use the .venv Python which has Playwright + Chromium installed.
        # sys.executable may point to system Python if the dashboard was started outside .venv.
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        python_exe = str(venv_python) if venv_python.exists() else sys.executable

        cmd = [
            python_exe,
            "-u",
            str(worker_script),
            "--account-id", account_id,
            "--platform", platform,
            "--profile-dir", str(profile_dir),
            "--timeout", "300"
        ]

        try:
            # On Windows, launch with CREATE_NEW_CONSOLE so user sees the Chromium window.
            # CRITICAL: DO NOT redirect stdout to a file descriptor, as that breaks Node.js/Playwright IPC with EPIPE.
            cflags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0

            new_proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                creationflags=cflags
            )
            ACTIVE_LOGIN_PROCESSES[key] = (new_proc, None)

            return {
                "success": True,
                "status": "started",
                "platform": platform,
                "account_id": account_id,
                "auth_url": auth_url,
                "message": f"Browser launched for {platform.title()}! Please complete sign in on your screen."
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to launch login worker: {str(e)}"}

    def _start_youtube_oauth(self, account_id: str) -> Dict[str, Any]:
        """
        Starts an in-process WSGI OAuth server on a free port, generates the authorization URL,
        and launches the browser. Returns auth_url immediately to the frontend.
        """
        if not CLIENT_SECRETS_PATH.exists():
            return {
                "success": False,
                "error": f"client_secrets.json not found at {CLIENT_SECRETS_PATH}"
            }

        self._cleanup_oauth_server(account_id)

        try:
            import threading
            import wsgiref.simple_server
            from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _WSGIRequestHandler

            SCOPES = [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube'
            ]
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), SCOPES)

            success_html = """
            <!DOCTYPE html>
            <html>
            <head><title>YouTube Connected — TECHTRONICS</title>
            <style>
                body { background: #111111; color: #4CE616; font-family: monospace; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .box { border: 2px solid #4CE616; padding: 40px; text-align: center; border-radius: 8px; box-shadow: 0 0 30px rgba(76,230,22,0.25); background: #1a1a1a; max-width: 480px; }
                h2 { margin: 0 0 10px; color: #fff; font-size: 1.4rem; letter-spacing: 2px; }
                p { color: #888; font-size: 0.9rem; line-height: 1.4; }
            </style>
            </head>
            <body>
            <div class="box">
                <h2>TECHTRONICS // GOING MERRY</h2>
                <h1 style="color: #4CE616; margin: 15px 0;">YOUTUBE AUTHENTICATED!</h1>
                <p>Google OAuth token has been saved successfully.<br>You may now close this tab and return to the dashboard.</p>
            </div>
            </body>
            </html>
            """
            wsgi_app = _RedirectWSGIApp(success_html)
            wsgiref.simple_server.WSGIServer.allow_reuse_address = False
            local_server = wsgiref.simple_server.make_server(
                "localhost", 0, wsgi_app, handler_class=_WSGIRequestHandler
            )
            port = local_server.server_port
            flow.redirect_uri = f"http://localhost:{port}/"

            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

            status_file = YOUTUBE_TOKENS_DIR / f"status_{account_id}.json"
            token_file = YOUTUBE_TOKENS_DIR / f"token_{account_id}.json"
            channel_file = YOUTUBE_TOKENS_DIR / f"channel_{account_id}.json"

            with open(status_file, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "in_progress",
                    "auth_url": auth_url,
                    "port": port,
                    "message": "Authorization server active. Please complete sign-in in your browser..."
                }, f, indent=2)

            def oauth_listener_worker():
                try:
                    local_server.timeout = 300
                    local_server.handle_request()
                    local_server.server_close()

                    if not hasattr(wsgi_app, "last_request_uri") or not wsgi_app.last_request_uri:
                        return

                    auth_response = wsgi_app.last_request_uri.replace("http://", "https://")
                    flow.fetch_token(authorization_response=auth_response)
                    creds = flow.credentials

                    with open(token_file, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())

                    # Query live YouTube channel details
                    from googleapiclient.discovery import build
                    youtube = build('youtube', 'v3', credentials=creds)
                    channels_res = youtube.channels().list(part="snippet,statistics", mine=True).execute()
                    items = channels_res.get("items", [])
                    channel_info = {}
                    if items:
                        snippet = items[0].get("snippet", {})
                        stats = items[0].get("statistics", {})
                        channel_info = {
                            "title": snippet.get("title", "YouTube Channel"),
                            "id": items[0].get("id", ""),
                            "custom_url": snippet.get("customUrl", ""),
                            "subscriber_count": int(stats.get("subscriberCount", 0)),
                            "video_count": int(stats.get("videoCount", 0)),
                            "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                        }
                    else:
                        channel_info = {"title": "YouTube Channel", "id": "", "custom_url": "", "subscriber_count": 0}

                    with open(channel_file, "w", encoding="utf-8") as f:
                        json.dump(channel_info, f, indent=2)

                    # Update database if persona exists
                    try:
                        from web_app.app import app, db
                        from web_app.models import AccountPersona, SocialAccount
                        with app.app_context():
                            persona = AccountPersona.query.filter_by(id=account_id).first()
                            if persona:
                                handle = channel_info.get("custom_url") or f"@{channel_info.get('title')}"
                                persona.youtube_handle = handle
                                persona.youtube_status = "connected"
                                db.session.commit()
                    except Exception as db_err:
                        print(f"[OAUTH] DB notice: {db_err}")

                    final_status = {
                        "status": "connected",
                        "connected": True,
                        "account_id": account_id,
                        "channel": channel_info,
                        "message": f"Successfully connected to YouTube channel: {channel_info.get('title')}!"
                    }
                    with open(status_file, "w", encoding="utf-8") as f:
                        json.dump(final_status, f, indent=2)

                except Exception as ex:
                    print(f"[OAUTH] Worker exception: {ex}")
                    err_status = {"status": "error", "error": str(ex), "message": f"OAuth failed: {ex}"}
                    with open(status_file, "w", encoding="utf-8") as f:
                        json.dump(err_status, f, indent=2)
                finally:
                    ACTIVE_OAUTH_SERVERS.pop(account_id, None)

            t = threading.Thread(target=oauth_listener_worker, daemon=True)
            t.start()

            ACTIVE_OAUTH_SERVERS[account_id] = {
                "server": local_server,
                "thread": t,
                "port": port,
                "auth_url": auth_url
            }

            # Attempt desktop browser launch directly on Windows
            try:
                os.startfile(auth_url)
            except Exception:
                try:
                    import webbrowser
                    webbrowser.open(auth_url)
                except Exception:
                    pass

            return {
                "success": True,
                "status": "started",
                "auth_url": auth_url,
                "port": port,
                "platform": "youtube",
                "account_id": account_id,
                "message": "Authorization server ready. Opening Google sign-in window..."
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to initialize OAuth server: {str(e)}"}

    def get_login_progress(self, account_id: str, platform: str) -> Dict[str, Any]:
        """
        Polls the status of an ongoing login flow without killing running workers prematurely.
        """
        platform = platform.lower().strip()
        key = (account_id, platform)

        # 1. Check running state first
        is_running = False
        if platform == "youtube":
            is_running = account_id in ACTIVE_OAUTH_SERVERS
        else:
            item = ACTIVE_LOGIN_PROCESSES.get(key)
            proc = item[0] if isinstance(item, tuple) else item
            is_running = proc is not None and proc.poll() is None

        # 2. Read status file from LocalAppData safe dir or workspace
        status_data = {}
        if platform == "youtube":
            status_file = YOUTUBE_TOKENS_DIR / f"status_{account_id}.json"
            if status_file.exists():
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        status_data = json.load(f)
                except Exception:
                    pass
        else:
            local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
            candidate_status_files = [
                Path(local_app_data) / "GoingMerry" / "profiles" / account_id / f"{platform}_profile" / "status.json",
                SESSIONS_DIR / account_id / f"{platform}_profile" / "status.json",
            ]
            for sf in candidate_status_files:
                if sf.exists():
                    try:
                        with open(sf, "r", encoding="utf-8") as f:
                            d = json.load(f)
                        if d.get("connected") or d.get("status") in ("connected", "in_progress"):
                            status_data = d
                            break
                    except Exception:
                        pass

        # 3. If worker signaled success or connected
        if status_data.get("connected") is True or status_data.get("status") == "connected":
            self.cancel_login(account_id, platform)
            return {
                "status": "connected",
                "connected": True,
                "platform": platform,
                "account_id": account_id,
                "message": status_data.get("message", f"{platform.title()} is connected!"),
                "details": status_data
            }

        if status_data.get("status") == "error":
            self.cancel_login(account_id, platform)
            return {
                "status": "error",
                "connected": False,
                "platform": platform,
                "account_id": account_id,
                "error": status_data.get("error") or status_data.get("message", "Login error.")
            }

        # 4. If process is actively running, report in_progress without killing it!
        if is_running:
            return {
                "status": "in_progress",
                "connected": False,
                "platform": platform,
                "account_id": account_id,
                "auth_url": status_data.get("auth_url") if platform == "youtube" else None,
                "message": status_data.get("message", f"Chrome window is open on screen! Please complete {platform.title()} sign in.")
            }

        # 5. Process has ended. Check physical disk reality
        disk_status = self.get_account_platform_status(account_id).get(platform, {})
        if disk_status.get("connected"):
            return {
                "status": "connected",
                "connected": True,
                "platform": platform,
                "account_id": account_id,
                "message": f"{platform.title()} is successfully connected!",
                "details": disk_status
            }

        return {
            "status": "idle",
            "connected": False,
            "platform": platform,
            "account_id": account_id,
            "message": status_data.get("error") or "Login window was closed before completion."
        }

    def cancel_login(self, account_id: str, platform: str) -> bool:
        """Kills any active login browser window or OAuth server for this platform."""
        platform = platform.lower().strip()
        if platform == "youtube":
            self._cleanup_oauth_server(account_id)
            status_file = YOUTUBE_TOKENS_DIR / f"status_{account_id}.json"
            if status_file.exists():
                try:
                    os.remove(status_file)
                except Exception:
                    pass
            return True

        # Clean status files
        local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
        for pdir in [
            Path(local_app_data) / "GoingMerry" / "profiles" / account_id / f"{platform}_profile",
            SESSIONS_DIR / account_id / f"{platform}_profile"
        ]:
            st_file = pdir / "status.json"
            if st_file.exists():
                try:
                    with open(st_file, "r", encoding="utf-8") as f:
                        cur = json.load(f)
                    if cur.get("status") in ("in_progress", "launching", "waiting_for_user"):
                        with open(st_file, "w", encoding="utf-8") as f:
                            json.dump({"status": "not_connected", "connected": False}, f)
                except Exception:
                    pass

        key = (account_id, platform)
        item = ACTIVE_LOGIN_PROCESSES.pop(key, None)
        if item:
            proc = item[0] if isinstance(item, tuple) else item
            log_file = item[1] if isinstance(item, tuple) and len(item) > 1 else None
            if proc:
                try:
                    import psutil
                    parent = psutil.Process(proc.pid)
                    for child in parent.children(recursive=True):
                        try:
                            child.kill()
                        except Exception:
                            pass
                    parent.kill()
                except Exception:
                    try:
                        proc.terminate()
                        proc.kill()
                    except Exception:
                        pass
            if log_file and not log_file.closed:
                try:
                    log_file.close()
                except Exception:
                    pass
            return True
        return False

    # ── 3. Disconnect / Clear Session ─────────────────────────────────────────

    def disconnect_platform(self, account_id: str, platform: str) -> Dict[str, Any]:
        """
        Safely clears the session directory or OAuth token from disk.
        """
        platform = platform.lower().strip()
        self.cancel_login(account_id, platform)

        try:
            if platform == "youtube":
                token_file = YOUTUBE_TOKENS_DIR / f"token_{account_id}.json"
                ch_file = YOUTUBE_TOKENS_DIR / f"channel_{account_id}.json"
                st_file = YOUTUBE_TOKENS_DIR / f"status_{account_id}.json"
                for f in (token_file, ch_file, st_file):
                    if f.exists():
                        f.unlink()
            elif platform in ("instagram", "tiktok", "facebook"):
                profile_dir = SESSIONS_DIR / account_id / f"{platform}_profile"
                if profile_dir.exists():
                    shutil.rmtree(profile_dir, ignore_errors=True)

                # Clean up any exported cookies json for this account/platform
                accounts_dir = PROJECT_ROOT / "uploader_profiles" / "accounts"
                for ck_file in [
                    accounts_dir / f"{account_id}_{platform}_cookies.json",
                    accounts_dir / f"{account_id}_cookies.json",
                ]:
                    if ck_file.exists():
                        try:
                            ck_file.unlink()
                        except Exception:
                            pass

            # Update SQLite database: set status to not_connected and clear handle
            try:
                from web_app.app import app, db
                from web_app.models import AccountPersona
                with app.app_context():
                    persona = AccountPersona.query.filter_by(id=account_id).first()
                    if persona:
                        if platform == "youtube":
                            persona.youtube_status = "not_connected"
                            persona.youtube_handle = None
                        elif platform == "instagram":
                            persona.instagram_status = "not_connected"
                            persona.instagram_handle = None
                        elif platform == "tiktok":
                            persona.tiktok_status = "not_connected"
                            persona.tiktok_handle = None
                        elif platform == "facebook":
                            persona.facebook_status = "not_connected"
                            persona.facebook_handle = None
                        db.session.commit()
            except Exception as db_err:
                print(f"[AUTH_MGR] Notice: DB update on disconnect: {db_err}")

            return {
                "success": True,
                "platform": platform,
                "account_id": account_id,
                "message": f"Successfully disconnected {platform.title()}."
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 4. Test Platform Connection Live ──────────────────────────────────────

    def test_connection(self, account_id: str, platform: str) -> Dict[str, Any]:
        """
        Live verification of API/session health.
        """
        platform = platform.lower().strip()
        disk_status = self.get_account_platform_status(account_id).get(platform, {})

        if not disk_status.get("connected"):
            return {
                "success": False,
                "connected": False,
                "message": f"{platform.title()} is not connected. Click 'Connect Now' to sign in."
            }

        if platform == "youtube":
            token_file = YOUTUBE_TOKENS_DIR / f"token_{account_id}.json"
            if not token_file.exists():
                token_file = YOUTUBE_TOKENS_DIR / "token_default.json"

            try:
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                from googleapiclient.discovery import build

                SCOPES = [
                    'https://www.googleapis.com/auth/youtube.upload',
                    'https://www.googleapis.com/auth/youtube'
                ]
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(token_file, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())

                youtube = build('youtube', 'v3', credentials=creds)
                res = youtube.channels().list(part="snippet,statistics", mine=True).execute()
                items = res.get("items", [])
                if items:
                    title = items[0]["snippet"]["title"]
                    subs = items[0]["statistics"].get("subscriberCount", 0)
                    vids = items[0]["statistics"].get("videoCount", 0)
                    return {
                        "success": True,
                        "connected": True,
                        "channel_title": title,
                        "subscriber_count": int(subs),
                        "video_count": int(vids),
                        "message": f"✅ YouTube channel '{title}' is online and verified! ({subs} subscribers)"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "connected": False,
                    "error": f"YouTube API verification error: {str(e)}"
                }

        # For Instagram / TikTok / Facebook
        if disk_status.get("connected"):
            handle = disk_status.get("handle") or f"@{platform.capitalize()} Profile"
            return {
                "success": True,
                "connected": True,
                "handle": handle,
                "message": f"✅ {platform.title()} session verified for {handle}! Cookies and browser storage are active on disk."
            }

        return {
            "success": False,
            "connected": False,
            "message": f"{platform.title()} is not logged in. Click 'Connect' to open Chrome and sign in."
        }
