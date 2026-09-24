import cv2
import json
import numpy as np
import subprocess
import os
import time
from collections import deque


def get_active_speakers(speaker_turns, current_time):
    """Returns a set of all speakers active at the given time."""
    active = set()
    for turn in speaker_turns:
        if turn['start'] <= current_time <= turn['end']:
            active.add(turn['speaker'])
    return active


def build_scene_timeline(speaker_turns, fps, total_frames,
                         allow_split=False,
                         conversation_window=10.0, min_changes=4,
                         min_monologue=3.0, speaker_debounce=1.2):
    """
    Pre-compute the mode (single/split) and active speaker for every frame.
    For podcasts & interviews, allow_split=False ensures 100% full-screen dynamic cuts.
    """
    total_time = total_frames / fps

    if not allow_split:
        # 100% full-screen dynamic cuts for podcast / interview videos
        raw_mode = ['single'] * total_frames
    else:
        # Step 1: Find all speaker change timestamps
        change_times = []
        prev_spk = None
        for turn in speaker_turns:
            if turn['speaker'] != prev_spk:
                change_times.append(turn['start'])
                prev_spk = turn['speaker']

        print(f"[Timeline] {len(change_times)} speaker changes detected")

        # Step 2: For each second, count speaker changes in the surrounding window
        raw_mode = []  # one entry per frame
        for f_idx in range(total_frames):
            t = f_idx / fps
            window_start = t - conversation_window / 2
            window_end = t + conversation_window / 2

            changes_in_window = sum(
                1 for ct in change_times
                if window_start <= ct <= window_end
            )

            if changes_in_window >= min_changes:
                raw_mode.append('split')
            else:
                raw_mode.append('single')

        # Step 3: Debounce — remove runs shorter than 0.8 seconds
        debounce_frames = int(0.8 * fps)
        i = 0
        while i < len(raw_mode):
            j = i + 1
            while j < len(raw_mode) and raw_mode[j] == raw_mode[i]:
                j += 1
            run_length = j - i
            if run_length < debounce_frames and i > 0:
                fill_mode = raw_mode[i - 1]
                for k in range(i, j):
                    raw_mode[k] = fill_mode
            i = j

    # Step 4: For single-mode frames, determine which speaker to focus on
    timeline = []
    for f_idx in range(total_frames):
        t = f_idx / fps
        mode = raw_mode[f_idx]

        if mode == 'single':
            # Find which speaker is active at this time
            active = get_active_speakers(speaker_turns, t)
            if len(active) == 1:
                speaker = list(active)[0]
            elif len(active) >= 2:
                # Both active but we decided single mode — pick the one who
                # started their turn most recently
                latest_start = -1
                speaker = None
                for turn in speaker_turns:
                    if (turn['start'] <= t <= turn['end']
                            and turn['start'] > latest_start):
                        latest_start = turn['start']
                        speaker = turn['speaker']
                if speaker is None:
                    speaker = list(active)[0]
            else:
                # Nobody talking — find the most recent speaker (max end time <= t)
                speaker = None
                best_end = -1
                for turn in speaker_turns:
                    if turn['end'] <= t and turn['end'] > best_end:
                        speaker = turn['speaker']
                        best_end = turn['end']
            timeline.append({'mode': 'single', 'speaker': speaker})
        else:
            timeline.append({'mode': 'split', 'speaker': None})

    # Step 5: Debounce active speaker in single mode (prevent micro-cuts)
    # Balanced physics rule: Ignore turns shorter than speaker_debounce (1.2s)
    # to filter out quick mic bleed/breaths, while preserving real 1.3-1.5s answers
    speaker_debounce_frames = int(speaker_debounce * fps)
    i = 0
    while i < len(timeline):
        j = i + 1
        while j < len(timeline) and timeline[j]['speaker'] == timeline[i]['speaker']:
            j += 1
        
        run_length = j - i
        # If this speaker's turn is too short, and we aren't at the very start
        if run_length < speaker_debounce_frames and i > 0:
            fill_speaker = timeline[i - 1]['speaker']
            for k in range(i, j):
                timeline[k]['speaker'] = fill_speaker
        i = j

    return timeline


