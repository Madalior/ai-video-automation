"""
Session Manager for Anti-Bot Detection

Tracks browser session health, request counts, and automatically
rotates sessions to avoid rate limiting and detection.
"""

import time
import random
from datetime import datetime, timedelta


class SessionManager:
    """
    Manage browser sessions to avoid detection.
    
    Features:
    - Request counting and limits
    - Time-based session expiry
    - Rate limiting between requests
    - Automatic session rotation
    """
    
    def __init__(self, max_requests=15, session_lifetime=3600, min_interval=15):
        """
        Initialize session manager.
        
        Args:
            max_requests: Maximum requests before session restart (default: 15)
            session_lifetime: Session lifetime in seconds (default: 3600 = 1 hour)
            min_interval: Minimum seconds between requests (default: 15)
        """
        self.max_requests = max_requests
        self.session_lifetime = session_lifetime
        self.min_interval = min_interval
        
        # Session tracking
        self.request_count = 0
        self.session_start_time = time.time()
        self.last_request_time = 0
        
        # Statistics
        self.total_requests = 0
        self.total_restarts = 0
        
        print(f"[SESSION] Manager initialized")
        print(f"[SESSION] Max requests per session: {max_requests}")
        print(f"[SESSION] Session lifetime: {session_lifetime}s")
        print(f"[SESSION] Min interval: {min_interval}s")
    
    def track_request(self):
        """
        Track a new request.
        
        Returns:
            Recommended delay before next request (seconds)
        """
        current_time = time.time()
        self.request_count += 1
        self.total_requests += 1
        
        # Calculate delay since last request
        if self.last_request_time > 0:
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                required_wait = self.min_interval - time_since_last
                print(f"[SESSION] Rate limiting: waiting {required_wait:.1f}s")
                time.sleep(required_wait)
        
        self.last_request_time = time.time()
        
        # Log progress
        print(f"[SESSION] Request {self.request_count}/{self.max_requests} " +
              f"(Total: {self.total_requests}, Restarts: {self.total_restarts})")
        
        # Return recommended delay for next request
        return random.uniform(self.min_interval, self.min_interval + 5)
    
    def should_restart_session(self):
        """
        Check if session should be restarted.
        
        Returns:
            (should_restart: bool, reason: str)
        """
        current_time = time.time()
        session_age = current_time - self.session_start_time
        
        # Check request limit
        if self.request_count >= self.max_requests:
            return True, f"Request limit reached ({self.request_count}/{self.max_requests})"
        
        # Check session age
        if session_age >= self.session_lifetime:
            return True, f"Session expired ({session_age:.0f}s/{self.session_lifetime}s)"
        
        return False, "Session healthy"
    
    def reset_session(self):
        """Reset session counters after browser restart."""
        print(f"[SESSION] Resetting session (requests: {self.request_count})")
        
        self.request_count = 0
        self.session_start_time = time.time()
        self.last_request_time = 0
        self.total_restarts += 1
        
        print(f"[SESSION] New session started (Total restarts: {self.total_restarts})")
    
    def get_session_stats(self):
        """
        Get current session statistics.
        
        Returns:
            Dict with session stats
        """
        current_time = time.time()
        session_age = current_time - self.session_start_time
        
        return {
            "request_count": self.request_count,
            "max_requests": self.max_requests,
            "requests_remaining": self.max_requests - self.request_count,
            "session_age_seconds": session_age,
            "session_lifetime_seconds": self.session_lifetime,
            "time_remaining_seconds": max(0, self.session_lifetime - session_age),
            "total_requests": self.total_requests,
            "total_restarts": self.total_restarts,
            "last_request_ago": current_time - self.last_request_time if self.last_request_time > 0 else 0,
        }
    
    def get_next_request_delay(self):
        """
        Calculate optimal delay before next request.
        
        Returns:
            Recommended delay in seconds
        """
        if self.last_request_time == 0:
            return 0  # First request
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            # Need to wait
            return self.min_interval - time_since_last
        else:
            # Can proceed, but add random delay for human-like behavior
            return random.uniform(1.0, 3.0)
    
    def wait_if_needed(self):
        """
        Wait if necessary to maintain rate limiting.
        
        Returns:
            Actual wait time in seconds
        """
        delay = self.get_next_request_delay()
        
        if delay > 0:
            print(f"[SESSION] Rate limit delay: {delay:.1f}s")
            time.sleep(delay)
        
        return delay
    
    def print_status(self):
        """Print current session status."""
        stats = self.get_session_stats()
        
        print("\n" + "="*60)
        print("SESSION STATUS")
        print("="*60)
        print(f"Requests: {stats['request_count']}/{stats['max_requests']} " +
              f"({stats['requests_remaining']} remaining)")
        print(f"Session age: {stats['session_age_seconds']:.0f}s / " +
              f"{stats['session_lifetime_seconds']}s")
        print(f"Time remaining: {stats['time_remaining_seconds']:.0f}s")
        print(f"Total requests (all sessions): {stats['total_requests']}")
        print(f"Total restarts: {stats['total_restarts']}")
        print(f"Last request: {stats['last_request_ago']:.1f}s ago")
        print("="*60 + "\n")


