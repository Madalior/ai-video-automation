import time
import os
import random
import string
import requests
import re
from uuid import uuid4

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dreamina_capcut_image import start_browser


# ================= CONFIG =================
DREAMINA_URL = "https://auth.business.gemini.google/login?continueUrl=https://business.gemini.google/"
TEST_SCRIPT = "A wide-angle landscape photograph of an ancient castle built into a cliffside overlooking the ocean. Stormy clouds, dramatic lighting, cinematic, Lord of the Rings style, 8k resolution."
REFERENCE_IMAGE = "output/images/backgrounds/scene_1.png"
DOWNLOAD_DIR = "output/videos"

BASE = "https://api.mail.tm"

import json

def universal_shadow_click(driver, selector):
    """Clicks any element, safely handling quotes and nested Shadow DOMs."""
    # Convert the python string to a safe JS string (handles ' and " automatically)
    safe_selector = json.dumps(selector)
    
    script = f"""
    function findInShadow(root, selector) {{
        let el = root.querySelector(selector);
        if (el) return el;
        const hosts = root.querySelectorAll('*');
        for (const host of hosts) {{
            if (host.shadowRoot) {{
                const found = findInShadow(host.shadowRoot, selector);
                if (found) return found;
            }}
        }}
        return null;
    }}
    const target = findInShadow(document, {safe_selector});
    if (target) {{ 
        ['mousedown', 'click', 'mouseup'].forEach(type => {{
            target.dispatchEvent(new MouseEvent(type, {{ bubbles: true, view: window }}));
        }});
        return true; 
    }}
    return false;
    """
    return driver.execute_script(script)


# ================= TEMP MAIL (INTEGRATED) =================
def get_new_email():
    print("📧 Creating new temporary email...")

    domains = requests.get(BASE + "/domains").json()
    domain = domains["hydra:member"][0]["domain"]

    email = f"{uuid4().hex[:8]}@{domain}"
    password = uuid4().hex

    requests.post(BASE + "/accounts", json={"address": email, "password": password})

    print(f"📨 New Email: {email}")
    return email, password


def get_token(email, password):
    r = requests.post(BASE + "/token", json={"address": email, "password": password}).json()
    return r["token"]


def get_otp(email, password):
    print("📩 Waiting for OTP...")

    token = get_token(email, password)
    headers = {"Authorization": f"Bearer {token}"}

    max_wait_seconds = 120
    check_interval = 3
    waited = 0

    while waited < max_wait_seconds:
        messages = requests.get(BASE + "/messages", headers=headers).json()

        if messages.get("hydra:totalItems", 0) > 0:
            msg_id = messages["hydra:member"][0]["id"]
            msg = requests.get(
                BASE + "/messages/" + msg_id,
                headers=headers
            ).json()

            text_part = msg.get("text", "")

            html_part = msg.get("html", [])
            if isinstance(html_part, list):
                html_part = " ".join(html_part)

            text = text_part + " " + html_part

            # ✅ Robust OTP extraction
            match = re.search(r"\b[A-Z0-9]{6}\b", text)

            if match:
                otp = match.group(0)
                print("🔐 OTP Received:", otp)
                return otp

        print("⏳ OTP not received yet... checking again...")
        time.sleep(check_interval)
        waited += check_interval

    raise TimeoutError("❌ OTP not received within time limit")


# ================= UTILS =================
def random_name():
    return "User" + "".join(random.choices(string.ascii_letters, k=5))


# ================= STEP 1 =================
def open_dreamina(driver):
    driver.get(DREAMINA_URL)
    time.sleep(5)


# ================= STEP 3 =================
def enter_email(driver, email):
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "email-input"))
    ).send_keys(email)


# ================= STEP 4 =================
def continue_with_email(driver):
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(),'Continue with email')]")
        )
    ).click()


