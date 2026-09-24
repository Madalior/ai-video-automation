"""
Music Mixer
===========
Division 3: Add trending background music to a video clip.

Strategy:
  - Video audio stays at 30% volume (keeps the original voice audible)
  - Background music plays at 70% volume underneath
  - Music loops if shorter than the clip
  - Music fades in at the start (0.5s) and fades out at the end (1.5s)
  - Audio is normalized to -14 LUFS (TikTok/Shorts standard)

Music Sources (in priority order):
  1. Local music folder (fastest, no API needed)
  2. YouTube audio download (trending, free)
  3. Pixabay API (royalty-free, no copyright)

Usage:
  mixer = MusicMixer()

  # Mix with a specific track
  out = mixer.mix(video_path, output_path, music_path="my_track.mp3")

  # Auto-pick a random track from local library
  out = mixer.mix(video_path, output_path)

  # Download a trending track from YouTube then mix
  out = mixer.mix_with_youtube(video_path, output_path, query="lofi hip hop chill")
"""

import os
import re
import json
import random
import subprocess
from pathlib import Path
from typing import Optional

# Default music library folder — drop MP3s here
MUSIC_LIBRARY = Path(os.getenv("MUSIC_LIBRARY", "music_library"))

# Volume levels
VIDEO_AUDIO_VOL = float(os.getenv("VIDEO_AUDIO_VOL", "1.0"))   # 100% dialogue clarity
MUSIC_VOL       = float(os.getenv("MUSIC_VOL",       "0.30"))  # 30% background music

# Audio normalization target (TikTok/Shorts/Reels standard)
LUFS_TARGET = -14.0


