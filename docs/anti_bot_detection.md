# Anti-Bot Detection Techniques for Gemini Automation

## Understanding the Problem

The error message **"Oh my, it seems our systems are overloaded"** is often Gemini's bot detection triggering, not actual server overload.

![Bot Detection](C:/Users/vijay/.gemini/antigravity/brain/fa91ae78-a4bd-44c9-9d4c-70982ad85897/uploaded_image_1768994839930.png)

## Current Anti-Detection Measures

Your `browser_utils.py` already has some protections:

```python
# ✅ Already implemented:
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """
})
```

## Additional Anti-Detection Enhancements

### 1. **Human-Like Mouse Movements**

Instead of instant clicks, simulate human mouse movement:

```python
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

def human_like_click(driver, element):
    """Click with human-like behavior."""
    actions = ActionChains(driver)
    
    # Move to element with slight offset (humans don't click exact center)
    offset_x = random.randint(-5, 5)
    offset_y = random.randint(-5, 5)
    actions.move_to_element_with_offset(element, offset_x, offset_y)
    
    # Pause before clicking (humans hesitate)
    time.sleep(random.uniform(0.3, 0.8))
    
    # Click
    actions.click()
    actions.perform()
    
    # Post-click delay
    time.sleep(random.uniform(1.0, 2.0))
```

### 2. **Enhanced Browser Fingerprint**

Make Chrome look more like a regular user browser:

```python
def start_browser_stealth(profile_path=None, headless=False):
    """Enhanced anti-detection browser setup."""
    options = Options()
    
    if profile_path:
        options.add_argument(f"user-data-dir={profile_path}")
    
    # Anti-detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # NEW: Additional stealth
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")  # Sometimes helps
    
    # Set realistic user agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    # Add language and timezone
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_experimental_option("prefs", {
        "intl.accept_languages": "en-US,en",
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
    })

    if headless:
        options.add_argument("--headless=new")
        # In headless, need extra stealth
        options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    
    # Execute comprehensive stealth script
    stealth_js = """
        // Hide webdriver
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Mock chrome object (makes it look like real Chrome)
        window.chrome = {
            runtime: {}
        };
        
        // Permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
        );
    """
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": stealth_js
    })
    
    return driver
```

### 3. **Random Delays Between Actions**

Already added! But here's an enhanced version:

```python
def smart_delay(action_type='normal'):
    """
    Human-like delays based on action type.
    
    Args:
        action_type: 'short', 'normal', 'long', 'thinking'
    """
    import random
    
    delays = {
        'short': (0.5, 1.5),      # Quick actions
        'normal': (1.0, 2.5),     # Regular actions
        'long': (2.0, 4.0),       # After important actions
        'thinking': (3.0, 6.0),   # Before starting generation
    }
    
    min_delay, max_delay = delays.get(action_type, (1.0, 2.0))
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
```

### 4. **IP Rotation (Advanced)**

If you're running many parallel workers:

```python
# Note: This requires proxy service (paid)
def start_browser_with_proxy(profile_path=None, proxy=None):
    """Start browser with proxy for IP rotation."""
    options = Options()
    
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    # ... rest of setup ...
    return driver
```

### 5. **Session Management**

Don't create too many new sessions:

```python
class SessionManager:
    """Manage browser sessions to avoid detection."""
    
    def __init__(self, max_requests_per_session=20):
        self.max_requests_per_session = max_requests_per_session
        self.request_count = 0
        self.last_request_time = 0
    
    def check_should_restart(self):
        """Check if we should restart the session."""
        import time
        
        self.request_count += 1
        current_time = time.time()
        
        # Restart if too many requests
        if self.request_count >= self.max_requests_per_session:
            print("[SESSION] Restarting due to request limit")
            return True
        
        # Restart if too fast (anti-rate-limit)
        if current_time - self.last_request_time < 15:
            print("[WARNING] Requests too fast, adding delay...")
            time.sleep(random.uniform(5, 10))
        
        self.last_request_time = current_time
        return False
```

### 6. **Handling "Overloaded" Messages**

Detect and retry with exponential backoff:

```python
def handle_overload_error(self, max_retries=3):
    """
    Detect and handle 'systems overloaded' message.
    
    Returns:
        True if should retry, False if should give up
    """
    import time
    import random
    
    # Check for overload message
    try:
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        
        if "overloaded" in body_text or "try again later" in body_text:
            print("[OVERLOAD] Bot detection triggered!")
            
            for retry in range(max_retries):
                # Exponential backoff: 30s, 60s, 120s
                wait_time = 30 * (2 ** retry) + random.uniform(0, 10)
                print(f"[WAIT] Waiting {wait_time:.0f}s before retry {retry + 1}/{max_retries}")
                time.sleep(wait_time)
                
                # Refresh page
                self.driver.refresh()
                time.sleep(5)
                
                # Check if message is gone
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                if "overloaded" not in body_text:
                    print("[SUCCESS] Overload cleared!")
                    return True
            
            return False  # Give up after max retries
            
    except Exception as e:
        print(f"[ERROR] Checking overload: {e}")
        return False
```

---

## Recommended Integration

Update your `image_generator.py` and `video_generator.py`:

```python
class DreaminaGenerator:
    def __init__(self, headless=False, profile_path=None):
        # Use enhanced stealth browser
        self.driver = start_browser_stealth(profile_path, headless)
        self.session_manager = SessionManager(max_requests_per_session=15)
    
    def generate_image(self, prompt, output_path, reference_image=None, max_retries=2):
        """Generate with overload handling."""
        
        # Check session health
        if self.session_manager.check_should_restart():
            self.close()
            self.driver = start_browser_stealth(self.profile_path, self.headless)
            self.login()
        
        for attempt in range(max_retries):
            try:
                # Your existing generation code...
                self.go_to_new_chat()
                smart_delay('thinking')  # Pause like a human
                
                self.click_start_button()
                smart_delay('normal')
                
                # ... rest of generation ...
                
            except Exception as e:
                if "overloaded" in str(e).lower():
                    if self.handle_overload_error():
                        continue  # Retry
                    else:
                        raise  # Give up
                else:
                    raise
```

---

## Best Practices Summary

### ✅ DO:
1. **Use persistent Chrome profiles** (you already do this)
2. **Add random delays** (you've already added 1-2s delays ✅)
3. **Limit requests per session** (15-20 max before restarting)
4. **Space out parallel workers** (10s stagger - you already do this ✅)
5. **Use realistic user agents**
6. **Handle "overloaded" with exponential backoff**
7. **Keep browser sessions alive** (don't close/reopen constantly)

### ⚠️ AVOID:
1. Too many parallel workers (4-8 is safe, 20+ is risky)
2. Requests faster than every 15 seconds per worker
3. Headless mode (if possible - less detectable with visible browser)
4. Creating new sessions too frequently

---

## Quick Fix for Your Current Issue

Add this to your generators right after login:

```python
def generate_with_overload_handling(self, prompt, output_path):
    """Wrapper with overload detection."""
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Check for overload message first
            time.sleep(2)
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            if "overloaded" in page_text:
                if attempt < max_attempts - 1:
                    wait = 60 * (attempt + 1)  # 60s, 120s, 180s
                    print(f"[OVERLOAD] Waiting {wait}s...")
                    time.sleep(wait)
                    self.driver.refresh()
                    continue
                else:
                    raise Exception("Bot detection - too many retries")
            
            # Proceed with generation
            return self.generate_image(prompt, output_path)
            
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            print(f"[RETRY] Attempt {attempt + 1} failed: {e}")
            time.sleep(30)
```

This should significantly reduce bot detection! 🤖→😊
