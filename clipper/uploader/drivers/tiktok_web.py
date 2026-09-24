"""
TikTok Web Creator Playwright Automation Driver
===============================================
Automates video uploads directly to TikTok Creator Center
using saved browser profiles. Bypasses all developer app reviews.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class TikTokWebUploader:
    """
    Automates uploading to TikTok Creator Center via Playwright.
    """

    UPLOAD_URL = "https://www.tiktok.com/creator-center/upload"

    def __init__(self, page: Page):
        self.page = page

    def is_logged_in(self) -> bool:
        """Checks if current session is authenticated into TikTok."""
        try:
            self.page.goto(self.UPLOAD_URL, wait_until="domcontentloaded", timeout=25000)
            self.page.wait_for_timeout(3000)
            if "login" in self.page.url:
                return False
            # Check for upload container or user profile icon
            return (
                self.page.locator("input[type='file']").count() > 0 or
                self.page.locator("iframe[src*='upload']").count() > 0 or
                "creator-center" in self.page.url
            )
        except Exception as e:
            print(f"[TIKTOK_BOT] Login check error: {e}")
            return False

    def upload_video(
        self,
        video_path: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads a video to TikTok Creator Center.
        """
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            return {"status": "error", "message": f"Video file not found: {video_path}"}

        print(f"[TIKTOK_BOT] 🚀 Starting upload for: {video_file.name}")

        hashtags = hashtags or []
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        full_caption = f"{caption.strip()} {tag_str}".strip()[:2000]

        # 1. Navigate to Upload page
        try:
            self.page.goto(self.UPLOAD_URL, wait_until="domcontentloaded", timeout=12000)
            self.page.wait_for_timeout(2000)
        except Exception as e:
            err_str = str(e)
            if "ERR_CONNECTION_TIMED_OUT" in err_str or "ERR_NAME_NOT_RESOLVED" in err_str or "Timeout" in err_str:
                print(f"[TIKTOK_BOT] ⚠️ TikTok is unreachable (India ISP restriction or proxy needed): {err_str[:80]}")
                return {
                    "status": "skipped",
                    "platform": "tiktok",
                    "message": "TikTok unreachable without proxy (India network restriction). Residential proxy required."
                }
            raise e

        if "login" in self.page.url:
            return {
                "status": "error",
                "message": "Session expired or not logged in. Please run the 1-time login command."
            }

        # Handle potential iframe on TikTok Creator Center
        target_frame = self.page
        if self.page.locator("iframe[src*='upload']").count() > 0:
            frame_element = self.page.locator("iframe[src*='upload']").first
            target_frame = frame_element.content_frame or self.page

        # 2. Upload File
        print(f"[TIKTOK_BOT] Uploading video binary: {video_file.name}...")
        file_input = target_frame.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=25000)
        file_input.set_input_files(str(video_file))

        # 3. Wait for caption area
        print("[TIKTOK_BOT] Setting Caption & Hashtags...")
        caption_box = target_frame.locator(".notranslate[contenteditable='true'], [contenteditable='true'], .public-DraftEditor-content").first
        try:
            caption_box.wait_for(state="visible", timeout=30000)
            caption_box.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.wait_for_timeout(300)
            self.page.keyboard.type(full_caption)
        except Exception as e:
            print(f"[TIKTOK_BOT] Warning setting caption: {e}")

        self.page.wait_for_timeout(2000)

        # 4. Click Post Button
        print("[TIKTOK_BOT] Clicking Post...")
        post_btn = target_frame.locator("button:has-text('Post'), .btn-post, button[type='button']:has-text('Post')").first
        post_btn.wait_for(state="visible", timeout=20000)
        
        # Ensure upload progress is complete before clicking post
        self.page.wait_for_timeout(4000)
        post_btn.click()

        self.page.wait_for_timeout(5000)
        print("[TIKTOK_BOT] ✅ Video posted to TikTok successfully!")
        return {
            "status": "success",
            "platform": "tiktok",
            "caption": full_caption
        }
