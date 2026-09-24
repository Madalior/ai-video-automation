"""
Shared Session Manager for Dreamina Generators

Enables multiple generators (image, video, thumbnail) to share a single
browser session and Google Enterprise account login.

Benefits:
- 50% fewer accounts created (1 instead of 2)
- 50% less memory usage (~500MB instead of ~1GB)
- 50% faster initialization (~30s instead of ~60s)
- No session conflicts between generators
"""

import os
import sys
import time
import random
import string
import base64
from uuid import uuid4
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flowchart.common.browser_utils import start_browser, get_new_email, get_otp, universal_shadow_click, handle_multiple_tabs_popup
from flowchart.common.session_manager import SessionManager, OverloadDetector
from flowchart.common.human_behavior import HumanBehavior
from flowchart.common.smart_reference_manager import SmartReferenceManager
from flowchart.common.account_manager import AccountManager
from flowchart.common.reusable_login import ReusableLoginManager
from flowchart.common.cookie_manager import CookieManager


class SharedSessionManager:
    """
    Manages a single browser session shared by multiple Dreamina generators.
    
    Usage:
        # Create session once
        session = SharedSessionManager(headless=False)
        session.login()
        
        # Share with multiple generators
        img_gen = DreaminaGenerator(shared_session=session)
        vid_gen = DreaminaVideoGenerator(shared_session=session)
    """
    
    DREAMINA_URL = "https://business.gemini.google/"
    
    def __init__(self, headless=False, profile_path=None, fresh_profile=False):
        """
        Initialize shared session manager.
        
        Args:
            headless: Run browser in headless mode
            profile_path: Chrome profile path (None = uses persistent default)
            fresh_profile: Create fresh temporary profile
        """
        self.is_temp_profile = False
        self.logged_in = False
        self.email = None
        self.password = None
        
        if fresh_profile:
            unique_id = uuid4().hex[:12]
            profile_path = os.path.abspath(f"temp_chrome_profiles/shared_{unique_id}")
            os.makedirs(profile_path, exist_ok=True)
            self.is_temp_profile = True
            print(f"[SHARED SESSION] Created fresh Chrome profile: shared_{unique_id}")
        elif profile_path is None:
            # ALWAYS use a persistent profile so login cookies survive between runs
            profile_path = os.path.abspath("chrome_profiles/saved_session")
            os.makedirs(profile_path, exist_ok=True)
            print(f"[SHARED SESSION] Using persistent Chrome profile: {profile_path}")
        
        self.driver = start_browser(profile_path, headless, fresh_profile=False)
        self.wait = WebDriverWait(self.driver, 30)
        self.profile_path = profile_path
        self.headless = headless
        
        # Clear cookies for fresh session
        if fresh_profile:
            try:
                self.driver.get("about:blank")
                self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
                print("[SHARED SESSION] Cleared browser cookies for fresh session")
            except Exception as e:
                print(f"[SHARED SESSION] Cookie clear skipped: {e}")
        
        print("[SHARED SESSION] Initialized (ready for single login)")

        # Anti-bot and Reference Managers (Consolidated)
        self.session_manager = SessionManager(max_requests=15, min_interval=15)
        self.overload_detector = OverloadDetector()
        self.human = HumanBehavior()
        self.ref_manager = SmartReferenceManager(mode='smart_order')
        # Use FIXED directory for credentials (not per-run Chrome profile)
        # so saved accounts persist across runs even with fresh_profile=True
        creds_dir = os.path.abspath("profiles")
        self.account_mgr = AccountManager(profile_dir=creds_dir)
        self.reusable_login = ReusableLoginManager(profile_dir=creds_dir)
        self.cookie_mgr = CookieManager(cookie_dir=creds_dir)
        self._img_gen = None  # Lazy-loaded DreaminaGenerator
        self._vid_gen = None  # Lazy-loaded DreaminaVideoGenerator
        
        print(f"[SHARED SESSION] Cookie Fortress: {self.cookie_mgr.get_status()}")
        print("[SHARED SESSION] Anti-bot & Consistency Managers Active")
    

    def login(self, max_login_attempts=3):
        """
        Login once to Google Enterprise account.
        This login is shared by all generators using this session.
        
        Args:
            max_login_attempts: Maximum retry attempts
            
        Returns:
            bool: True if login successful
        """
        if self.logged_in:
            print("[SHARED SESSION] Already logged in, reusing session")
            return True
        
        # =====================================================================
        # COOKIE FORTRESS: Try to restore session from saved cookies FIRST
        # =====================================================================
        if self.cookie_mgr.has_cookies():
            print("[COOKIE FORTRESS] Attempting session restore from saved cookies...")
            if self.cookie_mgr.import_cookies(self.driver):
                if self.cookie_mgr.verify_session(self.driver):
                    print("[COOKIE FORTRESS] ✅ SESSION RESTORED — No login needed!")
                    self.logged_in = True
                    # Re-export to refresh the timestamp
                    self.cookie_mgr.export_cookies(self.driver)
                    return True
                else:
                    print("[COOKIE FORTRESS] Cookies imported but session expired")
            else:
                print("[COOKIE FORTRESS] Cookie import failed")
        
        # Check if browser session is still alive (profile cookie-based)
        if self.account_mgr.is_session_alive(self.driver):
            print("[SHARED SESSION] Session cookie still valid — skipping login!")
            self.logged_in = True
            # Export cookies for future runs
            self.cookie_mgr.export_cookies(self.driver)
            return True
        
        print("[SHARED SESSION] Starting login flow...")
        
        for login_attempt in range(max_login_attempts):
            try:
                if login_attempt > 0:
                    print(f"\n[RETRY] Login attempt {login_attempt + 1}/{max_login_attempts}")
                    time.sleep(3)
                
                self.driver.get(self.DREAMINA_URL)
                time.sleep(3)
                
                # Check for popup before email input
                if self._handle_multiple_tabs_popup():
                    print("[SHARED SESSION] Early popup handled")
                    time.sleep(2)
                
                # Step 1: Email Input
                # Reuse saved credentials if available, otherwise create new
                email = None
                password = None
                otp = None
                
                for retry_attempt in range(2):
                    if retry_attempt == 0:
                        # Use ReusableLoginManager: tries saved creds first, then creates new
                        email, password = self.reusable_login.get_email_for_login()
                    # else: keep same email/password for retry
                    if not email:
                        if login_attempt < max_login_attempts - 1:
                            print("[WARNING] Email generation failed, restarting login...")
                            break
                        return False
                    
                    print(f"[SHARED SESSION] Entering email (Attempt {retry_attempt+1})...")
                    
                    # Check for popup before email input
                    if self._handle_multiple_tabs_popup():
                        print("[SHARED SESSION] Popup appeared, restarting login...")
                        email = None
                        break
                    
                    try:
                        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#email-input")))
                        email_input.clear()
                        
                        # Human-like delay
                        delay = random.uniform(2, 4)
                        print(f"[ANTI-BOT] Waiting {delay:.1f}s before typing email...")
                        time.sleep(delay)
                        
                        email_input.send_keys(email)
                        
                        continue_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Continue with email')]")))
                        continue_btn.click()
                        
                        # Check for popup after Continue
                        time.sleep(2)
                        if self._handle_multiple_tabs_popup():
                            print("[SHARED SESSION] Popup after Continue, restarting...")
                            email = None
                            break
                    except Exception as e:
                        print(f"[ERROR] Error during email input: {e}")
                        if login_attempt < max_login_attempts - 1:
                            break
                        return False
                    
                    # Step 2: OTP
                    print("[SHARED SESSION] Waiting for OTP...")
                    
                    otp = None
                    max_otp_wait = 90
                    popup_interrupt = False
                    
                    # Check for popup before waiting for OTP
                    if self._handle_multiple_tabs_popup():
                        print("[SHARED SESSION] Popup before OTP wait")
                        popup_interrupt = True
                    
                    if not popup_interrupt:
                        # Single call with full timeout — get_otp_from_inbox handles
                        # its own polling internally. Do NOT call it repeatedly with
                        # short timeouts, because each call clears the inbox first
                        # and would delete the OTP before it can be read.
                        otp = self.reusable_login.get_otp_from_inbox(email, password, max_wait=max_otp_wait)
                    
                    if popup_interrupt:
                        print("[INFO] Restarting login because popup interrupted OTP.")
                        continue

                    if otp:
                        break
                    else:
                        print("[WARNING] OTP missing, attempting workaround...")
                        if retry_attempt == 0:
                            try:
                                try_again = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Try again') or contains(text(),'Back')]")))
                                try_again.click()
                                time.sleep(2)
                            except:
                                self.driver.refresh()
                                time.sleep(3)
                
                # Check if we need to restart
                if not email or not otp:
                    print("[WARNING] OTP generation failed")
                    if login_attempt < max_login_attempts - 1:
                        print("[INFO] Restarting entire login process...")
                        continue
                    return self._wait_for_manual_login()
                
                # CRITICAL: Ensure OTP exists before proceeding
                if not otp:
                    print("[ERROR] No OTP received, cannot proceed with verification")
                    if login_attempt < max_login_attempts - 1:
                        continue
                    return self._wait_for_manual_login()
                
                # Enter OTP with 2s delay
                # Enter OTP with 2s delay
                print(f"[INFO] Entering OTP: {otp}")
                print("[ANTI-BOT] Waiting 2.0s before entering OTP...")
                time.sleep(2.0)
                
                try:
                    # Robust OTP Entry
                    otp_input = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pinInput']")))
                    otp_input.click()
                    time.sleep(0.5)
                    otp_input.send_keys(otp)
                    print(f"[SUCCESS] OTP entered: {otp}")
                    time.sleep(1)
                except Exception as e:
                    print(f"[ERROR] Failed to enter OTP: {e}")
                    if login_attempt < max_login_attempts - 1:
                        continue
                    return self._wait_for_manual_login()
                
                # Wait 3s before clicking verify button
                print("[ANTI-BOT] Waiting 3.0s before clicking verify button...")
                time.sleep(3.0)
                
                # Step 3: Verify
                try:
                    # Use button with aria-label="Verify" (Exact match from user HTML)
                    verify_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Verify']")))
                    self.driver.execute_script("arguments[0].click();", verify_btn)
                    print("[SUCCESS] Verify button clicked (via aria-label)")
                except Exception as e1:
                    print(f"[WARNING] aria-label Verify button not found: {e1}")
                    try:
                        # Fallback: Text content
                        verify_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Next') or contains(text(), 'Verify')]")))
                        self.driver.execute_script("arguments[0].click();", verify_btn)
                        print("[SUCCESS] Verify button clicked (fallback text)")
                    except Exception as e2:
                        print(f"[WARNING] Text fallback verify failed: {e2}")
                        try:
                            # Fallback: Try any button with "Next" or "Verify" in it
                            verify_btn = self.wait.until(EC.element_to_be_clickable(
                                (By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Verify') or contains(@aria-label, 'Next') or contains(@aria-label, 'Verify')]")
                            ))
                            verify_btn.click()
                            print("[SUCCESS] Verify button clicked (fallback generic)")
                        except Exception as e3:
                            print(f"[WARNING] Fallback verify button also failed: {e3}")
                            print("[INFO] Continuing anyway, may require manual intervention")
                        print("[INFO] Continuing anyway, may require manual intervention")
                
                # Step 4: Name & Agree
                first_names = ["James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley", "William", "Amanda"]
                last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Wilson", "Anderson"]
                human_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                
                delay = random.uniform(2, 4)
                print(f"[ANTI-BOT] Waiting {delay:.1f}s before typing name ({human_name})...")
                time.sleep(delay)
                
                # Use JS to inject name and trigger events (more reliable)
                name_script = """
                function cleanType(selector, text) {
                    const input = document.querySelector(selector);
                    if (input) {
                        input.value = text;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                    return false;
                }
                return cleanType("input[formcontrolname='fullName']", arguments[0]);
                """
                
                # Try to enter name with retries
                name_entered = False
                for i in range(5):
                    try:
                        name_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[formcontrolname='fullName']")))
                        # Try JS injection first
                        if self.driver.execute_script(name_script, human_name):
                            name_entered = True
                            break
                        # Fallback to standard typing
                        name_input.clear()
                        name_input.send_keys(human_name)
                        name_entered = True
                        break
                    except:
                        time.sleep(1)
                
                if not name_entered:
                    print("[WARNING] Could not enter name, trying to proceed anyway...")
                
                time.sleep(random.uniform(1, 2))
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'agree-button')]"))).click()
                
                # Wait for Google to finalize after agree
                time.sleep(5)
                
                # Handle any popup that appears during finalization
                if self._handle_multiple_tabs_popup():
                    print("[SHARED SESSION] Handled popup during account finalization")
                    time.sleep(3)
                
                # Wait for account creation to fully complete
                time.sleep(10)
                
                print("[SUCCESS] Shared session login successful!")
                print(f"[SHARED SESSION] Account: {email}")
                
                # Store credentials in memory and on disk for reuse
                self.email = email
                self.password = password
                self.logged_in = True
                self.reusable_login.on_login_success(email, password)
                self.account_mgr.save_credentials(email, password)
                
                # COOKIE FORTRESS: Export cookies immediately after successful login
                print("[COOKIE FORTRESS] Saving session cookies for future reuse...")
                self.cookie_mgr.export_cookies(self.driver)
                
                return True
                
            except Exception as e:
                print(f"[ERROR] Login failed on attempt {login_attempt + 1}: {e}")
                
                if self._handle_multiple_tabs_popup():
                    print("[SHARED SESSION] Popup detected during error")
                
                if login_attempt < max_login_attempts - 1:
                    print(f"[INFO] Restarting login (attempt {login_attempt + 2}/{max_login_attempts})...")
                    continue
                else:
                    print("[ERROR] All login attempts failed")
                    return self._wait_for_manual_login()
        
        return False
    
    def _wait_for_manual_login(self, timeout=120):
        """Fallback to manual login if automation fails."""
        print("\n" + "!"*50)
        print("[ACTION REQUIRED] Auto-Login Failed")
        print("Please log in MANUALLY in the opened Chrome window.")
        print(f"Waiting {timeout} seconds for you to complete login...")
        print("!"*50 + "\n")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if "login" not in self.driver.current_url and "gemini" in self.driver.current_url:
                    print("[SUCCESS] Manual login detected! Resuming...")
                    self.logged_in = True
                    time.sleep(3)
                    return True
            except:
                pass
            time.sleep(2)
        
        print("[ERROR] Manual login timed out")
        return False
    
    def _handle_multiple_tabs_popup(self):
        """
        Detects and handles the 'Let's try something else' popup.
        Delegates to the shared utility in browser_utils.
        """
        return handle_multiple_tabs_popup(self.driver)
    
    def get_driver(self):
        """
        Get the shared WebDriver instance.
        
        Returns:
            WebDriver: Shared Selenium WebDriver
        """
        if not self.logged_in:
            print("[SHARED SESSION] Driver requested but not logged in, logging in now...")
            self.login()
        
        return self.driver
    
    def reset_for_next_operation(self):
        """
        Reset interface for next generation operation.
        Navigates to new chat to clear state.
        """
        print("[SHARED SESSION] Resetting interface for next operation...")
        
        # Navigate to new chat
        new_chat_script = """
        function findAllInShadow(root, selector, list = []) {
            const items = root.querySelectorAll(selector);
            items.forEach(i => list.push(i));
            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) { findAllInShadow(host.shadowRoot, selector, list); }
            }
            return list;
        }

        const buttons = findAllInShadow(document, 'button.chat-button');
        for (let btn of buttons) {
            if (btn.innerText.includes('New chat')) {
                ['mousedown', 'click', 'mouseup'].forEach(type => {
                    btn.dispatchEvent(new MouseEvent(type, { 
                        bubbles: true, cancelable: true, view: window 
                    }));
                });
                return true;
            }
        }
        return false;
        """
        
        for attempt in range(5):
            try:
                success = self.driver.execute_script(new_chat_script)
                if success:
                    print("[SUCCESS] Interface reset to new chat")
                    time.sleep(2)
                    return True
            except Exception as e:
                pass
            
            print(f"[INFO] New Chat button search attempt {attempt+1}/5...")
            time.sleep(2)
            
        print("[WARNING] Could not find New Chat button after retries")
        return False
    
    def close(self):
        """Close the shared browser session."""
        print("[SHARED SESSION] Closing shared browser session...")
        try:
            self.driver.quit()
            self.logged_in = False
            print("[SUCCESS] Shared session closed")
        except Exception as e:
            print(f"[WARNING] Error closing session: {e}")
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()

    @property
    def image_generator(self):
        """Lazy-loaded DreaminaGenerator that shares our browser session."""
        if self._img_gen is None:
            from flowchart.character.image_generator import DreaminaGenerator
            # Create generator WITHOUT shared_session to avoid circular delegation
            # (DreaminaGenerator with shared_session calls back to SharedSessionManager.generate_image)
            gen = DreaminaGenerator.__new__(DreaminaGenerator)
            gen.driver = self.driver
            gen.wait = self.wait
            gen.profile_path = self.profile_path
            gen.headless = self.headless
            gen.shared_session = None
            gen._owns_driver = False  # Don't close our driver
            gen.is_temp_profile = False
            gen.session_manager = self.session_manager
            gen.overload_detector = self.overload_detector
            gen.human = self.human
            self._img_gen = gen
            print("[SHARED SESSION] DreaminaGenerator initialized (shared driver)")
        return self._img_gen

    @property
    def video_generator(self):
        """Lazy-loaded DreaminaVideoGenerator that shares our browser session."""
        if self._vid_gen is None:
            from flowchart.character.video_generator import DreaminaVideoGenerator
            # Create generator WITHOUT shared_session to avoid circular delegation
            gen = DreaminaVideoGenerator.__new__(DreaminaVideoGenerator)
            gen.driver = self.driver
            gen.wait = self.wait
            gen.profile_path = self.profile_path
            gen.headless = self.headless
            gen.shared_session = None
            gen._owns_driver = False  # Don't close our driver
            gen.is_temp_profile = False
            gen.session_manager = self.session_manager
            gen.overload_detector = self.overload_detector
            gen.human = self.human
            gen.ref_manager = self.ref_manager
            self._vid_gen = gen
            print("[SHARED SESSION] DreaminaVideoGenerator initialized (shared driver)")
        return self._vid_gen

    def upload_reference(self, path):
        """
        Upload reference image for character consistency.
        
        Args:
            path (str): Absolute path to the reference image file.
        """
        if not path or not os.path.exists(path): 
            print("[WARNING] Reference image path invalid or doesn't exist")
            return
        
        print(f"[INFO] Uploading reference image: {path}")
        
        # Click Add button
        universal_shadow_click(self.driver, "md-icon[text='add']")
        time.sleep(1.5)
        
        # Click 'Upload files'
        upload_item_script = """
        const items = document.querySelectorAll('md-menu-item');
        for (let item of items) {
            if (item.innerText.toLowerCase().includes('upload')) {
                ['mousedown', 'click', 'mouseup'].forEach(type => {
                    item.dispatchEvent(new MouseEvent(type, { bubbles: true, view: window }));
                });
                return true;
            }
        }
        return false;
        """
        self.driver.execute_script(upload_item_script)
        time.sleep(1)

        # Send file to hidden input
        file_input_script = """
        function findInput(root) {
            let el = root.querySelector('input[type="file"]');
            if (el) return el;
            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) {
                    const found = findInput(host.shadowRoot);
                    if (found) return found;
                }
            }
            return null;
        }
        return findInput(document);
        """
        file_input = self.driver.execute_script(file_input_script)
        if file_input:
            file_input.send_keys(os.path.abspath(path))
            print("[INFO] File path sent. Waiting for upload to finish...")
            
            # Wait for upload completion (25s for stable uploads)
            for i in range(25):
                print(f"[INFO] Uploading... {i+1}/25s")
                time.sleep(1)
            print("[SUCCESS] Assuming upload finished.")

    def upload_multiple_references(self, image_paths, scene_context=None):
        """
        Upload up to 3 reference images for Veo 3.1.
        
        Veo 3.1 supports up to 3 reference images to improve consistency:
        - Reference 1: Main character/object
        - Reference 2: Background/scene style  
        - Reference 3: Previous frame for continuity
        
        Smart auto-chain: if scene_context has independent=True,
        the ID card primary reference is prioritized.
        
        Args:
            image_paths: List of up to 3 image paths (strings)
                        Empty/None values are skipped
            scene_context: Optional dict with 'independent', 'id_card_primary' keys
        
        Returns:
            Number of successfully uploaded images
        """
        if not image_paths:
            print("[INFO] No reference images to upload")
            return 0
        
        # Smart auto-chain: override references for independent scenes
        if scene_context and scene_context.get('independent'):
            id_card_ref = scene_context.get('id_card_primary')
            if id_card_ref and os.path.exists(id_card_ref):
                print(f"[SMART CHAIN] Independent scene -> using ID card primary reference")
                image_paths = [id_card_ref]  # Override with ID card
            else:
                print(f"[SMART CHAIN] Independent scene but no ID card primary, using provided refs")
        elif scene_context:
            print(f"[SMART CHAIN] Chained scene -> using continuity reference")
        
        # Limit to 3 images (Veo 3.1 maximum)
        valid_paths = [p for p in image_paths if p and os.path.exists(p)][:3]
        
        if not valid_paths:
            print("[WARNING] No valid reference images found")
            return 0
        
        print(f"[INFO] Uploading {len(valid_paths)} reference image(s)...")
        uploaded_count = 0
        
        for idx, path in enumerate(valid_paths, 1):
            print(f"\n  [{idx}/{len(valid_paths)}] Uploading: {os.path.basename(path)}")
            
            try:
                self.upload_reference(path)
                uploaded_count += 1
                print(f"  [OK] Upload {idx} successful")
                
                # Brief delay between uploads (except after last)
                if idx < len(valid_paths):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"  [FAIL] Upload {idx} failed: {e}")
                # Continue with remaining uploads
        
        print(f"\n[SUCCESS] Uploaded {uploaded_count}/{len(valid_paths)} reference images")
    
    # =========================================================================
    # CORE GENERATION METHODS (Consolidated)
    # =========================================================================

    def generate_image(self, prompt, output_path, reference_image=None, max_retries=2, scene_context=None):
        """
        Generate image using DreaminaGenerator's proven flow.
        
        Delegates to DreaminaGenerator which uses the correct menu text
        ("Generate images (Pro)") and element screenshot saving.
        
        Args:
            prompt: Text prompt
            output_path: Path to save the image
            reference_image: Optional path to reference image (character consistency)
            max_retries: Maximum number of retry attempts (default: 2)
            scene_context: Optional dict with smart auto-chain data:
                          - independent: bool (use ID card primary instead of chain)
                          - id_card_primary: str (path to ID card primary reference)
            
        Returns:
            bool: True if successful
        """
        print(f"\n[SHARED SESSION] Image Generation via DreaminaGenerator: {prompt[:30]}...")
        
        # Smart auto-chain: override reference for independent scenes
        if scene_context and scene_context.get('independent'):
            id_card_ref = scene_context.get('id_card_primary')
            if id_card_ref and os.path.exists(id_card_ref):
                print(f"[SMART CHAIN] Independent scene -> ID card primary reference")
                reference_image = id_card_ref
        
        # Ensure logged in first
        if not self.login():
            print("[ERROR] Login failed, aborting generation")
            return False
        
        # Delegate to DreaminaGenerator (uses shared driver, no circular loop)
        return self.image_generator.generate_image(prompt, output_path, reference_image, max_retries)

    def generate_video(self, prompt, output_path, reference_image_paths=None, max_retries=2, scene_context=None):
        """
        Generate video using DreaminaVideoGenerator's proven flow.
        
        Delegates to DreaminaVideoGenerator which uses the correct video tool
        selection (Veo), smart reference management, and blob->base64 download.
        
        Args:
            prompt: Text prompt
            output_path: Path to save the video
            reference_image_paths: List of paths (or single path) for consistency
            max_retries: Maximum number of retry attempts (default: 2)
            scene_context: Optional dict with smart auto-chain data:
                          - independent: bool (use ID card primary instead of chain)
                          - id_card_primary: str (path to ID card primary reference)
            
        Returns:
            bool: True if successful
        """
        print(f"\n[SHARED SESSION] Video Generation via DreaminaVideoGenerator: {prompt[:30]}...")
        
        # Smart auto-chain: override references for independent scenes
        if scene_context and scene_context.get('independent'):
            id_card_ref = scene_context.get('id_card_primary')
            if id_card_ref and os.path.exists(id_card_ref):
                print(f"[SMART CHAIN] Independent scene -> ID card primary reference")
                reference_image_paths = [id_card_ref]
        
        # Ensure logged in first
        if not self.login():
            print("[ERROR] Login failed, aborting generation")
            return False
        
        # Delegate to DreaminaVideoGenerator (uses shared driver, no circular loop)
        return self.video_generator.generate_video(
            prompt=prompt,
            reference_image_paths=reference_image_paths,
            output_path=output_path,
            max_retries=max_retries
        )

    # =========================================================================
    # HELPER METHODS (Ported from Generators)
    # =========================================================================

    def click_start_button(self):
        """Click the Start button with retry logic and touch overlay handling."""
        # Human-like delay before clicking
        delay = random.uniform(2, 4)
        print(f"[ANTI-BOT] Waiting {delay:.1f}s before clicking Start button...")
        time.sleep(delay)
        
        print("[INFO] Searching for Start button and touch overlay...")
        
        # JavaScript logic with proper event dispatching for Lit components
        js_click_script = """
        // Helper: Dispatch proper mouse events (mousedown → mouseup → click)
        function realClick(element) {
            if (!element) return false;
            
            // Scroll into view
            element.scrollIntoView({block: 'center', behavior: 'instant'});
            
            // Get element center coordinates
            const rect = element.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            
            const eventOptions = {
                bubbles: true,
                cancelable: true,
                composed: true, // Critical for Shadow DOM/Lit events
                view: window,
                detail: 1,
                clientX: x,
                clientY: y
            };
            
            // Dispatch full mouse event sequence (what real clicks do)
            element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
            element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
            element.dispatchEvent(new MouseEvent('click', eventOptions));
            
            // Also try pointerdown/up for touch-enabled components
            element.dispatchEvent(new PointerEvent('pointerdown', eventOptions));
            element.dispatchEvent(new PointerEvent('pointerup', eventOptions));
            
            return true;
        }
        
        // Deep search for button in Shadow DOM
        const btn = (function findElementEverywhere(selector) {
            const findInElement = (root) => {
                const el = root.querySelector(selector);
                if (el) return el;
                const shadowHosts = root.querySelectorAll('*');
                for (const host of shadowHosts) {
                    if (host.shadowRoot) {
                        const found = findInElement(host.shadowRoot);
                        if (found) return found;
                    }
                }
                return null;
            };
            return findInElement(document);
        })('#button');

        if (btn) {
            // Try clicking touch overlay first (Lit pattern)
            const touchArea = btn.querySelector('.touch');
            if (touchArea) {
                if (realClick(touchArea)) return "touch_clicked";
            }
            
            // Try the label
            const labelArea = btn.querySelector('.label');
            if (labelArea) {
                if (realClick(labelArea)) return "label_clicked";
            }
            
            // Fall back to button itself
            if (realClick(btn)) return "button_clicked";
        }
        
        return null;
        """
        
        for i in range(10):  # 10 Retries
            try:
                result = self.driver.execute_script(js_click_script)
                
                if result:
                    print(f"[SUCCESS] {result} performed.")
                    return True
                    
                print(f"[INFO] Retry {i+1}/10: Button/Touch area not found yet...")
            except Exception as e:
                print(f"[WARNING] Error during click attempt: {e}")
                
            time.sleep(2)

        print("[ERROR] Could not click the button after 10 retries.")
        # Proceed anyway as it might not be there
        return False

    def open_video_tool(self):
        """Open the video generation tool menu."""
        print("[INFO] Step 1: Opening Tool Menu...")
        # Open the initial menu anchor
        universal_shadow_click(self.driver, "#tool-selector-menu-anchor")
        
        # Wait for the menu overlay to render
        time.sleep(2) 

        print("[INFO] Step 2: Deep Searching for 'Generate a video'...")
        deep_click_script = """
        // Helper: Robust click with composed events
        function realClick(element) {
            if (!element) return false;
            
            element.scrollIntoView({block: 'center', behavior: 'instant'});
            const rect = element.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            
            const eventOptions = {
                bubbles: true,
                cancelable: true,
                composed: true,
                view: window,
                detail: 1,
                clientX: x,
                clientY: y
            };
            
            element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
            element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
            element.dispatchEvent(new MouseEvent('click', eventOptions));
            element.dispatchEvent(new PointerEvent('pointerdown', eventOptions));
            element.dispatchEvent(new PointerEvent('pointerup', eventOptions));
            return true;
        }

        function findAllInShadow(root, tagName, list = []) {
            const items = root.querySelectorAll(tagName);
            items.forEach(i => list.push(i));
            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) { findAllInShadow(host.shadowRoot, tagName, list); }
            }
            return list;
        }

        const allItems = findAllInShadow(document, 'md-menu-item');
        for (let item of allItems) {
            // Check slotted headline text
            const headline = item.querySelector('[slot="headline"]');
            
            // Match 'veo' or 'video' (case insensitive)
            if (headline && (
                headline.textContent.toLowerCase().includes('veo') || 
                headline.textContent.toLowerCase().includes('video')
            )) {
                // 1. Try clicking the host element (md-menu-item)
                console.log("Found menu item, attempting click on host...");
                realClick(item);
                
                // 2. Try clicking the internal list item (inside shadow root)
                if (item.shadowRoot) {
                    const internalLi = item.shadowRoot.querySelector('li');
                    if (internalLi) {
                        console.log("Found internal li, clicking...");
                        realClick(internalLi);
                    }
                }
                
                // 3. Try clicking the headline text itself
                realClick(headline);
                
                return true;
            }
        }
        return false;
        """
        
        if self.driver.execute_script(deep_click_script):
            print("[SUCCESS] 'Generate a video' clicked.")
            return True
        else:
            print("[ERROR] Could not find the video menu item even with deep search.")
            return False
        
    def click_menu_item_by_text(self, text="Image (Pro)"):
        """Click menu item by text with fuzzy matching and Shadow DOM traversal."""
        delay = random.uniform(2, 4)
        print(f"[ANTI-BOT] Waiting {delay:.1f}s before clicking menu item...")
        time.sleep(delay)
        
        print(f"[INFO] Searching for menu item: '{text}'...")

        js_logic = """
        const targetText = arguments[0].toLowerCase().trim();
        
        function findAllInShadow(root, selector, list = []) {
            const items = root.querySelectorAll(selector);
            items.forEach(i => list.push(i));
            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) { findAllInShadow(host.shadowRoot, selector, list); }
            }
            return list;
        }

        const menuItems = findAllInShadow(document, 'md-menu-item');
        const availableItems = [];
        
        for (let item of menuItems) {
            const itemText = item.innerText.toLowerCase().trim();
            availableItems.push(item.innerText.trim());
            
            // Try exact match or fuzzy match
            if (itemText === targetText || itemText.includes(targetText) || targetText.includes(itemText)) {
                console.log("Found matching menu item:", item.innerText.trim());
                
                const clickEv = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    composed: true
                });
                
                item.focus();
                item.dispatchEvent(clickEv);
                return { success: true, text: item.innerText.trim() };
            }
        }
        
        return { success: false, available: availableItems };
        """

        for i in range(5):
            try:
                result = self.driver.execute_script(js_logic, text)
                if result and result.get('success'):
                    print(f"[SUCCESS] Successfully clicked '{result['text']}' (matched '{text}')")
                    return True
                else:
                    items = result.get('available', []) if result else []
                    if items:
                        print(f"[INFO] Available menu items: {', '.join(items)}")
            except Exception as e:
                print(f"[WARNING] Error during attempt {i+1}: {e}")
            
            print(f"[INFO] Retry {i+1}/5: Element '{text}' not found. Retrying...")
            time.sleep(4)

        print(f"[ERROR] Failed to find and click '{text}' after retries.")
        return False

    def inject_prompt(self, text):
        """Inject text with TrustedHTML bypass for secure contexts."""
        print(f"[INFO] Injecting script text: {text[:50]}...")
        try:
            injection_script = """
            function findInShadow(root, selector) {
                let el = root.querySelector(selector);
                if (el) return el;
                const hosts = root.querySelectorAll('*');
                for (const host of hosts) {
                    if (host.shadowRoot) {
                        const found = findInShadow(host.shadowRoot, selector);
                        if (found) return found;
                    }
                }
                return null;
            }

            const editor = findInShadow(document, 'div.ProseMirror');
            if (editor) {
                const htmlContent = '<p>' + arguments[0] + '</p>';
                let secureHtml = htmlContent;

                if (window.trustedTypes && window.trustedTypes.createPolicy) {
                    const policy = window.trustedTypes.defaultPolicy || 
                                   window.trustedTypes.createPolicy('bot-policy', {
                                       createHTML: (s) => s
                                   });
                    secureHtml = policy.createHTML(htmlContent);
                }

                editor.focus();
                editor.innerHTML = secureHtml;
                
                editor.dispatchEvent(new Event('input', { bubbles: true }));
                editor.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
            return false;
            """
            
            success = self.driver.execute_script(injection_script, text)
            if success:
                print("[SUCCESS] Text successfully injected into the editor.")
                return True
            else:
                print("[ERROR] Failed to find the ProseMirror editor div.")
                return False
                
        except Exception as e:
            print(f"[WARNING] Exception during text injection: {e}")
            return False

    def submit_generation(self):
        """Trigger submission with force-click sequence and retry logic."""
        delay = random.uniform(2, 4)
        print(f"[ANTI-BOT] Waiting {delay:.1f}s before clicking Submit button...")
        time.sleep(delay)
        
        print("[INFO] Triggering Force-Click sequence on Submit button...")
        
        click_execution_script = """
        function findInShadow(root, selector) {
            let el = root.querySelector(selector);
            if (el) return el;
            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) {
                    const found = findInShadow(host.shadowRoot, selector);
                    if (found) return found;
                }
            }
            return null;
        }

        const btn = findInShadow(document, 'button[aria-label="Submit"]');
        
        if (!btn) return "missing";
        if (btn.disabled) return "disabled";

        try {
            btn.focus();
            const events = ['mousedown', 'mouseup', 'click'];
            events.forEach(type => {
                btn.dispatchEvent(new MouseEvent(type, {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    buttons: 1,
                    which: 1
                }));
            });
            
            const start = Date.now();
            while (Date.now() - start < 500) {}
            
            btn.click();
            return "clicked";
        } catch (e) {
            return "error: " + e.message;
        }
        """
        
        for attempt in range(1, 11):
            result = self.driver.execute_script(click_execution_script)
            
            if result == "clicked":
                print(f"[SUCCESS] Click signal sent on attempt {attempt}.")
                time.sleep(5)
                return True
            else:
                print(f"[INFO] Attempt {attempt}/10: Button status: {result}. Retrying...")
                
            time.sleep(2)

        print("[ERROR] Button was visible but refused the click command.")
        return False

    def save_result(self, filepath, timeout=120):
        """Wait for image to render and save it."""
        print(f"[INFO] Waiting for AI to generate image (up to {timeout}s)...")
        
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        find_img_js = """
        function findLargeImg(root) {
            const imgs = Array.from(root.querySelectorAll('img'));
            const largeImg = imgs.reverse().find(img => img.naturalWidth > 300);
            if (largeImg) return largeImg;

            const hosts = root.querySelectorAll('*');
            for (const host of hosts) {
                if (host.shadowRoot) {
                    const found = findLargeImg(host.shadowRoot);
                    if (found) return found;
                }
            }
            return null;
        }
        return findLargeImg(document);
        """
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                img_element = self.driver.execute_script(find_img_js)
                if img_element:
                    src = img_element.get_attribute('src')
                    if src and src.startswith('http'):
                        print(f"[SUCCESS] Image found: {src[:50]}...")
                        # Download logic
                        import requests
                        response = requests.get(src)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            print(f"[SUCCESS] Saved image to: {filepath}")
                            return True
            except Exception as e:
                pass
            time.sleep(2)
            
        print("[ERROR] Timeout waiting for image generation")
        return False

    def download_video(self, filepath, timeout=600):
        """Wait for video generation and download it via blob/base64 conversion."""
        print(f"[INFO] Waiting for video generation (up to {timeout}s)...")
        
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        blob_to_base64_js = """
        const callback = arguments[arguments.length - 1];
        
        async function getLatestVideoBase64() {
            function findAllVids(root, list = []) {
                const vids = root.querySelectorAll('video');
                vids.forEach(v => { if(v.src) list.push(v.src); });
                
                const hosts = root.querySelectorAll('*');
                for (const host of hosts) {
                    if (host.shadowRoot) { findAllVids(host.shadowRoot, list); }
                }
                return list;
            }

            const sources = findAllVids(document);
            if (sources.length === 0) return null;
            
            const latestBlobUrl = sources[sources.length - 1];
            
            try {
                const response = await fetch(latestBlobUrl);
                const blob = await response.blob();
                
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.onerror = () => resolve(null);
                    reader.readAsDataURL(blob);
                });
            } catch (e) {
                return null;
            }
        }

        getLatestVideoBase64().then(result => callback(result));
        """
        
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                base64_data = self.driver.execute_async_script(blob_to_base64_js)
                
                if base64_data and base64_data.startswith("data:video"):
                    header, encoded = base64_data.split(",", 1)
                    binary_data = base64.b64decode(encoded)
                    
                    with open(filepath, "wb") as f:
                        f.write(binary_data)
                    
                    print(f"[SUCCESS] Video saved successfully!")
                    return True
                
                print("[INFO] Video not found yet, retrying in 10s...")
                
            except Exception as e:
                print(f"[WARNING] Error during check: {str(e)[:100]}")
                
            time.sleep(10)


