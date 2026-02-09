"""
Test Script for Video Generator (Used in master_manager.py)

This script tests the DreaminaVideoGenerator directly with a simple test prompt.
This is the same video generator used in master_manager.py for character videos.
"""

import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.video_generator import DreaminaVideoGenerator


def test_video_generator():
    """
    Test the DreaminaVideoGenerator with a simple prompt.
    """
    print("\n" + "="*80)
    print("TESTING VIDEO GENERATOR (from master_manager.py)")
    print("="*80 + "\n")
    
    # Test prompt for video generation
    test_prompt = "An astronaut floating in space, looking at Earth from orbit, dramatic cinematic shot"
    
    # Optional: Test with a reference image (set to None if you don't have one)
    reference_image = None  # You can add a path to an image here
    
    # Output path
    output_dir = "output/test_videos"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "test_astronaut_video.mp4")
    
    print(f"[TEST] Test Prompt:")
    print(f"  '{test_prompt}'")
    print(f"\n[TEST] Reference Image: {reference_image if reference_image else 'None (prompt-only)'}")
    print(f"[TEST] Output Path: {output_path}")
    print(f"[TEST] Headless Mode: False (visible browser for debugging)")
    print("\n" + "="*80 + "\n")
    
    # Initialize video generator
    print("[TEST] Initializing DreaminaVideoGenerator...")
    generator = DreaminaVideoGenerator(
        headless=False,  # Visible browser
        profile_path=None,  # Use default profile
        fresh_profile=False  # Use existing profile
    )
    
    try:
        # Login
        print("\n[TEST] Logging into video generator...")
        generator.login()
        
        # Generate video
        print(f"\n[TEST] Generating video...")
        print(f"  This may take 2-5 minutes depending on the AI generation time...")
        
        generator.generate_video(
            prompt=test_prompt,
            reference_image_paths=reference_image,
            output_path=output_path
        )
        
        # Check if video was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print("\n" + "="*80)
            print("✅ TEST PASSED - Video Generated Successfully!")
            print("="*80)
            print(f"Video Path: {output_path}")
            print(f"File Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            print("="*80 + "\n")
            return True
        else:
            print("\n" + "="*80)
            print("❌ TEST FAILED - Video file not created")
            print("="*80 + "\n")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED - Exception occurred:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            generator.close()
            print("[CLEANUP] Video generator closed")
        except:
            pass


if __name__ == "__main__":
    success = test_video_generator()
    sys.exit(0 if success else 1)
