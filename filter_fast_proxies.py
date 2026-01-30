"""
Filter Fast Proxies (< 500ms)

Tests all proxies and keeps only those with response time below 500ms.
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Original proxy list
PROXY_LIST = """178.170.43.121:8082
8.219.97.248:80
195.26.224.135:80
154.3.236.202:3128
190.128.241.102:80
20.78.26.206:8561
20.27.11.248:8561
174.138.119.88:80
89.116.88.19:80
203.115.101.61:82
5.161.155.252:80
154.31.113.209:80
219.93.101.62:80
103.253.43.144:80
154.65.39.7:80
133.18.234.13:80
217.217.254.94:80
188.65.89.225:80
182.53.202.208:8080
23.247.136.254:80
130.185.122.199:8090
50.122.86.118:80
190.119.132.62:80
43.209.8.12:93
160.20.55.235:8080
190.119.132.61:80
20.210.113.32:8123
20.111.54.16:8123
162.245.85.36:80
20.210.39.153:8561
77.242.177.57:3128
89.58.57.45:80
213.33.126.130:80
194.158.203.14:80
54.90.159.174:22229
41.191.203.163:80
219.93.101.63:80
200.33.20.25:80
212.114.194.73:80
212.114.194.79:80
190.116.28.148:80
219.93.101.60:80
47.74.157.194:80
183.110.216.128:8090
213.73.25.230:8080
104.197.218.238:8080
197.221.240.178:80
211.230.49.122:3128
147.75.34.105:443
213.143.113.82:80
41.220.22.7:80
27.34.242.98:80
103.125.31.222:80
174.136.204.40:80
46.47.197.210:3128
200.174.198.32:8888
156.146.56.231:8081
212.114.194.72:80
35.202.49.74:80
97.74.87.226:80
47.250.177.202:8090
141.147.9.254:80
219.249.37.107:8382
51.161.131.235:8080
20.27.14.220:8561
154.17.228.122:80
103.205.64.153:80
150.107.140.238:3128
31.220.78.244:80
197.221.249.195:80
213.142.156.97:80
154.17.224.118:80
38.60.196.214:80
172.237.73.24:80
202.133.88.173:80
188.166.222.51:80
135.148.120.6:80
175.139.233.76:80
210.223.44.230:3128
117.54.114.99:80
212.114.194.76:80
81.169.213.169:8888
89.58.55.33:80
124.108.6.20:8085
5.75.198.72:80
52.188.28.218:3128
62.113.119.14:8080
197.221.237.248:80
197.221.249.199:80
212.114.194.75:80
183.110.216.159:8090
80.74.54.148:3128
147.231.163.133:80
154.31.115.210:80
84.39.112.144:3128
193.53.127.169:80
95.216.49.153:80
41.220.16.215:80
197.221.240.246:80
212.114.194.74:80
185.200.37.37:8080
201.220.112.98:999
103.231.177.120:5020
103.255.243.10:8080
103.145.57.25:8080
190.60.48.171:999
38.156.235.34:999
194.186.248.97:80
38.194.250.66:999
195.158.8.123:3128
156.246.90.81:80
47.251.87.199:8008
31.132.151.158:8080
188.245.218.56:80
139.99.237.62:80
162.240.19.30:80
41.220.16.214:80
91.99.181.245:80
185.85.111.18:80
157.180.118.86:80
176.61.151.123:80
209.135.168.41:80
32.223.6.94:80
72.10.164.178:2493
27.147.137.234:9108
201.222.50.218:80
50.203.147.157:80
41.191.203.164:80
212.114.194.78:80
41.191.203.162:80
219.65.73.81:80
197.221.249.198:80
41.220.16.213:80
160.251.142.232:80
47.56.110.204:8989
41.191.203.167:80
212.34.144.253:80
134.209.29.120:80
143.42.66.91:80
176.126.164.213:80
197.221.234.253:80
20.27.15.111:8561
192.145.31.160:4145
190.58.248.86:80
20.205.61.143:80
20.24.43.214:80
192.73.244.36:80
109.120.135.230:2030
213.157.6.50:80
162.223.90.144:80
8.212.177.126:8080
197.221.234.252:80
172.193.178.226:80
34.44.49.215:80
45.59.186.60:80
117.54.114.33:80
175.101.240.38:80
163.5.128.210:14270
66.29.154.103:3128
103.82.23.118:5178
181.48.234.214:8080
38.52.209.229:999
175.106.14.126:3128
190.121.157.41:999
36.37.180.40:8080
160.20.128.27:1080
201.230.121.86:999
201.218.150.4:999
168.194.64.219:8888
8.213.151.128:3128
8.209.255.13:3128
47.89.184.18:3128
41.223.119.156:3128
63.250.32.220:3128
63.250.32.221:3128
95.213.217.168:52004
37.58.48.214:2255
178.130.47.129:1082
149.129.255.179:9050
47.250.159.65:64
140.245.105.90:8080
20.78.118.91:8561
50.203.147.153:80
31.56.137.189:6265
107.175.135.52:6493
50.203.147.159:80
197.221.240.240:80
72.10.160.173:10073
72.10.160.91:5975
147.91.22.150:80
39.109.113.97:4090
37.27.6.46:80
45.92.108.112:80
20.27.15.49:8561
137.184.96.68:80
41.220.16.218:80
51.178.76.203:80
104.251.81.224:14270
188.40.57.101:80
62.99.138.162:80
101.47.16.15:7890
212.47.232.28:80
43.252.238.222:8080
200.24.130.150:999
193.43.145.124:8080
160.30.83.10:83"""

def test_proxy_speed(proxy_str, timeout=10):
    """Test proxy speed and return response time."""
    try:
        proxy_url = f"http://{proxy_str}"
        start_time = time.time()
        
        response = requests.get(
            'http://httpbin.org/ip',
            proxies={'http': proxy_url, 'https': proxy_url},
            timeout=timeout
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms
        
        if response.status_code == 200:
            return True, response_time
        
        return False, 0
    except:
        return False, 0


def main():
    print("="*80)
    print("FILTERING FAST PROXIES (< 500ms)")
    print("="*80)
    
    # Parse proxies
    proxies = [line.strip() for line in PROXY_LIST.strip().split('\n') if line.strip()]
    proxies = [p for p in proxies if p not in ['0.0.0.0:80', '127.0.0.7:80']]  # Skip invalid
    
    print(f"\nTesting {len(proxies)} proxies in parallel...")
    print("Target: < 500ms (FAST)\n")
    
    fast_proxies = []
    slow_proxies = []
    failed_proxies = []
    
    # Test all proxies in parallel
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_proxy = {
            executor.submit(test_proxy_speed, proxy): proxy 
            for proxy in proxies
        }
        
        completed = 0
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            completed += 1
            
            try:
                is_working, speed = future.result()
                
                if is_working:
                    if speed < 500:
                        fast_proxies.append((proxy, speed))
                        print(f"✓ [{completed}/{len(proxies)}] {proxy:30s} {speed:6.0f}ms ⚡ FAST")
                    else:
                        slow_proxies.append((proxy, speed))
                        if completed % 10 == 0:
                            print(f"  [{completed}/{len(proxies)}] Progress: {len(fast_proxies)} fast, {len(slow_proxies)} slow, {len(failed_proxies)} failed")
                else:
                    failed_proxies.append(proxy)
                    
            except:
                failed_proxies.append(proxy)
    
    # Sort fast proxies by speed
    fast_proxies.sort(key=lambda x: x[1])
    
    # Save fast proxies
    if fast_proxies:
        with open('fast_proxies.txt', 'w') as f:
            for proxy, speed in fast_proxies:
                f.write(f"http://{proxy}\n")
        
        print(f"\n✓ Saved {len(fast_proxies)} fast proxies to: fast_proxies.txt")
    
    # Print summary
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Total tested: {len(proxies)}")
    print(f"FAST (< 500ms): {len(fast_proxies)} proxies ⚡")
    print(f"SLOW (>= 500ms): {len(slow_proxies)} proxies ⚠")
    print(f"FAILED: {len(failed_proxies)} proxies ✗")
    
    # Generate Full Markdown Report
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open('proxy_speed_report.md', 'w') as f:
        f.write(f"# Proxy Speed Report\n")
        f.write(f"Generated: {timestamp}\n\n")
        
        f.write(f"## ⚡ FAST PROXIES (< 500ms)\n")
        if fast_proxies:
            f.write("| Rank | Proxy | Speed |\n")
            f.write("|------|-------|-------|\n")
            for i, (proxy, speed) in enumerate(fast_proxies, 1):
                f.write(f"| {i} | {proxy} | **{speed:.0f}ms** |\n")
        else:
            f.write("No fast proxies found.\n")
            
        f.write(f"\n## ⚠ SLOW PROXIES (>= 500ms)\n")
        if slow_proxies:
            # Sort slow proxies too
            slow_proxies.sort(key=lambda x: x[1])
            f.write("| Rank | Proxy | Speed |\n")
            f.write("|------|-------|-------|\n")
            for i, (proxy, speed) in enumerate(slow_proxies, 1):
                f.write(f"| {i} | {proxy} | {speed:.0f}ms |\n")
        else:
            f.write("No slow proxies found.\n")
            
        f.write(f"\n## ✗ FAILED PROXIES\n")
        if failed_proxies:
            for proxy in failed_proxies:
                f.write(f"- {proxy}\n")
        else:
            f.write("No failed proxies.\n")
    
    print(f"\n✓ Full report saved to: proxy_speed_report.md")

    if fast_proxies:
        print(f"\n⚡ FAST PROXIES (See report for full list):")
        for i, (proxy, speed) in enumerate(fast_proxies, 1):
            print(f"{i:2d}. {proxy:30s} {speed:6.0f}ms")
            
        # Update working_proxies.txt
        with open('working_proxies.txt', 'w') as f:
            for proxy, speed in fast_proxies:
                f.write(f"http://{proxy}\n")
        print("\n✓ Updated working_proxies.txt with only FAST proxies")
    else:
        print("\n⚠ No proxies found under 500ms")


if __name__ == "__main__":
    main()
