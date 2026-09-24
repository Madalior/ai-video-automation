"""
Platform Interactive Login Worker (Isolated Playwright Chromium)
================================================================
Launches a 100% isolated, clean Chromium browser window on screen for
Instagram, TikTok, or Facebook sign-in.
- Uses dedicated profile in LocalAppData to eliminate OneDrive sharing violations.
- Never touches or launches the user's personal Edge or Chrome profiles.
- Monitors authentication cookies in real time.
- Syncs session cookies to disk and updates Going Merry database.
"""

import os
import sys
import json
import time
import ctypes
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)

PLATFORM_CONFIG = {
    "instagram": {
        "login_url": "https://www.instagram.com/accounts/login/",
        "auth_cookies": ["sessionid"],
        "name": "Instagram"
    },
    "tiktok": {
        "login_url": "https://www.tiktok.com/login",
        "auth_cookies": ["sessionid", "sid_guard"],
        "name": "TikTok"
    },
    "facebook": {
        "login_url": "https://www.facebook.com/login",
        "auth_cookies": ["c_user", "xs"],
        "name": "Facebook"
    }
}


def get_safe_profile_dir(account_id: str, platform: str) -> Path:
    """
    Returns an isolated profile directory in LocalAppData outside OneDrive.
    Prevents OneDrive ERROR_SHARING_VIOLATION (0x20) and ProcessSingleton lock conflicts.
    """
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
    safe_dir = Path(local_app_data) / "GoingMerry" / "profiles" / account_id / f"{platform}_profile"
    safe_dir.mkdir(parents=True, exist_ok=True)
    return safe_dir


def _clean_stale_locks(profile_dir: Path):
    """Remove stale Chromium/Edge lock files and kill any orphaned processes holding them."""
    try:
        import psutil
        dir_str = str(profile_dir).lower()
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = " ".join(p.info.get('cmdline') or []).lower()
                pname = p.info['name'].lower()
                if dir_str in cmd and ('chrome' in pname or 'msedge' in pname or 'node' in pname):
                    p.kill()
            except Exception:
                pass
    except Exception:
        pass

    time.sleep(0.3)
    lock_names = ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie", "LOCK"]
    for name in lock_names:
        for f in profile_dir.rglob(name):
            try:
                if f.is_file():
                    f.unlink()
            except Exception:
                pass


