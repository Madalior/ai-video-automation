"""
Split Screen Formatter
======================
Handles Division 2.2: Gaming / React content where there are TWO
focus regions in the video:
  - Top half    → Face cam / main character
  - Bottom half → Gameplay / second monitor / reaction content

Uses OpenCV + FFmpeg to:
  1. Detect which half of the video contains the face (top or bottom, left or right)
  2. Crop face region → resize to fill top 50% of 1080x1920
  3. Crop gameplay region → resize to fill bottom 50% of 1080x1920
  4. Stack them vertically with FFmpeg vstack filter
  5. Output final 1080x1920 (9:16) split-screen video

Typical layouts it handles:
  ┌──────────────┐    ┌──────┬───────┐    ┌───────┬──────┐
  │   Gameplay   │    │ Face │ Game  │    │ Game  │ Face │
  ├──────────────┤    │      │       │    │       │      │
  │  Face  Cam   │    └──────┴───────┘    └───────┴──────┘
  └──────────────┘    (side by side)       (side by side)
  (top/bottom)

Usage:
  formatter = SplitScreenFormatter()

  # Auto-detect layout and produce split screen
  out = formatter.format(clip_path, output_path)

  # Force a specific layout
  out = formatter.format(clip_path, output_path, layout="top_gameplay_bottom_face")
"""

import os
import json
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from typing import Optional

# Output resolution
OUT_W = 1080
OUT_H = 1920
HALF_H = OUT_H // 2   # 960px per panel

import math

