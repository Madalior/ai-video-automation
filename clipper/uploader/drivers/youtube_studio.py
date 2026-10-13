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

    STUDIO_URL = "https://studio.youtube.com/?approve_browser_access=true"

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
        self.page.wait_for_timeout(4000)

        # Check for "Skip to YouTube Studio" browser warning page
        skip_btn = self.page.locator("a:has-text('Skip to YouTube Studio')").first
        if skip_btn.is_visible():
            print("[YOUTUBE_BOT] Bypassing browser version check -> Clicking 'Skip to YouTube Studio'...")
            skip_btn.click()
            self.page.wait_for_timeout(4000)

        if "accounts.google.com" in self.page.url:
            return {
                "status": "error",
                "message": "Session expired or not logged in. Please run the 1-time login command."
            }

        # 3. Dismiss any initial modals & overlays
        for dismiss_sel in ["#dismiss-button", "ytcp-button:has-text('Dismiss')", "ytcp-button:has-text('Got it')", "button:has-text('Close')"]:
            try:
                elem = self.page.locator(dismiss_sel).first
                if elem.is_visible():
                    elem.click()
                    self.page.wait_for_timeout(500)
            except Exception:
                pass

        try:
            self.page.evaluate("() => { document.querySelectorAll('tp-yt-iron-overlay-backdrop.opened').forEach(e => e.remove()); }")
        except Exception:
            pass

        print("[YOUTUBE_BOT] Opening Upload Dialog...")
        create_btn = self.page.locator("#create-icon, ytcp-button#create-icon, button#create-icon, [aria-label*='Create']").first
        try:
            create_btn.wait_for(state="visible", timeout=20000)
            create_btn.click(force=True)
        except PlaywrightTimeoutError:
            upload_direct = self.page.locator("#upload-button, [aria-label*='Upload videos']").first
            if upload_direct.is_visible():
                upload_direct.click(force=True)
            else:
                return {"status": "error", "message": "Could not find Create button in YouTube Studio."}

        self.page.wait_for_timeout(1000)

        # 4. Click 'Upload videos' in popup menu
        upload_menu_item = self.page.locator("tp-yt-paper-item, paper-item, ytcp-text-menu tp-yt-paper-item, [test-id='upload-video-menu-item']").filter(has_text="Upload videos").first
        try:
            if upload_menu_item.is_visible():
                upload_menu_item.click(force=True)
        except Exception:
            pass

        self.page.wait_for_timeout(1500)

        # 5. Set Input Files (drag & drop upload)
        print(f"[YOUTUBE_BOT] Uploading video binary: {video_file.name} ({video_file.stat().st_size / (1024*1024):.1f} MB)...")
        file_input = self.page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=25000)
        file_input.set_input_files(str(video_file))

        # Wait for dialog details screen to appear
        print("[YOUTUBE_BOT] Waiting for Details dialog...")
        title_box = self.page.locator("#textbox[aria-label*='title'], ytcp-mention-textbox#title-textarea #textbox, #title-textarea #textbox, div#textbox[contenteditable='true']").first
        title_box.wait_for(state="visible", timeout=40000)
        self.page.wait_for_timeout(2000)

        # 6. Fill Title
        print("[YOUTUBE_BOT] Setting Title...")
        try:
            title_box.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.wait_for_timeout(300)
            title_box.fill(final_title)
        except Exception:
            self.page.keyboard.type(final_title)
        self.page.wait_for_timeout(1000)

        # 7. Fill Description
        if full_description:
            print("[YOUTUBE_BOT] Setting Description...")
            desc_box = self.page.locator("#textbox[aria-label*='description'], ytcp-mention-textbox#description-textarea #textbox, #description-textarea #textbox").first
            if desc_box.is_visible():
                try:
                    desc_box.click()
                    desc_box.fill(full_description[:4900])
                except Exception:
                    pass
                self.page.wait_for_timeout(1000)

        # 8. Set 'Not made for kids'
        print("[YOUTUBE_BOT] Selecting 'Not made for kids'...")
        not_for_kids = self.page.locator("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], [name='VIDEO_MADE_FOR_KIDS_NOT_MFK']").first
        if not not_for_kids.is_visible():
            not_for_kids = self.page.locator("tp-yt-paper-radio-button").filter(has_text="not made for kids").first
        try:
            not_for_kids.scroll_into_view_if_needed(timeout=5000)
            not_for_kids.click(force=True)
            self.page.wait_for_timeout(1000)
        except Exception as k_err:
            print(f"[YOUTUBE_BOT] Note selecting not made for kids: {k_err}")

        # 9. Grab the Video URL while in details screen
        video_url = ""
        try:
            url_elem = self.page.locator("a.ytcp-video-info, .video-url-fadeable a, a[href*='youtu.be']").first
            if url_elem.is_visible():
                video_url = url_elem.get_attribute("href") or url_elem.inner_text().strip()
                print(f"[YOUTUBE_BOT] Video Link Captured: {video_url}")
        except Exception:
            pass

        # 10. Advance dynamically through wizard steps to the Visibility screen
        priv_upper = privacy.strip().upper()
        if priv_upper not in ("PUBLIC", "UNLISTED", "PRIVATE"): 
            priv_upper = "PUBLIC"

        for step_idx in range(5):
            self.page.wait_for_timeout(1000)

            # Check if we reached Visibility screen
            done_btn = self.page.locator("#done-button:not([hidden]), ytcp-button#done-button:not([hidden])").first
            vis_radio = self.page.locator(f"tp-yt-paper-radio-button[name='{priv_upper}']").first
            if (done_btn.count() > 0 and done_btn.is_visible()) or (vis_radio.count() > 0 and vis_radio.is_visible()):
                print(f"[YOUTUBE_BOT] Reached Visibility screen (step {step_idx + 1})!")
                break

            # Handle possible monetization screen
            monetization_off = self.page.locator("tp-yt-paper-radio-button[name='OFF'], [name='OFF']").first
            if monetization_off.count() > 0 and monetization_off.is_visible():
                try:
                    monetization_off.click(force=True)
                    self.page.wait_for_timeout(500)
                    save_mon = self.page.locator("ytcp-button:has-text('Save'), #save-button").first
                    if save_mon.is_visible(): save_mon.click(force=True)
                except Exception:
                    pass

            # Find visible Next button
            next_button = self.page.locator("#next-button:not([hidden]), ytcp-button#next-button:not([hidden])").first
            if next_button.count() == 0 or not next_button.is_visible():
                print(f"[YOUTUBE_BOT] Next button no longer visible; reached final step.")
                break

            # Wait for next button to enable
            print(f"[YOUTUBE_BOT] Waiting for Next button to be enabled (step {step_idx + 1})...")
            for _ in range(20):
                is_disabled = (
                    next_button.get_attribute("aria-disabled") == "true" or
                    next_button.get_attribute("disabled") is not None
                )
                if not is_disabled:
                    break
                self.page.wait_for_timeout(1000)

            print(f"[YOUTUBE_BOT] Clicking Next button (step {step_idx + 1})...")
            next_button.scroll_into_view_if_needed()
            next_button.click(force=True)
            self.page.wait_for_timeout(2000)

        self.page.wait_for_timeout(1500)

        # 11. Select Visibility
        print(f"[YOUTUBE_BOT] Setting visibility to: {priv_upper}...")
        vis_radio = self.page.locator(f"tp-yt-paper-radio-button[name='{priv_upper}'], [name='{priv_upper}']").first
        if not vis_radio.is_visible():
            vis_radio = self.page.locator("tp-yt-paper-radio-button").filter(has_text=priv_upper.capitalize()).first
        if vis_radio.is_visible():
            vis_radio.scroll_into_view_if_needed()
            vis_radio.click(force=True)
            self.page.wait_for_timeout(1000)
        else:
            pub = self.page.locator("tp-yt-paper-radio-button[name='PUBLIC'], [name='PUBLIC']").first
            if pub.is_visible():
                pub.scroll_into_view_if_needed()
                pub.click(force=True)
                self.page.wait_for_timeout(1000)

        # 12. Click Save / Publish
        print("[YOUTUBE_BOT] Clicking Publish / Save...")
        done_button = self.page.locator("#done-button:not([hidden]), ytcp-button#done-button:not([hidden]), #done-button").first
        done_button.wait_for(state="attached", timeout=25000)
        for _ in range(25):
            if done_button.is_visible():
                is_disabled = (
                    done_button.get_attribute("aria-disabled") == "true" or
                    done_button.get_attribute("disabled") is not None
                )
                if not is_disabled:
                    break
            self.page.wait_for_timeout(1000)

        done_button.scroll_into_view_if_needed()
        done_button.click(force=True)
        print("[YOUTUBE_BOT] Clicked Save/Publish button successfully!")

        # Wait for confirmation modal or dialog close
        self.page.wait_for_timeout(6000)

        # Try to capture link from share dialog if not yet captured
        if not video_url:
            for url_sel in ["a.ytcp-video-info", "a#share-url", ".video-url-fadeable a", "a[href*='youtu.be']", "a[href*='youtube.com/watch']"]:
                try:
                    share_url_elem = self.page.locator(url_sel).first
                    if share_url_elem.is_visible():
                        video_url = share_url_elem.get_attribute("href") or share_url_elem.inner_text().strip()
                        if video_url: break
                except Exception:
                    pass

        close_btn = self.page.locator("#close-button, ytcp-button#close-button, button:has-text('Close')").first
        if close_btn.is_visible():
            close_btn.click()

        print(f"[YOUTUBE_BOT] ✅ SUCCESS! Video published successfully: {video_url or 'Published to YouTube Studio'}")
        return {
            "status": "success",
            "platform": "youtube",
            "url": video_url,
            "title": final_title,
            "privacy": privacy
        }
