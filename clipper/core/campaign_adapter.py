"""
Campaign Adapter — Dynamic Whop Brief Ingestion & Pipeline Orchestration
========================================================================
Translates raw Whop campaign brief JSONs into dynamic runtime parameters:
  1. LLM Moment Detection Context (description + restrictions injection)
  2. Remotion Visual Overlay Badge
  3. Video Duration & Pacing Constraints
  4. Compliant Social Media Copywriting (Titles, Captions, Hashtags, Bio Links)
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional, Union

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class CampaignAdapter:
    """
    Parses and adapts any Whop campaign brief dynamically.
    Eliminates hardcoded strings and architecture modifications across campaigns.
    """

    def __init__(self, brief_source: Optional[Union[str, Path, dict]] = None):
        self.brief_path = None
        self.raw_data = {}
        self._load(brief_source)

    def _load(self, source: Optional[Union[str, Path, dict]]):
        if isinstance(source, dict):
            self.raw_data = source
            return

        # Default path
        default_brief = Path("campaigns") / "active_campaign_brief.json"

        if source is None:
            self.brief_path = default_brief
        else:
            p = Path(source)
            if p.exists() and p.is_file():
                self.brief_path = p
            else:
                # Check if it's a name in campaigns/
                candidate = Path("campaigns") / f"{source}.json"
                if candidate.exists():
                    self.brief_path = candidate
                elif default_brief.exists():
                    self.brief_path = default_brief
                else:
                    self.brief_path = None

        if self.brief_path and self.brief_path.exists():
            try:
                with open(self.brief_path, "r", encoding="utf-8") as f:
                    self.raw_data = json.load(f)
            except Exception as e:
                print(f"⚠️ [CampaignAdapter] Warning reading brief file {self.brief_path}: {e}")
                self.raw_data = {}
        else:
            self.raw_data = {}

    @property
    def campaign_name(self) -> str:
        return self.raw_data.get("campaign_name", "Whop Content Rewards")

    @property
    def description(self) -> str:
        return self.raw_data.get("description", "")

    @property
    def rules_and_restrictions(self) -> list[str]:
        rules = self.raw_data.get("rules_and_restrictions", [])
        if isinstance(rules, list):
            return [str(r) for r in rules if r]
        elif isinstance(rules, str):
            return [r.strip() for r in rules.split("\n") if r.strip()]
        return []

    @property
    def cpm_rate(self) -> float:
        try:
            return float(self.raw_data.get("cpm_rate", 1.0))
        except (ValueError, TypeError):
            return 1.0

    @property
    def min_duration_sec(self) -> float:
        try:
            return float(self.raw_data.get("min_duration_sec", 20.0))
        except (ValueError, TypeError):
            return 20.0

    @property
    def max_duration_sec(self) -> float:
        try:
            return float(self.raw_data.get("max_duration_sec", 90.0))
        except (ValueError, TypeError):
            return 90.0

    @property
    def required_overlay(self) -> str:
        return self.raw_data.get("required_overlay", "")

    @property
    def required_bio_link(self) -> str:
        return self.raw_data.get("required_bio_link", "")

    @property
    def required_tag(self) -> str:
        tag = self.raw_data.get("required_tag", "")
        # Clean up if ends with "in caption"
        if " in caption" in tag.lower():
            tag = tag.split()[0]
        return tag

    @property
    def required_hashtags(self) -> list[str]:
        tags = self.raw_data.get("required_hashtags", [])
        if isinstance(tags, list):
            return [t if t.startswith("#") else f"#{t}" for t in tags if t]
        elif isinstance(tags, str):
            return [t if t.startswith("#") else f"#{t}" for t in tags.split() if t]
        return []

    @property
    def source_video_links(self) -> list[str]:
        links = self.raw_data.get("source_video_links", [])
        return links if isinstance(links, list) else [links]

    # ── Helpers for Engine Integration ──────────────────────────────────────

    def get_overlay_badge(self) -> str:
        """Returns the overlay text to burn onto the clip."""
        return self.required_overlay or ""

    def get_min_duration(self) -> float:
        """Returns minimum duration requirement in seconds."""
        return max(15.0, self.min_duration_sec)

    def get_audio_policy(self) -> dict:
        """
        Analyzes campaign rules, restrictions, and fields to determine strict audio compliance:
        - If brief explicitly mandates a track, use that track.
        - If brief forbids music, strictly forbid music.
        - If brief explicitly allows trending audio, allow it.
        - If brief has no mention of music, DO NOT add music (protects Whop payout compliance).
        """
        raw_text = " ".join(self.rules_and_restrictions + [self.description]).lower()

        # 1. Check for specific required sound/audio field in brief
        specific = (
            self.raw_data.get("required_audio") or
            self.raw_data.get("required_sound") or
            self.raw_data.get("sound_name") or ""
        )
        if specific:
            return {
                "allowed": True,
                "required_track": specific,
                "reason": f"Mandatory audio mandated in brief: '{specific}'"
            }

        # 2. Check if rules explicitly mandate a specific song / sound name
        audio_matches = re.findall(r'(?:use|must use|required audio|sound)\s*:\s*["\']?([^"\'\n,\.]+)', raw_text)
        for match in audio_matches:
            m = match.strip()
            if m and not any(k in m for k in ["trending", "original", "clean", "your", "no"]):
                return {
                    "allowed": True,
                    "required_track": m,
                    "reason": f"Mandatory audio in campaign rules: '{m}'"
                }

        # 3. Check if music is explicitly forbidden
        forbidden_keywords = [
            "original audio only", "original sound only", "no background music",
            "no music", "do not add music", "voice only", "dialogue only",
            "keep original audio", "no added audio", "raw dialogue only", "clean audio only"
        ]
        for kw in forbidden_keywords:
            if kw in raw_text:
                return {
                    "allowed": False,
                    "required_track": None,
                    "reason": f"Music strictly forbidden by campaign rule: '{kw}'"
                }

        # 4. Check if trending audio is explicitly permitted
        allowed_keywords = [
            "trending audio allowed", "trending tiktok", "trending instagram",
            "music allowed", "background music allowed", "add trending music",
            "use trending audio", "audios allowed", "bgm allowed", "music permitted"
        ]
        for kw in allowed_keywords:
            if kw in raw_text:
                return {
                    "allowed": True,
                    "required_track": None,
                    "reason": f"Trending audio explicitly permitted by rule: '{kw}'"
                }

        # 5. Default for Whop Content: If not explicitly requested, DO NOT add music!
        return {
            "allowed": False,
            "required_track": None,
            "reason": "Whop brief does not request music — keeping original dialogue for 100% submission compliance"
        }

    def get_prompt_injection(self) -> str:
        """
        Formats campaign requirements into a structured block to inject
        into the LLM ViralDetector prompt.
        """
        lines = []
        if self.description:
            lines.append("=== CAMPAIGN OBJECTIVE & TOPIC FOCUS ===")
            lines.append(f"Campaign: {self.campaign_name}")
            lines.append(f"Description:\n{self.description.strip()}")
            lines.append("")

        if self.rules_and_restrictions:
            lines.append("=== MANDATORY CAMPAIGN RULES & CONTENT RESTRICTIONS ===")
            for rule in self.rules_and_restrictions:
                lines.append(f"• {rule}")
            lines.append("")
            lines.append("CRITICAL: You MUST prioritize moments that satisfy the rules above. Clips that violate them will be rejected for payouts.")

        return "\n".join(lines)

    def generate_social_post(
        self,
        clip_title: str = "",
        clip_hook: str = "",
        platform: str = "all",
        use_llm: bool = True
    ) -> dict:
        """
        Generates platform-compliant social metadata:
          - Title
          - Caption (with required_tag and bio link)
          - Hashtags (merging campaign required_hashtags)
        Uses LLM if available; falls back to an intelligent template.
        """
        clean_tag = self.required_tag
        bio_link = self.required_bio_link
        overlay = self.required_overlay
        hashtags = list(self.required_hashtags)

        if not hashtags:
            slug = self.campaign_name.lower().replace(" ", "").replace("-", "")
            hashtags = [f"#{slug}", "#viral", "#shorts"]

        # Default fallback values
        title = f"{clip_title or self.campaign_name} ({overlay})".strip() if overlay else (clip_title or self.campaign_name)
        if len(title) > 95:
            title = title[:92] + "..."

        caption_parts = []
        if clean_tag:
            caption_parts.append(clean_tag)
        if clip_hook:
            caption_parts.append(clip_hook)
        elif self.description:
            caption_parts.append(self.description[:140] + "...")

        if overlay:
            caption_parts.append(f"Promo: {overlay}")
        if bio_link:
            caption_parts.append(f"🔗 Link in bio: {bio_link}")

        caption = "\n\n".join(caption_parts)

        # Try LLM generation for punchy high-converting copy
        if use_llm:
            try:
                from clipper.utils.llm_router import call_llm_with_fallback
                prompt = f"""You are an elite short-form social copywriter for YouTube Shorts, TikTok, and Instagram Reels.
