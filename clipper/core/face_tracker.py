import os
import cv2
import json
import math
import numpy as np
from pathlib import Path


class OneEuroFilter:
    """
    1€ (One Euro) Filter — the industry-standard for smooth face tracking.
    Borrowed from auto-vertical-reframe / Google MediaPipe AutoFlip.
    
    - When the face is STILL → aggressive smoothing (no jitter)
    - When the face MOVES → filter becomes responsive (no lag)
    
    Parameters:
        min_cutoff: Lower = smoother when still (default 0.004 Hz = ultra smooth)
        beta: Higher = more responsive during fast motion (default 0.005)
        d_cutoff: Cutoff for derivative estimation
    """
    def __init__(self, x0: float, min_cutoff: float = 0.004, beta: float = 0.005, d_cutoff: float = 1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = x0
        self.dx_prev = 0.0

    def _alpha(self, cutoff: float, dt: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / max(dt, 1e-6))

    def __call__(self, x: float, dt: float = 1.0) -> float:
        # Derivative estimation
        a_d = self._alpha(self.d_cutoff, dt)
        dx = (x - self.x_prev) / max(dt, 1e-6)
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        # Adaptive cutoff: smooth when slow, responsive when fast
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(cutoff, dt)
        x_hat = a * x + (1.0 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat


class FaceTracker:
    def __init__(self, sample_rate: int = 5):
        """
        Professional face tracker upgraded to YOLO26 (Ultralytics).
        Uses YOLO for robust multi-face detection and ByteTrack internally,
        paired with 1€ Filter + Gaussian post-smooth for silky camera moves.
        """
        self.sample_rate = sample_rate
        
        # Load YOLO model — auto-download if missing
        try:
            from ultralytics import YOLO
            model_path = "yolov8n-face.pt"
            if not os.path.exists(model_path):
                print("[TRACKER] yolov8n-face.pt not found, downloading...")
                import requests
                url = "https://huggingface.co/arnabdhar/YOLOv8-Face-Detection/resolve/main/model.pt"
                r = requests.get(url, allow_redirects=True, timeout=120)
                if r.status_code == 200:
                    with open(model_path, "wb") as f:
                        f.write(r.content)
                    print(f"[TRACKER] Downloaded yolov8n-face.pt ({len(r.content)/1024/1024:.1f} MB)")
                else:
                    raise RuntimeError(f"Failed to download face model: HTTP {r.status_code}")
            self.model = YOLO(model_path)
        except ImportError:
            print("[TRACKER] Error: ultralytics not installed. Run: pip install ultralytics")
            raise

        # Dead zone: ignore face movement smaller than this (prevents micro-jitter)
        self.dead_zone = 0.06
        # Max step per sample: clamp how fast the camera can pan
        self.max_step = 0.015

    def track(self, video_path: str, output_json: str) -> list:
        """
        Tracks ALL faces in the video using YOLO.
        Returns and saves JSON:
        [
          {"f": 0, "faces": [{"id": 0, "x": 0.5, "box": [x,y,w,h]}, ...]},
          ...
        ]
        """
        print(f"[TRACKER] Analyzing {video_path} with YOLO...", flush=True)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("[TRACKER] Error: Could not open video.", flush=True)
            return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        raw_data = []

        frame_idx = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            if frame_idx % self.sample_rate == 0:
                # Run YOLO detection + tracking
                # persist=True enables ByteTrack for consistent IDs
                results = self.model.track(image, persist=True, verbose=False)
                
                frame_faces = []
                
                if results and len(results) > 0 and results[0].boxes:
                    boxes = results[0].boxes
                    for box in boxes:
                        # Ensure we have an ID from the tracker
                        face_id = int(box.id[0]) if box.id is not None else 0
                        
                        # Get bbox coordinates
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        w, h = x2 - x1, y2 - y1
                        
                        # Calculate normalized center X
                        detected_x = (x1 + w / 2.0) / frame_width
                        
                        frame_faces.append({
                            "id": face_id,
                            "x": round(detected_x, 4),
                            "box": [round(x1), round(y1), round(w), round(h)]
                        })

                raw_data.append({
                    "f": frame_idx,
                    "faces": frame_faces
                })

            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"[TRACKER] Processed {frame_idx}/{total_frames} frames...", flush=True)

        cap.release()

        # === SMOOTHING PIPELINE ===
        # Since we now have multiple faces, we need to smooth each ID independently
        # Extract unique IDs
        all_ids = set()
        for d in raw_data:
            for f in d["faces"]:
                all_ids.add(f["id"])
                
        smoothed_data = []
        for d in raw_data:
            smoothed_data.append({"f": d["f"], "faces": []})
            
        # Smooth each ID's trajectory
        for face_id in all_ids:
            # Extract just this ID's X coordinates
            id_trajectory = []
            for i, d in enumerate(raw_data):
                face = next((f for f in d["faces"] if f["id"] == face_id), None)
                if face:
                    id_trajectory.append({"f": d["f"], "idx": i, "x": face["x"]})
                    
            if not id_trajectory: continue
            
            # Apply 1 Euro Filter
            euro = self._apply_one_euro(id_trajectory)
            # Bidirectional EMA
            bidi = self._smooth_bidirectional(euro, alpha=0.08)
            # Gaussian final pass
            final_x = self._gaussian_smooth(bidi, sigma=3.0)
            
            # Put smoothed X back into the main data structure
            for point in final_x:
                idx = point["idx"]
                # Find the original face dict to copy the box
                orig_face = next(f for f in raw_data[idx]["faces"] if f["id"] == face_id)
                
                smoothed_data[idx]["faces"].append({
                    "id": face_id,
                    "x": point["x"],
                    "box": orig_face["box"]
                })

        # Save to JSON
        with open(output_json, 'w') as f:
            json.dump({"fps": fps, "data": smoothed_data}, f)

        print(f"[TRACKER] Saved tracking data to {output_json} ({len(smoothed_data)} points)", flush=True)
        return smoothed_data

    def _apply_one_euro(self, data: list) -> list:
        """Apply 1€ filter forward pass."""
        if not data:
            return data
        filt = OneEuroFilter(data[0]["x"], min_cutoff=0.004, beta=0.005)
        result = []
        for d in data:
            filtered_x = filt(d["x"], dt=1.0)
            result.append({**d, "x": round(filtered_x, 4)})
        return result

    def _smooth_bidirectional(self, data: list, alpha: float = 0.08) -> list:
        """Two-pass bidirectional EMA for lag-free smoothing."""
        if not data:
            return data

        # Forward
        forward = []
        cx = data[0]["x"]
        for d in data:
            cx = alpha * d["x"] + (1.0 - alpha) * cx
            forward.append(cx)

        # Backward
        backward = [0.0] * len(data)
        cx = data[-1]["x"]
        for i in range(len(data) - 1, -1, -1):
            cx = alpha * data[i]["x"] + (1.0 - alpha) * cx
            backward[i] = cx

        return [
            {**data[i], "x": round((forward[i] + backward[i]) / 2.0, 4)}
            for i in range(len(data))
        ]

    def _gaussian_smooth(self, data: list, sigma: float = 3.0) -> list:
        """Final Gaussian kernel smoothing pass for silky output."""
        if len(data) < 3:
            return data

        x_values = np.array([d["x"] for d in data], dtype=np.float64)
        kernel_size = int(sigma * 6) | 1  # Ensure odd
        kernel_size = max(3, min(kernel_size, len(x_values)))
        if kernel_size % 2 == 0:
            kernel_size += 1

        kernel = cv2.getGaussianKernel(kernel_size, sigma).flatten()
        # Pad edges to avoid boundary artifacts
        padded = np.pad(x_values, kernel_size // 2, mode='edge')
        smoothed = np.convolve(padded, kernel, mode='valid')

        return [
            {**data[i], "x": round(float(smoothed[i]), 4)}
            for i in range(len(data))
        ]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        tracker = FaceTracker()
        tracker.track(sys.argv[1], "tracking.json")

