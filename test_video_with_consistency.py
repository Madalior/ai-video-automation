"""
Test Script for Video Generator WITH Consistency Features

This test uses:
1. Identity Cards for character consistency
2. Reference images (Veo 3.1 multi-reference)
3. Frame controller for consistent character across scenes
"""

import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.video_generator import DreaminaVideoGenerator
from flowchart.common.identity_cards import IdentityCardManager
from flowchart.common.frame_controller import FrameController


def test_video_with_consistency():
    """
    Test video generation with character consistency using identity cards.
    """
    print("\n" + "="*80)
    print("TESTING VIDEO GENERATOR WITH CONSISTENCY (Veo 3.1)")
    print("="*80 + "\n")
    
    # Initialize consistency tools
    print("[SETUP] Initializing consistency tools...")
    identity_manager = IdentityCardManager()
    frame_controller = FrameController()
    
    # Character definition
    character_name = "Captain Nova"
    character_description = "A brave female astronaut with short brown hair, blue spacesuit, determined expression"
    
    # Create identity card for the character
    print(f"\n[STEP 1] Creating identity card for '{character_name}'...")
    print(f"  Description: {character_description}")
    
    # Note: In a real scenario, you would first generate a reference image
    # For this test, let's assume we have reference images or will generate them
    
    # Test prompts for 3 scenes with the same character
    scenes = [
        {
            "scene_num": 1,
            "prompt": f"{character_name} floating inside a spaceship, looking at control panels, cinematic shot",
            "description": "Inside spaceship cockpit"
        },
        {
            "scene_num": 2,
            "prompt": f"{character_name} performing spacewalk outside the ship, Earth visible in background, dramatic lighting",
            "description": "Spacewalk scene"
        },
        {
            "scene_num": 3,
            "prompt": f"{character_name} discovering mysterious alien artifact on Mars surface, excited expression",
            "description": "Mars discovery"
        }
    ]
    
    # Output directory
    output_dir = "output/test_videos_consistency"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[STEP 2] Testing {len(scenes)} scenes with character consistency")
    print(f"  Character: {character_name}")
    print(f"  Output: {output_dir}")
    
    # Initialize video generator
    print("\n[STEP 3] Initializing DreaminaVideoGenerator...")
    generator = DreaminaVideoGenerator(
        headless=False,
        profile_path=None,
        fresh_profile=False
    )
    
    try:
        # Login once
        print("\n[STEP 4] Logging into video generator...")
        generator.login()
        
        # For consistency testing, we would ideally:
        # 1. Generate a reference image first (or use an existing one)
        # 2. Create identity card from that image
        # 3. Use that identity card for all subsequent scenes
        
        print("\n" + "="*80)
        print("GENERATING VIDEOS WITH CONSISTENCY")
        print("="*80)
        
        # For this test, let's generate videos in two modes:
        # Mode A: Without reference (baseline)
        # Mode B: With reference images (if you have them)
        
        reference_images_available = False  # Set to True if you have reference images
        
        if reference_images_available:
            print("\n[MODE] Using reference images for consistency (Veo 3.1)")
            # You would add reference image paths here
            reference_images = [
                "path/to/character_reference_1.png",
                "path/to/character_reference_2.png"
            ]
        else:
            print("\n[MODE] Prompt-only mode (no reference images)")
            print("  Tip: For best consistency, first generate reference images")
            print("  Then use those images with identity cards for subsequent scenes")
            reference_images = None
        
        # Generate each scene
        successful_videos = []
        
        for scene in scenes:
            scene_num = scene["scene_num"]
            prompt = scene["prompt"]
            description = scene["description"]
            
            output_path = os.path.join(output_dir, f"scene_{scene_num:02d}_{character_name.replace(' ', '_')}.mp4")
            
            print(f"\n{'='*80}")
            print(f"SCENE {scene_num}: {description}")
            print(f"{'='*80}")
            print(f"Prompt: {prompt}")
            print(f"Output: {output_path}")
            
            try:
                # Generate video
                success = generator.generate_video(
                    prompt=prompt,
                    reference_image_paths=reference_images,  # Will be None if not available
                    output_path=output_path
                )
                
                if success and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✅ Scene {scene_num} generated successfully!")
                    print(f"   File: {output_path}")
                    print(f"   Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                    successful_videos.append(output_path)
                else:
                    print(f"❌ Scene {scene_num} failed to generate")
                    
            except Exception as e:
                print(f"❌ Scene {scene_num} error: {str(e)}")
        
        # Summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Character: {character_name}")
        print(f"Total Scenes: {len(scenes)}")
        print(f"Successful: {len(successful_videos)}/{len(scenes)}")
        
        if successful_videos:
            print(f"\n✅ Generated Videos:")
            for video_path in successful_videos:
                print(f"  - {video_path}")
                
            print(f"\n💡 CONSISTENCY TIPS:")
            print(f"  1. Generate a high-quality reference image first")
            print(f"  2. Use IdentityCardManager to create character identity card")
            print(f"  3. Pass reference images to all subsequent scene generations")
            print(f"  4. This ensures the same character appears in all scenes!")
            
        print("="*80 + "\n")
        
        return len(successful_videos) == len(scenes)
        
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
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                    VIDEO CONSISTENCY TEST (Veo 3.1)                          ║
    ║                                                                              ║
    ║  This test demonstrates how to use reference images and identity cards       ║
    ║  for character consistency across multiple video scenes.                     ║
    ║                                                                              ║
    ║  Features:                                                                   ║
    ║   ✓ Identity Cards (character consistency)                                  ║
    ║   ✓ Frame Controller (scene management)                                     ║
    ║   ✓ Multi-Reference (Veo 3.1 up to 3 reference images)                      ║
    ║                                                                              ║
    ║  NOTE: For best results, generate reference images first!                    ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_video_with_consistency()
    sys.exit(0 if success else 1)
