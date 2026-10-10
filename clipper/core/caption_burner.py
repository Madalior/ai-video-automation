"""
Caption Burner — Word-level animated captions
Powered by: Remotion (React-based programmatic video rendering)
"""

import os
import json
import subprocess
import time
from typing import Optional
from pathlib import Path

from clipper.core.keyword_caption_detector import CaptionKeywordDetector

class CaptionBurner:
    """
    Burns styled captions into video clips using Remotion.
    Reads word-level SRT and passes it as JSON props to Remotion.
    """
    def __init__(self):
        self.remotion_dir = Path(__file__).parent.parent / "remotion"
        self._check_remotion()

    def _check_remotion(self):
        if not (self.remotion_dir / "package.json").exists():
            print("[CAPTIONS] Remotion project not found in ./remotion!")

    def _parse_srt(self, srt_path: str):
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split('\n\n')
        words = []
        
        def time_to_sec(tStr):
            h, m, s = tStr.split(':')
            s, ms = s.split(',')
            return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                times = lines[1].split(' --> ')
                if len(times) == 2:
                    start = time_to_sec(times[0])
                    end = time_to_sec(times[1])
                    text = " ".join(lines[2:])
                    words.append({"text": text, "start": start, "end": end})
        return words

    def _probe_video_info(self, video_path: str):
        """Extract duration and native FPS from video using ffprobe."""
        dur = 0.0
        fps = 30.0
        try:
            cmd = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate,duration:format=duration",
                "-of", "json", str(video_path)
            ]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                data = json.loads(r.stdout)
                streams = data.get("streams", [])
                if streams:
                    s = streams[0]
                    if s.get("duration"):
                        dur = float(s["duration"])
                    r_fr = s.get("r_frame_rate", "30/1")
                    if "/" in r_fr:
                        n, d = r_fr.split("/")
                        fps = float(n) / max(1.0, float(d))
                    else:
                        fps = float(r_fr)
                if dur <= 0 and data.get("format", {}).get("duration"):
                    dur = float(data["format"]["duration"])
        except Exception as e:
            print(f"[CAPTIONS] ffprobe info notice: {e}")
        return dur, fps

    def burn_word_srt(
        self,
        video_path: str,
        word_srt_path: str,
        output_path: str = None,
        style: str = "editor_masala",
        max_frames: Optional[int] = None,
        tracking_data: list = None,
        tracking_json: str = None,
        style_overrides: dict = None,
    ) -> Optional[str]:
        """
        Burn SRT captions into a video using Option B (transparent Remotion overlay + FFmpeg composite).
        Supported styles/templates: "delhi", "editor_masala", "gum_gum"
        """
        if not os.path.exists(video_path):
            print(f"[CAPTIONS] Video not found: {video_path}")
            return None

        if not os.path.exists(word_srt_path):
            print(f"[CAPTIONS] SRT not found: {word_srt_path}")
            return None

        transcript = self._parse_srt(word_srt_path)
        overrides = {"template": style}
        if style_overrides:
            overrides.update(style_overrides)

        return self.burn_from_words(
            video_path=video_path,
            words=transcript,
            output_path=output_path,
            style_overrides=overrides,
            max_frames=max_frames,
            tracking_data=tracking_data,
            tracking_json=tracking_json
        )

    def burn_srt(self, video_path: str, srt_path: str, output_path: str = None, style: str = "editor_masala") -> Optional[str]:
        return self.burn_word_srt(video_path, srt_path, output_path, style)

    # ─────────────────────────────────────────────────────────────────────────
    # NEW: Direct word JSON path (bypasses SRT, uses LLM keyword detection)
    # ─────────────────────────────────────────────────────────────────────────

    def burn_from_words(
        self,
        video_path: str,
        words: list,
        output_path: str = None,
        offset_sec: float = 0.0,
        duration_sec: float = None,
        style_overrides: dict = None,
        max_frames: int = None,
        tracking_data: list = None,
        tracking_json: str = None,
    ) -> Optional[str]:
        """
        Burn captions from a list of word dicts directly into a video using Remotion.
        Skips the SRT step entirely — passes JSON props directly.

        Args:
            video_path:     Path to the source video file
            words:          List of {"text": str, "start": float, "end": float}
            output_path:    Output MP4 path (auto-generated if None)
            offset_sec:     Clip start offset in the original video (shifts timestamps to 0)
            duration_sec:   Clip duration (used to filter words)
            style_overrides: Extra props to pass to Remotion (e.g. keywordColor, fontSize)
            max_frames:     Render only this many frames (for quick preview)
            tracking_data:  Pre-computed face tracking points (avoids duplicate YOLO tracking)
            tracking_json:  Path to pre-computed tracking JSON file

        Returns:
            Path to the captioned output video, or None if failed
        """
        if not os.path.exists(video_path):
            print(f"[CAPTIONS] Video not found: {video_path}")
            return None

        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_captioned.mp4"

        out_abs = str(Path(output_path).absolute())
        if os.path.exists(out_abs) and os.path.getsize(out_abs) > 1024 and not os.getenv("FORCE_RE_RENDER"):
            size_mb = os.path.getsize(out_abs) / (1024 * 1024)
            print(f"[CAPTIONS] ⚡ Fast-forward: Caption render already completed: {os.path.basename(out_abs)} ({size_mb:.1f} MB)")
            return out_abs

        # ── 1. Filter + shift word timestamps to start at 0 ─────────────────
        print("[CAPTIONS] Building word transcript...")
        clip_words = self._filter_and_shift_words(words, offset_sec, duration_sec)

        if not clip_words:
            print("[CAPTIONS] No speech in audio window. Generating dynamic hook captions from active campaign...")
            hook_text = ""
            if style_overrides and isinstance(style_overrides, dict):
                hook_text = style_overrides.get("hook") or style_overrides.get("overlayText") or style_overrides.get("title") or ""
            
            import re
            clean_tokens = [re.sub(r"[^\w]", "", w).upper() for w in hook_text.split() if re.sub(r"[^\w]", "", w)]
            if len(clean_tokens) < 3:
                clean_tokens = ["WATCH", "THIS", "EXCLUSIVE", "BREAKDOWN", "NOW"]
            
            clip_words = []
            curr_start = 0.3
            for tok in clean_tokens[:7]:
                dur = 0.55
                clip_words.append({
                    "text": tok,
                    "start": round(curr_start, 2),
                    "end": round(curr_start + dur, 2)
                })
                curr_start += dur + 0.08

        # ── 2. LLM keyword detection ─────────────────────────────────────────
        print("[CAPTIONS] Detecting keywords with LLM...")
        detector = CaptionKeywordDetector()
        keywords = detector.detect(clip_words, max_keywords=6)

        for w in clip_words:
            w["text"] = w["text"].upper().strip().strip(".,!?'\"")
        clip_words = [w for w in clip_words if w["text"]]

        # ── 4. Probe video stream parameters ──────────────────────────────
        import uuid
        render_id = uuid.uuid4().hex[:8]
        v_dur, v_fps = self._probe_video_info(video_path)
        calc_duration = duration_sec if duration_sec else v_dur
        fps_int = int(round(v_fps)) if v_fps > 0 else 30
        dur_frames = int(round(calc_duration * fps_int)) if calc_duration > 0 else 300

        # ── 5. Face tracking (if provided or skip) ───────────────────────────
        if tracking_data is not None:
            print(f"[CAPTIONS] Using provided tracking data ({len(tracking_data)} points)...")
        elif tracking_json == "skip":
            print("[CAPTIONS] Video is already 9:16 vertical; skipping redundant face tracking.")
            tracking_data = []
        elif tracking_json and os.path.exists(tracking_json):
            print(f"[CAPTIONS] Loading existing tracking data from {tracking_json}...")
            try:
                with open(tracking_json, "r", encoding="utf-8") as f:
                    t_content = json.load(f)
                tracking_data = t_content.get("data", t_content) if isinstance(t_content, dict) else t_content
            except Exception as e:
                print(f"[CAPTIONS] Failed to read {tracking_json}: {e}")
                tracking_data = []
        else:
            tracking_data = []

        # ── 6. Build Remotion props (Option B: transparent overlay, zero video copy)
        template_name = "gum_gum"
        if style_overrides and "template" in style_overrides:
            template_name = style_overrides["template"]

        props = {
            "template": template_name,
            "personaMode": "auto",
            "videoPath": "",
            "transparentOverlay": True,
            "durationInFrames": dur_frames,
            "fps": fps_int,
            "transcript": clip_words,
            "trackingData": tracking_data,
            # 2-Sword style styling defaults
            "textColor": "#FFFFFF",
            "line1Color": "#FFFFFF",
            "line2Color": "#FF2A4D",
            "keywordColor": "#00FF66",
            "heroColor": "#FFD700",
            "glowIntensity": 1.0,
            "shadowIntensity": 1.0,
            "fontSize": 44,
            "line1FontSize": 38,
            "line2FontSize": 50,
            "keywordFontSize": 52,
            "letterSpacing": 2,
            "popScaleAmount": 1.10,
            "lineGap": 2,
            "captionYPercent": 54,
            "keywords": list(keywords),
        }

        # Allow caller to override any style props
        if style_overrides:
            props.update(style_overrides)

        # ── 7. Check for Distributed GPU Cluster ──────────────────────────────
        from clipper.core.gpu_cluster import cluster
        if not os.getenv("FORCE_LOCAL") and cluster.get_configured_workers():
            remote_out = cluster.render_single(
                video_path=video_path,
                props=props,
                output_path=out_abs,
                max_frames=max_frames
            )
            if remote_result := remote_out:
                return remote_result
            print("[CAPTIONS] ⚠️ GPU Cluster nodes offline — falling back to local Option B render...")

        # ── 8. Local Option B: Render transparent ProRes 4444 MOV with Remotion
        props_file = self.remotion_dir / f"temp_props_{render_id}.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        overlay_mov = self.remotion_dir / f"temp_overlay_{render_id}.mov"
        print(f"[CAPTIONS] 🎨 Rendering transparent caption layer via Remotion (ProRes 4444)...")
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "ViralCaptionComponent", str(overlay_mov),
            "--props", f"temp_props_{render_id}.json",
            "--codec=prores",
            "--prores-profile=4444",
            "--pixel-format=yuva444p10le",
            "--image-format=png",
            "--gl=angle"
        ]
        if max_frames:
            cmd.extend(["--frames", f"0-{max_frames}"])
            print(f"[CAPTIONS] Quick preview: rendering frames 0-{max_frames}")

        try:
            r = subprocess.run(
                cmd,
                cwd=str(self.remotion_dir),
                capture_output=True, text=True,
                shell=(os.name == "nt")
            )
            if r.returncode != 0 or not overlay_mov.exists():
                print(f"[CAPTIONS] ❌ Remotion Overlay Error:\n{r.stderr[-2000:]}")
                return None

            # ── 9. Composite transparent captions onto pristine reframed video via FFmpeg
            print(f"[CAPTIONS] ⚡ Compositing transparent captions onto pristine video with FFmpeg...")
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(overlay_mov),
                "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                out_abs
            ]
            if max_frames:
                preview_sec = max_frames / max(1.0, float(fps_int))
                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-t", str(preview_sec),
                    "-i", str(video_path),
                    "-i", str(overlay_mov),
                    "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "copy",
                    out_abs
                ]

            fr = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if fr.returncode == 0 and os.path.exists(out_abs):
                size = os.path.getsize(out_abs) / (1024 * 1024)
                print(f"[CAPTIONS] ✅ Option B Complete: {os.path.basename(out_abs)} ({size:.1f} MB, native {v_fps:.2f} fps)")
                return out_abs
            else:
                print(f"[CAPTIONS] ❌ FFmpeg composite error:\n{fr.stderr[-2000:]}")
                return None
        except Exception as e:
            print(f"[CAPTIONS] Error running Option B: {e}")
            return None
        finally:
            if props_file.exists():
                try:
                    os.remove(props_file)
                except Exception:
                    pass
            if overlay_mov.exists():
                try:
                    os.remove(overlay_mov)
                except Exception:
                    pass

    def _render_remote(
        self,
        video_path: str,
        props: dict,
        output_path: str,
        remote_url: str,
        max_frames: Optional[int] = None
    ) -> Optional[str]:
        """
        Offloads Remotion render job to a remote GPU node (e.g. Lightning AI).
        Returns output_path if successful, None otherwise.
        """
        import requests
        endpoint = remote_url.rstrip("/")
        if not endpoint.endswith("/render"):
            endpoint = f"{endpoint}/render"

        print(f"[CAPTIONS] ⚡ Offloading Remotion render to remote GPU worker: {endpoint}...")
        try:
            start_t = time.time()
            with open(video_path, "rb") as vf:
                files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
                data = {"props_json": json.dumps(props, ensure_ascii=False)}
                if max_frames:
                    data["max_frames"] = str(max_frames)

                res = requests.post(endpoint, files=files, data=data, timeout=600)

            if res.status_code == 200:
                with open(output_path, "wb") as out_f:
                    out_f.write(res.content)
                elapsed = time.time() - start_t
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[CAPTIONS] ✅ Remote GPU render completed in {elapsed:.1f}s: {os.path.basename(output_path)} ({size_mb:.1f} MB)")
                return output_path
            else:
                print(f"[CAPTIONS] ⚠️ Remote worker returned HTTP {res.status_code}: {res.text[:300]}")
                return None
        except Exception as e:
            print(f"[CAPTIONS] ⚠️ Remote render failed: {e}")
            return None

    def _filter_and_shift_words(
        self,
        words: list,
        offset_sec: float,
        duration_sec: float = None,
    ) -> list:
        """Filter words to the clip window and shift timestamps to start at 0."""
        result = []
        end_sec = (offset_sec + duration_sec) if duration_sec else float("inf")

        for w in words:
            start = w.get("start", 0)
            end   = w.get("end",   0)

            # Skip words outside the clip window
            if end <= offset_sec:
                continue

            # If word started before clip, only keep it if majority is inside the clip
            if start < offset_sec:
                overlap = end - offset_sec
                dur = max(0.01, end - start)
                if (overlap / dur) < 0.55 or overlap < 0.15:
                    continue

            if start >= end_sec:
                break

            result.append({
                "text":  w.get("text", ""),
                "start": round(max(0.0, start - offset_sec), 3),
                "end":   round(max(0.0, end   - offset_sec), 3),
            })

        return result
