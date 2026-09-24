"""
Going Merry — Viral Video View Detection & Monitoring Engine
============================================================
Continuously tracks live views of posted clips across YouTube Shorts,
TikTok, Instagram Reels, and Facebook Reels.

When views exceed the user's defined criteria (e.g. >1,000 views):
  1. Marks clip as a Verified Viral Hit (is_viral=True)
  2. Emits real-time event to Web Dashboard (SSE)
  3. Sends instant rich Telegram alert with estimated Whop payout
  4. Prepares one-click Whop submission for the user
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()
load_dotenv("clipper/.env", override=False)

from dataclasses import dataclass
from clipper.core.analytics_tracker import AnalyticsTracker
from clipper.core.telegram_notifier import TelegramNotifier
from clipper.core.event_bus import event_bus


@dataclass
class Clip:
    start: float
    end: float
    title: str
    score: int = 85
    hook: str = ""
    hashtags: Optional[List[str]] = None
    platform: str = "shorts"
    emotion: str = "chill"
    music_vibe: str = ""

    @property
    def duration(self) -> float:
        return max(0.1, self.end - self.start)


class ViralDetector:
    """
    Dual-engine viral processor:
    1. Moment Detection: Identifies top viral clips in video transcripts via LLM router.
    2. View Tracker: Monitors live views and sends Telegram/Web alerts when criteria are met.
    """

    def __init__(
        self, 
        default_threshold: int = 1000, 
        default_criteria_views: Optional[int] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None
    ):
        self.tracker = AnalyticsTracker()
        self.telegram = TelegramNotifier(bot_token=telegram_bot_token, chat_id=telegram_chat_id)
        effective_threshold = default_criteria_views if default_criteria_views is not None else default_threshold
        self.default_threshold = int(os.getenv("VIRAL_VIEW_THRESHOLD", effective_threshold))

    def find_clips(
        self,
        transcript_text: str,
        segments: list,
        video_duration: float,
        num_clips: int = 3,
        min_duration: float = 15.0,
        max_duration: float = 60.0,
        target_platform: str = "all",
        campaign_prompt: Optional[str] = None,
        required_hashtags: Optional[list] = None,
    ) -> List[Clip]:
        """
        Uses LLM (NVIDIA NIM / Groq / OpenRouter) to identify top retention clips.
        """
        import re
        try:
            from clipper.utils.llm_router import call_llm_with_fallback

            prompt = f"""You are a viral shorts editor for TikTok, YouTube Shorts, and Instagram Reels.
Analyze this video transcript and extract the top {num_clips} most engaging, high-retention clips.

Video Duration: {video_duration:.1f}s
Target Platform: {target_platform}
Clip Duration Rules: Minimum {min_duration:.0f}s, Maximum {max_duration:.0f}s.
{f'Campaign Context: {campaign_prompt}' if campaign_prompt else ''}

Segments:
"""
            sample_segments = segments[:70] if len(segments) > 70 else segments
            for s in sample_segments:
                text = getattr(s, "text", str(s))
                start = getattr(s, "start", 0)
                end = getattr(s, "end", 0)
                prompt += f"[{start:.1f}s - {end:.1f}s]: {text}\n"

            prompt += """
