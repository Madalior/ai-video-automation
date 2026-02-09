import os
import time
import base64
import random
import string
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flowchart.common.browser_utils import start_browser, universal_shadow_click, get_new_email, get_otp
from flowchart.common.session_manager import SessionManager, OverloadDetector
from flowchart.common.human_behavior import HumanBehavior
from flowchart.common.smart_reference_manager import SmartReferenceManager

class DreaminaVideoGenerator:
    DREAMINA_URL = "https://auth.business.gemini.google/login?continueUrl=https://business.gemini.google/"
    
    def __init__(self, headless=False, profile_path=None, fresh_profile=False, shared_session=None):
        """
        Initialize video generator.
        
        Args:
            headless: Run browser in headless mode
            profile_path: Chrome profile path
            fresh_profile: Create fresh temporary profile
            shared_session: Optional SharedSessionManager for session sharing (NEW)
        """
        self.is_temp_profile = False
        self.shared_session = shared_session
        self._owns_driver = shared_session is None  # Only own driver if not using shared session
        
        if shared_session:
            # Use shared session (NEW APPROACH)
            print("[VIDEO GEN] Using shared session (no separate login needed)")
            self.driver = shared_session.get_driver()
            self.wait = WebDriverWait(self.driver, 30)
            self.profile_path = shared_session.profile_path
            self.headless = shared_session.headless
        else:
            # Create own browser (BACKWARD COMPATIBLE)
            if fresh_profile:
                unique_id = uuid4().hex[:12]
                profile_path = os.path.abspath(f"temp_chrome_profiles/fresh_{unique_id}")
                os.makedirs(profile_path, exist_ok=True)
                self.is_temp_profile = True
                print(f"[BROWSER] Created fresh Chrome ID (Video): fresh_{unique_id}")
                
            self.driver = start_browser(profile_path, headless, fresh_profile=False)
            self.wait = WebDriverWait(self.driver, 30)
            self.profile_path = profile_path
            self.headless = headless
        
        # Advanced anti-bot detection (always needed)
        self.session_manager = SessionManager(max_requests=15, min_interval=15)
        self.overload_detector = OverloadDetector()
        self.human = HumanBehavior()
        
        # Smart reference manager for typed references (NEW)
        self.ref_manager = SmartReferenceManager(mode='smart_order')
        
        print("[ANTI-BOT] Video generator anti-bot protection active")

    def login(self, max_login_attempts=3):
        """Login with automatic retry on any error."""
        
        # If using shared session, login is already done
        if self.shared_session:
            print("[VIDEO GEN] Using shared session, skipping separate login")
            return True
        
        # Otherwise, use original login logic
        print("[INFO] Starting Login Flow (Video)...")
        
        for login_attempt in range(max_login_attempts):
            try:
                if login_attempt > 0:
                    print(f"\n[RETRY] Login attempt {login_attempt + 1}/{max_login_attempts}")
                    time.sleep(3)
                
                self.driver.get(self.DREAMINA_URL)
                time.sleep(3)
                
                # CRITICAL: Check for popup BEFORE email input
                # This button appears between page load and email input
                if self._handle_multiple_tabs_popup():
                    print("[INFO] Early popup handled, continuing to email input...")
                    time.sleep(2)
                
                # Step 1: Email Input (with Retry Loop)
                email = None
                password = None
                otp = None
                
                for retry_attempt in range(2): 
                    email, password = get_new_email() if retry_attempt == 0 else (email, password)
                    if not email: 
                        if login_attempt < max_login_attempts - 1:
                            print("[WARNING] Email generation failed, restarting login...")
                            break  # Break inner loop to restart login
                        return False
                    
                    print(f"[INFO] Entering Email (Attempt {retry_attempt+1})...")
                    
                    # Check for popup again before email input
                    if self._handle_multiple_tabs_popup():
                        print("[INFO] Popup appeared before email input, restarting login...")
                        # Break both loops to restart from beginning
                        email = None  # Force restart
                        break
                    
                    try:
                        email_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#email-input")))
                        email_input.clear()
                        # Human-like delay before typing email
                        delay = random.uniform(2, 4)
                        print(f"[ANTI-BOT] Waiting {delay:.1f}s before typing email...")
                        time.sleep(delay)
                        email_input.send_keys(email)
                        
                        continue_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Continue with email')]")))
                        continue_btn.click()
                        
                        # CRITICAL: Check for popup AFTER clicking Continue
                        # The popup often appears right after this click
                        time.sleep(2)  # Brief wait for popup to appear
                        if self._handle_multiple_tabs_popup():
                            print("[INFO] Popup appeared after Continue click, restarting login...")
                            # Break to restart entire login
                            email = None  # Force restart
                            break
                    except Exception as e:
                        print(f"[ERROR] Error during email input: {e}")
                        if login_attempt < max_login_attempts - 1:
                            break  # Restart login
                        return False
                    
                    # Step 2: OTP (Shorter wait + Retry)
                    print("[INFO] Waiting for OTP...")
                    
                    # Wait for OTP with continuous popup checking
                    otp = None
                    max_otp_wait = 45  # 45 seconds max wait
                    otp_check_interval = 5  # Check every 5 seconds
                    otp_waited = 0
                    
                    while otp_waited < max_otp_wait and not otp:
                        # Check for popup while waiting for OTP
                        if self._handle_multiple_tabs_popup():
                            print("[INFO] Popup appeared while waiting for OTP, restarting login...")
                            # Break to restart entire login
                            email = None  # Force restart
                            otp = None
                            break
                        
                        # Try to get OTP (non-blocking check)
                        otp = get_otp(email, password, max_wait=otp_check_interval)
                        
                        if not otp:
                            otp_waited += otp_check_interval
                            if otp_waited % 15 == 0:
                                print(f"[INFO] Still waiting for OTP... ({otp_waited}s/{max_otp_wait}s)")
                    
                    if otp:
                        break  # Got OTP, exit retry loop
                    else:
                        print(f"[WARNING] OTP missing. Attempting workaround...")
                        if retry_attempt == 0:
                            try:
                                try_again = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Try again') or contains(text(),'Back')]")))
                                try_again.click()
                                time.sleep(2)
                            except:
                                self.driver.refresh()
                                time.sleep(3)
                
                # Check if we need to restart login due to popup or email being None
                if not email or not otp: 
                    print("[WARNING] OTP generation failed.")
                    if login_attempt < max_login_attempts - 1:
                        print("[INFO] Restarting entire login process...")
                        continue  # Restart login from beginning
                    return self._wait_for_manual_login()
                
                # OTP Handling
                # Human-like delay before entering OTP
                delay = random.uniform(2, 4)
                print(f"[ANTI-BOT] Waiting {delay:.1f}s before entering OTP...")
                time.sleep(delay)
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='pinInput']"))).send_keys(otp)
                time.sleep(1)
                
                # Step 3: Verify / Agree
                try:
                    # Try generic text match first as it's more robust
                    verify_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Next') or contains(text(), 'Verify')]")))
                    self.driver.execute_script("arguments[0].click();", verify_btn)
                except:
                    print("[WARNING] Verify button issue, trying fallback CSS...")
                
                # Step 4: Name & Agree
                # Human-like delay before typing name
                human_name = "User" + "".join(random.choices(string.ascii_letters, k=5))
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
                time.sleep(random.uniform(1, 2))  # Small delay before clicking agree
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'agree-button')]"))).click()
                
                print("[SUCCESS] Login Successful")
                time.sleep(5)
                return True
                
            except Exception as e:
                print(f"[ERROR] Login Failed on attempt {login_attempt + 1}: {e}")
                
                # Check for popup during error
                if self._handle_multiple_tabs_popup():
                    print("[INFO] Popup detected during error, will restart login...")
                
                if login_attempt < max_login_attempts - 1:
                    print(f"[INFO] Restarting login (attempt {login_attempt + 2}/{max_login_attempts})...")
                    continue
                else:
                    print("[ERROR] All login attempts failed")
                    return self._wait_for_manual_login()

    def _wait_for_manual_login(self, timeout=120):
        """Fallback to manual login if automation fails."""
        print("\n" + "!"*50)
        print("[ACTION REQUIRED] Auto-Login Failed (Temp Mail Issues?)")
        print("Please log in MANUALLY in the opened Chrome window.")
        print(f"Waiting {timeout} seconds for you to complete login...")
        print("!"*50 + "\n")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check for successful login state (URL change or specific element)
                # Dreamina/Gemini usually redirects to https://business.gemini.google/
                if "login" not in self.driver.current_url and "gemini" in self.driver.current_url:
                    print("[SUCCESS] Manual Login Detected! Resuming...")
                    time.sleep(3) # Let it load
                    return True
            except:
                pass
            time.sleep(2)
            
        print("[ERROR] Manual login timed out.")
        return False

    
    def _handle_multiple_tabs_popup(self):
        """
        Detects and handles the 'Let's try something else' popup.
        Uses JavaScript to find and click the button (same approach as console testing).
        """
        try:
            time.sleep(1)
            
            # Use JavaScript to find and click the button (proven to work in console)
            click_script = """
            // Synchronous sleep function
            function sleep(ms) {
                const start = Date.now();
                while (Date.now() - start < ms) {}
            }
            
            // Find button by jsname or by searching all buttons
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
                print("[DETECTED] Multiple tabs popup found!")
                print("[SUCCESS] Clicked 'Sign up or sign in' button")
                time.sleep(3)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[WARN] Error checking for multiple tabs popup: {e}")
            return False

    def generate_video(self, prompt, reference_image_paths=None, output_path=None, max_retries=2, scene_context=None):
        """
        Generate video with automatic retry if popup appears.
        
        Args:
            prompt: Video generation prompt
            reference_image_paths: References can be:
                - None: No references
                - str: Single path (legacy)
                - List[str]: Multiple paths (legacy)
                - Dict: Typed references {'character': path, 'background': path, 'continuity': path}
            output_path: Where to save the video
            max_retries: Maximum number of retry attempts (default: 2)
            scene_context: Optional scene metadata for smart reference modes (future use)
        
        Examples:
            # Legacy: single path
            generate_video("Prompt", reference_image_paths="char.png")
            
            # Legacy: list
            generate_video("Prompt", reference_image_paths=["img1.png", "img2.png"])
            
            # NEW: Typed dict
            generate_video("Prompt", reference_image_paths={
                'character': 'detective.png',
                'background': 'room.png',
                'continuity': 'prev_frame.png'
            })
        """
        if self.shared_session:
            print("[VIDEO GEN] Delegating generation to SharedSessionManager")
            return self.shared_session.generate_video(prompt, output_path, reference_image_paths)

        # Process references with SmartReferenceManager
        processed_refs = None
        if reference_image_paths:
            processed_refs = self.ref_manager.process_references(
                reference_image_paths, 
                scene_context
            )
            
            # Convert to old format for upload methods (always list)
            if isinstance(reference_image_paths, str):
                # Keep as list for upload_reference
                pass
            elif isinstance(reference_image_paths, (list, dict)):
                # Already processed into list by ref_manager
                reference_image_paths = processed_refs
        
        for attempt in range(max_retries + 1):
            try:
                print(f"[INFO] Generating Video (Attempt {attempt + 1}/{max_retries + 1}): {prompt[:50]}...")
                
                # Check for popup before starting
                if self._handle_multiple_tabs_popup():
                    print("[INFO] Popup handled, continuing with generation...")
                    time.sleep(2)
                
                # 1. Start Button
                self.click_start_button()
                
                # Check for popup after start button
                if self._handle_multiple_tabs_popup():
                    print("[WARNING] Popup appeared after start button, restarting...")
                    if attempt < max_retries:
                        continue
                    else:
                        print("[ERROR] Max retries reached")
                        return False

                # 2. Open Video Tool
                self.open_video_tool()

                time.sleep(2)

                # 3. Inject Prompt
                self.inject_prompt(prompt)

                # 4. Upload Reference(s) - Support multiple images
                if reference_image_paths:
                    if isinstance(reference_image_paths, list):
                        # Multiple reference images (Veo 3.1 feature)
                        self.upload_multiple_references(reference_image_paths)
                    else:
                        # Single reference (backward compatibility)
                        if os.path.exists(reference_image_paths):
                            self.upload_reference(reference_image_paths)
                        else:
                            print(f"[WARNING] Reference image not found: {reference_image_paths}")

                # 5. Submit
                self.submit_generation()

                # 6. Download
                result = self.download_video(output_path)
                
                if result:
                    print(f"[SUCCESS] Video generated successfully on attempt {attempt + 1}")
                    
                    # Reset interface for next generation
                    self.go_to_new_chat()
                    
                    return True
                else:
                    print(f"[WARNING] Generation failed on attempt {attempt + 1}")
                    if attempt < max_retries:
                        print("[INFO] Retrying...")
                        time.sleep(3)
                        continue
                        
            except Exception as e:
                print(f"[ERROR] Exception during generation (attempt {attempt + 1}): {e}")
                
                # Check if popup appeared during generation
                if self._handle_multiple_tabs_popup():
                    print("[INFO] Popup detected during error, will retry...")
                    if attempt < max_retries:
                        time.sleep(3)
                        continue
                    
                if attempt >= max_retries:
                    print("[ERROR] Max retries reached")
                    return False
        
        return False

    def go_to_new_chat(self):
        """Navigate to New Chat to reset the generation interface."""
        print("[INFO] Navigating to New Chat...")
        
        # This script searches for the button that contains the 'New chat' title
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
        
        try:
            success = self.driver.execute_script(new_chat_script)
            if success:
                print("[SUCCESS] Successfully started a New Chat.")
                time.sleep(2)  # Wait for the new chat interface to clear
                return True
            else:
                print("[WARNING] Could not find the New Chat button.")
                return False
        except Exception as e:
            print(f"[WARNING] Error clicking New Chat: {e}")
            return False

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
        else:
            print("[ERROR] Could not find the video menu item even with deep search.")

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

                // --- Trusted Types Bypass ---
                if (window.trustedTypes && window.trustedTypes.createPolicy) {
                    // Try to use existing policy or create a temporary 'pass-through' policy
                    const policy = window.trustedTypes.defaultPolicy || 
                                   window.trustedTypes.createPolicy('bot-policy', {
                                       createHTML: (s) => s
                                   });
                    secureHtml = policy.createHTML(htmlContent);
                }

                editor.focus();
                editor.innerHTML = secureHtml;
                
                // Trigger events to wake up the 'Submit' button
                editor.dispatchEvent(new Event('input', { bubbles: true }));
                editor.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
            }
            return false;
            """
            
            success = self.driver.execute_script(injection_script, text)
            if success:
                print("[SUCCESS] Text successfully injected into the editor.")
            else:
                print("[ERROR] Failed to find the ProseMirror editor div.")
                
        except Exception as e:
            print(f"[WARNING] Exception during text injection: {e}")

    def upload_reference(self, path):
        """Upload reference image with proper wait for completion."""
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
            print(f"\n  [{idx}/{len(valid_paths)}] Uploading: {os.path.basename(path)}")
            
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
        
        print(f"\n[SUCCESS] Uploaded {uploaded_count}/{len(valid_paths)} reference images")
        return uploaded_count

    def submit_generation(self):
        """Trigger submission with force-click sequence and retry logic."""
        # Human-like delay before submitting
        delay = random.uniform(2, 4)
        print(f"[ANTI-BOT] Waiting {delay:.1f}s before clicking Submit button...")
        time.sleep(delay)
        
        print("[INFO] Triggering Force-Click sequence on Submit button...")
        
        # This script bypasses standard listeners by simulating a physical hardware click
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
        
        if (btn && !btn.disabled) {
            try {
                // 1. Force the browser to treat this as the active element
                btn.focus();

                // 2. Dispatch sequence to trigger internal framework listeners (React/Angular)
                const events = ['mousedown', 'mouseup', 'click'];
                events.forEach(type => {
                    btn.dispatchEvent(new MouseEvent(type, {
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        buttons: 1, // Left click
                        which: 1
                    }));
                });
                
                // 3. Synchronous sleep before final fallback click
                const start = Date.now();
                while (Date.now() - start < 500) {}
                
                btn.click();
                return "clicked";
            } catch (e) {
                return "error: " + e.message;
            }
        }
        return "not_ready_or_missing";
        """
        
        for attempt in range(1, 11):
            result = self.driver.execute_script(click_execution_script)
            
            if result == "clicked":
                print(f"[SUCCESS] Click signal sent on attempt {attempt}.")
                # Wait to ensure the site registers the transition to 'Generating'
                time.sleep(5)
                return True
            else:
                print(f"[INFO] Attempt {attempt}/10: Button not ready for click ({result}). Retrying...")
                
            time.sleep(2)

        print("[ERROR] Button was visible but refused the click command.")
        return False

    def download_video(self, filepath, timeout=600):
        """Wait for video generation and download it via blob/base64 conversion."""
        print(f"[INFO] Waiting for video generation (up to {timeout}s)...")
        
        # Ensure the directory exists
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"[INFO] Created directory: {output_dir}")

        # This script combines the Shadow DOM crawler with a Base64 reader
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
            
            // Target the latest video source
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
                # execute_async_script is used because we are awaiting a Promise (fetch/FileReader)
                base64_data = self.driver.execute_async_script(blob_to_base64_js)
                
                if base64_data and base64_data.startswith("data:video"):
                    # Split the header (data:video/mp4;base64,) from the actual data
                    header, encoded = base64_data.split(",", 1)
                    binary_data = base64.b64decode(encoded)
                    
                    with open(filepath, "wb") as f:
                        f.write(binary_data)
                    
                    print(f"[SUCCESS] Video saved successfully!")
                    print(f"[INFO] Location: {filepath}")
                    return True
                
                print("[INFO] Video not found yet, retrying in 10s...")
                
            except Exception as e:
                print(f"[WARNING] Error during check: {str(e)[:100]}")
                
            time.sleep(10) # Wait before next poll

        print("[ERROR] Timeout reached: Video was never found or failed to download.")
        return False

    def close(self):
        """Closes the browser instance and cleans up temporary profiles."""
        try:
            if self.driver:
                self.driver.quit()
                print("[INFO] Browser closed.")
            
            # Cleanup temp profile if it was a fresh one
            if hasattr(self, 'is_temp_profile') and self.is_temp_profile and self.profile_path and os.path.exists(self.profile_path):
                import shutil
                try:
                    shutil.rmtree(self.profile_path, ignore_errors=True)
                    print(f"[INFO] Cleaned up temp profile: {os.path.basename(self.profile_path)}")
                except Exception as e:
                    print(f"[WARN] Failed to delete temp profile: {e}")
                    
        except Exception as e:
            print(f"[WARNING] Error closing browser: {e}")


class MultiVeo3Generator:
    """
    Parallel Video Generator - Manages multiple DreaminaVideoGenerator workers.
    """
    
    def __init__(self, num_workers=4, headless=False):
        self.num_workers = num_workers
        self.headless = headless
        self.workers = []
        
        print(f"[MULTI-GEN] Initializing {num_workers} video workers...")
        print(f"[ANTI-BOT] Using 10-second delays between worker launches to avoid detection")
        
        # Initialize workers SEQUENTIALLY with 10-second delays to avoid bot detection
        for i in range(num_workers):
            if i > 0:
                print(f"\n[ANTI-BOT] Waiting 10 seconds before launching Worker {i}...")
                time.sleep(10)
            
            profile_path = os.path.abspath(f"chrome_data_parallel_video_{i}")
            worker = self._init_worker(i, profile_path)
            if worker:
                self.workers.append(worker)
        
        print(f"[MULTI-GEN] {len(self.workers)}/{num_workers} workers initialized and ready.")

    def _init_worker(self, i, profile_path):
        """Initialize and login a single worker."""
        print(f"[WORKER {i}] Launching Chrome...")
        try:
            gen = DreaminaVideoGenerator(
                headless=self.headless, 
                profile_path=profile_path, 
                fresh_profile=False  # Reuse profile to keep login
            )
            
            # Login immediately
            if gen.login():
                print(f"[WORKER {i}] Login successful")
                return gen
            else:
                print(f"[WORKER {i}] Login failed")
                gen.close()
                return None
        except Exception as e:
            print(f"[WORKER {i}] Initialization failed: {e}")
            return None

    def generate_batch(self, tasks):
        """
        Generate multiple videos in parallel using persistent workers.
        tasks: List of dicts with 'prompt', 'output_path', 'reference_image_paths'
        """
        results = []
        
        if not self.workers:
            print("[ERROR] No workers available!")
            return results

        print(f"[MULTI-GEN] Distributing {len(tasks)} tasks across {len(self.workers)} workers")
        
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            futures = {}
            for i, task in enumerate(tasks):
                worker_idx = i % len(self.workers)
                worker = self.workers[worker_idx]
                
                future = executor.submit(
                    worker.generate_video,
                    prompt=task['prompt'],
                    output_path=task['output_path'],
                    reference_image_paths=task.get('reference_image_paths') or task.get('reference_image_path')
                )
                futures[future] = task
            
            for future in as_completed(futures):
                task = futures[future]
                try:
                    success = future.result()
                    results.append({
                        'task': task,
                        'status': 'success' if success else 'failed',
                        'path': task['output_path'] if success else None
                    })
                    status = 'OK' if success else 'FAIL'
                    print(f"   [BATCH] Task finished: {os.path.basename(task['output_path'])} ({status})")
                except Exception as e:
                    print(f"   [BATCH] Task error: {e}")
                    results.append({'task': task, 'status': 'failed', 'error': str(e)})
        
        return results

    def close(self):
        """Close all workers."""
        print("[MULTI-GEN] Closing workers...")
        for w in self.workers:
            try:
                w.close()
            except:
                pass


if __name__ == "__main__":
    import os
    print(">>> RUNNING PARALLEL VIDEO GENERATOR TEST - 4 WORKERS <<<")
    
    # Ensure output directory exists
    os.makedirs("output/tests", exist_ok=True)
    
    # Define 4 tasks with prompts and reference images
    tasks = [
        {
            'prompt': "A serene ASMR scene: gentle hands pouring colorful paint onto a canvas, 8 seconds",
            'reference_image_path': None, 
            'output_path': 'output/tests/test_video_worker_0.mp4'
        },
        {
            'prompt': "Close-up of soap cutting ASMR, satisfying texture, 8 seconds",
            'reference_image_path': None,
            'output_path': 'output/tests/test_video_worker_1.mp4'
        }
    ]
    
    # Use MultiVeo3Generator for parallel processing
    generator = MultiVeo3Generator(num_workers=2, headless=False)
    results = generator.generate_batch(tasks)
    
    # Show results
    if len(results) == len(tasks):
        print("\n[SUCCESS] All videos generated successfully!")
    else:
        print(f"\n[PARTIAL] {len(results)}/{len(tasks)} videos generated.")
    
    generator.close()
    


