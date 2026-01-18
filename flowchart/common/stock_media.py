"""
Stock Media Fetcher
Downloads stock videos and images from Pexels and Pixabay
"""

import requests
import os
from urllib.parse import urlencode

class StockMediaFetcher:
    """Fetch stock videos and images from free APIs."""
    
    def __init__(self, pexels_api_key=None, pixabay_api_key=None):
        """
        Initialize with API keys.
        
        Get keys from:
        - Pexels: https://www.pexels.com/api/
        - Pixabay: https://pixabay.com/api/docs/
        """
        self.pexels_key = pexels_api_key or os.getenv('PEXELS_API_KEY')
        self.pixabay_key = pixabay_api_key or os.getenv('PIXABAY_API_KEY')
        
        self.pexels_base = "https://api.pexels.com/v1"
        self.pexels_video_base = "https://api.pexels.com/videos"
        self.pixabay_base = "https://pixabay.com/api/"
        
        self.cache_dir = "stock_media_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def search_pexels_photos(self, query, per_page=10, orientation=None):
        """
        Search Pexels for photos.
        
        Args:
            query: Search keyword
            per_page: Results per page (max 80)
            orientation: 'landscape', 'portrait', or 'square'
        
        Returns:
            List of photo URLs
        """
        if not self.pexels_key:
            print("[ERROR] Pexels API key not set")
            return []
        
        params = {
            'query': query,
            'per_page': min(per_page, 80)
        }
        
        if orientation:
            params['orientation'] = orientation
        
        headers = {
            'Authorization': self.pexels_key
        }
        
        try:
            response = requests.get(
                f"{self.pexels_base}/search?{urlencode(params)}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                photos = []
                
                for photo in data.get('photos', []):
                    photos.append({
                        'id': photo['id'],
                        'url': photo['src']['large'],  # or 'original', 'large2x'
                        'photographer': photo['photographer'],
                        'source': 'pexels'
                    })
                
                print(f"[SUCCESS] Found {len(photos)} photos from Pexels")
                return photos
            else:
                print(f"[ERROR] Pexels API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Pexels request failed: {e}")
            return []
    
    def search_pexels_videos(self, query, per_page=10, orientation=None):
        """
        Search Pexels for videos.
        
        Args:
            query: Search keyword
            per_page: Results per page (max 80)
            orientation: 'landscape', 'portrait', or 'square'
        
        Returns:
            List of video URLs
        """
        if not self.pexels_key:
            print("[ERROR] Pexels API key not set")
            return []
        
        params = {
            'query': query,
            'per_page': min(per_page, 80)
        }
        
        if orientation:
            params['orientation'] = orientation
        
        headers = {
            'Authorization': self.pexels_key
        }
        
        try:
            response = requests.get(
                f"{self.pexels_video_base}/search?{urlencode(params)}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                videos = []
                
                for video in data.get('videos', []):
                    # Get HD video file
                    video_files = video.get('video_files', [])
                    hd_file = None
                    
                    for vf in video_files:
                        if vf.get('quality') == 'hd':
                            hd_file = vf
                            break
                    
                    if not hd_file and video_files:
                        hd_file = video_files[0]  # Fallback to first
                    
                    if hd_file:
                        videos.append({
                            'id': video['id'],
                            'url': hd_file['link'],
                            'duration': video.get('duration', 0),
                            'source': 'pexels'
                        })
                
                print(f"[SUCCESS] Found {len(videos)} videos from Pexels")
                return videos
            else:
                print(f"[ERROR] Pexels API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Pexels request failed: {e}")
            return []
    
    def search_pixabay(self, query, image_type='all', per_page=20):
        """
        Search Pixabay for images/videos.
        
        Args:
            query: Search keyword
            image_type: 'all', 'photo', 'illustration', 'vector'
            per_page: Results per page (max 200)
        
        Returns:
            List of media URLs
        """
        if not self.pixabay_key:
            print("[ERROR] Pixabay API key not set")
            return []
        
        params = {
            'key': self.pixabay_key,
            'q': query,
            'image_type': image_type,
            'per_page': min(per_page, 200)
        }
        
        try:
            response = requests.get(
                f"{self.pixabay_base}?{urlencode(params)}"
            )
            
            if response.status_code == 200:
                data = response.json()
                media = []
                
                for item in data.get('hits', []):
                    media.append({
                        'id': item['id'],
                        'url': item['largeImageURL'],
                        'source': 'pixabay'
                    })
                
                print(f"[SUCCESS] Found {len(media)} items from Pixabay")
                return media
            else:
                print(f"[ERROR] Pixabay API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] Pixabay request failed: {e}")
            return []
    
    def download_media(self, url, filename):
        """
        Download media file from URL.
        
        Args:
            url: Media URL
            filename: Local filename to save
        
        Returns:
            Local file path or None
        """
        filepath = os.path.join(self.cache_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(filepath):
            print(f"[INFO] Using cached: {filename}")
            return filepath
        
        try:
            print(f"[INFO] Downloading: {filename}")
            response = requests.get(url, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"[SUCCESS] Downloaded: {filepath}")
                return filepath
            else:
                print(f"[ERROR] Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Download error: {e}")
            return None
    
    def get_stock_video(self, keyword, duration_range=(5, 15)):
        """
        Get stock video matching keyword and duration.
        
        Args:
            keyword: Search term
            duration_range: (min, max) seconds
        
        Returns:
            Local file path or None
        """
        print(f"[INFO] Fetching stock video for: {keyword}")
        
        # Try Pexels first
        videos = self.search_pexels_videos(keyword, per_page=10)
        
        if not videos:
            print("[INFO] No videos from Pexels, trying Pixabay...")
            # Pixabay doesn't have videos in free tier
            return None
        
        # Filter by duration
        suitable = [v for v in videos 
                    if duration_range[0] <= v['duration'] <= duration_range[1]]
        
        if not suitable:
            suitable = videos  # Use any if no perfect match
        
        # Download first suitable video
        if suitable:
            video = suitable[0]
            filename = f"{keyword.replace(' ', '_')}_{video['id']}.mp4"
            return self.download_media(video['url'], filename)
        
        return None
    
    def get_stock_image(self, keyword, orientation='landscape'):
        """
        Get stock image matching keyword.
        
        Args:
            keyword: Search term
            orientation: 'landscape', 'portrait', 'square'
        
        Returns:
            Local file path or None
        """
        print(f"[INFO] Fetching stock image for: {keyword}")
        
        # Try Pexels first
        photos = self.search_pexels_photos(keyword, per_page=5, orientation=orientation)
        
        if not photos:
            print("[INFO] No photos from Pexels, trying Pixabay...")
            photos = self.search_pixabay(keyword, per_page=5)
        
        if photos:
            photo = photos[0]
            filename = f"{keyword.replace(' ', '_')}_{photo['id']}.jpg"
            return self.download_media(photo['url'], filename)
        
        return None


# Usage example
if __name__ == "__main__":
    # Set your API keys
    fetcher = StockMediaFetcher(
        pexels_api_key="YOUR_PEXELS_KEY",
        pixabay_api_key="YOUR_PIXABAY_KEY"
    )
    
    # Get stock video
    video = fetcher.get_stock_video("ocean", duration_range=(10, 20))
    print(f"Video: {video}")
    
    # Get stock image
    image = fetcher.get_stock_image("sunset")
    print(f"Image: {image}")
