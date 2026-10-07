"""
IRL / Outdoor / Dynamic Stream 100% Full-Screen 9:16 Reframe Renderer
Finalized from September 5 Live Stream Testing (Step 5215 - 5230)

Layout:
- 100% Full-Screen Dynamic 9:16 Reframe (Zero black bars, no awkward split panels)
- Smooth Exponential Moving Average (EMA) camera panning (alpha=0.08)
- Crowd / Crew filtering (isolates main streamer, ignores background bystanders)
"""

import cv2
import json
import numpy as np
import subprocess
import os
import sys
import argparse


def render_irl_dynamic(src_path, faces_json, out_path, out_w=1080, out_h=1920, alpha=0.08, crew_thresh=0.70):
    print(f"[IRLReframe] Rendering: {src_path} -> {out_path}")
    temp_v = out_path + ".temp_video.mp4"
    
    cap = cv2.VideoCapture(src_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with open(faces_json, 'r') as f:
        face_data = json.load(f)['data']
    frame_lookup = {pt['f']: pt.get('faces', []) for pt in face_data}
    
    # 9:16 aspect ratio crop calculation
    crop_w = int(h * (out_w / out_h))  # e.g. 720 * (9/16) = 405
    max_x = w - crop_w
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_v, fourcc, fps, (out_w, out_h))
    
    current_cx = 0.50 * w
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        faces = frame_lookup.get(frame_idx, [])
        # Find main streamer / subject (filter out crew/crowd walking on far right x >= crew_thresh)
        subject_faces = [fc for fc in faces if fc['x'] < crew_thresh]
        if subject_faces:
            target_cx = subject_faces[0]['x'] * w
        else:
            # Maintain current position or gently bias toward center
            target_cx = 0.50 * w
            
        # Smooth camera panning with exponential moving average
        current_cx = (1 - alpha) * current_cx + alpha * target_cx
        
        x1 = int(current_cx - crop_w // 2)
        x1 = max(0, min(x1, max_x))
        
        crop = frame[:, x1:x1 + crop_w]
        out_frame = cv2.resize(crop, (out_w, out_h))
        out.write(out_frame)
        frame_idx += 1
        
        if frame_idx % 200 == 0:
            print(f"[IRLReframe] Rendered {frame_idx}/{total_frames} frames...")
            
    cap.release()
    out.release()
    print(f"[IRLReframe] Video frames rendered ({frame_idx} frames). Merging audio...")
    
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
        '-i', temp_v,
        '-i', src_path,
        '-map', '0:v:0',
        '-map', '1:a:0?',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'aac', '-b:a', '128k',
        out_path
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(temp_v):
        try: os.remove(temp_v)
        except Exception: pass
        
    print(f"[SUCCESS] Saved: {out_path} ({os.path.getsize(out_path)/(1024*1024):.2f} MB)")
    return out_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="IRL Outdoor Stream Dynamic 9:16 Reframe Renderer")
    parser.add_argument("src_video", help="Input 16:9 video path")
    parser.add_argument("faces_json", help="Path to MediaPipe tracking JSON")
    parser.add_argument("out_video", help="Output 9:16 vertical MP4 path")
    parser.add_argument("--alpha", type=float, default=0.08, help="Smoothing alpha (default 0.08)")
    parser.add_argument("--crew-thresh", type=float, default=0.70, help="Crew x threshold filter (default 0.70)")
    args = parser.parse_args()
    
    render_irl_dynamic(args.src_video, args.faces_json, args.out_video, alpha=args.alpha, crew_thresh=args.crew_thresh)
