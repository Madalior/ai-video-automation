# Free Proxy Rotation Options

## ⚠️ Important Warning

**Free proxies are NOT recommended for production use** because:
- ❌ Slow and unreliable
- ❌ Often blacklisted by websites
- ❌ Security risks (data interception)
- ❌ High failure rate (60-90%)
- ❌ Limited locations

**However**, they can work for testing or very small-scale use.

---

## Option 1: Free Public Proxy Lists (Best Free Option)

### Sources

1. **Free Proxy List** - https://free-proxy-list.net/
2. **ProxyScrape** - https://proxyscrape.com/free-proxy-list
3. **GeoNode** - https://geonode.com/free-proxy-list
4. **Proxy-List.download** - https://www.proxy-list.download/

### Implementation

```python
import requests
from bs4 import BeautifulSoup
import random

class FreeProxyManager:
    """Scrape and manage free proxies."""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
    
    def fetch_free_proxies(self):
        """Fetch proxies from free-proxy-list.net."""
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'id': 'proxylisttable'})
            proxies = []
            
            for row in table.tbody.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    protocol = 'https' if https == 'yes' else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    proxies.append(proxy)
            
            self.proxies = proxies
            print(f"[PROXY] Fetched {len(proxies)} free proxies")
            return proxies
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch proxies: {e}")
            return []
    
    def test_proxy(self, proxy_url, timeout=5):
        """Test if proxy is working."""
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout
            )
            if response.status_code == 200:
                return True
        except:
            pass
        return False
    
    def test_all_proxies(self, max_workers=10):
        """Test all proxies and keep working ones."""
        from concurrent.futures import ThreadPoolExecutor
        
        print(f"[PROXY] Testing {len(self.proxies)} proxies...")
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.test_proxy, self.proxies))
        
        for proxy, is_working in zip(self.proxies, results):
            if is_working:
                working.append(proxy)
        
        self.working_proxies = working
        print(f"[PROXY] Found {len(working)} working proxies")
        return working
    
    def get_random_proxy(self):
        """Get random working proxy."""
        if not self.working_proxies:
            self.fetch_free_proxies()
            self.test_all_proxies()
        
        if self.working_proxies:
            return random.choice(self.working_proxies)
        return None
    
    def save_proxies(self, filename='working_proxies.txt'):
        """Save working proxies to file."""
        with open(filename, 'w') as f:
            for proxy in self.working_proxies:
                f.write(proxy + '\n')
        print(f"[PROXY] Saved {len(self.working_proxies)} proxies to {filename}")
```

### Usage

```python
# Fetch and test free proxies
proxy_mgr = FreeProxyManager()
proxy_mgr.fetch_free_proxies()
working = proxy_mgr.test_all_proxies()

# Use with browser
if working:
    proxy = proxy_mgr.get_random_proxy()
    driver = start_stealth_browser(proxy=proxy)
    
    # Save for later
    proxy_mgr.save_proxies()
```

---

## Option 2: Tor Network (Anonymous + Free)

### Setup

1. **Install Tor Browser** or **Tor Service**
   - Download: https://www.torproject.org/download/

2. **Start Tor Service**:
   ```bash
   # Windows (after installing Tor)
   "C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe"
   ```

3. **Default Proxy**: `socks5://127.0.0.1:9050`

### Implementation

```python
from stem import Signal
from stem.control import Controller
import time

class TorProxyManager:
    """Manage Tor proxy and IP rotation."""
    
    def __init__(self, tor_port=9050, control_port=9051, password=None):
        self.tor_port = tor_port
        self.control_port = control_port
        self.password = password
        self.proxy_url = f"socks5://127.0.0.1:{tor_port}"
    
    def get_current_ip(self):
        """Get current Tor IP."""
        import requests
        try:
            session = requests.Session()
            session.proxies = {
                'http': self.proxy_url,
                'https': self.proxy_url
            }
            response = session.get('http://httpbin.org/ip', timeout=10)
            return response.json()['origin']
        except Exception as e:
            print(f"[TOR] Error getting IP: {e}")
            return None
    
    def rotate_ip(self):
        """Request new Tor circuit (new IP)."""
        try:
            with Controller.from_port(port=self.control_port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    controller.authenticate()
                
                controller.signal(Signal.NEWNYM)
                print("[TOR] Requesting new circuit...")
                time.sleep(3)  # Wait for new circuit
                
                new_ip = self.get_current_ip()
                print(f"[TOR] New IP: {new_ip}")
                return True
                
        except Exception as e:
            print(f"[TOR] Failed to rotate: {e}")
            return False
    
    def get_proxy(self):
        """Get Tor proxy URL."""
        return self.proxy_url
```

### Usage

```python
# Setup Tor
tor = TorProxyManager()

# Use with browser
driver = start_stealth_browser(proxy=tor.get_proxy())

# Rotate IP after 15 requests
tor.rotate_ip()  # New IP!

# Use new IP
driver.quit()
driver = start_stealth_browser(proxy=tor.get_proxy())
```

---

## Option 3: ProxyScrape Free API

### API Access