Generate a viral post title and caption for this clip based on the campaign brief below.

CAMPAIGN: {self.campaign_name}
REQUIRED MENTION: {clean_tag}
DISCOUNT / BADGE: {overlay}
BIO LINK: {bio_link}
CLIP HOOK: {clip_hook}
CLIP TITLE: {clip_title}

RULES:
1. Title must be under 70 characters, high-curiosity or aggressive hook.
2. Caption must naturally include {clean_tag} and refer to the discount code ({overlay}) or bio link.
3. Keep it punchy (1-2 sentences). Do not repeat hashtags.

Return ONLY valid JSON:
{{
  "title": "...",
  "caption": "..."
}}
"""
                resp = call_llm_with_fallback(
                    [{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=300,
                    timeout=15.0
                )
                raw_str = resp.strip()
                if "{" in raw_str and "}" in raw_str:
                    s = raw_str.find("{")
                    e = raw_str.rfind("}")
                    data = json.loads(raw_str[s : e + 1])
                    if data.get("title"):
                        title = data["title"].strip()
                    if data.get("caption"):
                        caption = data["caption"].strip()
            except Exception as e:
                # LLM timed out or failed; deterministic template already prepared
                pass

        return {
            "title": title,
            "caption": caption,
            "hashtags": hashtags,
            "overlay": overlay,
            "bio_link": bio_link,
            "tag": clean_tag,
            "campaign_name": self.campaign_name
        }
