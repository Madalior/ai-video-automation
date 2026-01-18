"""
Rate Limit Handler - Add delays to avoid "systems overloaded" errors
"""
import time
import random

class RateLimitHandler:
    """Handles rate limiting with smart delays."""
    
    def __init__(self, base_delay=3, max_delay=10):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_count = 0
    
    def wait_before_request(self):
        """Wait before making a request to avoid rate limits."""
        # Random delay between 3-5 seconds
        delay = random.uniform(self.base_delay, self.base_delay + 2)
        print(f"[Rate Limit] Waiting {delay:.1f}s before request...")
        time.sleep(delay)
    
    def handle_rate_limit_error(self, error_message):
        """Handle rate limit error with exponential backoff."""
        if "overloaded" in error_message.lower() or "try again later" in error_message.lower():
            self.retry_count += 1
            # Exponential backoff: 5s, 10s, 20s, 40s...
            wait_time = min(5 * (2 ** (self.retry_count - 1)), self.max_delay * 6)
            print(f"[WARNING] Rate limited! Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
            return True
        return False
    
    def reset(self):
        """Reset retry counter after success."""
        self.retry_count = 0

# Usage in generators:
# Before clicking submit:
# rate_limiter = RateLimitHandler()
# rate_limiter.wait_before_request()
# submit_generation()
