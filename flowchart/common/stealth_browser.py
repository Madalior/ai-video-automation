"""
Advanced Stealth Browser for Anti-Detection

Comprehensive browser setup with fingerprint masking, WebGL spoofing,
canvas randomization, and all major bot detection countermeasures.

NOW USES: undetected-chromedriver for binary-level bot evasion
"""

import random
import os

# Try to use undetected-chromedriver for best stealth
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
    print("[STEALTH] Using undetected-chromedriver for maximum stealth")
except ImportError:
    UC_AVAILABLE = False
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    print("[STEALTH] undetected-chromedriver not found, using standard selenium")

def start_stealth_browser(profile_path=None, headless=False):
    """
    Start Chrome with comprehensive anti-detection measures.
    
    This now uses undetected-chromedriver for binary-level stealth:
    - Patches Chrome binary to remove automation traces
    - Removes $cdc_ variables
    - WebDriver masking at kernel level
    - Plus all JavaScript-level countermeasures
    
    Args:
        profile_path: Chrome profile directory path
        headless: Run in headless mode
        
    Returns:
        Stealth-configured WebDriver
    """
    
    # === USE UNDETECTED CHROMEDRIVER (PREFERRED) ===
    if UC_AVAILABLE:
        print("[STEALTH BROWSER] Initializing with undetected-chromedriver...")
        
        options = uc.ChromeOptions()
        
        # === INCOGNITO MODE for fresh state (skip profile in incognito) ===
        options.add_argument("--incognito")
        # Note: user-data-dir is NOT used with incognito - they conflict!
        # Incognito already provides a fresh session
        
        # === DISABLE SYNC/BACKUP PROMPTS ===
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "sync.requested": False,
            "sync.suppress_start": True,
            "signin.allowed": False,
            "signin.allowed_on_next_startup": False,
            "browser.startup_page": 0,
            "profile.default_content_setting_values.notifications": 2,
            # Disable Google account promo popups
            "browser.enable_spellchecking": False,
            "spellcheck.use_spelling_service": False,
            "safebrowsing.enabled": False,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            # Disable backup reminders
            "browser.show_update_promotion_info_bar": False,
            "browser.suppress_first_run_default_browser_prompt": True,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Core anti-detection flags (some are redundant with UC but good to have)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Clear cache/cookies on startup
        options.add_argument("--disk-cache-size=0")
        options.add_argument("--aggressive-cache-discard")
        
        # Realistic window size
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        
        # Language and locale
        options.add_argument("--lang=en-US,en;q=0.9")
        
        # Detect Chrome version FIRST (critical for correct driver download)
        chrome_version = None
        import subprocess
        try:
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                version_line = result.stdout.strip().split()[-1]
                chrome_version = int(version_line.split('.')[0])
                print(f"[STEALTH] Detected Chrome version: {chrome_version}")
        except Exception as e:
            print(f"[WARNING] Could not detect Chrome version: {e}")
        
        # Initialize undetected Chrome with explicit version
        try:
            if chrome_version:
                driver = uc.Chrome(
                    options=options, 
                    use_subprocess=True,
                    version_main=chrome_version  # Force correct driver version
                )
            else:
                driver = uc.Chrome(options=options, use_subprocess=True)
        except Exception as e:
            print(f"[ERROR] UC initialization failed: {e}")
            print("[INFO] Falling back to standard Selenium...")
            raise e
        
        # UC already patches navigator.webdriver, but we add extra JS for safety
        _inject_extra_stealth(driver)
        
        print("[STEALTH BROWSER] OK - Undetected ChromeDriver initialized")
        print(f"[STEALTH BROWSER] Profile: {profile_path if profile_path else 'Default'}")
        print(f"[STEALTH BROWSER] Headless: {headless}")
        
        return driver
    
    # === FALLBACK: STANDARD SELENIUM WITH JS STEALTH ===
    else:
        print("[STEALTH BROWSER] Fallback: Using standard Selenium with JS stealth...")
        
        options = Options()
        
        # Profile setup
        if profile_path:
            options.add_argument(f"user-data-dir={profile_path}")
        
        # === INCOGNITO MODE for fresh state ===
        options.add_argument("--incognito")
        
        # Core anti-detection flags
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Additional stealth flags
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        
        # Realistic window size
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")
        
        # Realistic user agent (updated for 2026)
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")
        
        # Language and locale
        options.add_argument("--lang=en-US,en;q=0.9")
        
        # Preferences for realistic behavior + ANTI-TRACKING + NO SYNC/BACKUP
        options.add_experimental_option("prefs", {
            "intl.accept_languages": "en-US,en",
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "sync.requested": False,
            "sync.suppress_start": True,
            "signin.allowed": False,
            "signin.allowed_on_next_startup": False,
            "profile.block_third_party_cookies": True,
            "profile.cookie_controls_mode": 1,
            "autofill.enabled": False,
            "autofill.profile_enabled": False,
            "autofill.credit_card_enabled": False,
            # Additional anti-backup/sync settings
            "browser.startup_page": 0,
            "browser.enable_spellchecking": False,
            "spellcheck.use_spelling_service": False,
            "safebrowsing.enabled": False,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "browser.show_update_promotion_info_bar": False,
            "browser.suppress_first_run_default_browser_prompt": True,
        })
        
        # Initialize driver
        driver = webdriver.Chrome(options=options)
    
        # ==== COMPREHENSIVE STEALTH JAVASCRIPT ====
        stealth_script = _get_stealth_script()
        
        # Inject stealth script on every new page
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_script
        })
        
        # Additional CDP commands for stealth
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": user_agent,
            "platform": "Win32",
            "acceptLanguage": "en-US,en;q=0.9"
        })
        
        # Enable logging
        print("[STEALTH BROWSER] Initialized with comprehensive anti-detection")
        print(f"[STEALTH BROWSER] Profile: {profile_path if profile_path else 'Default'}")
        print(f"[STEALTH BROWSER] Headless: {headless}")
        
        return driver


