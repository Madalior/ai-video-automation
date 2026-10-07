# RULE: Protected Tracking & Layout Engine

## CRITICAL DIRECTIVE: DO NOT MODIFY CORE TRACKING FILES
The face tracking, speaker diarization, dynamic reframe, and split-screen engine were finalized across 20+ iterations and tested on both the Mark Zuckerberg interview and IShowSpeed live stream tests.

The following files are **LOCKED** and must **NEVER** be modified, rewritten, refactored, or degraded without explicit, unambiguous user confirmation:
1. `clipper/opencv_renderer.py`
2. `clipper/core/split_screen.py`
3. `clipper/core/face_tracker.py`
4. `clipper/core/speaker_detector.py`
5. `clipper/remotion/src/SmartReframer.tsx`
6. `clipper/core/clip_cutter.py`
7. All files in `reference_bank/finalized_tracking_engine/`

## CORE BEHAVIORS TO PRESERVE
- **Podcasts & Interviews**: 100% full-screen dynamic cuts (`allow_split=False`). Speaker debounce at 1.2s. Instant jump cuts between speakers with zero camera sliding.
- **Webcam / Streamer Split Screen**: Static camera at median fixed positions (`static_lx`, `static_rx`). Zero tracking in split screen to prevent jitter.
- **Single Subject / IRL**: `OneEuroFilter` / exponential smoothing (`alpha=0.08`) for smooth subject following.
