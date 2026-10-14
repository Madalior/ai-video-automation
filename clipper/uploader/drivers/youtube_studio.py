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

        # 2. Navigate directly to Studio Upload Dialog
        print("[YOUTUBE_BOT] Navigating directly to YouTube Studio Upload interface...")
        self.page.goto("https://studio.youtube.com/?d=ud", wait_until="domcontentloaded", timeout=45000)

        # Allow up to 10 seconds for any Google CheckCookie SSO bounce to complete
        for _ in range(5):
            if "studio.youtube.com" in self.page.url and "accounts.google.com" not in self.page.url:
                break
            self.page.wait_for_timeout(2000)

        # Check for "Skip to YouTube Studio" browser warning page
        skip_btn = self.page.locator("a:has-text('Skip to YouTube Studio')").first
        if skip_btn.is_visible():
            print("[YOUTUBE_BOT] Bypassing browser version check -> Clicking 'Skip to YouTube Studio'...")
            skip_btn.click()
            self.page.wait_for_timeout(4000)

        # If on account chooser, attempt to click the account card
        if "accounts.google.com" in self.page.url:
            acct_btn = self.page.locator("[data-identifier], [data-email], div[role='link']:has-text('@gmail.com')").first
            if acct_btn.is_visible():
                print("[YOUTUBE_BOT] Detected Account Chooser. Attempting to select account...")
                try:
                    acct_btn.click()
                    self.page.wait_for_timeout(5000)
                except Exception:
                    pass

        if "accounts.google.com" in self.page.url:
            return {
                "status": "error",
                "message": "Session expired or not logged in. Please run the 1-time login command."
            }

        # 3. Dismiss any initial modals & overlays (except upload dialog)
        for dismiss_sel in ["#dismiss-button", "ytcp-button:has-text('Dismiss')", "ytcp-button:has-text('Got it')"]:
            try:
                elem = self.page.locator(dismiss_sel).first
                if elem.is_visible():
                    elem.click()
                    self.page.wait_for_timeout(500)
            except Exception:
                pass

        # Check and cancel any previous stuck upload draft
        cancel_btn = self.page.locator("button:has-text('Cancel upload'), ytcp-button:has-text('Cancel upload'), [aria-label*='Cancel upload']").first
        if cancel_btn.is_visible():
            print("[YOUTUBE_BOT] Found previous stuck upload draft. Cancelling it cleanly...")
            try:
                cancel_btn.click(force=True)
                self.page.wait_for_timeout(2000)
                confirm_btn = self.page.locator("ytcp-button:has-text('Cancel upload'), button:has-text('Cancel upload')").first
                if confirm_btn.is_visible():
                    confirm_btn.click(force=True)
                    self.page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[YOUTUBE_BOT] Cancel draft note: {e}")

        print("[YOUTUBE_BOT] Verifying Upload Dialog and File Input...")
        file_input = self.page.locator("input[type='file']").first
        
        # Click dashboard up-arrow upload button or center upload button if file input not yet attached
        for _ in range(15):
            if file_input.count() > 0:
                break
            btn = self.page.locator("#upload-button, [aria-label*='Upload'], ytcp-button#upload-button, ytcp-button:has-text('Upload videos'), button:has-text('Upload videos'), ytcp-button:has-text('Create'), button:has-text('Create')").first
            try:
                if btn.is_visible():
                    print("[YOUTUBE_BOT] Clicking Upload button on dashboard...")
                    btn.click(force=True)
                    self.page.wait_for_timeout(2000)
            except Exception:
                pass
            self.page.wait_for_timeout(1000)

        # 5. Set Input Files (drag & drop upload)
        print(f"[YOUTUBE_BOT] Uploading video binary: {video_file.name} ({video_file.stat().st_size / (1024*1024):.1f} MB)...")
        file_input = self.page.locator("input[type='file']").first
        file_input.wait_for(state="attached", timeout=30000)
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
            next_button = self.page.locator("#next-button:not([hidden]), ytcp-button#next-button:not([hidden]), ytcp-button:has-text('Next'), button:has-text('Next')").first
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

        # 12. Wait for binary upload transmission to complete (Upload complete / Processing / Checks)
        print("[YOUTUBE_BOT] Waiting for file transmission to reach 100% (Upload complete)...")
        for wait_idx in range(90):
            progress_el = self.page.locator(".progress-label, ytcp-video-upload-progress, [class*='progress-label']").first
            status_text = ""
            if progress_el.count() > 0:
                try:
                    status_text = progress_el.inner_text().strip()
                except Exception:
                    pass
            
            dialog_text = ""
            try:
                dialog_text = self.page.locator("ytcp-uploads-dialog, [role='dialog']").first.inner_text()
            except Exception:
                pass
            
            combined = f"{status_text} {dialog_text}"
            if any(term in combined for term in ["Upload complete", "Processing", "Checks complete", "Checks finished"]):
                print(f"[YOUTUBE_BOT] ✅ Upload transmission complete: '{status_text or 'Upload complete'}'")
                break
                
            if wait_idx % 5 == 0 and status_text:
                print(f"[YOUTUBE_BOT] Upload progress: {status_text}")
                
            self.page.wait_for_timeout(2000)

        # 13. Click Save / Publish
        print("[YOUTUBE_BOT] Clicking Publish / Save...")
        done_button = self.page.locator("#done-button:not([hidden]), ytcp-button#done-button:not([hidden]), #done-button, ytcp-button:has-text('Publish'), button:has-text('Publish'), ytcp-button:has-text('Save'), button:has-text('Save')").first
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
        self.page.wait_for_timeout(8000)
        try:
            self.page.screenshot(path="/app/output/yt_published_confirmation.png")
        except Exception:
            pass

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
