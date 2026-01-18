"""
AI Metadata Generator - Platform-Optimized Titles & Descriptions
Uses Gemini AI to generate high-reach metadata for each platform
"""

import os
import google.generativeai as genai

class AIMetadataGenerator:
    """
    Generate platform-specific optimized metadata using AI.
    
    Creates:
    - Titles/captions optimized for each platform
    - Descriptions/text
    - Hashtags
    - Tags/keywords
    
    Optimized for maximum reach and engagement!
    """
    
    def __init__(self, gemini_api_key=None):
        """Initialize with Gemini API key."""
        self.api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model
        else:
            print("[WARNING] No Gemini API key - using fallback metadata")
            self.model = None
        
        # Platform-specific best practices
        self.platform_rules = {
            'youtube': {
                'title_max': 100,
                'description_max': 5000,
                'tags_max': 500,
                'hashtags_count': 3,
                'focus': 'SEO keywords, searchability, watch time'
            },
            'tiktok': {
                'caption_max': 150,
                'hashtags_count': 5,
                'focus': 'trending hashtags, hooks, viral potential'
            },
            'instagram': {
                'caption_max': 2200,
                'hashtags_count': 10,
                'focus': 'engagement, community, visual storytelling'
            },
            'facebook': {
                'description_max': 63206,
                'hashtags_count': 3,
                'focus': 'shareability, emotional connection, longer text'
            },
            'twitter': {
                'tweet_max': 280,
                'hashtags_count': 3,
                'focus': 'concise, newsworthy, trending topics'
            }
        }
    
    def generate_all_metadata(self, video_topic, video_duration, niche="General"):
        """
        Generate optimized metadata for ALL platforms.
        
        Args:
            video_topic: Main topic/idea of video
            video_duration: Duration in seconds
            niche: Content niche (Tech, Gaming, Education, etc.)
        
        Returns:
            Dict with metadata for each platform
        """
        print(f"🤖 Generating AI-optimized metadata...")
        print(f"   Topic: {video_topic}")
        print(f"   Duration: {video_duration}s")
        print(f"   Niche: {niche}")
        print()
        
        metadata = {}
        
        # Determine video type
        is_short = video_duration <= 60
        video_type = "Short" if is_short else "Long"
        
        # Generate for each platform
        platforms = ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter']
        
        for platform in platforms:
            print(f"📝 Generating {platform.capitalize()} metadata...")
            metadata[platform] = self.generate_platform_metadata(
                platform=platform,
                topic=video_topic,
                niche=niche,
                is_short=is_short
            )
            print(f"   ✅ Done!")
        
        print()
        print("✅ All metadata generated!")
        return metadata
    
    def generate_platform_metadata(self, platform, topic, niche, is_short):
        """
        Generate optimized metadata for specific platform.
        
        Args:
            platform: Platform name
            topic: Video topic
            niche: Content niche
            is_short: True if short-form video
        
        Returns:
            Dict with platform-specific metadata
        """
        if not self.model:
            return self._generate_fallback_metadata(platform, topic, is_short)
        
        rules = self.platform_rules.get(platform, {})
        
        # Create platform-specific prompts
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
        """Generate YouTube-optimized metadata."""
        video_type = "YouTube Short" if is_short else "YouTube video"
        
        # Viral title formulas and power words
        viral_formulas = [
            "The #1 [Topic] Nobody Tells You About",
            "[Number] Secrets About [Topic] That...",
            "I Tried [Topic] For 30 Days - Here's What Happened",
            "Why Everyone Is Wrong About [Topic]",
            "[Topic] - This Changed EVERYTHING",
            "You Won't Believe What [Topic] Can Do"
        ]
        
        power_words = "SHOCKING, INSANE, UNBELIEVABLE, SECRET, PROVEN, EXPOSED, GENIUS, MUST SEE, VIRAL"
        
        prompt = f"""
        Create high-performing {video_type} metadata optimized for YouTube algorithm and maximum CTR.
        
        Topic: {topic}
        Niche: {niche}
        
        VIRAL TITLE FORMULAS TO USE:
        {chr(10).join(['- ' + f for f in viral_formulas])}
        
        POWER WORDS (use 1-2): {power_words}
        
        CTR OPTIMIZATION TECHNIQUES:
        - Use CAPS for 1-2 words for emphasis
        - Include numbers when possible
        - Create curiosity gap (make them want to click)
        - Add brackets or parentheses: "(Works in 2025)"
        - Use emojis sparingly: 🔥 💯 ⚡
        
        Generate:
        1. Title (max {rules['title_max']} chars, MUST be clickable and curiosity-inducing)
        2. Description (SEO-optimized, include keywords, timestamps, 2-3 CTAs)
        3. Tags (10-15 relevant tags, mix of broad and specific)
        4. Hashtags ({rules['hashtags_count']} trending hashtags)
        
        Focus: {rules['focus']}
        Goal: 10-14% CTR (vs 4-6% baseline)
        
        Format your response as:
        TITLE: [your viral title here]
        DESCRIPTION: [your SEO description here]
        TAGS: tag1, tag2, tag3, ...
        HASHTAGS: #hashtag1 #hashtag2 #hashtag3
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_youtube_response(response.text, is_short)
        except Exception as e:
            print(f"   [ERROR] AI generation failed: {e}")
            return self._generate_fallback_metadata('youtube', topic, is_short)
    
    def _generate_tiktok_metadata(self, topic, niche, rules):
        """Generate TikTok-optimized metadata."""
        prompt = f"""
        Create viral TikTok caption optimized for maximum reach and engagement.
        
        Topic: {topic}
        Niche: {niche}
        
        Generate:
        1. Caption (max {rules['caption_max']} chars, must have hook, engaging, conversational)
        2. Hashtags ({rules['hashtags_count']} trending + niche-specific hashtags)
        
        Focus: {rules['focus']}
        Use trending phrases and hooks that make people stop scrolling!
        
        Format your response as:
        CAPTION: [your caption here]
        HASHTAGS: #hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_tiktok_response(response.text)
        except Exception as e:
            print(f"   [ERROR] AI generation failed: {e}")
            return self._generate_fallback_metadata('tiktok', topic, True)
    
    def _generate_instagram_metadata(self, topic, niche, rules):
        """Generate Instagram-optimized metadata."""
        prompt = f"""
        Create engaging Instagram Reels caption optimized for discovery and engagement.
        
        Topic: {topic}
        Niche: {niche}
        
        Generate:
        1. Caption (engaging, storytelling, conversational, ask questions)
        2. Hashtags ({rules['hashtags_count']} mix of trending + niche + branded hashtags)
        
        Focus: {rules['focus']}
        Make it relatable and encourage comments!
        
        Format your response as:
        CAPTION: [your caption here]
        HASHTAGS: #hashtag1 #hashtag2 ... #{rules['hashtags_count']}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_instagram_response(response.text)
        except Exception as e:
            print(f"   [ERROR] AI generation failed: {e}")
            return self._generate_fallback_metadata('instagram', topic, True)
    
    def _generate_facebook_metadata(self, topic, niche, rules):
        """Generate Facebook-optimized metadata."""
        prompt = f"""
        Create shareable Facebook post optimized for engagement and shares.
        
        Topic: {topic}
        Niche: {niche}
        
        Generate:
        1. Description (emotional, shareable, longer form, include question/call-to-action)
        2. Hashtags ({rules['hashtags_count']} hashtags, optional on Facebook)
        
        Focus: {rules['focus']}
        Make people want to share with friends!
        
        Format your response as:
        DESCRIPTION: [your description here]
        HASHTAGS: #hashtag1 #hashtag2 #hashtag3
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_facebook_response(response.text)
        except Exception as e:
            print(f"   [ERROR] AI generation failed: {e}")
            return self._generate_fallback_metadata('facebook', topic, True)
    
    def _generate_twitter_metadata(self, topic, niche, rules):
        """Generate Twitter-optimized metadata."""
        prompt = f"""
        Create concise, engaging tweet optimized for retweets and engagement.
        
        Topic: {topic}
        Niche: {niche}
        
        Generate:
        1. Tweet (max {rules['tweet_max']} chars, punchy, newsworthy, include hook)
        2. Hashtags ({rules['hashtags_count']} trending hashtags)
        
        Focus: {rules['focus']}
        Make it tweetable and conversation-starting!
        
        Format your response as:
        TWEET: [your tweet here]
        HASHTAGS: #hashtag1 #hashtag2 #hashtag3
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_twitter_response(response.text)
        except Exception as e:
            print(f"   [ERROR] AI generation failed: {e}")
            return self._generate_fallback_metadata('twitter', topic, True)
    
    def _parse_youtube_response(self, text, is_short):
        """Parse YouTube metadata from AI response."""
        lines = text.split('\n')
        metadata = {
            'title': '',
            'description': '',
            'tags': [],
            'hashtags': []
        }
        
        for line in lines:
            if line.startswith('TITLE:'):
                metadata['title'] = line.replace('TITLE:', '').strip()
                if is_short and '#Shorts' not in metadata['title']:
                    metadata['title'] += ' #Shorts'
            elif line.startswith('DESCRIPTION:'):
                metadata['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('TAGS:'):
                tags_str = line.replace('TAGS:', '').strip()
                metadata['tags'] = [t.strip() for t in tags_str.split(',')]
            elif line.startswith('HASHTAGS:'):
                hashtags_str = line.replace('HASHTAGS:', '').strip()
                metadata['hashtags'] = hashtags_str.split()
        
        return metadata
    
    def _parse_tiktok_response(self, text):
        """Parse TikTok metadata from AI response."""
        lines = text.split('\n')
        metadata = {
            'caption': '',
            'hashtags': []
        }
        
        for line in lines:
            if line.startswith('CAPTION:'):
                metadata['caption'] = line.replace('CAPTION:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_str = line.replace('HASHTAGS:', '').strip()
                metadata['hashtags'] = hashtags_str.split()
        
        return metadata
    
    def _parse_instagram_response(self, text):
        """Parse Instagram metadata from AI response."""
        lines = text.split('\n')
        metadata = {
            'caption': '',
            'hashtags': []
        }
        
        for line in lines:
            if line.startswith('CAPTION:'):
                metadata['caption'] = line.replace('CAPTION:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_str = line.replace('HASHTAGS:', '').strip()
                metadata['hashtags'] = hashtags_str.split()
        
        return metadata
    
    def _parse_facebook_response(self, text):
        """Parse Facebook metadata from AI response."""
        lines = text.split('\n')
        metadata = {
            'description': '',
            'hashtags': []
        }
        
        for line in lines:
            if line.startswith('DESCRIPTION:'):
                metadata['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_str = line.replace('HASHTAGS:', '').strip()
                metadata['hashtags'] = hashtags_str.split()
        
        return metadata
    
    def _parse_twitter_response(self, text):
        """Parse Twitter metadata from AI response."""
        lines = text.split('\n')
        metadata = {
            'tweet': '',
            'hashtags': []
        }
        
        for line in lines:
            if line.startswith('TWEET:'):
                metadata['tweet'] = line.replace('TWEET:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags_str = line.replace('HASHTAGS:', '').strip()
                metadata['hashtags'] = hashtags_str.split()
        
        return metadata
    
    def _generate_fallback_metadata(self, platform, topic, is_short):
        """Generate basic metadata when AI is not available."""
        if platform == 'youtube':
            return {
                'title': f"{topic}{'#Shorts' if is_short else ''}",
                'description': f"Watch this video about {topic}!",
                'tags': [topic, 'viral', 'trending'],
                'hashtags': ['#viral', '#trending']
            }
        elif platform == 'tiktok':
            return {
                'caption': f"Check out {topic}! 🔥",
                'hashtags': ['#fyp', '#viral', '#trending']
            }
        elif platform == 'instagram':
            return {
                'caption': f"Amazing content about {topic}! ✨",
                'hashtags': ['#viral', '#trending', '#reels']
            }
        elif platform == 'facebook':
            return {
                'description': f"Check out this video about {topic}!",
                'hashtags': ['#viral']
            }
        elif platform == 'twitter':
            return {
                'tweet': f"Must-see: {topic}!",
                'hashtags': ['#viral', '#trending']
            }


# Test/Demo
if __name__ == "__main__":
    # Set API key
    os.environ['GEMINI_API_KEY'] = 'AIzaSyALy_4CeWDzrkeunWdIa-UHKWk71-fwHiw'
    
    generator = AIMetadataGenerator()
    
    # Generate metadata for all platforms
    metadata = generator.generate_all_metadata(
        video_topic="10 Mind-Blowing AI Tools You Need to Try",
        video_duration=45,  # Short video
        niche="Technology"
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 GENERATED METADATA")
    print("=" * 70)
    
    for platform, data in metadata.items():
        print(f"\n{platform.upper()}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
