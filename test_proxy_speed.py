"""
Test Proxy Speed

Measures response time and speed for each proxy in working_proxies.txt
"""

import requests
import time

def test_proxy_speed(proxy_url, test_url='http://httpbin.org/ip', timeout=10):
    """
    Test proxy speed by measuring response time.
    
    Returns:
        (success, response_time_ms, ip_address)
    """
    try:
        start_time = time.time()
        
        response = requests.get(
            test_url,
            proxies={'http': proxy_url, 'https': proxy_url},
            timeout=timeout
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            ip = response.json().get('origin', 'Unknown')
            return True, response_time, ip
        else:
            return False, 0, None
            
    except Exception as e:
        return False, 0, None


def main():
    print("="*80)
    print("PROXY SPEED TEST")
    print("="*80)
    
    # Load proxies
    with open('working_proxies.txt', 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    print(f"\nTesting {len(proxies)} proxies...\n")
    
    results = []
    
    for i, proxy in enumerate(proxies, 1):
        print(f"[{i}/{len(proxies)}] Testing {proxy}...", end=" ")
        
        success, response_time, ip = test_proxy_speed(proxy)
        
        if success:
            print(f"✓ {response_time:.0f}ms (IP: {ip})")
            results.append({
                'proxy': proxy,
                'speed_ms': response_time,
                'ip': ip,
                'working': True
            })
        else:
            print(f"✗ FAILED")
            results.append({
                'proxy': proxy,
                'speed_ms': 0,
                'ip': None,
                'working': False
            })
    
    # Sort by speed (fastest first)
    working_results = [r for r in results if r['working']]
    working_results.sort(key=lambda x: x['speed_ms'])
    
    # Print summary
    print("\n" + "="*80)
    print("SPEED RANKING (Fastest to Slowest)")
    print("="*80)
    
    for i, result in enumerate(working_results, 1):
        speed = result['speed_ms']
        proxy = result['proxy']
        ip = result['ip']
        
        # Speed category
        if speed < 500:
            category = "FAST ⚡"
        elif speed < 1000:
            category = "GOOD ✓"
        elif speed < 2000:
            category = "OK"
        else:
            category = "SLOW ⚠"
        
        print(f"{i:2d}. {speed:6.0f}ms  {category:10s}  {proxy:30s}  (IP: {ip})")
    
    # Failed proxies
    failed = [r for r in results if not r['working']]
    if failed:
        print(f"\n{len(failed)} proxies failed:")
        for result in failed:
            print(f"  ✗ {result['proxy']}")
    
    # Statistics
    if working_results:
        avg_speed = sum(r['speed_ms'] for r in working_results) / len(working_results)
        fastest = working_results[0]['speed_ms']
        slowest = working_results[-1]['speed_ms']
        
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        print(f"Working proxies: {len(working_results)}/{len(proxies)}")
        print(f"Average speed:   {avg_speed:.0f}ms")
        print(f"Fastest:         {fastest:.0f}ms")
        print(f"Slowest:         {slowest:.0f}ms")
        print("\nRecommendation:")
        
        fast_count = sum(1 for r in working_results if r['speed_ms'] < 500)
        good_count = sum(1 for r in working_results if 500 <= r['speed_ms'] < 1000)
        
        if fast_count >= 3:
            print(f"  ✓ You have {fast_count} fast proxies! Great for production use.")
        elif good_count >= 5:
            print(f"  ✓ You have {good_count} good proxies. Suitable for most tasks.")
        else:
            print(f"  ⚠ Most proxies are slow. Consider getting fresh proxies.")
        
        print("\nSpeed Guide:")
        print("  < 500ms   = FAST ⚡ (Excellent)")
        print("  500-1000ms = GOOD ✓ (Suitable)")
        print("  1000-2000ms = OK (Acceptable)")
        print("  > 2000ms   = SLOW ⚠ (May cause timeouts)")


if __name__ == "__main__":
    main()
