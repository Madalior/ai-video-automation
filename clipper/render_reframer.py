"""
Remotion SmartReframer Renderer
===============================
Python script that:
1. Copies the source video to Remotion's public/ folder
2. Prepares the tracking data as Remotion input props
3. Calls `npx remotion render` to produce the final 1080x1920 video

Usage:
    python render_reframer.py <source_video> <tracking_json> <output_path>
    
Example:
    python render_reframer.py output/tests/podcast_1000f.mp4 output/tests/face_tracking_result.json output/tests/remotion_reframed.mp4
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REMOTION_DIR = Path(__file__).parent / "remotion"
PUBLIC_DIR = REMOTION_DIR / "public"


def render_reframed_video(
    source_video: str,
    tracking_json: str,
    output_path: str,
    fps: int = 25,
    source_width: int = 1280,
    source_height: int = 720,
    transition_frames: int = 8,
    debounce_seconds: float = 1.5,
    face_distance_threshold: float = 0.22,
) -> str | None:
    """
    Renders a Smart Reframed 9:16 video using Remotion.
    
    Returns the output path on success, None on failure.
    """
    # 1. Copy source video to Remotion's public folder
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    video_name = Path(source_video).name
    public_video = PUBLIC_DIR / video_name
    
    print(f"[REMOTION-REFRAMER] Copying {video_name} to public/...")
    shutil.copy2(source_video, public_video)
    
    # 2. Load tracking data
    with open(tracking_json, "r") as f:
        tracking_data = json.load(f)
    
    data_fps = tracking_data.get("fps", fps)
    data_points = tracking_data.get("data", [])
    
    # Calculate duration in frames
    if data_points:
        max_frame = max(pt["f"] for pt in data_points)
    else:
        max_frame = 1000
    
    total_frames = max_frame + 1
    
    print(f"[REMOTION-REFRAMER] {len(data_points)} tracking points, {total_frames} frames @ {data_fps} fps")
    
    # 3. Build Remotion input props
    props = {
        "videoSrc": video_name,
        "trackingData": tracking_data,
        "sourceWidth": source_width,
        "sourceHeight": source_height,
        "faceDistanceThreshold": face_distance_threshold,
        "debounceSeconds": debounce_seconds,
        "transitionFrames": transition_frames,
        "trackingSmoothing": 0.85,
    }
    
    # Write props to temp file
    props_file = REMOTION_DIR / "reframer_props.json"
    with open(props_file, "w") as f:
        json.dump(props, f)
    
    print(f"[REMOTION-REFRAMER] Props written to {props_file.name}")
    
    # 4. Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    output_abs = os.path.abspath(output_path)
    
    # 5. Render with Remotion CLI
    cmd = [
        "npx", "remotion", "render",
        "SmartReframer",
        output_abs,
        "--props", str(props_file),
        "--frames", f"0-{total_frames - 1}",
        "--concurrency", "4",
        "--log", "verbose",
    ]
    
    print(f"[REMOTION-REFRAMER] Rendering {total_frames} frames → {output_path}")
    print(f"  Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        if result.returncode == 0 and os.path.exists(output_abs):
            size_mb = os.path.getsize(output_abs) / (1024 * 1024)
            print(f"[REMOTION-REFRAMER] ✅ Done! {output_path} ({size_mb:.1f} MB)")
            return output_path
        else:
            print(f"[REMOTION-REFRAMER] ❌ Render failed (exit code {result.returncode})")
            if result.stderr:
                # Print last 1000 chars of stderr
                print(result.stderr[-1000:])
            if result.stdout:
                print(result.stdout[-500:])
            return None
            
    except subprocess.TimeoutExpired:
        print("[REMOTION-REFRAMER] ❌ Render timed out after 600s")
        return None
    except Exception as e:
        print(f"[REMOTION-REFRAMER] ❌ Error: {e}")
        return None
    finally:
        # Cleanup public video copy
        if public_video.exists():
            public_video.unlink()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python render_reframer.py <source_video> <tracking_json> <output_path>")
        print("\nExample:")
        print("  python render_reframer.py output/tests/podcast_1000f.mp4 output/tests/face_tracking_result.json output/tests/remotion_reframed.mp4")
        sys.exit(1)
    
    src = sys.argv[1]
    tracking = sys.argv[2]
    out = sys.argv[3]
    
    render_reframed_video(src, tracking, out)
