"""
YouTube Studio Interactive Authenticator (Option B - Persistent Chrome Profile)
=============================================================================
Launches official Google Chrome on screen with an isolated profile directory.
You log in manually to YouTube Studio (https://studio.youtube.com) with your channel.
Because this runs the official signed Chrome binary with no automation flags:
- Google NEVER blocks login ("browser not secure" is bypassed).
- No Google Cloud Console projects needed.
- No client_secrets.json needed.
- No 10,000 quota units / 6 video limit.
- Permanent session saved directly to disk.
"""

import os
import sys
import json
import time
import shutil
import sqlite3
import argparse
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_profile_dirs(account_id: str):
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\vijay\AppData\Local")
    safe_profile = Path(local_app_data) / "GoingMerry" / "profiles" / account_id / "youtube_profile"
    safe_profile.mkdir(parents=True, exist_ok=True)
    
    workspace_profile = PROJECT_ROOT / "uploader_profiles" / "sessions" / account_id / "youtube_profile"
    workspace_profile.mkdir(parents=True, exist_ok=True)
    return safe_profile, workspace_profile


def find_chrome_exe():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def check_youtube_cookies_in_db(profile_dir: Path) -> bool:
    """Checks SQLite cookies database for active YouTube auth cookies."""
    cookie_paths = [
        profile_dir / "Default" / "Network" / "Cookies",
        profile_dir / "Default" / "Cookies",
    ]
    for p in cookie_paths:
        if not p.exists():
            continue
        try:
            temp_copy = profile_dir / "yt_check_temp.db"
            try:
                shutil.copy2(p, temp_copy)
            except Exception:
                continue
            conn = sqlite3.connect(temp_copy)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM cookies WHERE host_key LIKE '%youtube.com%' AND name IN ('LOGIN_INFO', 'SAPISID', 'SID', 'SSID')")
            rows = cursor.fetchall()
            conn.close()
            try:
                temp_copy.unlink(missing_ok=True)
            except Exception:
                pass
            if rows and len(rows) >= 1:
                return True
        except Exception:
            pass
    return False


