"""
Proxy-Aware Multi-Account Social Media Publisher
=================================================
Wraps PostizManager to route API calls through a SOCKS5 proxy
(Tailscale exit node -> Android mobile IP) while serving video
files directly from the cloud VPS.

Key design:
  - Only API calls (auth, posting JSON ~2KB) go through the phone's mobile IP
  - Video files are served from the cloud's public IP (platforms pull directly)
  - IP rotation via Airplane Mode toggle between account batches
  - Staggered posting with human-like random delays

Usage:
  publisher = ProxyPublisher(
      postiz_url="https://postiz.sarkaricalc.me",
      socks5_proxy="socks5://127.0.0.1:1080"  # Tailscale SOCKS5
  )
  publisher.publish_batch(clips, accounts, stagger_seconds=(30, 90))
"""

import os
import sys
import json
import time
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from clipper.core.postiz_manager import PostizManager


@dataclass
class AccountConfig:
    """Configuration for a single social media account."""
    name: str
    platform: str  # youtube, tiktok, instagram
    postiz_integration_id: str
    # Optional per-account proxy override
    proxy_override: Optional[str] = None


@dataclass
class PublishJob:
    """A single video publish job."""
    video_path: str
    title: str
    caption: str
    hashtags: List[str] = field(default_factory=list)
    accounts: List[AccountConfig] = field(default_factory=list)
    schedule_time: Optional[str] = None


@dataclass
class PublishResult:
    """Result of a single publish attempt."""
    account_name: str
    platform: str
    success: bool
    message: str
    ip_used: str = ""
    payload_bytes: int = 0
    timestamp: str = ""


