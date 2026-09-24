"""
Transcriber — Local Audio/Video Transcription
Powered by: faster-whisper (free, local, word-level timestamps)

No API cost. Runs on CPU or GPU.
Model: large-v3-turbo (best speed/accuracy balance in 2026)
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

WHISPER_MODEL   = os.getenv("WHISPER_MODEL",        "small")
WHISPER_DEVICE  = os.getenv("WHISPER_DEVICE",       "cpu")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")


@dataclass
class Word:
    text:  str
    start: float   # seconds
    end:   float   # seconds
    prob:  float   # confidence 0-1


@dataclass
class Segment:
    text:  str
    start: float
    end:   float
    words: list[Word]


@dataclass
class Transcript:
    text:     str            # full transcript
    segments: list[Segment]  # sentence-level segments
    words:    list[Word]     # all words with timestamps
    language: str
    duration: float


class Transcriber:
    """
    Transcribes audio/video files locally using faster-whisper.
    Produces word-level timestamps for precise clip cutting + captions.
    """

    def __init__(self, model_size: str = None, device: str = None,
                 compute_type: str = None):
        self.model_size   = model_size   or WHISPER_MODEL
        self.device       = device       or WHISPER_DEVICE
        self.compute_type = compute_type or WHISPER_COMPUTE
        self._model       = None   # lazy-loaded

    def _load_model(self):
        if self._model is not None:
            return
        
        # On Windows, add nvidia and torch pip package lib paths so CTranslate2 finds cublas64_12.dll / cudnn
        if sys.platform == "win32":
            try:
                import site
                for site_dir in site.getsitepackages():
                    # Check nvidia package libs
                    nvidia_dir = Path(site_dir) / "nvidia"
                    if nvidia_dir.exists():
                        for lib_dir in nvidia_dir.glob("*/lib"):
                            if lib_dir.is_dir():
                                os.add_dll_directory(str(lib_dir))
                                os.environ["PATH"] += os.pathsep + str(lib_dir)
                    
                    # Check torch lib
                    torch_lib = Path(site_dir) / "torch" / "lib"
                    if torch_lib.exists():
                        os.add_dll_directory(str(torch_lib))
                        os.environ["PATH"] += os.pathsep + str(torch_lib)
            except Exception:
                pass

        try:
            from faster_whisper import WhisperModel
            print(f"[TRANSCRIBER] Loading Whisper {self.model_size} "
                  f"on {self.device} ({self.compute_type})...")
            self._model = WhisperModel(
                self.model_size,
                device       = self.device,
                compute_type = self.compute_type,
            )
            print("[TRANSCRIBER] Model ready")
        except ImportError:
            print("[TRANSCRIBER] faster-whisper not installed")
            print("[TRANSCRIBER] Run: pip install faster-whisper")
            sys.exit(1)

    def transcribe(self, video_path: str,
                   language: str = None,
                   vad_filter: bool = True) -> Optional[Transcript]:
        """
        Transcribe a video/audio file with word-level timestamps.
        Automatically chunks long files (>10 min) to prevent OOM on CPU.

        Args:
            video_path: Path to .mp4, .mp3, .wav, .m4a, etc.
            language:   Force language (e.g. "en") or None for auto-detect
            vad_filter: Remove silence for faster/cleaner transcription

        Returns:
            Transcript object with segments and word timestamps
        """
        if not os.path.exists(video_path):
            print(f"[TRANSCRIBER] File not found: {video_path}")
            return None

        self._load_model()

        print(f"[TRANSCRIBER] Transcribing: {os.path.basename(video_path)}")
        size_mb = os.path.getsize(video_path) / (1024*1024)
        print(f"[TRANSCRIBER] File size: {size_mb:.1f} MB")

        # Check duration — if >10 min, use chunked transcription to avoid OOM
        audio_duration = self._get_audio_duration(video_path)
        chunk_threshold = 600  # 10 minutes

        if audio_duration and audio_duration > chunk_threshold:
            print(f"[TRANSCRIBER] Long audio detected ({audio_duration/60:.1f} min). "
                  f"Splitting into {chunk_threshold//60}-min chunks to prevent OOM...")
            return self._transcribe_chunked(video_path, audio_duration, chunk_threshold, language, vad_filter)

        return self._transcribe_single(video_path, language, vad_filter)

    def _get_audio_duration(self, path: str) -> Optional[float]:
        """Get audio duration in seconds using FFprobe."""
        import subprocess
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            print(f"[TRANSCRIBER] Could not probe duration: {e}")
        return None

    def _transcribe_chunked(self, video_path: str, total_duration: float,
                            chunk_seconds: int, language: str, vad_filter: bool) -> Optional[Transcript]:
        """Split long audio into chunks, transcribe each, merge results."""
        import subprocess
        import tempfile
        import math

        num_chunks = math.ceil(total_duration / chunk_seconds)
        print(f"[TRANSCRIBER] Will process {num_chunks} chunk(s) of {chunk_seconds//60} min each.")

        all_segments = []
        all_words = []
        detected_language = language or "en"
        chunk_dir = Path(video_path).parent / "_whisper_chunks"
        chunk_dir.mkdir(exist_ok=True)

        try:
            for chunk_idx in range(num_chunks):
                offset = chunk_idx * chunk_seconds
                remaining = total_duration - offset
                duration = min(chunk_seconds, remaining)

                chunk_file = str(chunk_dir / f"chunk_{chunk_idx:03d}.wav")
                print(f"\n[TRANSCRIBER] ── Chunk {chunk_idx + 1}/{num_chunks} "
                      f"({offset/60:.1f}m → {(offset + duration)/60:.1f}m) ──")

                # Extract chunk as 16kHz mono WAV (optimal for Whisper)
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{offset:.2f}",
                    "-i", video_path,
                    "-t", f"{duration:.2f}",
                    "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    chunk_file
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode != 0 or not os.path.exists(chunk_file):
                    print(f"[TRANSCRIBER] ⚠️ Failed to extract chunk {chunk_idx + 1}, skipping.")
                    continue

                chunk_size = os.path.getsize(chunk_file) / (1024 * 1024)
                print(f"[TRANSCRIBER] Chunk WAV: {chunk_size:.1f} MB")

                # Transcribe this chunk
                try:
                    segments_raw, info = self._model.transcribe(
                        chunk_file,
                        language        = language,
                        word_timestamps = True,
                        vad_filter      = vad_filter,
                        vad_parameters  = {"min_silence_duration_ms": 500},
                    )

                    if chunk_idx == 0:
                        detected_language = info.language

                    chunk_seg_count = 0
                    chunk_word_count = 0
                    for seg in segments_raw:
                        words = []
                        if seg.words:
                            for w in seg.words:
                                word = Word(
                                    text  = w.word.strip(),
                                    start = round(w.start + offset, 3),
                                    end   = round(w.end + offset, 3),
                                    prob  = round(w.probability, 3),
                                )
                                words.append(word)
                                all_words.append(word)
                                chunk_word_count += 1

                        all_segments.append(Segment(
                            text  = seg.text.strip(),
                            start = round(seg.start + offset, 3),
                            end   = round(seg.end + offset, 3),
                            words = words,
                        ))
                        chunk_seg_count += 1

                    print(f"[TRANSCRIBER] ✅ Chunk {chunk_idx + 1}: "
                          f"{chunk_seg_count} segments, {chunk_word_count} words")

                except Exception as e:
                    print(f"[TRANSCRIBER] ⚠️ Chunk {chunk_idx + 1} transcription error: {e}")
                    continue
                finally:
                    # Clean up chunk file immediately to save disk space
                    try:
                        os.remove(chunk_file)
                    except Exception:
                        pass

            # Clean up chunk directory
            try:
                chunk_dir.rmdir()
            except Exception:
                pass

            if not all_segments:
                print("[TRANSCRIBER] ❌ All chunks failed to transcribe.")
                return None

            full_text = " ".join(s.text for s in all_segments)
            duration = all_segments[-1].end if all_segments else total_duration

            print(f"\n[TRANSCRIBER] ✅ Chunked transcription complete: "
                  f"{len(all_segments)} segments, {len(all_words)} words, "
                  f"lang={detected_language}, duration={duration:.0f}s")

            return Transcript(
                text     = full_text,
                segments = all_segments,
                words    = all_words,
                language = detected_language,
                duration = duration,
            )

        except Exception as e:
            print(f"[TRANSCRIBER] ❌ Chunked transcription failed: {e}")
            # Clean up any leftover chunks
            try:
                for f in chunk_dir.glob("chunk_*.wav"):
                    os.remove(f)
                chunk_dir.rmdir()
            except Exception:
                pass
            return None

    def _transcribe_single(self, video_path: str, language: str, vad_filter: bool) -> Optional[Transcript]:
        """Transcribe a short audio file in one pass (original behavior)."""
        try:
            segments_raw, info = self._model.transcribe(
                video_path,
                language        = language,
                word_timestamps = True,
                vad_filter      = vad_filter,
                vad_parameters  = {"min_silence_duration_ms": 500},
            )

            segments = []
            all_words = []

            for seg in segments_raw:
                words = []
                if seg.words:
                    for w in seg.words:
                        word = Word(
                            text  = w.word.strip(),
                            start = round(w.start, 3),
                            end   = round(w.end, 3),
                            prob  = round(w.probability, 3),
                        )
                        words.append(word)
                        all_words.append(word)

                segments.append(Segment(
                    text  = seg.text.strip(),
                    start = round(seg.start, 3),
                    end   = round(seg.end, 3),
                    words = words,
                ))

            full_text = " ".join(s.text for s in segments)
            duration  = segments[-1].end if segments else 0

            print(f"[TRANSCRIBER] Done: {len(segments)} segments, "
                  f"{len(all_words)} words, lang={info.language}")

            return Transcript(
                text     = full_text,
                segments = segments,
                words    = all_words,
                language = info.language,
                duration = duration,
            )

        except Exception as e:
            print(f"[TRANSCRIBER] Error: {e}")
            return None

    def to_srt(self, transcript: Transcript, output_path: str) -> str:
        """Export transcript to SRT subtitle format."""
        lines = []
        for i, seg in enumerate(transcript.segments, 1):
            start = self._fmt_time(seg.start)
            end   = self._fmt_time(seg.end)
            lines.append(f"{i}\n{start} --> {end}\n{seg.text}\n")

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[TRANSCRIBER] SRT saved: {output_path}")
        return output_path

    def to_word_srt(self, transcript: Transcript,
                    output_path: str,
                    words_per_line: int = 3,
                    offset_sec: float = 0.0,
                    duration_sec: float = None) -> str:
        """
        Export word-level SRT — each subtitle = N words.
        Used for karaoke/animated captions.
        """
        lines = []
        
        # Filter words within the chunk and adjust timestamps
        valid_words = []
        for w in transcript.words:
            if w.end < offset_sec:
                continue
            if duration_sec and w.start > offset_sec + duration_sec:
                break
            
            # Shift timestamps to start at 0
            shifted_start = max(0, w.start - offset_sec)
            shifted_end   = max(0, w.end - offset_sec)
            
            # Create a mock word object with shifted times
            class ShiftedWord:
                def __init__(self, t, s, e):
                    self.text = t
                    self.start = s
                    self.end = e
            
            valid_words.append(ShiftedWord(w.text, shifted_start, shifted_end))

        idx = 1
        for i in range(0, len(valid_words), words_per_line):
            chunk = valid_words[i:i+words_per_line]
            if not chunk:
                continue
            start = self._fmt_time(chunk[0].start)
            end   = self._fmt_time(chunk[-1].end)
            text  = " ".join(w.text for w in chunk)
            lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
            idx += 1

        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[TRANSCRIBER] Word SRT saved: {output_path}")
        return output_path

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
