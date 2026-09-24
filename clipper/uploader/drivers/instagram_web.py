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

        shots_dir = Path("/app/output")
        shots_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.page.screenshot(path=str(shots_dir / "ig_step1_nav.png"))
        except Exception:
            pass

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
            try: self.page.screenshot(path=str(shots_dir / "ig_err_no_create.png"))
            except Exception: pass
            return {"status": "error", "message": "Could not find 'Create' button on Instagram."}

        self.page.wait_for_timeout(1500)
        try: self.page.screenshot(path=str(shots_dir / "ig_step2_create_dialog.png"))
        except Exception: pass

        # 3. Upload File
        print(f"[INSTAGRAM_BOT] Uploading video: {video_file.name}...")
        file_input = self.page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=15000)
        file_input.set_input_files(str(video_file))

        self.page.wait_for_timeout(4000)
        try: self.page.screenshot(path=str(shots_dir / "ig_step3_file_attached.png"))
        except Exception: pass

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

        try: self.page.screenshot(path=str(shots_dir / "ig_step4_crop.png"))
        except Exception: pass

        # 5. Click 'Next' (Filter/Cover screen)
        try:
            next_btn2 = self.page.locator("div[role='button']:has-text('Next'), button:has-text('Next')").first
            next_btn2.wait_for(state="visible", timeout=10000)
            next_btn2.click()
            self.page.wait_for_timeout(2500)
        except Exception as e:
            print(f"[INSTAGRAM_BOT] Next 2 notice: {e}")

        try: self.page.screenshot(path=str(shots_dir / "ig_step5_cover.png"))
        except Exception: pass

        # 6. Add Caption
        print("[INSTAGRAM_BOT] Setting Caption...")
        try:
            caption_area = self.page.locator("div[aria-label*='caption'], div[role='textbox'], div[contenteditable='true']").first
            caption_area.wait_for(state="visible", timeout=10000)
            caption_area.click()
            self.page.wait_for_timeout(500)
            try:
                caption_area.fill(full_caption)
            except Exception:
                pass
            # Also insert via keyboard to ensure contenteditable receives text
            self.page.keyboard.insert_text(full_caption)
            self.page.wait_for_timeout(1000)
        except Exception as cap_err:
            print(f"[INSTAGRAM_BOT] Caption set notice: {cap_err}")

        try: self.page.screenshot(path=str(shots_dir / "ig_step6_caption_set.png"))
        except Exception: pass

        # 7. Click 'Share'
        print("[INSTAGRAM_BOT] Clicking Share...")
        share_btn = self.page.locator("div[role='button']:has-text('Share'), button:has-text('Share')").last
        share_btn.wait_for(state="visible", timeout=15000)
        try:
            share_btn.click(force=True, timeout=8000)
        except Exception:
            self.page.evaluate("(btn) => btn.click()", share_btn.element_handle())

        # Wait for 'Reel shared' confirmation (poll up to 120 seconds)
        print("[INSTAGRAM_BOT] Video uploading to Meta servers... Waiting for confirmation (up to 120s)...")
        shared_confirmed = False
        start_wait = time.time()
        while time.time() - start_wait < 120:
            self.page.wait_for_timeout(3000)
            elapsed = int(time.time() - start_wait)
            try:
                # 1. Check for specific success text or checkmark
                success_locators = self.page.locator(
                    "span:has-text('Your reel has been shared'), "
                    "span:has-text('Your post has been shared'), "
                    "div:has-text('Your reel has been shared'), "
                    "div:has-text('Your post has been shared'), "
                    "img[alt*='Animated checkmark'], "
                    "img[alt*='checkmark']"
                )
                if success_locators.count() > 0:
                    shared_confirmed = True
                    print(f"[INSTAGRAM_BOT] ✅ Detected confirmation: 'Your reel has been shared' after {elapsed}s!")
                    break

                # 2. Check if 'has been shared' appears in dialog text
                dialog = self.page.locator("div[role='dialog']").first
                if dialog.is_visible():
                    d_text = dialog.inner_text().lower()
                    if "has been shared" in d_text or "reel shared" in d_text:
                        shared_confirmed = True
                        print(f"[INSTAGRAM_BOT] ✅ Detected confirmation in dialog text after {elapsed}s!")
                        break

                if elapsed % 15 < 4:
                    print(f"[INSTAGRAM_BOT] Still uploading/processing... ({elapsed}s elapsed)")
            except Exception:
                pass

        try: self.page.screenshot(path=str(shots_dir / "ig_step7_after_share.png"))
        except Exception: pass

        if shared_confirmed:
            self.page.wait_for_timeout(3000)
            print("[INSTAGRAM_BOT] ✅ Reel shared successfully on Instagram!")
            return {
                "status": "success",
                "platform": "instagram",
                "caption": full_caption
            }
        else:
            print("[INSTAGRAM_BOT] ⚠️ Share button clicked, but confirmation checkmark was not verified within 120s.")
            return {
                "status": "unverified",
                "platform": "instagram",
                "message": "Share was clicked; confirmation dialog timed out. Check ig_step7_after_share.png for state."
            }

