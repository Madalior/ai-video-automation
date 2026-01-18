#!/usr/bin/env python3
"""
Test Mail.tm API (working alternative to mail.gw)
"""
import requests
import json
from uuid import uuid4

BASE = "https://api.mail.tm"

print("="*60)
print("  TESTING MAIL.TM API")
print("="*60)

# Test 1: Get domains
print("\n1. Getting available domains...")
try:
    r = requests.get(f"{BASE}/domains", timeout=10)
    print(f"   Status: {r.status_code}")
    domains = r.json()
    if "hydra:member" in domains and domains["hydra:member"]:
        domain = domains["hydra:member"][0]["domain"]
        print(f"   ✓ Domain: {domain}")
        
        # Test 2: Create account
        print("\n2. Creating account...")
        email = f"test{uuid4().hex[:8]}@{domain}"
        password = uuid4().hex
        
        r = requests.post(f"{BASE}/accounts", 
                         json={"address": email, "password": password},
                         timeout=10)
        print(f"   Status: {r.status_code}")
        
        if r.status_code in [200, 201]:
            print(f"   ✓ Email: {email}")
            
            # Test 3: Get auth token
            print("\n3. Getting auth token...")
            r = requests.post(f"{BASE}/token",
                             json={"address": email, "password": password},
                             timeout=10)
            print(f"   Status: {r.status_code}")
            
            if r.status_code == 200:
                token = r.json().get("token")
                print(f"   ✓ Token: {token[:20]}...")
                
                # Test 4: Check messages
                print("\n4. Checking inbox...")
                headers = {"Authorization": f"Bearer {token}"}
                r = requests.get(f"{BASE}/messages", headers=headers, timeout=10)
                print(f"   Status: {r.status_code}")
                print(f"   Messages: {r.json().get('hydra:totalItems', 0)}")
                
                print("\n" + "="*60)
                print("  ✅ MAIL.TM IS WORKING!")
                print("="*60)
            else:
                print(f"   ✗ Token failed: {r.text[:100]}")
        else:
            print(f"   ✗ Account creation failed: {r.text[:100]}")
    else:
        print("   ✗ No domains available")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
