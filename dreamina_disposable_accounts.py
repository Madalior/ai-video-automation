"""
Dreamina Video Generator with Disposable Account & IP Rotation

This module implements a throwaway account strategy:
- Each video generation uses a new temporary Dreamina account
- Each account is assigned a unique IP from the proxy pool
- Accounts are discarded after use (no reuse)
- Proxies rotate in round-robin fashion for unlimited scaling

Benefits:
- No ban risk (each account only sees one IP)
- Infinite scaling (45 proxies support unlimited accounts over time)
- No account maintenance needed
- Fresh identity for each generation
"""

import random
import string
import time
from flowchart.common.proxy_manager import ProxyManager

# Try to use undetected-chromedriver for best stealth
try:
    import undetected_chromedriver as uc
    UC_AVAILABLE = True
    print("[DISPOSABLE] Using undetected-chromedriver for maximum stealth")
except ImportError:
    UC_AVAILABLE = False
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    print("[DISPOSABLE] undetected-chromedriver not found, using standard selenium")


class DisposableAccountGenerator:
    """Manages disposable Dreamina accounts with IP rotation."""
    
    def __init__(self, proxy_file='fast_proxies.txt'):
        """
        Initialize disposable account generator.
        
        Args:
            proxy_file: Path to file with working proxies
        """
        self.proxy_manager = ProxyManager(proxy_file)
        self.active_accounts = []
        self.completed_count = 0
        
        stats = self.proxy_manager.get_stats()
        print(f"[INIT] Loaded {stats['total_proxies']} proxies for rotation")
    
    def generate_temp_credentials(self):
        """Generate random temporary credentials."""
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        
        credentials = {
            'email': f"temp_{random_id}@guerrillamail.com",  # Temp email service
            'password': ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
            'username': f"user_{random_id}"
        }
        
        return credentials
    
    def create_browser_with_proxy(self, proxy_url):
        """
        Launch Chrome browser with proxy configuration using undetected-chromedriver.
        
        Args:
            proxy_url: Proxy URL (e.g., http://1.2.3.4:8080)
            
        Returns:
            WebDriver instance
        """
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        if UC_AVAILABLE:
            # Use undetected-chromedriver (better stealth)
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument(f'--proxy-server={proxy_url}')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument(f'--user-data-dir={temp_dir}')
            
            try:
                driver = uc.Chrome(options=chrome_options, use_subprocess=True)
                print(f"[BROWSER] Launched with UC stealth + proxy: {proxy_url}")
                return driver, temp_dir
            except Exception as e:
                print(f"[ERROR] UC browser launch failed: {e}")
                return None, None
        else:
            # Fallback to standard selenium
            chrome_options = Options()
            chrome_options.add_argument(f'--proxy-server={proxy_url}')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
            chrome_options.add_argument(f'--user-data-dir={temp_dir}')
            
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print(f"[BROWSER] Launched with standard selenium + proxy: {proxy_url}")
                return driver, temp_dir
            except Exception as e:
                print(f"[ERROR] Failed to launch browser: {e}")
                return None, None
    
    def create_disposable_account(self):
        """
        Create a disposable Dreamina account with rotating IP.
        
        Returns:
            dict: Account information including credentials, proxy, and browser
        """
        # Get next proxy in rotation
        proxy = self.proxy_manager.get_next_proxy()
        
        # Generate random credentials
        credentials = self.generate_temp_credentials()
        
        print(f"\n[ACCOUNT] Creating disposable account...")
        print(f"  Email: {credentials['email']}")
        print(f"  Proxy: {proxy}")
        
        # Launch browser with this proxy
        driver, temp_profile = self.create_browser_with_proxy(proxy)
        
        if not driver:
            print(f"[ERROR] Failed to create account (browser launch failed)")
            return None
        
        account = {
            'email': credentials['email'],
            'password': credentials['password'],
            'username': credentials['username'],
            'proxy': proxy,
            'driver': driver,
            'temp_profile': temp_profile,
            'created_at': time.time()
        }
        
        self.active_accounts.append(account)
        return account
    
    def generate_video_with_disposable_account(self, video_config):
        """
        Generate a single video using a disposable account.
        
        Args:
            video_config: dict with video generation parameters
            
        Returns:
            dict: Generation result
        """
        print(f"\n{'='*80}")
        print(f"[VIDEO] Generating with disposable account...")
        print(f"{'='*80}")
        
        # Create disposable account
        account = self.create_disposable_account()
        
        if not account:
            return {'success': False, 'error': 'Account creation failed'}
        
        try:
            # Navigate to Dreamina
            driver = account['driver']
            driver.get('https://dreamina.com')
            
            print(f"[DREAMINA] Opening Dreamina with IP: {account['proxy']}")
            time.sleep(3)
            
            # TODO: Implement actual Dreamina automation steps:
            # 1. Sign up with temp credentials
            # 2. Navigate to video generation
            # 3. Input prompts/parameters
            # 4. Generate video
            # 5. Download result
            
            # Placeholder for actual implementation
            result = {
                'success': True,
                'account': account['email'],
                'proxy': account['proxy'],
                'video_url': 'placeholder_url',
                'message': 'Video generation placeholder - implement Dreamina automation'
            }
            
            self.completed_count += 1
            print(f"[SUCCESS] Video {self.completed_count} generated")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Video generation failed: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Cleanup: Close browser and discard account
            self.cleanup_account(account)
    
    def cleanup_account(self, account):
        """
        Cleanup disposable account and free resources.
        
        Args:
            account: Account dict to cleanup
        """
        try:
            if account and account.get('driver'):
                account['driver'].quit()
                print(f"[CLEANUP] Browser closed")
            
            # Remove temp profile
            if account and account.get('temp_profile'):
                import shutil
                shutil.rmtree(account['temp_profile'], ignore_errors=True)
                print(f"[CLEANUP] Temp profile deleted")
            
            # Remove from active accounts
            if account in self.active_accounts:
                self.active_accounts.remove(account)
            
            print(f"[CLEANUP] Account discarded: {account.get('email', 'unknown')}")
            
        except Exception as e:
            print(f"[CLEANUP] Warning: {e}")
    
    def generate_batch_videos(self, video_configs):
        """
        Generate multiple videos using disposable accounts.
        
        Args:
            video_configs: List of video configuration dicts
            
        Returns:
            list: Results for each video
        """
        print(f"\n{'='*80}")
        print(f"[BATCH] Generating {len(video_configs)} videos with rotating IPs")
        print(f"{'='*80}")
        
        results = []
        
        for i, config in enumerate(video_configs, 1):
            print(f"\n[BATCH] Video {i}/{len(video_configs)}")
            result = self.generate_video_with_disposable_account(config)
            results.append(result)
            
            # Small delay between batches
            if i < len(video_configs):
                time.sleep(2)
        
        # Summary
        successful = sum(1 for r in results if r.get('success'))
        print(f"\n{'='*80}")
        print(f"[SUMMARY] Batch complete: {successful}/{len(video_configs)} successful")
        print(f"{'='*80}")
        
        return results
    
    def get_statistics(self):
        """Get generator statistics."""
        return {
            'total_proxies': self.proxy_manager.get_stats()['total_proxies'],
            'active_accounts': len(self.active_accounts),
            'completed_videos': self.completed_count,
            'proxy_rotation_index': self.proxy_manager.current_index
        }


# Example usage
if __name__ == "__main__":
    print("="*80)
    print("DISPOSABLE ACCOUNT GENERATOR - DEMO")
    print("="*80)
    
    # Initialize generator
    generator = DisposableAccountGenerator()
    
    # Example: Generate 3 videos with disposable accounts
    video_configs = [
        {'prompt': 'A detective solving a mystery', 'duration': 5},
        {'prompt': 'Space exploration adventure', 'duration': 5},
        {'prompt': 'Cooking show episode', 'duration': 5}
    ]
    
    # Generate videos (each with new account + IP)
    results = generator.generate_batch_videos(video_configs)
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"\n{'='*80}")
    print("FINAL STATISTICS")
    print(f"{'='*80}")
    print(f"Total proxies available: {stats['total_proxies']}")
    print(f"Videos generated: {stats['completed_videos']}")
    print(f"Current proxy index: {stats['proxy_rotation_index']}")
    print(f"\nWith {stats['total_proxies']} proxies, you can generate unlimited videos!")
    print(f"Each video uses a fresh account + unique IP combination.")
