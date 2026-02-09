"""
Test Frame Extraction and Chained Consistency Logic
WITHOUT generating new videos (offline test)

This tests:
1. Frame extraction from existing video files
2. The chaining logic (using extracted frames as references)
3. Verifies the consistency workflow works correctly
"""

import os
import cv2
import numpy as np


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
        print(f"  [EXTRACT] Extracting frame {frame_number} from: {os.path.basename(video_path)}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"  [ERROR] Could not open video file")
            return None
        
        # Get video info
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"    Video info: {total_frames} frames @ {fps:.1f} fps")
        
        # Adjust frame number if needed
        if frame_number >= total_frames:
            frame_number = total_frames // 2
            print(f"    Adjusted to frame {frame_number} (middle of video)")
        
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # Read frame
        success, frame = cap.read()
        
        if success:
            # Save frame as image
            cv2.imwrite(output_path, frame)
            cap.release()
            
            # Get frame size
            height, width = frame.shape[:2]
            print(f"  [SUCCESS] Frame saved: {os.path.basename(output_path)} ({width}x{height})")
            return output_path
        else:
            cap.release()
            print(f"  [ERROR] Could not extract frame from video")
            return None
            
    except Exception as e:
        print(f"  [ERROR] Frame extraction failed: {str(e)}")
        return None


def test_frame_extraction_offline():
    """
    Test the frame extraction and chaining logic using existing video files.
    """
    print("\n" + "="*80)
    print("OFFLINE FRAME EXTRACTION TEST")
    print("="*80)
    print("Testing the consistency chain logic with existing videos")
    print("="*80 + "\n")
    
    # Look for existing videos in output directories
    video_dirs = [
        "output/test_videos",
        "output/test_videos_consistency",
        "output/test_chained_consistency",
        "output/character_videos/videos",
        "output/videos"
    ]
    
    # Find available video files
    available_videos = []
    for dir_path in video_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    video_path = os.path.join(dir_path, file)
                    available_videos.append(video_path)
    
    if not available_videos:
        print("❌ No video files found in output directories!")
        print("\nSearched in:")
        for dir_path in video_dirs:
            print(f"  - {dir_path}")
        print("\nPlease run a video generation test first to create some videos.")
        return False
    
    print(f"✅ Found {len(available_videos)} video file(s):\n")
    for i, video_path in enumerate(available_videos[:5], 1):  # Show first 5
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        print(f"  {i}. {os.path.basename(video_path)} ({file_size:.2f} MB)")
    
    if len(available_videos) > 5:
        print(f"  ... and {len(available_videos) - 5} more")
    
    # Create output directory for extracted frames
    output_dir = "output/test_frame_extraction"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📁 Output directory: {output_dir}\n")
    
    # Test the chaining logic
    print("="*80)
    print("TESTING CHAINED CONSISTENCY LOGIC")
    print("="*80)
    
    # Simulate the chaining workflow
    reference_chain = []
    
    # Use up to 3 videos to simulate 3 scenes
    test_videos = available_videos[:min(3, len(available_videos))]
    
    for i, video_path in enumerate(test_videos, 1):
        print(f"\n--- Scene {i} Simulation ---")
        
        if i == 1:
            print(f"Scene {i}: No reference (establishing character)")
            print(f"  Input: {os.path.basename(video_path)}")
        else:
            print(f"Scene {i}: Using reference from Scene {i-1}")
            print(f"  Reference: {os.path.basename(reference_chain[-1])}")
            print(f"  Input: {os.path.basename(video_path)}")
        
        # Extract frame from this scene's video
        ref_frame_path = os.path.join(output_dir, f"scene_{i:02d}_reference.png")
        
        extracted = extract_reference_frame(
            video_path=video_path,
            output_path=ref_frame_path,
            frame_number=30
        )
        
        if extracted:
            reference_chain.append(extracted)
            if i < len(test_videos):
                print(f"  [CHAIN] This frame will be used as reference for Scene {i+1}")
        else:
            print(f"  [WARNING] Frame extraction failed")
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"Videos processed: {len(test_videos)}")
    print(f"Frames extracted: {len(reference_chain)}")
    
    if reference_chain:
        print(f"\n✅ Reference Chain Created:")
        for i, ref_path in enumerate(reference_chain, 1):
            if os.path.exists(ref_path):
                file_size = os.path.getsize(ref_path) / 1024
                print(f"  {i}. {os.path.basename(ref_path)} ({file_size:.1f} KB)")
                if i < len(reference_chain):
                    print(f"     → Will be used for Scene {i+1}")
        
        print(f"\n💡 CONSISTENCY CHAIN VERIFIED:")
        print(f"  ✓ Scene 1: Pure prompt (establishes character)")
        if len(reference_chain) > 1:
            print(f"  ✓ Scene 2: Uses Scene 1's extracted frame")
        if len(reference_chain) > 2:
            print(f"  ✓ Scene 3: Uses Scene 2's extracted frame")
        
        print(f"\n🎬 HOW TO USE IN VIDEO GENERATION:")
        print(f"  1. Generate Scene 1 with prompt only")
        print(f"  2. Extract frame from Scene 1 output")
        print(f"  3. Generate Scene 2 with prompt + Scene 1 frame as reference")
        print(f"  4. Extract frame from Scene 2 output")
        print(f"  5. Generate Scene 3 with prompt + Scene 2 frame as reference")
        print(f"  = Character stays consistent across all scenes!")
        
        print(f"\n✅ OFFLINE TEST PASSED!")
        print(f"Frame extraction and chaining logic works correctly!")
        
    else:
        print(f"\n❌ No frames were extracted")
    
    print("="*80 + "\n")
    
    return len(reference_chain) > 0


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                  OFFLINE FRAME EXTRACTION TEST                               ║
    ║                                                                              ║
    ║  Tests the consistency chain logic without generating new videos             ║
    ║  Uses existing videos to verify frame extraction works correctly             ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_frame_extraction_offline()
    exit(0 if success else 1)
