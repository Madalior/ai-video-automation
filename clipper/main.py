"""
 ██████╗██╗     ██╗██████╗ ██████╗ ███████╗██████╗
██╔════╝██║     ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║     ██║     ██║██████╔╝██████╔╝█████╗  ██████╔╝
██║     ██║     ██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
╚██████╗███████╗██║██║     ██║     ███████╗██║  ██║
 ╚═════╝╚══════╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝

AI Video Repurposing Tool — OpusClip Alternative
Powered by: NVIDIA NIM + faster-whisper + FFmpeg

Usage:
  python main.py --url "https://youtube.com/watch?v=..." --clips 8
  python main.py --file "video.mp4" --clips 5 --platform tiktok
  python main.py --url "..." --no-captions --no-reformat
"""

import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# ── Rich terminal output ─────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel   import Panel
    from rich.table   import Table
    from rich         import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console  = None

# ── Clipper modules ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from clipper.utils.downloader       import Downloader
from clipper.core.transcriber       import Transcriber
from clipper.core.viral_detector    import ViralDetector
from clipper.core.clip_cutter       import ClipCutter
from clipper.core.caption_burner    import CaptionBurner


def print_banner():
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]CLIPPER[/bold cyan] — AI Video Repurposing\n"
            "[dim]NVIDIA NIM + faster-whisper + FFmpeg[/dim]",
            border_style="cyan"
        ))
    else:
        print("=" * 50)
        print("  CLIPPER — AI Video Repurposing Tool")
        print("  NVIDIA NIM + faster-whisper + FFmpeg")
        print("=" * 50)


def print_results(clips_info: list):
    if HAS_RICH:
        table = Table(title="Generated Clips", show_header=True)
        table.add_column("#",        style="cyan",  width=4)
        table.add_column("Score",    style="green", width=7)
        table.add_column("Duration", width=10)
        table.add_column("Title",    width=40)
        table.add_column("File",     width=30)

        for i, (clip, path) in enumerate(clips_info, 1):
            dur = f"{clip.duration:.0f}s"
            fname = os.path.basename(path) if path else "FAILED"
            table.add_row(str(i), str(clip.score), dur, clip.title[:38], fname)

        console.print(table)
    else:
        print("\nGenerated Clips:")
        for i, (clip, path) in enumerate(clips_info, 1):
            fname = os.path.basename(path) if path else "FAILED"
            print(f"  [{i}] Score={clip.score} | {clip.duration:.0f}s | {clip.title[:40]} | {fname}")


