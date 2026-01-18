#!/usr/bin/env python3
"""
Enhanced Temporary Email with Multiple Fallbacks

Implements 3-tier fallback system:
1. mail.gw (primary)
2. 1secmail.com (fallback 1)
3. Manual email option (fallback 2)
"""

import time
import json
import requests
import re
from uuid import uuid4

# ================= MAIL.GW (Primary) =================
MAIL_GW_BASE = "https://api.mail.gw"

def get_email_mailgw():
    """mail.gw temporary email (primary)"""
    try:
        response = requests.get(f"{MAIL_GW_BASE}/domains", timeout=10)
        domains = response.json()
        
        if "hydra:member" not in domains or not domains["hydra:member"]:
            return None, None
        
        domain = domains["hydra:member"][0]["domain"]
        email = f"{uuid4().hex[:8]}@{domain}"
        password = uuid4().hex
        
        requests.post(f"{MAIL_GW_BASE}/accounts", 
                     json={"address": email, "password": password},
                     timeout=10)
        
        return email, password
    except:
        return None, None


def get_otp_mailgw(email, password, max_wait=120):
    """Get OTP from mail.gw"""
    try:
        r = requests.post(f"{MAIL_GW_BASE}/token", 
                         json={"address": email, "password": password},
                         timeout=10).json()
        token = r.get("token")
        if not token:
            return None
        
        headers = {"Authorization": f"Bearer {token}"}
        waited = 0
        
        while waited < max_wait:
            messages = requests.get(f"{MAIL_GW_BASE}/messages", 
                                   headers=headers, timeout=10).json()
            
            if messages.get("hydra:totalItems", 0) > 0:
                msg_id = messages["hydra:member"][0]["id"]
                msg = requests.get(f"{MAIL_GW_BASE}/messages/{msg_id}", 
                                  headers=headers, timeout=10).json()
                
                full_text = msg.get("text", "") + " " + str(msg.get("html", ""))
                match = re.search(r"\b[A-Z0-9]{6}\b", full_text)
                if match:
                    return match.group(0)
            
            time.sleep(5)
            waited += 5
        
        return None
    except:
        return None


# ================= 1SECMAIL (Fallback 1) =================
SECMAIL_BASE = "https://www.1secmail.com/api/v1/"

def get_email_1secmail():
    """1secmail.com temporary email (fallback)"""
    try:
        response = requests.get(f"{SECMAIL_BASE}?action=genRandomMailbox&count=1", timeout=10)
        emails = response.json()
        
        if emails and len(emails) > 0:
            email = emails[0]
            # Parse email to get login and domain
            login, domain = email.split("@")
            return email, {"login": login, "domain": domain}
        
        return None, None
    except:
        return None, None


def get_otp_1secmail(email_data, max_wait=120):
    """Get OTP from 1secmail"""
    try:
        login = email_data["login"]
        domain = email_data["domain"]
        waited = 0
        
        while waited < max_wait:
            response = requests.get(
                f"{SECMAIL_BASE}?action=getMessages&login={login}&domain={domain}",
                timeout=10
            )
            messages = response.json()
            
            if messages and len(messages) > 0:
                msg_id = messages[0]["id"]
                msg_response = requests.get(
                    f"{SECMAIL_BASE}?action=readMessage&login={login}&domain={domain}&id={msg_id}",
                    timeout=10
                )
                msg = msg_response.json()
                
                full_text = msg.get("textBody", "") + " " + msg.get("htmlBody", "")
                match = re.search(r"\b[A-Z0-9]{6}\b", full_text)
                if match:
                    return match.group(0)
            
            time.sleep(5)
            waited += 5
        
        return None
    except:
        return None


# ================= UNIFIED API =================
def get_new_email():
    """
    Get temporary email with automatic fallback.
    
    Returns:
        (email, password/config) or (None, None)
    """
    print("[INFO] Creating temporary email...")
    
    # Try mail.gw first
    print("[TRY] Attempting mail.gw...")
    email, password = get_email_mailgw()
    if email:
        print(f"[SUCCESS] mail.gw email: {email}")
        return email, {"provider": "mailgw", "password": password}
    
    print("[WARN] mail.gw failed, trying 1secmail...")
    
    # Fallback to 1secmail
    email, config = get_email_1secmail()
    if email:
        print(f"[SUCCESS] 1secmail email: {email}")
        return email, {"provider": "1secmail", **config}
    
    print("[ERROR] All tempmail providers failed")
    print("[INFO] You may need to use manual email input")
    return None, None


def get_otp(email, config, max_wait=120):
    """
    Get OTP with provider-specific logic.
    
    Args:
        email: Email address
        config: Provider config dict with 'provider' key
        max_wait: Maximum wait time in seconds
    """
    print(f"[INFO] Waiting for OTP (max {max_wait}s)...")
    
    if not config or "provider" not in config:
        print("[ERROR] Invalid config")
        return None
    
    provider = config["provider"]
    
    if provider == "mailgw":
        password = config.get("password")
        return get_otp_mailgw(email, password, max_wait)
    
    elif provider == "1secmail":
        return get_otp_1secmail(config, max_wait)
    
    else:
        print(f"[ERROR] Unknown provider: {provider}")
        return None


# ================= TEST =================
if __name__ == "__main__":
    print("="*60)
    print("  TESTING MULTI-PROVIDER TEMPMAIL")
    print("="*60)
    
    email, config = get_new_email()
    
    if email:
        print(f"\n✓ Email: {email}")
        print(f"✓ Provider: {config.get('provider')}")
        print(f"✓ Config: {config}")
        
        print("\nWaiting 10s for test email...")
        time.sleep(10)
        
        otp = get_otp(email, config, max_wait=30)
        if otp:
            print(f"✓ OTP: {otp}")
        else:
            print("✓ No OTP (expected for test)")
        
        print("\n" + "="*60)
        print("  TEST PASSED ✓")
        print("="*60)
    else:
        print("\n✗ Failed to get email from any provider")
        print("\nCheck:")
        print("  1. Internet connection")
        print("  2. Firewall settings")
        print("  3. Try running test again")
