"""
Local Multi-Account Uploader Manager
====================================
Drop-in replacement for PostizManager.
Manages automated browser-based dispatch across 30+ accounts for
YouTube Shorts, TikTok, and Instagram Reels.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from clipper.uploader.profiles_manager import ProfileManager
from clipper.uploader.browser_engine import BrowserEngine
from clipper.uploader.drivers.youtube_studio import YouTubeStudioUploader
from clipper.uploader.drivers.tiktok_web import TikTokWebUploader
from clipper.uploader.drivers.instagram_web import InstagramWebUploader


class LocalUploaderManager:
    """
    Self-hosted, browser-backed social uploader manager.
    Zero Docker, Zero Cloud APIs, $0 cost. Supports 30+ accounts.
    """

    PLATFORM_MAPPING = {
        "shorts": "youtube",
        "youtube": "youtube",
        "tiktok": "tiktok",
        "reels": "instagram",
        "instagram": "instagram",
        "all": "all"
    }

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profile_mgr = ProfileManager(base_dir=profiles_dir)
        self.browser_engine = BrowserEngine(profile_manager=self.profile_mgr)

    def check_health(self) -> Dict[str, Any]:
        """Returns health status compatible with web dashboard."""
        accounts = self.profile_mgr.list_accounts()
        ready_count = sum(1 for a in accounts if a["has_session"])
        return {
            "online": True,
            "status_code": 200,
            "engine": "Playwright Real-Chrome",
            "accounts_count": len(accounts),
            "ready_sessions": ready_count,
            "message": f"Local Uploader Active: {len(accounts)} accounts configured ({ready_count} logged in)."
        }

    def get_integrations(self) -> List[Dict[str, Any]]:
        """Returns registered accounts in a format compatible with dashboard."""
        accounts = self.profile_mgr.list_accounts()
        integrations = []
        for acc in accounts:
            for platform in acc.get("platforms", ["youtube", "tiktok", "instagram"]):
                integrations.append({
                    "id": f"{acc['id']}_{platform}",
                    "account_id": acc["id"],
                    "identifier": platform,
                    "name": f"{acc['name']} ({platform.capitalize()})",
                    "status": "ready" if acc["has_session"] else "needs_login"
                })
        return integrations

    def publish_clip(
        self,
        video_path: str,
        title: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None,
        target_platform: str = "all",
        account_id: str = "default",
        schedule_time: Optional[str] = None,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Dispatches a video upload to the requested platforms for an account.
        
        Args:
            video_path: Absolute path to rendered .mp4
            title: Video title
            caption: Caption or hook text
            hashtags: List of hashtags
            target_platform: 'all', 'youtube', 'tiktok', or 'instagram'
            account_id: Target account ID (e.g. 'acc_01', 'speed_clips')
            schedule_time: Optional ISO timestamp
            headless: Whether to run Chrome in background (True) or visible (False)
        """
        target = self.PLATFORM_MAPPING.get(target_platform.lower(), target_platform.lower())
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "video_path": video_path,
            "account_id": account_id,
            "platforms": {}
        }

        # Normalize target platforms
        platforms_to_run = []
        if target == "all":
            platforms_to_run = ["youtube", "tiktok", "instagram"]
        else:
            platforms_to_run = [target]

        print(f"\n[LOCAL_UPLOADER] 🚀 Dispatching clip to [{account_id}] across: {platforms_to_run}")

        # Execute upload session
        with self.browser_engine.open_session(account_id=account_id, headless=headless) as (context, page):
            # 1. YouTube Upload
            if "youtube" in platforms_to_run:
                try:
                    yt = YouTubeStudioUploader(page)
                    yt_result = yt.upload_short(
                        video_path=video_path,
                        title=title,
                        caption=caption,
                        hashtags=hashtags,
                        privacy="public"
                    )
                    results["platforms"]["youtube"] = yt_result
                except Exception as e:
                    print(f"[LOCAL_UPLOADER] ❌ YouTube upload failed: {e}")
                    results["platforms"]["youtube"] = {"status": "error", "message": str(e)}

            # 2. TikTok Upload
            if "tiktok" in platforms_to_run:
                try:
                    tt = TikTokWebUploader(page)
                    tt_result = tt.upload_video(
                        video_path=video_path,
                        caption=caption,
                        hashtags=hashtags
                    )
                    results["platforms"]["tiktok"] = tt_result
                except Exception as e:
                    print(f"[LOCAL_UPLOADER] ❌ TikTok upload failed: {e}")
                    results["platforms"]["tiktok"] = {"status": "error", "message": str(e)}

            # 3. Instagram Reels Upload
            if "instagram" in platforms_to_run:
                try:
                    ig = InstagramWebUploader(page)
                    ig_result = ig.upload_reel(
                        video_path=video_path,
                        caption=caption,
                        hashtags=hashtags
                    )
                    results["platforms"]["instagram"] = ig_result
                except Exception as e:
                    print(f"[LOCAL_UPLOADER] ❌ Instagram upload failed: {e}")
                    results["platforms"]["instagram"] = {"status": "error", "message": str(e)}

        self.profile_mgr.update_last_upload(account_id)
        print(f"[LOCAL_UPLOADER] ✨ Finished upload run for [{account_id}].")
        return results
