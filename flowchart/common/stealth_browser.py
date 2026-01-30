"""
Advanced Stealth Browser for Anti-Detection

Comprehensive browser setup with fingerprint masking, WebGL spoofing,
canvas randomization, and all major bot detection countermeasures.
"""

import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def start_stealth_browser(profile_path=None, headless=False, proxy=None):
    """
    Start Chrome with comprehensive anti-detection measures.
    
    This now uses the comprehensive stealth browser with:
    - WebDriver masking
    - Plugin mocking
    - WebGL spoofing
    - Canvas randomization
    - Chrome runtime injection
    - Proxy support (NEW!)
    - And 10+ other anti-detection measures
    
    Args:
        profile_path: Chrome profile directory path
        headless: Run in headless mode
        proxy: Proxy URL (e.g., "http://proxy:port" or "socks5://proxy:port")
        
    Returns:
        Stealth-configured WebDriver
    """
    options = Options()
    
    # Profile setup
    if profile_path:
        options.add_argument(f"user-data-dir={profile_path}")
    
    # Core anti-detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Additional stealth flags
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    
    # === PROXY SETUP ===
    if proxy:
        proxy_clean = proxy.split('@')[1] if '@' in proxy else proxy
        print(f"[PROXY] Using proxy: {proxy_clean}")
        options.add_argument(f'--proxy-server={proxy}')
    
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
    
    # Preferences for realistic behavior
    options.add_experimental_option("prefs", {
        "intl.accept_languages": "en-US,en",
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    })
    
    # Initialize driver
    driver = webdriver.Chrome(options=options)
    
    # ==== COMPREHENSIVE STEALTH JAVASCRIPT ====
    stealth_script = """
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
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.call(this, parameter);
    };
    
    // ===== Canvas Fingerprint Randomization =====
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        // Add minimal noise to canvas
        const context = this.getContext('2d');
        if (context) {
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                // Add tiny random noise
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
                // Return realistic devices
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
    Object.defineProperty(window.screen, 'colorDepth', {
        get: () => 24
    });
    Object.defineProperty(window.screen, 'pixelDepth', {
        get: () => 24
    });
    
    // ===== Timezone Consistency =====
    // Make sure Intl.DateTimeFormat returns consistent timezone
    const originalDateTimeFormat = Intl.DateTimeFormat;
    Intl.DateTimeFormat = function(...args) {
        const dtf = new originalDateTimeFormat(...args);
        const originalResolvedOptions = dtf.resolvedOptions;
        dtf.resolvedOptions = function() {
            const options = originalResolvedOptions.call(this);
            options.timeZone = 'America/New_York';  // Consistent timezone
            return options;
        };
        return dtf;
    };
    
    // ===== WebRTC IP Leak Prevention =====
    if (window.RTCPeerConnection) {
        const originalRTC = window.RTCPeerConnection;
        window.RTCPeerConnection = function(...args) {
            const pc = new originalRTC(...args);
            const originalCreateDataChannel = pc.createDataChannel;
            pc.createDataChannel = function() {
                return null;
            };
            return pc;
        };
    }
    
    // ===== Notification Permission =====
    Object.defineProperty(Notification, 'permission', {
        get: () => 'default'
    });
    
    console.log('[STEALTH] Anti-detection measures activated');
    """
    
    # Inject stealth script on every new page
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": stealth_script
    })
    
    # Additional CDP commands for stealth
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
