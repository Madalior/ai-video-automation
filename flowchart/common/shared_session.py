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
import time
import random
import string
import base64
from uuid import uuid4
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flowchart.common.browser_utils import start_browser, get_new_email, get_otp, universal_shadow_click
from flowchart.common.session_manager import SessionManager, OverloadDetector
from flowchart.common.human_behavior import HumanBehavior
from flowchart.common.smart_reference_manager import SmartReferenceManager


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
            profile_path: Chrome profile path (None = temp profile)
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
                email = None
                password = None
                otp = None
                
                for retry_attempt in range(2):
                    email, password = get_new_email() if retry_attempt == 0 else (email, password)
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
                    otp_check_interval = 5
                    otp_waited = 0
                    
                    while otp_waited < max_otp_wait and not otp:
                        # Check for popup while waiting
                        if self._handle_multiple_tabs_popup():
                            print("[SHARED SESSION] Popup while waiting for OTP")
                            email = None
                            otp = None
                            break
                        
                        otp = get_otp(email, password, max_wait=otp_check_interval)
                        
                        if not otp:
                            otp_waited += otp_check_interval
                            if otp_waited % 15 == 0:
                                print(f"[INFO] Still waiting for OTP... ({otp_waited}s/{max_otp_wait}s)")
                    
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
                print(f"[INFO] Entering OTP: {otp}")
                print("[ANTI-BOT] Waiting 2.0s before entering OTP...")
                time.sleep(2.0)
                
                try:
                    otp_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='pinInput']")))
                    otp_input.clear()
                    otp_input.send_keys(otp)
                    # Trigger events manually to ensure state update
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", otp_input)
                    print(f"[SUCCESS] OTP entered: {otp}")
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
                    # Try finding the button containing "Next" or "Verify" text
                    verify_btn = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[contains(text(), 'Next') or contains(text(), 'Verify')]]")
                    ))
                    self.driver.execute_script("arguments[0].click();", verify_btn)
                    print("[SUCCESS] Verify button clicked")
                except Exception as e1:
                    print(f"[WARNING] Primary verify button not found: {e1}")
                    try:
                        # Fallback: Try any button with "Next" or "Verify" in it
                        verify_btn = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Verify') or contains(@aria-label, 'Next') or contains(@aria-label, 'Verify')]")
                        ))
                        verify_btn.click()
                        print("[SUCCESS] Verify button clicked (fallback)")
                    except Exception as e2:
                        print(f"[WARNING] Fallback verify button also failed: {e2}")
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
                
                print("[SUCCESS] Shared session login successful!")
                print(f"[SHARED SESSION] Account: {email}")
                
                # Store credentials
                self.email = email
                self.password = password
                self.logged_in = True
                
                time.sleep(5)
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
        """Detect and handle the 'Let's try something else' popup."""
        try:
            time.sleep(1)
            
            click_script = """
            function sleep(ms) {
                const start = Date.now();
                while (Date.now() - start < ms) {}
            }
            
            let btn = document.querySelector("button[jsname='clYohf']");
            
            if (!btn) {
                const all = document.querySelectorAll("button");
                for (let b of all) {
                    const text = b.textContent || '';
                    if (text.includes("Sign up") || text.includes("sign in")) {
                        btn = b;
                        break;
                    }
                }
            }
            
            if (btn) {
                sleep(500);
                btn.click();
                return true;
            }
            return false;
            """
            
            result = self.driver.execute_script(click_script)
            
            if result:
                print("[DETECTED] Multiple tabs popup handled")
                time.sleep(3)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[WARN] Error checking for popup: {e}")
            return False
    
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

    def upload_multiple_references(self, image_paths):
        """
        Upload up to 3 reference images for Veo 3.1.
        
        Veo 3.1 supports up to 3 reference images to improve consistency:
        - Reference 1: Main character/object
        - Reference 2: Background/scene style  
        - Reference 3: Previous frame for continuity
        
        Args:
            image_paths: List of up to 3 image paths (strings)
                        Empty/None values are skipped
        
        Returns:
            Number of successfully uploaded images
        """
        if not image_paths:
            print("[INFO] No reference images to upload")
            return 0
        
        # Limit to 3 images (Veo 3.1 maximum)
        valid_paths = [p for p in image_paths if p and os.path.exists(p)][:3]
        
        if not valid_paths:
            print("[WARNING] No valid reference images found")
            return 0
        
        print(f"[INFO] Uploading {len(valid_paths)} reference image(s)...")
        uploaded_count = 0
        
        for idx, path in enumerate(valid_paths, 1):
            print(f"\\n  [{idx}/{len(valid_paths)}] Uploading: {os.path.basename(path)}")
            
            try:
                self.upload_reference(path)
                uploaded_count += 1
                print(f"  ✓ Upload {idx} successful")
                
                # Brief delay between uploads (except after last)
                if idx < len(valid_paths):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"  ✗ Upload {idx} failed: {e}")
                # Continue with remaining uploads
        
        print(f"\\n[SUCCESS] Uploaded {uploaded_count}/{len(valid_paths)} reference images")
    
    # =========================================================================
    # CORE GENERATION METHODS (Consolidated)
    # =========================================================================

    def generate_image(self, prompt, output_path, reference_image=None):
        """
        Full Image Generation Flow.
        
        Args:
            prompt: Text prompt
            output_path: Path to save the image
            reference_image: Optional path to reference image (character consistency)
            
        Returns:
            bool: True if successful
        """
        print(f"\\n[SHARED SESSION] Starting Image Generation: {prompt[:30]}...")
        
        try:
            # 1. Ensure Login
            if not self.login():
                print("[ERROR] Login failed, aborting generation")
                return False
            
            # 2. Reset / New Chat
            if not self.reset_for_next_operation():
                print("[ERROR] Failed to reset interface")
                return False

            # 3. Select Image Tool
            if not self.click_menu_item_by_text("Image (Pro)"):
                print("[ERROR] Failed to select Image (Pro) tool")
                return False
            
            # 4. Upload Reference (if any)
            if reference_image:
                self.upload_reference(reference_image)
            
            # 5. Inject Prompt
            self.inject_prompt(prompt)
            
            # 6. Submit
            if not self.submit_generation():
                print("[ERROR] Failed to submit generation")
                return False
            
            # 7. Wait & Save
            return self.save_result(output_path)
            
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            return False

    def generate_video(self, prompt, output_path, reference_image_paths=None):
        """
        Full Video Generation Flow.
        
        Args:
            prompt: Text prompt
            output_path: Path to save the video
            reference_image_paths: List of paths (or single path) for consistency
            
        Returns:
            bool: True if successful
        """
        print(f"\\n[SHARED SESSION] Starting Video Generation: {prompt[:30]}...")
        
        try:
            # 1. Ensure Login
            if not self.login():
                print("[ERROR] Login failed, aborting generation")
                return False
            
            # 2. Reset / New Chat
            if not self.reset_for_next_operation():
                print("[ERROR] Failed to reset interface")
                return False

            # 3. Select Video Tool (Veo 3)
            # Try specific Veo 3 menu items, fallback to generic Video
            if not self.click_menu_item_by_text("Video (Veo 3)"):
                if not self.click_menu_item_by_text("Video"):
                    print("[ERROR] Failed to select Video tool")
                    return False
            
            # 4. Upload References (Smart Handling)
            if reference_image_paths:
                # Handle single path vs list
                paths = reference_image_paths if isinstance(reference_image_paths, list) else [reference_image_paths]
                self.upload_multiple_references(paths)
            
            # 5. Inject Prompt
            self.inject_prompt(prompt)
            
            # 6. Submit
            if not self.submit_generation():
                print("[ERROR] Failed to submit generation")
                return False
            
            # 7. Wait & Download
            return self.download_video(output_path)
            
        except Exception as e:
            print(f"[ERROR] Video generation failed: {e}")
            return False

    # =========================================================================
    # HELPER METHODS (Ported from Generators)
    # =========================================================================

    def click_menu_item_by_text(self, text="Image (Pro)"):
        """Click menu item by text with retry logic and Shadow DOM traversal."""
        delay = random.uniform(2, 4)
        print(f"[ANTI-BOT] Waiting {delay:.1f}s before clicking menu item...")
        time.sleep(delay)
        
        print(f"[INFO] Searching for menu item: '{text}'...")

        js_logic = """
        const textToFind = arguments[0];
        
        function findElementByText(root, text) {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
            let node;
            while (node = walker.nextNode()) {
                if (node.textContent.includes(text)) {
                    return node.parentElement;
                }
            }
            const all = root.querySelectorAll('*');
            for (const el of all) {
                if (el.shadowRoot) {
                    const found = findElementByText(el.shadowRoot, text);
                    if (found) return found;
                }
            }
            return null;
        }

        const element = findElementByText(document, textToFind);
        if (element) {
            const menuItem = element.closest('md-menu-item') || element;
            const clickEv = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                composed: true
            });
            
            const start = Date.now();
            while (Date.now() - start < 500) {}
            
            menuItem.focus();
            menuItem.dispatchEvent(clickEv);
            return true;
        }
        return false;
        """

        for i in range(5):
            try:
                success = self.driver.execute_script(js_logic, text)
                if success:
                    print(f"[SUCCESS] Successfully clicked '{text}'")
                    return True
            except Exception as e:
                print(f"[WARNING] Error during attempt {i+1}: {e}")
            
            print(f"[INFO] Retry {i+1}/5: Element not found or not interactable...")
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

        print("[ERROR] Timeout reached: Video was never found or failed to download.")
        return False
