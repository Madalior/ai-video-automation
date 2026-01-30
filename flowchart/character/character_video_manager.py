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
    
    def __init__(self, output_dir: str = "output/character_videos", headless: bool = False, proxy_manager=None):
        """
        Initialize the Character Video Manager.
        
        Args:
            output_dir: Base directory for all outputs
            headless: Run browsers in headless mode (for automation)
            proxy_manager: Optional proxy manager for IP rotation
        """
        self.output_dir = output_dir
        self.headless = headless
        self.proxy_manager = proxy_manager
        
        # Create output directories
        self.dirs = {
            'base': output_dir,
            'scripts': os.path.join(output_dir, 'scripts'),
            'images': os.path.join(output_dir, 'images'),
            'videos': os.path.join(output_dir, 'videos'),
            'thumbnails': os.path.join(output_dir, 'thumbnails'),
            'metadata': os.path.join(output_dir, 'metadata')
        }
        # JSON Example
        curl \
        -d '{"apiKey": "your_api_key", "country": ["US", "RU"], "https": true, "quantity": 20}' \
        -H 'Content-Type: application/json' \
        https://api.proxifly.dev/get-proxy
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize generators (lazy loading)
        self._script_generator = None
        self._image_generator = None
        self._video_generator = None
        self._thumbnail_generator = None
        
        print(f"[MANAGER] Character Video Manager initialized")
        print(f"[MANAGER] Output directory: {output_dir}")
        print(f"[MANAGER] Proxy enabled: {'YES' if proxy_manager else 'NO'}")
    
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
            self._image_generator = DreaminaGenerator(headless=self.headless, proxy_manager=self.proxy_manager)
            print("[MANAGER] Image Generator loaded")
        return self._image_generator
    
    @property
    def video_generator(self) -> DreaminaVideoGenerator:
        """Lazy load video generator."""
        if self._video_generator is None:
            self._video_generator = DreaminaVideoGenerator(headless=self.headless, proxy_manager=self.proxy_manager)
            print("[MANAGER] Video Generator loaded")
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
    
    def produce_video(self, video_idea: str, num_scenes: int = 6) -> Dict:
        """
        Complete video production pipeline.
        
        Args:
            video_idea: The core idea/theme for the video
            num_scenes: Number of scenes to generate (default: 6)
            
        Returns:
            Dictionary containing all output paths and metadata
        """
        print("\n" + "="*80)
        print(f"[MANAGER] Starting Character Video Production")
        print(f"[MANAGER] Video Idea: {video_idea}")
        print(f"[MANAGER] Number of Scenes: {num_scenes}")
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
            print("[PHASE 1/4] SCRIPT GENERATION")
            print("="*80)
            
            script_result = self._generate_script(video_idea, num_scenes, project_id)
            result['script'] = script_result
            
            if not script_result or 'scenes' not in script_result:
                raise Exception("Script generation failed")
            
            # ============================================================
            # PHASE 2: Image Generation (Character References)
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 2/4] IMAGE GENERATION (Character References)")
            print("="*80)
            
            image_results = self._generate_images(script_result, project_id)
            result['images'] = image_results
            
            # ============================================================
            # PHASE 3: Video Generation
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 3/4] VIDEO GENERATION")
            print("="*80)
            
            video_results = self._generate_videos(script_result, image_results, project_id)
            result['videos'] = video_results
            
            # ============================================================
            # PHASE 4: Thumbnail Generation
            # ============================================================
            print("\n" + "="*80)
            print("[PHASE 4/4] THUMBNAIL GENERATION")
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
    
    def _generate_videos(self, script_data: Dict, image_results: List[Dict], 
                        project_id: str) -> List[Dict]:
        """
        Phase 3: Generate videos from scenes and reference images.
        
        Returns:
            List of dicts with 'scene_number', 'video_path', 'status'
        """
        scenes = script_data['scenes']
        video_results = []
        
        # Create lookup for images by scene number
        image_lookup = {img['scene_number']: img for img in image_results}
        
        # Login once
        print("\n[Step 3.1] Logging into Video Generator")
        self.video_generator.login()
        
        # Generate video for each scene
        for idx, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', idx)
            video_script = scene.get('video_script', '')
            dialogue = scene.get('dialogue', '')
            
            # Build video prompt
            prompt = f"{video_script}. Dialogue: {dialogue}"
            
            # Get reference image
            image_data = image_lookup.get(scene_num)
            reference_image = image_data['image_path'] if image_data and image_data['status'] == 'success' else None
            
            # Output path
            video_filename = f"{project_id}_scene{scene_num:02d}.mp4"
            video_path = os.path.join(self.dirs['videos'], video_filename)
            
            print(f"\n[Step 3.{idx+1}] Generating video for Scene {scene_num}")
            print(f"  Prompt: {prompt[:100]}...")
            print(f"  Reference: {reference_image if reference_image else 'None'}")
            
            try:
                if reference_image:
                    self.video_generator.generate_video(
                        prompt=prompt,
                        reference_image_path=reference_image,
                        output_path=video_path
                    )
                else:
                    print(f"  [WARNING] No reference image available, skipping video generation")
                    raise Exception("No reference image available")
                
                video_results.append({
                    'scene_number': scene_num,
                    'prompt': prompt,
                    'reference_image': reference_image,
                    'video_path': video_path,
                    'status': 'success'
                })
                
                print(f"  [SUCCESS] Video saved: {video_path}")
                
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