class ProxyPublisher:
    """
    Multi-account publisher that routes API calls through mobile IP
    via SOCKS5 proxy (Tailscale exit node).
    """

    def __init__(
        self,
        postiz_url: Optional[str] = None,
        postiz_api_key: Optional[str] = None,
        socks5_proxy: Optional[str] = None,
        batch_size: int = 5,
        stagger_range: Tuple[int, int] = (30, 90),
        rotate_ip_every: int = 5
    ):
        """
        Args:
            postiz_url: Postiz API base URL
            postiz_api_key: Postiz API key
            socks5_proxy: SOCKS5 proxy URL (e.g., socks5://127.0.0.1:1080)
            batch_size: Number of accounts to post per batch before IP rotation
            stagger_range: (min, max) seconds between posts for human-like delay
            rotate_ip_every: Rotate IP every N posts
        """
        self.postiz_url = postiz_url or os.getenv("POSTIZ_API_URL", "https://postiz.sarkaricalc.me")
        self.postiz_api_key = postiz_api_key or os.getenv("POSTIZ_API_KEY", "")
        self.socks5_proxy = socks5_proxy or os.getenv("POSTIZ_SOCKS5_PROXY", "")
        self.batch_size = batch_size
        self.stagger_range = stagger_range
        self.rotate_ip_every = rotate_ip_every
        self.results: List[PublishResult] = []

        # Create proxy-aware PostizManager
        self.manager = PostizManager(
            api_url=self.postiz_url,
            api_key=self.postiz_api_key,
            proxy_url=self.socks5_proxy
        )

    def get_current_ip(self) -> Dict[str, str]:
        """
        Check current outbound IP and ASN through the proxy.
        Returns: {"ip": "x.x.x.x", "org": "AS55836 Reliance Jio", "city": "Mumbai"}
        """
        import requests
        try:
            proxies = {"http": self.socks5_proxy, "https": self.socks5_proxy} if self.socks5_proxy else None
            resp = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "ip": data.get("ip", "unknown"),
                    "org": data.get("org", "unknown"),
                    "city": data.get("city", "unknown"),
                    "country": data.get("country", "unknown")
                }
        except Exception as e:
            print(f"[PROXY] [WARN] Could not check IP: {e}")
        return {"ip": "unknown", "org": "unknown", "city": "unknown", "country": "unknown"}

    def measure_payload_size(self, job: PublishJob) -> int:
        """
        Calculate the size of the API payload (JSON only, not video).
        This proves mobile data usage is minimal (~2KB per post).
        """
        # Build a representative payload
        payload = self.manager.build_post_payload(
            media_id="test_media_id",
            title=job.title,
            caption=job.caption,
            hashtags=job.hashtags,
            integrations=[{"id": "test", "identifier": "tiktok"}],
            target_platforms=["tiktok"],
            schedule_time=job.schedule_time
        )
        payload_json = json.dumps(payload)
        size = len(payload_json.encode("utf-8"))
        print(f"[PROXY] API payload size: {size} bytes ({size/1024:.1f} KB)")
        return size

    def rotate_ip(self):
        """
        Trigger IP rotation by toggling Airplane Mode on the Android phone.
        Method 1: ADB over Tailscale (if phone has USB debugging enabled)
        Method 2: Just log a reminder for manual toggle
        """
        print("\n[PROXY] === IP ROTATION ===")
        ip_before = self.get_current_ip()
        print(f"[PROXY] Current IP: {ip_before['ip']} ({ip_before['org']})")

        # Try ADB method first
        try:
            # ADB airplane mode toggle (requires USB debugging + ADB over network)
            adb_ip = os.getenv("ADB_PHONE_IP", "")
            if adb_ip:
                subprocess.run(
                    ["adb", "-s", f"{adb_ip}:5555", "shell",
                     "settings", "put", "global", "airplane_mode_on", "1"],
                    capture_output=True, timeout=5
                )
                time.sleep(3)
                subprocess.run(
                    ["adb", "-s", f"{adb_ip}:5555", "shell",
                     "settings", "put", "global", "airplane_mode_on", "0"],
                    capture_output=True, timeout=5
                )
                time.sleep(8)  # Wait for cellular reconnect
                ip_after = self.get_current_ip()
                print(f"[PROXY] New IP: {ip_after['ip']} ({ip_after['org']})")
                if ip_after['ip'] != ip_before['ip']:
                    print("[PROXY] [OK] IP successfully rotated!")
                    return True
                else:
                    print("[PROXY] [WARN] IP did not change after ADB toggle")
            else:
                print("[PROXY] [INFO] ADB not configured. Manual IP rotation required.")
                print("[PROXY] [INFO] Toggle Airplane Mode on your phone NOW, then wait 10 seconds.")

        except Exception as e:
            print(f"[PROXY] [WARN] ADB rotation failed: {e}")
            print("[PROXY] [INFO] Please manually toggle Airplane Mode on your phone.")

        return False

    def publish_single(self, job: PublishJob, account: AccountConfig,
                       simulate: bool = False) -> PublishResult:
        """Publish a single clip to a single account."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        ip_info = self.get_current_ip()

        print(f"\n[PROXY] Publishing to {account.name} ({account.platform})")
        print(f"[PROXY] Via IP: {ip_info['ip']} ({ip_info['org']})")

        # Use account-specific proxy if set, otherwise default
        if account.proxy_override:
            manager = PostizManager(
                api_url=self.postiz_url,
                api_key=self.postiz_api_key,
                proxy_url=account.proxy_override
            )
        else:
            manager = self.manager

        try:
            result = manager.publish_clip(
                video_path=job.video_path,
                title=job.title,
                caption=job.caption,
                hashtags=job.hashtags,
                target_platform=account.platform,
                schedule_time=job.schedule_time,
                simulate=simulate
            )

            payload_size = self.measure_payload_size(job)

            return PublishResult(
                account_name=account.name,
                platform=account.platform,
                success=result.get("success", False),
                message=result.get("message", result.get("error", "Unknown")),
                ip_used=f"{ip_info['ip']} ({ip_info['org']})",
                payload_bytes=payload_size,
                timestamp=timestamp
            )

        except Exception as e:
            return PublishResult(
                account_name=account.name,
                platform=account.platform,
                success=False,
                message=str(e),
                ip_used=f"{ip_info['ip']} ({ip_info['org']})",
                timestamp=timestamp
            )

    def publish_batch(self, job: PublishJob, simulate: bool = False) -> List[PublishResult]:
        """
        Publish a clip to multiple accounts with:
        - Staggered delays (human-like)
        - IP rotation every N posts
        - Batch processing (3-5 accounts per batch)
        """
        accounts = job.accounts
        total = len(accounts)
        self.results = []

        print(f"\n{'='*60}")
        print(f" PROXY PUBLISHER - Batch Publishing")
        print(f" Clip: {os.path.basename(job.video_path)}")
        print(f" Accounts: {total}")
        print(f" Batch size: {self.batch_size}")
        print(f" Stagger: {self.stagger_range[0]}-{self.stagger_range[1]}s")
        print(f" IP rotation every: {self.rotate_ip_every} posts")
        print(f" Mode: {'SIMULATE' if simulate else 'LIVE'}")
        print(f"{'='*60}")

        # Check initial IP
        ip_info = self.get_current_ip()
        print(f"\n[PROXY] Starting IP: {ip_info['ip']} ({ip_info['org']})")

        # Warn if using datacenter IP
        org_lower = ip_info['org'].lower()
        datacenter_keywords = ['digitalocean', 'amazon', 'google', 'microsoft',
                                'oracle', 'linode', 'vultr', 'hetzner', 'ovh']
        if any(kw in org_lower for kw in datacenter_keywords):
            print("[PROXY] [WARN] DATACENTER IP DETECTED! Social platforms may flag this.")
            print("[PROXY] [WARN] Ensure Tailscale exit node is active on your phone.")
            if not simulate:
                print("[PROXY] [WARN] Continuing anyway in 5 seconds...")
                time.sleep(5)

        for i, account in enumerate(accounts):
            # IP rotation check
            if i > 0 and i % self.rotate_ip_every == 0:
                print(f"\n[PROXY] Rotating IP after {i} posts...")
                self.rotate_ip()

            # Human-like delay
            if i > 0:
                delay = random.randint(self.stagger_range[0], self.stagger_range[1])
                print(f"[PROXY] Waiting {delay}s before next post (human-like delay)...")
                if not simulate:
                    time.sleep(delay)

            # Publish
            result = self.publish_single(job, account, simulate=simulate)
            self.results.append(result)

            status = "[OK]" if result.success else "[FAIL]"
            print(f"[PROXY] {status} {account.name} ({account.platform}) - "
                  f"Payload: {result.payload_bytes}B - IP: {result.ip_used}")

        # Summary
        self._print_summary()
        return self.results

    def _print_summary(self):
        """Print batch results summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        total_bytes = sum(r.payload_bytes for r in self.results)

        print(f"\n{'='*60}")
        print(f" PUBLISH BATCH COMPLETE")
        print(f" Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f" Total API data sent: {total_bytes} bytes ({total_bytes/1024:.1f} KB)")
        print(f" Estimated mobile data: ~{total_bytes/1024:.1f} KB (NOT {total * 15}MB!)")
        print(f"{'='*60}")

        if failed > 0:
            print("\n[PROXY] Failed accounts:")
            for r in self.results:
                if not r.success:
                    print(f"  - {r.account_name}: {r.message}")


# ── CLI ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Proxy-Aware Multi-Account Publisher")
    parser.add_argument("--video", type=str, help="Path to video file")
    parser.add_argument("--title", type=str, default="Check this out!", help="Video title")
    parser.add_argument("--caption", type=str, default="", help="Caption text")
    parser.add_argument("--proxy", type=str, default="", help="SOCKS5 proxy URL")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode")
    parser.add_argument("--check-ip", action="store_true", help="Just check current IP")
    parser.add_argument("--payload-size", action="store_true", help="Measure API payload size")
    args = parser.parse_args()

    publisher = ProxyPublisher(socks5_proxy=args.proxy)

    if args.check_ip:
        print("\n[PROXY] Checking IP through proxy...")
        ip = publisher.get_current_ip()
        print(f"  IP:      {ip['ip']}")
        print(f"  ASN/Org: {ip['org']}")
        print(f"  City:    {ip['city']}")
        print(f"  Country: {ip['country']}")

    elif args.payload_size:
        job = PublishJob(
            video_path=args.video or "dummy.mp4",
            title=args.title,
            caption=args.caption or "Testing payload size measurement #viral #trending",
            hashtags=["viral", "trending", "fyp", "shorts", "reels"],
            accounts=[AccountConfig("test", "tiktok", "test_id")]
        )
        size = publisher.measure_payload_size(job)
        print(f"\n[RESULT] Single post API payload: {size} bytes")
        print(f"[RESULT] 30 posts/day = {size * 30} bytes = {size * 30 / 1024:.1f} KB")
        print(f"[RESULT] vs 30 video uploads = {30 * 15 * 1024 * 1024 / 1024 / 1024:.0f} MB")
        print(f"[RESULT] Data savings: {30 * 15 * 1024 * 1024 / (size * 30):.0f}x less mobile data!")

    elif args.video:
        job = PublishJob(
            video_path=args.video,
            title=args.title,
            caption=args.caption,
            hashtags=["viral", "trending", "fyp"],
            accounts=[
                AccountConfig("Test Account", "tiktok", "int_tt_01"),
            ]
        )
        publisher.publish_batch(job, simulate=args.simulate)

    else:
        print("[PROXY] Usage:")
        print("  --check-ip         Check current outbound IP")
        print("  --payload-size     Measure API payload size")
        print("  --video <path>     Publish a video")
        print("  --simulate         Dry run without actually posting")
""",
"""