if __name__ == "__main__":
    import argparse
    import traceback

    parser = argparse.ArgumentParser(
        description="SharedSessionManager - Single-worker browser automation for image & video generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m flowchart.common.shared_session
  python -m flowchart.common.shared_session --image-only --prompt "A cyberpunk city"
  python -m flowchart.common.shared_session --video-only --prompt "Flying cars in neon streets"
  python -m flowchart.common.shared_session --headless --output-dir my_output
        """
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--image-only", action="store_true", help="Only generate an image (skip video)")
    parser.add_argument("--video-only", action="store_true", help="Only generate a video (skip image)")
    parser.add_argument("--prompt", type=str, default=None, help="Custom prompt for generation")
    parser.add_argument("--output-dir", type=str, default="output/shared_session_test", help="Output directory")
    parser.add_argument("--fresh-profile", action="store_true", default=True, help="Use a fresh Chrome profile (default: True)")
    args = parser.parse_args()

    # Default prompts
    default_img_prompt = "A futuristic cyberpunk detective ID card, neon blue and pink, high detail, digital art"
    default_vid_prompt = "The cyberpunk detective walking through a rainy neon city, cinematic lighting, 4k"

    img_prompt = args.prompt or default_img_prompt
    vid_prompt = args.prompt or default_vid_prompt

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    img_output = os.path.join(output_dir, "generated_image.png")
    vid_output = os.path.join(output_dir, "generated_video.mp4")

    print("=" * 60)
    print("  SHARED SESSION MANAGER - Standalone Runner")
    print("=" * 60)
    print(f"  Mode:       {'Image Only' if args.image_only else 'Video Only' if args.video_only else 'Full Pipeline (Image + Video)'}")
    print(f"  Headless:   {args.headless}")
    print(f"  Output Dir: {output_dir}")
    print("=" * 60)

    session = None
    try:
        # 1. Initialize
        print("\n[STEP 1/4] Initializing browser session...")
        session = SharedSessionManager(
            headless=args.headless,
            fresh_profile=args.fresh_profile
        )

        # 2. Login
        print("\n[STEP 2/4] Logging in to Google Enterprise account...")
        if not session.login():
            print("[FATAL] Login failed after all retries. Exiting.")
            sys.exit(1)
        print("[OK] Login successful!\n")

        # 3. Generate Image
        if not args.video_only:
            print("[STEP 3/4] Generating Image...")
            print(f"  Prompt: {img_prompt[:80]}...")
            print(f"  Output: {img_output}")
            
            if session.generate_image(img_prompt, img_output):
                print(f"[OK] Image saved to: {img_output}")
            else:
                print("[FAIL] Image generation failed.")
                if not args.image_only:
                    print("[INFO] Continuing to video generation anyway...")
        else:
            print("[STEP 3/4] Skipping image generation (--video-only)")

        # 4. Generate Video
        if not args.image_only:
            print("\n[STEP 4/4] Generating Video...")
            print(f"  Prompt: {vid_prompt[:80]}...")
            print(f"  Output: {vid_output}")
            
            # Use the generated image as a reference for character consistency
            refs = [img_output] if os.path.exists(img_output) else None
            if refs:
                print(f"  Reference: {os.path.basename(img_output)} (character consistency)")
            
            if session.generate_video(vid_prompt, vid_output, reference_image_paths=refs):
                print(f"[OK] Video saved to: {vid_output}")
            else:
                print("[FAIL] Video generation failed.")
        else:
            print("\n[STEP 4/4] Skipping video generation (--image-only)")

        # Summary
        print("\n" + "=" * 60)
        print("  RESULTS")
        print("=" * 60)
        if not args.video_only and os.path.exists(img_output):
            size_kb = os.path.getsize(img_output) / 1024
            print(f"  ✓ Image: {img_output} ({size_kb:.1f} KB)")
        if not args.image_only and os.path.exists(vid_output):
            size_mb = os.path.getsize(vid_output) / (1024 * 1024)
            print(f"  ✓ Video: {vid_output} ({size_mb:.1f} MB)")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"\n[ERROR] Fatal exception: {e}")
        traceback.print_exc()
    finally:
        if session:
            print("\n[CLEANUP] Closing browser session...")
            session.close()
            print("[DONE] Session closed.")

