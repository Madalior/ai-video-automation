"""
Character-Based Video Production Manager

Orchestrates the complete character video generation pipeline:
1. Script Generation - Create story and scenes
2. Image Generation - Generate character reference images for each scene
3. Video Generation - Create videos from scenes and reference images
4. Thumbnail Generation - Create viral thumbnails for the final video

This manager handles the entire workflow from video idea to final output.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


from flowchart.character.script_generator import ScriptGenerator
from flowchart.character.image_generator import DreaminaGenerator
from flowchart.character.video_generator import DreaminaVideoGenerator
from flowchart.character.thumbnail_generator import ThumbnailGenerator


class CharacterVideoManager:
    """
    Main orchestrator for character-based video production.
    
    Pipeline Flow:
    1. Script Generation → Creates overview and detailed scenes
    2. Image Generation → Generates character reference images
    3. Video Generation → Creates videos from scenes + images
    4. Thumbnail Generation → Creates viral thumbnails
    """
    
    def __init__(self, output_dir: str = "output/character_videos", headless: bool = False, 
                 proxy_manager=None, use_chained_consistency: bool = True,
                 use_shared_session: bool = True, workers=None):
        """
        Initialize the Character Video Manager.
        
        Args:
            output_dir: Base directory for all outputs
            headless: Run browsers in headless mode (for automation)
            proxy_manager: Optional proxy manager for IP rotation
            use_chained_consistency: Use chained consistency (Scene N → Scene N+1) (default: True)
            use_shared_session: Use shared session for image+video generators (default: True)
            workers: Optional list of pre-initialized workers for parallel processing
        """
        self.output_dir = output_dir
        self.headless = headless
        self.proxy_manager = proxy_manager
        self.use_chained_consistency = use_chained_consistency
        self.use_shared_session = use_shared_session
        self.workers = workers  # For parallel processing
        
        # Create output directories
        self.dirs = {
            'base': output_dir,
            'scripts': os.path.join(output_dir, 'scripts'),
            'images': os.path.join(output_dir, 'images'),
            'videos': os.path.join(output_dir, 'videos'),
            'thumbnails': os.path.join(output_dir, 'thumbnails'),
            'metadata': os.path.join(output_dir, 'metadata')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize generators (lazy loading)
        self._script_generator = None
        self._image_generator = None
        self._video_generator = None
        self._thumbnail_generator = None
        self._shared_session = None  # Lazy-loaded shared session
        
        print(f"[MANAGER] Character Video Manager initialized")
        print(f"[MANAGER] Output directory: {output_dir}")
        print(f"[MANAGER] Chained Consistency: {'ENABLED' if use_chained_consistency else 'DISABLED'}")
        print(f"[MANAGER] Shared Session: {'ENABLED (1 account for images+videos)' if use_shared_session else 'DISABLED (separate accounts)'}")
        print(f"[MANAGER] Parallel Mode: {'ENABLED ({} workers)'.format(len(workers)) if workers else 'DISABLED (sequential)'}")
        print(f"[MANAGER] Proxy enabled: {'YES' if proxy_manager else 'NO'}")
    
    
    @property
    def shared_session(self):
        """Lazy load shared session for both generators."""
        if self._shared_session is None and self.use_shared_session:
            from flowchart.common.shared_session import SharedSessionManager
            
            self._shared_session = SharedSessionManager(
                headless=self.headless,
                profile_path=None,
                fresh_profile=True
            )
            
            # Login once for both generators
            print("[SHARED SESSION] Logging in once for image + video generators...")
            self._shared_session.login()
            print("[SHARED SESSION] ✅ Ready for both image and video generation")
            
        return self._shared_session
    
    @property
    def script_generator(self) -> ScriptGenerator:
        """Lazy load script generator."""
        if self._script_generator is None:
            self._script_generator = ScriptGenerator()
            print("[MANAGER] Script Generator loaded")
        return self._script_generator
    
    
    @property
    def image_generator(self) -> DreaminaGenerator:
        """Lazy load image generator."""
        if self._image_generator is None:
            if self.use_shared_session:
                # Use shared session
                self._image_generator = DreaminaGenerator(shared_session=self.shared_session)
                print("[MANAGER] Image Generator loaded (using shared session)")
            else:
                # Use separate browser
                self._image_generator = DreaminaGenerator(headless=self.headless)
                print("[MANAGER] Image Generator loaded (separate browser)")
        return self._image_generator
    
    
    @property
    def video_generator(self) -> DreaminaVideoGenerator:
        """Lazy load video generator."""
        if self._video_generator is None:
            if self.use_shared_session:
                # Use shared session (same as image generator!)
                self._video_generator = DreaminaVideoGenerator(shared_session=self.shared_session)
                print("[MANAGER] Video Generator loaded (using shared session)")
            else:
                # Use separate browser
                self._video_generator = DreaminaVideoGenerator(headless=self.headless)
                print("[MANAGER] Video Generator loaded (separate browser)")
        return self._video_generator
    
    @property
    def thumbnail_generator(self) -> ThumbnailGenerator:
        """Lazy load thumbnail generator."""
        if self._thumbnail_generator is None:
            self._thumbnail_generator = ThumbnailGenerator(
                output_dir=self.dirs['thumbnails']
            )
            print("[MANAGER] Thumbnail Generator loaded")
        return self._thumbnail_generator
    
    def produce_video(self, video_idea: str, num_scenes: int = 6, use_chained_consistency: bool = None,
                      init_workers_callback=None) -> Dict:
        """
        Complete video production pipeline.
        
        Args:
            video_idea: The core idea/theme for the video
            num_scenes: Number of scenes to generate (default: 6)
            use_chained_consistency: Override default chained consistency setting (default: None, uses init value)
            init_workers_callback: Optional callback to initialize workers after script generation
            
        Returns:
            Dictionary containing all output paths and metadata
        """
        # Use instance default if not specified
        if use_chained_consistency is None:
            use_chained_consistency = self.use_chained_consistency
        
        print("\n" + "="*80)
        print(f"[MANAGER] Starting Character Video Production")
        print(f"[MANAGER] Video Idea: {video_idea}")
        print(f"[MANAGER] Number of Scenes: {num_scenes}")
        print(f"[MANAGER] Chained Consistency: {'ENABLED' if use_chained_consistency else 'DISABLED'}")
        print("="*80 + "\n")
        
        start_time = time.time()
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize result tracking
        result = {
            'project_id': project_id,
            'video_idea': video_idea,
            'num_scenes': num_scenes,
            'status': 'in_progress',
            'script': None,
            'images': [],
            'videos': [],
            'thumbnails': [],
            'errors': []
        }
        
        try:
            # ============================================================
            # PHASE 1: Script Generation
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 1/5] SCRIPT GENERATION")
            print("="*80)
            
            script_result = self._generate_script(video_idea, num_scenes, project_id)
            result['script'] = script_result
            
            if not script_result or 'scenes' not in script_result:
                raise Exception("Script generation failed")
            
            # ============================================================
            # PHASE 2: Worker Initialization (NEW POSITION!)
            # ============================================================
            if init_workers_callback and not self.workers:
                print("\n" + "="*80)
                print("[PHASE 2/5] WORKER INITIALIZATION")
                print("="*80)
                print("[INFO] Initializing workers now that script is ready...")
                
                self.workers = init_workers_callback()
                
                if self.workers:
                    print(f"[SUCCESS] {len(self.workers)} workers initialized and ready")
                else:
                    print("[WARNING] Worker initialization returned no workers, using sequential mode")
            
            # ============================================================
            # PHASE 3: Image Generation (Character References)
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 3/5] IMAGE GENERATION (Character References)")
            print("="*80)
            
            image_results = self._generate_images(script_result, project_id)
            result['images'] = image_results
            
            # ============================================================
            # PHASE 4: Video Generation
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 4/5] VIDEO GENERATION")
            print("="*80)
            
            video_results = self._generate_videos(script_result, image_results, project_id, use_chained_consistency)
            result['videos'] = video_results
            
            # ============================================================
            # PHASE 5: Thumbnail Generation
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 5/5] THUMBNAIL GENERATION")
            print("="*80)
            
            thumbnail_results = self._generate_thumbnails(
                script_result['overview']['title'],
                image_results,
                project_id
            )
            result['thumbnails'] = thumbnail_results
            
            # Mark as complete
            result['status'] = 'completed'
            
        except Exception as e:
            print(f"\n[ERROR] Production failed: {str(e)}")
            result['status'] = 'failed'
            result['errors'].append(str(e))
        
        finally:
            # Save metadata
            duration = time.time() - start_time
            result['duration_seconds'] = duration
            self._save_metadata(result, project_id)
            
            # Cleanup
            self._cleanup()
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _generate_script(self, video_idea: str, num_scenes: int, project_id: str) -> Dict:
        """
        Phase 1: Generate script using ScriptGenerator.
        
        Returns:
            Dictionary with 'overview' and 'scenes'
        """
        print(f"\n[Step 1.1] Generating overview for: '{video_idea}'")
        overview = self.script_generator.generate_overview(video_idea)
        
        print(f"[Step 1.2] Generating {num_scenes} detailed scenes")
        scenes = self.script_generator.generate_scenes(overview, num_scenes)
        
        # Save script to file
        script_file = os.path.join(self.dirs['scripts'], f"{project_id}_script.json")
        script_data = {
            'overview': overview,
            'scenes': scenes
        }
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Script saved to: {script_file}")
        print(f"[INFO] Title: {overview.get('title', 'N/A')}")
        print(f"[INFO] Characters: {', '.join(overview.get('characters', []))}")
        print(f"[INFO] Scenes: {len(scenes)}")
        
        return script_data
    
    def _generate_images(self, script_data: Dict, project_id: str) -> List[Dict]:
        """
        Phase 2: Generate character reference images for each scene.
        
        Returns:
            List of dicts with 'scene_number', 'prompt', 'image_path'
        """
        scenes = script_data['scenes']
        
        # Check if parallel mode is enabled
        if self.workers:
            print(f"\n[PARALLEL] Using {len(self.workers)} workers for image generation")
            return self._generate_images_parallel(scenes, project_id)
        
        # Sequential mode
        overview = script_data['overview']
        image_results = []
        
        # Login once
        print("\n[Step 2.1] Logging into Image Generator")
        self.image_generator.login()
        
        # Generate image for each scene
        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', idx)
            character_name = scene.get('character_name', 'Unknown')
            character_desc = scene.get('character_description', '')
            background = scene.get('background', '')
            
            # Build comprehensive prompt
            prompt = f"{character_desc}, {background}"
            
            # Output path
            image_filename = f"{project_id}_scene{scene_num:02d}_reference.png"
            image_path = os.path.join(self.dirs['images'], image_filename)
            
            print(f"\n[Step 2.{idx+1}] Generating image for Scene {scene_num}")
            print(f"  Character: {character_name}")
            print(f"  Prompt: {prompt[:100]}...")
            
            try:
                self.image_generator.generate_image(
                    prompt=prompt,
                    output_path=image_path,
                    reference_image=None
                )
                
                image_results.append({
                    'scene_number': scene_num,
                    'character_name': character_name,
                    'prompt': prompt,
                    'image_path': image_path,
                    'status': 'success'
                })
                
                print(f"  [SUCCESS] Image saved: {image_path}")
                
            except Exception as e:
                print(f"  [ERROR] Image generation failed: {str(e)}")
                image_results.append({
                    'scene_number': scene_num,
                    'character_name': character_name,
                    'prompt': prompt,
                    'image_path': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        successful = sum(1 for r in image_results if r['status'] == 'success')
        print(f"\n[SUCCESS] Image generation complete: {successful}/{len(scenes)} successful")
        
        return image_results
    
    def _generate_images_parallel(self, scenes: List[Dict], project_id: str) -> List[Dict]:
        """
        Parallel image generation using pre-initialized workers.
        Workers were already staggered during initialization, so tasks submit immediately.
        """
        workers = self.workers
        image_results = []
        
        print(f"[PARALLEL] Distributing {len(scenes)} scenes across {len(workers)} workers...")
        
        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = {}
            
            for idx, scene in enumerate(scenes, 1):
                scene_num = scene.get('scene_number', idx)
                character_name = scene.get('character_name', 'Unknown')
                character_desc = scene.get('character_description', '')
                background = scene.get('background', '')
                
                # Build prompt
                prompt = f"{character_desc}, {background}"
                
                # Output path
                image_filename = f"{project_id}_scene{scene_num:02d}_reference.png"
                image_path = os.path.join(self.dirs['images'], image_filename)
                
                # Assign to worker (round-robin)
                worker_idx = (idx - 1) % len(workers)
                worker = workers[worker_idx]
                
                print(f"[PARALLEL] Scene {scene_num} → Worker {worker['id']} (submitting now)")
                
                # Submit task immediately (no stagger delay - workers already staggered at init)
                future = executor.submit(
                    worker['img_gen'].generate_image,
                    prompt=prompt,
                    output_path=image_path,
                    reference_image=None
                )
                
                futures[future] = {
                    'scene_number': scene_num,
                    'character_name': character_name,
                    'prompt': prompt,
                    'image_path': image_path,
                    'worker_id': worker['id']
                }
            
            # Collect results as they complete
            print("\n[PARALLEL] Waiting for all tasks to complete...")
            for future in as_completed(futures):
                task = futures[future]
                try:
                    success = future.result()
                    image_results.append({
                        'scene_number': task['scene_number'],
                        'character_name': task['character_name'],
                        'prompt': task['prompt'],
                        'image_path': task['image_path'],
                        'status': 'success' if success else 'failed'
                    })
                    status = '✓' if success else '✗'
                    print(f"[PARALLEL] Scene {task['scene_number']} {status} (Worker {task['worker_id']})")
                except Exception as e:
                    print(f"[PARALLEL] Scene {task['scene_number']} ✗ Error: {e}")
                    image_results.append({
                        'scene_number': task['scene_number'],
                        'character_name': task['character_name'],
                        'prompt': task['prompt'],
                        'image_path': None,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        # Sort by scene number
        image_results.sort(key=lambda x: x['scene_number'])
        
        successful = sum(1 for r in image_results if r['status'] == 'success')
        print(f"\n[SUCCESS] Parallel image generation complete: {successful}/{len(scenes)} successful")
        
        return image_results
    
    def _generate_videos(self, script_data: Dict, image_results: List[Dict], 
                        project_id: str, use_chained_consistency: bool = True) -> List[Dict]:
        """
        Phase 3: Generate videos with chained consistency.
        
        With chained consistency:
        - Scene 1: Generated without reference (establishes character)
        - Scene 2: Uses frame extracted from Scene 1 as reference
        - Scene 3: Uses frame extracted from Scene 2 as reference
        - etc...
        
        Args:
            script_data: Script with scenes
            image_results: Pre-generated reference images (used if chained_consistency=False)
            project_id: Project identifier
            use_chained_consistency: If True, use chained consistency; if False, use image_results
        
        Returns:
            List of dicts with 'scene_number', 'video_path', 'status'
        """
        scenes = script_data['scenes']
        image_lookup = {img['scene_number']: img for img in image_results}
        
        
        # Check if parallel mode is available (only when NOT using chained consistency)
        if self.workers and not use_chained_consistency:
            print(f"\n[PARALLEL] Using {len(self.workers)} workers for video generation")
            return self._generate_videos_parallel(scenes, image_lookup, project_id)
        
        # Sequential mode (or chained consistency which requires sequential)
        from flowchart.common.frame_extractor import extract_frame_at_time
        
        video_results = []
        reference_chain = []  # Stores extracted frames for chaining
        
        # Login once
        print("\n[Step 3.1] Logging into Video Generator")
        self.video_generator.login()
        
        if use_chained_consistency:
            print("[CONSISTENCY] Using chained consistency (Scene N → Scene N+1)")
        else:
            print("[CONSISTENCY] Using pre-generated reference images")
        
        # Generate video for each scene
        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', idx)
            video_script = scene.get('video_script', '')
            dialogue = scene.get('dialogue', '')
            
            # Build video prompt
            prompt = f"{video_script}. Dialogue: {dialogue}"
            
            # Determine reference image
            if use_chained_consistency:
                # Chained consistency approach
                if scene_num == 1:
                    reference_image = None
                    print(f"\n[Step 3.{idx+1}] Generating video for Scene {scene_num} (establishing character)")
                else:
                    reference_image = reference_chain[-1] if reference_chain else None
                    print(f"\n[Step 3.{idx+1}] Generating video for Scene {scene_num}")
                    if reference_image:
                        print(f"  [CHAIN] Using reference from Scene {scene_num - 1}")
            else:
                # Original approach: use pre-generated images
                image_data = image_lookup.get(scene_num)
                reference_image = image_data['image_path'] if image_data and image_data['status'] == 'success' else None
                print(f"\n[Step 3.{idx+1}] Generating video for Scene {scene_num}")
            
            # Output path
            video_filename = f"{project_id}_scene{scene_num:02d}.mp4"
            video_path = os.path.join(self.dirs['videos'], video_filename)
            
            print(f"  Prompt: {prompt[:100]}...")
            print(f"  Reference: {os.path.basename(reference_image) if reference_image else 'None'}")
            
            try:
                # Generate video (works with or without reference)
                self.video_generator.generate_video(
                    prompt=prompt,
                    reference_image_paths=[reference_image] if reference_image else None,
                    output_path=video_path
                )
                
                if os.path.exists(video_path):
                    video_results.append({
                        'scene_number': scene_num,
                        'prompt': prompt,
                        'reference_image': reference_image,
                        'video_path': video_path,
                        'status': 'success'
                    })
                    
                    print(f"  [SUCCESS] Video saved: {video_path}")
                    
                    # Extract frame for next scene (if using chained consistency and not last scene)
                    if use_chained_consistency and scene_num < len(scenes):
                        frame_filename = f"{project_id}_scene{scene_num:02d}_chain_ref.png"
                        frame_path = os.path.join(self.dirs['images'], frame_filename)
                        
                        print(f"  [EXTRACT] Extracting reference frame for Scene {scene_num + 1}...")
                        extracted_frame = extract_frame_at_time(video_path, 1.0, frame_path)
                        
                        if extracted_frame:
                            reference_chain.append(extracted_frame)
                            print(f"  [CHAIN] Frame added to chain for Scene {scene_num + 1}")
                        else:
                            print(f"  [WARNING] Frame extraction failed, Scene {scene_num + 1} will have no reference")
                else:
                    raise Exception("Video file not created")
                
            except Exception as e:
                print(f"  [ERROR] Video generation failed: {str(e)}")
                video_results.append({
                    'scene_number': scene_num,
                    'prompt': prompt,
                    'reference_image': reference_image,
                    'video_path': None,
                    'status': 'failed',
                    'error': str(e)
                })
        
        successful = sum(1 for r in video_results if r['status'] == 'success')
        print(f"\n[SUCCESS] Video generation complete: {successful}/{len(scenes)} successful")
        
        if use_chained_consistency and reference_chain:
            print(f"[CHAIN] Created reference chain with {len(reference_chain)} frames")
        
        return video_results
    
    def _generate_videos_parallel(self, scenes: List[Dict], image_lookup: Dict, 
                                            project_id: str) -> List[Dict]:
        """
        Parallel video generation using pre-initialized workers.
        Workers were already staggered during initialization, so tasks submit immediately.
        """
        workers = self.workers
        video_results = []
        
        print(f"[PARALLEL] Distributing {len(scenes)} scenes across {len(workers)} workers...")
        
        with ThreadPoolExecutor(max_workers=len(workers)) as executor:
            futures = {}
            
            for idx, scene in enumerate(scenes, 1):
                scene_num = scene.get('scene_number', idx)
                video_script = scene.get('video_script', '')
                dialogue = scene.get('dialogue', '')
                
                # Build video prompt
                prompt = f"{video_script}. Dialogue: {dialogue}"
                
                # Get reference image from pre-generated images
                image_data = image_lookup.get(scene_num)
                reference_image = image_data['image_path'] if image_data and image_data.get('status') == 'success' else None
                
                # Output path
                video_filename = f"{project_id}_scene{scene_num:02d}.mp4"
                video_path = os.path.join(self.dirs['videos'], video_filename)
                
                # Assign to worker (round-robin)
                worker_idx = (idx - 1) % len(workers)
                worker = workers[worker_idx]
                
                print(f"[PARALLEL] Scene {scene_num} → Worker {worker['id']} (submitting now)")
                
                # Submit task immediately (no stagger delay - workers already staggered at init)
                future = executor.submit(
                    worker['video_gen'].generate_video,
                    prompt=prompt,
                    reference_image_paths=[reference_image] if reference_image else None,
                    output_path=video_path
                )
                
                futures[future] = {
                    'scene_number': scene_num,
                    'prompt': prompt,
                    'reference_image': reference_image,
                    'video_path': video_path,
                    'worker_id': worker['id']
                }
            
            # Collect results as they complete
            print("\n[PARALLEL] Waiting for all tasks to complete...")
            for future in as_completed(futures):
                task = futures[future]
                try:
                    success = future.result()
                    # Check if file exists
                    file_exists = os.path.exists(task['video_path'])
                    video_results.append({
                        'scene_number': task['scene_number'],
                        'prompt': task['prompt'],
                        'reference_image': task['reference_image'],
                        'video_path': task['video_path'] if file_exists else None,
                        'status': 'success' if (success and file_exists) else 'failed'
                    })
                    status = '✓' if (success and file_exists) else '✗'
                    print(f"[PARALLEL] Scene {task['scene_number']} {status} (Worker {task['worker_id']})")
                except Exception as e:
                    print(f"[PARALLEL] Scene {task['scene_number']} ✗ Error: {e}")
                    video_results.append({
                        'scene_number': task['scene_number'],
                        'prompt': task['prompt'],
                        'reference_image': task['reference_image'],
                        'video_path': None,
                        'status': 'failed',
                        'error': str(e)
                    })
        
        # Sort by scene number
        video_results.sort(key=lambda x: x['scene_number'])
        
        successful = sum(1 for r in video_results if r['status'] == 'success')
        print(f"\n[SUCCESS] Parallel video generation complete: {successful}/{len(scenes)} successful")
        
        return video_results
    
    def _generate_thumbnails(self, title: str, image_results: List[Dict], 
                            project_id: str) -> List[str]:
        """
        Phase 4: Generate viral thumbnails from reference images.
        
        Returns:
            List of thumbnail paths
        """
        # Get successful images
        successful_images = [
            img['image_path'] for img in image_results 
            if img['status'] == 'success' and img['image_path']
        ]
        
        if not successful_images:
            print("[WARNING] No images available for thumbnail generation")
            return []
        
        print(f"\n[Step 4.1] Generating thumbnails from {len(successful_images)} images")
        print(f"  Title: {title}")
        
        try:
            # Generate 3 variants per image (or just 1 for simplicity)
            thumbnails = self.thumbnail_generator.generate_from_images(
                title=title,
                reference_images=successful_images[:3],  # Use first 3 images max
                styles_per_image=1
            )
            
            print(f"[SUCCESS] Generated {len(thumbnails)} thumbnail variants")
            
            # Generate CTR report
            if thumbnails:
                report = self.thumbnail_generator.generate_ctr_report(thumbnails)
                print("\n" + report)
            
            return thumbnails
            
        except Exception as e:
            print(f"[ERROR] Thumbnail generation failed: {str(e)}")
            return []
    
    def _save_metadata(self, result: Dict, project_id: str):
        """Save production metadata to file."""
        metadata_file = os.path.join(self.dirs['metadata'], f"{project_id}_metadata.json")
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[METADATA] Saved to: {metadata_file}")
        except Exception as e:
            print(f"[WARNING] Could not save metadata: {str(e)}")
    
    def _cleanup(self):
        """Cleanup resources."""
        if self._image_generator:
            try:
                self._image_generator.close()
                print("[CLEANUP] Image generator closed")
            except:
                pass
        
        if self._video_generator:
            try:
                self._video_generator.close()
                print("[CLEANUP] Video generator closed")
            except:
                pass
    
    def _print_summary(self, result: Dict):
        """Print production summary."""
        print("\n" + "="*80)
        print("PRODUCTION SUMMARY")
        print("="*80)
        print(f"Project ID: {result['project_id']}")
        print(f"Status: {result['status'].upper()}")
        print(f"Duration: {result.get('duration_seconds', 0):.1f} seconds")
        print(f"\nVideo Idea: {result['video_idea']}")
        
        if result.get('script'):
            overview = result['script'].get('overview', {})
            print(f"\nTitle: {overview.get('title', 'N/A')}")
            print(f"Characters: {', '.join(overview.get('characters', []))}")
        
        print(f"\nImages Generated: {len([i for i in result['images'] if i.get('status') == 'success'])}/{len(result['images'])}")
        print(f"Videos Generated: {len([v for v in result['videos'] if v.get('status') == 'success'])}/{len(result['videos'])}")
        print(f"Thumbnails Generated: {len(result['thumbnails'])}")
        
        if result.get('errors'):
            print(f"\nErrors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"  - {error}")
        
        print(f"\nOutput Directory: {self.output_dir}")
        print("="*80 + "\n")


# ============================================================
# CLI Interface
# ============================================================

def main():
    """Command-line interface for character video production."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Character-Based Video Production Manager"
    )
    parser.add_argument(
        'video_idea',
        type=str,
        help='The video idea/theme (e.g., "The Lost City of Atlantis")'
    )
    parser.add_argument(
        '--scenes',
        type=int,
        default=6,
        help='Number of scenes to generate (default: 6)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output/character_videos',
        help='Output directory (default: output/character_videos)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browsers in headless mode'
    )
    
    args = parser.parse_args()
    
    # Create manager and produce video
    manager = CharacterVideoManager(
        output_dir=args.output,
        headless=args.headless
    )
    
    result = manager.produce_video(
        video_idea=args.video_idea,
        num_scenes=args.scenes
    )
    
    # Exit with appropriate code
    exit(0 if result['status'] == 'completed' else 1)


if __name__ == "__main__":
    main()
