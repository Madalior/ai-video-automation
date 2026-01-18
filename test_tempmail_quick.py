#!/usr/bin/env python3
"""
Quick test of temporary email functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flowchart.common.browser_utils import get_new_email, get_otp

print("="*60)
print("  TESTING TEMPORARY EMAIL SYSTEM")
print("="*60)

print("\nTest 1: Creating temporary email...")
email, password = get_new_email()

if email and password:
    print(f"✓ Email created successfully: {email}")
    print(f"✓ Password: {password[:8]}...")
    
    print("\nTest 2: Checking if mail.gw API is accessible...")
    import requests
    try:
        response = requests.get("https://api.mail.gw/domains", timeout=10)
        print(f"✓ API Status: {response.status_code}")
        print(f"✓ Domains available: {response.json().get('hydra:totalItems', 0)}")
    except Exception as e:
        print(f"✗ API Error: {e}")
    
    print("\n" + "="*60)
    print("  TEMP MAIL TEST: PASSED ✓")
    print("="*60)
else:
    print("\n✗ Failed to create email")
    print("\nTroubleshooting:")
    print("  1. Check internet connection")
    print("  2. Verify mail.gw API is not blocked")
    print("  3. Check firewall settings")
    
    print("\n" + "="*60)
    print("  TEMP MAIL TEST: FAILED ✗")
    print("="*60)
