"""
Proxy Manager for Free Proxy Rotation

Handles fetching, testing, and rotating free proxies for anti-bot detection.
"""

import requests
from bs4 import BeautifulSoup
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


class ProxyManager:
    """Manage free proxy rotation."""
    
    def __init__(self, proxy_file='working_proxies.txt'):
        """
        Initialize proxy manager.
        
        Args:
            proxy_file: Path to file with working proxies
        """
        self.proxy_file = proxy_file
        self.proxies = []
        self.current_index = 0
        
        # Load proxies if file exists
        if os.path.exists(proxy_file):
            self.load_proxies_from_file(proxy_file)
            print(f"[PROXY] Loaded {len(self.proxies)} proxies from {proxy_file}")
        else:
            print(f"[PROXY] No proxy file found. Use fetch_and_test_proxies() to get fresh proxies")
    
    def load_proxies_from_file(self, filepath):
        """Load proxies from file."""
        with open(filepath, 'r') as f:
            self.proxies = [line.strip() for line in f if line.strip()]
    
    def fetch_proxies_from_proxyscrape(self, protocol='http'):
        """Fetch proxies from ProxyScrape API."""
        try:
            url = "https://api.proxyscrape.com/v2/"
            params = {
                'request': 'get',
                'protocol': protocol,  # 'http', 'socks4', or 'socks5'
                'timeout': '5000',
                'country': 'all',
                'ssl': 'all',
                'anonymity': 'all'
            }
            
            response = requests.get(url, params=params, timeout=10)
            proxy_list = response.text.strip().split('\n')
            
            proxies = []
            for p in proxy_list[:50]:
                p = p.strip()
                if p:
                    if protocol == 'socks5':
                        proxies.append(f"socks5://{p}")
                    elif protocol == 'socks4':
                        proxies.append(f"socks4://{p}")
                    else:
                        proxies.append(f"http://{p}")
            
            return proxies
        except Exception as e:
            print(f"[PROXY] ProxyScrape API failed: {e}")
            return []
    
    def fetch_socks5_proxies(self):
        """Fetch SOCKS5 proxies from multiple sources."""
        print("[PROXY] Fetching SOCKS5 proxies...")
        all_socks5 = []
        
        # Source 1: ProxyScrape SOCKS5
        try:
            socks5 = self.fetch_proxies_from_proxyscrape(protocol='socks5')
            all_socks5.extend(socks5)
            print(f"  ProxyScrape SOCKS5: {len(socks5)} proxies")
        except:
            pass
        
        # Source 2: PubProxy API
        try:
            response = requests.get(
                "http://pubproxy.com/api/proxy",
                params={'type': 'socks5', 'limit': '20', 'format': 'txt'},
                timeout=10
            )
            if response.status_code == 200:
                for line in response.text.strip().split('\n'):
                    if line.strip():
                        all_socks5.append(f"socks5://{line.strip()}")
                print(f"  PubProxy SOCKS5: {len(response.text.strip().split())} proxies")
        except Exception as e:
            print(f"  PubProxy failed: {e}")
        
        print(f"[PROXY] Total SOCKS5 proxies collected: {len(all_socks5)}")
        return all_socks5
    
    def fetch_proxies_from_free_proxy_list(self):
        """Fetch proxies from free-proxy-list.net."""
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table = soup.find('table', {'class': 'table table-striped table-bordered'})
            if not table:
                return []
            
            proxies = []
            rows = table.find_all('tr')[1:][:50]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https = cols[6].text.strip()
                    
                    protocol = 'https' if https == 'yes' else 'http'
                    proxy = f"{protocol}://{ip}:{port}"
                    proxies.append(proxy)
            
            return proxies
        except Exception as e:
            print(f"[PROXY] free-proxy-list.net failed: {e}")
            return []
    
    def test_proxy(self, proxy_url, timeout=10, test_https=True):
        """
        Test if proxy is working.
        
        Args:
            proxy_url: Proxy URL (http://, socks5://, etc.)
            timeout: Request timeout
            test_https: If True, test against HTTPS site (required for Google)
        """
        try:
            # Use HTTPS test for Google/Gemini compatibility
            test_url = 'https://www.google.com' if test_https else 'http://httpbin.org/ip'
            
            response = requests.get(
                test_url,
                proxies={'http': proxy_url, 'https': proxy_url},
                timeout=timeout,
                allow_redirects=True
            )
            if response.status_code == 200:
                return True
        except requests.exceptions.ProxyError:
            pass
        except requests.exceptions.SSLError:
            pass
        except requests.exceptions.Timeout:
            pass
        except Exception:
            pass
        return False
    
    def test_proxies_parallel(self, proxies, max_workers=20):
        """Test multiple proxies in parallel."""
        print(f"[PROXY] Testing {len(proxies)} proxies...")
        working = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy): proxy 
                for proxy in proxies
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        working.append(proxy)
                except:
                    pass
        
        print(f"[PROXY] Found {len(working)}/{len(proxies)} working proxies")
        return working
    
    def fetch_and_test_proxies(self):
        """Fetch proxies from all sources and test them."""
        print("[PROXY] Fetching fresh proxies...")
        
        all_proxies = []
        all_proxies.extend(self.fetch_proxies_from_proxyscrape())
        all_proxies.extend(self.fetch_proxies_from_free_proxy_list())
        
        if not all_proxies:
            print("[PROXY] Failed to fetch proxies!")
            return []
        
        # Remove duplicates
        all_proxies = list(set(all_proxies))
        print(f"[PROXY] Collected {len(all_proxies)} unique proxies")
        
        # Test them
        working = self.test_proxies_parallel(all_proxies)
        
        if working:
            self.proxies = working
            self.save_proxies()
        
        return working
    
    def save_proxies(self, filename=None):
        """Save current proxies to file."""
        filename = filename or self.proxy_file
        with open(filename, 'w') as f:
            for proxy in self.proxies:
                f.write(proxy + '\n')
        print(f"[PROXY] Saved {len(self.proxies)} proxies to {filename}")
    
    def get_next_proxy(self):
        """Get next proxy in rotation (round-robin)."""
        if not self.proxies:
            print("[PROXY] No proxies available!")
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self):
        """Get random proxy."""
        if not self.proxies:
            print("[PROXY] No proxies available!")
            return None
        return random.choice(self.proxies)
    
    def get_stats(self):
        """Get proxy statistics."""
        return {
            'total_proxies': len(self.proxies),
            'current_index': self.current_index,
            'proxy_file': self.proxy_file
        }


