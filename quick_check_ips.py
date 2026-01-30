"""Quick check of India proxy IPs"""
import requests

proxies = [
    "27.34.242.98",
    "219.65.73.81", 
    "175.101.240.38"
]

print("="*70)
print("INDIA PROXY IP LOCATIONS")
print("="*70)

for ip in proxies:
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = r.json()
        print(f"\nIP: {ip}")
        print(f"  Country: {data.get('country', 'Unknown')}")
        print(f"  City: {data.get('city', 'Unknown')}")
        print(f"  Region: {data.get('regionName', 'Unknown')}")
        print(f"  ISP: {data.get('isp', 'Unknown')}")
        
        if data.get('countryCode') == 'IN':
            print(f"  ✓ CONFIRMED INDIA IP 🇮🇳")
        else:
            print(f"  ⚠ NOT from India ({data.get('countryCode')})")
    except Exception as e:
        print(f"\nIP: {ip} - Error: {e}")

print("\n" + "="*70)
