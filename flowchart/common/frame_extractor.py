"""
Frame Extraction Utility for Scene Continuity

Extracts frames from videos to use as reference images for the next scene,
implementing Veo 3.1's first/last frame control technique.
"""

import cv2
import os


def extract_last_frame(video_path, output_path=None):
    """
    Extract the last frame from a video.
    
    Args:
        video_path: Path to video file
        output_path: Where to save frame (auto-generated if None)
    
    Returns:
        Path to extracted frame image, or None if failed
    """
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Get total frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames == 0:
            print(f"[ERROR] Video has no frames: {video_path}")
            cap.release()
            return None
        
        # Go to last frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"[ERROR] Could not read last frame from: {video_path}")
            return None
        
        # Auto-generate output path if not provided
        if not output_path:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_last_frame.jpg"
        
        # Save frame
        cv2.imwrite(output_path, frame)
        print(f"[SUCCESS] Extracted last frame to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Frame extraction failed: {e}")
        return None


def extract_first_frame(video_path, output_path=None):
    """
    Extract the first frame from a video.
    
    Args:
        video_path: Path to video file
        output_path: Where to save frame (auto-generated if None)
    
    Returns:
        Path to extracted frame image, or None if failed
    """
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Read first frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"[ERROR] Could not read first frame from: {video_path}")
            return None
        
        # Auto-generate output path if not provided
        if not output_path:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_first_frame.jpg"
        
        # Save frame
        cv2.imwrite(output_path, frame)
        print(f"[SUCCESS] Extracted first frame to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Frame extraction failed: {e}")
        return None


def extract_frame_at_time(video_path, time_seconds, output_path=None):
    """
    Extract a frame at specific time.
    
    Args:
        video_path: Path to video file
        time_seconds: Time position in seconds
        output_path: Where to save frame (auto-generated if None)
    
    Returns:
        Path to extracted frame image, or None if failed
    """
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        return None
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Get FPS and calculate frame number
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_seconds * fps)
        
        # Set position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"[ERROR] Could not read frame at {time_seconds}s from: {video_path}")
            return None
        
        # Auto-generate output path if not provided
        if not output_path:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_frame_{int(time_seconds)}s.jpg"
        
        # Save frame
        cv2.imwrite(output_path, frame)
        print(f"[SUCCESS] Extracted frame at {time_seconds}s to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Frame extraction failed: {e}")
        return None


# Test/Demo
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python frame_extractor.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    print("="*60)
    print("FRAME EXTRACTOR TEST")
    print("="*60)
    
    print("\nExtracting first frame...")
    first = extract_first_frame(video_path)
    
    print("\nExtracting last frame...")
    last = extract_last_frame(video_path)
    
    print("\nExtracting frame at 4 seconds...")
    mid = extract_frame_at_time(video_path, 4.0)
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"First: {first}")
    print(f"Last: {last}")
    print(f"Mid: {mid}")