# ================= STEP 6 =================
def enter_otp(driver, otp):
    print(f"📩 Entering OTP: {otp}")
    print("⏳ Waiting 2.0s before entering OTP...")
    time.sleep(2.0)

    hidden = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='pinInput']"))
    )
    hidden.clear()
    hidden.send_keys(otp)
    
    # Trigger events manually to ensure state update
    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true })); arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", hidden)
    print("✅ OTP typed and triggered events.")

# ================= STEP 6A =================
# ================= STEP 6A =================
def click_verify(driver):
    print("⏳ Waiting 3.0s before verify click...")
    time.sleep(3.0)
    print("✅ Clicking Verify button...")
    
    # Use a generic wait for presence, not clickable (since clickable checks for obstruction)
    wait = WebDriverWait(driver, 10)
    
    # Option 1: Stick to your current selector but force the click
    try:
        button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".YUhpIc-RLmnJb"))
        )
        driver.execute_script("arguments[0].click();", button)
        print("🖱️ Clicked using JavaScript execution")
        
    except Exception as e:
        print(f"⚠️ CSS Selector failed, trying generic XPath text match: {e}")
        # Option 2: Fallback to finding the button by text content (More robust against class changes)
        button = wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Next') or contains(text(), 'Verify')]"))
        )
        driver.execute_script("arguments[0].click();", button)


# ================= STEP 7–8 =================
def enter_name_and_agree(driver):
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@formcontrolname='fullName']")
        )
    ).send_keys(random_name())

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@class,'agree-button')]")
        )
    ).click()

# ================= STEP 9 =================
def wait_for_dashboard(driver):
    print("⏳ Waiting for dashboard to load...")
    # Explicit wait to let animations/overlays finish
    time.sleep(5) 

# ================= STEP 10 (REVISED) =================
import time

def click_start_button(driver):
    print("🎯 Searching for Start button and touch overlay...")
    
    # JavaScript logic that mirrors what worked in your console
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

    if (btn) {
        const touchArea = btn.querySelector('.touch');
        const labelArea = btn.querySelector('.label');
        if (touchArea) {
            touchArea.click();
            return "touch_clicked";
        } else if (labelArea) {
            labelArea.click();
            return "label_clicked";
        } else {
            btn.click();
            return "button_clicked";
        }
    }
    return null;
    """

    for i in range(10):  # 10 Retries
        try:
            # Execute the working JS logic directly in the browser
            result = driver.execute_script(js_click_script)
            
            if result:
                print(f"✅ Success: {result} performed.")
                return True
                
            print(f"⏳ Retry {i+1}/10: Button/Touch area not found yet...")
        except Exception as e:
            print(f"⚠️ Error during click attempt: {e}")
            
        time.sleep(2)

    print("❌ Could not click the button after 10 retries.")
    driver.save_screenshot("debug_final_attempt.png")
    return False
# ================= STEP 10–12 (REVISED) =================

def click_menu_item_by_text(driver, target_text="Create images (Pro)"):
    print(f"🔍 Searching for menu item: '{target_text}'...")

    # This JS script handles Shadow DOM, Slots, and Composed Events
    js_logic = """
    const textToFind = arguments[0];
    
    function findElementByText(root, text) {
        // Search text nodes
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes(text)) {
                return node.parentElement;
            }
        }
        // Recursively search shadow roots
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
        // Find the actual md-menu-item parent
        const menuItem = element.closest('md-menu-item') || element;
        
        // Trigger a 'composed' click that travels through Shadow DOM
        const clickEv = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            composed: true
        });
        
        menuItem.focus();
        menuItem.dispatchEvent(clickEv);
        return true;
    }
    return false;
    """

    for i in range(5):  # 5 Retries
        try:
            success = driver.execute_script(js_logic, target_text)
            if success:
                print(f"✅ Successfully clicked '{target_text}'")
                return True
        except Exception as e:
            print(f"⚠️ Error during attempt {i+1}: {e}")
        
        print(f"⏳ Retry {i+1}/5: Element not found or not interactable...")
        time.sleep(2)

    print(f"❌ Failed to find and click '{target_text}' after retries.")
    return False

# --- Example Usage ---
# click_menu_item_by_text(driver, "Create images (Pro)")
# ================= STEP 13 =================
def paste_video_script(driver, text):
    print(f"✍️ Injecting script text with TrustedHTML bypass: {text}")
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
        
        success = driver.execute_script(injection_script, text)
        if success:
            print("✅ Text successfully injected into the editor.")
        else:
            print("❌ Failed to find the ProseMirror editor div.")
            
    except Exception as e:
        print(f"⚠️ Exception during text injection: {e}")
# ================= STEP 14–15 =================
# ================= STEP 14–15 (UPLOAD) =================
def upload_reference_image(driver):
    print("📂 Uploading reference image...")
    # Click Add button
    universal_shadow_click(driver, "md-icon[text='add']")
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
    driver.execute_script(upload_item_script)
    time.sleep(1)

    # Send file to hidden input
    file_path = os.path.abspath(REFERENCE_IMAGE)
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
    file_input = driver.execute_script(file_input_script)
    if file_input:
        file_input.send_keys(file_path)
        print("📤 File path sent. Waiting for upload to finish...")
        
        # --- NEW: WAIT FOR UPLOAD COMPLETION ---
        # We wait 10-15 seconds here or check for the disappearance of a loading spinner
        for i in range(15):
            print(f"⏳ Uploading... {i+1}/15s")
            time.sleep(1)
        print("✅ Assuming upload finished.")
# ================= SUBMIT =================
import time

def submit_video(driver):
    print("🚀 Triggering Force-Click sequence on READY button...")
    
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
            
            // 3. Final fallback click
            btn.click();
            return "clicked";
        } catch (e) {
            return "error: " + e.message;
        }
    }
    return "not_ready_or_missing";
    """

    for attempt in range(1, 11):
        result = driver.execute_script(click_execution_script)
        
        if result == "clicked":
            print(f"✅ SUCCESS: Click signal sent on attempt {attempt}.")
            # Wait to ensure the site registers the transition to 'Generating'
            time.sleep(5) 
            return True
        else:
            print(f"⏳ Attempt {attempt}/10: Button not ready for click ({result}). Retrying...")
            
        time.sleep(2)

    print("❌ FAILED: Button was visible but refused the click command.")
    return False

