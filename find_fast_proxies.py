#!/usr/bin/env python3
"""
Fetch and Test 200+ Proxies - Get Only Fast IPs

This script fetches proxies from multiple sources and returns only fast ones.
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class FastProxyFinder:
    """Find fast proxies from 200+ sources."""
    
    def __init__(self):
        self.all_proxies = []
        self.fast_proxies = []
        
    def fetch_from_proxyscrape(self):
        """Fetch from ProxyScrape API - up to 100 proxies."""
        print("[1/5] Fetching from ProxyScrape API...")
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
            
            response = requests.get(url, params=params, timeout=15)
            proxy_list = response.text.strip().split('\n')
            
            proxies = []
            for p in proxy_list[:100]:
                p = p.strip()
                if p:
                    proxies.append(f"http://{p}")
            
            print(f"  ✓ Got {len(proxies)} proxies from ProxyScrape")
            return proxies
        except Exception as e:
            print(f"  ✗ ProxyScrape failed: {e}")
            return []
    
    def fetch_from_free_proxy_list(self):
        """Fetch from free-proxy-list.net - ~300 proxies."""
        print("[2/5] Fetching from free-proxy-list.net...")
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table')
            if not table:
                print("  ✗ No table found")
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    protocol = 'https' if https == 'yes' else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    proxies.append(proxy)
            
            print(f"  ✓ Got {len(proxies)} proxies from free-proxy-list.net")
            return proxies
        except Exception as e:
            print(f"  ✗ free-proxy-list.net failed: {e}")
            return []
    
    def fetch_from_geonode(self):
        """Fetch from Geonode API - up to 500 proxies."""
        print("[3/5] Fetching from Geonode API...")
        try:
            url = "https://proxylist.geonode.com/api/proxy-list"
            params = {
                'limit': 500,
                'page': 1,
                'sort_by': 'lastChecked',
                'sort_type': 'desc'
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            proxies = []
            for item in data.get('data', []):
                ip = item.get('ip')
                port = item.get('port')
                protocols = item.get('protocols', [])
                
                if ip and port and protocols:
                    protocol = 'https' if 'https' in protocols else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    proxies.append(proxy)
            
            print(f"  ✓ Got {len(proxies)} proxies from Geonode")
            return proxies
        except Exception as e:
            print(f"  ✗ Geonode failed: {e}")
            return []
    
    def fetch_from_proxy_list_download(self):
        """Fetch from proxy-list.download."""
        print("[4/5] Fetching from proxy-list.download...")
        try:
            url = "https://www.proxy-list.download/api/v1/get?type=http"
            response = requests.get(url, timeout=15)
            
            proxies = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and ':' in line:
                    proxies.append(f"http://{line}")
            
            print(f"  ✓ Got {len(proxies)} proxies from proxy-list.download")
            return proxies
        except Exception as e:
            print(f"  ✗ proxy-list.download failed: {e}")
            return []
    
    def fetch_from_proxynova(self):
        """Fetch from ProxyNova."""
        print("[5/5] Fetching from ProxyNova...")
        try:
            url = "https://www.proxynova.com/proxy-server-list/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            proxies = []
            table = soup.find('table', {'id': 'tbl_proxy_list'})
            if table:
                rows = table.find_all('tr')[1:]
                for row in rows[:100]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        if ip and port:
                            proxies.append(f"http://{ip}:{port}")
            
            print(f"  ✓ Got {len(proxies)} proxies from ProxyNova")
            return proxies
        except Exception as e:
            print(f"  ✗ ProxyNova failed: {e}")
            return []
    
    def test_proxy_speed(self, proxy_url, timeout=5):
        """Test proxy speed."""
        try:
            start = time.time()
            response = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout
            )
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                ip = response.json().get('origin', 'unknown')
                return True, elapsed, ip
        except:
            pass
        return False, None, None
    
    def test_all_proxies(self, proxies, max_workers=50):
        """Test all proxies in parallel."""
        print(f"\n[TESTING] Testing {len(proxies)} proxies with {max_workers} workers...")
        print("This may take a few minutes...\n")
        
        results = []
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_proxy_speed, proxy): proxy 
                for proxy in proxies
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                completed += 1
                
                try:
                    is_working, speed, ip = future.result()
                    
                    if is_working:
                        results.append({
                            'proxy': proxy,
                            'speed': speed,
                            'ip': ip
                        })
                        
                        if speed < 1000:
                            category = "FAST"
                        elif speed < 2000:
                            category = "GOOD"
                        else:
                            category = "OK"
                        
                        print(f"  [{completed}/{len(proxies)}] ✓ {category:6s} {speed:6.0f}ms  {proxy}")
                    else:
                        if completed % 10 == 0:
                            print(f"  [{completed}/{len(proxies)}] Progress...")
                except:
                    pass
        
        return results
    
    def fetch_all_proxies(self):
        """Fetch from all sources."""
        print("="*80)
        print("FETCHING PROXIES FROM MULTIPLE SOURCES")
        print("="*80)
        
        all_proxies = []
        all_proxies.extend(self.fetch_from_proxyscrape())
        all_proxies.extend(self.fetch_from_free_proxy_list())
        all_proxies.extend(self.fetch_from_geonode())
        all_proxies.extend(self.fetch_from_proxy_list_download())
        all_proxies.extend(self.fetch_from_proxynova())
        
        # Remove duplicates
        self.all_proxies = list(set(all_proxies))
        
        print(f"\n{'='*80}")
        print(f"TOTAL UNIQUE PROXIES COLLECTED: {len(self.all_proxies)}")
        print("="*80)
        
        return self.all_proxies
    
    def find_fast_proxies(self, max_speed=1000):
        """Find and return only fast proxies."""
        # Fetch all proxies
        proxies = self.fetch_all_proxies()
        
        if not proxies:
            print("\n[ERROR] No proxies found!")
            return []
        
        # Test all proxies
        results = self.test_all_proxies(proxies)
        
        # Sort by speed
        results.sort(key=lambda x: x['speed'])
        
        # Filter fast ones
        fast_proxies = [r for r in results if r['speed'] < max_speed]
        
        # Display results
        print(f"\n{'='*80}")
        print(f"FAST PROXIES (< {max_speed}ms)")
        print("="*80)
        
        if fast_proxies:
            for i, result in enumerate(fast_proxies, 1):
                print(f"{i:3d}. {result['speed']:6.0f}ms  {result['proxy']:40s}  (IP: {result['ip']})")
        else:
            print("No fast proxies found!")
        
        # Show all working proxies stats
        print(f"\n{'='*80}")
        print("STATISTICS")
        print("="*80)
        print(f"Total fetched:   {len(self.all_proxies)}")
        print(f"Working:         {len(results)} ({len(results)/len(self.all_proxies)*100:.1f}%)")
        print(f"Fast (< 1000ms): {len(fast_proxies)}")
        
        if results:
            avg_speed = sum(r['speed'] for r in results) / len(results)
            print(f"Average speed:   {avg_speed:.0f}ms")
            print(f"Fastest:         {results[0]['speed']:.0f}ms")
            print(f"Slowest:         {results[-1]['speed']:.0f}ms")
        
        # Save fast proxies
        if fast_proxies:
            with open('fast_proxies.txt', 'w') as f:
                for result in fast_proxies:
                    f.write(result['proxy'] + '\n')
            print(f"\n✓ Saved {len(fast_proxies)} fast proxies to fast_proxies.txt")
        
        return fast_proxies


if __name__ == "__main__":
    finder = FastProxyFinder()
    fast_proxies = finder.find_fast_proxies(max_speed=1000)
    
    print("\n" + "="*80)
    print("DONE!")
    print("="*80)
    print(f"\nFound {len(fast_proxies)} fast proxies ready to use!")
