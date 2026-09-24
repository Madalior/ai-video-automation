"""
Browser Automation Engine for Multi-Account Uploader
====================================================
Launches and manages persistent Playwright browser sessions with
anti-detection stealth settings and optional proxy routing.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
from playwright.sync_api import sync_playwright, BrowserContext, Page
from clipper.uploader.profiles_manager import ProfileManager


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)

PLATFORM_LOGIN_URLS = {
    "youtube": "https://studio.youtube.com",
    "tiktok": "https://www.tiktok.com/creator-center/upload",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com/login",
    "x": "https://x.com/login"
}


class BrowserEngine:
    """
    Manages Playwright persistent browser contexts.
    Each account gets its own isolated disk-backed user data directory.
    """

    def __init__(self, profile_manager: Optional[ProfileManager] = None):
        self.profile_mgr = profile_manager or ProfileManager()

    @contextmanager
    def open_session(
        self,
        account_id: str,
        headless: bool = True,
        slow_mo: int = 50
    ):
        """
        Context manager yielding (context, page) for an isolated account profile.
        Automatically saves cookies, local storage, and history on exit.
        """
        account = self.profile_mgr.get_account(account_id)
        if not account:
            # Auto-register if not present
            self.profile_mgr.add_account(account_id)
            account = self.profile_mgr.get_account(account_id)

        # Workspace session directory
        session_dir = self.profile_mgr.base_dir / "sessions" / account_id
        session_dir.mkdir(parents=True, exist_ok=True)

        if sys.platform != "win32":
            safe_session_dir = session_dir / "uploader_session"
            use_channel = None
        else:
            local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
            safe_session_dir = Path(local_app_data) / "GoingMerry" / "profiles" / account_id / "uploader_session"
            edge_exe_candidates = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]
            has_edge = any(os.path.exists(p) for p in edge_exe_candidates)
            use_channel = "msedge" if has_edge else "chrome"

        safe_session_dir.mkdir(parents=True, exist_ok=True)

        # Clear stale locks
        for lf in ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie", "LOCK"]:
            for f in safe_session_dir.rglob(lf):
                try:
                    if f.is_file(): f.unlink()
                except Exception:
                    pass

        proxy_config = None
        if account.get("proxy"):
            proxy_config = {"server": account["proxy"]}

        chrome_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--disable-features=IsolateOrigins,site-per-process",
            "--start-maximized"
        ]
        if sys.platform != "win32":
            chrome_args.extend([
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ])

        playwright = sync_playwright().start()
        try:
            launch_kwargs = {
                "user_data_dir": str(safe_session_dir),
                "headless": headless,
                "args": chrome_args,
                "slow_mo": slow_mo,
                "viewport": None,
                "user_agent": DEFAULT_USER_AGENT,
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "permissions": ["clipboard-read", "clipboard-write"]
            }
            if proxy_config:
                launch_kwargs["proxy"] = proxy_config
            if use_channel:
                launch_kwargs["channel"] = use_channel

            context = playwright.chromium.launch_persistent_context(**launch_kwargs)

            # Mask navigator.webdriver
            page = context.pages[0] if context.pages else context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Load any saved cookies from workspace or localappdata into context
            local_app_data = os.environ.get("LOCALAPPDATA", "")
            cookie_candidates = [
                self.profile_mgr.base_dir / "accounts" / f"{account_id}_instagram_cookies.json",
                self.profile_mgr.base_dir / "accounts" / f"{account_id}_cookies.json",
                session_dir / "instagram_profile" / "cookies.json",
                session_dir / "cookies.json",
                safe_session_dir / "cookies.json",
            ]
            if local_app_data:
                cookie_candidates.append(Path(local_app_data) / "GoingMerry" / "profiles" / account_id / "instagram_profile" / "cookies.json")

            for ck_file in cookie_candidates:
                if ck_file.exists():
                    try:
                        with open(ck_file, "r", encoding="utf-8") as f:
                            saved_cookies = json.load(f)
                        if isinstance(saved_cookies, list) and saved_cookies:
                            valid_cookies = []
                            for c in saved_cookies:
                                if isinstance(c, dict) and "name" in c and "value" in c:
                                    cookie_entry = {
                                        "name": c["name"],
                                        "value": c["value"],
                                        "domain": c.get("domain", ".instagram.com"),
                                        "path": c.get("path", "/")
                                    }
                                    if "secure" in c: cookie_entry["secure"] = c["secure"]
                                    if "httpOnly" in c: cookie_entry["httpOnly"] = c["httpOnly"]
                                    s_site = c.get("sameSite")
                                    if s_site in ["Strict", "Lax", "None"]:
                                        cookie_entry["sameSite"] = s_site
                                    valid_cookies.append(cookie_entry)
                            if valid_cookies:
                                context.add_cookies(valid_cookies)
                                print(f"[BROWSER_ENGINE] Loaded {len(valid_cookies)} cookies from {ck_file.name}")
                            break
                    except Exception as ce:
                        print(f"[BROWSER_ENGINE] Notice loading cookies from {ck_file}: {ce}")

            yield context, page

        finally:
            try:
                context.close()
            except Exception:
                pass
            playwright.stop()

    def interactive_login(self, account_id: str, platform: str = "youtube") -> bool:
        """
        Opens a visible Google Chrome window with the specified profile.
        Allows the user to log in manually. Once closed, the session is saved permanently.
        """
        target_url = PLATFORM_LOGIN_URLS.get(platform.lower(), "https://studio.youtube.com")
        print("\n" + "=" * 65)
        print(f"🔑 1-TIME LOGIN SESSION FOR ACCOUNT: [{account_id.upper()}]")
        print(f"🎯 Target Platform: {platform.capitalize()} ({target_url})")
        print("=" * 65)
        print("Opening Google Chrome window...")
        print("👉 Log into your account in the browser.")
        print("👉 When finished and logged in, simply close the browser window (or press Enter in terminal).\n")

        with self.open_session(account_id=account_id, headless=False, slow_mo=0) as (context, page):
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for user to finish (either close browser OR press Enter in terminal)
            print("[BROWSER] Chrome is open. Waiting for you to complete login...")
            print("👉 Press [ENTER] in this terminal when you are done logging in, OR simply close the browser window.")

            import threading
            user_finished = threading.Event()

            def wait_for_enter():
                try:
                    input()
                    user_finished.set()
                except Exception:
                    pass

            t = threading.Thread(target=wait_for_enter, daemon=True)
            t.start()

            try:
                while not user_finished.is_set() and len(context.pages) > 0 and not page.is_closed():
                    time.sleep(0.5)
            except Exception:
                pass


            # Auto-save cookies across all targets
            try:
                cookies = context.cookies()
                accounts_dir = self.profile_mgr.base_dir / "accounts"
                accounts_dir.mkdir(parents=True, exist_ok=True)
                
                target_cookie_files = [
                    accounts_dir / f"{account_id}_cookies.json",
                    accounts_dir / f"{account_id}_{platform}_cookies.json",
                    session_dir / "cookies.json",
                    session_dir / f"{platform}_profile" / "cookies.json",
                    safe_session_dir / "cookies.json",
                ]
                for cf in target_cookie_files:
                    try:
                        cf.parent.mkdir(parents=True, exist_ok=True)
                        with open(cf, "w", encoding="utf-8") as f:
                            json.dump(cookies, f, indent=2)
                    except Exception:
                        pass
                print(f"[BROWSER] 🍪 Saved {len(cookies)} cookies across all profile directories.")

                # Extract handle
                detected_handle = ""
                cookie_map = {c.get("name"): c.get("value") for c in cookies if isinstance(c, dict)}
                if platform == "instagram":
                    if "ds_user" in cookie_map:
                        detected_handle = f"@{cookie_map['ds_user']}"
                    elif "ds_user_id" in cookie_map:
                        detected_handle = f"user_{cookie_map['ds_user_id']}"
                elif platform == "facebook":
                    if "c_user" in cookie_map:
                        detected_handle = f"fb_{cookie_map['c_user']}"
                elif platform == "tiktok":
                    if "sessionid" in cookie_map:
                        detected_handle = "@tiktok_creator"

                # Write status.json
                st_data = {
                    "status": "connected",
                    "connected": True,
                    "platform": platform,
                    "account_id": account_id,
                    "handle": detected_handle or f"@{platform.capitalize()} Profile",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "message": f"Successfully connected to {platform.title()}!"
                }
                for st_dir in [session_dir / f"{platform}_profile", safe_session_dir]:
                    try:
                        st_dir.mkdir(parents=True, exist_ok=True)
                        with open(st_dir / "status.json", "w", encoding="utf-8") as f:
                            json.dump(st_data, f, indent=2)
                    except Exception:
                        pass

                # Update database
                try:
                    from web_app.app import app, db
                    from web_app.models import AccountPersona, SocialAccount
                    with app.app_context():
                        persona = AccountPersona.query.filter_by(id=account_id).first()
                        if persona:
                            setattr(persona, f"{platform}_status", "connected")
                            if detected_handle:
                                setattr(persona, f"{platform}_handle", detected_handle)
                            soc = SocialAccount.query.filter_by(user_id=persona.user_id, platform=platform).first()
                            if not soc:
                                soc = SocialAccount(
                                    user_id=persona.user_id,
                                    platform=platform,
                                    channel_name=detected_handle or f"{persona.username}_{platform[:2]}",
                                    is_active=True
                                )
                                db.session.add(soc)
                            else:
                                soc.channel_name = detected_handle or soc.channel_name
                                soc.is_active = True
                            db.session.commit()
                            print(f"[BROWSER] 💾 Database updated for persona '{account_id}' -> {platform} connected!")
                except Exception as db_err:
                    print(f"[BROWSER] DB notice: {db_err}")

            except Exception as e:
                print(f"[BROWSER] Warning saving cookies: {e}")

        print(f"[BROWSER] ✅ Session saved successfully for account '{account_id}'!\n")
        return True