# ================= DOWNLOAD =================
import base64

import os
import base64
import time

# Target directory
DOWNLOAD_DIR = r"C:\Users\vijay\OneDrive\Pictures\automation-bot\output\videos"

import os
import time

# Configuration
SAVE_PATH = r"C:\Users\vijay\OneDrive\Pictures\automation-bot\output\images"
TARGET_MENU_TEXT = "Create images (Pro)"

def generate_and_save_image(driver, timeout=120):
    """
    Clicks the generation button, waits for the image to render, and saves it.
    """
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH, exist_ok=True)

    # --- STEP 1: TRIGGER GENERATION ---
    print(f"🚀 Triggering: {TARGET_MENU_TEXT}...")
    
    click_js = """
    const findByText = (root, text) => {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes(text)) return node.parentElement;
        }
        const hosts = root.querySelectorAll('*');
        for (const host of hosts) {
            if (host.shadowRoot) {
                const found = findByText(host.shadowRoot, text);
                if (found) return found;
            }
        }
        return null;
    };
    const el = findByText(document, arguments[0]);
    if (el) {
        const menu = el.closest('md-menu-item') || el;
        menu.dispatchEvent(new MouseEvent('click', {bubbles: true, composed: true}));
        return true;
    }
    return false;
    """
    
    triggered = driver.execute_script(click_js, TARGET_MENU_TEXT)
    if not triggered:
        print("❌ Could not find the generation button.")
        return False

    # --- STEP 2: WAIT AND CAPTURE ---
    print(f"⏳ Waiting for AI to generate image (up to {timeout}s)...")
    
    find_img_js = """
    function findLargeImg(root) {
        // Look for images larger than 300px (ignores icons)
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
            image_element = driver.execute_script(find_img_js)
            
            if image_element:
                # Give it an extra second to finish the "fade-in" animation
                time.sleep(2) 
                
                filename = f"ai_result_{int(time.time())}.png"
                full_path = os.path.join(SAVE_PATH, filename)
                
                # Take screenshot of the specific element
                image_element.screenshot(full_path)
                
                print(f"✅ Image generated and saved: {full_path}")
                return True
                
        except Exception as e:
            # If the element is found but not yet ready to screenshot
            pass
            
        print("⏳ Still generating...")
        time.sleep(5)  # Poll every 5 seconds

    print("❌ Timeout: Image did not appear in time.")
    return False

# --- Usage ---
# generate_and_save_image(driver)

# --- To Run ---
# wait_and_download_video(driver)
def go_to_new_chat(driver):
    print("🆕 Navigating to New Chat...")
    
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
        success = driver.execute_script(new_chat_script)
        if success:
            print("✅ Successfully started a New Chat.")
            time.sleep(2) # Wait for the new chat interface to clear
        else:
            print("❌ Could not find the New Chat button.")
    except Exception as e:
        print(f"⚠️ Error clicking New Chat: {e}")


def run_automation_loop(driver):
    while True:
        try:
            print("\n🔄 --- Starting New Generation Cycle ---")

            # STEP 1: RESET STATE (New Chat)
            # This ensures a clean workspace for every run
            if not go_to_new_chat(driver):
                print("⚠️ New Chat navigation failed, attempting to proceed...")

            # STEP 2: START/CREATE BUTTON
            # Re-initialize the generation dashboard
            click_start_button(driver)

            # STEP 3: OPEN VIDEO TOOL
            # Access the 'Generate a video' menu
            click_menu_item_by_text(driver)

            # STEP 4: PASTE SCRIPT
            # Inject your prompt into the editor
            paste_video_script(driver, TEST_SCRIPT)

            # STEP 5: UPLOAD IMAGE
            # Provide the reference image
            upload_reference_image(driver)

            # STEP 6: SUBMIT
            # Trigger the generation process
            submit_video(driver)

            # STEP 7: WAIT & DOWNLOAD
            # Monitor browser memory for the resulting Blob and save it
            if generate_and_save_image(driver, timeout=120):
                print("✅ Cycle successful. Preparing next run...")
            else:
                print("❌ Generation or download timed out. Stopping loop.")
                break

            # Small cooldown between cycles
            time.sleep(5)

        except Exception as e:
            print(f"🛑 Critical error in automation loop: {e}")
            driver.save_screenshot("critical_loop_error.png")
            break

# ================= MAIN =================
def test_video_full_flow():
    driver = start_browser()
    try:
        open_dreamina(driver)

        # Login Flow
        email, password = get_new_email()
        enter_email(driver, email)
        continue_with_email(driver)

        otp = get_otp(email, password)
        enter_otp(driver, otp)
        click_verify(driver) 
        
        time.sleep(5)
        enter_name_and_agree(driver)
        
        # Wait for the dashboard to settle
        time.sleep(10) 

        # Start the generation loop
        while True:
            print("\n🔄 --- Starting Generation Cycle ---")
            
            if not click_start_button(driver):
                # If the button isn't there, maybe we need to go to New Chat first
                go_to_new_chat(driver)
                click_start_button(driver)

            click_menu_item_by_text(driver, target_text="Create images (Pro)")
            time.sleep(2)
            
            paste_video_script(driver, TEST_SCRIPT)
            
            
            submit_video(driver)

            if generate_and_save_image(driver, timeout=120):
                print("✅ Cycle complete. Resetting...")
            else:
                print("⚠️ Download failed or timed out.")

            go_to_new_chat(driver)
            time.sleep(3)

    except Exception as e:
        print(f"🚨 Script crashed: {e}")
    finally:
        # Keep driver open for debugging if it fails
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    test_video_full_flow()
