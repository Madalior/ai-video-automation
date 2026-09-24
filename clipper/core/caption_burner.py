"""
Caption Burner — Word-level animated captions
Powered by: Remotion (React-based programmatic video rendering)
"""

import os
import json
import subprocess
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

    def burn_word_srt(
        self,
        video_path: str,
        word_srt_path: str,
        output_path: str = None,
        style: str = "viral_ishowspeed",
        max_frames: Optional[int] = None,
        tracking_data: list = None,
        tracking_json: str = None,
    ) -> Optional[str]:
        """
        Burn SRT captions into a video using Remotion.
        """
        if not os.path.exists(video_path):
            print(f"[CAPTIONS] Video not found: {video_path}")
            return None

        if not os.path.exists(word_srt_path):
            print(f"[CAPTIONS] SRT not found: {word_srt_path}")
            return None

        if output_path is None:
            base = os.path.splitext(video_path)[0]
            output_path = f"{base}_captioned.mp4"

        out_abs = str(Path(output_path).absolute())
        if os.path.exists(out_abs) and os.path.getsize(out_abs) > 1024 and not os.getenv("FORCE_RE_RENDER"):
            size_mb = os.path.getsize(out_abs) / (1024 * 1024)
            print(f"[CAPTIONS] ⚡ Fast-forward: Pre-rendered video already exists: {os.path.basename(out_abs)} ({size_mb:.1f} MB)")
            return out_abs

        print("\n[CAPTIONS] Parsing SRT to JSON for Remotion...")
        transcript = self._parse_srt(word_srt_path)

        import shutil
        import uuid
        render_id = uuid.uuid4().hex[:8]
        public_dir = self.remotion_dir / "public"
        public_dir.mkdir(exist_ok=True)
        safe_video_name = f"temp_render_vid_{render_id}.mp4"
        safe_video_path = public_dir / safe_video_name

        out_abs = Path(output_path).absolute().as_posix()

        print("[CAPTIONS] Copying video to Remotion public directory for rendering...")
        shutil.copy2(video_path, safe_video_path)

        if tracking_data is not None:
            print(f"[CAPTIONS] Using provided tracking data ({len(tracking_data)} points)...")
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
            print("[CAPTIONS] Running Face Tracking analysis...")
            try:
                from clipper.core.face_tracker import FaceTracker
                tracker = FaceTracker(sample_rate=3)
                tracking_json_path = str(self.remotion_dir / f"temp_tracking_{render_id}.json")
                tracking_data = tracker.track(str(safe_video_path), tracking_json_path)
            except ImportError:
                print("[CAPTIONS] Face tracking dependencies not installed. Skipping.")
                tracking_data = []
            except Exception as e:
                print(f"[CAPTIONS] Face tracking error: {e}")
                tracking_data = []

        props = {
            "videoPath": safe_video_name,
            "transcript": transcript,
            "trackingData": tracking_data
        }

        # Write props to a temp file to avoid huge command line arguments
        props_file = self.remotion_dir / f"temp_props_{render_id}.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f)

        print(f"[CAPTIONS] Invoking Remotion CLI...")
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "ViralCaptionComponent", out_abs,
            "--props", f"temp_props_{render_id}.json"
        ]
        if max_frames:
            cmd.extend(["--frames", f"0-{max_frames}"])
            print(f"[CAPTIONS] Quick Render mode enabled: rendering frames 0-{max_frames}")

        try:
            r = subprocess.run(cmd, cwd=str(self.remotion_dir), capture_output=True, text=True, shell=os.name == 'nt')
            if r.returncode == 0 and os.path.exists(out_abs):
                size = os.path.getsize(out_abs) / (1024*1024)
                print(f"[CAPTIONS] Done: {os.path.basename(out_abs)} ({size:.1f} MB)")
                
                # Cleanup temp files
                if props_file.exists():
                    try:
                        os.remove(props_file)
                    except Exception:
                        pass
                if safe_video_path.exists():
                    try:
                        os.remove(safe_video_path)
                    except Exception:
                        pass
                    
                return out_abs
            else:
                print(f"[CAPTIONS] Remotion Error:\n{r.stderr}")
                return None
        except Exception as e:
            print(f"[CAPTIONS] Error running Remotion: {e}")
            return None
        finally:
            if props_file.exists():
                try:
                    os.remove(props_file)
                except Exception:
                    pass
            if safe_video_path.exists():
                try:
                    os.remove(safe_video_path)
                except Exception:
                    pass

    def burn_srt(self, video_path: str, srt_path: str, output_path: str = None, style: str = "modern") -> Optional[str]:
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

        # ── 3. Uppercase all words + tag keywords ─────────────────────────────
        for w in clip_words:
            w["text"] = w["text"].upper().strip().strip(".,!?'\"")

        # ── 4. Copy video to Remotion /public ────────────────────────────────
        import shutil
        import uuid
        render_id = uuid.uuid4().hex[:8]
        public_dir = self.remotion_dir / "public"
        public_dir.mkdir(exist_ok=True)
        safe_video_name = f"temp_render_vid_{render_id}.mp4"
        safe_video_path = public_dir / safe_video_name
        print(f"[CAPTIONS] Copying video to Remotion public directory ({safe_video_name})...")
        shutil.copy2(video_path, safe_video_path)

        # ── 5. Face tracking ─────────────────────────────────────────────────
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
            print("[CAPTIONS] Running face tracking...")
            try:
                from clipper.core.face_tracker import FaceTracker
                tracker = FaceTracker(sample_rate=3)
                tracking_json_path = str(self.remotion_dir / f"temp_tracking_{render_id}.json")
                tracking_data = tracker.track(str(safe_video_path), tracking_json_path)
            except Exception as e:
                print(f"[CAPTIONS] Face tracking skipped: {e}")
                tracking_data = []

        # ── 6. Build Remotion props ───────────────────────────────────────────
        props = {
            "videoPath": safe_video_name,
            "transcript": clip_words,
            "trackingData": tracking_data,
            # Style defaults matching our Composition.tsx
            "line1Color": "#CCCCCC",
            "line2Color": "#FFFFFF",
            "keywordColor": "#00FF66",
            "glowIntensity": 1.0,
            "shadowIntensity": 1.0,
            "line1FontSize": 34,
            "line2FontSize": 40,
            "keywordFontSize": 42,
            "letterSpacing": 3,
            "popScaleAmount": 1.08,
            "lineGap": 2,
            "captionYPercent": 68,
            # Pass keyword list so Composition.tsx knows which words to highlight
            "keywords": list(keywords),
        }

        # Allow caller to override any style props
        if style_overrides:
            props.update(style_overrides)

        # ── 7. Write props JSON ───────────────────────────────────────────────
        props_file = self.remotion_dir / f"temp_props_{render_id}.json"
        with open(props_file, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        # ── 8. Run Remotion render ────────────────────────────────────────────
        print(f"[CAPTIONS] Invoking Remotion render...")
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "ViralCaptionComponent", out_abs,
            "--props", f"temp_props_{render_id}.json"
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
            if r.returncode == 0 and os.path.exists(out_abs):
                size = os.path.getsize(out_abs) / (1024 * 1024)
                print(f"[CAPTIONS] ✅ Done: {os.path.basename(out_abs)} ({size:.1f} MB)")
                return out_abs
            else:
                print(f"[CAPTIONS] ❌ Remotion Error:\n{r.stderr[-2000:]}")
                return None
        except Exception as e:
            print(f"[CAPTIONS] Error running Remotion: {e}")
            return None
        finally:
            if props_file.exists():
                try:
                    os.remove(props_file)
                except Exception:
                    pass
            if safe_video_path.exists():
                try:
                    os.remove(safe_video_path)
                except Exception:
                    pass

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
            if start >= end_sec:
                break

            result.append({
                "text":  w.get("text", ""),
                "start": round(max(0.0, start - offset_sec), 3),
                "end":   round(max(0.0, end   - offset_sec), 3),
            })

        return result
