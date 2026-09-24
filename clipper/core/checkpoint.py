"""
CheckpointManager — State Persistence & Fault-Tolerant Recovery
==============================================================
Saves intermediate pipeline state after every step:
  - Step 1: Transcribed audio & word timestamps
  - Step 2: LLM viral moment clips
  - Steps 3-7: Per-clip processing artifacts (raw, reframed, captioned, music, upload)

Allows resuming interrupted pipelines instantly without redundant compute.
"""

import os
import json
import hashlib
from pathlib import Path
from dataclasses import asdict
from typing import Optional

from clipper.core.transcriber import Transcript, Segment, Word
from clipper.core.viral_detector import Clip


class CheckpointManager:
    """Manages checkpoint saving and restoration for a specific pipeline job."""

    def __init__(self, cache_dir: Path, job_id: str):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.job_id = job_id
        self.file_path = self.cache_dir / f"checkpoint_{self.job_id}.json"
        self.data = self._load()

    def clear(self):
        """Wipes checkpoint state from memory and disk for a true from-scratch run."""
        self.data = {}
        if self.file_path.exists():
            try:
                self.file_path.unlink()
            except Exception:
                pass

    @staticmethod
    def generate_job_id(url: str = None, video_file: str = None) -> str:
        """Generate a deterministic, human-readable job ID for a source input."""
        norm_file = ""
        if video_file:
            try:
                p = Path(video_file)
                if not p.exists():
                    for candidate in [
                        Path("campaigns/raw_footage") / p.name,
                        Path("output") / p.name,
                        Path("cache") / p.name,
                    ]:
                        if candidate.exists():
                            p = candidate
                            break
                norm_file = p.resolve().as_posix().lower()
            except Exception:
                norm_file = str(video_file).strip().replace("\\", "/").lower()

        norm_url = (url or "").strip().lower()
        key = norm_url + norm_file
        if not key:
            import uuid
            return f"job_{uuid.uuid4().hex[:8]}"

        h = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
        if video_file:
            base = Path(video_file).stem
        elif url:
            import re
            m = re.search(r"[?&]v=([a-zA-Z0-9_-]+)", url)
            base = m.group(1) if m else "web"
        else:
            base = "job"
        safe_base = "".join(c for c in base if c.isalnum() or c in ("-", "_"))[:16]
        return f"{safe_base}_{h}"

    def _load(self) -> dict:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CHECKPOINT] Warning: could not load existing checkpoint: {e}")
                return {}
        return {}

    def save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CHECKPOINT] Warning: failed to save checkpoint: {e}")

    def save_step_1_transcribe(self, transcript: Transcript, audio_path: str):
        """Save word-level transcript and audio location."""
        self.data["step_1"] = {
            "completed": True,
            "audio_path": audio_path,
            "language": transcript.language,
            "duration": transcript.duration,
            "text": transcript.text,
            "segments": [
                {
                    "text": s.text,
                    "start": s.start,
                    "end": s.end,
                    "words": [
                        {"text": w.text, "start": w.start, "end": w.end, "prob": getattr(w, "prob", 1.0)}
                        for w in s.words
                    ],
                }
                for s in transcript.segments
            ],
            "words": [
                {"text": w.text, "start": w.start, "end": w.end, "prob": getattr(w, "prob", 1.0)}
                for w in transcript.words
            ],
        }
        self.save()

    def get_step_1_transcript(self) -> tuple[Optional[Transcript], Optional[str]]:
        """Restore transcript if step 1 was previously completed."""
        step = self.data.get("step_1")
        if not step or not step.get("completed"):
            return None, None

        audio_path = step.get("audio_path")
        if audio_path and not os.path.exists(audio_path):
            return None, None

        words = [
            Word(text=w["text"], start=float(w["start"]), end=float(w["end"]), prob=float(w.get("prob", 1.0)))
            for w in step.get("words", [])
        ]
        segments = []
        for s in step.get("segments", []):
            s_words = [
                Word(text=w["text"], start=float(w["start"]), end=float(w["end"]), prob=float(w.get("prob", 1.0)))
                for w in s.get("words", [])
            ]
            segments.append(
                Segment(text=s["text"], start=float(s["start"]), end=float(s["end"]), words=s_words)
            )

        transcript = Transcript(
            text=step.get("text", ""),
            segments=segments,
            words=words,
            language=step.get("language", "en"),
            duration=float(step.get("duration", 0.0)),
        )
        return transcript, audio_path

    def save_step_2_clips(self, clips: list[Clip]):
        """Save list of scored viral clips."""
        self.data["step_2"] = {
            "completed": True,
            "clips": [asdict(c) for c in clips],
        }
        self.save()

    def get_step_2_clips(self) -> Optional[list[Clip]]:
        """Restore viral clips if step 2 was previously completed."""
        step = self.data.get("step_2")
        if not step or not step.get("completed"):
            return None
        return [Clip(**c) for c in step.get("clips", [])]

    def save_clip_progress(self, index: int, clip_info: dict):
        """Record partial/full progress for a specific clip."""
        if "clips_progress" not in self.data:
            self.data["clips_progress"] = {}
        existing = self.data["clips_progress"].get(str(index), {})
        existing.update(clip_info)
        self.data["clips_progress"][str(index)] = existing
        self.save()

    def get_clip_progress(self, index: int) -> Optional[dict]:
        """Return saved state for clip index."""
        return self.data.get("clips_progress", {}).get(str(index))

    def mark_completed(self, final_videos: list[str]):
        """Mark entire pipeline run as finished."""
        self.data["completed"] = True
        self.data["final_videos"] = final_videos
        self.save()

    def is_completed(self) -> bool:
        return self.data.get("completed", False)

    def get_final_videos(self) -> list[str]:
        return self.data.get("final_videos", [])
