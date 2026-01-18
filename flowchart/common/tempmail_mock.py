#!/usr/bin/env python3
"""
Mock Temporary Email for Testing

Use this when external tempmail services are down.
Bypasses email generation for development/testing purposes.
"""

def get_new_email():
    """
    Returns mock email for testing.
    No actual email account is created.
    """
    print("[INFO] Creating MOCK temporary email (for testing only)...")
    print("[WARN] This is a mock - OTP will be hardcoded!")
    
    email = "mock.test.12345@example.com"
    config = {
        "provider": "mock",
        "email": email
    }
    
    print(f"[SUCCESS] Mock email: {email}")
    return email, config


def get_otp(email, config, max_wait=120):
    """
    Returns hardcoded OTP for testing.
    Use only when tempmail services are unavailable.
    """
    print("[INFO] Returning MOCK OTP (for testing only)...")
    print("[WARN] You'll need to manually enter OTP in the actual flow!")
    
    # Return None to trigger manual OTP entry
    return None


if __name__ == "__main__":
    print("="*60)
    print("  MOCK TEMPMAIL - FOR TESTING ONLY")
    print("="*60)
    
    email, config = get_new_email()
    print(f"\nEmail: {email}")
    print(f"Config: {config}")
    
    otp = get_otp(email, config)
    print(f"OTP: {otp} (will trigger manual entry)")
    
    print("\n" + "="*60)
    print("  USE THIS ONLY WHEN REAL SERVICES ARE DOWN")
    print("="*60)
