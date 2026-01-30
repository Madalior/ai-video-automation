#!/usr/bin/env python3
"""
Parallel Info Director - 4x Faster Info Video Generation

Enables parallel processing for info/documentary videos:
- Parallel AI video generation (4 workers)
- Parallel stock footage fetching (concurrent API calls)
- Matches character pipeline speed

Based on character pipeline's parallel architecture.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelInfoDirector:
    """
    Parallel director for info content pipeline.
    Processes multiple scenes simultaneously for 4-8x speedup.
    """
    
    def __init__(self, num_workers=4, output_dir="output_info", proxy_manager=None):
        """
        Initialize parallel info director
        
        Args:
            num_workers: Number of parallel Chrome workers (default: 4)
            output_dir: Output directory for videos
            proxy_manager: Optional proxy manager for IP rotation
        """
        self.num_workers = num_workers
        self.output_dir = output_dir
        self.proxy_manager = proxy_manager
        
        print(f"[ParallelInfoDirector] Initialized with {num_workers} workers")
        print(f"[ParallelInfoDirector] Proxy enabled: {'YES' if proxy_manager else 'NO'}")
    
    def generate_ai_videos_parallel(self, scenes: List[Dict], use_veo3=True) -> List[str]:
        """
        Generate AI videos for multiple scenes in parallel
        
        Args:
            scenes: List of scene dictionaries with prompts
            use_veo3: If True, use Veo3; if False, use Dreamina
            
        Returns:
            List of generated video paths
        """
        print(f"\n[Parallel AI] Generating {len(scenes)} videos with {self.num_workers} workers...")
        
        # Prepare tasks
        tasks = []
        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            prompt = scene.get('video_script', scene.get('narration', ''))
            output_path = f"{self.output_dir}/videos/ai_scene_{scene_num}.mp4"
            
            tasks.append({
                'scene_number': scene_num,
                'prompt': prompt,
                'output_path': output_path,
                'worker_id': i % self.num_workers
            })
        
        # Execute in parallel
        video_paths = []
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {}
            
            for task in tasks:
                if use_veo3:
                    future = executor.submit(
                        self._generate_veo3_video,
                        task['prompt'],
                        task['output_path'],
                        task['worker_id']
                    )
                else:
                    future = executor.submit(
                        self._generate_dreamina_video,
                        task['prompt'],
                        task['output_path'],
                        task['worker_id']
                    )
                futures[future] = task
            
            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        video_paths.append(result)
                        print(f"   [OK] Scene {task['scene_number']} generated")
                except Exception as e:
                    print(f"   [X] Scene {task['scene_number']} failed: {e}")
        
        # Sort by scene number
        video_paths = sorted(video_paths,
                           key=lambda x: int(x.split('_')[-1].replace('.mp4', '')))
        
        print(f"[Parallel AI] Completed: {len(video_paths)}/{len(scenes)} videos")
        return video_paths
    
    def _generate_veo3_video(self, prompt: str, output_path: str, worker_id: int) -> Optional[str]:
        """Generate video using Veo3 with dedicated worker"""
        # Staggered launch
        launch_delay = worker_id * 10
        if launch_delay > 0:
            print(f"   [Worker {worker_id}] Waiting {launch_delay}s (staggered start)...")
            time.sleep(launch_delay)
        
        profile_path = os.path.abspath(f"chrome_data_info_veo_{worker_id}")
        
        try:
            from modules.generators.veo3_generator import Veo3Generator
            
            gen = Veo3Generator(headless=False, profile_path=profile_path, proxy_manager=self.proxy_manager)
            try:
                if gen.login():
                    success = gen.generate_video(prompt, None, output_path)
                    if success:
                        return output_path
            finally:
                gen.close()
        except Exception as e:
            print(f"   [Worker {worker_id}] Veo3 Error: {e}")
        
        return None
    
    def _generate_dreamina_video(self, prompt: str, output_path: str, worker_id: int) -> Optional[str]:
        """Generate video using Dreamina with dedicated worker"""
        # Staggered launch
        launch_delay = worker_id * 10
        if launch_delay > 0:
            print(f"   [Worker {worker_id}] Waiting {launch_delay}s (staggered start)...")
            time.sleep(launch_delay)
        
        profile_path = os.path.abspath(f"chrome_data_info_dreamina_{worker_id}")
        
        try:
            from flowchart.character.video_generator import DreaminaVideoGenerator
            
            gen = DreaminaVideoGenerator(headless=False, profile_path=profile_path, proxy_manager=self.proxy_manager)
            try:
                if gen.login():
                    success = gen.generate_video(prompt, None, output_path)
                    if success:
                        return output_path
            finally:
                gen.close()
        except Exception as e:
            print(f"   [Worker {worker_id}] Dreamina Error: {e}")
        
        return None
    
    def fetch_stock_footage_parallel(self, scenes: List[Dict]) -> List[str]:
        """
        Fetch stock footage for multiple scenes in parallel
        
        Args:
            scenes: List of scene dictionaries with keywords
            
        Returns:
            List of downloaded stock video paths
        """
        print(f"\n[Parallel Stock] Fetching for {len(scenes)} scenes with {self.num_workers} concurrent requests...")
        
        # Prepare tasks
        tasks = []
        for i, scene in enumerate(scenes):
            scene_num = scene.get('scene_number', i + 1)
            keywords = scene.get('keywords', [])
            if not keywords and 'narration' in scene:
                # Extract keywords from narration
                keywords = scene['narration'].split()[:3]
            
            output_path = f"{self.output_dir}/videos/stock_scene_{scene_num}.mp4"
            
            tasks.append({
                'scene_number': scene_num,
                'keywords': keywords,
                'output_path': output_path
            })
        
        # Execute in parallel (API calls are I/O bound, so more workers is fine)
        stock_paths = []
        with ThreadPoolExecutor(max_workers=self.num_workers * 2) as executor:  # 2x workers for API calls
            futures = {}
            
            for task in tasks:
                future = executor.submit(
                    self._fetch_single_stock,
                    task['keywords'],
                    task['output_path']
                )
                futures[future] = task
            
            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        stock_paths.append(result)
                        print(f"   [OK] Scene {task['scene_number']} stock fetched")
                except Exception as e:
                    print(f"   [X] Scene {task['scene_number']} failed: {e}")
        
        # Sort by scene number
        stock_paths = sorted(stock_paths,
                           key=lambda x: int(x.split('_')[-1].replace('.mp4', '')))
        
        print(f"[Parallel Stock] Completed: {len(stock_paths)}/{len(scenes)} videos")
        return stock_paths
    
    def _fetch_single_stock(self, keywords: List[str], output_path: str) -> Optional[str]:
        """Fetch single stock video from Pexels/Pixabay"""
        try:
            from flowchart.common.stock_media import StockMediaFetcher
            
            fetcher = StockMediaFetcher()
            
            # Try Pexels first
            query = " ".join(keywords) if keywords else "nature"
            videos = fetcher.search_videos(query, max_results=1)
            
            if videos:
                video_url = videos[0]['url']
                success = fetcher.download_video(video_url, output_path)
                if success:
                    return output_path
            
            # Fallback to Pixabay
            videos = fetcher.search_pixabay_videos(query, max_results=1)
            if videos:
                video_url = videos[0]['url']
                success = fetcher.download_video(video_url, output_path)
                if success:
                    return output_path
        
        except Exception as e:
            print(f"   Stock fetch error: {e}")
        
        return None
    
    def generate_hybrid_parallel(self, scenes: List[Dict], ai_ratio=0.4) -> List[str]:
        """
        Generate hybrid AI + Stock videos in parallel
        
        Args:
            scenes: List of scene dictionaries
            ai_ratio: Percentage of scenes to use AI (0.0-1.0)
            
        Returns:
            List of video paths (mixed AI and stock)
        """
        print(f"\n[Parallel Hybrid] Generating {len(scenes)} videos ({int(ai_ratio*100)}% AI, {int((1-ai_ratio)*100)}% Stock)...")
        
        # Classify scenes
        ai_scenes = []
        stock_scenes = []
        
        for i, scene in enumerate(scenes):
            # Smart classification based on content
            scene_type = scene.get('scene_type', '').lower()
            visual_desc = scene.get('visual_description', '').lower()
            
            # AI for: abstract, animated, fantasy, sci-fi, artistic
            if any(keyword in scene_type or keyword in visual_desc 
                   for keyword in ['abstract', 'fantasy', 'animated', 'sci-fi', 'artistic', 'conceptual']):
                ai_scenes.append(scene)
            # Stock for: real-world, documentary, nature, buildings, people
            elif any(keyword in scene_type or keyword in visual_desc
                     for keyword in ['real', 'documentary', 'nature', 'city', 'people', 'building']):
                stock_scenes.append(scene)
            # Fallback: alternate based on ratio
            else:
                if i < len(scenes) * ai_ratio:
                    ai_scenes.append(scene)
                else:
                    stock_scenes.append(scene)
        
        print(f"   AI scenes: {len(ai_scenes)}, Stock scenes: {len(stock_scenes)}")
        
        # Generate both in parallel (using ThreadPoolExecutor to coordinate)
        all_videos = []
        
        with ThreadPoolExecutor(max_workers=2) as coordinator:
            # Task 1: AI videos
            ai_future = coordinator.submit(
                self.generate_ai_videos_parallel,
                ai_scenes,
                use_veo3=True
            )
            
            # Task 2: Stock videos
            stock_future = coordinator.submit(
                self.fetch_stock_footage_parallel,
                stock_scenes
            )
            
            # Collect results
            ai_videos = ai_future.result()
            stock_videos = stock_future.result()
            
            all_videos.extend(ai_videos)
            all_videos.extend(stock_videos)
        
        # Sort by original scene order
        all_videos = sorted(all_videos,
                          key=lambda x: int(x.split('_')[-1].replace('.mp4', '')))
        
        print(f"[Parallel Hybrid] Completed: {len(all_videos)} total videos")
        return all_videos


if __name__ == "__main__":
    # Test the parallel director
    print("=== Testing Parallel Info Director ===\n")
    
    director = ParallelInfoDirector(num_workers=4)
    
    # Mock scenes
    test_scenes = [
        {'scene_number': 1, 'video_script': 'Amazing space nebula', 'scene_type': 'abstract'},
        {'scene_number': 2, 'video_script': 'City skyline at night', 'scene_type': 'real'},
        {'scene_number': 3, 'video_script': 'Ocean waves crashing', 'scene_type': 'nature'},
        {'scene_number': 4, 'video_script': 'Futuristic AI visualization', 'scene_type': 'abstract'},
    ]
    
    print("Test: Hybrid parallel generation")
    print(f"Scenes: {len(test_scenes)}")
    print(f"Workers: {director.num_workers}\n")
    
    # This would actually generate if modules are available
    print("[NOTE] This is a dry run. Actual generation requires AI/stock modules.")
