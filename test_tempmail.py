"""
Test Temporary Email Functionality

This script tests the tempmail API used in the image_generator.py login process.
It verifies:
1. Email generation (get_new_email)
2. OTP retrieval (get_otp)
"""

import sys
import time
from flowchart.common.browser_utils import get_new_email, get_otp

def test_email_generation():
    """Test generating a temporary email address."""
    print("\n" + "="*80)
    print("TEST 1: Email Generation")
    print("="*80)
    
    try:
        print("[Step 1] Requesting temporary email...")
        email, password = get_new_email()
        
        if email and password:
            print(f"[SUCCESS] Email generated!")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            return email, password
        else:
            print("[FAILED] Email generation returned None")
            return None, None
            
    except Exception as e:
        print(f"[ERROR] Email generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def test_otp_retrieval(email, password):
    """Test OTP retrieval from temporary email."""
    print("\n" + "="*80)
    print("TEST 2: OTP Retrieval")
    print("="*80)
    
    print(f"[INFO] This test requires you to MANUALLY trigger an OTP email")
    print(f"[INFO] to the address: {email}")
    print(f"\n[ACTION REQUIRED]:")
    print(f"  1. Open a browser")
    print(f"  2. Go to a site that sends OTP (e.g., Google signup)")
    print(f"  3. Use email: {email}")
    print(f"  4. Request OTP to be sent")
    print(f"\n[INFO] Waiting 120 seconds for OTP email to arrive...")
    
    proceed = input("\nPress ENTER when ready to check for OTP (or 'skip' to skip): ")
    
    if proceed.lower() == 'skip':
        print("[SKIPPED] OTP retrieval test skipped")
        return None
    
    try:
        print(f"\n[Step 1] Checking inbox for OTP...")
        otp = get_otp(email, password, max_wait=120)
        
        if otp:
            print(f"[SUCCESS] OTP retrieved!")
            print(f"  OTP Code: {otp}")
            return otp
        else:
            print("[FAILED] No OTP found within timeout period")
            return None
            
    except Exception as e:
        print(f"[ERROR] OTP retrieval failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_automated_flow():
    """Test the automated flow as used in image_generator.py"""
    print("\n" + "="*80)
    print("TEST 3: Automated Login Flow Simulation")
    print("="*80)
    
    print("\n[INFO] This simulates the login process in image_generator.py")
    print("[INFO] It will:")
    print("  1. Generate a temporary email")
    print("  2. Display the email for you to use in a login form")
    print("  3. Wait for OTP")
    print("  4. Retrieve and display the OTP")
    
    # Step 1: Generate email
    print("\n[Step 1/3] Generating temporary email...")
    email, password = get_new_email()
    
    if not email:
        print("[FAILED] Could not generate email")
        return False
    
    print(f"[SUCCESS] Email: {email}")
    
    # Step 2: Instruct user
    print("\n" + "-"*80)
    print(f"📧 USE THIS EMAIL IN YOUR LOGIN FORM: {email}")
    print("-"*80)
    
    input("\nPress ENTER after you've entered the email and requested the OTP...")
    
    # Step 3: Wait for OTP
    print("\n[Step 2/3] Waiting for OTP email (max 120 seconds)...")
    start_time = time.time()
    
    otp = get_otp(email, password, max_wait=120)
    elapsed = time.time() - start_time
    
    if otp:
        print(f"[SUCCESS] OTP retrieved in {elapsed:.1f} seconds!")
        print("\n" + "-"*80)
        print(f"🔑 YOUR OTP CODE: {otp}")
        print("-"*80)
        return True
    else:
        print(f"[FAILED] No OTP received after {elapsed:.1f} seconds")
        return False


def main():
    print("\n" + "="*80)
    print("TEMPMAIL FUNCTIONALITY TEST")
    print("="*80)
    print("\nThis script tests the temporary email API used in image_generator.py")
    print("\nAvailable tests:")
    print("  1. Email Generation Only")
    print("  2. Full Automated Flow (recommended)")
    print("  3. Both")
    
    choice = input("\nSelect test (1/2/3) [default: 2]: ").strip() or "2"
    
    if choice == "1":
        email, password = test_email_generation()
        
    elif choice == "2":
        success = test_automated_flow()
        if success:
            print("\n[OVERALL] ✅ Tempmail test PASSED")
        else:
            print("\n[OVERALL] ❌ Tempmail test FAILED")
            sys.exit(1)
            
    elif choice == "3":
        # Test 1: Email generation
        email, password = test_email_generation()
        
        if not email:
            print("\n[OVERALL] ❌ Email generation failed - stopping tests")
            sys.exit(1)
        
        # Test 2: OTP retrieval (optional)
        otp = test_otp_retrieval(email, password)
        
        # Test 3: Full flow
        success = test_automated_flow()
        
        if success:
            print("\n[OVERALL] ✅ All tempmail tests PASSED")
        else:
            print("\n[OVERALL] ⚠️  Some tests failed - check output above")
    
    else:
        print(f"[ERROR] Invalid choice: {choice}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
