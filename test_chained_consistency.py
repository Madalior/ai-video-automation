"""
Test Video Generator with CHAINED CONSISTENCY

This implements the proper consistency approach:
1. Generate Scene 1 (prompt only)
2. Extract frame from Scene 1 output video
3. Use that frame as reference for Scene 2
4. Extract frame from Scene 2 output video  
5. Use that frame as reference for Scene 3
... and so on!

This ensures character consistency across all scenes using previous outputs!
"""

import sys
import os
import cv2

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.video_generator import DreaminaVideoGenerator
from flowchart.common.identity_cards import IdentityCardManager
from flowchart.common.frame_controller import FrameController


def extract_reference_frame(video_path, output_path, frame_number=30):
    """
    Extract a frame from video to use as reference for next scene.
    
    Args:
        video_path: Path to the video file
        output_path: Where to save the extracted frame
        frame_number: Which frame to extract (default: frame 30, ~1 second in)
    
    Returns:
        Path to extracted frame, or None if failed
    """
    try:
        print(f"  [EXTRACT] Extracting frame {frame_number} from video...")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        success, frame = cap.read()
        
        if success:
            # Save frame as image
            cv2.imwrite(output_path, frame)
            cap.release()
            print(f"  [SUCCESS] Reference frame saved: {output_path}")
            return output_path
        else:
            cap.release()
            print(f"  [ERROR] Could not extract frame from video")
            return None
            
    except Exception as e:
        print(f"  [ERROR] Frame extraction failed: {str(e)}")
        return None


def test_chained_consistency():
    """
    Test video generation with CHAINED consistency.
    Each scene uses the previous scene's output as reference!
    """
    print("\n" + "="*80)
    print("VIDEO GENERATOR - CHAINED CONSISTENCY TEST")
    print("="*80)
    print("Scene 1 → Extract Frame → Scene 2 → Extract Frame → Scene 3")
    print("This ensures the same character appears in ALL scenes!")
    print("="*80 + "\n")
    
    # Character & scenes
    character_name = "Captain Nova"
    
    scenes = [
        {
            "scene_num": 1,
            "prompt": f"A brave female astronaut with short brown hair and blue spacesuit, floating inside a spaceship control room, looking at holographic displays, cinematic lighting",
            "description": "Inside spaceship (establishes character appearance)"
        },
        {
            "scene_num": 2,
            "prompt": f"The same astronaut performing a spacewalk outside the ship, Earth visible in the background, dramatic perspective, cinematic shot",
            "description": "Spacewalk scene (uses Scene 1 reference)"
        },
        {
            "scene_num": 3,
            "prompt": f"The same astronaut on Mars surface, discovering a glowing alien artifact, excited expression, red rocky terrain, cinematic lighting",
            "description": "Mars discovery (uses Scene 2 reference)"
        }
    ]
    
    # Output directories
    output_dir = "output/test_chained_consistency"
    refs_dir = os.path.join(output_dir, "reference_frames")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(refs_dir, exist_ok=True)
    
    print(f"Output Directory: {output_dir}")
    print(f"Reference Frames: {refs_dir}\n")
    
    # Initialize video generator
    print("[INIT] Initializing DreaminaVideoGenerator...")
    generator = DreaminaVideoGenerator(
        headless=False,
        profile_path=None,
        fresh_profile=False
    )
    
    try:
        # Login once
        print("\n[LOGIN] Logging into video generator...\n")
        generator.login()
        
        # Track successful videos and reference frames
        successful_videos = []
        reference_chain = []  # This will store the reference images chain
        
        # Generate each scene with chained consistency
        for scene in scenes:
            scene_num = scene["scene_num"]
            prompt = scene["prompt"]
            description = scene["description"]
            
            video_path = os.path.join(output_dir, f"scene_{scene_num:02d}.mp4")
            
            print("\n" + "="*80)
            print(f"SCENE {scene_num}: {description}")
            print("="*80)
            print(f"Prompt: {prompt}")
            
            # Determine reference images for this scene
            if scene_num == 1:
                # First scene - no reference (establishes character)
                reference_images = None
                print("Reference: None (establishing character appearance)")
            else:
                # Use previous scene's extracted frame as reference
                reference_images = [reference_chain[-1]]  # Last reference frame
                print(f"Reference: {reference_images[0]}")
                print(f"  (Using frame from Scene {scene_num - 1} for consistency)")
            
            print(f"Output: {video_path}\n")
            
            try:
                # Generate video
                print(f"[GENERATE] Generating Scene {scene_num}...")
                success = generator.generate_video(
                    prompt=prompt,
                    reference_image_paths=reference_images,
                    output_path=video_path
                )
                
                if success and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    print(f"\n✅ Scene {scene_num} generated successfully!")
                    print(f"   File: {video_path}")
                    print(f"   Size: {file_size/1024/1024:.2f} MB")
                    successful_videos.append(video_path)
                    
                    # Extract reference frame for next scene
                    if scene_num < len(scenes):  # Don't extract from last scene
                        ref_frame_path = os.path.join(refs_dir, f"scene_{scene_num:02d}_reference.png")
                        extracted_frame = extract_reference_frame(
                            video_path=video_path,
                            output_path=ref_frame_path,
                            frame_number=30  # Extract frame at ~1 second
                        )
                        
                        if extracted_frame:
                            reference_chain.append(extracted_frame)
                            print(f"  [CHAIN] Reference frame added to chain for Scene {scene_num + 1}")
                        else:
                            print(f"  [WARNING] Could not extract reference frame")
                            # Fallback: continue without reference for next scene
                    
                else:
                    print(f"\n❌ Scene {scene_num} failed to generate")
                    
            except Exception as e:
                print(f"\n❌ Scene {scene_num} error: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print("\n" + "="*80)
        print("CHAINED CONSISTENCY TEST RESULTS")
        print("="*80)
        print(f"Character: {character_name}")
        print(f"Total Scenes: {len(scenes)}")
        print(f"Successful: {len(successful_videos)}/{len(scenes)}")
        print(f"Reference Chain: {len(reference_chain)} frames extracted")
        
        if successful_videos:
            print(f"\n✅ Generated Videos:")
            for i, video_path in enumerate(successful_videos, 1):
                print(f"  {i}. {video_path}")
            
            if reference_chain:
                print(f"\n🔗 Reference Chain:")
                for i, ref_path in enumerate(reference_chain, 1):
                    print(f"  {i}. {ref_path} → Used for Scene {i+1}")
                
            print(f"\n💡 CONSISTENCY METHOD:")
            print(f"  ✓ Scene 1: Pure prompt (establishes character)")
            if len(successful_videos) > 1:
                print(f"  ✓ Scene 2: Uses Scene 1's frame as reference")
            if len(successful_videos) > 2:
                print(f"  ✓ Scene 3: Uses Scene 2's frame as reference")
            print(f"\n  This creates a consistency CHAIN ensuring the same character!")
            
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
    ║              CHAINED CONSISTENCY TEST - Veo 3.1 Multi-Reference              ║
    ║                                                                              ║
    ║  Scene 1 (prompt) → extract frame → Scene 2 (with ref) → extract frame →    ║
    ║  Scene 3 (with ref) = CONSISTENT CHARACTER ACROSS ALL SCENES!                ║
    ║                                                                              ║
    ║  This is the PROPER way to maintain character consistency!                   ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_chained_consistency()
    sys.exit(0 if success else 1)
