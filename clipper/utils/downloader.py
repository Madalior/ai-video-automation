"""
Downloader — yt-dlp wrapper
Moved from: flowchart/common/youtube_footage.py
Downloads any video by URL, detects copyright from title/description.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(os.getenv("CACHE_DIR", "cache"))


# ── Copyright detection phrases ─────────────────────────────────────────────

SAFE_PHRASES = [
    "no copyright", "copyright free", "copyright-free", "royalty free",
    "royalty-free", "free to use", "free for commercial use", "cc0",
    "creative commons", "public domain", "free footage", "free stock",
    "you can use this", "feel free to use", "free background",
]

RISKY_PHRASES = [
    "all rights reserved", "licensed to youtube by", "provided to youtube by",
    "sony music", "universal music", "warner music", "official video",
    "official music video", "℗", "© 20",
]


def classify_copyright(title: str, description: str,
                       channel: str, license_field: str = "") -> dict:
    """
    Analyze title + description + channel to determine if video is safe to use.
    Returns: { safe: bool|None, confidence: str, reason: str }
    """
    text = f"{title} {description} {channel} {license_field}".lower()

    safe_found  = [p for p in SAFE_PHRASES  if p in text]
    risky_found = [p for p in RISKY_PHRASES if p in text]

    if "creative commons" in license_field.lower():
        return {"safe": True,  "confidence": "high",
                "reason": f"YouTube CC license field detected"}

    if risky_found and not safe_found:
        return {"safe": False, "confidence": "high",
                "reason": f"Risky: {risky_found[:2]}"}

    strong = [p for p in safe_found if p in [
        "no copyright", "cc0", "public domain", "royalty free",
        "free to use", "creative commons", "copyright free"
    ]]
    if strong:
        return {"safe": True, "confidence": "high",
                "reason": f"Safe signals: {strong[:2]}"}

    if safe_found:
        return {"safe": True, "confidence": "medium",
                "reason": f"Safe phrases: {safe_found[:2]}"}

    return {"safe": None, "confidence": "low",
            "reason": "No copyright signals found"}


class Downloader:
    """
    Download videos from any URL using yt-dlp.
    Supports copyright pre-check on YouTube videos.
    """

    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or CACHE_DIR / "downloads")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._check_ytdlp()

    def _check_ytdlp(self):
        try:
            r = subprocess.run(["yt-dlp", "--version"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                print(f"[DOWNLOADER] yt-dlp v{r.stdout.strip()} ready")
            else:
                print("[DOWNLOADER] yt-dlp not found — run: pip install yt-dlp")
        except Exception:
            print("[DOWNLOADER] yt-dlp not found — run: pip install yt-dlp")

    def get_info(self, url: str) -> Optional[dict]:
        """Fetch video metadata without downloading."""
        try:
            r = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download",
                 "--no-warnings", "--quiet", url],
                capture_output=True, text=True, timeout=30
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout.strip().split("\n")[0])
                return {
                    "id":          data.get("id", ""),
                    "title":       data.get("title", ""),
                    "description": (data.get("description") or "")[:1000],
                    "channel":     data.get("uploader", ""),
                    "duration":    data.get("duration", 0),
                    "url":         url,
                    "license":     data.get("license", ""),
                    "tags":        data.get("tags", []),
                }
        except Exception as e:
            print(f"[DOWNLOADER] get_info error: {e}")
        return None

    def check_copyright(self, url: str) -> dict:
        """
        Check if a YouTube video is safe to use before downloading.
        """
        info = self.get_info(url)
        if not info:
            return {"safe": None, "confidence": "low", "reason": "Could not fetch metadata"}

        result = classify_copyright(
            title       = info.get("title", ""),
            description = info.get("description", ""),
            channel     = info.get("channel", ""),
            license_field = info.get("license", ""),
        )
        result["title"]    = info.get("title", "")
        result["duration"] = info.get("duration", 0)
        return result

    def download(self, url: str, output_path: str = None,
                 max_height: int = 1080,
                 check_copyright: bool = True) -> Optional[str]:
        """
        Download a video from URL.

        Args:
            url: Video URL (YouTube or direct)
            output_path: Where to save (auto if None)
            max_height: Max video resolution (720 or 1080)
            check_copyright: Warn if not safe to use

        Returns:
            Local file path or None on failure
        """
        if check_copyright and "youtube.com" in url or "youtu.be" in url:
            check = self.check_copyright(url)
            if check["safe"] is False:
                print(f"[DOWNLOADER] [WARN] Copyright risk detected!")
                print(f"[DOWNLOADER]   Reason: {check['reason']}")
                print(f"[DOWNLOADER]   Title:  {check.get('title', '')}")
                print(f"[DOWNLOADER]   Proceeding anyway — use at your own risk.")
            elif check["safe"] is True:
                print(f"[DOWNLOADER] [OK] Copyright safe: {check['reason']}")
            else:
                print(f"[DOWNLOADER] [UNCRT] No copyright info — use with caution")

        if output_path is None:
            info = self.get_info(url)
            vid_id = info["id"] if info else "video"
            output_path = str(self.cache_dir / f"{vid_id}.mp4")

        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"[DOWNLOADER] [CACHE] {os.path.basename(output_path)}")
            return output_path

        print(f"[DOWNLOADER] Downloading: {url[:80]}")

        ffmpeg_ok = self._check_ffmpeg()
        cmd = [
            "yt-dlp", url,
            "-f", f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", output_path,
            "--no-warnings", "--quiet",
        ]
        if not ffmpeg_ok:
            cmd = ["yt-dlp", url,
                   "-f", f"best[height<={max_height}][ext=mp4]/best",
                   "-o", output_path,
                   "--no-warnings", "--quiet",
                   "--max-filesize", "500M"]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                size = os.path.getsize(output_path) / (1024*1024)
                print(f"[DOWNLOADER] Done: {os.path.basename(output_path)} ({size:.1f} MB)")
                return output_path
            print(f"[DOWNLOADER] Failed: {(r.stderr or r.stdout)[:200]}")
        except subprocess.TimeoutExpired:
            print("[DOWNLOADER] Timeout")
        except Exception as e:
            print(f"[DOWNLOADER] Error: {e}")
        return None

    def download_audio_only(self, url: str, output_path: str = None) -> Optional[str]:
        """
        Download only the audio of a video (extremely fast, small file size).
        """
        if output_path is None:
            info = self.get_info(url)
            vid_id = info["id"] if info else "audio"
            output_path = str(self.cache_dir / f"{vid_id}.m4a")

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"[DOWNLOADER] [CACHE] {os.path.basename(output_path)}")
            return output_path

        print(f"[DOWNLOADER] Downloading Audio Only: {url[:80]}")

        cmd = [
            "yt-dlp", url,
            "-f", "ba[ext=m4a]/ba",
            "-o", output_path,
            "--no-warnings", "--quiet",
        ]

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                size = os.path.getsize(output_path) / (1024*1024)
                print(f"[DOWNLOADER] Audio Done: {os.path.basename(output_path)} ({size:.1f} MB)")
                return output_path
            print(f"[DOWNLOADER] Failed: {(r.stderr or r.stdout)[:200]}")
        except subprocess.TimeoutExpired:
            print("[DOWNLOADER] Timeout")
        except Exception as e:
            print(f"[DOWNLOADER] Error: {e}")
        return None

    def download_video_section(self, url: str, start_sec: float, end_sec: float, output_path: str) -> Optional[str]:
        """
        Download a specific time range of a video directly from YouTube.
        Requires yt-dlp to use ffmpeg under the hood.
        """
        print(f"[DOWNLOADER] Sniping video section: {start_sec}s to {end_sec}s")

        # Format as HH:MM:SS
        start_str = f"*{int(start_sec//3600):02d}:{int((start_sec%3600)//60):02d}:{int(start_sec%60):02d}"
        end_str = f"{int(end_sec//3600):02d}:{int((end_sec%3600)//60):02d}:{int(end_sec%60):02d}"
        section = f"{start_str}-{end_str}"

        cmd = [
            "yt-dlp",
            "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b",
            "--download-sections", section,
            "--force-keyframes-at-cuts",
            "--merge-output-format", "mp4",
            "-o", output_path,
            url,
            "--no-warnings", "--quiet",
        ]

        try:
            # Short timeout for network ffmpeg slicing because it often hangs
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                size = os.path.getsize(output_path) / (1024*1024)
                print(f"[DOWNLOADER] Sniped chunk: {os.path.basename(output_path)} ({size:.1f} MB)")
                return output_path
            print(f"[DOWNLOADER] Snipe Failed: {(r.stderr or r.stdout)[:200]}")
        except subprocess.TimeoutExpired:
            print("[DOWNLOADER] Snipe network timeout. Falling back to local cut...")
        except Exception as e:
            print(f"[DOWNLOADER] Snipe Error: {e}")
            
        print("[DOWNLOADER] Falling back to downloading full video and cutting locally...")
        full_vid = str(self.cache_dir / "temp_full_vid.mp4")
        if not os.path.exists(full_vid):
            full_cmd = [
                "yt-dlp", "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b",
                "--merge-output-format", "mp4", "-o", full_vid, url, "--quiet"
            ]
            subprocess.run(full_cmd, timeout=300)
            
        if os.path.exists(full_vid):
            print("[DOWNLOADER] Cutting locally with ffmpeg...")
            cut_cmd = [
                "ffmpeg", "-y", "-i", full_vid,
                "-ss", str(start_sec), "-to", str(end_sec),
                "-c:v", "copy", "-c:a", "copy", output_path
            ]
            subprocess.run(cut_cmd, capture_output=True, timeout=60)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path
                
        return None

    def _check_ffmpeg(self) -> bool:
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False