def _inject_extra_stealth(driver):
    """
    Inject extra stealth scripts for undetected-chromedriver.
    UC already handles most anti-detection, but we add extras for safety.
    """
    extra_stealth = """
    // Extra stealth for UC - minimal additions
    
    // Make sure chrome.runtime exists
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) {
        window.chrome.runtime = {
            connect: () => {},
            sendMessage: () => {},
            onMessage: { addListener: () => {}, removeListener: () => {}, hasListener: () => false }
        };
    }
    
    // Canvas fingerprint randomization
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        const context = this.getContext('2d');
        if (context && this.width > 0 && this.height > 0) {
            try {
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < Math.min(imageData.data.length, 40); i += 4) {
                    imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                }
                context.putImageData(imageData, 0, 0);
            } catch(e) {}
        }
        return originalToDataURL.apply(this, arguments);
    };
    
    console.log('[UC-STEALTH] Extra anti-detection activated');
    """
    
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": extra_stealth
        })
    except Exception as e:
        print(f"[WARNING] Could not inject extra stealth: {e}")


def _get_stealth_script():
    """Return the comprehensive stealth JavaScript for standard Selenium."""
    return """
    // ===== Navigator Webdriver =====
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // Delete automation traces
    delete navigator.__proto__.webdriver;
    
    // ===== Plugins (make it look like a real browser) =====
    Object.defineProperty(navigator, 'plugins', {
        get: () => [
            {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}},
            {1: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}},
            {2: {type: "text/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin}}
        ]
    });
    
    // ===== Languages =====
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    
    // ===== Chrome Object (critical for detection) =====
    if (!window.chrome) {
        window.chrome = {};
    }
    window.chrome.runtime = {
        connect: () => {},
        sendMessage: () => {},
        onMessage: {
            addListener: () => {},
            removeListener: () => {},
            hasListener: () => false
        }
    };
    window.chrome.loadTimes = function() {
        return {
            commitLoadTime: Date.now() / 1000 - 5,
            connectionInfo: 'h2',
            finishDocumentLoadTime: Date.now() / 1000 - 1,
            finishLoadTime: Date.now() / 1000,
            firstPaintAfterLoadTime: 0,
            firstPaintTime: Date.now() / 1000 - 2,
            navigationType: 'Other',
            npnNegotiatedProtocol: 'h2',
            requestTime: Date.now() / 1000 - 6,
            startLoadTime: Date.now() / 1000 - 6,
            wasAlternateProtocolAvailable: false,
            wasFetchedViaSpdy: true,
            wasNpnNegotiated: true
        };
    };
    window.chrome.csi = function() {
        return {
            onloadT: Date.now(),
            pageT: 1234.5,
            startE: Date.now() - 10000,
            tran: 15
        };
    };
    window.chrome.app = {
        isInstalled: false,
        InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'},
        RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}
    };
    
    // ===== WebGL Vendor/Renderer Spoofing =====
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return getParameter.call(this, parameter);
    };
    
    // ===== Canvas Fingerprint Randomization =====
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            }
            context.putImageData(imageData, 0, 0);
        }
        return originalToDataURL.apply(this, arguments);
    };
    
    // ===== Permissions API =====
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
    );
    
    // ===== Battery API Mocking =====
    Object.defineProperty(navigator, 'getBattery', {
        get: () => () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1,
            addEventListener: () => {},
            removeEventListener: () => {},
            dispatchEvent: () => true
        })
    });
    
    // ===== Media Devices =====
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
        navigator.mediaDevices.enumerateDevices = function() {
            return originalEnumerateDevices.call(this).then(devices => {
                return [
                    {deviceId: 'default', groupId: '', kind: 'audioinput', label: ''},
                    {deviceId: 'communications', groupId: '', kind: 'audioinput', label: ''},
                    {deviceId: 'default', groupId: '', kind: 'audiooutput', label: ''},
                    {deviceId: '', groupId: '', kind: 'videoinput', label: ''}
                ];
            });
        };
    }
    
    // ===== Screen Depth/ColorDepth =====
    Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
    Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
    
    // ===== Timezone Consistency =====
    const originalDateTimeFormat = Intl.DateTimeFormat;
    Intl.DateTimeFormat = function(...args) {
        const dtf = new originalDateTimeFormat(...args);
        const originalResolvedOptions = dtf.resolvedOptions;
        dtf.resolvedOptions = function() {
            const options = originalResolvedOptions.call(this);
            options.timeZone = 'America/New_York';
            return options;
        };
        return dtf;
    };
    
    // ===== WebRTC IP Leak Prevention =====
    if (window.RTCPeerConnection) {
        const originalRTC = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
            const pc = new originalRTC(...args);
            pc.createDataChannel = function() { return null; };
            return pc;
        };
    }
    
    // ===== Notification Permission =====
    Object.defineProperty(Notification, 'permission', { get: () => 'default' });
    
    console.log('[STEALTH] Anti-detection measures activated');
    """


def get_stealth_capabilities():
    """
    Return list of active stealth features.
    
    Returns:
        List of enabled anti-detection features
    """
    return [
        "Navigator.webdriver hidden",
        "Plugins array mocked",
        "Chrome runtime injected",
        "WebGL vendor/renderer spoofed",
        "Canvas fingerprint randomized",
        "Permissions API normalized",
        "Battery API mocked",
        "Media devices realistic",
        "Screen properties normalized",
        "Timezone consistency",
        "WebRTC leak prevention",
        "User agent realistic (Chrome 131)",
        "Languages set to en-US",
    ]
