import os
import time
from flowchart.common.shared_session import SharedSessionManager

def test_shared_session_full():
    print("="*60)
    print("TEST: SharedSessionManager - Full Generation Capabilities")
    print("="*60)
    
    # 1. Initialize Shared Session (headless=False for visibility)
    print("\n[1] Initializing Shared Session...")
    session = SharedSessionManager(headless=False, fresh_profile=False)
    
    try:
        # 2. Login
        print("\n[2] Logging in...")
        if session.login():
            print("[SUCCESS] Login complete.")
        else:
            print("[ERROR] Login failed.")
            return

        # 3. Generate Image
        print("\n[3] Testing Image Generation...")
        img_prompt = "A futuristic cyberpunk detective ID card, neon blue and pink, high detail, digital art"
        img_output = os.path.abspath("output/tests/shared_test_image.png")
        
        if session.generate_image(img_prompt, img_output):
            print(f"[SUCCESS] Image generated: {img_output}")
        else:
            print("[ERROR] Image generation failed.")

        # 4. Generate Video (using the generated image as reference if available)
        print("\n[4] Testing Video Generation (with Character Consistency)...")
        vid_prompt = "The cyberpunk detective from the ID card walking through a rainy neon city, cinematic lighting, 4k"
        vid_output = os.path.abspath("output/tests/shared_test_video.mp4")
        
        # Use the image we just generated as a reference
        refs = [img_output] if os.path.exists(img_output) else None
        
        if session.generate_video(vid_prompt, vid_output, reference_image_paths=refs):
            print(f"[SUCCESS] Video generated: {vid_output}")
        else:
            print("[ERROR] Video generation failed.")
            
    except Exception as e:
        print(f"\n[EXCEPTION] Test failed: {e}")
    finally:
        print("\n[5] Closing Session...")
        session.close()
        print("="*60)
        print("Test Complete")
        print("="*60)

if __name__ == "__main__":
    test_shared_session_full()
