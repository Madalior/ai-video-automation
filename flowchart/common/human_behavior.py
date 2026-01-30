"""
Human Behavior Simulation for Anti-Detection

Simulates realistic human interaction patterns to avoid bot detection.
"""

import time
import random


class HumanBehavior:
    """
    Simulate human-like behavior patterns.
    
    Features:
    - Variable typing speeds
    - Reading pauses based on content length
    - Random micro-delays
    - Natural hesitation
    """
    
    @staticmethod
    def smart_delay(action_type='normal'):
        """
        Apply context-appropriate delay.
        
        Args:
            action_type: Type of action (short, normal, long, thinking, reading)
        """
        delays = {
            'short': (0.5, 1.5),      # Quick actions (click buttons)
            'normal': (1.0, 2.5),     # Regular actions
            'long': (2.0, 4.0),        # After important actions
            'thinking': (3.0, 6.0),   # Before starting task
            'reading': (2.0, 5.0),    # Reading content
        }
        
        min_delay, max_delay = delays.get(action_type, (1.0, 2.0))
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @staticmethod
    def typing_delay(text_length):
        """
        Calculate realistic typing delay based on text length.
        
        Args:
            text_length: Number of characters
            
        Returns:
            Delay in seconds
        """
        # Average typing speed: 40-60 words per minute = ~200-300 chars per minute
        chars_per_second = random.uniform(3, 5)
        base_delay = text_length / chars_per_second
        
        # Add some variance for natural pauses
        variance = random.uniform(0.8, 1.2)
        total_delay = base_delay * variance
        
        return total_delay
    
    @staticmethod
    def type_like_human(driver, element, text):
        """
        Type text with human-like delays between characters.
        
        Args:
            driver: Selenium WebDriver
            element: Input element
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            # Random delay between characters (50-150ms)
            time.sleep(random.uniform(0.05, 0.15))
        
        # Pause after finishing typing
        time.sleep(random.uniform(0.5, 1.0))
    
    @staticmethod
    def reading_pause(content_length):
        """
        Pause as if reading content.
        
        Args:
            content_length: Number of characters or words to read
            
        Returns:
            Pause duration in seconds
        """
        # Average reading speed: 200-250 words per minute
        # Assume ~5 characters per word
        words = content_length / 5
        reading_time = words / (200 / 60)  # Convert to seconds
        
        # Add minimum pause and variance
        min_pause = 2.0
        variance = random.uniform(0.8, 1.5)
        
        return max(min_pause, reading_time * variance)
    
    @staticmethod
    def random_micro_delay():
        """Small random delay to simulate natural hesitation."""
        time.sleep(random.uniform(0.1, 0.5))
    
    @staticmethod
    def simulate_page_scan(driver):
        """
        Simulate human scanning a page before interacting.
        
        Args:
            driver: Selenium WebDriver
        """
        # Scroll down a bit
        scroll_amount = random.randint(100, 400)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.5, 1.5))
        
        # Scroll back up
        driver.execute_script(f"window.scrollBy(0, -{scroll_amount});")
        time.sleep(random.uniform(0.3, 0.8))
    
    @staticmethod
    def get_delay_profile(aggression='balanced'):
        """
        Get delay configuration based on aggression level.
        
        Args:
            aggression: 'conservative', 'balanced', or 'aggressive'
            
        Returns:
            Dict of delay multipliers
        """
        profiles = {
            'conservative': {
                'min_interval': 20,
                'max_requests': 10,
                'delay_multiplier': 1.5
            },
            'balanced': {
                'min_interval': 15,
                'max_requests': 15,
                'delay_multiplier': 1.0
            },
            'aggressive': {
                'min_interval': 10,
                'max_requests': 20,
                'delay_multiplier': 0.7
            }
        }
        
        return profiles.get(aggression, profiles['balanced'])


def inject_human_js(driver):
    """
    Inject JavaScript to make interactions more human-like.
    
    Args:
        driver: Selenium WebDriver
    """
    human_js = """
    // Override Date.now() to add slight variation
    const originalDateNow = Date.now;
    Date.now = function() {
        return originalDateNow() + Math.random() * 10;
    };
    
    // Override Math.random() to be less predictable
    const originalRandom = Math.random;
    let randomSeed = Date.now();
    Math.random = function() {
        randomSeed = (randomSeed * 9301 + 49297) % 233280;
        return randomSeed / 233280;
    };
    
    // Make mouse movements less perfect
    document.addEventListener('mousemove', function(e) {
        // Add tiny jitter to mouse position
        const jitterX = (Math.random() - 0.5) * 2;
        const jitterY = (Math.random() - 0.5) * 2;
        // Note: This is just for appearance, actual movement handled by Selenium
    });
    
    console.log('[HUMAN] Behavior simulation injected');
    """
    
    try:
        driver.execute_script(human_js)
    except Exception as e:
        print(f"[HUMAN] Failed to inject JS: {e}")
