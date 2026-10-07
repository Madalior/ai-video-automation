"""
MediaPipe Full-Range Face Tracker
Uses model_selection=1 (Full Range - up to 5 meters) to reliably detect
both close-up speakers AND distant/wide-table shots (which FaceMesh misses).
Includes a 5-frame grace period for hand occlusions and EMA smoothing.
"""
import cv2
import json
import argparse
import mediapipe as mp
import time
from pathlib import Path


def track_faces(video_path, output_json, smooth_alpha=0.3, grace_frames=5):
    start_time = time.time()
    
    mp_face_detection = mp.solutions.face_detection
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[FaceTracker] Tracking {total_frames} frames from {video_path} (Full-Range)")
    
    tracking_data = []
    prev_faces = []
    last_known_faces = []
    frames_since_detection = 0
    
    with mp_face_detection.FaceDetection(
        model_selection=1,          # 1 = Full Range (0-5m, handles wide shots), 0 = Short Range
        min_detection_confidence=0.45
    ) as face_detection:
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            h, w = frame.shape[:2]
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(image_rgb)
            
            raw_faces = []
            if results.detections:
                for det in results.detections:
                    box = det.location_data.relative_bounding_box
                    cx = box.xmin + box.width / 2
                    cy = box.ymin + box.height / 2
                    raw_faces.append({
                        'x': cx,
                        'box': [box.xmin, box.ymin, box.width, box.height],
                        'score': float(det.score[0]) if det.score else 1.0
                    })
                # Sort left to right
                raw_faces.sort(key=lambda f: f['x'])
                last_known_faces = raw_faces
                frames_since_detection = 0
            else:
                # Occlusion grace period: hold last known faces if lost for <= grace_frames
                frames_since_detection += 1
                if frames_since_detection <= grace_frames and last_known_faces:
                    raw_faces = last_known_faces
                else:
                    raw_faces = []
            
            # Smooth face coordinates between frames
            smoothed_faces = _smooth_faces(raw_faces, prev_faces, alpha=smooth_alpha)
            prev_faces = smoothed_faces if smoothed_faces else prev_faces
            
            tracking_data.append({
                'f': frame_idx,
                'faces': smoothed_faces
            })
            
            frame_idx += 1
            if frame_idx % 200 == 0:
                print(f"[FaceTracker] Processed {frame_idx}/{total_frames} frames...")
                
    cap.release()
    
    out_dict = {
        'fps': fps,
        'data': tracking_data
    }
    
    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(out_dict, f)
        
    print(f"[FaceTracker] Complete in {time.time() - start_time:.1f}s -> {output_json}")


def _smooth_faces(faces_current, faces_prev, alpha=0.3):
    if not faces_prev or not faces_current:
        return faces_current
    if len(faces_current) != len(faces_prev):
        return faces_current
        
    smoothed = []
    for curr in faces_current:
        cx_curr = curr['x']
        closest_prev = None
        min_dist = float('inf')
        for prev in faces_prev:
            dist = abs(cx_curr - prev['x'])
            if dist < min_dist:
                min_dist = dist
                closest_prev = prev
                
        if closest_prev and min_dist < 0.15:
            cx_smooth = alpha * cx_curr + (1 - alpha) * closest_prev['x']
            smoothed.append({
                'x': cx_smooth,
                'box': curr.get('box', [])
            })
        else:
            smoothed.append(curr)
            
    return smoothed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediaPipe Full-Range Face Tracker")
    parser.add_argument("video_path", help="Path to input video")
    parser.add_argument("output_json", help="Path to output JSON")
    parser.add_argument("--alpha", type=float, default=0.3, help="Smoothing alpha (0.0-1.0)")
    parser.add_argument("--grace", type=int, default=5, help="Grace frames during occlusion")
    args = parser.parse_args()
    
    track_faces(args.video_path, args.output_json, smooth_alpha=args.alpha, grace_frames=args.grace)