def run(url: str = None,
        file_path: str = None,
        num_clips: int = 8,
        platform: str = "all",
        add_captions: bool = True,
        add_blur_bg:  bool = True,
        add_music:    bool = False,
        min_duration: float = 20.0,
        max_duration: float = 90.0,
        language: str = None):
    """
    Full pipeline: Download → Transcribe → Detect → Cut → Caption → Trending Music

    Args:
        url:          YouTube (or any) video URL
        file_path:    Local video file (alternative to url)
        num_clips:    How many clips to generate
        platform:     Target: "tiktok" | "reels" | "shorts" | "all"
        add_captions: Burn word-level captions
        add_blur_bg:  Add blurred background (9:16 vertical)
        add_music:    Add emotion-based trending TikTok background music
        min_duration: Minimum clip length in seconds
        max_duration: Maximum clip length in seconds
        language:     Force language (None = auto-detect)
    """
    start_time = time.time()
    print_banner()

    # ── Step 1: Get the audio (Stream Sniper) or video ───────────────────────
    downloader  = Downloader()
    source_path = file_path
    is_stream_sniper = False

    if url and not file_path:
        print("\n[1/5] Stream Sniper Mode: Downloading Audio Only...")
        source_path = downloader.download_audio_only(url)
        if not source_path:
            print("[ERROR] Audio download failed. Exiting.")
            return []
        is_stream_sniper = True

    if not source_path or not os.path.exists(source_path):
        print("[ERROR] No media file found. Provide --url or --file")
        return []

    print(f"[1/5] Source ready: {os.path.basename(source_path)}")

    # ── Step 2: Get video info (if local file) ───────────────────────────────
    cutter = ClipCutter()
    video_duration = 0
    if not is_stream_sniper:
        info = cutter.get_video_info(source_path)
        video_duration = info.get("duration", 0)
        print(f"      Duration: {video_duration:.0f}s | "
              f"{info.get('width')}x{info.get('height')} | "
              f"{info.get('fps', 0):.1f}fps")
    else:
        # We don't have video duration yet, whisper will tell us the audio duration
        pass

    # ── Step 3: Transcribe ───────────────────────────────────────────────────
    print("\n[2/5] Transcribing (faster-whisper, local)...")
    transcriber = Transcriber()
    transcript  = transcriber.transcribe(source_path, language=language)

    if not transcript:
        print("[ERROR] Transcription failed. Exiting.")
        return []
        
    if is_stream_sniper:
        video_duration = transcript.segments[-1].end if transcript.segments else 0

    print(f"      {len(transcript.words)} words | "
          f"{len(transcript.segments)} segments | "
          f"lang={transcript.language}")

    # ── Step 4: Find viral moments ───────────────────────────────────────────
    print(f"\n[3/5] Finding top {num_clips} viral moments (NVIDIA NIM)...")
    detector = ViralDetector()
    clips    = detector.find_clips(
        transcript_text = transcript.text,
        segments        = transcript.segments,
        video_duration  = video_duration,
        num_clips       = num_clips,
        min_duration    = min_duration,
        max_duration    = max_duration,
        target_platform = platform,
    )

    if not clips:
        print("[ERROR] No clips found. Check NVIDIA API key.")
        return []

    # ── Step 5 & 6: Snipe, Cut & Caption ─────────────────────────────────────
    print(f"\n[4/5 & 5/5] Processing {len(clips)} clips...")
    caption_burner = CaptionBurner()
    cache_dir = Path(os.getenv("CACHE_DIR", "cache"))
    cache_dir.mkdir(exist_ok=True)
    
    final_clips = []
    
    for i, clip in enumerate(clips, 1):
        print(f"\n--- Clip {i}/{len(clips)}: Score {clip.score} ---")
        
        if is_stream_sniper:
            # 1. Download specific section
            chunk_path = str(cache_dir / f"chunk_{i}.mp4")
            downloaded = downloader.download_video_section(url, clip.start, clip.end, chunk_path)
            
            if not downloaded:
                continue
                
            # 2. Reformat to 9:16 (pre-cut)
            rendered = cutter.cut_and_reformat(
                source_path=downloaded, start=0, end=clip.end-clip.start,
                title=clip.title, score=clip.score, add_blur_bg=add_blur_bg,
                is_pre_cut=True
            )
        else:
            # Traditional cut from local file
            rendered = cutter.cut_and_reformat(
                source_path=source_path, start=clip.start, end=clip.end,
                title=clip.title, score=clip.score, add_blur_bg=add_blur_bg,
                is_pre_cut=False
            )
            
        if not rendered:
            continue
            
        final_path = rendered.path

        if add_captions and transcript:
            # Build word list for this clip (filter + shift timestamps)
            clip_words = [
                {"text": w.text, "start": w.start, "end": w.end}
                for w in transcript.words
            ]

            # Burn captions using new direct JSON path (LLM keyword detection)
            captioned = caption_burner.burn_from_words(
                video_path=rendered.path,
                words=clip_words,
                offset_sec=clip.start,
                duration_sec=clip.end - clip.start,
            )
            final_path = captioned or rendered.path
            
        # Optional: Mix emotion-based trending TikTok background music
        if add_music and final_path:
            from clipper.core.music_mixer import MusicMixer
            music_out = str(Path(final_path).with_name(f"{Path(final_path).stem}_music.mp4"))
            mixer = MusicMixer()
            mixed = mixer.mix_by_clip(final_path, music_out, clip)
            if mixed:
                final_path = mixed

        final_clips.append(final_path)

    # ── Summary ──────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"  DONE in {elapsed:.0f}s — {len(final_clips)} clips generated")
    print(f"  Output: {os.path.abspath(cutter.output_dir)}")
    print(f"{'=' * 60}")

    clips_with_paths = list(zip(clips[:len(final_clips)], final_clips))
    print_results(clips_with_paths)

    return final_clips


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CLIPPER — AI Video Repurposing (OpusClip Alternative)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--url",        type=str,  help="YouTube or video URL")
    parser.add_argument("--file",       type=str,  help="Local video file path")
    parser.add_argument("--clips",      type=int,  default=8, help="Number of clips (default: 8)")
    parser.add_argument("--platform",   type=str,  default="all",
                        choices=["tiktok","reels","shorts","all"],
                        help="Target platform (default: all)")
    parser.add_argument("--min",        type=float, default=20.0, help="Min clip duration (default: 20)")
    parser.add_argument("--max",        type=float, default=90.0, help="Max clip duration (default: 90)")
    parser.add_argument("--lang",       type=str,  default=None, help="Force language (e.g. en)")
    parser.add_argument("--no-captions",action="store_true", help="Skip caption burning")
    parser.add_argument("--no-blur-bg", action="store_true", help="Skip blur background (plain crop)")
    parser.add_argument("--music",      action="store_true", help="Add emotion-based trending TikTok background music")

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.print_help()
        print("\nExample:")
        print('  python main.py --url "https://youtube.com/watch?v=dQw4w9WgXcQ" --clips 5')
        sys.exit(1)

    run(
        url          = args.url,
        file_path    = args.file,
        num_clips    = args.clips,
        platform     = args.platform,
        add_captions = not args.no_captions,
        add_blur_bg  = not args.no_blur_bg,
        add_music    = args.music,
        min_duration = args.min,
        max_duration = args.max,
        language     = args.lang,
    )


if __name__ == "__main__":
    main()
