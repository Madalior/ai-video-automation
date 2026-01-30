"""
Check India Proxy Locations

Verifies the geographic location of India proxies.
"""

import requests

def check_proxy_location(proxy_url):
    """Check where a proxy IP is located."""
    try:
        # Extract IP from proxy URL
        ip = proxy_url.replace('http://', '').replace('https://', '').split(':')[0]
        
        print(f"\nChecking: {proxy_url}")
        print(f"IP: {ip}")
        
        # Method 1: Test through proxy
        try:
            response = requests.get(
                'http://ip-api.com/json',
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Proxy is WORKING")
                print(f"  Country: {data.get('country', 'Unknown')}")
                print(f"  Country Code: {data.get('countryCode', 'Unknown')}")
                print(f"  Region: {data.get('regionName', 'Unknown')}")
                print(f"  City: {data.get('city', 'Unknown')}")
                print(f"  ISP: {data.get('isp', 'Unknown')}")
                print(f"  Org: {data.get('org', 'Unknown')}")
                
                if data.get('countryCode') == 'IN':
                    print(f"  ✓ CONFIRMED: This is an INDIA IP! 🇮🇳")
                    return True
                else:
                    print(f"  ⚠ WARNING: This is NOT from India!")
                    return False
        except Exception as e:
            print(f"  ✗ Proxy not responding: {e}")
            
            # Method 2: Check IP directly (without going through proxy)
            print(f"\n  Checking IP {ip} directly...")
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  IP Location Info:")
                print(f"    Country: {data.get('country', 'Unknown')}")
                print(f"    City: {data.get('city', 'Unknown')}")
                print(f"    Region: {data.get('regionName', 'Unknown')}")
                
                if data.get('countryCode') == 'IN':
                    print(f"  ✓ IP is from INDIA (but proxy not responding)")
                else:
                    print(f"  ✗ IP is NOT from India")
            return False
                
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("="*70)
    print("INDIA PROXY LOCATION CHECKER")
    print("="*70)
    
    # Load India proxies
    try:
        with open('india_proxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("\n❌ india_proxies.txt not found!")
        print("Run: python fetch_india_proxies.py first")
        return
    
    if not proxies:
        print("\n❌ No proxies found in india_proxies.txt")
        return
    
    print(f"\nFound {len(proxies)} India proxies to check:\n")
    
    working_india = []
    
    for proxy in proxies:
        is_working = check_proxy_location(proxy)
        if is_working:
            working_india.append(proxy)
        print("-" * 70)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total proxies checked: {len(proxies)}")
    print(f"Working India proxies: {len(working_india)}")
    
    if working_india:
        print("\n✓ CONFIRMED INDIA PROXIES:")
        for proxy in working_india:
            print(f"  {proxy}")
        
        print("\nThese proxies are ready to use!")
        print("Add them to working_proxies.txt or use with:")
        print("  proxy_mgr = ProxyManager('india_proxies.txt')")
    else:
        print("\n⚠ No working India proxies found")
        print("The proxies may have died or are not actually from India")


if __name__ == "__main__":
    main()
