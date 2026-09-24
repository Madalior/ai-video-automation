"""
 ██████╗  ██████╗ ██╗███╗   ██╗ ██████╗     ███╗   ███╗███████╗██████╗ ██████╗ ██╗   ██╗
██╔════╝ ██╔═══██╗██║████╗  ██║██╔════╝     ████╗ ████║██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
██║  ███╗██║   ██║██║██╔██╗ ██║██║  ███╗    ██╔████╔██║█████╗  ██████╔╝██████╔╝ ╚████╔╝ 
██║   ██║██║   ██║██║██║╚██╗██║██║   ██║    ██║╚██╔╝██║██╔══╝  ██╔══██╗██╔══██╗  ╚██╔╝  
╚██████╔╝╚██████╔╝██║██║ ╚████║╚██████╔╝    ██║ ╚═╝ ██║███████╗██║  ██║██║  ██║   ██║   
 ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   

Going Merry — Full Auto Viral Shorts Factory
============================================
Named after the Going Merry (One Piece) — a ship that carries the crew everywhere.
This file is the ship that carries your content from raw URL to finished viral short.

Pipeline:
  URL
   │
   ▼
  [1] Transcribe audio (faster-whisper, local, free)
   │
   ▼
  [2] LLM finds best moments (NVIDIA NIM / Llama 4)
   │
   ▼
  [3] Download exact video clip from URL (yt-dlp)
   │
   ▼
  [4] Extract captions with word-level timestamps (Whisper)
   │
   ▼
  [5] LLM detects keywords to highlight in green (NVIDIA NIM)
   │
   ▼
  [6] Remotion renders captioned video (Komika Axis + Deep Glow)
   │
   ▼
  [7] Combine + reformat to 9:16 (FFmpeg + face crop)
   │
   ▼
  [8] Upload to YouTube Shorts / TikTok / Instagram Reels
   │
   ▼
  DONE ✅

Usage:
  python going_merry.py --url "https://youtube.com/watch?v=..." --clips 5
  python going_merry.py --url "..." --clips 3 --platform tiktok --upload
  python going_merry.py --url "..." --clips 1 --preview  # Quick 5s preview render
"""

import os
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import time
import argparse
import shutil
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ── Add project root to path ────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── Rich terminal output ────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    console = Console(legacy_windows=False)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console  = None


def log(msg: str, style: str = ""):
    if HAS_RICH:
        console.print(f"[{style}]{msg}[/{style}]" if style else msg)
    else:
        print(msg)


def banner():
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]GOING MERRY[/bold cyan] — Viral Shorts Factory\n"
            "[dim]URL → LLM → Clip → Caption → Render → Upload[/dim]",
            border_style="cyan"
        ))
    else:
        print("=" * 60)
        print("  GOING MERRY — Viral Shorts Factory")
        print("  URL → LLM → Clip → Caption → Render → Upload")
        print("=" * 60)


# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Transcribe the full video audio
# ════════════════════════════════════════════════════════════════════════════

def step_transcribe(url: str = None, video_path: str = None, cache_dir: Path = None, language: str = None):
    """
    Downloads audio-only from URL or extracts from local video, and transcribes with faster-whisper.
    Returns a Transcript object with word-level timestamps.
    """
    import subprocess
    from clipper.utils.downloader    import Downloader
    from clipper.core.transcriber    import Transcriber

    log("\n[bold][1/7] 🎙️  Transcribing video...[/bold]")

    if video_path and os.path.exists(video_path):
        audio_path = str(cache_dir / f"{Path(video_path).stem}_audio.wav")
        if not os.path.exists(audio_path):
            log(f"      Extracting audio from local file: {os.path.basename(video_path)}")
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
            )
    elif url:
        downloader  = Downloader()
        audio_path  = downloader.download_audio_only(url)
    else:
        log("[red]❌ Neither URL nor local video provided.[/red]")
        return None, None

    if not audio_path or not os.path.exists(audio_path):
        log("[red]❌ Audio preparation failed.[/red]")
        return None, None

    log(f"      Audio: {os.path.basename(audio_path)}")

    transcriber = Transcriber()
    transcript  = transcriber.transcribe(audio_path, language=language)

    if not transcript:
        log("[red]❌ Transcription failed.[/red]")
        return None, None

    log(f"      ✅ {len(transcript.words)} words | {len(transcript.segments)} segments | lang={transcript.language}")
    return transcript, audio_path


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — LLM finds the best viral moments
# ════════════════════════════════════════════════════════════════════════════

def step_find_clips(transcript, num_clips: int, platform: str,
                   min_dur: float, max_dur: float,
                   campaign_prompt: str = None,
                   required_hashtags: list = None):
    """
    Sends the transcript to NVIDIA NIM (Llama 4) to find the
    highest-virality moments. Returns a list of Clip objects.
    """
    from clipper.core.viral_detector import ViralDetector

    log(f"\n[bold][2/7] 🤖  LLM analysing transcript for top {num_clips} moments...[/bold]")

    detector = ViralDetector()
    clips = detector.find_clips(
        transcript_text = transcript.text,
        segments        = transcript.segments,
        video_duration  = transcript.duration,
        num_clips       = num_clips,
        min_duration    = min_dur,
        max_duration    = max_dur,
        target_platform = platform,
        campaign_prompt = campaign_prompt,
        required_hashtags = required_hashtags,
    )

    if not clips:
        log("[red]❌ LLM found no viral moments. Check your LLM API keys in .env[/red]")
        return []

    log(f"      ✅ Found {len(clips)} clips")
    for i, c in enumerate(clips, 1):
        log(f"         [{i}] {c.start:.0f}s–{c.end:.0f}s | Score:{c.score} | \"{c.title[:50]}\"")

    return clips


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Download exact video section from URL
# ════════════════════════════════════════════════════════════════════════════

