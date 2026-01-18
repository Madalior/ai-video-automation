"""
URL-to-Video Feature
Input a video URL → Analyze → Create similar video
"""

import re
import requests
from urllib.parse import urlparse, parse_qs
from modules.llm_manager import LLMManager

class VideoAnalyzer:
    """Analyzes video from URL and extracts concept for recreation."""
    
    def __init__(self):
        self.llm = LLMManager()
    
    def extract_youtube_id(self, url):
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_metadata(self, url):
        """Get video title, description from URL."""
        video_id = self.extract_youtube_id(url)
        if not video_id:
            return None
        
        try:
            # Use YouTube oEmbed API (no API key needed!)
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'video_id': video_id,
                    'title': data.get('title', ''),
                    'author': data.get('author_name', ''),
                    'thumbnail': data.get('thumbnail_url', ''),
                    'url': url
                }
        except Exception as e:
            print(f"[ERROR] Failed to get metadata: {e}")
        
        return None
    
    def analyze_video_concept(self, metadata):
        """Use AI to analyze video and extract recreation concept."""
        if not metadata:
            return None
        
        prompt = f"""
        Analyze this YouTube video and create a detailed recreation plan:
        
        Title: {metadata['title']}
        Channel: {metadata['author']}
        
        Based on the title, provide:
        1. Main topic/niche
        2. Video concept (what makes it interesting)
        3. Target audience
        4. Key elements to recreate
        5. Suggested improvements or variations
        
        Format as JSON:
        {{
            "niche": "category name",
            "concept": "main idea",
            "hook": "attention-grabbing opening",
            "audience": "target viewers",
            "key_elements": ["element1", "element2", "element3"],
            "improvements": ["idea1", "idea2"]
        }}
        """
        
        response = self.llm.generate(prompt)
        
        try:
            import json
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                concept = json.loads(json_match.group(0))
                return concept
        except:
            # Fallback: simple extraction
            return {
                'niche': 'General',
                'concept': metadata['title'],
                'hook': f"Inspired by: {metadata['title']}",
                'audience': 'General audience',
                'key_elements': ['Engaging visuals', 'Clear narration'],
                'improvements': ['Better graphics', 'Unique perspective']
            }
        
        return None
    
    def create_video_idea(self, url):
        """Main method: URL → Video Idea."""
        print(f"[INFO] Analyzing video: {url}")
        
        # Step 1: Get metadata
        metadata = self.get_video_metadata(url)
        if not metadata:
            print("[ERROR] Could not extract video metadata")
            return None
        
        print(f"[SUCCESS] Found video: {metadata['title']}")
        print(f"[INFO] Channel: {metadata['author']}")
        
        # Step 2: Analyze concept
        concept = self.analyze_video_concept(metadata)
        if not concept:
            print("[ERROR] Could not analyze video concept")
            return None
        
        print(f"[SUCCESS] Analyzed niche: {concept['niche']}")
        print(f"[SUCCESS] Core concept: {concept['concept']}")
        
        # Step 3: Create video idea
        video_idea = f"{concept['hook']} - {concept['concept']}"
        
        return {
            'source_url': url,
            'source_title': metadata['title'],
            'niche': concept['niche'],
            'video_idea': video_idea,
            'concept': concept,
            'metadata': metadata
        }


# Usage example
if __name__ == "__main__":
    analyzer = VideoAnalyzer()
    
    # Example URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ"
    ]
    
    for url in test_urls:
        result = analyzer.create_video_idea(url)
        if result:
            print("\n" + "="*50)
            print(f"Source: {result['source_title']}")
            print(f"Niche: {result['niche']}")
            print(f"New Idea: {result['video_idea']}")
            print("="*50)
