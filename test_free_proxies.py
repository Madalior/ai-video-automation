"""
Test Free Proxy Rotation

This script tests free proxy fetching and rotation.
"""

import requests
from bs4 import BeautifulSoup
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class FreeProxyTester:
    """Fetch and test free proxies."""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
    
    def fetch_proxies_from_free_proxy_list(self):
        """Fetch proxies from free-proxy-list.net."""
        print("\n[FETCH] Getting proxies from free-proxy-list.net...")
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'class': 'table table-striped table-bordered'})
            if not table:
                print("[ERROR] Could not find proxy table")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows[:50]:  # Get first 50
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    protocol = 'https' if https == 'yes' else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    proxies.append(proxy)
            
            print(f"[SUCCESS] Fetched {len(proxies)} proxies")
            return proxies
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch from free-proxy-list.net: {e}")
            return []
    
    def fetch_proxies_from_proxyscrape(self):
        """Fetch proxies from ProxyScrape API."""
        print("\n[FETCH] Getting proxies from ProxyScrape API...")
        try:
            url = "https://api.proxyscrape.com/v2/"
            params = {
                'request': 'get',
                'protocol': 'http',
                'timeout': '5000',
                'country': 'all',
                'ssl': 'all',
                'anonymity': 'all'
            }
            
            response = requests.get(url, params=params, timeout=10)
            proxy_list = response.text.strip().split('\n')
            
            proxies = []
            for p in proxy_list[:50]:  # Get first 50
                p = p.strip()
                if p:
                    proxies.append(f"http://{p}")
            
            print(f"[SUCCESS] Fetched {len(proxies)} proxies")
            return proxies
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch from ProxyScrape: {e}")
            return []
    
    def test_single_proxy(self, proxy_url, timeout=5):
        """Test if a single proxy is working."""
        try:
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout
            )
            if response.status_code == 200:
                ip = response.json().get('origin', 'Unknown')
                return True, ip
        except:
            pass
        return False, None
    
    def test_proxies_parallel(self, proxies, max_workers=20):
        """Test multiple proxies in parallel."""
        print(f"\n[TEST] Testing {len(proxies)} proxies (this may take a minute)...")
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_single_proxy, proxy): proxy 
                for proxy in proxies
            }
            
            completed = 0
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    is_working, ip = future.result()
                    if is_working:
                        working.append(proxy)
                        print(f"  [OK] [{completed}/{len(proxies)}] Working: {proxy} (IP: {ip})")
                    else:
                        if completed % 10 == 0:
                            print(f"  [WAIT] [{completed}/{len(proxies)}] Tested so far, {len(working)} working...")
                except Exception as e:
                    pass
        
        print(f"\n[RESULT] Found {len(working)}/{len(proxies)} working proxies ({len(working)/len(proxies)*100:.1f}%)")
        return working
    
    def demonstrate_rotation(self, proxies, num_rotations=5):
        """Demonstrate proxy rotation."""
        if not proxies:
            print("\n[ERROR] No working proxies to demonstrate!")
            return
        
        print(f"\n[DEMO] Demonstrating proxy rotation with {len(proxies)} proxies...")
        
        for i in range(min(num_rotations, len(proxies))):
            proxy = proxies[i]
            print(f"\n[ROTATION {i+1}] Using proxy: {proxy}")
            
            is_working, ip = self.test_single_proxy(proxy, timeout=10)
            if is_working:
                print(f"  [OK] Successfully connected")
                print(f"  IP Address: {ip}")
                print(f"  Status: READY FOR AUTOMATION")
            else:
                print(f"  [FAIL] Failed (proxy may have died)")
            
            time.sleep(1)
    
    def save_working_proxies(self, proxies, filename='working_proxies.txt'):
        """Save working proxies to file."""
        if proxies:
            with open(filename, 'w') as f:
                for proxy in proxies:
                    f.write(proxy + '\n')
            print(f"\n[SAVED] {len(proxies)} working proxies saved to {filename}")


def main():
    """Main test function."""
    print("="*70)
    print("FREE PROXY ROTATION TESTER")
    print("="*70)
    
    tester = FreeProxyTester()
    all_proxies = []
    
    # Try to fetch from multiple sources
    proxies1 = tester.fetch_proxies_from_proxyscrape()
    if proxies1:
        all_proxies.extend(proxies1)
    
    proxies2 = tester.fetch_proxies_from_free_proxy_list()
    if proxies2:
        all_proxies.extend(proxies2)
    
    if not all_proxies:
        print("\n[ERROR] Failed to fetch any proxies!")
        print("\nTip: Free proxy sites may be temporarily down.")
        print("Try again later or use Tor network instead.")
        return
    
    print(f"\n[INFO] Total proxies collected: {len(all_proxies)}")
    
    # Remove duplicates
    all_proxies = list(set(all_proxies))
    print(f"[INFO] Unique proxies: {len(all_proxies)}")
    
    # Test proxies
    working = tester.test_proxies_parallel(all_proxies)
    
    if working:
        # Save working proxies
        tester.save_working_proxies(working)
        
        # Demonstrate rotation
        tester.demonstrate_rotation(working, num_rotations=3)
        
        print("\n" + "="*70)
        print("TEST COMPLETE!")
        print("="*70)
        print(f"Working proxies: {len(working)}/{len(all_proxies)}")
        print(f"Success rate: {len(working)/len(all_proxies)*100:.1f}%")
        print(f"\nProxies saved to: working_proxies.txt")
        print("\nYou can now use these proxies with your automation!")
    else:
        print("\n" + "="*70)
        print("NO WORKING PROXIES FOUND")
        print("="*70)
        print("\nRecommendations:")
        print("1. Try running the test again (proxies change frequently)")
        print("2. Use Tor network instead (most reliable free option)")
        print("3. Consider using a VPN ($5-10/month)")
        print("4. For production, use paid residential proxies")


if __name__ == "__main__":
    main()