```python
import requests

class ProxyScrapeAPI:
    """Use ProxyScrape free API."""
    
    def __init__(self):
        self.api_url = "https://api.proxyscrape.com/v2/"
    
    def get_proxies(self, protocol='http', timeout=5000, country='all'):
        """
        Get free proxies from ProxyScrape API.
        
        Args:
            protocol: 'http', 'socks4', 'socks5'
            timeout: Proxy timeout in ms
            country: 'all' or specific country code (e.g., 'us')
        """
        params = {
            'request': 'get',
            'protocol': protocol,
            'timeout': timeout,
            'country': country,
            'ssl': 'all',
            'anonymity': 'all'
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            proxies = response.text.strip().split('\n')
            
            # Format proxies
            formatted = [f"{protocol}://{p.strip()}" for p in proxies if p.strip()]
            print(f"[PROXYSCRAPE] Fetched {len(formatted)} proxies")
            return formatted
            
        except Exception as e:
            print(f"[ERROR] ProxyScrape API failed: {e}")
            return []
```

---

## Option 4: Free Trials of Premium Services

### Services with Free Trials

1. **Bright Data** - $5.88 free trial credit
   - https://brightdata.com/

2. **Smartproxy** - 3-day free trial
   - https://smartproxy.com/

3. **Oxylabs** - 7-day free trial
   - https://oxylabs.io/

4. **IPRoyal** - Free tier (limited)
   - https://iproyal.com/

### Recommended for Testing

Start with **Bright Data $5.88 trial** to test professional proxies before committing.

---

## Complete Free Solution Example

```python
# free_proxy_solution.py

from flowchart.common.stealth_browser import start_stealth_browser
from flowchart.character.image_generator import DreaminaGenerator
import time

class FreeProxyRotator:
    """Complete free proxy solution."""
    
    def __init__(self):
        self.proxy_mgr = FreeProxyManager()
        self.current_proxy = None
        self.request_count = 0
        self.max_per_proxy = 5  # Use each proxy for max 5 requests
    
    def setup(self):
        """Setup free proxies."""
        print("[SETUP] Fetching free proxies...")
        self.proxy_mgr.fetch_free_proxies()
        self.proxy_mgr.test_all_proxies()
        
        if not self.proxy_mgr.working_proxies:
            print("[ERROR] No working proxies found!")
            return False
        
        self.current_proxy = self.proxy_mgr.get_random_proxy()
        print(f"[SETUP] Ready with {len(self.proxy_mgr.working_proxies)} proxies")
        return True
    
    def get_proxy(self):
        """Get current or new proxy."""
        if self.request_count >= self.max_per_proxy:
            # Rotate to new proxy
            print(f"[ROTATE] Switching proxy after {self.request_count} requests")
            self.current_proxy = self.proxy_mgr.get_random_proxy()
            self.request_count = 0
        
        self.request_count += 1
        return self.current_proxy

# Usage
rotator = FreeProxyRotator()
if rotator.setup():
    for i in range(20):
        proxy = rotator.get_proxy()
        print(f"[GEN {i+1}] Using proxy: {proxy}")
        
        # Use with browser
        driver = start_stealth_browser(proxy=proxy)
        # ... generate image/video ...
        driver.quit()
```

---

## Comparison: Free vs Paid

| Feature | Free Proxies | Paid Proxies |
|---------|--------------|--------------|
| Cost | $0 | $50-100/month |
| Reliability | 10-40% | 99%+ |
| Speed | Slow | Fast |
| Detection Risk | High | Very Low |
| Locations | Limited | 100+ countries |
| Rotation | Manual | Automatic |
| Support | None | 24/7 |

---

## Recommended Free Strategy

### For Testing / Small Scale (1-5 videos/day)

```python
# 1. Fetch free proxies daily
proxy_mgr = FreeProxyManager()
proxy_mgr.fetch_free_proxies()
working = proxy_mgr.test_all_proxies()

# 2. Use each proxy for 3-5 requests max
# 3. Rotate to new proxy
# 4. Combine with:
#    - Stealth browser ✅
#    - Session manager ✅
#    - Overload detection ✅
#    - Long delays (20-30s between requests)
```

### For Production (10+ videos/day)

**Don't use free proxies!** Instead:

1. ✅ **Bright Data Trial** - $5.88 credit (good for ~100 requests)
2. ✅ **Then upgrade** to paid residential proxies
3. ✅ Or use **VPN rotation** ($5-10/month) as compromise

---

## Free Option Summary

### Best Free Options (Ranked)

1. 🥇 **Tor Network** - Free, anonymous, built-in rotation
   - ✅ Best reliability among free options
   - ❌ Slower than regular proxies
   - ❌ May be blocked by some sites

2. 🥈 **ProxyScrape API** - Free API, fresh proxies
   - ✅ Easy to use
   - ❌ Still unreliable (~20-30% work)

3. 🥉 **Manual Free Proxy Lists** - Scrape yourself
   - ✅ Most proxies available
   - ❌ Most work required
   - ❌ Lowest reliability

### Reality Check

**Free proxies + Anti-bot system = 60-70% success rate**

**Paid proxies + Anti-bot system = 95-99% success rate**

### My Recommendation

1. **Start**: Test with Tor (free, most reliable)
2. **Scale**: Bright Data trial ($5.88)
3. **Production**: Upgrade to residential proxies ($50-100/month)

The advanced anti-bot system you already have will work great with **any** proxy option! 🎯
