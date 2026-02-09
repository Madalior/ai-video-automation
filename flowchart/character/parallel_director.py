import time
import os
from typing import Dict, List
from flowchart.character.character_video_manager import CharacterVideoManager
from flowchart.character.image_generator import MultiDreaminaGenerator
from flowchart.character.video_generator import MultiVeo3Generator

class ParallelDirector(CharacterVideoManager):
    """
    Parallel version of CharacterVideoManager.
    Uses multi-worker generators to speed up production.
    """
    
    def __init__(self, output_dir: str = "output/parallel_videos", headless: bool = False, num_workers: int = 6):
        super().__init__(output_dir, headless)
        self.num_workers = num_workers
        self._multi_img_gen = None
        self._multi_video_gen = None
        
        print(f"[PARALLEL DIRECTOR] Initialized with {num_workers} workers")

    @property
    def image_generator(self) -> MultiDreaminaGenerator:
        """Lazy load multi-worker image generator."""
        if self._multi_img_gen is None:
            # Distribute workers: 2 image workers vs 4 video workers roughly
            # Default logic: 1/3 for images (min 1)
            img_workers = max(1, self.num_workers // 3)
            self._multi_img_gen = MultiDreaminaGenerator(num_workers=img_workers, headless=self.headless)
            print(f"[PARALLEL DIRECTOR] Multi-Image Generator loaded ({img_workers} workers)")
        return self._multi_img_gen
    
    @property
    def video_generator(self) -> MultiVeo3Generator:
        """Lazy load multi-worker video generator."""
        if self._multi_video_gen is None:
            # Distribute workers: remaining for videos
            img_workers = max(1, self.num_workers // 3)
            vid_workers = self.num_workers - img_workers
            self._multi_video_gen = MultiVeo3Generator(num_workers=vid_workers, headless=self.headless)
            print(f"[PARALLEL DIRECTOR] Multi-Video Generator loaded ({vid_workers} workers)")
        return self._multi_video_gen

    def _generate_images(self, script_data: Dict, project_id: str) -> List[Dict]:
        """Parallel image generation."""
        print(f"\n[PARALLEL] Starting Batch Image Generation...")
        
        scenes = script_data['scenes']
        tasks = []
        
        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', idx)
            character_desc = scene.get('character_description', '')
            background = scene.get('background', '')
            prompt = f"{character_desc}, {background}"
            
            image_filename = f"{project_id}_scene{scene_num:02d}_reference.png"
            image_path = os.path.join(self.dirs['images'], image_filename)
            
            tasks.append({
                'prompt': prompt,
                'output_path': image_path,
                'scene_number': scene_num, # Metadata for mapping back
                'character_name': scene.get('character_name', 'Unknown')
            })
            
        # Execute batch
        batch_results = self.image_generator.generate_batch(tasks)
        
        # Format results to match parent class expectations
        formatted_results = []
        for res in batch_results:
            task = res['task']
            success = res['status'] == 'success'
            formatted_results.append({
                'scene_number': task['scene_number'],
                'character_name': task['character_name'],
                'prompt': task['prompt'],
                'image_path': res['path'],
                'status': res['status'],
                'error': res.get('error')
            })
            
        # Sort by scene number
        formatted_results.sort(key=lambda x: x['scene_number'])
        return formatted_results

    def _generate_videos(self, script_data: Dict, image_results: List[Dict], project_id: str) -> List[Dict]:
        """Parallel video generation."""
        print(f"\n[PARALLEL] Starting Batch Video Generation...")
        
        scenes = script_data['scenes']
        image_lookup = {img['scene_number']: img for img in image_results}
        tasks = []
        
        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', idx)
            video_script = scene.get('video_script', '')
            dialogue = scene.get('dialogue', '')
            prompt = f"{video_script}. Dialogue: {dialogue}"
            
            image_data = image_lookup.get(scene_num)
            reference_image = image_data['image_path'] if image_data and image_data['status'] == 'success' else None
            
            if not reference_image:
                print(f"[WARNING] Scene {scene_num} missing reference image, skipping.")
                continue

            video_filename = f"{project_id}_scene{scene_num:02d}.mp4"
            video_path = os.path.join(self.dirs['videos'], video_filename)
            
            tasks.append({
                'prompt': prompt,
                'output_path': video_path,
                'reference_image_paths': reference_image, # Compatible key
                'scene_number': scene_num
            })
            
        # Execute batch
        batch_results = self.video_generator.generate_batch(tasks)
        
        # Format results
        formatted_results = []
        for res in batch_results:
            task = res['task']
            success = res['status'] == 'success'
            formatted_results.append({
                'scene_number': task['scene_number'],
                'prompt': task['prompt'],
                'video_path': res['path'],
                'status': res['status'],
                'error': res.get('error')
            })
            
        formatted_results.sort(key=lambda x: x['scene_number'])
        return formatted_results

    def _cleanup(self):
        """Cleanup multi-worker generators."""
        if self._multi_img_gen:
            self._multi_img_gen.close()
        if self._multi_video_gen:
            self._multi_video_gen.close()
