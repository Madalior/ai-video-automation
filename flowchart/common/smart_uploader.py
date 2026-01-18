"""
Smart Multi-Platform Uploader
Automatically uploads to appropriate platforms based on video duration
"""

import os
from moviepy.editor import VideoFileClip

class SmartUploader:
    """
    Smart uploader that selects platforms based on video type.
    
    Logic:
    - Short video (≤60s) → Upload to ALL 5 platforms
      (YouTube Shorts, TikTok, Instagram, Facebook, Twitter)
    
    - Long video (>60s) → Upload to YouTube & Facebook only
    """
    
    def __init__(self):
        self.short_video_threshold = 60  # seconds
        
        # Platform-specific settings
        self.platforms = {
            'youtube': {
                'enabled': True,
                'supports_shorts': True,
                'supports_long': True
            },
            'tiktok': {
                'enabled': True,
                'supports_shorts': True,
                'supports_long': False
            },
            'instagram': {
                'enabled': True,
                'supports_shorts': True,
                'supports_long': False
            },
            'facebook': {
                'enabled': True,
                'supports_shorts': True,
                'supports_long': True
            },
            'twitter': {
                'enabled': True,
                'supports_shorts': True,
                'supports_long': False
            }
        }
    
    def get_video_duration(self, video_path):
        """
        Get video duration in seconds.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Duration in seconds
        """
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            clip.close()
            return duration
        except Exception as e:
            print(f"[ERROR] Could not read video duration: {e}")
            return 0
    
    def is_short_video(self, video_path):
        """
        Check if video is a short (≤60 seconds).
        
        Args:
            video_path: Path to video file
        
        Returns:
            True if short video, False if long video
        """
        duration = self.get_video_duration(video_path)
        return duration <= self.short_video_threshold
    
    def get_target_platforms(self, video_path):
        """
        Determine which platforms to upload to based on video duration.
        
        Args:
            video_path: Path to video file
        
        Returns:
            List of platform names to upload to
        """
        is_short = self.is_short_video(video_path)
        duration = self.get_video_duration(video_path)
        
        print(f"📊 Video Analysis:")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Type: {'SHORT' if is_short else 'LONG'} video")
        print()
        
        target_platforms = []
        
        if is_short:
            # Short video → Upload to ALL platforms
            print("✅ SHORT VIDEO - Uploading to ALL 5 platforms:")
            for platform, settings in self.platforms.items():
                if settings['enabled'] and settings['supports_shorts']:
                    target_platforms.append(platform)
                    print(f"   ✓ {platform.capitalize()}")
        else:
            # Long video → YouTube + Facebook only
            print("✅ LONG VIDEO - Uploading to YouTube & Facebook only:")
            for platform, settings in self.platforms.items():
                if settings['enabled'] and settings['supports_long']:
                    target_platforms.append(platform)
                    print(f"   ✓ {platform.capitalize()}")
        
        print()
        return target_platforms
    
    def upload_to_all_platforms(self, video_path, metadata):
        """
        Upload video to appropriate platforms based on duration.
        
        Args:
            video_path: Path to video file
            metadata: Dict with title, description, tags, etc.
        
        Returns:
            Dict of upload results by platform
        """
        print("=" * 70)
        print("🚀 SMART MULTI-PLATFORM UPLOAD")
        print("=" * 70)
        print()
        
        # Determine target platforms
        platforms = self.get_target_platforms(video_path)
        
        results = {}
        
        # Upload to each platform
        for platform in platforms:
            print(f"📤 Uploading to {platform.capitalize()}...")
            
            try:
                if platform == 'youtube':
                    result = self.upload_to_youtube(video_path, metadata)
                elif platform == 'tiktok':
                    result = self.upload_to_tiktok(video_path, metadata)
                elif platform == 'instagram':
                    result = self.upload_to_instagram(video_path, metadata)
                elif platform == 'facebook':
                    result = self.upload_to_facebook(video_path, metadata)
                elif platform == 'twitter':
                    result = self.upload_to_twitter(video_path, metadata)
                
                results[platform] = {
                    'success': result,
                    'status': 'uploaded' if result else 'failed'
                }
                
                if result:
                    print(f"   ✅ {platform.capitalize()} upload successful!")
                else:
                    print(f"   ❌ {platform.capitalize()} upload failed")
            
            except Exception as e:
                print(f"   ❌ {platform.capitalize()} error: {e}")
                results[platform] = {
                    'success': False,
                    'status': 'error',
                    'error': str(e)
                }
            
            print()
        
        # Summary
        print("=" * 70)
        print("📊 UPLOAD SUMMARY")
        print("=" * 70)
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        print("=" * 70)
        print()
        
        return results
    
    def upload_to_youtube(self, video_path, metadata):
        """
        Upload to YouTube (Shorts or regular).
        
        Args:
            video_path: Video file path
            metadata: Upload metadata
        
        Returns:
            True if successful
        """
        # Check if it's a short
        is_short = self.is_short_video(video_path)
        
        if is_short:
            # Add #Shorts to title/description for YouTube Shorts
            metadata['title'] = metadata.get('title', '') + ' #Shorts'
            if 'tags' not in metadata:
                metadata['tags'] = []
            metadata['tags'].append('Shorts')
        
        # TODO: Implement actual YouTube upload using OAuth
        print(f"   [INFO] Would upload to YouTube {'Shorts' if is_short else ''}")
        print(f"   [INFO] Title: {metadata.get('title')}")
        
        # Placeholder - replace with actual implementation
        return True  # Simulated success
    
    def upload_to_tiktok(self, video_path, metadata):
        """
        Upload to TikTok.
        
        Args:
            video_path: Video file path
            metadata: Upload metadata
        
        Returns:
            True if successful
        """
        # TODO: Implement TikTok API upload
        print(f"   [INFO] Would upload to TikTok")
        print(f"   [INFO] Caption: {metadata.get('description', '')[:100]}")
        
        # Placeholder
        return True  # Simulated success
    
    def upload_to_instagram(self, video_path, metadata):
        """
        Upload to Instagram Reels.
        
        Args:
            video_path: Video file path
            metadata: Upload metadata
        
        Returns:
            True if successful
        """
        # TODO: Implement Instagram Graph API upload
        print(f"   [INFO] Would upload to Instagram Reels")
        print(f"   [INFO] Caption: {metadata.get('description', '')[:100]}")
        
        # Placeholder
        return True  # Simulated success
    
    def upload_to_facebook(self, video_path, metadata):
        """
        Upload to Facebook.
        
        Args:
            video_path: Video file path
            metadata: Upload metadata
        
        Returns:
            True if successful
        """
        # TODO: Implement Facebook Graph API upload
        print(f"   [INFO] Would upload to Facebook")
        print(f"   [INFO] Description: {metadata.get('description', '')[:100]}")
        
        # Placeholder
        return True  # Simulated success
    
    def upload_to_twitter(self, video_path, metadata):
        """
        Upload to Twitter/X.
        
        Args:
            video_path: Video file path
            metadata: Upload metadata
        
        Returns:
            True if successful
        """
        # TODO: Implement Twitter API v2 upload
        print(f"   [INFO] Would upload to Twitter/X")
        print(f"   [INFO] Tweet: {metadata.get('title', '')[:100]}")
        
        # Placeholder
        return True  # Simulated success


# Usage example
if __name__ == "__main__":
    uploader = SmartUploader()
    
    # Example 1: Short video (will upload to all 5 platforms)
    print("TEST 1: Short Video")
    print("-" * 70)
    
    short_metadata = {
        'title': '10 Amazing AI Tools!',
        'description': 'Check out these incredible AI tools that will change your life!',
        'tags': ['AI', 'technology', 'tools']
    }
    
    # Assuming you have a short video
    # results = uploader.upload_to_all_platforms(
    #     'output/final/short_video.mp4',
    #     short_metadata
    # )
    
    print("\n" * 2)
    
    # Example 2: Long video (will upload to YouTube & Facebook only)
    print("TEST 2: Long Video")
    print("-" * 70)
    
    long_metadata = {
        'title': 'Complete Guide to AI in 2025',
        'description': 'A comprehensive 10-minute guide to artificial intelligence.',
        'tags': ['AI', 'tutorial', 'guide']
    }
    
    # Assuming you have a long video
    # results = uploader.upload_to_all_platforms(
    #     'output/final/long_video.mp4',
    #     long_metadata
    # )