def step_download_clip(url: str, clip, index: int, cache_dir: Path) -> Optional[str]:
    """
    Downloads only the specific time range of the clip from the URL.
    Much faster than downloading the full video.
    """
    from clipper.utils.downloader import Downloader

    log(f"\n[bold][3/7] 📥  Downloading clip {index}: {clip.start:.0f}s → {clip.end:.0f}s...[/bold]")

    downloader  = Downloader()
    output_path = str(cache_dir / f"raw_clip_{index}.mp4")

    downloaded = downloader.download_video_section(url, clip.start, clip.end, output_path)

    if not downloaded or not os.path.exists(output_path):
        log(f"[red]❌ Clip download failed for clip {index}[/red]")
        return None

    size = os.path.getsize(output_path) / (1024 * 1024)
    log(f"      ✅ Downloaded: {os.path.basename(output_path)} ({size:.1f} MB)")
    return output_path


def step_slice_local_clip(video_path: str, clip, index: int, cache_dir: Path) -> Optional[str]:
    """
    Slices the specific time range from a local video file using FFmpeg.
    """
    import subprocess
    log(f"\n[bold][3/7] ✂️  Slicing local clip {index}: {clip.start:.1f}s → {clip.end:.1f}s...[/bold]")
    output_path = str(cache_dir / f"raw_clip_{index}.mp4")
    dur = max(0.1, clip.end - clip.start)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{clip.start:.2f}",
        "-i", video_path,
        "-t", f"{dur:.2f}",
        "-c:v", "libx264", "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        output_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / (1024 * 1024)
        log(f"      ✅ Sliced: {os.path.basename(output_path)} ({size:.1f} MB)")
        return output_path
    log(f"[red]❌ Slicing failed for clip {index}[/red]")
    return None


def step_add_overlay(video_path: str, overlay_text: str, output_path: str) -> str:
    """
    Burns compliance text badge (e.g. '20% OFF CODE: AF527550') onto video using FFmpeg.
    """
    import subprocess
    escaped = overlay_text.replace(":", "\\:").replace("'", "\\'")
    vf = f"drawtext=text='{escaped}':fontcolor=white:fontsize=36:box=1:boxcolor=black@0.75:boxborderw=12:x=(w-text_w)/2:y=130"
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf, "-c:a", "copy", output_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0 and os.path.exists(output_path):
        return output_path
    return video_path


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Reformat to 9:16 vertical with face crop
# ════════════════════════════════════════════════════════════════════════════

def step_reformat(clip_path: str, clip, index: int, output_dir: Path,
                  add_blur_bg: bool = True) -> Optional[str]:
    """
    Reformats the clip to 1080x1920 (9:16) with:
    - Face tracking crop (keeps speaker in frame)
    - Blurred background (pillarbox fill)
    """
    from clipper.core.clip_cutter import ClipCutter

    log(f"\n[bold][4/7] ✂️   Reformatting to 9:16 vertical...[/bold]")

    cutter  = ClipCutter()
    result  = cutter.cut_and_reformat(
        source_path  = clip_path,
        start        = 0,
        end          = clip.end - clip.start,
        title        = clip.title,
        score        = clip.score,
        add_blur_bg  = add_blur_bg,
        is_pre_cut   = True,
    )

    if not result:
        log(f"[red]❌ Reformat failed for clip {index}[/red]")
        return None

    log(f"      ✅ Reformatted: {os.path.basename(result.path)}")
    return result.path


# ════════════════════════════════════════════════════════════════════════════
# STEP 5 + 6 — Burn captions (Whisper + LLM keywords + Remotion)
# ════════════════════════════════════════════════════════════════════════════

def step_burn_captions(
    video_path: str,
    transcript,
    clip,
    index: int,
    output_dir: Path,
    overlay_text: str = None,
    preview_frames: int = None,
    tracking_json: str = None,
    tracking_data: list = None,
    job_id: str = None,
) -> Optional[str]:
    """
    Extracts the word-level timestamps for this clip's time window,
    runs LLM keyword detection, and renders the Deep Glow Remotion captions with Whop overlay badge.
    """
    from clipper.core.caption_burner import CaptionBurner

    log(f"\n[bold][5+6/7] 💬  Burning captions (LLM keywords + Remotion)...[/bold]")

    # Build word list for this clip time window
    clip_words = [
        {"text": w.text, "start": w.start, "end": w.end}
        for w in transcript.words
    ]

    prefix = f"{job_id}_" if job_id else ""
    output_path = str(output_dir / f"{prefix}clip_{index:02d}_captioned.mp4")

    style_overrides = {"overlayText": overlay_text} if overlay_text else {}
    if hasattr(clip, "hook") and clip.hook:
        style_overrides["hook"] = clip.hook
    if hasattr(clip, "title") and clip.title:
        style_overrides["title"] = clip.title

    burner    = CaptionBurner()
    captioned = burner.burn_from_words(
        video_path      = video_path,
        words           = clip_words,
        output_path     = output_path,
        offset_sec      = clip.start,
        duration_sec    = clip.end - clip.start,
        style_overrides = style_overrides,
        max_frames      = preview_frames,
        tracking_json   = tracking_json,
        tracking_data   = tracking_data,
    )

    if not captioned:
        log(f"[yellow]⚠️  Caption render failed — falling back to FFmpeg overlay badge[/yellow]")
        if overlay_text:
            return step_add_overlay(video_path, overlay_text, output_path)
        return video_path

    log(f"      ✅ Captions burned: {os.path.basename(captioned)}")
    return captioned


# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Upload (stub — plug in your platform uploader here)
# ════════════════════════════════════════════════════════════════════════════

def step_upload(video_path: str, clip, platform: str, account_id: str = "acc_01") -> bool:
    """
    Upload to target platforms via Local Multi-Account Engine (Zero Docker).
    Automatically dispatches to YouTube Shorts, TikTok, and Instagram Reels.
    """
    log(f"\n[bold][7/7] 🚀  Auto-Upload ({platform}) via Local Bulk Engine [{account_id}]...[/bold]")

    try:
        from clipper.core.postiz_manager import PostizManager
        uploader = PostizManager()
        
        # Prepare title, caption, hashtags
        title = getattr(clip, 'title', 'Viral Short')
        hook = getattr(clip, 'hook', '')
        tags = getattr(clip, 'hashtags', [])
        
        res = uploader.publish_clip(
            video_path=video_path,
            title=title,
            caption=f"{hook}\n\n{title}",
            hashtags=tags,
            target_platform=platform,
            simulate=False,
            account_id=account_id
        )

        if res.get("success"):
            log(f"      ✅ Upload successfully dispatched to: {', '.join(res.get('platforms', [platform]))}")
            return True
        else:
            log(f"      [yellow]⚠️ Upload warning: {res.get('error', 'Unknown')}[/yellow]")
            return False


    except Exception as e:
        log(f"[yellow]⚠️ Postiz upload manager failed: {e}. File saved locally.[/yellow]")
        return False


# ════════════════════════════════════════════════════════════════════════════
# STEP 6b.1 — Trending Song Finder & Tester
# ════════════════════════════════════════════════════════════════════════════

def step_find_trending_song(genre_or_emotion: str = "phonk", download: bool = True) -> Optional[dict]:
    """
    Discovers, ranks, and retrieves the top trending songs for a given genre/mood (e.g. 'phonk' / 'fonk' / 'hype').
    Prints a rich summary table and downloads/caches the top track.
    """
    import re
    banner()
    query = (genre_or_emotion or "phonk").strip().lower()
    log(f"\n[bold cyan]🎵  [SONG FINDER] Searching trending '{query.upper()}' audio today...[/bold cyan]")

    from clipper.core.tiktok_trending_scraper import TikTokTrendingScraper, EMOTION_TO_TIKTOK_MOOD
    from clipper.core.emotion_music import EmotionMusicSelector, TRENDING_AUDIO_DIR

    # Map common aliases (fonk, phonk, funk, drift -> Exciting / Phonk)
    if query in ["fonk", "phonk", "funk", "brazilian phonk", "drift"]:
        emotion_tag = "phonk"
    else:
        emotion_tag = query

    scraper = TikTokTrendingScraper()
    songs = scraper.get_trending_songs(emotion_tag)

    if not songs:
        log(f"[red]❌ No trending tracks found for '{query}'.[/red]")
        return None

    mood = EMOTION_TO_TIKTOK_MOOD.get(emotion_tag, "Exciting")
    mood_dir = TRENDING_AUDIO_DIR / mood.lower()
    mood_dir.mkdir(parents=True, exist_ok=True)

    log(f"      ✅ Found {len(songs)} trending tracks for category: [yellow]{mood}[/yellow]\n")

    if HAS_RICH:
        table = Table(title=f"🔥 Top Trending {query.title()} Sounds Today (TikTok & Shorts)", show_header=True, header_style="bold cyan")
        table.add_column("Rank", width=6, justify="center")
        table.add_column("Title", width=34)
        table.add_column("Artist", width=22)
        table.add_column("Vibe / Style", width=38)
        table.add_column("Status", width=12, justify="center")

        for s in songs:
            clean_name = re.sub(r'[\\/*?:"<>|]', "", f"{s.get('title')}_{s.get('artist', '')}" if s.get('artist') else s.get('title', ''))
            clean_name = re.sub(r'\s+', '_', clean_name)[:60].strip("_")
            cached = (mood_dir / f"{clean_name}.mp3").exists()
            status_badge = "[green]Cached[/green]" if cached else "[dim]Available[/dim]"
            table.add_row(
                f"#{s.get('rank', '-')}",
                str(s.get('title', 'Unknown')),
                str(s.get('artist', 'Unknown')),
                str(s.get('vibe', '')),
                status_badge
            )
        console.print(table)
    else:
        for s in songs:
            print(f"  #{s.get('rank')} {s.get('title')} by {s.get('artist', 'Unknown')} ({s.get('vibe', '')})")

    top_song = songs[0]
    result = {
        "query": query,
        "mood": mood,
        "top_song": top_song,
        "all_songs": songs,
        "audio_path": None,
    }

    if download and top_song:
        log(f"\n[bold green]📥 Sourcing / Verifying audio for #1 track: \"{top_song.get('title')}\"...[/bold green]")
        selector = EmotionMusicSelector(scraper=scraper)
        clean_name = selector._sanitize_filename(f"{top_song['title']}_{top_song.get('artist', '')}" if top_song.get('artist') else top_song['title'])
        cached_file = mood_dir / f"{clean_name}.mp3"

        if cached_file.exists() and cached_file.stat().st_size > 10000:
            audio_path = str(cached_file)
            log(f"      ⚡ Found existing high-quality cache: {cached_file.name}")
        else:
            audio_path = selector._download_trending_audio(
                song=top_song,
                output_file=cached_file,
                custom_vibe=top_song.get("vibe", "")
            )

        if audio_path and os.path.exists(audio_path):
            size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            result["audio_path"] = audio_path
            log(f"      ✅ [bold green]Ready for Going Merry audio mixing:[/bold green] {os.path.basename(audio_path)} ({size_mb:.2f} MB)")
            log(f"      📁 File path: [dim]{audio_path}[/dim]")
        else:
            log(f"      [yellow]⚠️ Track download skipped or unavailable. Catalog details ready.[/yellow]")

    return result


