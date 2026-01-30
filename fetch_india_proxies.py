"""
Fetch India-Specific Proxies

Gets and tests proxies specifically from India.
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class IndiaProxyFetcher:
    """Fetch proxies specifically from India."""
    
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
    
    def fetch_from_proxyscrape_india(self):
        """Fetch India proxies from ProxyScrape API."""
        print("[FETCH] Getting India proxies from ProxyScrape...")
        try:
            url = "https://api.proxyscrape.com/v2/"
            params = {
                'request': 'get',
                'protocol': 'http',
                'timeout': '5000',
                'country': 'in',  # India country code
                'ssl': 'all',
                'anonymity': 'all'
            }
            
            response = requests.get(url, params=params, timeout=10)
            proxy_list = response.text.strip().split('\n')
            
            proxies = []
            for p in proxy_list:
                p = p.strip()
                if p:
                    proxies.append(f"http://{p}")
            
            print(f"  Found {len(proxies)} India proxies")
            return proxies
        except Exception as e:
            print(f"  Failed: {e}")
            return []
    
    def fetch_from_geonode_india(self):
        """Fetch India proxies from GeoNode."""
        print("[FETCH] Getting India proxies from GeoNode...")
        try:
            url = "https://proxylist.geonode.com/api/proxy-list"
            params = {
                'limit': 50,
                'page': 1,
                'sort_by': 'lastChecked',
                'sort_type': 'desc',
                'country': 'IN',  # India
                'protocols': 'http'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            proxies = []
            if 'data' in data:
                for proxy in data['data']:
                    ip = proxy.get('ip')
                    port = proxy.get('port')
                    if ip and port:
                        proxies.append(f"http://{ip}:{port}")
            
            print(f"  Found {len(proxies)} India proxies")
            return proxies
        except Exception as e:
            print(f"  Failed: {e}")
            return []
    
    def fetch_from_free_proxy_list_india(self):
        """Fetch India proxies from free-proxy-list.net."""
        print("[FETCH] Getting India proxies from free-proxy-list.net...")
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'class': 'table table-striped table-bordered'})
            if not table:
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 8:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    country = cols[2].text.strip()
                    https = cols[6].text.strip()
                    
                    # Check if it's India
                    if country.upper() == 'IN' or 'INDIA' in country.upper():
                        protocol = 'https' if https == 'yes' else 'http'
                        proxy = f"{protocol}://{ip}:{port}"
                        proxies.append(proxy)
            
            print(f"  Found {len(proxies)} India proxies")
            return proxies
        except Exception as e:
            print(f"  Failed: {e}")
            return []
    
    def test_proxy(self, proxy_url, timeout=5):
        """Test if proxy is working and verify it's from India."""
        try:
            response = requests.get(
                'http://ip-api.com/json',  # Returns location info
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                country = data.get('country', '')
                country_code = data.get('countryCode', '')
                city = data.get('city', 'Unknown')
                ip = data.get('query', 'Unknown')
                
                # Verify it's actually from India
                if country_code == 'IN' or 'India' in country:
                    return True, ip, city
            
            return False, None, None
        except:
            return False, None, None
    
    def test_proxies_parallel(self, proxies, max_workers=20):
        """Test multiple India proxies in parallel."""
        print(f"\n[TEST] Testing {len(proxies)} India proxies...")
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in proxies
            }
            
            completed = 0
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    is_working, ip, city = future.result()
                    if is_working:
                        working.append(proxy)
                        print(f"  [OK] [{completed}/{len(proxies)}] {proxy} - IP: {ip} (City: {city})")
                    else:
                        if completed % 10 == 0:
                            print(f"  [{completed}/{len(proxies)}] Tested, {len(working)} working...")
                except:
                    pass
        
        print(f"\n[RESULT] Found {len(working)}/{len(proxies)} working India proxies")
        return working


def main():
    print("="*70)
    print("INDIA PROXY FETCHER")
    print("="*70)
    
    fetcher = IndiaProxyFetcher()
    all_proxies = []
    
    # Fetch from multiple sources
    all_proxies.extend(fetcher.fetch_from_proxyscrape_india())
    all_proxies.extend(fetcher.fetch_from_geonode_india())
    all_proxies.extend(fetcher.fetch_from_free_proxy_list_india())
    
    if not all_proxies:
        print("\n[ERROR] Could not fetch any India proxies!")
        print("\nTips:")
        print("1. India proxies are rare in free lists")
        print("2. Try paid services for guaranteed Indian IPs")
        print("3. Consider VPN services with Indian servers")
        return
    
    # Remove duplicates
    all_proxies = list(set(all_proxies))
    print(f"\n[INFO] Collected {len(all_proxies)} unique India proxies")
    
    # Test them
    working = fetcher.test_proxies_parallel(all_proxies)
    
    if working:
        # Save to file
        filename = 'india_proxies.txt'
        with open(filename, 'w') as f:
            for proxy in working:
                f.write(proxy + '\n')
        
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Found {len(working)} working India proxies")
        print(f"Saved to: {filename}")
        print("\nProxies:")
        for proxy in working:
            print(f"  {proxy}")
        
        print("\nTo use these proxies:")
        print("1. Add them to working_proxies.txt")
        print("2. Or use them separately with: ProxyManager('india_proxies.txt')")
    else:
        print("\n" + "="*70)
        print("NO WORKING INDIA PROXIES FOUND")
        print("="*70)
        print("\nReasons:")
        print("  - Free India proxies are very rare")
        print("  - High demand, low supply")
        print("  - Most get blocked quickly")
        
        print("\nAlternative Solutions:")
        print("1. Use paid proxy services with India location:")
        print("   - Bright Data (has India residential)")
        print("   - Smartproxy (has India datacenters)")
        print("   - IPRoyal (affordable India proxies)")
        
        print("\n2. Use VPN with India server:")
        print("   - NordVPN (has Mumbai, Bangalore servers)")
        print("   - ExpressVPN (has multiple India locations)")
        
        print("\n3. Mix India + nearby countries:")
        print("   - Try: Bangladesh (BD), Pakistan (PK), Sri Lanka (LK)")
        print("   - Run: python test_free_proxies.py (gets global proxies)")


if __name__ == "__main__":
    main()
