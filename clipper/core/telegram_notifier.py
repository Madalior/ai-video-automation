"""
Telegram Notifier for Going Merry & Viral Video Alerts
======================================================
Sends instant rich HTML notifications to your Telegram account/channel
when a video surpasses your viral view criteria (e.g. >1,000 views).
"""

import os
import sys
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()
load_dotenv("clipper/.env", override=False)


class TelegramNotifier:
    """
    Sends alerts to Telegram bot/chat via Telegram Bot API.
    """

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id and "your_" not in str(self.bot_token).lower())

    def send_message(self, text: str, parse_mode: str = "HTML", reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends an HTML formatted message to the configured Telegram chat.
        """
        if not self.is_configured():
            return {"success": False, "error": "Telegram bot_token or chat_id not configured"}

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            res = requests.post(url, json=payload, timeout=12)
            data = res.json()
            if res.status_code == 200 and data.get("ok"):
                return {"success": True, "message_id": data["result"]["message_id"]}
            else:
                err = data.get("description", res.text[:120])
                return {"success": False, "error": err, "status_code": res.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_viral_alert(
        self,
        title: str,
        platform: str,
        views: int,
        criteria_views: int,
        post_url: str,
        account_username: str = "@GoingMerry",
        campaign_name: str = "FundingPips ($5 CPM)",
        estimated_payout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Sends a high-priority viral detection alert.
        """
        if estimated_payout is None:
            # Default to $5 CPM if not provided
            estimated_payout = round((views / 1000.0) * 5.0, 2)

        platform_icons = {
            "youtube": "🔴 YouTube Shorts",
            "youtube_shorts": "🔴 YouTube Shorts",
            "tiktok": "🎵 TikTok",
            "instagram": "🟣 Instagram Reels",
            "instagram_reels": "🟣 Instagram Reels",
            "facebook": "🔵 Facebook Reels",
        }
        p_label = platform_icons.get(platform.lower(), f"📺 {platform.capitalize()}")

        text = (
            f"🔥 <b>VIRAL HIT DETECTED!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎬 <b>Clip:</b> {title}\n"
            f"👤 <b>Account:</b> <code>{account_username}</code>\n"
            f"📺 <b>Platform:</b> {p_label}\n"
            f"👁️ <b>Live Views:</b> <b>{views:,}</b> <i>(Criteria: &gt;{criteria_views:,})</i>\n"
            f"🏆 <b>Campaign:</b> {campaign_name}\n"
            f"💰 <b>Estimated Bounty:</b> <b>${estimated_payout:,.2f}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <b>Watch Live:</b> <a href=\"{post_url}\">{post_url}</a>\n\n"
            f"👉 <i>This video has exceeded your viral criteria and is ready to submit to Whop Content Rewards!</i>"
        )

        return self.send_message(text)

    def test_connection(self) -> Dict[str, Any]:
        """
        Sends a test ping to verify Telegram bot connection.
        """
        text = (
            f"🚀 <b>Going Merry Telegram Alert System Connected!</b>\n\n"
            f"Your Telegram bot is successfully linked to Going Merry.\n"
            f"You will receive automatic pings whenever any video crosses your viral view criteria!"
        )
        return self.send_message(text)


def send_telegram_alert(
    title: str,
    platform: str,
    views: int,
    criteria_views: int,
    post_url: str,
    account_username: str = "@GoingMerry",
    campaign_name: str = "FundingPips ($5 CPM)"
) -> Dict[str, Any]:
    """Helper function for quick calling."""
    notifier = TelegramNotifier()
    return notifier.send_viral_alert(
        title=title,
        platform=platform,
        views=views,
        criteria_views=criteria_views,
        post_url=post_url,
        account_username=account_username,
        campaign_name=campaign_name
    )
