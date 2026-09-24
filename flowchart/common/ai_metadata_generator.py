"""
🔥 GOD MASTER MODE — AI Metadata Generator
════════════════════════════════════════════

Script-aware, emotion-driven metadata optimization:
- Script.json integration (uses real story data, not generic topics)
- Genre-aware prompt engineering (thriller vs comedy = different strategy)
- Emotion-driven copy (power words from scene emotions)
- Scene-aware hooks (actual dialogue/subtext for captions)
- Robust multi-line response parsing
- Auto-generated SEO keywords from script content
- Platform algorithm intelligence (2025/2026 best practices)
- Persistence (saves metadata.json alongside script)

Target: 12-18% CTR, 300%+ reach vs generic metadata
"""

import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


# ═══════════════════════════════════════════════════════════
# GENRE → METADATA STRATEGY
# ═══════════════════════════════════════════════════════════
GENRE_STRATEGY = {
    'mystery_thriller': {
        'tone': 'suspenseful, dark, intense',
        'hooks': ['Who did it?', 'The truth will shock you', 'Nothing is what it seems'],
        'cta_style': 'cliffhanger questions',
        'emoji_set': '🔍🕵️‍♂️💀🔪😱',
    },
    'horror': {
        'tone': 'terrifying, visceral, dread',
        'hooks': ['Dont watch alone', 'This is cursed', 'You cant unsee this'],
        'cta_style': 'dare/warning',
        'emoji_set': '👻💀🩸😱🫣',
    },
    'romance': {
        'tone': 'emotional, heartfelt, passionate',
        'hooks': ['This will make you cry', 'Love story that broke the internet', 'True love exists'],
        'cta_style': 'emotional pull',
        'emoji_set': '❤️💔🥺✨😍',
    },
    'action': {
        'tone': 'explosive, adrenaline, intense',
        'hooks': ['INSANE action', 'You wont believe this', 'Edge of your seat'],
        'cta_style': 'hype/excitement',
        'emoji_set': '🔥💥⚡🎬😤',
    },
    'comedy': {
        'tone': 'hilarious, relatable, fun',
        'hooks': ['I cant stop laughing', 'This is TOO real', 'Wait for the ending'],
        'cta_style': 'conversational/fun',
        'emoji_set': '😂🤣💀😭✋',
    },
    'drama': {
        'tone': 'emotional, deep, thought-provoking',
        'hooks': ['This changed my perspective', 'The ending destroyed me', 'Real story'],
        'cta_style': 'thought-provoking questions',
        'emoji_set': '😢🎭💔🥺✨',
    },
}

DEFAULT_STRATEGY = {
    'tone': 'engaging, viral, must-watch',
    'hooks': ['You need to see this', 'This is incredible', 'Wait for it'],
    'cta_style': 'curiosity gap',
    'emoji_set': '🔥✨💯😱⚡',
}

# Emotion → viral copy power words
EMOTION_COPY = {
    'shock': {'words': ['SHOCKING', 'UNBELIEVABLE', 'JAW-DROPPING'], 'energy': 'explosive'},
    'anger': {'words': ['FURIOUS', 'OUTRAGE', 'EXPOSED'], 'energy': 'aggressive'},
    'fear': {'words': ['TERRIFYING', 'NIGHTMARE', 'CHILLING'], 'energy': 'intense'},
    'mystery': {'words': ['SECRET', 'HIDDEN', 'REVEALED'], 'energy': 'suspenseful'},
    'suspense': {'words': ['WAIT FOR IT', 'THEN THIS', 'HOLD ON'], 'energy': 'building'},
    'revelation': {'words': ['EXPOSED', 'TRUTH', 'FINALLY'], 'energy': 'climactic'},
    'sadness': {'words': ['HEARTBREAKING', 'EMOTIONAL', 'TEARS'], 'energy': 'somber'},
    'triumph': {'words': ['UNSTOPPABLE', 'LEGENDARY', 'VICTORY'], 'energy': 'triumphant'},
    'excitement': {'words': ['INCREDIBLE', 'INSANE', 'AMAZING'], 'energy': 'hype'},
    'confusion': {'words': ['WHAT?!', 'HOW?!', 'IMPOSSIBLE'], 'energy': 'bewildered'},
    'curiosity': {'words': ['DISCOVER', 'HIDDEN', 'WHAT IF'], 'energy': 'intriguing'},
    'love': {'words': ['FOREVER', 'DESTINY', 'SOULMATE'], 'energy': 'warm'},
    'relief': {'words': ['FINALLY', 'AT LAST', 'REDEMPTION'], 'energy': 'cathartic'},
    'frustration': {'words': ['ENOUGH', 'BREAKING POINT', 'FED UP'], 'energy': 'tense'},
    'horror': {'words': ['CURSED', 'EVIL', 'POSSESSED'], 'energy': 'dark'},
}