class MusicMixer:
    """
    Mixes background music into a video using FFmpeg.
    Handles looping, volume balancing, fade in/out, and LUFS normalization.
    """

    def __init__(
        self,
        music_library: str = None,
        video_vol: float = VIDEO_AUDIO_VOL,
        music_vol: float = MUSIC_VOL,
    ):
        self.music_library = Path(music_library or MUSIC_LIBRARY)
        self.video_vol     = video_vol
        self.music_vol     = music_vol
        self.music_library.mkdir(parents=True, exist_ok=True)
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            print("[MUSIC] FFmpeg ready")
        except Exception:
            print("[MUSIC] [WARN] FFmpeg not found!")

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def detect_viral_hook_start(self, music_path: str) -> float:
        """
        Detects the start time of the main viral part / hook / chorus of the song.
        Uses Instagram Reels highlight markers (`highlight_start_times_in_ms`)
        and audio volume analysis to guarantee starting on the iconic drop.
        """
        if not music_path or not os.path.exists(music_path):
            return 0.0

        try:
            from clipper.core.instagram_music import InstagramAudioResolver
            resolver = InstagramAudioResolver()
            fname = os.path.splitext(os.path.basename(music_path))[0].replace("_", " ")
            res = resolver.resolve_highlight(title=fname, audio_file=music_path)
            offset = float(res.get("highlight_start_sec", 0.0))
            if offset > 0:
                print(f"[MUSIC] [INSTAGRAM_HOOK] Using viral drop offset: {offset:.1f}s ({res.get('source')})")
                return offset
        except Exception as e:
            print(f"[MUSIC] Instagram highlight resolver fallback: {e}")

        return 0.0

    def mix(
        self,
        video_path: str,
        output_path: str,
        music_path: str = None,
        music_start: Optional[float] = None,
        fade_in: float = 0.5,
        fade_out: float = 1.5,
    ) -> Optional[str]:
        """
        Mix background music into a video.

        Args:
            video_path:   Input video with audio
            output_path:  Output MP4 path
            music_path:   Path to music file (MP3/WAV/M4A).
                          If None, auto-picks a random track from library.
            music_start:  Start timestamp (seconds) into the music track.
                          If None, automatically detects the main viral hook / drop.
            fade_in:      Music fade-in duration in seconds
            fade_out:     Music fade-out duration in seconds

        Returns:
            Path to output video with music mixed in, or None on failure
        """
        if not os.path.exists(video_path):
            print(f"[MUSIC] [ERROR] Video not found: {video_path}")
            return None

        # Auto-pick music if not provided
        if not music_path:
            music_path = self._pick_random_track()
            if not music_path:
                print("[MUSIC] [ERROR] No music tracks found in library. Add MP3s to:", self.music_library)
                return None

        if not os.path.exists(music_path):
            print(f"[MUSIC] [ERROR] Music file not found: {music_path}")
            return None

        # Get video duration
        duration = self._get_duration(video_path)
        if not duration:
            print("[MUSIC] [ERROR] Could not read video duration")
            return None

        # Detect viral hook start if not explicitly specified
        if music_start is None:
            music_start = self.detect_viral_hook_start(music_path)

        print(f"[MUSIC] Mixing: {os.path.basename(music_path)}")
        print(f"[MUSIC] Music hook start offset: {music_start:.1f}s")
        print(f"[MUSIC] Video vol: {self.video_vol:.0%} | Music vol: {self.music_vol:.0%}")
        print(f"[MUSIC] Duration: {duration:.1f}s | Fade: {fade_in}s in / {fade_out}s out")

        return self._mix_with_ffmpeg(
            video_path  = video_path,
            music_path  = music_path,
            output_path = output_path,
            duration    = duration,
            music_start = music_start,
            fade_in     = fade_in,
            fade_out    = fade_out,
        )

    def mix_with_youtube(
        self,
        video_path: str,
        output_path: str,
        query: str = "lofi hip hop chill no copyright",
        fade_in: float = 0.5,
        fade_out: float = 1.5,
    ) -> Optional[str]:
        """
        Download a track from YouTube matching the query, then mix it in.

        Args:
            video_path:  Input video
            output_path: Output MP4 path
            query:       YouTube search query for background music
            fade_in/out: Fade durations

        Returns:
            Path to output video, or None on failure
        """
        print(f"[MUSIC] Searching YouTube for: \"{query}\"")
        music_path = self._download_youtube_audio(query)

        if not music_path:
            print("[MUSIC] ⚠️  YouTube download failed, trying local library...")
            return self.mix(video_path, output_path, fade_in=fade_in, fade_out=fade_out)

        return self.mix(video_path, output_path, music_path=music_path,
                        fade_in=fade_in, fade_out=fade_out)

    def mix_with_trending_tiktok(
        self,
        video_path: str,
        output_path: str,
        emotion: str = "chill",
        custom_vibe: str = "",
        music_start: Optional[float] = None,
        fade_in: float = 0.5,
        fade_out: float = 1.5,
    ) -> Optional[str]:
        """
        Selects a top trending TikTok sound matching the clip's emotion,
        downloads/caches it, and mixes it into the video.
        """
        from clipper.core.emotion_music import EmotionMusicSelector
        print(f"[MUSIC] Sourcing trending TikTok sound for emotion: '{emotion.upper()}'")
        selector = EmotionMusicSelector()
        music_path = selector.get_music_for_emotion(emotion=emotion, custom_vibe=custom_vibe)

        if not music_path:
            print("[MUSIC] [WARN] Trending TikTok audio selection failed, falling back to local library...")
            return self.mix(video_path, output_path, music_start=music_start, fade_in=fade_in, fade_out=fade_out)

        return self.mix(video_path, output_path, music_path=music_path,
                        music_start=music_start, fade_in=fade_in, fade_out=fade_out)

    def mix_by_clip(
        self,
        video_path: str,
        output_path: str,
        clip,
        music_start: Optional[float] = None,
        fade_in: float = 0.5,
        fade_out: float = 1.5,
    ) -> Optional[str]:
        """
        Convenience method to mix trending music based on a Clip object's emotion and music_vibe.
        """
        from clipper.core.emotion_music import EmotionMusicSelector
        selector = EmotionMusicSelector()
        music_path = selector.get_music_for_clip(clip)
        return self.mix(
            video_path=video_path,
            output_path=output_path,
            music_path=music_path,
            music_start=music_start,
            fade_in=fade_in,
            fade_out=fade_out,
        )

    def list_library(self) -> list[str]:
        """List all music tracks in the local library."""
        extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
        tracks = [
            str(f) for f in self.music_library.rglob("*")
            if f.suffix.lower() in extensions
        ]
        return sorted(tracks)

    # ─────────────────────────────────────────────────────────────────────────
    # FFMPEG MIXING
    # ─────────────────────────────────────────────────────────────────────────

    def _mix_with_ffmpeg(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        duration: float,
        music_start: float = 0.0,
        fade_in: float = 0.5,
        fade_out: float = 1.5,
    ) -> Optional[str]:
        """
        FFmpeg filter_complex that:
          1. Trims music from viral hook offset
          2. Loops music to fill the video duration
          3. Applies fade in/out to music
          4. Lowers video audio to video_vol
          5. Lowers music to music_vol
          6. Mixes both audio streams together
          7. Normalizes to -14 LUFS
        """
        fade_out_start = max(0, duration - fade_out)

        # Music trim: start at viral hook
        if music_start and music_start > 0:
            music_trim = f"[1:a]atrim=start={music_start:.2f},asetpts=PTS-STARTPTS,aloop=loop=-1:size=2e+09,atrim=duration={duration},"
        else:
            music_trim = f"[1:a]aloop=loop=-1:size=2e+09,atrim=duration={duration},"

        filter_complex = (
            f"{music_trim}"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={fade_out_start}:d={fade_out},"
            f"volume={self.music_vol}[music];"

            # Video audio: just lower the volume
            f"[0:a]volume={self.video_vol}[speech];"

            # Mix both streams
            f"[speech][music]amix=inputs=2:duration=first:normalize=0,"

            # Loudness normalize to -14 LUFS (TikTok/Shorts/Reels standard)
            f"loudnorm=I={LUFS_TARGET}:TP=-1.5:LRA=11[out]"
        )

        cmd = [
            "ffmpeg",
            "-i", video_path,        # input 0: video
            "-i", music_path,        # input 1: music
            "-filter_complex", filter_complex,
            "-map", "0:v",           # video stream from input 0 (untouched)
            "-map", "[out]",         # mixed audio
            "-c:v", "copy",          # no re-encode of video (fast!)
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            "-y",
            output_path,
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[MUSIC] [OK] Done: {os.path.basename(output_path)} ({size:.1f} MB)")
                return output_path
            else:
                print(f"[MUSIC] [ERROR] FFmpeg error:\n{r.stderr[-800:]}")
                return None
        except subprocess.TimeoutExpired:
            print("[MUSIC] [ERROR] Timeout")
            return None
        except Exception as e:
            print(f"[MUSIC] [ERROR] Error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # MUSIC SOURCING
    # ─────────────────────────────────────────────────────────────────────────

    def _pick_random_track(self) -> Optional[str]:
        """Pick a random track from the local music library."""
        tracks = self.list_library()
        if not tracks:
            return None
        track = random.choice(tracks)
        print(f"[MUSIC] Auto-picked: {os.path.basename(track)}")
        return track

    def _download_youtube_audio(self, query: str) -> Optional[str]:
        """
        Download audio from YouTube matching the search query using yt-dlp.
        Saves to music_library/downloaded/ folder.
        """
        download_dir = self.music_library / "downloaded"
        download_dir.mkdir(exist_ok=True)

        # Use yt-dlp to search YouTube and download audio-only
        output_template = str(download_dir / "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp",
            f"ytsearch1:{query}",           # search YouTube, take first result
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "5",          # medium quality (fast download)
            "--max-downloads", "1",
            "--no-playlist",
            "--output", output_template,
            "--quiet",
            "--no-warnings",
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                # Find the newly downloaded file
                files = sorted(download_dir.glob("*.mp3"), key=os.path.getmtime, reverse=True)
                if files:
                    print(f"[MUSIC] Downloaded: {files[0].name}")
                    return str(files[0])
            print(f"[MUSIC] yt-dlp error: {r.stderr[:300]}")
            return None
        except Exception as e:
            print(f"[MUSIC] Download error: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _get_duration(self, path: str) -> Optional[float]:
        """Get video/audio duration using ffprobe."""
        try:
            r = subprocess.run([
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", path
            ], capture_output=True, text=True, timeout=15)
            data = json.loads(r.stdout)
            return float(data.get("format", {}).get("duration", 0))
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python music_mixer.py <video.mp4> <output.mp4> [music.mp3]")
        print("       python music_mixer.py <video.mp4> <output.mp4> --youtube \"lofi chill\"")
        sys.exit(1)

    video_in  = sys.argv[1]
    video_out = sys.argv[2]
    mixer     = MusicMixer()

    if len(sys.argv) > 3 and sys.argv[3] == "--youtube":
        query  = sys.argv[4] if len(sys.argv) > 4 else "lofi hip hop chill no copyright"
        result = mixer.mix_with_youtube(video_in, video_out, query=query)
    elif len(sys.argv) > 3:
        result = mixer.mix(video_in, video_out, music_path=sys.argv[3])
    else:
        result = mixer.mix(video_in, video_out)

    print(f"\n{'✅ Done: ' + result if result else '❌ Failed'}")
