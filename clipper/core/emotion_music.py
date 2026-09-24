"""
Emotion Music Selector
======================
Coordinates clip emotion detection with trending TikTok sounds.
Selects, downloads, and caches the highest-ranked trending music for each mood category.
"""

import os
import sys
import re
import json
import random
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from clipper.core.tiktok_trending_scraper import (
    TikTokTrendingScraper,
    EMOTION_TO_TIKTOK_MOOD,
    get_trending_tiktok_songs,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MUSIC_LIBRARY = Path(os.getenv("MUSIC_LIBRARY", PROJECT_ROOT / "music_library"))
TRENDING_AUDIO_DIR = MUSIC_LIBRARY / "trending"
TRENDING_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class EmotionMusicSelector:
    """
    Finds and downloads the top trending TikTok audio matching the clip's emotion.
    Caches downloaded MP3s in music_library/trending/{mood}/ for zero-latency reuse.
    """

    def __init__(self, scraper: Optional[TikTokTrendingScraper] = None):
        self.scraper = scraper or TikTokTrendingScraper()

    def get_music_for_clip(self, clip) -> Optional[str]:
        """
        Main entry point for Going Merry / Clipper pipelines.
        Inspects clip metadata (is it a podcast, interview, tech discussion?),
        resolves trending audio tailored to that format,
        and returns local MP3 path.
        """
        title = (getattr(clip, "title", "") or "").lower()
        hook = (getattr(clip, "hook", "") or "").lower()
        clip_type = (getattr(clip, "clip_type", "") or "").lower()
        reason = (getattr(clip, "reason", "") or "").lower()

        # Check if content is spoken talk / interview / podcast / business insight
        is_talk = any(kw in f"{title} {hook} {clip_type} {reason}" for kw in [
            "podcast", "interview", "ceo", "founder", "talk", "scaling", "discussion",
            "speech", "insight", "story", "education", "investor", "business", "mindset"
        ])

        emotion = getattr(clip, "emotion", "atmospheric") or "atmospheric"
        music_vibe = getattr(clip, "music_vibe", "") or ""

        # Hard Guardrail: NEVER put Phonk, meme clown sounds, or aggressive drift beats on spoken podcasts/interviews
        if is_talk:
            if emotion.lower() in ("hype", "exciting", "action", "gaming", "phonk", "fonk"):
                emotion = "atmospheric"
            elif emotion.lower() in ("chill", "relaxed", "calm"):
                emotion = "atmospheric"

        return self.get_music_for_emotion(emotion=emotion, custom_vibe=music_vibe)

    def get_music_for_emotion(
        self,
        emotion: str = "atmospheric",
        custom_vibe: str = "",
        top_k: int = 3,
    ) -> Optional[str]:
        """
        Selects a trending sound for the given emotion, downloads it if needed,
        and returns the absolute path to the local audio file.
        """
        mood = EMOTION_TO_TIKTOK_MOOD.get(emotion.lower().strip(), "Atmospheric")
        mood_audio_dir = TRENDING_AUDIO_DIR / mood.lower()
        mood_audio_dir.mkdir(parents=True, exist_ok=True)

        # 1. Fetch current trending TikTok songs for this mood
        trending_songs = self.scraper.get_trending_songs(emotion)
        if not trending_songs:
            print(f"[EMOTION_MUSIC] [WARN] No trending songs found for mood '{mood}'")
            return None

        # 2. Pick a top trending track (random choice from top K to add variety)
        candidate_pool = trending_songs[:top_k] if len(trending_songs) >= top_k else trending_songs
        selected_song = random.choice(candidate_pool)
        title = selected_song.get("title", "Trending Track")
        artist = selected_song.get("artist", "")
        vibe = custom_vibe or selected_song.get("vibe", "")

        print(f"[EMOTION_MUSIC] [*] Emotion: {emotion.upper()} -> TikTok Mood: {mood}")
        print(f"[EMOTION_MUSIC] [TREND] Selected: #{selected_song.get('rank', 1)} '{title}' by {artist or 'Unknown'}")

        # 3. Check if we already have this audio cached locally
        clean_name = self._sanitize_filename(f"{title}_{artist}" if artist else title)
        cached_file = mood_audio_dir / f"{clean_name}.mp3"

        if cached_file.exists() and cached_file.stat().st_size > 10000:
            print(f"[EMOTION_MUSIC] [CACHE] Found existing cached audio: {cached_file.name}")
            return str(cached_file)

        # 4. Check if any audio exists in this mood folder to reuse
        existing_tracks = list(mood_audio_dir.glob("*.mp3"))
        if existing_tracks and random.random() < 0.4:
            # 40% chance to reuse an existing mood track for maximum speed
            chosen = random.choice(existing_tracks)
            print(f"[EMOTION_MUSIC] [REUSE] Reusing previously downloaded mood track: {chosen.name}")
            return str(chosen)

        # 5. Download the exact trending TikTok audio via yt-dlp
        downloaded = self._download_trending_audio(
            song=selected_song,
            output_file=cached_file,
            custom_vibe=vibe
        )
        if downloaded and os.path.exists(downloaded):
            return downloaded

        # 6. Fallback: If specific download fails, try any existing track in mood folder
        if existing_tracks:
            return str(existing_tracks[0])

        return None

    def _download_trending_audio(
        self,
        song: Dict,
        output_file: Path,
        custom_vibe: str = ""
    ) -> Optional[str]:
        """
        Download the audio for the selected trending TikTok sound using yt-dlp.
        Searches YouTube for the exact TikTok audio title and creator.
        """
        title = song.get("title", "")
        artist = song.get("artist", "")
        
        # Build search query targeting the TikTok audio version
        if artist:
            query = f"{title} {artist} tiktok sound audio"
        elif custom_vibe:
            query = f"{title} {custom_vibe} no copyright"
        else:
            query = f"{title} viral tiktok trend audio"

        print(f"[EMOTION_MUSIC] [DOWNLOAD] Sourcing audio via: '{query}'...")

        output_template = str(output_file.with_suffix("")) + ".%(ext)s"

        cmd = [
            "yt-dlp",
            f"ytsearch1:{query}",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "5",
            "--max-downloads", "1",
            "--no-playlist",
            "--output", output_template,
            "--quiet",
            "--no-warnings",
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if output_file.exists() and output_file.stat().st_size > 10000:
                print(f"[EMOTION_MUSIC] [OK] Successfully downloaded: {output_file.name}")
                return str(output_file)
            elif r.returncode in (0, 101) and output_file.exists():
                return str(output_file)
            else:
                print(f"[EMOTION_MUSIC] [WARN] yt-dlp returned code {r.returncode}: {r.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("[EMOTION_MUSIC] [WARN] yt-dlp download timed out")
        except Exception as e:
            print(f"[EMOTION_MUSIC] [ERROR] Download error: {e}")

        return None

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize title/artist for safe filesystem storage."""
        cleaned = re.sub(r'[\\/*?:"<>|]', "", text)
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned[:60].strip("_")


if __name__ == "__main__":
    import sys
    emotion_arg = sys.argv[1] if len(sys.argv) > 1 else "hype"
    selector = EmotionMusicSelector()
    path = selector.get_music_for_emotion(emotion_arg)
    print(f"\nResulting Track Path: {path}")
