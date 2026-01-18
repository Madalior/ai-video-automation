#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              INFO VIDEO GENERATOR (Stock Footage)                 ║
║                                                                   ║
║  Fetches and manages stock footage for Info/Documentary niches   ║
║  NO AI video generation - uses Pexels/Pixabay stock videos       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import shutil
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class InfoVideoGenerator:
    """
    Video "generator" for INFO/DOCUMENTARY niches.
    
    Key differences from character-based DreaminaVideoGenerator:
    - Uses stock footage instead of AI generation
    - Fetches from Pexels and Pixabay APIs
    - Keyword-based video selection
    - No character consistency needed
    """
    
    def __init__(self, 
                 pexels_api_key: str = None,
                 pixabay_api_key: str = None,
                 output_dir: str = "output_info/stock"):
        
        self.pexels_api_key = pexels_api_key or os.getenv('PEXELS_API_KEY')
        self.pixabay_api_key = pixabay_api_key or os.getenv('PIXABAY_API_KEY')
        self.output_dir = output_dir
        self.cache_dir = "stock_media_cache"
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Import stock fetcher
        self._fetcher = None
        try:
            from ..stock_media import StockMediaFetcher
            self._fetcher_class = StockMediaFetcher
        except ImportError:
            try:
                from modules.stock_media import StockMediaFetcher
                self._fetcher_class = StockMediaFetcher
            except ImportError:
                self._fetcher_class = None
                print("[WARNING] Stock media fetcher not available")
    
    def _get_fetcher(self):
        """Lazy load stock fetcher"""
        if self._fetcher is None and self._fetcher_class:
            self._fetcher = self._fetcher_class(
                pexels_api_key=self.pexels_api_key,
                pixabay_api_key=self.pixabay_api_key
            )
        return self._fetcher
    
    def fetch_video(self,
                    keywords: List[str],
                    duration_range: Tuple[int, int] = (5, 15),
                    orientation: str = "landscape") -> Optional[str]:
        """
        Fetch a stock video matching keywords.
        
        Args:
            keywords: List of search keywords (tries each until success)
            duration_range: (min, max) duration in seconds
            orientation: 'landscape', 'portrait', or 'square'
        
        Returns:
            Path to downloaded video or None
        """
        fetcher = self._get_fetcher()
        if not fetcher:
            print("[X] Stock fetcher not available")
            return None
        
        for keyword in keywords:
            print(f"   Searching: '{keyword}'...", end=" ")
            
            video_path = fetcher.get_stock_video(
                keyword=keyword,
                duration_range=duration_range
            )
            
            if video_path and os.path.exists(video_path):
                print("OK")
                return video_path
            else:
                print("not found")
        
        return None
    
    def fetch_scene_videos(self, 
                           scenes: List[Dict],
                           duration_range: Tuple[int, int] = (5, 15)) -> List[str]:
        """
        Fetch stock videos for all scenes.
        
        Args:
            scenes: List of scene dicts with 'stock_keywords' field
            duration_range: Video duration range
        
        Returns:
            List of video paths (ordered by scene)
        """
        print(f"\n[INFO] Fetching stock videos for {len(scenes)} scenes...")
        
        video_paths = []
        
        for scene in scenes:
            scene_num = scene.get('scene_number', len(video_paths) + 1)
            keywords = scene.get('stock_keywords', ['technology'])
            
            # Ensure keywords is a list
            if isinstance(keywords, str):
                keywords = [keywords]
            
            print(f"\n   Scene {scene_num}:")
            
            video_path = self.fetch_video(keywords, duration_range)
            
            if video_path:
                # Copy to output with scene number
                dest_filename = f"scene_{scene_num}_{os.path.basename(video_path)}"
                dest_path = os.path.join(self.output_dir, dest_filename)
                
                shutil.copy(video_path, dest_path)
                video_paths.append(dest_path)
                print(f"   [OK] {dest_filename}")
            else:
                print(f"   [!] No video found for scene {scene_num}")
        
        print(f"\n[OK] Fetched {len(video_paths)}/{len(scenes)} videos")
        return video_paths
    
    def fetch_broll(self, 
                    topic: str, 
                    count: int = 5,
                    duration_range: Tuple[int, int] = (5, 10)) -> List[str]:
        """
        Fetch multiple B-roll videos for a topic.
        
        Args:
            topic: Main topic keyword
            count: Number of videos to fetch
            duration_range: Video duration range
        
        Returns:
            List of video paths
        """
        print(f"\n[INFO] Fetching {count} B-roll videos for: {topic}")
        
        # Generate related keywords
        related_keywords = [
            topic,
            f"{topic} background",
            f"{topic} abstract",
            f"{topic} technology",
            f"{topic} modern"
        ]
        
        videos = []
        fetcher = self._get_fetcher()
        
        if not fetcher:
            return videos
        
        for i in range(count):
            keyword = related_keywords[i % len(related_keywords)]
            print(f"   [{i+1}/{count}] Searching: '{keyword}'...", end=" ")
            
            video_path = fetcher.get_stock_video(
                keyword=keyword,
                duration_range=duration_range
            )
            
            if video_path:
                dest_path = os.path.join(self.output_dir, f"broll_{i+1}_{os.path.basename(video_path)}")
                shutil.copy(video_path, dest_path)
                videos.append(dest_path)
                print("OK")
            else:
                print("not found")
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n[OK] Fetched {len(videos)}/{count} B-roll videos")
        return videos
    
    def search_videos(self,
                      keyword: str,
                      per_page: int = 10,
                      orientation: str = "landscape") -> List[Dict]:
        """
        Search for videos without downloading.
        
        Args:
            keyword: Search keyword
            per_page: Number of results
            orientation: Video orientation
        
        Returns:
            List of video info dicts
        """
        fetcher = self._get_fetcher()
        if not fetcher:
            return []
        
        results = fetcher.search_pexels_videos(
            query=keyword,
            per_page=per_page,
            orientation=orientation
        )
        
        return results if results else []
    
    def get_video_info(self, video_path: str) -> Dict:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with duration, size, etc.
        """
        if not os.path.exists(video_path):
            return {}
        
        info = {
            'path': video_path,
            'filename': os.path.basename(video_path),
            'size_mb': os.path.getsize(video_path) / (1024 * 1024)
        }
        
        # Try to get duration with moviepy
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            info['duration'] = clip.duration
            info['fps'] = clip.fps
            info['resolution'] = f"{clip.w}x{clip.h}"
            clip.close()
        except:
            pass
        
        return info


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Info Video Generator (Stock)")
    parser.add_argument('--topic', type=str, required=True,
                       help='Topic to search for')
    parser.add_argument('--count', type=int, default=5,
                       help='Number of videos to fetch')
    parser.add_argument('--min-duration', type=int, default=5,
                       help='Minimum video duration')
    parser.add_argument('--max-duration', type=int, default=15,
                       help='Maximum video duration')
    
    args = parser.parse_args()
    
    generator = InfoVideoGenerator()
    videos = generator.fetch_broll(
        topic=args.topic,
        count=args.count,
        duration_range=(args.min_duration, args.max_duration)
    )
    
    print(f"\n[RESULT] Downloaded {len(videos)} videos:")
    for v in videos:
        print(f"   - {v}")
