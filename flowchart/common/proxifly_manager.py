"""
Proxifly API Integration

Uses Proxifly (proxifly.dev) for reliable HTTPS/SOCKS5 proxies.
Supports rotating proxies from 100+ countries.

Usage:
    from flowchart.common.proxifly_manager import ProxiflyManager
    
    pm = ProxiflyManager(api_key="YOUR_API_KEY")
    proxies = pm.get_proxies(quantity=10, https=True)
"""

import requests
from typing import List, Dict, Optional
import os


class ProxiflyManager:
    """
    Proxifly API Manager for reliable proxy rotation.
    
    Features:
    - HTTPS proxies that work with Google/Gemini
    - SOCKS5 proxies for advanced tunneling
    - Country-specific proxies (100+ countries)
    - Rotating IP addresses
    """
    
    API_URL = "https://api.proxifly.dev/get-proxy"
    
    def __init__(self, api_key: str = None):
        """
        Initialize Proxifly manager.
        
        Args:
            api_key: Proxifly API key (or set PROXIFLY_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('PROXIFLY_API_KEY')
        if not self.api_key:
            raise ValueError("Proxifly API key required. Pass api_key or set PROXIFLY_API_KEY")
        
        self.proxies = []
        self.current_index = 0
        print(f"[PROXIFLY] Manager initialized")
    
    def get_proxies(
        self, 
        quantity: int = 20,
        https: bool = True,
        countries: List[str] = None,
        protocol: str = None  # 'http', 'socks4', 'socks5', or None for any
    ) -> List[Dict]:
        """
        Fetch proxies from Proxifly API.
        
        Args:
            quantity: Number of proxies to fetch (max 100)
            https: Only get HTTPS-capable proxies
            countries: List of country codes (e.g., ['US', 'IN'])
            protocol: Specific protocol or None for any
        
        Returns:
            List of proxy dictionaries
        """
        print(f"[PROXIFLY] Fetching {quantity} proxies...")
        
        payload = {
            'apiKey': self.api_key,
            'quantity': min(quantity, 100),
            'https': https
        }
        
        if countries:
            payload['country'] = countries
        
        if protocol:
            payload['protocol'] = protocol
        
        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle single proxy response
                if 'proxy' in data:
                    proxies = [data]
                # Handle multiple proxies response
                elif 'proxies' in data:
                    proxies = data['proxies']
                elif isinstance(data, list):
                    proxies = data
                else:
                    proxies = [data]
                
                self.proxies = proxies
                print(f"[PROXIFLY] Got {len(proxies)} proxies")
                return proxies
            else:
                print(f"[PROXIFLY ERROR] Status {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"[PROXIFLY ERROR] {e}")
            return []
    
    def get_proxy_url(self, proxy_dict: Dict = None) -> Optional[str]:
        """
        Convert proxy dict to URL format for requests library.
        
        Args:
            proxy_dict: Proxy dictionary from API, or None to use next in rotation
        
        Returns:
            Proxy URL string (e.g., 'socks5://1.2.3.4:1080')
        """
        if proxy_dict is None:
            if not self.proxies:
                self.get_proxies()
            if not self.proxies:
                return None
            proxy_dict = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
        
        proxy_str = proxy_dict.get('proxy', '')
        return proxy_str if proxy_str else None
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy URL in rotation."""
        return self.get_proxy_url()
    
    def test_proxy(self, proxy_url: str, timeout: int = 15) -> bool:
        """
        Test if proxy works with HTTPS (Google).
        
        Args:
            proxy_url: Proxy URL to test
            timeout: Request timeout
        
        Returns:
            True if proxy works
        """
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
    
    def get_working_proxy(self, max_attempts: int = 5) -> Optional[str]:
        """
        Get a working proxy that passes HTTPS test.
        
        Args:
            max_attempts: Maximum proxies to test
        
        Returns:
            Working proxy URL or None
        """
        if not self.proxies:
            self.get_proxies(quantity=20, https=True)
        
        for i in range(min(max_attempts, len(self.proxies))):
            proxy_url = self.get_next_proxy()
            if proxy_url:
                print(f"  [{i+1}/{max_attempts}] Testing {proxy_url}...", end=" ")
                if self.test_proxy(proxy_url):
                    print("OK")
                    return proxy_url
                else:
                    print("FAILED")
        
        return None
    
    def get_stats(self) -> Dict:
        """Get proxy statistics."""
        return {
            'total_proxies': len(self.proxies),
            'current_index': self.current_index,
            'has_api_key': bool(self.api_key)
        }


# Convenience function
def fetch_proxifly_proxies(api_key: str, quantity: int = 20) -> List[str]:
    """
    Quick fetch of proxy URLs from Proxifly.
    
    Args:
        api_key: Proxifly API key
        quantity: Number of proxies
    
    Returns:
        List of proxy URL strings
    """
    pm = ProxiflyManager(api_key=api_key)
    proxies = pm.get_proxies(quantity=quantity, https=True)
    return [pm.get_proxy_url(p) for p in proxies if pm.get_proxy_url(p)]


if __name__ == "__main__":
    # Test with API key
    import sys
    
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('PROXIFLY_API_KEY')
    
    if not api_key:
        print("Usage: python proxifly_manager.py <API_KEY>")
        sys.exit(1)
    
    print("=" * 60)
    print("PROXIFLY API TEST")
    print("=" * 60)
    
    pm = ProxiflyManager(api_key=api_key)
    
    # Fetch proxies
    proxies = pm.get_proxies(quantity=5, https=True)
    
    print(f"\nProxies received: {len(proxies)}")
    for i, p in enumerate(proxies[:5]):
        print(f"  {i+1}. {p.get('proxy', 'N/A')} ({p.get('country', 'Unknown')})")
    
    # Test a proxy
    print("\nTesting proxy connectivity...")
    working = pm.get_working_proxy(max_attempts=3)
    
    if working:
        print(f"\n✅ Working proxy found: {working}")
    else:
        print("\n❌ No working proxy found")
    
    print("=" * 60)
