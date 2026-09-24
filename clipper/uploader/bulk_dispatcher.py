"""
Bulk Multi-Account Social Media Dispatcher
===========================================
The production engine for 30+ accounts & bulk video clipping.
Integrates:
  - Instagram: instagrapi (Private Mobile API + Session persistence)
  - TikTok: tiktok-uploader (Playwright + Cookie persistence)
  - YouTube: Playwright YouTube Studio (Persistent Chrome profile)
  
Zero Docker, $0 Cost, Full Proxy Isolation.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import drivers
try:
    from instagrapi import Client as InstaClient
    INSTAGRAPI_AVAILABLE = True
except ImportError:
    INSTAGRAPI_AVAILABLE = False

try:
    from tiktok_uploader.upload import upload_video as tiktok_upload_video
    TIKTOK_UPLOADER_AVAILABLE = True
except ImportError:
    TIKTOK_UPLOADER_AVAILABLE = False

from clipper.uploader.profiles_manager import ProfileManager
from clipper.uploader.browser_engine import BrowserEngine
from clipper.uploader.drivers.youtube_studio import YouTubeStudioUploader

BASE_PROFILES_DIR = Path(__file__).resolve().parent.parent.parent / "uploader_profiles"


class BulkDispatcher:
    """
    Unified multi-account dispatcher for bulk video distribution.
    """

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.base_dir = Path(profiles_dir) if profiles_dir else BASE_PROFILES_DIR
        self.accounts_dir = self.base_dir / "accounts"
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile_mgr = ProfileManager(base_dir=self.base_dir)
        self.browser_engine = BrowserEngine(profile_manager=self.profile_mgr)

    def get_account_config(self, account_id: str) -> Dict[str, Any]:
        """Loads account config from accounts/acc_id.json or returns default."""
        cfg_file = self.accounts_dir / f"{account_id}.json"
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DISPATCHER] Error reading {cfg_file}: {e}")
        
        # Fallback to profile_mgr registry
        meta = self.profile_mgr.get_account(account_id) or {}
        return {
            "id": account_id,
            "name": meta.get("name", account_id),
            "proxy": meta.get("proxy", ""),
            "platforms": meta.get("platforms", ["youtube", "tiktok", "instagram"])
        }

    def save_account_config(self, account_id: str, config: Dict[str, Any]) -> None:
        """Saves account config to accounts/acc_id.json."""
        config["id"] = account_id
        config["updated_at"] = datetime.utcnow().isoformat()
        cfg_file = self.accounts_dir / f"{account_id}.json"
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    # -------------------------------------------------------------
    # 1. Instagram Reels Upload (instagrapi)
    # -------------------------------------------------------------
    def upload_instagram_reel(
        self,
        account_id: str,
        video_path: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Uploads a Reel to Instagram via instagrapi."""
        if not INSTAGRAPI_AVAILABLE:
            return {"status": "error", "message": "instagrapi is not installed."}

        cfg = self.get_account_config(account_id)
        ig_cfg = cfg.get("instagram", {})
        session_file = self.accounts_dir / f"{account_id}_ig_session.json"

        hashtags = hashtags or []
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        full_caption = f"{caption.strip()}\n\n{tag_str}".strip()

        print(f"[INSTAGRAM] Initializing instagrapi for [{account_id}]...")
        cl = InstaClient()

        # Set proxy if configured
        proxy = cfg.get("proxy") or ig_cfg.get("proxy")
        if proxy:
            print(f"[INSTAGRAM] Routing via proxy: {proxy}")
            cl.set_proxy(proxy)

        # 1. Load session or login
        if session_file.exists():
            try:
                print(f"[INSTAGRAM] Loading saved session: {session_file.name}")
                cl.load_settings(session_file)
            except Exception as e:
                print(f"[INSTAGRAM] Session load failed ({e}), re-logging in...")
                username = ig_cfg.get("username")
                password = ig_cfg.get("password")
                if username and password:
                    cl.login(username, password)
                    cl.dump_settings(session_file)
                else:
                    return {"status": "error", "message": f"Saved session invalid and no username/password in {account_id}.json"}
        else:
            username = ig_cfg.get("username")
            password = ig_cfg.get("password")
            if not username or not password:
                print(f"[INSTAGRAM] No direct API session file -> Falling back to persistent Chrome browser session...")
                with self.browser_engine.open_session(account_id=account_id, headless=True) as (context, page):
                    from clipper.uploader.drivers.instagram_web import InstagramWebUploader
                    ig_driver = InstagramWebUploader(page)
                    return ig_driver.upload_reel(video_path=video_path, caption=caption, hashtags=hashtags)

            print(f"[INSTAGRAM] Logging in user {username}...")
            cl.login(username, password)
            cl.dump_settings(session_file)


        # 2. Upload Reel
        print(f"[INSTAGRAM] Uploading Reel: {Path(video_path).name}...")
        try:
            media = cl.clip_upload(
                path=video_path,
                caption=full_caption
            )
            media_id = media.id if hasattr(media, "id") else str(media)
            media_code = media.code if hasattr(media, "code") else ""
            url = f"https://www.instagram.com/reel/{media_code}/" if media_code else ""
            print(f"[INSTAGRAM] ✅ Reel Published! Media ID: {media_id} | URL: {url}")
            return {"status": "success", "platform": "instagram", "media_id": media_id, "url": url}
        except Exception as e:
            print(f"[INSTAGRAM] ❌ Upload failed: {e}")
            return {"status": "error", "platform": "instagram", "message": str(e)}

    # -------------------------------------------------------------
    # 2. TikTok Video Upload (tiktok-uploader)
    # -------------------------------------------------------------
    def upload_tiktok_video(
        self,
        account_id: str,
        video_path: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Uploads a video to TikTok via tiktok-uploader."""
        if not TIKTOK_UPLOADER_AVAILABLE:
            return {"status": "error", "message": "tiktok-uploader is not installed."}

        cfg = self.get_account_config(account_id)
        tt_cfg = cfg.get("tiktok", {})
        cookies_txt = self.accounts_dir / f"{account_id}_tiktok_cookies.txt"
        cookies_json = self.accounts_dir / f"{account_id}_cookies.json"

        hashtags = hashtags or []
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        full_caption = f"{caption.strip()} {tag_str}".strip()[:2000]

        proxy = cfg.get("proxy") or tt_cfg.get("proxy")

        # 1. Check for cookies file
        cookies_arg = str(cookies_txt) if cookies_txt.exists() else None
        cookies_list_arg = []
        if not cookies_arg and cookies_json.exists():
            try:
                with open(cookies_json, "r", encoding="utf-8") as f:
                    cookies_list_arg = json.load(f)
            except Exception as e:
                print(f"[TIKTOK] Warning loading JSON cookies: {e}")

        # Fallback to browser session if neither cookie file is found
        if not cookies_arg and not cookies_list_arg:
            print(f"[TIKTOK] No cookie file found -> Uploading via persistent Chrome browser session...")
            with self.browser_engine.open_session(account_id=account_id, headless=True) as (context, page):
                from clipper.uploader.drivers.tiktok_web import TikTokWebUploader
                tt_driver = TikTokWebUploader(page)
                return tt_driver.upload_video(video_path=video_path, caption=caption, hashtags=hashtags)

        print(f"[TIKTOK] Uploading video for [{account_id}] via cookies...")
        try:
            kwargs = {
                "filename": video_path,
                "description": full_caption,
                "proxy": proxy,
                "headless": True
            }
            if cookies_arg:
                kwargs["cookies"] = cookies_arg
            elif cookies_list_arg:
                kwargs["cookies_list"] = cookies_list_arg

            res = tiktok_upload_video(**kwargs)
            print(f"[TIKTOK] ✅ TikTok upload result: {res}")
            return {"status": "success", "platform": "tiktok", "result": str(res)}
        except Exception as e:
            print(f"[TIKTOK] ❌ TikTok upload failed: {e}")
            return {"status": "error", "platform": "tiktok", "message": str(e)}


    # -------------------------------------------------------------
    # 3. YouTube Shorts Upload (Playwright Chrome Session)
    # -------------------------------------------------------------
    def upload_youtube_short(
        self,
        account_id: str,
        video_path: str,
        title: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None,
        privacy: str = "public"
    ) -> Dict[str, Any]:
        """Uploads a Short to YouTube Studio using persistent Chrome session."""
        print(f"[YOUTUBE] Uploading Short for [{account_id}]...")
        with self.browser_engine.open_session(account_id=account_id, headless=True) as (context, page):
            yt = YouTubeStudioUploader(page)
            return yt.upload_short(
                video_path=video_path,
                title=title,
                caption=caption,
                hashtags=hashtags,
                privacy=privacy
            )

    # -------------------------------------------------------------
    # Master Dispatch
    # -------------------------------------------------------------
    def dispatch(
        self,
        video_path: str,
        title: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        account_id: str = "acc_01",
        privacy: str = "public"
    ) -> Dict[str, Any]:
        """
        Dispatches a clip to the target platforms for the given account.
        """
        platforms = platforms or ["youtube", "instagram", "tiktok"]
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "video_path": video_path,
            "results": {}
        }

        print("\n" + "=" * 60)
        print(f"🚀 [BULK DISPATCH] Account: {account_id} | Video: {Path(video_path).name}")
        print(f"🎯 Target Platforms: {platforms}")
        print("=" * 60)

        # 1. YouTube Shorts
        if "youtube" in platforms or "shorts" in platforms:
            try:
                results["results"]["youtube"] = self.upload_youtube_short(
                    account_id=account_id,
                    video_path=video_path,
                    title=title,
                    caption=caption,
                    hashtags=hashtags,
                    privacy=privacy
                )
            except Exception as e:
                print(f"[YOUTUBE] ⚠️ Upload exception: {e}")
                results["results"]["youtube"] = {"success": False, "error": str(e)}

        # 2. Instagram
        if "instagram" in platforms or "reels" in platforms:
            try:
                results["results"]["instagram"] = self.upload_instagram_reel(
                    account_id=account_id,
                    video_path=video_path,
                    caption=caption,
                    hashtags=hashtags
                )
            except Exception as e:
                print(f"[INSTAGRAM] ⚠️ Upload exception: {e}")
                results["results"]["instagram"] = {"success": False, "error": str(e)}

        # 3. TikTok
        if "tiktok" in platforms:
            try:
                results["results"]["tiktok"] = self.upload_tiktok_video(
                    account_id=account_id,
                    video_path=video_path,
                    caption=caption,
                    hashtags=hashtags
                )
            except Exception as e:
                print(f"[TIKTOK] ⚠️ Upload notice (e.g. region network/proxy requirement): {e}")
                results["results"]["tiktok"] = {"success": False, "error": str(e)}

        print(f"✨ [BULK DISPATCH] Completed dispatch for {account_id}.\n")
        return results
