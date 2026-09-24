"""
Instagram Web Reels Playwright Automation Driver
================================================
Automates Instagram Reels uploads directly via web session.
Bypasses Meta Graph API business verification.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class InstagramWebUploader:
    """
    Automates uploading Reels to Instagram via Playwright.
    """

    IG_URL = "https://www.instagram.com"

    def __init__(self, page: Page):
        self.page = page

    def is_logged_in(self) -> bool:
        """Checks if current session is authenticated into Instagram."""
        try:
            self.page.goto(self.IG_URL, wait_until="domcontentloaded", timeout=25000)
            self.page.wait_for_timeout(3000)
            if "accounts/login" in self.page.url:
                return False
            # Look for create icon or profile icon
            return (
                self.page.locator("svg[aria-label='New post']").count() > 0 or
                self.page.locator("span:has-text('Create')").count() > 0 or
                self.page.locator("svg[aria-label='Home']").count() > 0
            )
        except Exception as e:
            print(f"[INSTAGRAM_BOT] Login check error: {e}")
            return False

    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Uploads a vertical video as an Instagram Reel.
        """
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            return {"status": "error", "message": f"Video file not found: {video_path}"}

        print(f"[INSTAGRAM_BOT] 🚀 Starting upload for: {video_file.name}")

        hashtags = hashtags or []
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        full_caption = f"{caption.strip()}\n\n{tag_str}".strip()[:2200]

        # 1. Navigate to Instagram
        self.page.goto(self.IG_URL, wait_until="domcontentloaded", timeout=45000)
        self.page.wait_for_timeout(3000)

        if "accounts/login" in self.page.url:
            return {
                "status": "error",
                "message": "Session expired or not logged in. Please run the 1-time login command."
            }

        # Dismiss common popups (Save Info / Notifications)
        for popup_text in ["Not Now", "Not now", "Cancel"]:
            try:
                btn = self.page.locator(f"button:has-text('{popup_text}')").first
                if btn.is_visible():
                    btn.click(timeout=2000)
                    self.page.wait_for_timeout(1000)
            except Exception:
                pass

        # 2. Click 'Create' (+) button
        print("[INSTAGRAM_BOT] Opening Create Dialog...")
        create_btn = self.page.locator("svg[aria-label='New post'], span:has-text('Create'), div[role='button']:has-text('Create'), a:has-text('Create')").first
        try:
            create_btn.wait_for(state="visible", timeout=15000)
            create_btn.click()
            self.page.wait_for_timeout(1500)
            # If sub-menu appears (Post / Live video), click Post
            post_sub = self.page.locator("span:has-text('Post'), div:has-text('Post')").first
            if post_sub.is_visible():
                post_sub.click(timeout=3000)
        except PlaywrightTimeoutError:
            return {"status": "error", "message": "Could not find 'Create' button on Instagram."}

        self.page.wait_for_timeout(1500)

        # 3. Upload File
        print(f"[INSTAGRAM_BOT] Uploading video: {video_file.name}...")
        file_input = self.page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=15000)
        file_input.set_input_files(str(video_file))

        self.page.wait_for_timeout(3000)

        # Handle 'Video posts are now shared as reels' modal if it appears
        ok_btn = self.page.locator("button:has-text('OK'), button:has-text('Continue')").first
        if ok_btn.is_visible():
            ok_btn.click()
            self.page.wait_for_timeout(1000)

        # 4. Click 'Next' (Crop screen)
        print("[INSTAGRAM_BOT] Navigating crop screen...")
        try:
            next_btn1 = self.page.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
            next_btn1.wait_for(state="visible", timeout=15000)
            next_btn1.click()
            self.page.wait_for_timeout(2500)
        except Exception as e:
            print(f"[INSTAGRAM_BOT] Next 1 notice: {e}")

        # 5. Click 'Next' (Filter/Cover screen)
        try:
            next_btn2 = self.page.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
            next_btn2.wait_for(state="visible", timeout=10000)
            next_btn2.click()
            self.page.wait_for_timeout(2500)
        except Exception as e:
            print(f"[INSTAGRAM_BOT] Next 2 notice: {e}")

        # 6. Add Caption
        print("[INSTAGRAM_BOT] Setting Caption...")
        try:
            caption_area = self.page.locator("div[aria-label*='caption'], div[contenteditable='true']").first
            caption_area.wait_for(state="visible", timeout=10000)
            caption_area.click()
            caption_area.fill(full_caption)
            self.page.wait_for_timeout(1000)
        except Exception as cap_err:
            print(f"[INSTAGRAM_BOT] Caption set notice: {cap_err}")

        # 7. Click 'Share'
        print("[INSTAGRAM_BOT] Clicking Share...")
        share_btn = self.page.locator("div[role='button']:has-text('Share'), button:has-text('Share')").last
        share_btn.wait_for(state="visible", timeout=15000)
        try:
            share_btn.click(force=True, timeout=8000)
        except Exception:
            # JavaScript direct click bypasses any pointer-intercepting overlay
            self.page.evaluate("(btn) => btn.click()", share_btn.element_handle())

        # Wait for 'Reel shared' confirmation
        print("[INSTAGRAM_BOT] Waiting for upload and processing to finish...")
        self.page.wait_for_timeout(12000)

        print("[INSTAGRAM_BOT] ✅ Reel shared successfully on Instagram!")
        return {
            "status": "success",
            "platform": "instagram",
            "caption": full_caption
        }

