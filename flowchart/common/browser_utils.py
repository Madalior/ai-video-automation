import time
import json
import requests
import re
import os
import shutil
import zipfile
from uuid import uuid4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= BROWSER SETUP =================
def start_browser(profile_path=None, headless=False, fresh_profile=False):
    """
    Starts a Chrome browser instance with ADVANCED anti-detection.
    
    This now uses the comprehensive stealth browser with:
    - WebDriver masking
    - Plugin mocking
    - WebGL spoofing
    - Canvas randomization
    - Chrome runtime injection
    - And 10+ other anti-detection measures
    
    Args:
        profile_path: Chrome profile directory
        headless: Run in headless mode
        fresh_profile: Create unique new Chrome ID for this instance
        
    Returns:
        Stealth-configured WebDriver
    """
    # Create fresh unique Chrome profile if requested
    if fresh_profile:
        unique_id = uuid4().hex[:12]
        profile_path = os.path.abspath(f"temp_chrome_profiles/fresh_{unique_id}")
        os.makedirs(profile_path, exist_ok=True)
        print(f"[BROWSER] Created fresh Chrome ID: fresh_{unique_id}")
    
    try:
        from .stealth_browser import start_stealth_browser
        print("[BROWSER] Using advanced stealth mode")
        
        return start_stealth_browser(profile_path, headless)
    except ImportError:
        print("[BROWSER] Warning: stealth_browser not found, using basic mode")
        # Fallback to basic setup
        options = Options()
        
        if profile_path:
            options.add_argument(f"user-data-dir={profile_path}")
            
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if headless:
            options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)
        
        # Basic stealth
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        return driver



# ================= SHADOW DOM HELPERS =================
def universal_shadow_click(driver, selector, delay_before=True, delay_after=True):
    """
    Clicks any element, safely handling quotes and nested Shadow DOMs.
    
    Args:
        driver: Selenium WebDriver
        selector: CSS selector for the element
        delay_before: Add random delay before click (default: True)
        delay_after: Add random delay after click (default: True)
    """
    import random
    
    # Delay BEFORE click - mimics human hesitation
    if delay_before:
        pre_delay = random.uniform(1.0, 4.0)
        print(f"[CLICK] Waiting {pre_delay:.1f}s before clicking...")
        time.sleep(pre_delay)
    
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
            target.dispatchEvent(new MouseEvent(type, {{ bubbles: true, view: window, composed: true }}));
        }});
        return true; 
    }}
    return false;
    """
    result = driver.execute_script(script)
    
    # Delay AFTER click - waits for page response
    if result and delay_after:
        post_delay = random.uniform(1.0, 2.0)
        time.sleep(post_delay)
    
    return result

def find_shadow_element(driver, selector):
    """Returns the element if found in Shadow DOM, else None."""
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
    return findInShadow(document, {safe_selector});
    """
    return driver.execute_script(script)

# ================= TEMP MAIL UTILS (MAIL.TM - WORKING!) =================
# Mail.tm is the working successor to mail.gw with identical API structure

# Provider: Mail.tm (confirmed working 2026-01-18)
MAIL_TM_BASE = "https://api.mail.tm"


def get_new_email():
    """
    Get temporary email from Mail.tm (mail.gw successor).
    
    Returns:
        (email, config_dict) or (None, None)
        config_dict contains provider info needed for get_otp()
    """
    print("[INFO] Creating new temporary email...")
    
    try:
        print("[TRY] Using Mail.tm provider...")
        response = requests.get(f"{MAIL_TM_BASE}/domains", timeout=10)
        
        if response.status_code == 200:
            domains = response.json()
            
            if "hydra:member" in domains and domains["hydra:member"]:
                domain = domains["hydra:member"][0]["domain"]
                email = f"{uuid4().hex[:8]}@{domain}"
                password = uuid4().hex
                
                # Create account
                r = requests.post(f"{MAIL_TM_BASE}/accounts", 
                                 json={"address": email, "password": password},
                                 timeout=10)
                
                if r.status_code in [200, 201]:
                    print(f"[SUCCESS] Mail.tm email: {email}")
                    return email, {"provider": "mailtm", "password": password}
                else:
                    print(f"[WARN] Mail.tm account creation failed: {r.status_code}")
        else:
            print(f"[WARN] Mail.tm domains failed: {response.status_code}")
            
    except Exception as e:
        print(f"[WARN] Mail.tm failed: {e}")
    
    print("[ERROR] Tempmail provider failed")
    print("[INFO] Manual login will be required")
    return None, None


def get_otp(email, config, max_wait=300):
    """
    Get OTP from Mail.tm inbox.
    
    Args:
        email: Email address string
        config: Provider config dict (from get_new_email)
        max_wait: Maximum wait time in seconds
    
    Returns:
        6-character OTP string or None
    """
    print("[INFO] Waiting for OTP...")
    
    if not config or "provider" not in config:
        print("[ERROR] Invalid config for OTP retrieval")
        return None
    
    provider = config["provider"]
    
    if provider != "mailtm":
        print(f"[ERROR] Unsupported provider: {provider}")
        return None
    
    try:
        password = config.get("password")
        if not password:
            return None
        
        # Get auth token
        r = requests.post(f"{MAIL_TM_BASE}/token", 
                         json={"address": email, "password": password},
                         timeout=10)
        
        if r.status_code != 200:
            print(f"[ERROR] Mail.tm auth failed: {r.status_code}")
            return None
        
        token = r.json().get("token")
        if not token:
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        waited = 0
        check_interval = 5
        
        while waited < max_wait:
            # Check for messages
            messages = requests.get(f"{MAIL_TM_BASE}/messages", 
                                   headers=headers, timeout=10).json()
            
            if messages.get("hydra:totalItems", 0) > 0:
                # Get first message
                msg_id = messages["hydra:member"][0]["id"]
                msg = requests.get(f"{MAIL_TM_BASE}/messages/{msg_id}", 
                                  headers=headers, timeout=10).json()
                
                # Search for OTP in email text
                full_text = msg.get("text", "") + " " + str(msg.get("html", ""))
                match = re.search(r"\b[A-Z0-9]{6}\b", full_text)
                
                if match:
                    otp = match.group(0)
                    print(f"[SUCCESS] OTP Received: {otp}")
                    return otp
            
            time.sleep(check_interval)
            waited += check_interval
            
            # Show progress every 15 seconds
            if waited % 15 == 0:
                print(f"[INFO] Still waiting for email... ({waited}s/{max_wait}s)")
        
        print("[ERROR] OTP Timeout")
        return None
        
    except Exception as e:
        print(f"[ERROR] OTP Error: {e}")
        return None



# ================= POPUP HANDLING =================
def handle_multiple_tabs_popup(driver):
    """
    Detects and handles the 'Let's try something else' popup.
    Uses JavaScript to find and click the button (same approach as console testing).
    
    Args:
        driver: Selenium WebDriver
        
    Returns:
        bool: True if popup was handled, False otherwise
    """
    try:
        # Use JavaScript to find and click the button
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
        
        result = driver.execute_script(click_script)
        
        if result:
            print("[DETECTED] Multiple tabs popup handled (via browser_utils)")
            time.sleep(3)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[WARN] Error handling popup: {e}")
        return False
