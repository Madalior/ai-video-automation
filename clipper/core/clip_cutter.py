"""
Clip Cutter — FFmpeg-powered video processor
Cuts clips, reformats to 9:16, adds blur background for vertical video.
100% FFmpeg — no moviepy overhead, fast and modern.
"""

import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

OUTPUT_DIR  = Path(os.getenv("OUTPUT_DIR",  "output"))
CACHE_DIR   = Path(os.getenv("CACHE_DIR",   "cache"))
RESOLUTION  = os.getenv("OUTPUT_RESOLUTION", "1080x1920")   # 9:16 vertical


@dataclass
class RenderedClip:
    path:     str
    start:    float
    end:      float
    duration: float
    score:    int
    title:    str
    width:    int
    height:   int


class ClipCutter:
    """
    Cuts video segments and reformats them to vertical 9:16 format.
    Uses FFmpeg blur-background technique (no black bars).
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._check_ffmpeg()
        w, h = RESOLUTION.split("x")
        self.out_w = int(w)
        self.out_h = int(h)

    def _check_ffmpeg(self):
        try:
            r = subprocess.run(["ffmpeg", "-version"],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                print("[CUTTER] FFmpeg ready")
            else:
                print("[CUTTER] FFmpeg not found!")
        except Exception:
            print("[CUTTER] FFmpeg not found — install from ffmpeg.org")

    def _safe_filename(self, text: str, max_len: int = 40) -> str:
        return re.sub(r'[^\w\-]', '_', text)[:max_len]

    def cut_and_reformat(self, source_path: str, start: float, end: float,
                         title: str = "clip",
                         score: int = 0,
                         add_blur_bg: bool = True,
                         is_pre_cut: bool = False) -> Optional[RenderedClip]:
        """
        Cut a segment from source video and reformat to 9:16 vertical.

        Uses the modern blur-background technique:
        - Original footage is centered (letterboxed if needed)
        - Blurred + zoomed version fills the background
        - Looks professional, no black bars

        Args:
            source_path: Source .mp4 file
            start: Start time in seconds
            end: End time in seconds
            title: Clip title (used in filename)
            score: Virality score (used in filename)
            add_blur_bg: Add blurred background (True = modern style)

        Returns:
            RenderedClip object or None on failure
        """
        duration = end - start
        if duration <= 0:
            print(f"[CUTTER] Invalid duration: {duration}")
            return None

        safe_title = self._safe_filename(title)
        filename   = f"clip_{score:03d}_{safe_title}.mp4"
        out_path   = str(self.output_dir / filename)

        if os.path.exists(out_path):
            print(f"[CUTTER] [CACHE] {filename}")
            return RenderedClip(
                path=out_path, start=start, end=end, duration=duration,
                score=score, title=title, width=self.out_w, height=self.out_h
            )

        print(f"\n[CUTTER] Cutting: {start:.1f}s - {end:.1f}s ({duration:.1f}s)")
        print(f"[CUTTER] Output: {filename}")

        w, h = self.out_w, self.out_h

        if is_pre_cut:
            # We skip FFmpeg cropping to allow Remotion to do dynamic Face Panning
            # Just copy the video stream or apply simple setpts
            vf = "[0:v]setpts=PTS-STARTPTS[v]"
            cmd = [
                "ffmpeg",
                "-i", source_path,
                "-filter_complex", vf,
                "-map", "[v]",
                "-map", "0:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-y",
                out_path,
            ]
        else:
            # Trim only, keep original aspect ratio for Remotion dynamic pan
            vf = f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v]"

            cmd = [
                "ffmpeg",
                "-ss", str(start),
                "-i", source_path,
                "-t", str(duration),
                "-filter_complex", vf,
                "-map", "[v]",
                "-map", "0:a",
                "-af", f"atrim=start={start}:end={end},asetpts=PTS-STARTPTS",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                "-y",
                out_path,
            ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and os.path.exists(out_path):
                size = os.path.getsize(out_path) / (1024*1024)
                print(f"[CUTTER] Done: {filename} ({size:.1f} MB)")
                return RenderedClip(
                    path=out_path, start=start, end=end, duration=duration,
                    score=score, title=title, width=w, height=h
                )
            print(f"[CUTTER] FFmpeg error: {r.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            print("[CUTTER] Timeout")
        except Exception as e:
            print(f"[CUTTER] Error: {e}")
        return None

    def cut_batch(self, source_path: str, clips: list,
                  add_blur_bg: bool = True) -> list[RenderedClip]:
        """
        Cut multiple clips from the same source video.

        Args:
            source_path: Source video file
            clips: List of Clip objects (from ViralDetector)
            add_blur_bg: Add blurred background

        Returns:
            List of RenderedClip objects (successful cuts only)
        """
        results = []
        total = len(clips)
        print(f"\n[CUTTER] Cutting {total} clips from {os.path.basename(source_path)}")

        # Detect scenes once for the whole video
        scene_list = []
        try:
            from scenedetect import detect, ContentDetector
            print("[CUTTER] Running scene detection for smart cuts...")
            scene_list = detect(source_path, ContentDetector())
            print(f"[CUTTER] Found {len(scene_list)} scene boundaries")
        except ImportError:
            print("[CUTTER] scenedetect not found, skipping smart cuts")
        except Exception as e:
            print(f"[CUTTER] Scene detection failed: {e}")

        for i, clip in enumerate(clips, 1):
            print(f"\n[CUTTER] [{i}/{total}] Score={clip.score} | {clip.title}")
            
            actual_start = clip.start
            actual_end   = clip.end
            
            # Snap to nearest scene boundaries (within 2 seconds)
            if scene_list:
                for (start_scene, end_scene) in scene_list:
                    scene_start_sec = start_scene.get_seconds()
                    scene_end_sec   = end_scene.get_seconds()
                    
                    if abs(scene_start_sec - actual_start) < 2.0:
                        print(f"      [SCENE] Snapped start: {actual_start:.1f}s -> {scene_start_sec:.1f}s")
                        actual_start = scene_start_sec
                    
                    if abs(scene_end_sec - actual_end) < 2.0:
                        print(f"      [SCENE] Snapped end: {actual_end:.1f}s -> {scene_end_sec:.1f}s")
                        actual_end = scene_end_sec

            result = self.cut_and_reformat(
                source_path = source_path,
                start       = actual_start,
                end         = actual_end,
                title       = clip.title,
                score       = clip.score,
                add_blur_bg = add_blur_bg,
            )
            if result:
                results.append(result)

        print(f"\n[CUTTER] Complete: {len(results)}/{total} clips rendered")
        return results

    def get_video_info(self, path: str) -> dict:
        """Get video metadata using ffprobe."""
        try:
            import json
            r = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-show_format", path
            ], capture_output=True, text=True, timeout=15)
            data = json.loads(r.stdout)
            video_stream = next(
                (s for s in data.get("streams", []) if s["codec_type"] == "video"),
                {}
            )
            return {
                "width":    video_stream.get("width", 0),
                "height":   video_stream.get("height", 0),
                "duration": float(data.get("format", {}).get("duration", 0)),
                "fps":      eval(video_stream.get("r_frame_rate", "0/1")),
            }
        except Exception as e:
            return {"width": 0, "height": 0, "duration": 0, "fps": 0}
