"""
Multi-Account Uploader CLI
==========================
Simple command-line interface to manage 30+ accounts,
run 1-time browser logins, and test uploads.
"""

import sys
import argparse
from pathlib import Path

# Safe UTF-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from clipper.uploader.profiles_manager import ProfileManager
from clipper.uploader.browser_engine import BrowserEngine
from clipper.uploader.bulk_dispatcher import BulkDispatcher



def main():
    parser = argparse.ArgumentParser(description="Multi-Account Social Media Uploader CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list
    list_p = subparsers.add_parser("list", help="List registered accounts")
    list_p.add_argument("--fleet", choices=["whop", "normal"], default=None, help="Filter by fleet: whop or normal")

    # Command: add
    add_p = subparsers.add_parser("add", help="Register a new account")
    add_p.add_argument("--id", required=True, help="Unique account ID (e.g. acc_01, speed_clips)")
    add_p.add_argument("--name", default="", help="Human readable name")
    add_p.add_argument("--fleet", default="normal", choices=["whop", "normal"], help="Fleet: whop (bounty) or normal (organic)")
    add_p.add_argument("--pod", default="", help="Pod/Cluster (e.g. Pod_A, Pod_B)")
    add_p.add_argument("--campaign", default="", help="Assigned Whop campaign name")
    add_p.add_argument("--niche", default="", help="Niche (e.g. trading, saas, lifestyle, podcast)")
    add_p.add_argument("--proxy", default="", help="Optional SOCKS5/HTTP proxy (e.g. socks5://127.0.0.1:1080)")
    add_p.add_argument("--notes", default="", help="Optional notes")

    # Command: assign
    assign_p = subparsers.add_parser("assign", help="Reassign account to a fleet or campaign")
    assign_p.add_argument("--id", required=True, help="Account ID")
    assign_p.add_argument("--fleet", required=True, choices=["whop", "normal"], help="Target fleet")
    assign_p.add_argument("--pod", default=None, help="Optional pod name")
    assign_p.add_argument("--campaign", default=None, help="Optional campaign name")
    assign_p.add_argument("--niche", default=None, help="Optional niche")

    # Command: login
    login_p = subparsers.add_parser("login", help="Open browser to log into an account once")
    login_p.add_argument("--id", required=True, help="Account ID")
    login_p.add_argument("--platform", default="youtube", choices=["youtube", "tiktok", "instagram", "facebook", "twitter"], help="Platform to log in to")

    # Command: upload
    upload_p = subparsers.add_parser("upload", help="Upload a video to one or all platforms")
    upload_p.add_argument("--id", required=True, help="Account ID")
    upload_p.add_argument("--video", required=True, help="Path to video file")
    upload_p.add_argument("--title", default="Viral Clip #shorts", help="Video title")
    upload_p.add_argument("--caption", default="", help="Caption")
    upload_p.add_argument("--tags", default="shorts,viral", help="Comma-separated tags")
    upload_p.add_argument("--platforms", default="youtube", help="Comma-separated platforms: youtube,tiktok,instagram")
    upload_p.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="YouTube visibility")

    args = parser.parse_args()
    pm = ProfileManager()
    engine = BrowserEngine(profile_manager=pm)
    dispatcher = BulkDispatcher()

    if args.command == "list":
        accounts = pm.list_accounts(fleet=args.fleet)
        fleet_title = f" [{args.fleet.upper()} FLEET]" if args.fleet else ""
        print("\n" + "=" * 75)
        print(f"📋 REGISTERED ACCOUNTS ({len(accounts)} Total){fleet_title}")
        print("=" * 75)
        if not accounts:
            print("No accounts found. Run: python -m clipper.uploader.cli add --id acc_01 --fleet whop")
        for acc in accounts:
            session_status = "🟢 Ready" if acc["has_session"] else "🟡 Needs Login"
            fleet_str = f"[{acc['fleet'].upper()}]"
            pod_str = f" ({acc['pod']})" if acc['pod'] else ""
            camp_str = f" -> Campaign: {acc['assigned_campaign']}" if acc['assigned_campaign'] else ""
            proxy_str = f" | Proxy: {acc['proxy']}" if acc['proxy'] else ""
            print(f"{fleet_str:<8} [{acc['id']}] {acc['name']}{pod_str} -> {session_status}{camp_str}{proxy_str}")
        print("=" * 75 + "\n")

    elif args.command == "add":
        pm.add_account(
            account_id=args.id,
            name=args.name or args.id,
            fleet=args.fleet,
            pod=args.pod,
            assigned_campaign=args.campaign,
            niche=args.niche,
            proxy=args.proxy,
            notes=args.notes
        )
        print(f"✅ Account '{args.id}' added to {args.fleet.upper()} fleet! Now run login:")
        print(f"   python -m clipper.uploader.cli login --id {args.id} --platform youtube")

    elif args.command == "assign":
        ok = pm.update_account_fleet(
            account_id=args.id,
            fleet=args.fleet,
            pod=args.pod,
            assigned_campaign=args.campaign,
            niche=args.niche
        )
        if ok:
            print(f"✅ Successfully reassigned account '{args.id}' to {args.fleet.upper()} fleet!")
        else:
            print(f"❌ Account '{args.id}' not found in registry.")

    elif args.command == "login":
        engine.interactive_login(account_id=args.id, platform=args.platform)

    elif args.command == "upload":
        tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        plat_list = [p.strip() for p in args.platforms.split(",") if p.strip()]
        res = dispatcher.dispatch(
            video_path=args.video,
            title=args.title,
            caption=args.caption,
            hashtags=tags_list,
            platforms=plat_list,
            account_id=args.id,
            privacy=args.privacy
        )
        print("Upload Result:", res)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