Return ONLY a valid JSON array of objects with keys:
"start" (float), "end" (float), "title" (string), "score" (integer 1-100), "hook" (string), "hashtags" (array of strings),
"emotion" (string: "hype", "suspense", "chill", "funny", "dramatic", or "sad"),
"music_vibe" (string: short description of ideal background music, e.g. "brazilian phonk bass boost", "dark suspense piano", "lofi chill beats")
"""
            messages = [
                {"role": "system", "content": "You are an elite viral video editor. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ]

            raw = call_llm_with_fallback(messages, temperature=0.3)
            cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned)

            clips = []
            for item in data[:num_clips]:
                start = float(item.get("start", 0))
                end = float(item.get("end", start + 30.0))
                if end <= start: end = start + 30.0
                clips.append(Clip(
                    start=start,
                    end=end,
                    title=item.get("title", "Viral Short"),
                    score=int(item.get("score", 85)),
                    hook=item.get("hook", ""),
                    hashtags=item.get("hashtags", required_hashtags or ["#shorts", "#viral"]),
                    platform=target_platform,
                    emotion=item.get("emotion", "chill").lower().strip(),
                    music_vibe=item.get("music_vibe", "")
                ))
            if clips:
                return clips
        except Exception as e:
            print(f"[VIRAL_DETECTOR] LLM extraction notice: {e}. Using intelligent timeline slicing.")

        # Fallback slice
        clip_len = min(40.0, max(min_duration, video_duration if video_duration > 0 else 30.0))
        return [
            Clip(
                start=0.0,
                end=clip_len,
                title="Top Highlight Moment",
                score=90,
                hook="Watch this unbelievable moment...",
                hashtags=required_hashtags or ["#shorts", "#viral"],
                platform=target_platform
            )
        ]

    def evaluate_clip(
        self,
        clip_id: int,
        post_url: str,
        title: str,
        platform: str = "youtube",
        threshold: Optional[int] = None,
        account_username: str = "@GoingMerry",
        campaign_name: str = "FundingPips ($5 CPM)",
        db_session = None
    ) -> Dict[str, Any]:
        """
        Fetches live view metrics for a specific clip and checks against viral criteria.
        """
        criteria = threshold or self.default_threshold
        print(f"\n🔍 Checking views for clip [{clip_id}]: {title[:30]}...")
        print(f"   Target URL: {post_url}")
        print(f"   Criteria  : >{criteria:,} views")

        metrics = self.tracker.fetch_clip_metrics(post_url)
        live_views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)

        print(f"   📊 Live Stats: {live_views:,} views | {likes} likes | {comments} comments")

        is_viral = live_views >= criteria
        alert_sent = False
        telegram_result = None

        if is_viral:
            print(f"   🔥 VIRAL THRESHOLD MET! ({live_views:,} >= {criteria:,})")
            
            # 1. Send Telegram Notification
            telegram_result = self.telegram.send_viral_alert(
                title=title,
                platform=platform,
                views=live_views,
                criteria_views=criteria,
                post_url=post_url,
                account_username=account_username,
                campaign_name=campaign_name
            )
            alert_sent = telegram_result.get("success", False)
            if alert_sent:
                print("   📲 Telegram alert delivered successfully!")
            else:
                print(f"   ℹ️ Telegram alert status: {telegram_result.get('error', 'Not configured')}")

            # 2. Emit Web Dashboard Event (SSE)
            event_bus.emit("viral.detected", {
                "clip_id": clip_id,
                "title": title,
                "platform": platform,
                "views": live_views,
                "criteria": criteria,
                "post_url": post_url,
                "account": account_username,
                "campaign": campaign_name,
                "timestamp": datetime.utcnow().isoformat()
            })

        # 3. Update Database if session provided
        if db_session:
            try:
                from web_app.models import Clip
                clip = db_session.query(Clip).filter_by(id=clip_id).first()
                if clip:
                    clip.views = max(clip.views or 0, live_views)
                    clip.likes = max(clip.likes or 0, likes)
                    clip.comments = max(clip.comments or 0, comments)
                    clip.last_tracked_at = datetime.utcnow()
                    if is_viral:
                        clip.is_viral = True
                        if alert_sent:
                            clip.viral_alert_sent = True
                            clip.viral_notified_at = datetime.utcnow()
                    db_session.commit()
            except Exception as e:
                print(f"   ⚠️ DB update error: {e}")

        return {
            "clip_id": clip_id,
            "title": title,
            "views": live_views,
            "criteria": criteria,
            "is_viral": is_viral,
            "alert_sent": alert_sent,
            "telegram_result": telegram_result,
            "post_url": post_url
        }

    def scan_all_clips(self, db_session, threshold: Optional[int] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scans all posted clips in the database and evaluates virality.
        """
        from web_app.models import Clip, AccountPersona

        query = db_session.query(Clip).filter(Clip.post_url != None, Clip.post_url != "")
        if user_id:
            query = query.filter_by(user_id=user_id)

        clips = query.all()
        results = []
        for c in clips:
            acc_name = "@GoingMerry"
            if hasattr(c, "account_persona") and c.account_persona:
                acc_name = c.account_persona.username or c.account_persona.name

            res = self.evaluate_clip(
                clip_id=c.id,
                post_url=c.post_url,
                title=c.title or "Untitled Clip",
                threshold=threshold or c.viral_criteria_views or self.default_threshold,
                account_username=acc_name,
                db_session=db_session
            )
            results.append(res)

        return results


def check_clip_virality(clip_id: int, post_url: str, title: str, threshold: int = 1000) -> Dict[str, Any]:
    """Standalone helper function."""
    detector = ViralDetector(default_threshold=threshold)
    return detector.evaluate_clip(clip_id=clip_id, post_url=post_url, title=title, threshold=threshold)