# ════════════════════════════════════════════════════════════════════════════
# SINGLE CLIP PROCESSOR (Thread-safe for parallel rendering)
# ════════════════════════════════════════════════════════════════════════════

def process_single_clip(
    i: int,
    clip,
    total_clips: int,
    url: str,
    video_file: str,
    cache_dir: Path,
    output_dir: Path,
    transcript,
    overlay: str,
    preview_frames: Optional[int],
    music: bool,
    music_query: str,
    upload: bool,
    platform: str,
    preview: bool,
    user_id: int,
    clip_id: Optional[int],
    checkpoint,
    job_id: str,
    resume: bool = True,
    account_id: str = "acc_01",
) -> Optional[str]:
    from clipper.core.event_bus import bus

    log(f"\n{'─' * 60}")
    log(f"[bold]Clip {i}/{total_clips}: \"{clip.title}\"[/bold]")
    log(f"[dim]  {clip.start:.1f}s → {clip.end:.1f}s | Score: {clip.score} | {clip.platform}[/dim]")
    log(f"[dim]  Hook: {clip.hook[:80]}[/dim]")

    expected_output = str(
        output_dir / f"whop_{job_id}_clip_{i:02d}_captioned.mp4"
        if job_id
        else output_dir / f"clip_{i:02d}_captioned.mp4"
    )

    # Checkpoint recovery check
    if resume and not preview:
        final_path = None
        if checkpoint:
            saved = checkpoint.get_clip_progress(i)
            if saved and saved.get("final") and os.path.exists(saved["final"]) and os.path.getsize(saved["final"]) > 1024:
                final_path = saved["final"]
        if not final_path and os.path.exists(expected_output) and os.path.getsize(expected_output) > 1024:
            final_path = expected_output
            if checkpoint:
                checkpoint.save_clip_progress(i, {"final": final_path})

        if final_path:
            log(f"      ⏩ [bold green]Clip {i} restored from checkpoint/disk: {os.path.basename(final_path)} ({os.path.getsize(final_path)/1024/1024:.2f} MB)[/bold green]")
            bus.emit("stage.clip.completed", {"job_id": job_id, "clip_index": i, "video": final_path, "resumed": True})
            if upload and not (checkpoint and checkpoint.get_clip_progress(i) and checkpoint.get_clip_progress(i).get("uploaded")) and not preview:
                bus.emit("stage.7.upload", {"job_id": job_id, "clip_index": i, "status": "starting"})
                up_ok = step_upload(final_path, clip, platform, account_id=account_id)
                if checkpoint:
                    checkpoint.save_clip_progress(i, {"uploaded": up_ok})
                bus.emit("stage.7.upload", {"job_id": job_id, "clip_index": i, "status": "completed", "success": up_ok})
            return final_path

    # 3. Download or slice raw clip section
    raw_clip = None
    if resume and checkpoint:
        saved = checkpoint.get_clip_progress(i)
        if saved and saved.get("raw_clip") and os.path.exists(saved["raw_clip"]):
            raw_clip = saved["raw_clip"]
            log(f"      ⏩ Restored sliced raw clip from checkpoint: {os.path.basename(raw_clip)}")

    if not raw_clip:
        bus.emit("stage.3.download", {"job_id": job_id, "clip_index": i, "status": "starting"})
        if video_file:
            raw_clip = step_slice_local_clip(video_file, clip, i, cache_dir)
        else:
            raw_clip = step_download_clip(url, clip, i, cache_dir)
        if not raw_clip:
            bus.emit("stage.3.download", {"job_id": job_id, "clip_index": i, "status": "failed"})
            return None
        bus.emit("stage.3.download", {"job_id": job_id, "clip_index": i, "status": "completed", "path": raw_clip})
        if checkpoint:
            checkpoint.save_clip_progress(i, {"raw_clip": raw_clip})

    # 4. Aspect Ratio & Reformatting Check
    is_already_vertical = False
    try:
        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", raw_clip],
            capture_output=True, text=True
        )
        if "x" in probe.stdout:
            w_str, h_str = probe.stdout.strip().split("x")
            if int(h_str) > int(w_str):
                is_already_vertical = True
                log(f"   ℹ️ Video is already vertical 9:16 ({w_str}x{h_str}). Skipping horizontal reframing.")
    except Exception:
        pass

    tracking_json = None
    if is_already_vertical:
        formatted = raw_clip
        tracking_json = "skip"
    else:
        # 3.5 Speaker Diarization
        speakers_json = str(cache_dir / f"clip_{i:02d}_speakers.json")
        try:
            from clipper.core.speaker_detector import SpeakerDetector
            log(f"\n[bold][3.5/7] 🗣️  Detecting speakers (pyannote)...[/bold]")
            detector = SpeakerDetector()
            detector.detect(raw_clip, speakers_json)
        except Exception as e:
            log(f"[yellow]⚠️  Speaker detection failed: {e}. Smart reframing will fall back to center crop.[/yellow]")

        # 4. Face Tracking & Smart Reframing
        bus.emit("stage.4.tracking", {"job_id": job_id, "clip_index": i, "status": "starting"})
        tracking_json = str(cache_dir / f"clip_{i:02d}_tracking.json")
        try:
            from clipper.core.face_tracker import FaceTracker
            log(f"\n[bold][4a/7] 👁️  Tracking faces (YOLO)...[/bold]")
            tracker = FaceTracker()
            tracker.track(raw_clip, tracking_json)
            bus.emit("stage.4.tracking", {"job_id": job_id, "clip_index": i, "status": "completed"})
        except Exception as e:
            log(f"[red]❌ Face tracking failed: {e}[/red]")
            bus.emit("stage.4.tracking", {"job_id": job_id, "clip_index": i, "status": "failed", "error": str(e)})
            return None

        formatted_out = str(output_dir / f"clip_{i:02d}_reframed.mp4")
        log(f"\n[bold][4b/7] 🎬  Smart Reframing (Dynamic Layout)...[/bold]")
        bus.emit("stage.5.reframe", {"job_id": job_id, "clip_index": i, "status": "starting"})
        try:
            from clipper.core.split_screen import SmartReframer
            reframer = SmartReframer()
            formatted = reframer.reframe(
                source_path=raw_clip, 
                output_path=formatted_out, 
                tracking_json=tracking_json, 
                speakers_json=speakers_json
            )
            if not formatted:
                formatted = raw_clip
            bus.emit("stage.5.reframe", {"job_id": job_id, "clip_index": i, "status": "completed", "path": formatted})
        except Exception as e:
            log(f"[yellow]⚠️  Smart reframing error: {e}[/yellow]")
            formatted = raw_clip
            bus.emit("stage.5.reframe", {"job_id": job_id, "clip_index": i, "status": "fallback"})

    if checkpoint:
        checkpoint.save_clip_progress(i, {"formatted": formatted, "tracking_json": tracking_json})

    # 5+6. Burn captions (Deep Glow subtitles + Whop overlay badge via Remotion)
    bus.emit("stage.6.captions", {"job_id": job_id, "clip_index": i, "status": "starting"})
    final = step_burn_captions(
        video_path    = formatted,
        transcript    = transcript,
        clip          = clip,
        index         = i,
        output_dir    = output_dir,
        overlay_text  = overlay,
        preview_frames= preview_frames,
        tracking_json = tracking_json,
        job_id        = job_id,
    )
    bus.emit("stage.6.captions", {"job_id": job_id, "clip_index": i, "status": "completed" if final else "failed", "path": final})

    # 6b. Mix background music (optional)
    if music and final and not preview:
        from clipper.core.music_mixer import MusicMixer
        music_out = str(output_dir / f"clip_{i:02d}_music.mp4")
        emotion = getattr(clip, "emotion", "chill") or "chill"
        music_vibe = getattr(clip, "music_vibe", "") or ""
        log(f"\n[bold][6b/7] 🎵 Mixing trending TikTok music for emotion: [cyan]{emotion.upper()}[/cyan]...[/bold]")
        
        mixer = MusicMixer()
        if music_query and music_query != "lofi hip hop chill no copyright":
            music_result = mixer.mix_with_youtube(final, music_out, query=music_query)
        else:
            music_result = mixer.mix_with_trending_tiktok(
                video_path=final,
                output_path=music_out,
                emotion=emotion,
                custom_vibe=music_vibe,
            )

        if music_result:
            final = music_result
            log(f"      ✅ Music mixed: {os.path.basename(music_result)}")
        else:
            log("[yellow]⚠️  Music mix failed, keeping un-mixed version[/yellow]")

    # 6c. Whop Compliance check
    if overlay and final:
        log(f"      ✅ Whop compliance overlay badge integrated: [yellow]{overlay}[/yellow]")

    if final:
        if checkpoint:
            checkpoint.save_clip_progress(i, {"final": final})

        # Persist clip record to database (Flowchart: PIPELINE --> DB)
        try:
            from web_app.app import app, db
            from web_app.models import Clip as ClipModel, UploadJob
            with app.app_context():
                duration_val = float(getattr(clip, 'duration', 0.0) or (getattr(clip, 'end', 0.0) - getattr(clip, 'start', 0.0)))
                title_val = getattr(clip, 'title', f"Viral Moment #{i}")
                hook_val = getattr(clip, 'hook', "")
                score_val = int(getattr(clip, 'score', 85))

                target_rec = None
                if clip_id and i == 1:
                    target_rec = ClipModel.query.get(clip_id)

                if target_rec:
                    target_rec.clip_path = final
                    target_rec.title = title_val
                    target_rec.hook = hook_val
                    target_rec.score = score_val
                    target_rec.duration = duration_val
                    target_rec.status = "posted" if upload else "ready"
                else:
                    new_clip_rec = ClipModel(
                        user_id=user_id or 1,
                        source_url=url or (video_file or "local_file"),
                        clip_path=final,
                        title=title_val,
                        hook=hook_val,
                        score=score_val,
                        duration=duration_val,
                        status="posted" if upload else "ready",
                        hashtags=json.dumps(getattr(clip, 'hashtags', []))
                    )
                    db.session.add(new_clip_rec)
                    db.session.flush()
                    target_rec = new_clip_rec

                if upload and target_rec:
                    upload_job = UploadJob(
                        user_id=user_id or 1,
                        clip_id=target_rec.id,
                        platform=platform if platform != "all" else "youtube_shorts",
                        caption=f"{hook_val}\n\n{title_val}",
                        status="done"
                    )
                    db.session.add(upload_job)

                db.session.commit()
        except Exception as e:
            log(f"[dim]DB sync notice: {e}[/dim]")

    # 7. Upload (optional)
    if upload and final and not preview:
        bus.emit("stage.7.upload", {"job_id": job_id, "clip_index": i, "status": "starting"})
        up_ok = step_upload(final, clip, platform, account_id=account_id)
        if checkpoint:
            checkpoint.save_clip_progress(i, {"uploaded": up_ok})
        bus.emit("stage.7.upload", {"job_id": job_id, "clip_index": i, "status": "completed", "success": up_ok})

    bus.emit("stage.clip.completed", {"job_id": job_id, "clip_index": i, "video": final})
    return final


