"""
Stream Monitor
==============
Automated 24/7 background monitor for YouTube and Twitch creators.
Detects when an influencer finishes a livestream, extracts the completed VOD,
and queues it for autonomous clipping with Going Merry.

Zero-cost architecture: Uses fast yt-dlp flat-playlist queries (no YouTube Data API quota used).
"""

import os
import sys
import re
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class StreamMonitor:
    """
    Monitors creators across YouTube and Twitch for newly ended livestreams.
    """

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                print(f"[STREAM MONITOR] yt-dlp v{r.stdout.strip()} ready")
        except Exception:
            print("[STREAM MONITOR] [WARN] yt-dlp check skipped or not found.")

    @staticmethod
    def normalize_channel_url(raw_url: str) -> Dict[str, str]:
        """
        Takes any YouTube or Twitch link (watch URL, channel handle, or stream link)
        and normalizes it into a direct streams / VOD archive URL.
        
        Returns:
            {
                "platform": "youtube" | "twitch" | "kick" | "unknown",
                "channel_url": normalized streams URL,
                "handle": creator handle/name
            }
        """
        url = raw_url.strip()

        # YouTube handling
        if "youtube.com" in url or "youtu.be" in url:
            # Handle formats like:
            # https://www.youtube.com/@IShowSpeed
            # https://www.youtube.com/@IShowSpeed/live
            # https://www.youtube.com/watch?v=...
            handle_match = re.search(r"@([a-zA-Z0-9_\-]+)", url)
            if handle_match:
                handle = f"@{handle_match.group(1)}"
                return {
                    "platform": "youtube",
                    "channel_url": f"https://www.youtube.com/{handle}/streams",
                    "handle": handle
                }
            
            # If standard watch URL, yt-dlp can resolve the channel uploader
            return {
                "platform": "youtube",
                "channel_url": url,
                "handle": ""
            }

        # Twitch handling
        elif "twitch.tv" in url:
            match = re.search(r"twitch\.tv/([a-zA-Z0-9_]+)", url)
            if match:
                channel = match.group(1).lower()
                # Skip reserved paths
                if channel not in ["directory", "videos", "downloads", "settings"]:
                    return {
                        "platform": "twitch",
                        "channel_url": f"https://www.twitch.tv/{channel}/videos?filter=archives",
                        "handle": channel
                    }

        return {
            "platform": "unknown",
            "channel_url": url,
            "handle": ""
        }

    def resolve_channel_metadata(self, url: str) -> Dict[str, str]:
        """
        Queries yt-dlp for channel title and handle if not readily obvious from URL.
        """
        info = self.normalize_channel_url(url)
        try:
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--playlist-end", "1",
                "--dump-json",
                info["channel_url"]
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                first_line = r.stdout.strip().split("\n")[0]
                data = json.loads(first_line)
                
                channel_title = (
                    data.get("playlist_uploader") or 
                    data.get("playlist_channel") or 
                    data.get("uploader") or 
                    data.get("channel") or
                    info.get("handle") or
                    "Creator"
                )
                handle = data.get("playlist_uploader_id") or info.get("handle") or channel_title
                
                return {
                    "platform": info["platform"],
                    "channel_name": channel_title,
                    "channel_handle": handle,
                    "channel_url": info["channel_url"]
                }
        except Exception as e:
            print(f"[STREAM MONITOR] [WARN] Metadata resolution error for {url}: {e}")

        return {
            "platform": info["platform"],
            "channel_name": info.get("handle") or "Creator",
            "channel_handle": info.get("handle") or "",
            "channel_url": info["channel_url"]
        }

    def fetch_completed_streams(self, channel_url: str, limit: int = 5) -> List[Dict]:
        """
        Scans a creator's stream tab and returns list of COMPLETED livestreams.
        
        Filters for:
        - YouTube: `was_live: True` or `live_status == 'was_live'`
        - Twitch: Past Broadcasts VODs
        """
        completed = []
        try:
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--playlist-end", str(limit),
                "--dump-json",
                channel_url
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if r.returncode != 0:
                print(f"[STREAM MONITOR] [ERROR] yt-dlp error querying {channel_url}:\n{r.stderr[:200]}")
                return []

            lines = r.stdout.strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    stream_id = data.get("id")
                    title = data.get("title", "Untitled Stream")
                    duration = data.get("duration") or 0.0
                    webpage_url = data.get("url") or data.get("webpage_url")
                    
                    if not webpage_url and stream_id:
                        if "twitch.tv" in channel_url:
                            webpage_url = f"https://www.twitch.tv/videos/{stream_id}"
                        else:
                            webpage_url = f"https://www.youtube.com/watch?v={stream_id}"

                    # Detection checks:
                    # 1. YouTube was_live flag
                    # 2. Twitch VOD (has TwitchVod extractor or /videos/)
                    is_ended_stream = False
                    
                    if data.get("was_live") is True or data.get("live_status") == "was_live":
                        is_ended_stream = True
                    elif "twitch" in channel_url and data.get("ie_key") == "TwitchVod":
                        is_ended_stream = True
                    elif duration and duration > 300 and data.get("is_live") is not True:
                        # Stream archive with valid duration that is not currently live
                        is_ended_stream = True

                    if is_ended_stream and stream_id:
                        completed.append({
                            "stream_id": stream_id,
                            "title": title,
                            "url": webpage_url,
                            "duration": float(duration),
                            "thumbnails": data.get("thumbnails") or [],
                        })
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            print(f"[STREAM MONITOR] [ERROR] Failed to fetch streams for {channel_url}: {e}")

        return completed

    def check_and_enqueue_streams(self, db_session) -> List[Dict]:
        """
        Iterates over all active MonitoredInfluencer records in the DB,
        finds newly finished livestreams, and registers them in ProcessedStream.
        
        Returns:
            List of newly discovered stream task dicts ready for pipeline execution.
        """
        from web_app.models import MonitoredInfluencer, ProcessedStream

        active_influencers = db_session.query(MonitoredInfluencer).filter_by(is_active=True).all()
        print(f"[STREAM MONITOR] [SCAN] Checking {len(active_influencers)} followed influencers...")

        new_jobs = []

        for influencer in active_influencers:
            print(f"[STREAM MONITOR] [SCAN] Checking '{influencer.channel_name}' ({influencer.channel_url})...")
            streams = self.fetch_completed_streams(influencer.channel_url, limit=3)

            for s in streams:
                stream_id = s["stream_id"]

                # Check if we already processed or queued this stream
                existing = db_session.query(ProcessedStream).filter_by(
                    influencer_id=influencer.id,
                    stream_id=stream_id
                ).first()

                if not existing:
                    print(f"[STREAM MONITOR] [NEW STREAM] Detected: '{s['title']}' (ID: {stream_id})")
                    
                    # Create DB record
                    new_stream_record = ProcessedStream(
                        influencer_id=influencer.id,
                        stream_id=stream_id,
                        stream_title=s["title"],
                        stream_url=s["url"],
                        duration=s["duration"],
                        status="queued"
                    )
                    db_session.add(new_stream_record)
                    influencer.last_stream_id = stream_id
                    influencer.last_checked_at = datetime.utcnow()
                    db_session.commit()

                    job_payload = {
                        "influencer_id": influencer.id,
                        "user_id": influencer.user_id,
                        "channel_name": influencer.channel_name,
                        "stream_id": stream_id,
                        "stream_url": s["url"],
                        "stream_title": s["title"],
                        "num_clips": influencer.num_clips,
                        "target_platform": influencer.target_platform,
                        "auto_upload": influencer.auto_upload
                    }
                    new_jobs.append(job_payload)

                    # Enqueue to QueueManager (Flowchart: MONITOR --> REDIS)
                    try:
                        from clipper.core.queue_manager import queue_manager
                        queue_manager.enqueue("stream_job", job_payload)
                    except Exception as q_err:
                        print(f"[STREAM MONITOR] [WARN] Could not enqueue to QueueManager: {q_err}")

            influencer.last_checked_at = datetime.utcnow()

        db_session.commit()
        print(f"[STREAM MONITOR] [DONE] Scan complete. {len(new_jobs)} new stream(s) queued.")
        return new_jobs

    def run_monitor_daemon(self, interval_seconds: int = 1800, stop_event=None):
        """
        Runs continuous 24/7 scanning daemon.
        Checks for completed streams every interval_seconds (default: 30 minutes / 1800s).
        """
        import time
        from web_app.app import app, db
        print(f"\n[STREAM MONITOR] 🛰️  Starting 24/7 Stream Monitor Daemon (Interval: {interval_seconds}s / {interval_seconds/60:.1f}m)...")
        print("[STREAM MONITOR] Press Ctrl+C to stop.\n")

        while not (stop_event and stop_event.is_set()):
            try:
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                print(f"\n[STREAM MONITOR] [{now_str}] 🔎 Running scheduled stream check...")
                with app.app_context():
                    new_jobs = self.check_and_enqueue_streams(db.session)
                    if new_jobs:
                        print(f"[STREAM MONITOR] 🚀 Successfully queued {len(new_jobs)} new stream(s) to Task Broker.")
                    else:
                        print("[STREAM MONITOR] 💤 No newly finished streams detected.")
            except Exception as e:
                print(f"[STREAM MONITOR] [ERROR] Daemon cycle encountered an error: {e}")

            for _ in range(int(interval_seconds)):
                if stop_event and stop_event.is_set():
                    break
                time.sleep(1)

        print("[STREAM MONITOR] 🛑 Stream monitor daemon stopped cleanly.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    monitor = StreamMonitor()
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/@IShowSpeed"
    
    print(f"\n--- Testing StreamMonitor on: {target_url} ---")
    meta = monitor.resolve_channel_metadata(target_url)
    print("Resolved Metadata:", json.dumps(meta, indent=2))
    
    print("\nFetching latest completed streams...")
    completed = monitor.fetch_completed_streams(meta["channel_url"], limit=3)
    for i, c in enumerate(completed, 1):
        print(f"[{i}] ID: {c['stream_id']} | Title: {c['title']} | Duration: {c['duration']}s | URL: {c['url']}")
