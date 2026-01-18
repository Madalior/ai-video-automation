import os
import time
import base64
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flowchart.common.browser_utils import start_browser, universal_shadow_click, get_new_email, get_otp

class DreaminaVideoGenerator:
    DREAMINA_URL = "https://auth.business.gemini.google/login?continueUrl=https://business.gemini.google/"
    
    def __init__(self, headless=False, profile_path=None):
        self.driver = start_browser(profile_path, headless)
        self.wait = WebDriverWait(self.driver, 30)

    def login(self, max_login_attempts=3):
        """Login with automatic retry on any error."""
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
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='fullName']"))).send_keys("User" + "".join(random.choices(string.ascii_letters, k=5)))
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

    def generate_video(self, prompt, reference_image_paths=None, output_path=None, max_retries=2):
        """
        Generate video with automatic retry if popup appears.
        
        Args:
            prompt: Video generation prompt
            reference_image_paths: Single path (str) OR list of up to 3 paths for multi-reference
            output_path: Where to save the video
            max_retries: Maximum number of retry attempts (default: 2)
        """
        # Convert single path to list for compatibility
        if reference_image_paths and isinstance(reference_image_paths, str):
            reference_image_paths = [reference_image_paths]
        
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
        print("[INFO] Searching for Start button and touch overlay...")
        
        # JavaScript logic that mirrors the working implementation from test file
        js_click_script = """
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

        // Synchronous sleep function
        function sleep(ms) {
            const start = Date.now();
            while (Date.now() - start < ms) {}
        }
        
        if (btn) {
            const touchArea = btn.querySelector('.touch');
            const labelArea = btn.querySelector('.label');
            if (touchArea) {
                sleep(500);
                touchArea.click();
                return "touch_clicked";
            } else if (labelArea) {
                sleep(500);
                labelArea.click();
                return "label_clicked";
            } else {
                sleep(500);
                btn.click();
                return "button_clicked";
            }
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
            const headline = item.querySelector('[slot="headline"]');
            if (headline && headline.textContent.toLowerCase().includes('video')) {
                ['mousedown', 'click', 'mouseup'].forEach(type => {
                    item.dispatchEvent(new MouseEvent(type, { 
                        bubbles: true, cancelable: true, view: window 
                    }));
                });
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
            
            # Wait for upload completion
            for i in range(15):
                print(f"[INFO] Uploading... {i+1}/15s")
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
        """Closes the browser instance."""
        try:
            if self.driver:
                self.driver.quit()
                print("[INFO] Browser closed.")
        except Exception as e:
            print(f"[WARNING] Error closing browser: {e}")


class MultiVeo3Generator:
    """
    Parallel Video Generator - Manages multiple DreaminaVideoGenerator workers.
    
    Features:
    - Multiple workers with unique Chrome profiles
    - Staggered start (10-second delay between workers)
    - Batch processing with progress tracking
    - Automatic result aggregation
    """
    
    def __init__(self, num_workers=4, headless=False):
        """
        Initialize parallel video generator.
        
        Args:
            num_workers: Number of parallel workers (default: 4)
            headless: Run browsers in headless mode (default: False)
        """
        self.num_workers = num_workers
        self.headless = headless
        print(f"[INFO] MultiVeo3Generator initialized with {num_workers} workers")
    
    def generate_batch(self, tasks):
        """
        Generate multiple videos in parallel.
        
        Args:
            tasks: List of dicts with 'prompt', 'reference_image_path', and 'output_path'
                   Example: [
                       {
                           'prompt': 'A cat walking',
                           'reference_image_path': 'images/cat.png',
                           'output_path': 'output/cat.mp4'
                       },
                       {
                           'prompt': 'A dog running',
                           'reference_image_path': 'images/dog.png',
                           'output_path': 'output/dog.mp4'
                       }
                   ]
        
        Returns:
            List of successful output paths
        """
        print(f"\n{'='*70}")
        print(f"  STARTING PARALLEL VIDEO GENERATION - {len(tasks)} TASKS")
        print(f"{'='*70}\n")
        
        results = []
        start_time = time.time()
        
        # Execute tasks in parallel with staggered start
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}
            
            for i, task in enumerate(tasks):
                # Add 10-second delay for each worker to prevent conflicts
                if i > 0:
                    print(f"\n   Waiting 10 seconds before starting Worker {i}...")
                    time.sleep(10)
                
                future = executor.submit(
                    self._generate_single_task,
                    i,  # worker_id
                    task['prompt'],
                    task.get('reference_image_path'),
                    task['output_path']
                )
                futures[future] = task
                print(f"   [STARTED] Worker {i} started")
            
            # Wait for completion
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"\n[FAIL] Task failed: {e}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Show results
        print(f"\n{'='*70}")
        print(f"  BATCH VIDEO GENERATION COMPLETE")
        print(f"{'='*70}\n")
        print(f"[RESULTS]:")
        print(f"   Total Tasks: {len(tasks)}")
        print(f"   Successful: {len(results)}")
        print(f"   Failed: {len(tasks) - len(results)}")
        print(f"   Duration: {int(duration)} seconds ({int(duration/60)} minutes)")
        
        if results:
            print(f"\n[SUCCESS] Generated Videos:")
            for path in results:
                if os.path.exists(path):
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    print(f"   [OK] {path} ({size_mb:.1f} MB)")
        
        return results
    
    def _generate_single_task(self, worker_id, prompt, reference_image_path, output_path):
        """
        Worker function for parallel execution.
        
        Args:
            worker_id: Unique worker identifier
            prompt: Video generation prompt
            reference_image_path: Path to reference image (optional)
            output_path: Where to save the video
            
        Returns:
            output_path if successful, None otherwise
        """
        print(f"\n[Worker {worker_id}] Starting...")
        print(f"[Worker {worker_id}] Prompt: {prompt[:80]}...")
        
        # Create generator with unique Chrome profile
        profile_path = os.path.abspath(f"chrome_data_video_{worker_id}")
        gen = DreaminaVideoGenerator(headless=self.headless, profile_path=profile_path)
        
        try:
            # Login
            print(f"[Worker {worker_id}] Logging in...")
            if not gen.login():
                print(f"[Worker {worker_id}] [FAIL] Login failed!")
                return None
            
            print(f"[Worker {worker_id}] [SUCCESS] Logged in")
            
            # Generate video
            print(f"[Worker {worker_id}] Generating video...")
            success = gen.generate_video(prompt, reference_image_path, output_path)
            
            if success:
                print(f"[Worker {worker_id}] [SUCCESS] Video saved: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"[Worker {worker_id}] [FAIL] Generation failed!")
                return None
                
        except Exception as e:
            print(f"[Worker {worker_id}] [ERROR] Error: {e}")
            return None
        finally:
            gen.close()



if __name__ == "__main__":
    import os
    print(">>> RUNNING PARALLEL VIDEO GENERATOR TEST - 4 WORKERS <<<")
    
    # Ensure output directory exists
    os.makedirs("output/tests", exist_ok=True)
    
    # Define 4 tasks with prompts and reference images
    tasks = [
        {
            'prompt': """A serene ASMR scene: gentle hands pouring colorful paint onto a canvas,
            slow motion, soft lighting, peaceful atmosphere, 8 seconds""",
            'reference_image_path': None,  # Optional
            'output_path': 'output/tests/test_video_worker_0.mp4'
        },
        {
            'prompt': """Close-up of soap cutting ASMR, satisfying texture, smooth slicing motion,
            pastel colors, soft natural lighting, 8 seconds""",
            'reference_image_path': None,  # Optional
            'output_path': 'output/tests/test_video_worker_1.mp4'
        },
        {
            'prompt': """Kinetic sand being slowly poured and shaped, mesmerizing ASMR texture,
            vibrant purple and pink colors, macro close-up, 8 seconds""",
            'reference_image_path': None,  # Optional
            'output_path': 'output/tests/test_video_worker_2.mp4'
        },
        {
            'prompt': """Slime stretching and folding ASMR, glossy translucent texture with glitter,
            satisfying slow motion, soft pastel background, 8 seconds""",
            'reference_image_path': None,  # Optional
            'output_path': 'output/tests/test_video_worker_3.mp4'
        }
    ]
    
    # Use MultiVeo3Generator for parallel processing
    generator = MultiVeo3Generator(num_workers=4, headless=False)
    results = generator.generate_batch(tasks)
    
    # Show results
    if len(results) == len(tasks):
        print("\n[SUCCESS] All videos generated successfully!")
    else:
        print(f"\n[PARTIAL] {len(results)}/{len(tasks)} videos generated.")