# ════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════

def sail(
    url:          str   = None,
    video_file:   str   = None,
    whop:         bool  = False,
    campaign:     str   = None,
    overlay:      str   = None,
    num_clips:    int   = 5,
    platform:     str   = "all",
    upload:       bool  = False,
    add_blur_bg:  bool  = True,
    split_screen: bool  = False,
    music:        bool  = False,
    music_query:  str   = "lofi hip hop chill no copyright",
    min_dur:      float = 20.0,
    max_dur:      float = 90.0,
    language:     str   = None,
    preview:      bool  = False,
    user_id:      int   = 1,
    clip_id:      int   = None,
    job_id:       str   = None,
    resume:       bool  = True,
    workers:      int   = 1,
    account_id:   str   = "acc_01",
) -> list[str]:
    """
    Full pipeline: URL / Local File → transcript → LLM clips → slice → captions → Whop overlay → upload.
    Supports real-time EventBus streaming, checkpoint recovery, and parallel clip rendering.
    """
    start_time = time.time()
    banner()

    cache_dir  = Path(os.getenv("CACHE_DIR",  "cache"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
    cache_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    if not resume:
        os.environ["FORCE_RE_RENDER"] = "1"
        log("[bold yellow]⚡ Force Re-generation: Running full production pipeline from scratch (--no-resume)...[/bold yellow]")
    elif "FORCE_RE_RENDER" in os.environ:
        del os.environ["FORCE_RE_RENDER"]

    from clipper.core.checkpoint import CheckpointManager
    from clipper.core.event_bus import bus

    if not job_id:
        job_id = CheckpointManager.generate_job_id(url=url, video_file=video_file)

    checkpoint = CheckpointManager(cache_dir, job_id)
    log(f"[bold cyan]🛳️  Job ID:[/bold cyan] [yellow]{job_id}[/yellow]")
    bus.emit("pipeline.start", {
        "job_id": job_id,
        "url": url,
        "video_file": video_file,
        "num_clips": num_clips,
        "platform": platform,
        "workers": workers
    })

    # ── Whop / Dynamic Campaign Configuration ─────────────────────────────
    camp_adapter = None
    campaign_prompt = None
    required_hashtags = None
    if whop or campaign:
        from clipper.core.campaign_adapter import CampaignAdapter
        camp_adapter = CampaignAdapter(campaign)
        if not overlay:
            overlay = camp_adapter.get_overlay_badge()
        min_dur = max(min_dur, camp_adapter.get_min_duration())
        campaign_prompt = camp_adapter.get_prompt_injection()
        required_hashtags = camp_adapter.required_hashtags
        log(f"\n[bold green]🏆 DYNAMIC CAMPAIGN ADAPTER ACTIVE[/bold green]")
        log(f"   • Campaign: [cyan]{camp_adapter.campaign_name}[/cyan]")
        log(f"   • Overlay Badge: [yellow]{overlay or 'None'}[/yellow]")
        log(f"   • Min Duration: {min_dur}s")
        if camp_adapter.required_tag:
            log(f"   • Required Tag: {camp_adapter.required_tag}")
        if required_hashtags:
            log(f"   • Required Hashtags: {' '.join(required_hashtags)}")

        # Strict Audio Policy Compliance for Whop Content Rewards:
        audio_policy = camp_adapter.get_audio_policy()
        log(f"   • Audio Policy: [yellow]{audio_policy['reason']}[/yellow]")
        if audio_policy.get("required_track"):
            music = True
            music_query = audio_policy["required_track"]
            log(f"   • Mandated Sound: [green]{music_query}[/green]")
        elif not audio_policy.get("allowed"):
            # Strictly do not add background music if not requested in Whop brief
            music = False
            log(f"   • Background Music: [dim]Disabled (Original dialogue protected for Whop payout compliance)[/dim]")
        else:
            log(f"   • Background Music: [green]Allowed by campaign guidelines[/green]")

    preview_frames = 150 if preview else None
    final_videos: list[str] = []

    # ── Check if Entire Job is Already Completed ───────────────────────────
    if not resume:
        checkpoint.clear()
        log("[bold yellow]🔄 Running pipeline FROM SCRATCH (checkpoint & cached clips bypassed)...[/bold yellow]")
    elif not preview:
        saved_final = []
        if checkpoint.is_completed():
            saved_final = [v for v in checkpoint.get_final_videos() if os.path.exists(v) and os.path.getsize(v) > 1024]

        # Disk check fallback: check if target output files already exist
        if not saved_final or len(saved_final) < num_clips:
            expected_clips = [str(output_dir / f"clip_{idx:02d}_captioned.mp4") for idx in range(1, num_clips + 1)]
            if all(os.path.exists(p) and os.path.getsize(p) > 1024 for p in expected_clips):
                saved_final = expected_clips
                checkpoint.mark_completed(saved_final)

        if saved_final and len(saved_final) >= num_clips:
            log(f"\n[bold green]⏩ [RESTORED] All {len(saved_final[:num_clips])} clip(s) already completed from previous run! Restoring in 0.01s...[/bold green]")
            for idx, v in enumerate(saved_final[:num_clips], 1):
                log(f"   [{idx}] {v} ({os.path.getsize(v)/1024/1024:.2f} MB)")
            bus.emit("pipeline.complete", {
                "job_id": job_id,
                "final_videos": saved_final[:num_clips],
                "elapsed_sec": 0.01,
                "total_clips": len(saved_final[:num_clips]),
                "resumed_full": True
            })
            return saved_final[:num_clips]

    # ── Step 1: Transcribe ──────────────────────────────────────────────────
    transcript, audio_path = (None, None)
    if resume:
        transcript, audio_path = checkpoint.get_step_1_transcript()
        if transcript:
            log(f"\n[bold green]⏩ [1/7] Restored transcript from checkpoint ({len(transcript.words)} words)[/bold green]")
            bus.emit("stage.1.transcribe", {"job_id": job_id, "status": "resumed", "words": len(transcript.words)})

    if not transcript:
        bus.emit("stage.1.transcribe", {"job_id": job_id, "status": "starting"})
        transcript, audio_path = step_transcribe(url=url, video_path=video_file, cache_dir=cache_dir, language=language)
        if not transcript:
            bus.emit("pipeline.error", {"job_id": job_id, "stage": 1, "error": "Transcription failed"})
            return []
        checkpoint.save_step_1_transcribe(transcript, audio_path)
        bus.emit("stage.1.transcribe", {"job_id": job_id, "status": "completed", "words": len(transcript.words)})

    # ── Step 2: LLM finds viral moments (or auto-clip single short) ────────
    clips = None
    if resume:
        clips = checkpoint.get_step_2_clips()
        if clips:
            log(f"\n[bold green]⏩ [2/7] Restored {len(clips)} viral clips from checkpoint[/bold green]")
            bus.emit("stage.2.llm", {"job_id": job_id, "status": "resumed", "count": len(clips)})

    if not clips:
        bus.emit("stage.2.llm", {"job_id": job_id, "status": "starting"})
        if video_file and (transcript.duration <= max_dur or num_clips == 1):
            from clipper.core.viral_detector import Clip
            clip_end = transcript.duration if transcript.duration > 0 else 40.5
            camp_name = camp_adapter.campaign_name if camp_adapter else Path(video_file).stem.replace("_", " ").title()
            camp_badge = camp_adapter.get_overlay_badge() if camp_adapter else ""
            camp_hook = f"{camp_name} {camp_badge}".strip() if camp_badge else f"Must Watch {camp_name}"
            camp_tags = camp_adapter.required_hashtags if (camp_adapter and camp_adapter.required_hashtags) else ["#shorts", "#viral"]
            clips = [Clip(
                start=0.0,
                end=clip_end,
                score=95,
                hook=camp_hook,
                title=f"{camp_name} — High Retention",
                reason=f"Selected footage compliant with {camp_name} campaign brief",
                hashtags=camp_tags,
                platform=platform if platform != "all" else "shorts",
                clip_type="insight",
                emotion="hype"
            )]
            log(f"\n[bold][2/7] 🎬 Local short video detected: 0.0s → {clip_end:.1f}s[/bold]")
        else:
            clips = step_find_clips(
                transcript, num_clips, platform, min_dur, max_dur,
                campaign_prompt=campaign_prompt,
                required_hashtags=required_hashtags
            )

        if not clips:
            bus.emit("pipeline.error", {"job_id": job_id, "stage": 2, "error": "No clips found"})
            return []
        checkpoint.save_step_2_clips(clips)
        bus.emit("stage.2.llm", {"job_id": job_id, "status": "completed", "count": len(clips)})

    # ── Steps 3–7: Process each clip ───────────────────────────────────────
    log(f"\n[bold cyan]Processing {len(clips)} clips (Workers: {workers})...[/bold cyan]")

    if workers > 1 and len(clips) > 1:
        import concurrent.futures
        log(f"      ⚡ Running in parallel across {workers} worker threads")
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {
                executor.submit(
                    process_single_clip,
                    i, clip, len(clips), url, video_file, cache_dir, output_dir,
                    transcript, overlay, preview_frames, music, music_query,
                    upload, platform, preview, user_id, clip_id,
                    checkpoint, job_id, resume, account_id
                ): i
                for i, clip in enumerate(clips, 1)
            }
            results = {}
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    res = future.result()
                    if res:
                        results[idx] = res
                except Exception as exc:
                    log(f"[red]❌ Clip {idx} generated an exception: {exc}[/red]")
                    bus.emit("pipeline.error", {"job_id": job_id, "clip_index": idx, "error": str(exc)})

            for i in sorted(results.keys()):
                final_videos.append(results[i])
    else:
        for i, clip in enumerate(clips, 1):
            res = process_single_clip(
                i, clip, len(clips), url, video_file, cache_dir, output_dir,
                transcript, overlay, preview_frames, music, music_query,
                upload, platform, preview, user_id, clip_id,
                checkpoint, job_id, resume, account_id
            )
            if res:
                final_videos.append(res)

    checkpoint.mark_completed(final_videos)

    # ── Summary ─────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    bus.emit("pipeline.complete", {
        "job_id": job_id,
        "final_videos": final_videos,
        "elapsed_sec": round(elapsed, 1),
        "total_clips": len(clips)
    })

    log(f"\n{'═' * 60}")
    log(f"[bold green]DONE ✅  {len(final_videos)}/{len(clips)} clips in {elapsed:.0f}s[/bold green]")
    log(f"[dim]Output: {output_dir.absolute()}[/dim]")

    if HAS_RICH and final_videos:
        table = Table(title="Generated Clips", show_header=True, header_style="bold cyan")
        table.add_column("#",     width=4)
        table.add_column("File",  width=45)
        table.add_column("Size",  width=10)
        for i, path in enumerate(final_videos, 1):
            size = f"{os.path.getsize(path)/1024/1024:.1f} MB" if os.path.exists(path) else "?"
            table.add_row(str(i), os.path.basename(path), size)
        console.print(table)

    return final_videos


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Going Merry — Full Auto Viral Shorts Factory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python going_merry.py --find-song phonk
  python going_merry.py --url "https://youtube.com/watch?v=..." --clips 5
  python going_merry.py --video-file "campaigns/raw_footage/sample_clip.mp4" --whop --preview
  python going_merry.py --video-file "sample.mp4" --whop --overlay "20% OFF CODE: AF527550"
  python going_merry.py --url "..." --clips 4 --workers 2
        """
    )
    parser.add_argument("--url",        default=None,   type=str,   help="YouTube or video URL")
    parser.add_argument("--video-file", "--file", default=None, type=str, help="Local video file path")
    parser.add_argument("--whop",       action="store_true",  help="Enable Whop Campaign mode (auto-loads active brief & overlay)")
    parser.add_argument("--campaign",   default=None,   type=str,   help="Campaign brief path (e.g. campaigns/active_campaign_brief.json) or name")
    parser.add_argument("--overlay",    default=None,   type=str,   help="Custom overlay text badge")
    parser.add_argument("--clips",      default=1,      type=int,   help="Number of clips to generate (default: 1)")
    parser.add_argument("--platform",   default="all",  type=str,
                        choices=["tiktok", "reels", "shorts", "instagram", "youtube", "all"],
                        help="Target platform (default: all)")
    parser.add_argument("--min",        default=20.0,   type=float, help="Min clip duration seconds (default: 20)")
    parser.add_argument("--max",        default=90.0,   type=float, help="Max clip duration seconds (default: 90)")
    parser.add_argument("--lang",       default=None,   type=str,   help="Force language (e.g. en)")
    parser.add_argument("--no-blur-bg",    action="store_true",  help="Skip blur background")
    parser.add_argument("--split-screen",   action="store_true",  help="Enable split screen for gaming/react content")
    parser.add_argument("--music",          action="store_true",  help="Add background music")
    parser.add_argument("--music-query",    default="lofi hip hop chill no copyright", type=str,
                        help="YouTube search query for background music (default: lofi hip hop chill)")
    parser.add_argument("--upload",         action="store_true",  help="Auto-upload after render")
    parser.add_argument("--preview",        action="store_true",  help="Quick render (first 150 frames only)")
    parser.add_argument("--job-id",         default=None,   type=str,   help="Custom job ID for tracking and checkpointing")
    parser.add_argument("--no-resume",      action="store_true",        help="Disable checkpoint resumption and recompute from scratch")
    parser.add_argument("--workers",        default=1,      type=int,   help="Number of parallel clip rendering workers (default: 1)")
    parser.add_argument("--find-song", "--test-song", default=None, nargs="?", const="phonk", type=str,
                        help="Test the song finder: find trending songs for emotion/genre (e.g. 'phonk', 'fonk', 'hype', 'chill')")

    parser.add_argument("--account-id",     default="acc_01", type=str, help="Target account persona ID (e.g. acc_c71c624f)")

    args = parser.parse_args()

    if args.find_song is not None:
        step_find_trending_song(genre_or_emotion=args.find_song)
        return

    if not args.url and not args.video_file:
        parser.error("Must provide either --url or --video-file (or use --find-song [genre])")

    sail(
        url          = args.url,
        video_file   = args.video_file,
        whop         = args.whop or bool(args.campaign),
        campaign     = args.campaign,
        overlay      = args.overlay,
        num_clips    = args.clips,
        platform     = args.platform,
        upload       = args.upload,
        add_blur_bg  = not args.no_blur_bg,
        split_screen = args.split_screen,
        music        = args.music,
        music_query  = args.music_query,
        min_dur      = args.min,
        max_dur      = args.max,
        language     = args.lang,
        preview      = args.preview,
        job_id       = args.job_id,
        resume       = not args.no_resume,
        workers      = args.workers,
        account_id   = args.account_id,
    )


if __name__ == "__main__":
    main()


