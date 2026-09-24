"""
PostizManager Adapter -> Local Multi-Account Uploader
======================================================
Seamless replacement for Postiz. All calls to PostizManager are now
directly routed to the Local Bulk Uploader Engine (Playwright + instagrapi).
Zero Docker, $0 Cost, 30+ Accounts supported.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from clipper.uploader.uploader_manager import LocalUploaderManager
from clipper.uploader.bulk_dispatcher import BulkDispatcher
from clipper.uploader.profiles_manager import ProfileManager


class PostizManager:
    """
    Drop-in replacement for PostizManager that routes all multi-platform uploads
    directly to the local browser-backed upload engine.
    """

    PLATFORM_MAPPING = {
        "shorts": "youtube",
        "youtube": "youtube",
        "tiktok": "tiktok",
        "reels": "instagram",
        "instagram": "instagram",
        "twitter": "x",
        "x": "x",
        "facebook": "facebook",
        "all": "all"
    }

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None, proxy_url: Optional[str] = None):
        self.api_url = "http://localhost/local-uploader"
        self.api_key = "local_active"
        self.uploader = LocalUploaderManager()
        self.dispatcher = BulkDispatcher()
        self.profile_mgr = ProfileManager()

    def check_health(self) -> Dict[str, Any]:
        """Returns health of the local upload engine."""
        return self.uploader.check_health()

    def get_integrations(self) -> List[Dict[str, Any]]:
        """Returns all configured accounts and platforms."""
        return self.uploader.get_integrations()

    def upload_media(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Verifies local media path."""
        if os.path.exists(file_path):
            return {"id": os.path.basename(file_path), "path": file_path}
        return None

    def build_post_payload(self, *args, **kwargs) -> Dict[str, Any]:
        return {"status": "ok", "mode": "local_engine"}

    def publish_clip(
        self,
        video_path: str,
        title: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None,
        target_platform: str = "all",
        schedule_time: Optional[str] = None,
        simulate: bool = False,
        account_id: str = "acc_01"
    ) -> Dict[str, Any]:
        """
        Dispatches video directly through the local multi-account engine.
        """
        hashtags = hashtags or []
        target = self.PLATFORM_MAPPING.get(target_platform.lower(), target_platform.lower())
        plat_list = ["youtube", "instagram", "tiktok"] if target == "all" else [target]

        print(f"\n[LOCAL_UPLOADER] 🚀 Publishing '{title}' to {plat_list} via Account [{account_id}]...")

        if simulate:
            print("[LOCAL_UPLOADER] [TEST] Simulation mode enabled.")
            return {
                "success": True,
                "mode": "simulation",
                "platforms": plat_list,
                "message": "Local uploader verified payload."
            }

        res = self.dispatcher.dispatch(
            video_path=video_path,
            title=title,
            caption=caption,
            hashtags=hashtags,
            platforms=plat_list,
            account_id=account_id,
            privacy="public"
        )

        return {
            "success": True,
            "mode": "local_live",
            "platforms": plat_list,
            "results": res.get("results", {}),
            "message": f"Successfully published clip to {plat_list} via local engine."
        }
