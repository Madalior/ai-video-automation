# Automatic IP Address Rotation Guide

## Overview

Automatic IP rotation adds another layer of bot detection avoidance by making each browser session appear to come from different locations/IP addresses.

## Methods

### Method 1: Proxy Rotation (Recommended)

**Best for**: Production use with rotating residential proxies

#### Setup

1. **Get Proxy Service** (Paid)
   - **Residential Proxies** (Best): BrightData, Smartproxy, Oxylabs
   - **Datacenter Proxies** (Cheaper): ProxyMesh, IPRoyal
   - Cost: ~$50-100/month for residential

2. **Proxy Format**:
   ```
   http://username:password@proxy-server:port
   socks5://username:password@proxy-server:port
   ```

#### Implementation

**File**: `flowchart/common/proxy_manager.py` [NEW]

```python
import random
import requests

class ProxyManager:
    """Manage proxy rotation for browser sessions."""
    
    def __init__(self, proxy_list_file=None):
        """
        Initialize proxy manager.
        
        Args:
            proxy_list_file: Path to file with proxy list (one per line)
        """
        self.proxies = []
        self.current_index = 0
        
        if proxy_list_file:
            self.load_proxies(proxy_list_file)
    
    def load_proxies(self, filepath):
        """Load proxies from file."""
        with open(filepath, 'r') as f:
            self.proxies = [line.strip() for line in f if line.strip()]
        print(f"[PROXY] Loaded {len(self.proxies)} proxies")
    
    def add_proxy(self, proxy_url):
        """Add a single proxy."""
        self.proxies.append(proxy_url)
    
    def get_next_proxy(self):
        """Get next proxy in rotation."""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self):
        """Get random proxy."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def test_proxy(self, proxy_url):
        """Test if proxy is working."""
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=10
            )
            if response.status_code == 200:
                ip = response.json().get('origin')
                print(f"[PROXY TEST] Working - IP: {ip}")
                return True
        except Exception as e:
            print(f"[PROXY TEST] Failed: {e}")
        return False
```

#### Integration with Stealth Browser

**Update**: `flowchart/common/stealth_browser.py`

```python
def start_stealth_browser(profile_path=None, headless=False, proxy=None):
    """
    Start Chrome with comprehensive anti-detection measures + proxy.
    
    Args:
        profile_path: Chrome profile directory path
        headless: Run in headless mode
        proxy: Proxy URL (e.g., "http://user:pass@proxy:port")
    """
    options = Options()
    
    # ... existing setup ...
    
    # === PROXY SETUP ===
    if proxy:
        print(f"[PROXY] Using proxy: {proxy.split('@')[1] if '@' in proxy else proxy}")
        options.add_argument(f'--proxy-server={proxy}')
        
        # For authenticated proxies, use extension
        if '@' in proxy:
            # Chrome extension approach for auth proxies
            # (Implementation below)
            pass
    
    # ... rest of setup ...
```

#### Usage with Generators

```python
from flowchart.common.proxy_manager import ProxyManager
from flowchart.common.stealth_browser import start_stealth_browser

# Initialize proxy manager
proxy_mgr = ProxyManager()
proxy_mgr.add_proxy("http://user:pass@proxy1.example.com:8080")
proxy_mgr.add_proxy("http://user:pass@proxy2.example.com:8080")

# Start browser with proxy
proxy = proxy_mgr.get_next_proxy()
driver = start_stealth_browser(
    profile_path="chrome_data_0",
    headless=False,
    proxy=proxy
)
```

---

### Method 2: VPN Rotation

**Best for**: Smaller scale, manual control

#### Windows VPN Setup

1. **Get VPN Service**: NordVPN, ExpressVPN, Surfshark
2. **Use Command Line**:

```bash
# Connect to specific server
rasdial "VPN Connection Name" username password

# Disconnect
rasdial "VPN Connection Name" /disconnect
```

#### Python VPN Controller

```python
import subprocess
import time

class VPNManager:
    """Manage VPN connections on Windows."""
    
    def __init__(self, connection_name, username, password):
        self.connection_name = connection_name
        self.username = username
        self.password = password
    
    def connect(self, server=None):
        """Connect to VPN."""
        cmd = f'rasdial "{self.connection_name}" {self.username} {self.password}'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if "successfully" in result.stdout.lower():
                print(f"[VPN] Connected to {self.connection_name}")
                time.sleep(5)  # Wait for connection
                return True
        except Exception as e:
            print(f"[VPN] Connection failed: {e}")
        return False
    
    def disconnect(self):
        """Disconnect from VPN."""
        cmd = f'rasdial "{self.connection_name}" /disconnect'
        subprocess.run(cmd, shell=True)
        print(f"[VPN] Disconnected")
        time.sleep(3)
    
    def reconnect(self):
        """Reconnect to get new IP."""
        self.disconnect()
        time.sleep(2)
        return self.connect()
```

#### Usage

```python
vpn = VPNManager("NordVPN", "username", "password")

# Before starting session
vpn.connect()

# Generate 15 images/videos...

# After session limit
vpn.reconnect()  # New IP!

# Start new session
```