def crop_face_panel(frame, face_x_norm, source_w, source_h, panel_w, panel_h):
    """
    Crop a region from `frame` centered on the face, sized to fill
    exactly (panel_w x panel_h) after resize.
    
    The crop aspect ratio matches panel_w:panel_h so there is zero
    letterboxing, zero blur padding — just a clean, tight crop on the speaker.
    """
    # Target aspect ratio of the output panel
    panel_aspect = panel_w / panel_h  # e.g. 1080/960 = 1.125 (9:8)

    # We want the tallest crop possible (use full height of the source)
    # and compute width from the panel aspect ratio
    crop_h = source_h
    crop_w = int(crop_h * panel_aspect)

    # If the computed crop width exceeds the source width, flip the logic
    if crop_w > source_w:
        crop_w = source_w
        crop_h = int(crop_w / panel_aspect)

    # Center the crop horizontally on the face
    face_x_px = int(face_x_norm * source_w)
    x1 = face_x_px - crop_w // 2
    x1 = max(0, min(x1, source_w - crop_w))
    x2 = x1 + crop_w

    # Center the crop vertically (faces are usually in top half, but
    # using full height keeps both head and shoulders visible)
    y1 = 0
    y2 = y1 + crop_h

    crop = frame[y1:y2, x1:x2]
    return cv2.resize(crop, (panel_w, panel_h))


