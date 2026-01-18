"""
Video URL Analyzer - Niche Detection
Analyzes YouTube/video URLs to automatically detect niche and create similar content
"""

import re
import requests
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
from modules.llm_manager import LLMManager

class VideoURLAnalyzer:
    """
    Analyze video URLs to detect niche and extract insights
    """
    
    def __init__(self):
        self.llm = LLMManager()
    
    def analyze_url(self, video_url: str) -> Dict:
        """
        Analyze a video URL and detect its niche
        
        Args:
            video_url: YouTube or video platform URL
            
        Returns:
            {
                'niche': str,
                'topic': str,
                'style': str,
                'keywords': List[str],
                'suggested_titles': List[str]
            }
        """
        print(f"🔍 Analyzing video: {video_url}")
        
        # Step 1: Extract video ID and metadata
        metadata = self._extract_video_metadata(video_url)
        
        if not metadata:
            print("❌ Could not extract video metadata")
            return None
        
        print(f"   ✓ Title: {metadata.get('title', 'N/A')}")
        print(f"   ✓ Channel: {metadata.get('channel', 'N/A')}")
        
        # Step 2: Analyze with AI to detect niche
        analysis = self._analyze_with_ai(metadata)
        
        print(f"\n✅ Niche Analysis Complete:")
        print(f"   📁 Detected Niche: {analysis['niche']}")
        print(f"   🎯 Topic Category: {analysis['topic']}")
        print(f"   🎨 Style: {analysis['style']}")
        print(f"   🏷️  Keywords: {', '.join(analysis['keywords'][:5])}")
        
        return analysis
    
    def _extract_video_metadata(self, url: str) -> Optional[Dict]:
        """
        Extract video metadata from URL
        Supports: YouTube, TikTok, Instagram
        """
        # Detect platform
        if 'youtube.com' in url or 'youtu.be' in url:
            return self._get_youtube_metadata(url)
        elif 'tiktok.com' in url:
            return self._get_tiktok_metadata(url)
        elif 'instagram.com' in url:
            return self._get_instagram_metadata(url)
        else:
            print("⚠️  Platform not supported, using URL-based analysis")
            return {'url': url, 'title': url, 'channel': 'Unknown'}
    
    def _get_youtube_metadata(self, url: str) -> Dict:
        """
        Get YouTube video metadata without API
        Uses oEmbed and scraping
        """
        try:
            # Extract video ID
            video_id = self._extract_youtube_id(url)
            
            if not video_id:
                return None
            
            # Method 1: oEmbed (no API key needed)
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            
            response = requests.get(oembed_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'video_id': video_id,
                    'title': data.get('title', ''),
                    'channel': data.get('author_name', ''),
                    'url': url,
                    'thumbnail': data.get('thumbnail_url', '')
                }
            
            # Method 2: Fallback to basic info
            return {
                'video_id': video_id,
                'title': f"YouTube video {video_id}",
                'channel': 'Unknown',
                'url': url
            }
            
        except Exception as e:
            print(f"⚠️  Error fetching YouTube metadata: {e}")
            return {'url': url, 'title': url}
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats"""
        # youtube.com/watch?v=VIDEO_ID
        if 'youtube.com/watch' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get('v', [None])[0]
        
        # youtu.be/VIDEO_ID
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0]
        
        # youtube.com/embed/VIDEO_ID
        if 'youtube.com/embed/' in url:
            return url.split('embed/')[-1].split('?')[0]
        
        # youtube.com/shorts/VIDEO_ID
        if 'youtube.com/shorts/' in url:
            return url.split('shorts/')[-1].split('?')[0]
        
        return None
    
    def _get_tiktok_metadata(self, url: str) -> Dict:
        """Get TikTok video metadata"""
        # TikTok oEmbed
        try:
            oembed_url = f"https://www.tiktok.com/oembed?url={url}"
            response = requests.get(oembed_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', ''),
                    'channel': data.get('author_name', ''),
                    'url': url,
                    'thumbnail': data.get('thumbnail_url', '')
                }
        except:
            pass
        
        return {'url': url, 'title': 'TikTok video'}
    
    def _get_instagram_metadata(self, url: str) -> Dict:
        """Get Instagram video metadata"""
        # Instagram oEmbed
        try:
            oembed_url = f"https://api.instagram.com/oembed?url={url}"
            response = requests.get(oembed_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', ''),
                    'channel': data.get('author_name', ''),
                    'url': url,
                    'thumbnail': data.get('thumbnail_url', '')
                }
        except:
            pass
        
        return {'url': url, 'title': 'Instagram video'}
    
    def _analyze_with_ai(self, metadata: Dict) -> Dict:
        """
        Use Gemini AI to analyze video and detect niche
        """
        prompt = f"""Analyze this video and determine its niche, topic, and style.

