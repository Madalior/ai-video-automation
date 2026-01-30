"""
Fetch SOCKS5 Proxies Script

Fetches fresh SOCKS5 proxies that support HTTPS tunneling.
Required for Google/Gemini services.

Usage:
    python fetch_socks5_proxies.py
    python fetch_socks5_proxies.py --test  # Also test proxies
"""

import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# SOCKS5 proxy sources - GitHub raw files (more reliable)
PROXY_SOURCES = [
    {
        'name': 'TheSpeedX SOCKS5',
        'url': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
        'protocol': 'socks5'
    },
    {
        'name': 'ShiftyTR SOCKS5',
        'url': 'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt',
        'protocol': 'socks5'
    },
    {
        'name': 'MuRongPIG SOCKS5',
        'url': 'https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt',
        'protocol': 'socks5'
    },
    {
        'name': 'ProxyScrape SOCKS5',
        'url': 'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all',
        'protocol': 'socks5'
    }
]


def fetch_proxies_from_source(source):
    """Fetch proxies from a single source."""
    try:
        response = requests.get(source['url'], timeout=15)
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            proxies = []
            protocol = source.get('protocol', 'socks5')
            for line in lines:
                line = line.strip()
                if line and ':' in line and not line.startswith('#'):
                    # Extract just IP:PORT
                    parts = line.split()
                    ip_port = parts[0] if parts else line
                    if ':' in ip_port:
                        proxies.append(f"{protocol}://{ip_port}")
            return proxies
    except Exception as e:
        print(f"  [ERROR] {source['name']}: {e}")
    return []


def test_proxy(proxy_url, timeout=15):
    """Test if proxy supports HTTPS (required for Google)."""
    try:
        response = requests.get(
            'https://www.google.com',
            proxies={'http': proxy_url, 'https': proxy_url},
            timeout=timeout,
            allow_redirects=True
        )
        return response.status_code == 200
    except:
        return False


def test_proxies_parallel(proxies, max_workers=20):
    """Test multiple proxies in parallel."""
    print(f"\n[TESTING] Testing {len(proxies)} proxies against HTTPS...")
    working = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(test_proxy, proxy): proxy 
            for proxy in proxies
        }
        
        done = 0
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            done += 1
            try:
                if future.result():
                    working.append(proxy)
                    print(f"  [{done}/{len(proxies)}] {proxy} - OK")
                else:
                    print(f"  [{done}/{len(proxies)}] {proxy} - FAILED")
            except Exception as e:
                print(f"  [{done}/{len(proxies)}] {proxy} - ERROR: {e}")
    
    return working


def main():
    print("=" * 60)
    print("SOCKS5 PROXY FETCHER")
    print("=" * 60)
    
    should_test = '--test' in sys.argv
    
    # Fetch from all sources
    all_proxies = []
    
    for source in PROXY_SOURCES:
        print(f"\n[FETCHING] {source['name']}...")
        proxies = fetch_proxies_from_source(source)
        print(f"  Found: {len(proxies)} proxies")
        all_proxies.extend(proxies)
    
    # Remove duplicates
    all_proxies = list(set(all_proxies))
    print(f"\n[TOTAL] {len(all_proxies)} unique proxies collected")
    
    if not all_proxies:
        print("[ERROR] No proxies found!")
        return
    
    # Test if requested
    if should_test:
        working = test_proxies_parallel(all_proxies[:50])  # Test max 50
        print(f"\n[RESULT] {len(working)}/{len(all_proxies[:50])} proxies work with HTTPS")
        
        if working:
            # Save working proxies
            with open('socks5_proxies.txt', 'w') as f:
                for proxy in working:
                    f.write(proxy + '\n')
            print(f"[SAVED] {len(working)} working SOCKS5 proxies to socks5_proxies.txt")
    else:
        # Save all proxies (untested)
        with open('socks5_proxies.txt', 'w') as f:
            for proxy in all_proxies:
                f.write(proxy + '\n')
        print(f"\n[SAVED] {len(all_proxies)} SOCKS5 proxies to socks5_proxies.txt")
        print("[TIP] Run with --test to verify proxies work with HTTPS")
    
    print("\n" + "=" * 60)
    print("[USAGE] In master_manager.py:")
    print("  python master_manager.py --proxy-file socks5_proxies.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()