class OverloadDetector:
    """
    Detect and handle "systems overloaded" bot detection messages.
    """
    
    # Common overload/bot detection indicators
    OVERLOAD_INDICATORS = [
        "systems are overloaded",
        "try again later",
        "too many requests",
        "please wait",
        "slow down",
        "rate limit",
    ]
    
    # Exponential backoff delays (seconds)
    BACKOFF_DELAYS = [30, 60, 120, 240, 480]  # Up to 8 minutes
    
    def __init__(self):
        """Initialize overload detector."""
        self.detection_count = 0
        self.last_detection_time = 0
    
    def check_for_overload(self, driver):
        """
        Check if page shows overload/bot detection message.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            True if overload detected, False otherwise
        """
        try:
            from selenium.webdriver.common.by import By
            
            # Get page text
            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            
            # Check for indicators
            for indicator in self.OVERLOAD_INDICATORS:
                if indicator in body_text:
                    print(f"[OVERLOAD] Detected: '{indicator}'")
                    self.detection_count += 1
                    self.last_detection_time = time.time()
                    return True
            
            return False
            
        except Exception as e:
            print(f"[OVERLOAD] Error checking: {e}")
            return False
    
    def handle_overload(self, driver, attempt=0, max_attempts=3):
        """
        Handle overload with exponential backoff.
        
        Args:
            driver: Selenium WebDriver instance
            attempt: Current attempt number (0-indexed)
            max_attempts: Maximum retry attempts
            
        Returns:
            True if recovery successful, False if max attempts reached
        """
        if attempt >= max_attempts:
            print(f"[OVERLOAD] Max attempts ({max_attempts}) reached, giving up")
            return False
        
        # Calculate backoff delay
        delay_index = min(attempt, len(self.BACKOFF_DELAYS) - 1)
        base_delay = self.BACKOFF_DELAYS[delay_index]
        
        # Add random jitter (±20%)
        jitter = random.uniform(-0.2, 0.2) * base_delay
        actual_delay = base_delay + jitter
        
        print(f"[OVERLOAD] Attempt {attempt + 1}/{max_attempts}: " +
              f"Waiting {actual_delay:.0f}s before retry...")
        
        time.sleep(actual_delay)
        
        # Refresh page
        print("[OVERLOAD] Refreshing page...")
        driver.refresh()
        time.sleep(5)  # Wait for page load
        
        # Check if overload cleared
        if not self.check_for_overload(driver):
            print("[OVERLOAD] Successfully recovered!")
            return True
        else:
            print("[OVERLOAD] Still overloaded, will retry...")
            return False
    
    def get_stats(self):
        """Get overload detection statistics."""
        return {
            "total_detections": self.detection_count,
            "last_detection": self.last_detection_time,
            "time_since_last": time.time() - self.last_detection_time if self.last_detection_time > 0 else 0
        }