Video Information:
- Title: {metadata.get('title', 'N/A')}
- Channel: {metadata.get('channel', 'N/A')}
- URL: {metadata.get('url', 'N/A')}

Based on the title and channel, provide a detailed analysis in JSON format:

{{
    "niche": "The primary niche/category (e.g., ASMR, Tech Reviews, Travel, Cooking, Gaming)",
    "topic": "Specific topic within the niche",
    "style": "Content style (e.g., Tutorial, Review, Vlog, Satisfying, Educational)",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "suggested_titles": [
        "Similar video title idea 1",
        "Similar video title idea 2",
        "Similar video title idea 3"
    ],
    "content_type": "Type of content (Short-form, Long-form, Tutorial, Compilation)",
    "target_audience": "Who this content is for",
    "mood": "Content mood/vibe (Relaxing, Energetic, Informative, etc.)"
}}

Provide ONLY the JSON, no other text."""

        try:
            response = self.llm.generate(prompt)
            
            # Extract JSON from response
            import json
            
            # Try to find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                analysis = json.loads(json_str)
                return analysis
            else:
                # Fallback parsing
                return self._fallback_analysis(metadata)
                
        except Exception as e:
            print(f"⚠️  AI analysis failed: {e}, using fallback")
            return self._fallback_analysis(metadata)
    
    def _fallback_analysis(self, metadata: Dict) -> Dict:
        """
        Fallback niche detection using simple rules
        """
        title = metadata.get('title', '').lower()
        
        # Niche detection rules
        if any(word in title for word in ['asmr', 'satisfying', 'relaxing', 'sleep', 'tingles']):
            niche = 'ASMR'
            style = 'Satisfying'
        elif any(word in title for word in ['review', 'unboxing', 'tech', 'gadget', 'iphone', 'laptop']):
            niche = 'Tech Reviews'
            style = 'Review'
        elif any(word in title for word in ['travel', 'vlog', 'adventure', 'explore', 'journey']):
            niche = 'Travel'
            style = 'Vlog'
        elif any(word in title for word in ['recipe', 'cooking', 'food', 'baking', 'kitchen']):
            niche = 'Cooking'
            style = 'Tutorial'
        elif any(word in title for word in ['gaming', 'gameplay', 'walkthrough', 'lets play']):
            niche = 'Gaming'
            style = 'Gameplay'
        elif any(word in title for word in ['tutorial', 'how to', 'guide', 'learn']):
            niche = 'Educational'
            style = 'Tutorial'
        else:
            niche = 'General'
            style = 'Content'
        
        keywords = [word for word in title.split() if len(word) > 3][:5]
        
        return {
            'niche': niche,
            'topic': title[:50],
            'style': style,
            'keywords': keywords,
            'suggested_titles': [
                f"{niche} - Similar Content 1",
                f"{niche} - Similar Content 2",
                f"{niche} - Similar Content 3"
            ],
            'content_type': 'Short-form',
            'target_audience': 'General',
            'mood': 'Engaging'
        }


# Example usage
if __name__ == "__main__":
    analyzer = VideoURLAnalyzer()
    
    # Test with various URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/xyz123"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        result = analyzer.analyze_url(url)
        
        if result:
            print(f"\nDetected Niche: {result['niche']}")
            print(f"Topic: {result['topic']}")
            print(f"Style: {result['style']}")
            print(f"Keywords: {', '.join(result['keywords'])}")
            print(f"\nSuggested video titles:")
            for i, title in enumerate(result['suggested_titles'], 1):
                print(f"  {i}. {title}")
        
        print('='*60)
