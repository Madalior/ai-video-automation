"""
YouTube Studio Playwright Automation Driver
===========================================
Automates video and Short uploads directly to YouTube Creator Studio
using saved browser profiles. Bypasses all Google Cloud API quotas.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class YouTubeStudioUploader:
    """
    Automates uploading to YouTube Creator Studio via Playwright.
    """

    STUDIO_URL = "https://studio.youtube.com"

    def __init__(self, page: Page):
        self.page = page

    def is_logged_in(self) -> bool:
        """Checks if the current session is authenticated into YouTube Studio."""
        try:
            self.page.goto(self.STUDIO_URL, wait_until="domcontentloaded", timeout=25000)
            self.page.wait_for_timeout(3000)
            current_url = self.page.url
            if "accounts.google.com" in current_url or "signin" in current_url:
                return False
            # Check for YouTube Studio avatar or create button
            return (
                self.page.locator("#create-icon").count() > 0 or
                self.page.locator("ytcp-button#create-icon").count() > 0 or
                "studio.youtube.com" in current_url
            )
        except Exception as e:
            print(f"[YOUTUBE_BOT] Login check error: {e}")
            return False

    def upload_short(
        self,
        video_path: str,
        title: str,
        caption: str = "",
        hashtags: Optional[List[str]] = None,
        privacy: str = "public",
        wait_for_processing: bool = False
    ) -> Dict[str, Any]:
        """
        Uploads a video to YouTube Studio.
        
        Args:
            video_path: Absolute path to the .mp4 file
            title: Video title (max 100 chars)
            caption: Description text
            hashtags: List of hashtags (e.g. ['#shorts', '#gaming'])
            privacy: 'public', 'unlisted', or 'private'
            wait_for_processing: Whether to block until YouTube finishes HD processing
            
        Returns:
            Dict containing status, video URL, and metadata.
        """
        video_file = Path(video_path).resolve()
        if not video_file.exists():
            return {"status": "error", "message": f"Video file not found: {video_path}"}

        print(f"[YOUTUBE_BOT] 🚀 Starting upload for: {video_file.name}")
        print(f"[YOUTUBE_BOT] Title: {title}")

        # 1. Format Title & Description
        hashtags = hashtags or []
        tag_str = " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)
        
        # Ensure #shorts is in title or description for YouTube Shorts algorithm
        final_title = title.strip()
        if "#shorts" not in final_title.lower() and "#short" not in final_title.lower():
            if len(final_title) <= 92:
                final_title = f"{final_title} #shorts"
        final_title = final_title[:100]

        full_description = f"{caption.strip()}\n\n{tag_str}".strip()

        # 2. Navigate to Studio
        self.page.goto(self.STUDIO_URL, wait_until="domcontentloaded", timeout=45000)
        self.page.wait_for_timeout(3000)

        if "accounts.google.com" in self.page.url:
            return {
                "status": "error",
                "message": "Session expired or not logged in. Please run the 1-time login command."
            }

        # 3. Click CREATE button
        print("[YOUTUBE_BOT] Opening Upload Dialog...")
        create_btn = self.page.locator("#create-icon, ytcp-button#create-icon, button#create-icon, [aria-label*='Create']").first
        try:
            create_btn.wait_for(state="visible", timeout=15000)
            create_btn.click()
        except PlaywrightTimeoutError:
            # Fallback: direct click on upload button if visible
            upload_direct = self.page.locator("#upload-button, [aria-label*='Upload videos']").first
            if upload_direct.is_visible():
                upload_direct.click()
            else:
                return {"status": "error", "message": "Could not find Create button in YouTube Studio."}

        self.page.wait_for_timeout(1000)

        # 4. Click 'Upload videos' in popup menu
        upload_menu_item = self.page.locator("tp-yt-paper-item, paper-item").filter(has_text="Upload videos").first
        if upload_menu_item.is_visible():
            upload_menu_item.click()

        self.page.wait_for_timeout(1500)

        # 5. Set Input Files (drag & drop upload)
        print(f"[YOUTUBE_BOT] Uploading video binary: {video_file.name} ({video_file.stat().st_size / (1024*1024):.1f} MB)...")
        file_input = self.page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=20000)
        file_input.set_input_files(str(video_file))

        # Wait for dialog details screen to appear
        print("[YOUTUBE_BOT] Waiting for Details dialog...")
        title_box = self.page.locator("#textbox[aria-label*='title'], ytcp-mention-textbox#title-textarea #textbox, #title-textarea #textbox").first
        title_box.wait_for(state="visible", timeout=35000)
        self.page.wait_for_timeout(2000)

        # 6. Fill Title
        print("[YOUTUBE_BOT] Setting Title...")
        title_box.click()
        # Clear existing text
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        self.page.wait_for_timeout(300)
        title_box.fill(final_title)
        self.page.wait_for_timeout(1000)

        # 7. Fill Description
        if full_description:
            print("[YOUTUBE_BOT] Setting Description...")
            desc_box = self.page.locator("#textbox[aria-label*='description'], ytcp-mention-textbox#description-textarea #textbox, #description-textarea #textbox").first
            if desc_box.is_visible():
                desc_box.click()
                desc_box.fill(full_description[:4900])
                self.page.wait_for_timeout(1000)

        # 8. Set 'Not made for kids'
        print("[YOUTUBE_BOT] Selecting 'Not made for kids'...")
        not_for_kids = self.page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if not_for_kids.is_visible():
            not_for_kids.click()
            self.page.wait_for_timeout(800)

        # 9. Grab the Video URL while in details screen
        video_url = ""
        url_elem = self.page.locator("a.ytcp-video-info, .video-url-fadeable a, [href*='youtu.be']").first
        if url_elem.is_visible():
            video_url = url_elem.get_attribute("href") or url_elem.inner_text().strip()
            print(f"[YOUTUBE_BOT] 🔗 Video Link Captured: {video_url}")

        # 10. Click 'Next' 3 times to get to Visibility screen
        next_button = self.page.locator("#next-button").first
        for step in range(1, 4):
            print(f"[YOUTUBE_BOT] Clicking Next (Step {step}/3)...")
            self.page.wait_for_timeout(1000)
            if next_button.is_visible():
                next_button.click()

        self.page.wait_for_timeout(2000)

        # 11. Select Visibility
        print(f"[YOUTUBE_BOT] Setting visibility to: {privacy.upper()}...")
        priv_upper = privacy.strip().upper()
        if priv_upper == "UNLISTED":
            vis_radio = self.page.locator("tp-yt-paper-radio-button[name='UNLISTED'], [name='UNLISTED']").first
        elif priv_upper == "PRIVATE":
            vis_radio = self.page.locator("tp-yt-paper-radio-button[name='PRIVATE'], [name='PRIVATE']").first
        else:
            vis_radio = self.page.locator("tp-yt-paper-radio-button[name='PUBLIC'], [name='PUBLIC']").first

        if vis_radio.is_visible():
            vis_radio.click()
            self.page.wait_for_timeout(1000)

        # 12. Click Save / Publish
        print("[YOUTUBE_BOT] Clicking Publish / Save...")
        done_button = self.page.locator("#done-button").first
        done_button.wait_for(state="visible", timeout=15000)
        done_button.click()

        # Wait for confirmation modal or dialog close
        self.page.wait_for_timeout(5000)
        close_btn = self.page.locator("#close-button, ytcp-button#close-button").first
        if close_btn.is_visible():
            close_btn.click()

        print(f"[YOUTUBE_BOT] ✅ SUCCESS! Short published successfully: {video_url or 'Published'}")
        return {
            "status": "success",
            "platform": "youtube",
            "url": video_url,
            "title": final_title,
            "privacy": privacy
        }
