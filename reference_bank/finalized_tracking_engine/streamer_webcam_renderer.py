"""
Streamer / Webcam Reaction Video Split-Screen Renderer
Finalized from September 5 Live Stream Testing (Step 5198 - 5230)

Layout:
- Top Panel (1080x960): Focuses on the main video / gameplay / talent performer
- Bottom Panel (1080x960): Automatically isolates & zooms into the streamer reaction webcam in corner
- 4px crisp white divider line, perfectly synchronized audio
"""

import cv2
import json
import numpy as np
import subprocess
import os
import sys
import argparse


def render_webcam_split(src_path, faces_json, out_path, panel_w=1080, panel_h=960):
    print(f"[WebcamSplit] Rendering: {src_path} -> {out_path}")
    temp_v = out_path + ".temp_video.mp4"
    
    cap = cv2.VideoCapture(src_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with open(faces_json, 'r') as f:
        face_data = json.load(f)['data']
    frame_lookup = {pt['f']: pt.get('faces', []) for pt in face_data}
    
    # Analyze webcam position:
    # Streamer reaction facecam is typically in bottom-left or corner
    bot_left_xs, bot_left_ys = [], []
    top_xs, top_ys = [], []
    for pt in face_data:
        for fc in pt.get('faces', []):
            if fc['x'] < 0.35 and fc.get('box', [0, 0, 0, 0])[1] > 0.4:
                bot_left_xs.append(fc['x'])
                bot_left_ys.append(fc['box'][1] + fc['box'][3] / 2)
            elif fc['x'] > 0.30:
                top_xs.append(fc['x'])
                top_ys.append(fc.get('box', [0, 0, 0, 0])[1] + fc.get('box', [0, 0, 0, 0])[3] / 2)
                
    cam_cx = sum(bot_left_xs) / len(bot_left_xs) if bot_left_xs else 0.11
    cam_cy = sum(bot_left_ys) / len(bot_left_ys) if bot_left_ys else 0.78
    top_cx = sum(top_xs) / len(top_xs) if top_xs else 0.52
    
    print(f"[WebcamSplit] Detected Streamer Facecam at x={cam_cx:.2f}, y={cam_cy:.2f}; Main content at x={top_cx:.2f}")
    
    # Target 1080 x 1920 (top 1080x960 + bottom 1080x960)
    out_h = panel_h * 2
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_v, fourcc, fps, (panel_w, out_h))
    
    # Top panel crop from source
    top_crop_h = int(h * 0.95)
    top_crop_w = int(top_crop_h * (panel_w / panel_h))
    top_x1 = max(0, min(int(top_cx * w - top_crop_w // 2), w - top_crop_w))
    top_y1 = int(0.02 * h)
    
    # Bottom panel (streamer webcam zoomed in)
    bot_crop_w = int(w * 0.28)
    bot_crop_h = int(bot_crop_w / (panel_w / panel_h))
    bot_x1 = max(0, min(int(cam_cx * w - bot_crop_w // 2), w - bot_crop_w))
    bot_y1 = max(0, min(int(cam_cy * h - bot_crop_h // 2), h - bot_crop_h))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Optional dynamic micro-adjustment for top panel if talent moves
        curr_faces = frame_lookup.get(frame_idx, [])
        talent_faces = [fc for fc in curr_faces if fc['x'] > 0.35]
        if talent_faces:
            t_cx = talent_faces[0]['x']
            tx1 = max(0, min(int(t_cx * w - top_crop_w // 2), w - top_crop_w))
            top_x1 = int(0.9 * top_x1 + 0.1 * tx1)
            
        top_crop = frame[top_y1:top_y1 + top_crop_h, top_x1:top_x1 + top_crop_w]
        top_panel = cv2.resize(top_crop, (panel_w, panel_h))
        
        bot_crop = frame[bot_y1:bot_y1 + bot_crop_h, bot_x1:bot_x1 + bot_crop_w]
        bot_panel = cv2.resize(bot_crop, (panel_w, panel_h))
        
        out_frame = np.zeros((out_h, panel_w, 3), dtype=np.uint8)
        out_frame[0:panel_h, :] = top_panel
        out_frame[panel_h:out_h, :] = bot_panel
        cv2.line(out_frame, (0, panel_h), (panel_w, panel_h), (255, 255, 255), 4)
        
        out.write(out_frame)
        frame_idx += 1
        
        if frame_idx % 200 == 0:
            print(f"[WebcamSplit] Rendered {frame_idx}/{total_frames} frames...")
            
    cap.release()
    out.release()
    print(f"[WebcamSplit] Video frames rendered ({frame_idx} frames). Merging audio...")
    
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
    parser = argparse.ArgumentParser(description="Streamer Reaction Webcam Split Screen Renderer")
    parser.add_argument("src_video", help="Input 16:9 video path")
    parser.add_argument("faces_json", help="Path to MediaPipe tracking JSON")
    parser.add_argument("out_video", help="Output 9:16 vertical MP4 path")
    args = parser.parse_args()
    
    render_webcam_split(args.src_video, args.faces_json, args.out_video)