---

### Method 3: Mobile Hotspot Rotation (Free!)

**Best for**: Small scale, no budget

#### How It Works

1. **Use Mobile Data** - Each reconnection gets new IP
2. **Toggle Airplane Mode** - Reconnect to get new IP

#### Windows Automation

```python
import subprocess
import time

class MobileHotspotRotator:
    """Toggle mobile hotspot for IP rotation."""
    
    def toggle_airplane_mode(self):
        """Toggle airplane mode to force IP change."""
        # Requires admin rights
        print("[MOBILE] Toggling airplane mode...")
        
        # Turn on
        subprocess.run('netsh interface set interface "Wi-Fi" admin=disable', shell=True)
        time.sleep(5)
        
        # Turn off
        subprocess.run('netsh interface set interface "Wi-Fi" admin=enable', shell=True)
        time.sleep(10)  # Wait for reconnection
        
        print("[MOBILE] Reconnected with new IP")
    
    def rotate_ip(self):
        """Rotate IP by toggling connection."""
        self.toggle_airplane_mode()
```

---

## Integration with Session Manager

**Update**: `flowchart/common/session_manager.py`

```python
class SessionManager:
    def __init__(self, max_requests=15, min_interval=15, proxy_manager=None, vpn_manager=None):
        # ... existing init ...
        self.proxy_manager = proxy_manager
        self.vpn_manager = vpn_manager
    
    def get_next_proxy(self):
        """Get next proxy for session rotation."""
        if self.proxy_manager:
            return self.proxy_manager.get_next_proxy()
        return None
    
    def rotate_ip(self):
        """Rotate IP address."""
        if self.vpn_manager:
            print("[SESSION] Rotating IP via VPN...")
            self.vpn_manager.reconnect()
        elif self.proxy_manager:
            print("[SESSION] Rotating to next proxy...")
            return self.proxy_manager.get_next_proxy()
```

---

## Full Integration Example

### With Proxy Rotation

```python
from flowchart.common.session_manager import SessionManager
from flowchart.common.proxy_manager import ProxyManager
from flowchart.character.image_generator import DreaminaGenerator

# Setup
proxy_mgr = ProxyManager('proxies.txt')  # One proxy per line
session_mgr = SessionManager(proxy_manager=proxy_mgr)

# Generate images
for i in range(50):
    # Check if should rotate
    should_restart, reason = session_mgr.should_restart_session()
    
    if should_restart:
        # Get new proxy
        proxy = proxy_mgr.get_next_proxy()
        print(f"[ROTATION] Starting new session with new IP")
        
        # Close old browser
        gen.close()
        
        # Start new browser with new proxy
        gen = DreaminaGenerator(
            profile_path=f"chrome_data_{i % 8}",
            proxy=proxy  # NEW!
        )
        gen.login()
        session_mgr.reset_session()
    
    # Generate
    session_mgr.track_request()
    gen.generate_image(f"Scene {i}", f"output/image_{i}.png")
```

---

## Proxy List Format

**File**: `proxies.txt`

```
http://user1:pass1@proxy1.example.com:8080
http://user2:pass2@proxy2.example.com:8080
http://user3:pass3@proxy3.example.com:8080
socks5://user4:pass4@proxy4.example.com:1080
```

---

## Recommendations

### Small Scale (1-10 videos/day)
✅ **Mobile Hotspot Rotation** - Free!
- Rotate after every 10-15 requests
- Simple toggle airplane mode

### Medium Scale (10-50 videos/day)
✅ **VPN Rotation** - $5-10/month
- Use NordVPN/Surfshark
- Reconnect every 15 requests
- Combines with all other anti-bot features

### Large Scale (50+ videos/day)
✅ **Rotating Residential Proxies** - $50-100/month
- Professional proxy service
- Automatic rotation
- Looks like real home users
- Best detection resistance

---

## Cost Comparison

| Method | Cost/Month | Difficulty | Detection Risk |
|--------|------------|------------|----------------|
| Mobile Hotspot | $0 | Easy | Low |
| VPN | $5-10 | Easy | Low |
| Datacenter Proxy | $20-40 | Medium | Medium |
| Residential Proxy | $50-100 | Medium | Very Low |

---

## Testing

```python
# Test proxy before use
proxy_mgr = ProxyManager()
proxy = "http://user:pass@proxy.example.com:8080"

if proxy_mgr.test_proxy(proxy):
    # Use it
    driver = start_stealth_browser(proxy=proxy)
```

---

## Summary

### Quick Start (Free)

1. **Use Mobile Data**
2. **Toggle airplane mode** every 15 requests
3. **Combine with**:
   - Session manager ✅
   - Stealth browser ✅
   - Overload detection ✅

### Production (Paid)

1. **Get Residential Proxies** ($50-100/month)
2. **Integrate with ProxyManager**
3. **Automatic rotation** every 15 requests
4. **Zero detection** with all features combined

**Your current anti-bot system + IP rotation = Virtually undetectable! 🎯**