class AIMetadataGenerator:
    """
    🔥 GOD MASTER MODE — AI Metadata Generator

    Script-aware, genre-driven, emotion-optimized metadata
    for maximum CTR and algorithmic reach.

    Target: 12-18% CTR (vs 4-6% baseline)
    """

    def __init__(self, gemini_api_key=None):
        """Initialize with Gemini API key."""
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')

        if self.api_key and HAS_GENAI:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            if not HAS_GENAI:
                print("[METADATA] google-generativeai not installed — using smart fallback")
            else:
                print("[METADATA] No Gemini API key — using smart fallback")
            self.model = None

        # Platform-specific rules (2025/2026 best practices)
        self.platform_rules = {
            'youtube': {
                'title_max': 100,
                'description_max': 5000,
                'tags_max': 500,
                'hashtags_count': 3,
                'focus': 'SEO keywords, search intent, watch time signals',
            },
            'tiktok': {
                'caption_max': 150,
                'hashtags_count': 5,
                'focus': 'trend-jacking, native hooks, FYP optimization',
            },
            'instagram': {
                'caption_max': 2200,
                'hashtags_count': 10,
                'focus': 'Reels discovery, engagement bait, community building',
            },
            'facebook': {
                'description_max': 63206,
                'hashtags_count': 3,
                'focus': 'shareability, group virality, emotional resonance',
            },
            'twitter': {
                'tweet_max': 280,
                'hashtags_count': 3,
                'focus': 'quote-tweet bait, hot takes, thread potential',
            },
        }

    # ════════════════════════════════════════════════════════
    # 1. SCRIPT.JSON INTEGRATION
    # ════════════════════════════════════════════════════════
    def generate_from_script(self, script_json_path: str) -> Dict:
        """
        🔥 Generate metadata for ALL platforms from script.json.

        Uses real story data: title, genre, emotions, dialogue,
        subtext, character names — for authentic, high-CTR copy.

        Returns:
            Dict with metadata for each platform + analysis
        """
        with open(script_json_path, 'r', encoding='utf-8') as f:
            script = json.load(f)

        title = script.get('title', 'Untitled')
        genre = script.get('genre', 'drama').lower()
        target_emotion = script.get('target_emotion', '').lower()
        protagonist = script.get('protagonist', '')
        scenes = script.get('scenes', [])
        full_script = script.get('Full_script', '')

        # Extract rich context
        context = self._extract_script_context(scenes, genre, target_emotion)

        print(f"\n{'═'*60}")
        print(f"📝 GOD MASTER MODE — AI METADATA GENERATOR")
        print(f"{'═'*60}")
        print(f"   Title: {title}")
        print(f"   Genre: {genre}")
        print(f"   Emotion: {target_emotion}")
        print(f"   Protagonist: {protagonist}")
        print(f"   Scenes: {len(scenes)}")
        print(f"   Hook scene: #{context['best_hook_scene']}")

        is_short = len(scenes) <= 6

        metadata = {}
        platforms = ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter']

        for platform in platforms:
            print(f"\n   📝 Generating {platform.upper()}...")
            metadata[platform] = self._generate_script_aware_metadata(
                platform=platform,
                title=title,
                genre=genre,
                emotion=target_emotion,
                protagonist=protagonist,
                context=context,
                is_short=is_short,
            )
            print(f"      ✓ Done")

        # Save metadata alongside script
        output_dir = os.path.dirname(script_json_path)
        metadata_path = os.path.join(output_dir, 'metadata.json')
        save_data = {
            'title': title,
            'genre': genre,
            'generated_at': datetime.now().isoformat(),
            'platforms': metadata,
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        print(f"\n   💾 Saved: {metadata_path}")

        print(f"\n   ✅ All platforms generated!")
        return metadata

    def _extract_script_context(self, scenes: List[Dict], genre: str, emotion: str) -> Dict:
        """Extract rich context from script scenes for prompt engineering."""
        context = {
            'emotions': [],
            'dialogues': [],
            'subtexts': [],
            'hook_dialogue': '',
            'hook_subtext': '',
            'best_hook_scene': 1,
            'keywords': set(),
            'emotion_journey': '',
        }

        best_hook_intensity = 0
        emotion_names = []

        for scene in scenes:
            em = scene.get('emotion', '').lower()
            context['emotions'].append(em)
            emotion_names.append(em)

            dialogue = scene.get('dialogue', '')
            if dialogue and dialogue.lower() not in ('none', ''):
                clean = re.sub(r'\[.*?\]', '', dialogue).strip()
                if clean:
                    context['dialogues'].append(clean)

            subtext = scene.get('subtext', '')
            if subtext and subtext.lower() not in ('none', ''):
                context['subtexts'].append(subtext)

            # Extract keywords from background and visual
            bg = scene.get('background', '')
            if bg:
                context['keywords'].update(bg.split()[:3])

            # Find best hook scene (highest emotion intensity)
            intensity_map = {
                'shock': 0.9, 'anger': 0.9, 'fear': 0.85, 'horror': 0.9,
                'revelation': 0.8, 'triumph': 0.8, 'excitement': 0.8,
                'suspense': 0.7, 'tension': 0.7, 'frustration': 0.7,
                'mystery': 0.6, 'curiosity': 0.65, 'surprise': 0.75,
                'confusion': 0.6, 'sadness': 0.4, 'love': 0.5, 'relief': 0.4,
            }
            intensity = intensity_map.get(em, 0.5)
            if intensity > best_hook_intensity:
                best_hook_intensity = intensity
                context['best_hook_scene'] = scene.get('scene_number', 1)
                if dialogue and dialogue.lower() != 'none':
                    context['hook_dialogue'] = re.sub(r'\[.*?\]', '', dialogue).strip()
                if subtext and subtext.lower() != 'none':
                    context['hook_subtext'] = subtext

        context['emotion_journey'] = ' → '.join(emotion_names)
        context['keywords'] = list(context['keywords'])[:10]

        return context

    def _generate_script_aware_metadata(self, platform: str, title: str,
                                          genre: str, emotion: str,
                                          protagonist: str, context: Dict,
                                          is_short: bool) -> Dict:
        """Generate metadata using full script context."""
        strategy = GENRE_STRATEGY.get(genre, DEFAULT_STRATEGY)
        emotion_data = EMOTION_COPY.get(emotion, {'words': ['INCREDIBLE'], 'energy': 'engaging'})
        rules = self.platform_rules.get(platform, {})

        # Build the super-prompt
        prompt = self._build_god_prompt(
            platform, title, genre, emotion, protagonist,
            context, strategy, emotion_data, rules, is_short
        )

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                parsed = self._parse_response(response.text, platform)
                if parsed:
                    return parsed
            except Exception as e:
                print(f"      [API ERROR] {e} — using smart fallback")

        # Smart fallback using script data
        return self._smart_fallback(platform, title, genre, emotion,
                                     context, strategy, emotion_data, is_short)

    def _build_god_prompt(self, platform, title, genre, emotion, protagonist,
                           context, strategy, emotion_data, rules, is_short) -> str:
        """Build the ultimate metadata generation prompt."""

        # Common context block
        story_context = f"""
STORY DATA (use this for authentic copy):
- Title: {title}
- Genre: {genre}
- Protagonist: {protagonist}
- Target emotion: {emotion}
- Emotion journey: {context['emotion_journey']}
- Best hook dialogue: "{context.get('hook_dialogue', '')}"
- Story subtext: "{context.get('hook_subtext', '')}"
- Available subtexts: {', '.join(context.get('subtexts', [])[:3])}

GENRE STRATEGY:
- Tone: {strategy['tone']}
- Hook templates: {', '.join(strategy['hooks'])}
- CTA style: {strategy['cta_style']}

POWER WORDS for this emotion: {', '.join(emotion_data['words'])}
Energy level: {emotion_data['energy']}
"""

        if platform == 'youtube':
            return f"""
You are a YouTube SEO expert and viral content strategist.

{story_context}

Generate VIRAL {('YouTube Shorts' if is_short else 'YouTube')} metadata:

1. TITLE (max {rules['title_max']} chars):
   - Use 1-2 CAPS power words from the story's emotion
   - Create curiosity gap using the story's subtext
   - Include brackets: "(SHOCKING ENDING)" or "(YOU WON'T BELIEVE)"
   - Reference the protagonist or key plot element
   {'- Add #Shorts at the end' if is_short else ''}

2. DESCRIPTION (SEO-optimized, 200-500 words):
   - Opening hook from the story's best dialogue or subtext
   - Include timestamps for key moments
   - 3 CTAs (subscribe, comment, share)
   - SEO keywords naturally woven in
   - Emotional storytelling paragraph

3. TAGS (15-20 tags, comma-separated):
   - Mix broad (genre) + specific (story elements)
   - Include trending variations
   - Long-tail keywords

4. HASHTAGS ({rules['hashtags_count']} hashtags):
   - 1 broad trending + 1 niche + 1 story-specific

Format EXACTLY as:
TITLE: [title]
DESCRIPTION: [full description]
TAGS: [tag1, tag2, tag3, ...]
HASHTAGS: [#tag1 #tag2 #tag3]
"""

        elif platform == 'tiktok':
            return f"""
You are a TikTok viral strategist.

{story_context}

Generate a VIRAL TikTok caption:

1. CAPTION (max {rules['caption_max']} chars):
   - Start with a scroll-stopping hook from the story
   - Use the actual dialogue or subtext
   - Conversational, Gen-Z friendly tone
   - End with engagement bait

2. HASHTAGS ({rules['hashtags_count']} hashtags):
   - #fyp #foryoupage always included
   - Genre-specific trending tags
   - Story-relevant niche tags

Format EXACTLY as:
CAPTION: [caption]
HASHTAGS: [#tag1 #tag2 #tag3 #tag4 #tag5]
"""

        elif platform == 'instagram':
            return f"""
You are an Instagram Reels growth expert.

{story_context}

Generate viral Instagram Reels metadata:

1. CAPTION (engaging, 100-300 chars for Reels):
   - Hook from story dialogue/subtext
   - Storytelling micro-paragraph
   - Question to drive comments
   - Emoji usage matching the genre: {strategy['emoji_set']}

2. HASHTAGS ({rules['hashtags_count']} hashtags):
   - Mix of large (1M+), medium (100K+), niche
   - Genre + emotion + story-specific

Format EXACTLY as:
CAPTION: [caption]
HASHTAGS: [#tag1 #tag2 ... #tag10]
"""

        elif platform == 'facebook':
            return f"""
You are a Facebook viral content strategist.

{story_context}

Generate a shareable Facebook post:

1. DESCRIPTION (emotional, 200-400 chars):
   - Lead with emotional hook from the story
   - Make people tag friends
   - Question or hot take at the end
   - Shareability over SEO

2. HASHTAGS ({rules['hashtags_count']} hashtags):

Format EXACTLY as:
DESCRIPTION: [description]
HASHTAGS: [#tag1 #tag2 #tag3]
"""

        elif platform == 'twitter':
            return f"""
You are a Twitter/X viral strategist.

{story_context}

Generate a viral tweet:

1. TWEET (max {rules['tweet_max']} chars):
   - Hot take or controversial angle on the story
   - Use actual dialogue as a quote
   - Thread potential
   - Quote-tweet bait

2. HASHTAGS ({rules['hashtags_count']} hashtags):

Format EXACTLY as:
TWEET: [tweet]
HASHTAGS: [#tag1 #tag2 #tag3]
"""
        return ""

    # ════════════════════════════════════════════════════════
    # 2. ROBUST PARSER
    # ════════════════════════════════════════════════════════
    def _parse_response(self, text: str, platform: str) -> Optional[Dict]:
        """
        Robust multi-line response parser.
        Handles both single-line and multi-line AI responses.
        """
        if not text:
            return None

        # Define expected fields per platform
        field_map = {
            'youtube': ['TITLE', 'DESCRIPTION', 'TAGS', 'HASHTAGS'],
            'tiktok': ['CAPTION', 'HASHTAGS'],
            'instagram': ['CAPTION', 'HASHTAGS'],
            'facebook': ['DESCRIPTION', 'HASHTAGS'],
            'twitter': ['TWEET', 'HASHTAGS'],
        }

        fields = field_map.get(platform, [])
        result = {}

        for i, field in enumerate(fields):
            # Find the field in text
            pattern = rf'{field}:\s*(.*?)(?={"|".join(f + ":" for f in fields[i+1:])}|\Z)'
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up
                value = re.sub(r'\n{3,}', '\n\n', value)
                key = field.lower()
                if key == 'tags':
                    result[key] = [t.strip() for t in value.split(',') if t.strip()]
                elif key == 'hashtags':
                    result[key] = [h.strip() for h in re.findall(r'#\w+', value)]
                else:
                    result[key] = value

        return result if result else None

    # ════════════════════════════════════════════════════════
    # 3. SMART FALLBACK (script-aware, no API needed)
    # ════════════════════════════════════════════════════════
    def _smart_fallback(self, platform, title, genre, emotion,
                         context, strategy, emotion_data, is_short) -> Dict:
        """
        Generate high-quality metadata WITHOUT API.
        Uses script data for authentic copy.
        """
        power_word = emotion_data['words'][0] if emotion_data['words'] else 'INCREDIBLE'
        hook = context.get('hook_dialogue', '') or context.get('hook_subtext', '') or title
        emojis = strategy.get('emoji_set', '🔥✨')
        genre_hooks = strategy.get('hooks', ['Must watch'])

        if platform == 'youtube':
            yt_title = f"{title} — {power_word} {emojis[0]}"
            if is_short:
                yt_title += ' #Shorts'
            if len(yt_title) > 100:
                yt_title = yt_title[:97] + '...'

            desc_parts = [
                f"{emojis[0]} {genre_hooks[0]}",
                f"",
                f'"{hook}"',
                f"",
                f"A {genre.replace('_', ' ')} story about {context.get('hook_subtext', title)}.",
                f"Emotional journey: {context.get('emotion_journey', emotion)}",
                f"",
                f"🔔 Subscribe for more {genre.replace('_', ' ')} content!",
                f"💬 Comment your thoughts below!",
                f"📤 Share if this moved you!",
            ]

            return {
                'title': yt_title,
                'description': '\n'.join(desc_parts),
                'tags': [genre.replace('_', ' '), emotion, 'viral', 'trending',
                         'short film', title.split()[0] if title else 'video',
                         'must watch', power_word.lower(), 'story', '2026'],
                'hashtags': [f'#{genre.replace("_", "")}', '#viral', '#shorts' if is_short else '#trending'],
            }

        elif platform == 'tiktok':
            caption = f"{emojis[0]} {genre_hooks[0]} {emojis[1]}"
            if hook:
                caption = f'"{hook}" {emojis[0]} {genre_hooks[0]}'
            if len(caption) > 150:
                caption = caption[:147] + '...'

            return {
                'caption': caption,
                'hashtags': ['#fyp', '#foryoupage', f'#{genre.replace("_", "")}',
                            '#viral', f'#{emotion}'],
            }

        elif platform == 'instagram':
            caption = f"{emojis[0]} {genre_hooks[0]}\n\n"
            if hook:
                caption += f'"{hook}"\n\n'
            caption += f"What would you do? {emojis[1]} Comment below!"

            return {
                'caption': caption,
                'hashtags': ['#reels', '#reelsinstagram', '#viral',
                            f'#{genre.replace("_", "")}', f'#{emotion}',
                            '#explore', '#trending', '#storytelling',
                            '#shortfilm', '#content'],
            }

        elif platform == 'facebook':
            desc = f"{emojis[0]} {genre_hooks[0]}\n\n"
            if hook:
                desc += f'"{hook}"\n\n'
            desc += f"This {genre.replace('_', ' ')} story will make you feel {emotion}. "
            desc += "Tag someone who needs to see this! 👇"

            return {
                'description': desc,
                'hashtags': [f'#{genre.replace("_", "")}', '#viral', '#mustwatch'],
            }

        elif platform == 'twitter':
            tweet = f'{emojis[0]} "{hook}"'
            if len(tweet) > 250:
                tweet = tweet[:247] + '...'
            tweet += f"\n\n{genre_hooks[0]} {emojis[1]}"
            if len(tweet) > 280:
                tweet = tweet[:277] + '...'

            return {
                'tweet': tweet,
                'hashtags': [f'#{genre.replace("_", "")}', '#viral', '#trending'],
            }

        return {}

    # ════════════════════════════════════════════════════════
    # 4. LEGACY METHODS (backward compatible)
    # ════════════════════════════════════════════════════════
    def generate_all_metadata(self, video_topic, video_duration, niche="General"):
        """Generate optimized metadata for ALL platforms (legacy)."""
        print(f"🤖 Generating AI-optimized metadata...")
        print(f"   Topic: {video_topic}")
        print(f"   Duration: {video_duration}s")
        print(f"   Niche: {niche}")
        print()

        metadata = {}
        is_short = video_duration <= 60

        for platform in ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter']:
            print(f"📝 Generating {platform.capitalize()} metadata...")
            metadata[platform] = self.generate_platform_metadata(
                platform=platform, topic=video_topic,
                niche=niche, is_short=is_short
            )
            print(f"   ✅ Done!")

        print()
        print("✅ All metadata generated!")
        return metadata

    def generate_platform_metadata(self, platform, topic, niche, is_short):
        """Generate optimized metadata for specific platform (legacy)."""
        if not self.model:
            return self._generate_fallback_metadata(platform, topic, is_short)

        rules = self.platform_rules.get(platform, {})

        if platform == 'youtube':
            return self._generate_youtube_metadata(topic, niche, is_short, rules)
        elif platform == 'tiktok':
            return self._generate_tiktok_metadata(topic, niche, rules)
        elif platform == 'instagram':
            return self._generate_instagram_metadata(topic, niche, rules)
        elif platform == 'facebook':
            return self._generate_facebook_metadata(topic, niche, rules)
        elif platform == 'twitter':
            return self._generate_twitter_metadata(topic, niche, rules)

    def _generate_youtube_metadata(self, topic, niche, is_short, rules):
        """Generate YouTube-optimized metadata (legacy)."""
        video_type = "YouTube Short" if is_short else "YouTube video"
        prompt = f"""
Create high-performing {video_type} metadata. Topic: {topic}. Niche: {niche}.
Use power words, curiosity gaps, and CAPS for emphasis.
Generate:
TITLE: (max {rules['title_max']} chars, viral and clickable)
DESCRIPTION: (SEO-optimized, include CTAs)
TAGS: (15 relevant tags, comma-separated)
HASHTAGS: ({rules['hashtags_count']} trending hashtags)
"""
        try:
            response = self.model.generate_content(prompt)
            parsed = self._parse_response(response.text, 'youtube')
            if parsed:
                if is_short and '#Shorts' not in parsed.get('title', ''):
                    parsed['title'] = parsed.get('title', '') + ' #Shorts'
                return parsed
        except Exception as e:
            print(f"   [ERROR] {e}")
        return self._generate_fallback_metadata('youtube', topic, is_short)

    def _generate_tiktok_metadata(self, topic, niche, rules):
        """Generate TikTok-optimized metadata (legacy)."""
        prompt = f"""
Create viral TikTok caption. Topic: {topic}. Niche: {niche}.
CAPTION: (max {rules['caption_max']} chars, hook + engagement bait)
HASHTAGS: ({rules['hashtags_count']} trending hashtags including #fyp)
"""
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, 'tiktok') or self._generate_fallback_metadata('tiktok', topic, True)
        except Exception as e:
            print(f"   [ERROR] {e}")
            return self._generate_fallback_metadata('tiktok', topic, True)

    def _generate_instagram_metadata(self, topic, niche, rules):
        """Generate Instagram-optimized metadata (legacy)."""
        prompt = f"""
Create engaging Instagram Reels caption. Topic: {topic}. Niche: {niche}.
CAPTION: (engaging storytelling, ask questions)
HASHTAGS: ({rules['hashtags_count']} mix of trending + niche)
"""
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, 'instagram') or self._generate_fallback_metadata('instagram', topic, True)
        except Exception as e:
            print(f"   [ERROR] {e}")
            return self._generate_fallback_metadata('instagram', topic, True)

    def _generate_facebook_metadata(self, topic, niche, rules):
        """Generate Facebook-optimized metadata (legacy)."""
        prompt = f"""
Create shareable Facebook post. Topic: {topic}. Niche: {niche}.
DESCRIPTION: (emotional, shareable, include question)
HASHTAGS: ({rules['hashtags_count']} hashtags)
"""
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, 'facebook') or self._generate_fallback_metadata('facebook', topic, True)
        except Exception as e:
            print(f"   [ERROR] {e}")
            return self._generate_fallback_metadata('facebook', topic, True)

    def _generate_twitter_metadata(self, topic, niche, rules):
        """Generate Twitter-optimized metadata (legacy)."""
        prompt = f"""
Create viral tweet. Topic: {topic}. Niche: {niche}.
TWEET: (max {rules['tweet_max']} chars, punchy, hot take)
HASHTAGS: ({rules['hashtags_count']} trending hashtags)
"""
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text, 'twitter') or self._generate_fallback_metadata('twitter', topic, True)
        except Exception as e:
            print(f"   [ERROR] {e}")
            return self._generate_fallback_metadata('twitter', topic, True)

    def _generate_fallback_metadata(self, platform, topic, is_short):
        """Generate basic metadata when AI is not available (legacy)."""
        if platform == 'youtube':
            return {
                'title': f"{topic}{' #Shorts' if is_short else ''}",
                'description': f"Watch this video about {topic}!",
                'tags': [topic, 'viral', 'trending'],
                'hashtags': ['#viral', '#trending'],
            }
        elif platform == 'tiktok':
            return {
                'caption': f"Check out {topic}! 🔥",
                'hashtags': ['#fyp', '#viral', '#trending'],
            }
        elif platform == 'instagram':
            return {
                'caption': f"Amazing content about {topic}! ✨",
                'hashtags': ['#viral', '#trending', '#reels'],
            }
        elif platform == 'facebook':
            return {
                'description': f"Check out this video about {topic}!",
                'hashtags': ['#viral'],
            }
        elif platform == 'twitter':
            return {
                'tweet': f"Must-see: {topic}!",
                'hashtags': ['#viral', '#trending'],
            }
        return {}


# ═══════════════════════════════════════════════════════════
# Quick test/demo
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🔥 GOD MASTER MODE — AI Metadata Generator Test")

    gen = AIMetadataGenerator()

    # Test with script.json if available
    test_path = 'output/test_export/script.json'
    if os.path.exists(test_path):
        metadata = gen.generate_from_script(test_path)
        print("\n" + "=" * 60)
        print("📊 GENERATED METADATA")
        print("=" * 60)
        for platform, data in metadata.items():
            print(f"\n{platform.upper()}:")
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"  {key}: {', '.join(value)}")
                else:
                    preview = str(value)[:100]
                    print(f"  {key}: {preview}")
    else:
        # Legacy test
        metadata = gen.generate_all_metadata(
            video_topic="10 Mind-Blowing AI Tools",
            video_duration=45,
            niche="Technology"
        )
        for platform, data in metadata.items():
            print(f"\n{platform.upper()}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