def render_video(source_path, tracking_path, diarization_path, output_path,
                 out_w=1080, out_h=1920, allow_split=False):
    start_time = time.time()
    temp_output = "temp_video_no_audio.mp4"

    # ── 1. Load Data ──────────────────────────────────────────────────
    with open(tracking_path, 'r') as f:
        tracking = json.load(f)
    with open(diarization_path, 'r') as f:
        diarization = json.load(f)

    data = tracking.get('data', [])
    fps = tracking.get('fps', 25)
    speaker_turns = diarization.get('speaker_turns', [])

    # Build a dict for O(1) frame lookup instead of scanning the list
    frame_lookup = {pt['f']: pt for pt in data}

    # ── 2. Open Video ─────────────────────────────────────────────────
    cap = cv2.VideoCapture(source_path)
    source_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps == 0:
        video_fps = fps

    print(f"[OpenCV-Pro] Source: {source_w}x{source_h} @ {video_fps:.1f}fps, "
          f"{total_frames} frames")

    # ── 3. Setup Writer ───────────────────────────────────────────────
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output, fourcc, video_fps, (out_w, out_h))

    # Pre-compute panel dimensions
    # Full-frame single speaker: 9:16 crop
    single_crop_w = int(source_h * (out_w / out_h))

    # Split screen: each panel is exactly half the output height
    panel_h = out_h // 2          # 960
    divider_thickness = 4

    # Identify unique speakers dynamically from diarization
    unique_speakers = []
    for turn in speaker_turns:
        spk = turn.get('speaker')
        if spk and spk not in unique_speakers:
            unique_speakers.append(spk)

    # ── 4. Build Scene Timeline ────────────────────────────────────────
    print(f"[OpenCV-Pro] Building scene timeline (allow_split={allow_split})...")
    scene_timeline = build_scene_timeline(
        speaker_turns, video_fps, total_frames, allow_split=allow_split)

    # Count modes for logging
    split_count = sum(1 for s in scene_timeline if s['mode'] == 'split')
    print(f"[OpenCV-Pro] Timeline: {split_count} split frames, "
          f"{total_frames - split_count} single frames")

    # ── Static Split Screen Camera Positions ──────────────────────────
    # User rule: in split screen, do NOT track people dynamically;
    # camera must remain 100% static to eliminate jitter and panning.
    split_lxs = []
    split_rxs = []
    for pt in data:
        fcs = pt.get('faces', [])
        if len(fcs) >= 2 and abs(fcs[0]['x'] - fcs[1]['x']) > 0.18:
            sorted_f = sorted(fcs, key=lambda f: f['x'])
            split_lxs.append(sorted_f[0]['x'])
            split_rxs.append(sorted_f[1]['x'])

    static_lx = float(np.median(split_lxs)) if split_lxs else 0.25
    static_rx = float(np.median(split_rxs)) if split_rxs else 0.75
    print(f"[OpenCV-Pro] Static Split Screen: Left={static_lx:.2f}, Right={static_rx:.2f}")

    # ── 5. Render Loop ────────────────────────────────────────────────
    # Hysteresis buffer: smooth face-count flicker over 15 frames (0.6s)
    two_face_history = deque(maxlen=15)
    last_single_target_x = 0.5  # Cached single focus position
    f_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Face coordinates for this frame
        pt = frame_lookup.get(f_idx)
        faces = pt['faces'] if pt and 'faces' in pt else []

        # Get pre-computed mode from the timeline
        scene = scene_timeline[f_idx] if f_idx < len(scene_timeline) else {
            'mode': 'single', 'speaker': None}
        mode = scene['mode']
        active_speaker = scene['speaker']

        # ── GOLDEN RULE + HYSTERESIS ──────────────────────────────────
        has_two_faces = (len(faces) >= 2
                         and abs(faces[0]['x'] - faces[1]['x']) > 0.18)
        two_face_history.append(has_two_faces)

        recent = list(two_face_history)
        two_face_ratio = sum(recent) / len(recent)

        if mode == 'split':
            if two_face_ratio < 0.4:
                mode = 'single'

        # ── Draw frame ────────────────────────────────────────────────
        if mode == 'single':
            # Determine which face to center on
            if len(faces) >= 2:
                sorted_faces = sorted(faces, key=lambda f: f['x'])
                # Map second speaker to right face, first speaker to left face
                if len(unique_speakers) >= 2 and active_speaker == unique_speakers[1]:
                    target_x = sorted_faces[1]['x']
                else:
                    target_x = sorted_faces[0]['x']
            elif len(faces) == 1:
                target_x = faces[0]['x']
            else:
                target_x = last_single_target_x
                
            last_single_target_x = target_x

            # INSTANT position — no smoothing, no sliding
            cx_px = int(target_x * source_w)
            x1 = max(0, min(cx_px - single_crop_w // 2,
                            source_w - single_crop_w))
            crop = frame[:, x1:x1 + single_crop_w]
            out_frame = cv2.resize(crop, (out_w, out_h))
        else:
            # ── SPLIT SCREEN (STATIC CAMERA - NO TRACKING) ────────────
            # Camera is strictly static at pre-computed fixed positions
            top_panel = crop_face_panel(
                frame, static_lx, source_w, source_h, out_w, panel_h)
            bot_panel = crop_face_panel(
                frame, static_rx, source_w, source_h, out_w, panel_h)

            # Assemble into output frame
            out_frame = np.zeros((out_h, out_w, 3), dtype=np.uint8)
            out_frame[0:panel_h, :] = top_panel
            out_frame[panel_h:out_h, :] = bot_panel

            # Clean white divider line
            y_mid = panel_h
            cv2.line(out_frame,
                     (0, y_mid), (out_w, y_mid),
                     (255, 255, 255), divider_thickness)

        out.write(out_frame)
        f_idx += 1

        if f_idx % 100 == 0:
            print(f"[OpenCV-Pro] Rendered {f_idx}/{total_frames} frames...")

    cap.release()
    out.release()
    elapsed = time.time() - start_time
    print(f"[OpenCV-Pro] Video rendered in {elapsed:.1f}s")

    # ── 5. Merge Audio ────────────────────────────────────────────────
    print("[FFmpeg] Merging audio...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", temp_output, "-i", source_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_path
    ]
    subprocess.run(cmd, check=True)
    os.remove(temp_output)
    print(f"[SUCCESS] Final video saved to: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python opencv_renderer.py <source.mp4> "
              "<tracking.json> <diarization.json> <output.mp4> [--split]")
    else:
        allow_split = "--split" in sys.argv
        render_video(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], allow_split=allow_split)
