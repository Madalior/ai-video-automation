# Finalized Tracking & Dynamic Layout Engine (GOLDEN SNAPSHOT)

## 🔒 PERMANENT CODE PRESERVATION
**DO NOT MODIFY, REWRITE, OR OVERWRITE THESE FILES.**
These files represent the perfected, finalized dynamic reframing, face tracking, speaker diarization, and split-screen engine tested and validated across 20+ iterations on both:
1. **The Mark Zuckerberg & Cleo Abram Interview** (`https://youtu.be/oX7OduG1YmI`) — Podcast multi-speaker dynamic cuts.
2. **IShowSpeed Stream Tests** (`4zVFht1KbnY` webcam & `20P6kQk6zII` IRL) — Streamer reaction split screen & moving subject tracking.

---

## 📐 CORE ARCHITECTURE & DECISION RULES

### 1. Podcasts & Multi-Speaker Dialogues (`allow_split = False`)
* **Layout**: **100% Full-Screen Dynamic 9:16 Reframe** (Zero vertical splitting).
* **Voice Tracking**: PyAnnote 3.1 speaker diarization identifies active speaker turns.
* **Debounce Filter**: `speaker_debounce = 1.2s`:
  * Micro-turns shorter than 1.2s (coughs, breaths, mic bleed) are merged into the ongoing speaker.
  * Preserves real 1.3s–1.5s answers without camera fluttering.
* **Face Tracking**: YOLOv8 + ByteTrack persistent IDs maps speaker turns to left/right subject positions.
* **Camera Cut**: **Instant jump cut** to the active speaker — zero sliding, zero pan-drag across the room.

### 2. Webcam / Streamer Reaction Content (Split Screen)
* **Layout**: **Vertical Split Screen (Top / Bottom Stack)**
  * **Top Panel (1080×960)**: Formatted on the main content / performer.
  * **Bottom Panel (1080×960)**: Zoomed into the streamer's reaction webcam in the corner.
  * **Divider**: 4px white dividing line at `y = 960`.
* **Static Camera Rule**:
  * In split-screen mode, **dynamic tracking is disabled**.
  * The camera remains 100% static at pre-computed fixed coordinates (`static_lx`, `static_rx`) to eliminate jitter and motion sickness.

### 3. IRL Streams & Single Moving Subjects
* **Layout**: **100% Full-Screen 9:16 Subject Tracking**
* **Smoothing Filter**: `OneEuroFilter` / Exponential smoothing (`alpha = 0.08`):
  * Still subject → camera stays locked in place.
  * Moving subject → smooth cinematic panning without jumpiness.

---

## 📁 PRESERVED MODULES IN THIS SNAPSHOT
1. `opencv_renderer.py` — High-performance OpenCV implementation of `build_scene_timeline`, `render_video`, and static-camera split-screen.
2. `mediapipe_tracker.py` — MediaPipe Full-Range face tracker (`model_selection=1`, 0-5m range, confidence 0.45, 5-frame occlusion grace, alpha 0.3) tested on live streams.
3. `streamer_webcam_renderer.py` — Dedicated streamer reaction split-screen renderer (Step 5198: Top 1080×960 talent, Bottom 1080×960 corner facecam zoom).
4. `irl_stream_renderer.py` — Dedicated IRL stream 100% full-screen dynamic 9:16 reframe renderer (Step 5215: EMA alpha=0.08 smoothing, crew filter).
5. `split_screen.py` — `SmartReframer` class with FFmpeg concat pipeline and 1.5s stability threshold.
6. `face_tracker.py` — YOLOv8 face detector with `OneEuroFilter` (`min_cutoff=0.004, beta=0.005`).
7. `speaker_detector.py` — PyAnnote 3.1 speaker diarization pipeline.
8. `SmartReframer.tsx` — Remotion composition implementation for client-side animated reframing.
9. `clip_cutter.py` — Lossless FFmpeg clip cutter with keyframe alignment.
