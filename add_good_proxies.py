#!/usr/bin/env python3
"""
Add Good IPs (1000-2000ms) to fast_proxies.txt
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def test_proxy_speed(proxy_url, timeout=5):
    """Test proxy speed."""
    try:
        start = time.time()
        response = requests.get(
            'http://httpbin.org/ip',
            proxies={'http': proxy_url, 'https': proxy_url},
            timeout=timeout
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            ip = response.json().get('origin', 'unknown')
            return True, elapsed, ip
    except:
        pass
    return False, None, None


def fetch_proxies():
    """Fetch proxies from multiple sources."""
    print("Fetching proxies from sources...")
    all_proxies = []
    
    # ProxyScrape
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
        for p in proxy_list[:100]:
            p = p.strip()
            if p:
                all_proxies.append(f"http://{p}")
        print(f"  ProxyScrape: {len(proxy_list[:100])} proxies")
    except:
        pass
    
    # Free Proxy List
    try:
        url = "https://free-proxy-list.net/"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    protocol = 'https' if https == 'yes' else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    all_proxies.append(proxy)
        print(f"  Free-proxy-list: {len(rows)} proxies")
    except:
        pass
    
    # Geonode
    try:
        url = "https://proxylist.geonode.com/api/proxy-list"
        params = {'limit': 500, 'page': 1, 'sort_by': 'lastChecked', 'sort_type': 'desc'}
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        for item in data.get('data', []):
            ip = item.get('ip')
            port = item.get('port')
            protocols = item.get('protocols', [])
            if ip and port and protocols:
                protocol = 'https' if 'https' in protocols else 'http'
                proxy = f"{protocol}://{ip}:{port}"
                all_proxies.append(proxy)
        print(f"  Geonode: {len(data.get('data', []))} proxies")
    except:
        pass
    
    return list(set(all_proxies))


def test_all(proxies):
    """Test all proxies."""
    print(f"\nTesting {len(proxies)} proxies...")
    results = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_proxy = {executor.submit(test_proxy_speed, proxy): proxy for proxy in proxies}
        
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            completed += 1
            
            try:
                is_working, speed, ip = future.result()
                if is_working:
                    results.append({'proxy': proxy, 'speed': speed, 'ip': ip})
                    if completed % 10 == 0:
                        print(f"  [{completed}/{len(proxies)}] Found {len(results)} working...")
            except:
                pass
    
    return sorted(results, key=lambda x: x['speed'])


# Main
print("="*80)
print("FETCHING GOOD IPs (1000-2000ms)")
print("="*80)

proxies = fetch_proxies()
print(f"\nCollected {len(proxies)} unique proxies")

results = test_all(proxies)
print(f"\nFound {len(results)} working proxies")

# Categorize
fast = [r for r in results if r['speed'] < 1000]
good = [r for r in results if 1000 <= r['speed'] < 2000]

print(f"\nFast (< 1000ms): {len(fast)}")
print(f"Good (1000-2000ms): {len(good)}")

# Read existing fast proxies
try:
    with open('fast_proxies.txt', 'r') as f:
        existing = set(line.strip() for line in f if line.strip())
except:
    existing = set()

# Add new good proxies
new_good = [r for r in good if r['proxy'] not in existing]

if new_good:
    with open('fast_proxies.txt', 'a') as f:
        f.write('\n# Good IPs (1000-2000ms)\n')
        for r in new_good:
            f.write(f"{r['proxy']}\n")
    
    print(f"\n✓ Added {len(new_good)} good IPs to fast_proxies.txt")
    print(f"\nTotal in file: {len(existing) + len(new_good)} proxies")
else:
    print("\nNo new good IPs found to add")

print("\nDone!")