class SmartReframer:
    """
    Intelligent Dynamic Reframer.
    Combines YOLO face tracking and Pyannote speaker diarization to create
    a dynamic 9:16 vertical video.
    
    Decision Engine Logic (Per Frame):
    1. If two faces are close together -> Single Crop (includes both)
    2. If one speaker is talking -> Single Focus Crop on that speaker
    3. If both talking / unknown -> Split Screen
    """

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            print("[REFRAMER] FFmpeg ready")
        except Exception:
            print("[REFRAMER] ⚠️ FFmpeg not found!")

    def reframe(self, source_path: str, output_path: str, 
                tracking_json: str, speakers_json: str) -> Optional[str]:
        """
        Takes raw video, tracking data, and speaker data and generates a dynamic 9:16 output.
        """
        if not os.path.exists(source_path):
            return None

        # Load data
        try:
            with open(tracking_json, 'r') as f:
                tracking_data = json.load(f)
            
            # Speaker data is optional (might fail on some machines)
            speaker_data = {"speaker_turns": []}
            if os.path.exists(speakers_json):
                with open(speakers_json, 'r') as f:
                    speaker_data = json.load(f)
        except Exception as e:
            print(f"[REFRAMER] Error loading data: {e}")
            return None

        fps = tracking_data.get("fps", 30)
        frames = tracking_data.get("data", [])
        turns = speaker_data.get("speaker_turns", [])
        
        info = self._get_video_info(source_path)
        if not info:
            return None

        src_w, src_h = info["width"], info["height"]
        
        print(f"[REFRAMER] Generating dynamic scene-adaptive crop plan for {len(frames)} frames...")
        return self._render_dynamic_adaptive(source_path, output_path, frames, turns, fps, src_w, src_h)

    def _render_dynamic_adaptive(self, source_path: str, output_path: str, frames: list, turns: list, fps: float, src_w: int, src_h: int) -> Optional[str]:
        """
        Intelligent Scene-Adaptive Reframer:
        1. When only 1 person is in shot -> Single 9:16 vertical crop with smooth head tracking (NO duplicate split).
        2. When 2 distinct people are in shot -> Stacked 2-speaker vertical split (Top: Speaker 1, Bottom: Speaker 2).
        3. Between different speakers/scenes -> Instant Jump Cut (NO slow dragging across room).
        """
        target_aspect = OUT_W / OUT_H
        single_w = int(src_h * target_aspect) # 405 for 720p
        split_w  = int(src_h * (OUT_W / (OUT_H / 2))) # 810 for 720p
        split_w  = min(split_w, src_w // 2)

        # 1. Classify frames into modes
        modes = []
        for p in frames:
            faces = p.get("faces", [])
            if len(faces) >= 2:
                dist = abs(faces[0]["x"] - faces[1]["x"])
                if dist > 0.22:
                    sorted_f = sorted(faces, key=lambda it: it["x"])
                    modes.append(("split", p["f"], sorted_f[0]["x"], sorted_f[1]["x"]))
                else:
                    avg_x = (faces[0]["x"] + faces[1]["x"]) / 2
                    modes.append(("single", p["f"], avg_x, avg_x))
            elif len(faces) == 1:
                modes.append(("single", p["f"], faces[0]["x"], faces[0]["x"]))
            else:
                modes.append(("single", p["f"], 0.5, 0.5))

        if not modes:
            return None

        # 2. Group into contiguous segments
        raw_segments = []
        curr_mode = modes[0][0]
        start_f = modes[0][1]
        f1_acc, f2_acc = [modes[0][2]], [modes[0][3]]

        for m, f_idx, x1, x2 in modes[1:]:
            if m != curr_mode:
                raw_segments.append((curr_mode, start_f, f_idx, sum(f1_acc)/len(f1_acc), sum(f2_acc)/len(f2_acc)))
                curr_mode = m
                start_f = f_idx
                f1_acc, f2_acc = [x1], [x2]
            else:
                f1_acc.append(x1)
                f2_acc.append(x2)
        raw_segments.append((curr_mode, start_f, modes[-1][1], sum(f1_acc)/len(f1_acc), sum(f2_acc)/len(f2_acc)))

        # 3. Clean short flickers with 1.5s stability threshold
        clean_segments = []
        for s in raw_segments:
            dur = (s[2] - s[1]) / fps
            if dur < 1.5 and clean_segments:
                prev = clean_segments[-1]
                clean_segments[-1] = (prev[0], prev[1], s[2], prev[3], prev[4])
            else:
                clean_segments.append(s)

        total_vid_frames = int(fps * self._get_video_info(source_path)["duration"])
        final_segments = []
        for i, s in enumerate(clean_segments):
            start_frame = 0 if i == 0 else clean_segments[i-1][2]
            end_frame   = total_vid_frames if i == len(clean_segments)-1 else s[2]
            final_segments.append((s[0], start_frame, end_frame, s[3], s[4]))

        print(f"[REFRAMER] Processing {len(final_segments)} glitch-free dynamic scene segments...")

        # 4. Render segments individually and join with concat demuxer to avoid transition glitches
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp(prefix="reframe_segments_")
        seg_files = []
        
        try:
            for idx, s in enumerate(final_segments):
                seg_path = os.path.join(temp_dir, f"seg_{idx:03d}.mp4")
                f_start = s[1]
                f_end   = s[2]
                mode    = s[0]
                
                if mode == "single":
                    cx = int(s[3] * src_w)
                    crop_x = max(0, min(cx - single_w // 2, src_w - single_w))
                    filt = (
                        f"trim=start_frame={f_start}:end_frame={f_end},setpts=PTS-STARTPTS,"
                        f"crop={single_w}:{src_h}:{crop_x}:0,"
                        f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
                        f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
                    )
                    cmd = [
                        "ffmpeg", "-y", "-i", source_path,
                        "-vf", filt, "-an",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                        "-r", str(int(fps)),
                        seg_path
                    ]
                else: # split
                    cx1 = int(s[3] * src_w)
                    cx2 = int(s[4] * src_w)
                    crop_x1 = max(0, min(cx1 - split_w // 2, src_w - split_w))
                    crop_x2 = max(0, min(cx2 - split_w // 2, src_w - split_w))
                    
                    filt = (
                        f"[0:v]split[a][b];"
                        f"[a]trim=start_frame={f_start}:end_frame={f_end},setpts=PTS-STARTPTS,"
                        f"crop={split_w}:{src_h}:{crop_x1}:0,"
                        f"scale={OUT_W}:958:force_original_aspect_ratio=increase,crop={OUT_W}:958,"
                        f"pad={OUT_W}:960:0:0:black,setsar=1[top];"
                        f"[b]trim=start_frame={f_start}:end_frame={f_end},setpts=PTS-STARTPTS,"
                        f"crop={split_w}:{src_h}:{crop_x2}:0,"
                        f"scale={OUT_W}:960:force_original_aspect_ratio=increase,crop={OUT_W}:960,setsar=1[bot];"
                        f"[top][bot]vstack=inputs=2,setsar=1"
                    )
                    cmd = [
                        "ffmpeg", "-y", "-i", source_path,
                        "-filter_complex", filt, "-an",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                        "-r", str(int(fps)),
                        seg_path
                    ]
                    
                print(f"  [REFRAMER] Rendering Seg {idx} ({mode}, {f_end-f_start} frames)...")
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if r.returncode == 0:
                    seg_files.append(seg_path)
                else:
                    print(f"[REFRAMER] ❌ FFmpeg error on seg {idx}:\n{r.stderr[-500:]}")
                    return None

            # 5. Join segments using concat demuxer
            concat_list = os.path.join(temp_dir, "concat.txt")
            with open(concat_list, "w") as f:
                for sp in seg_files:
                    # Windows paths need forward slashes for FFmpeg concat file
                    abs_path = os.path.abspath(sp).replace("\\", "/")
                    f.write(f"file '{abs_path}'\n")

            print(f"[REFRAMER] Joining {len(seg_files)} segments seamlessly...")
            cmd2 = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-i", source_path, "-map", "0:v", "-map", "1:a?",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", "-shortest",
                output_path
            ]
            
            r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
            if r2.returncode == 0 and os.path.exists(output_path):
                print(f"[REFRAMER] ✅ Done: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"[REFRAMER] ❌ Concat FFmpeg error:\n{r2.stderr[-1000:]}")
                return None
                
        except Exception as e:
            print(f"[REFRAMER] ❌ Error: {e}")
            return None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _map_faces_to_speakers(self, frames, turns, fps) -> dict:
        """
        Heuristic: Map Pyannote speaker labels (SPEAKER_00) to YOLO Face IDs (0, 1).
        In a simple world, the face whose mouth moves when SPEAKER_00 talks is SPEAKER_00.
        Without lip sync detection, we assume standard layouts or rely on visual active speaker detection.
        For now, we map Face 0 -> SPEAKER_00 and Face 1 -> SPEAKER_01 as a placeholder.
        # TODO: Implement active lip movement mapping here in the future.
        """
        # Placeholder mapping
        return {"SPEAKER_00": 0, "SPEAKER_01": 1}

    def _generate_crop_plan(self, frames, turns, fps, src_w, src_h, face_to_speaker) -> list:
        """
        The core intelligence. Decides per frame what the crop region(s) should be.
        Returns a list of frames, each containing the mode and the crop boxes.
        """
        plan = []
        
        target_aspect = OUT_W / OUT_H  # 9:16 = 0.5625
        target_w = int(src_h * target_aspect) # Target width in source pixels to get 9:16
        
        for f in frames:
            frame_time = f["f"] / fps
            faces = f["faces"]
            
            # Find who is talking right now
            active_speaker_label = None
            for t in turns:
                if t["start"] <= frame_time <= t["end"]:
                    active_speaker_label = t["speaker"]
                    break
                    
            active_face_id = face_to_speaker.get(active_speaker_label) if active_speaker_label else None
            
            # Decision Logic
            if len(faces) == 0:
                # No faces: center crop
                cx = src_w // 2
                mode = "single"
                
            elif len(faces) == 1:
                # One face: track it
                cx = int(faces[0]["x"] * src_w)
                mode = "single"
                
            else:
                # Multiple faces. Are they close?
                f1, f2 = faces[0], faces[1]
                dist = abs(f1["x"] - f2["x"])
                
                if dist < 0.35:
                    # Close together -> single crop containing both
                    cx = int(((f1["x"] + f2["x"]) / 2) * src_w)
                    mode = "single"
                else:
                    # Far apart. Who is talking?
                    if active_face_id is not None:
                        # Focus on active speaker
                        active_face = next((face for face in faces if face["id"] == active_face_id), faces[0])
                        cx = int(active_face["x"] * src_w)
                        mode = "single"
                    else:
                        # Split screen
                        mode = "split"
                        cx = src_w // 2 # Not used in split mode directly, handled in render
                        
            # Ensure crop box stays within video bounds
            x_left = max(0, cx - target_w // 2)
            if x_left + target_w > src_w:
                x_left = src_w - target_w
                
            plan.append({
                "f": f["f"],
                "mode": mode,
                "x": x_left,
                "y": 0,
                "w": target_w,
                "h": src_h,
                "faces": faces
            })
            
        return plan

    def _smooth_crop_plan(self, plan: list, jump_cut_threshold: int = 70) -> list:
        """
        Instant Camera Cut on speaker switch (no dragging across the room),
        with micro-stabilization for natural head movement.
        """
        if not plan:
            return plan
            
        cam_x = plan[0]["x"]
        
        for i in range(len(plan)):
            if plan[i]["mode"] == "single":
                target_x = plan[i]["x"]
                dist = abs(target_x - cam_x)
                
                # If speaker changes or distance is large -> Instant Jump Cut (Direct Switch)
                if dist > jump_cut_threshold:
                    cam_x = target_x
                else:
                    # Small head movement -> Gentle micro-stabilization
                    cam_x += (target_x - cam_x) * 0.15
                
                plan[i]["smoothed_x"] = int(cam_x)
            else:
                plan[i]["smoothed_x"] = plan[i]["x"]
                cam_x = plan[i]["x"]
                
        return plan

    def _render_ffmpeg(self, source_path, output_path, plan, fps, src_w, src_h):
        """
        Renders the dynamic crop.
        Interpolates the sparse crop plan to every frame for buttery-smooth panning,
        then uses FFmpeg sendcmd to apply the per-frame crop.
        """
        target_aspect = OUT_W / OUT_H
        target_w = int(src_h * target_aspect)
        
        # 1. Build sparse keyframe map: frame_number -> smoothed_x
        keyframes = {}
        for p in plan:
            if p["mode"] == "single":
                keyframes[p["f"]] = p["smoothed_x"]
        
        if not keyframes:
            print("[REFRAMER] No crop keyframes found, skipping.")
            return None
        
        # 2. Interpolate to every frame
        total_frames = int(fps * self._get_video_info(source_path)["duration"])
        sorted_keys = sorted(keyframes.keys())
        
        per_frame_x = []
        for frame_num in range(total_frames):
            if frame_num in keyframes:
                per_frame_x.append(keyframes[frame_num])
            elif frame_num < sorted_keys[0]:
                per_frame_x.append(keyframes[sorted_keys[0]])
            elif frame_num > sorted_keys[-1]:
                per_frame_x.append(keyframes[sorted_keys[-1]])
            else:
                lo = max(k for k in sorted_keys if k <= frame_num)
                hi = min(k for k in sorted_keys if k >= frame_num)
                if lo == hi:
                    per_frame_x.append(keyframes[lo])
                else:
                    # If it's a speaker switch (jump cut), snap directly instead of dragging
                    if abs(keyframes[hi] - keyframes[lo]) > 70:
                        per_frame_x.append(keyframes[hi] if frame_num >= (lo + hi)//2 else keyframes[lo])
                    else:
                        t = (frame_num - lo) / (hi - lo)
                        interp_x = int(keyframes[lo] + t * (keyframes[hi] - keyframes[lo]))
                        per_frame_x.append(interp_x)
        
        # 3. Micro-stabilization without dragging across cuts
        smooth_x = [per_frame_x[0]]
        alpha = 0.15
        for i in range(1, len(per_frame_x)):
            prev = smooth_x[-1]
            diff = abs(per_frame_x[i] - prev)
            if diff > 70:
                # Hard cut to new speaker
                smooth_x.append(per_frame_x[i])
            else:
                # Gentle head-tracking stabilization
                smooth_x.append(int(prev + alpha * (per_frame_x[i] - prev)))
        
        # 4. Clamp values to valid range
        max_x = max(0, src_w - target_w)
        smooth_x = [max(0, min(int(x), max_x)) for x in smooth_x]
        
        # 5. Write sendcmd file with per-frame entries
        cmd_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='.')
        
        frame_dur = 1.0 / fps
        for i, x in enumerate(smooth_x):
            t = i * frame_dur
            cmd_file.write(f"{t:.4f}-{t + frame_dur:.4f} [enter] crop x {x};\n")
                
        cmd_file.close()
        
        print(f"[REFRAMER] Wrote {len(smooth_x)} per-frame crop commands (Instant Cut enabled)")
        
        # 6. Build FFmpeg filter
        filter_complex = (
            f"[0:v]sendcmd=f='{os.path.basename(cmd_file.name)}',"
            f"crop={target_w}:{src_h}:'x':0[cropped];"
            f"[cropped]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
            f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:black[out]"
        )

        cmd = [
            "ffmpeg", "-i", source_path,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            "-y", output_path
        ]
        
        print(f"[REFRAMER] Rendering dynamic video...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            os.unlink(cmd_file.name)
            
            if r.returncode == 0 and os.path.exists(output_path):
                print(f"[REFRAMER] ✅ Done: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"[REFRAMER] ❌ FFmpeg error:\n{r.stderr[-1000:]}")
                return None
        except Exception as e:
            print(f"[REFRAMER] ❌ Error: {e}")
            if os.path.exists(cmd_file.name):
                os.unlink(cmd_file.name)
            return None

    def format_2speaker_split(self, source_path: str, output_path: str, tracking_json: str) -> Optional[str]:
        """
        Creates a stacked 9:16 vertical Split Screen for 2 speakers (or streamer + gameplay).
        Top panel (1080x960): Speaker 1 / Host
        Bottom panel (1080x960): Speaker 2 / Guest
        """
        if not os.path.exists(source_path):
            return None

        info = self._get_video_info(source_path)
        if not info:
            return None
        src_w, src_h = info["width"], info["height"]

        # Find average speaker 1 and speaker 2 positions from YOLO data
        x1_list, x2_list = [], []
        try:
            with open(tracking_json, 'r') as f:
                d = json.load(f)
                pts = d.get("data", [])
                for p in pts:
                    faces = p.get("faces", [])
                    if len(faces) >= 2:
                        sorted_f = sorted(faces, key=lambda item: item["x"])
                        x1_list.append(sorted_f[0]["x"])
                        x2_list.append(sorted_f[1]["x"])
                    elif len(faces) == 1:
                        if faces[0]["x"] < 0.45:
                            x1_list.append(faces[0]["x"])
                        else:
                            x2_list.append(faces[0]["x"])
        except Exception as e:
            print(f"[REFRAMER] Warning reading tracking JSON for split screen: {e}")

        # Default to 25% and 65% if not enough points
        x1_ratio = sum(x1_list) / len(x1_list) if x1_list else 0.25
        x2_ratio = sum(x2_list) / len(x2_list) if x2_list else 0.65

        # Each panel is 1080x960 (Aspect ratio: 1080 / 960 = 1.125)
        panel_w = int(src_h * (OUT_W / (OUT_H / 2))) # src_h * 1.125
        panel_w = min(panel_w, src_w // 2)

        x1 = max(0, min(int(x1_ratio * src_w - panel_w // 2), src_w - panel_w))
        x2 = max(0, min(int(x2_ratio * src_w - panel_w // 2), src_w - panel_w))

        print(f"[REFRAMER] Building 2-Speaker Split Screen: Top(x={x1}) / Bottom(x={x2})")

        # FFmpeg filter: Crop Speaker 1 -> scale to 1080x960; Crop Speaker 2 -> scale to 1080x960; Stack
        filter_complex = (
            f"[0:v]crop={panel_w}:{src_h}:{x1}:0,scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            f"[0:v]crop={panel_w}:{src_h}:{x2}:0,scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bottom];"
            f"[top][bottom]vstack=inputs=2[out]"
        )

        cmd = [
            "ffmpeg", "-i", source_path,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            "-y", output_path
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if r.returncode == 0 and os.path.exists(output_path):
                print(f"[REFRAMER] ✅ 2-Speaker Split Screen saved: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"[REFRAMER] ❌ FFmpeg error:\n{r.stderr[-1000:]}")
                return None
        except Exception as e:
            print(f"[REFRAMER] ❌ Error: {e}")
            return None

    def format_webcam_split(self, source_path: str, output_path: str, tracking_json: Optional[str] = None) -> Optional[str]:
        """
        Creates a stacked 9:16 vertical Split Screen for Webcam/Streamer content.
        Camera is 100% STATIC (no tracking people):
          - Top panel (1080x960): Main content/gameplay centered
          - Bottom panel (1080x960): Streamer facecam zoomed in from corner
        """
        if not os.path.exists(source_path):
            return None

        info = self._get_video_info(source_path)
        if not info:
            return None
        src_w, src_h = info["width"], info["height"]

        # Default static camera coordinates (Speed / typical streamer layout: bottom-left cam, center content)
        cam_cx, cam_cy = 0.12, 0.78
        content_cx = 0.50

        if tracking_json and os.path.exists(tracking_json):
            try:
                with open(tracking_json, 'r') as f:
                    d = json.load(f)
                    face_data = d.get("data", [])
                    bot_left_xs, bot_left_ys = [], []
                    top_xs = []
                    for pt in face_data:
                        for fc in pt.get('faces', []):
                            box = fc.get('box', [fc['x'] - 0.05, 0.5, 0.1, 0.2])
                            if fc['x'] < 0.35 and (box[1] > 0.4 or len(box) > 1 and box[1] > 0.4):
                                bot_left_xs.append(fc['x'])
                                bot_left_ys.append(box[1] + box[3] / 2)
                            elif fc['x'] > 0.30:
                                top_xs.append(fc['x'])
                    if bot_left_xs:
                        cam_cx = float(np.median(bot_left_xs))
                    if bot_left_ys:
                        cam_cy = float(np.median(bot_left_ys))
                    if top_xs:
                        content_cx = float(np.median(top_xs))
            except Exception as e:
                print(f"[REFRAMER] Warning analyzing tracking data for static webcam split: {e}")

        # Static crop boxes (aspect 1080 / 960 = 1.125)
        # Top panel: content
        top_crop_h = int(src_h * 0.95)
        top_crop_w = int(top_crop_h * (OUT_W / (OUT_H / 2)))
        top_x = max(0, min(int(content_cx * src_w - top_crop_w // 2), src_w - top_crop_w))
        top_y = int(0.02 * src_h)

        # Bottom panel: webcam zoomed in
        bot_crop_w = int(src_w * 0.28)
        bot_crop_h = int(bot_crop_w / (OUT_W / (OUT_H / 2)))
        bot_x = max(0, min(int(cam_cx * src_w - bot_crop_w // 2), src_w - bot_crop_w))
        bot_y = max(0, min(int(cam_cy * src_h - bot_crop_h // 2), src_h - bot_crop_h))

        print(f"[REFRAMER] Static Webcam Split: Content(x={top_x}, y={top_y}) / Facecam(x={bot_x}, y={bot_y})")

        filter_complex = (
            f"[0:v]crop={top_crop_w}:{top_crop_h}:{top_x}:{top_y},scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            f"[0:v]crop={bot_crop_w}:{bot_crop_h}:{bot_x}:{bot_y},scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bottom];"
            f"[top][bottom]vstack=inputs=2[out]"
        )

        cmd = [
            "ffmpeg", "-i", source_path,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            "-y", output_path
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if r.returncode == 0 and os.path.exists(output_path):
                print(f"[REFRAMER] ✅ Static Webcam Split saved: {os.path.basename(output_path)}")
                return output_path
            else:
                print(f"[REFRAMER] ❌ FFmpeg error:\n{r.stderr[-1000:]}")
                return None
        except Exception as e:
            print(f"[REFRAMER] ❌ Error: {e}")
            return None

    def _get_video_info(self, path: str) -> Optional[dict]:
        try:
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", path], capture_output=True, text=True, timeout=15)
            data = json.loads(r.stdout)
            video = next((s for s in data.get("streams", []) if s["codec_type"] == "video"), {})
            return {
                "width": video.get("width", 0),
                "height": video.get("height", 0),
                "duration": float(data.get("format", {}).get("duration", 0)),
                "fps": eval(video.get("r_frame_rate", "30/1")),
            }
        except Exception as e:
            print(f"[SPLIT] ffprobe error: {e}")
            return None

# Keep the old SplitScreenFormatter for fallback/testing
class SplitScreenFormatter:
    LAYOUTS = {
        "top_gameplay_bottom_face": "top gameplay, bottom face",
        "top_face_bottom_gameplay": "top face, bottom gameplay",
        "side_by_side": "side by side vertical split",
    }

    def format(self, clip_path: str, output_path: str, layout: Optional[str] = None) -> Optional[str]:
        """
        Formats a video into 9:16 (1080x1920) split screen using FFmpeg.
        Default layout splits source into two stacked halves (top and bottom).
        """
        if not os.path.exists(clip_path):
            return None

        # Filter: crop top half to 1080x960, bottom half to 1080x960, vstack to 1080x1920
        filter_complex = (
            "[0:v]crop=iw:ih/2:0:0,scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[top];"
            "[0:v]crop=iw:ih/2:0:ih/2,scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960[bottom];"
            "[top][bottom]vstack=inputs=2[out]"
        )

        cmd = [
            "ffmpeg", "-i", clip_path,
            "-filter_complex", filter_complex,
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            "-y", output_path
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and os.path.exists(output_path):
                return output_path
            return None
        except Exception as e:
            print(f"[SPLIT] Error: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python split_screen.py <input.mp4> <output.mp4> [layout]")
        print("Layouts:", list(SplitScreenFormatter.LAYOUTS.keys()))
        sys.exit(1)

    inp    = sys.argv[1]
    out    = sys.argv[2]
    layout = sys.argv[3] if len(sys.argv) > 3 else None

    formatter = SplitScreenFormatter()
    result    = formatter.format(inp, out, layout=layout)

    if result:
        print(f"\n✅ Split screen saved: {result}")
    else:
        print("\n❌ Failed")