def update_accounts_json(account_id: str):
    """Ensures account exists in accounts.json with youtube in platforms."""
    acc_json_path = PROJECT_ROOT / "uploader_profiles" / "accounts.json"
    try:
        data = {"version": "1.0", "accounts": {}}
        if acc_json_path.exists():
            with open(acc_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        accounts = data.setdefault("accounts", {})
        if account_id in accounts:
            platforms = accounts[account_id].setdefault("platforms", [])
            if "youtube" not in platforms:
                platforms.append("youtube")
        else:
            accounts[account_id] = {
                "id": account_id,
                "name": account_id,
                "fleet": "default",
                "platforms": ["youtube"],
                "created_at": datetime.now().isoformat()
            }
        data["updated_at"] = datetime.now().isoformat()
        with open(acc_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[NOTE] accounts.json update note: {e}")


def write_status(safe_profile: Path, workspace_profile: Path, status_data: dict):
    for pdir in (safe_profile, workspace_profile):
        try:
            with open(pdir / "status.json", "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="YouTube Studio Persistent Chrome Login (Option B)")
    parser.add_argument("--id", default="acc_7a6cba33", help="Account Persona ID (e.g. acc_01, acc_7a6cba33)")
    parser.add_argument("--timeout", type=int, default=300, help="Login timeout in seconds (default: 300)")
    args = parser.parse_args()

    account_id = args.id
    safe_profile, workspace_profile = get_profile_dirs(account_id)
    chrome_exe = find_chrome_exe()

    if not chrome_exe:
        print("[ERROR] Neither Google Chrome nor Edge was found on your system!")
        return

    print("=" * 70)
    print("  GOING MERRY™ // AUTONOMOUS FLEET COMMAND - YOUTUBE STUDIO CONNECTOR")
    print(f"  Account ID:   {account_id}")
    print(f"  Browser Exe:  {chrome_exe}")
    print(f"  Profile Dir:  {safe_profile}")
    print("=" * 70)

    # 1. Check if already logged in
    if check_youtube_cookies_in_db(safe_profile):
        print("\n[INFO] Active YouTube session detected on disk for this account!")
        print("Opening YouTube Studio so you can verify your channel...")
    else:
        print("\n[STEP 1] Launching clean official browser window on your screen...")
        print("[STEP 2] Sign in to your Google Account and select your YouTube channel.")
        print("[STEP 3] Once YouTube Studio loads, your session will be saved permanently!\n")

    # Launch Chrome as genuine system process (ZERO automation flags, ZERO bot detection)
    cmd = [
        chrome_exe,
        f"--user-data-dir={safe_profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        "https://studio.youtube.com"
    ]

    proc = subprocess.Popen(cmd)
    print(f"Browser launched (PID: {proc.pid}). Waiting for sign-in...")

    start_time = time.time()
    logged_in = False
    stop_event = threading.Event()

    def cookie_monitor():
        nonlocal logged_in
        while not stop_event.is_set() and (time.time() - start_time < args.timeout):
            if check_youtube_cookies_in_db(safe_profile):
                logged_in = True
                print("\n[SUCCESS] YouTube Studio session detected in cookies database!")
                stop_event.set()
                break
            time.sleep(2)

    monitor_thread = threading.Thread(target=cookie_monitor, daemon=True)
    monitor_thread.start()

    print("\n" + "-" * 70)
    print("  👉 Complete sign-in in the Google Chrome window.")
    print("  👉 Once you reach YouTube Studio (https://studio.youtube.com):")
    print("     Press [ENTER] in this window to confirm and save your session.")
    print("-" * 70 + "\n")

    try:
        # Wait for either auto-detection via monitor thread OR user pressing Enter
        def wait_enter():
            try:
                input("Press [ENTER] when you have signed into YouTube Studio: ")
                stop_event.set()
            except Exception:
                pass

        enter_thread = threading.Thread(target=wait_enter, daemon=True)
        enter_thread.start()

        while not stop_event.is_set() and (time.time() - start_time < args.timeout):
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")

    stop_event.set()

    # Final check on cookies
    time.sleep(1)
    if check_youtube_cookies_in_db(safe_profile):
        logged_in = True

    if logged_in:
        now_iso = datetime.now().isoformat()
        status_payload = {
            "status": "connected",
            "connected": True,
            "platform": "youtube",
            "account_id": account_id,
            "handle": f"@{account_id} (YouTube Studio)",
            "message": "YouTube Studio session active & verified!",
            "timestamp": now_iso
        }
        write_status(safe_profile, workspace_profile, status_payload)
        update_accounts_json(account_id)

        # Copy Network Cookies to workspace profile
        try:
            src_net = safe_profile / "Default" / "Network"
            dst_net = workspace_profile / "Default" / "Network"
            if src_net.exists():
                dst_net.mkdir(parents=True, exist_ok=True)
                for item in ["Cookies", "Cookies-journal"]:
                    if (src_net / item).exists():
                        shutil.copy2(src_net / item, dst_net / item)
        except Exception:
            pass

        print("\n" + "=" * 70)
        print("  [SUCCESS] YOUTUBE STUDIO CONNECTED SUCCESSFULLY!")
        print(f"  Account:     {account_id}")
        print(f"  Profile:     {safe_profile}")
        print(f"  Session:     Permanent (No API Quotas, Direct Studio Upload)")
        print("=" * 70)
        print("\nYou can now upload videos using:")
        print(f"  python -m clipper.uploader.uploader_manager")
        print("Or directly through the Web Dashboard / Video Pipeline!")
    else:
        print("\n[NOTICE] No authenticated YouTube session was detected before timeout or exit.")
        print("If you were in the middle of 2FA, run this command again anytime to finish.")


if __name__ == "__main__":
    main()