def _bring_window_to_front(target_title_substring: str = "instagram"):
    """Brings only the target platform window to the foreground without stealing personal browser windows."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    # Only target the specific platform window, never random Chrome/Edge personal windows
                    if target_title_substring.lower() in title:
                        user32.ShowWindow(hwnd, SW_RESTORE)
                        user32.SetForegroundWindow(hwnd)
                        user32.BringWindowToTop(hwnd)
                        return False
            return True
        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(EnumProc(cb), 0)
    except Exception:
        pass


def run_interactive_login(account_id: str, platform: str, timeout_sec: int = 300):
    platform = platform.lower().strip()
    config = PLATFORM_CONFIG.get(platform)
    if not config:
        print(json.dumps({"success": False, "error": f"Unsupported platform: {platform}"}))
        return False

    # 1. LocalAppData safe profile (outside OneDrive sync)
    safe_profile = get_safe_profile_dir(account_id, platform)
    _clean_stale_locks(safe_profile)

    # 2. Workspace mirror directory (for Going Merry status & dispatcher checks)
    workspace_profile = PROJECT_ROOT / "uploader_profiles" / "sessions" / account_id / f"{platform}_profile"
    workspace_profile.mkdir(parents=True, exist_ok=True)
    _clean_stale_locks(workspace_profile)

    def write_status(data):
        for target_dir in (safe_profile, workspace_profile):
            try:
                status_file = target_dir / "status.json"
                with open(status_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception as err:
                print(f"[{platform.upper()}_WORKER] Error writing status.json to {target_dir}: {err}")

    # Write initial launching status
    write_status({
        "status": "in_progress",
        "phase": "launching",
        "connected": False,
        "platform": platform,
        "account_id": account_id,
        "message": f"Opening official Chrome window on your screen for {config['name']}..."
    })

    print(f"[{platform.upper()}_WORKER] Starting isolated interactive login for {platform} (Account: {account_id})")
    print(f"[{platform.upper()}_WORKER] Isolated Profile (Safe Local Disk): {safe_profile}")

    try:
        from playwright.sync_api import sync_playwright

        edge_exe_candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        has_edge = any(os.path.exists(p) for p in edge_exe_candidates)
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        if has_edge:
            use_channel = "msedge"
            browser_name = "Microsoft Edge"
        elif os.path.exists(chrome_exe):
            use_channel = "chrome"
            browser_name = "Google Chrome"
        else:
            use_channel = None
            browser_name = "Chromium"

        with sync_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(safe_profile),
                "headless": False,
                "no_viewport": True,
                "ignore_default_args": ["--enable-automation"],
                "user_agent": DEFAULT_USER_AGENT,
                "args": [
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-infobars',
                    '--start-maximized',
                ]
            }
            if use_channel:
                launch_kwargs["channel"] = use_channel
                print(f"[{platform.upper()}_WORKER] Launching Real {browser_name} (channel='{use_channel}')...")
            else:
                print(f"[{platform.upper()}_WORKER] Launching bundled Chromium...")

            context = p.chromium.launch_persistent_context(**launch_kwargs)
            pages = context.pages
            page = pages[0] if pages else context.new_page()

            # Anti-detection stealth: mask navigator.webdriver
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            print(f"[{platform.upper()}_WORKER] Navigating to {config['login_url']}...")
            try:
                page.goto(config["login_url"], wait_until="domcontentloaded", timeout=45000)
            except Exception as nav_err:
                print(f"[{platform.upper()}_WORKER] Initial nav note: {nav_err}")

            page.bring_to_front()
            time.sleep(1)
            _bring_window_to_front()

            write_status({
                "status": "in_progress",
                "phase": "waiting_for_user",
                "connected": False,
                "platform": platform,
                "account_id": account_id,
                "message": f"Clean {browser_name} open! Please enter your credentials for {config['name']}."
            })

            print(f"[{platform.upper()}_WORKER] Isolated window active on screen! Waiting for sign-in ({timeout_sec}s timeout)...")
            start_time = time.time()
            logged_in = False
            detected_handle = ""
            last_tick = 0
            last_good_cookies = []

            while time.time() - start_time < timeout_sec:
                # Check if browser was closed by user
                try:
                    if not context.pages or (page and page.is_closed()):
                        print(f"[{platform.upper()}_WORKER] Browser page was closed by user.")
                        break
                except Exception:
                    break

                try:
                    current_url = page.url.lower() if page else ""
                    cookies = context.cookies()
                    if cookies:
                        last_good_cookies = cookies

                    cookie_names = {c.get("name") for c in cookies}

                    if platform == "instagram":
                        # Strict check: MUST have sessionid to be authenticated!
                        if "sessionid" in cookie_names:
                            for c in cookies:
                                if c.get("name") == "ds_user":
                                    detected_handle = f"@{c['value']}"
                                elif c.get("name") == "ds_user_id" and not detected_handle:
                                    detected_handle = f"user_{c['value']}"

                            if not detected_handle:
                                try:
                                    if "instagram.com" in current_url and "/login" not in current_url:
                                        prof = page.locator("a[href*='/'][role='link'] img[alt*='profile picture']").first
                                        alt = prof.get_attribute("alt") if prof.count() > 0 else None
                                        if alt and "'" in alt:
                                            detected_handle = f"@{alt.split(\"'s profile picture\")[0].strip()}"
                                except Exception:
                                    pass

                            logged_in = True
                            print(f"[{platform.upper()}_WORKER] ✅ Instagram session verified! (handle: {detected_handle or 'authenticated'})")
                            write_status({
                                "status": "in_progress",
                                "phase": "logged_in_finalizing",
                                "connected": True,
                                "platform": platform,
                                "account_id": account_id,
                                "handle": detected_handle or "@Instagram Profile",
                                "message": f"Login detected! Finalizing session for {detected_handle or 'Instagram'}..."
                            })
                            time.sleep(3)
                            break

                    elif platform == "tiktok":
                        if "sessionid" in cookie_names or "sid_guard" in cookie_names:
                            logged_in = True
                            print(f"[{platform.upper()}_WORKER] ✅ TikTok session verified!")
                            time.sleep(3)
                            break

                    elif platform == "facebook":
                        if "c_user" in cookie_names:
                            logged_in = True
                            for c in cookies:
                                if c.get("name") == "c_user":
                                    detected_handle = f"fb_{c['value']}"
                            print(f"[{platform.upper()}_WORKER] ✅ Facebook session verified!")
                            time.sleep(3)
                            break

                except Exception:
                    pass

                # Also check status.json in case user clicked "I HAVE FINISHED LOGGING IN" in dashboard
                for st_dir in (workspace_profile, safe_profile):
                    st_file = st_dir / "status.json"
                    if st_file.exists():
                        try:
                            with open(st_file, "r", encoding="utf-8") as f:
                                st = json.load(f)
                            if st.get("verified_by") == "user_confirmation":
                                print(f"[{platform.upper()}_WORKER] Confirmed connected via dashboard button!")
                                logged_in = True
                                break
                        except Exception:
                            pass
                if logged_in:
                    break

                elapsed = int(time.time() - start_time)
                if elapsed - last_tick >= 10:
                    last_tick = elapsed
                    print(f"[{platform.upper()}_WORKER] Waiting for login ({elapsed}s / {timeout_sec}s)...")

                time.sleep(1.5)

            # Final cookie extraction
            final_cookies = []
            try:
                final_cookies = context.cookies()
            except Exception:
                final_cookies = last_good_cookies

            if not final_cookies and last_good_cookies:
                final_cookies = last_good_cookies

            # If closed after login, verify strictly from last good cookies
            if not logged_in and final_cookies:
                c_names = {c.get("name") for c in final_cookies}
                if platform == "instagram" and "sessionid" in c_names:
                    logged_in = True
                    for c in final_cookies:
                        if c.get("name") == "ds_user":
                            detected_handle = f"@{c['value']}"
                        elif c.get("name") == "ds_user_id" and not detected_handle:
                            detected_handle = f"user_{c['value']}"
                elif platform == "tiktok" and ("sessionid" in c_names or "sid_guard" in c_names):
                    logged_in = True
                elif platform == "facebook" and "c_user" in c_names:
                    logged_in = True
                    for c in final_cookies:
                        if c.get("name") == "c_user":
                            detected_handle = f"fb_{c['value']}"

            if logged_in:
                # Save cookies to disk across all targets
                if final_cookies:
                    accounts_dir = PROJECT_ROOT / "uploader_profiles" / "accounts"
                    accounts_dir.mkdir(parents=True, exist_ok=True)
                    account_session_root = PROJECT_ROOT / "uploader_profiles" / "sessions" / account_id
                    account_session_root.mkdir(parents=True, exist_ok=True)

                    target_cookie_files = [
                        safe_profile / "cookies.json",
                        workspace_profile / "cookies.json",
                        account_session_root / "cookies.json",
                        account_session_root / f"{platform}_profile" / "cookies.json",
                        accounts_dir / f"{account_id}_cookies.json",
                        accounts_dir / f"{account_id}_{platform}_cookies.json"
                    ]
                    for cf in target_cookie_files:
                        try:
                            cf.parent.mkdir(parents=True, exist_ok=True)
                            with open(cf, "w", encoding="utf-8") as f:
                                json.dump(final_cookies, f, indent=2)
                        except Exception as ck_err:
                            print(f"[{platform.upper()}_WORKER] Warning saving to {cf}: {ck_err}")

                    # Sync Chromium Cookies DB across both workspace_profile and account_session_root
                    try:
                        import shutil
                        src_net = safe_profile / "Default" / "Network"
                        dst_targets = [
                            workspace_profile / "Default" / "Network",
                            account_session_root / "Default" / "Network",
                            account_session_root / f"{platform}_profile" / "Default" / "Network"
                        ]
                        if src_net.exists():
                            for dst_net in dst_targets:
                                dst_net.mkdir(parents=True, exist_ok=True)
                                for item in ["Cookies", "Cookies-journal"]:
                                    if (src_net / item).exists():
                                        shutil.copy2(src_net / item, dst_net / item)
                    except Exception:
                        pass

                    print(f"[{platform.upper()}_WORKER] Saved {len(final_cookies)} session cookies across all workspace paths.")

                result = {
                    "success": True,
                    "status": "connected",
                    "connected": True,
                    "platform": platform,
                    "account_id": account_id,
                    "handle": detected_handle or f"@{platform.capitalize()} Profile",
                    "profile_dir": str(safe_profile),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "message": f"Successfully connected to {config['name']}!"
                }
                write_status(result)

                # Update database
                try:
                    from web_app.app import app, db
                    from web_app.models import AccountPersona, SocialAccount

                    with app.app_context():
                        persona = AccountPersona.query.filter_by(id=account_id).first()
                        if persona:
                            if platform == "instagram":
                                persona.instagram_status = "connected"
                                if detected_handle: persona.instagram_handle = detected_handle
                            elif platform == "tiktok":
                                persona.tiktok_status = "connected"
                                if detected_handle: persona.tiktok_handle = detected_handle
                            elif platform == "facebook":
                                persona.facebook_status = "connected"
                                if detected_handle: persona.facebook_handle = detected_handle

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
                                soc.is_active = True

                            db.session.commit()
                            print(f"[{platform.upper()}_WORKER] Updated DB for persona '{account_id}' -> connected")
                except Exception as db_err:
                    print(f"[{platform.upper()}_WORKER] DB update notice: {db_err}")

                time.sleep(2.0)
                try:
                    context.close()
                except Exception:
                    pass

                _clean_stale_locks(safe_profile)
                print(json.dumps(result))
                return True

            else:
                try:
                    context.close()
                except Exception:
                    pass

                _clean_stale_locks(safe_profile)
                result = {
                    "success": False,
                    "status": "not_connected",
                    "connected": False,
                    "platform": platform,
                    "account_id": account_id,
                    "error": "Login window was closed or timed out before completion (no session detected)."
                }
                write_status(result)
                print(json.dumps(result))
                return False

    except Exception as e:
        err_msg = str(e)
        print(f"[{platform.upper()}_WORKER] Exception: {err_msg}")
        _clean_stale_locks(safe_profile)
        result = {
            "success": False,
            "status": "error",
            "connected": False,
            "platform": platform,
            "account_id": account_id,
            "error": err_msg
        }
        write_status(result)
        print(json.dumps(result))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive Platform Login Worker")
    parser.add_argument("--account-id", type=str, required=True, help="Unique account persona ID")
    parser.add_argument("--platform", type=str, required=True, choices=["instagram", "tiktok", "facebook"])
    parser.add_argument("--profile-dir", type=str, default="", help="Custom persistent profile directory")
    parser.add_argument("--timeout", type=int, default=300, help="Login timeout in seconds (default: 300)")
    args = parser.parse_args()

    run_interactive_login(
        account_id=args.account_id,
        platform=args.platform,
        timeout_sec=args.timeout
    )