class WorkerBatchProxy:
    """
    Worker-batch proxy manager.
    
    Strategy: One proxy handles multiple workers in a batch.
    - 1 Proxy → 2 Image Workers + 4 Video Workers (6 total)
    - Rotate to next proxy ONLY when all workers finish
    - More efficient than per-request rotation
    """
    
    def __init__(self, proxy_file='working_proxies.txt', image_workers=2, video_workers=4):
        """
        Initialize worker-batch proxy manager.
        
        Args:
            proxy_file: Path to proxy list
            image_workers: Number of image generation workers per batch
            video_workers: Number of video generation workers per batch
        """
        self.proxy_manager = ProxyManager(proxy_file)
        self.image_workers = image_workers
        self.video_workers = video_workers
        self.total_workers_per_batch = image_workers + video_workers
        
        # Current batch tracking
        self.current_proxy = None
        self.active_workers = 0
        self.completed_batches = 0
        
        import threading
        self.worker_lock = threading.Lock()
        
    def start_batch(self, validate=True, max_retries=5):
        """
        Start a new worker batch with fresh proxy.
        
        Tests proxy BEFORE assigning to workers to avoid dead proxies.
        
        Args:
            validate: Test proxy before using (default: True)
            max_retries: Max attempts to find working proxy (default: 5)
        
        Returns:
            str: Working proxy URL for this batch, or None if all failed
        """
        with self.worker_lock:
            retries = 0
            working_proxy = None
            
            while retries < max_retries:
                # Get next proxy
                candidate_proxy = self.proxy_manager.get_next_proxy()
                
                if candidate_proxy is None:
                    print("[ERROR] No proxies available!")
                    return None
                
                if validate:
                    print(f"[PROXY TEST] Testing: {candidate_proxy}...")
                    
                    # Test the proxy before using
                    if self.proxy_manager.test_proxy(candidate_proxy, timeout=5):
                        print(f"[PROXY OK] {candidate_proxy} is working!")
                        working_proxy = candidate_proxy
                        break
                    else:
                        print(f"[PROXY DEAD] {candidate_proxy} failed, trying next...")
                        retries += 1
                else:
                    # Skip validation
                    working_proxy = candidate_proxy
                    break
            
            if working_proxy is None:
                print(f"[ERROR] Failed to find working proxy after {max_retries} attempts!")
                return None
            
            # Assign working proxy to batch
            self.current_proxy = working_proxy
            self.active_workers = self.total_workers_per_batch
            
            print(f"[BATCH {self.completed_batches + 1}] Using proxy: {self.current_proxy}")
            print(f"  Workers: {self.total_workers_per_batch} ({self.image_workers} image + {self.video_workers} video)")
            
            return self.current_proxy
    
    def get_proxy(self):
        """Get current batch proxy. Auto-starts batch if none active."""
        if self.current_proxy is None:
            # Auto-start a new batch
            self.start_batch(validate=True, max_retries=3)
        return self.current_proxy
    
    def worker_complete(self):
        """
        Mark worker as complete. Rotate proxy if batch finished.
        
        Returns:
            bool: True if batch complete, False otherwise
        """
        with self.worker_lock:
            self.active_workers -= 1
            
            # Check if batch complete
            if self.active_workers == 0:
                self.completed_batches += 1
                print(f"[BATCH COMPLETE] All {self.total_workers_per_batch} workers finished. Rotating to next proxy...")
                
                # Reset for next batch
                self.current_proxy = None
                return True
            
            return False
    
    def get_stats(self):
        """Get batch statistics."""
        return {
            'total_proxies': self.proxy_manager.get_stats()['total_proxies'],
            'workers_per_batch': self.total_workers_per_batch,
            'image_workers': self.image_workers,
            'video_workers': self.video_workers,
            'completed_batches': self.completed_batches,
            'active_workers': self.active_workers,
            'current_proxy': self.current_proxy
        }
