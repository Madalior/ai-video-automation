"""
Master Video Automation Manager

Complete video automation workflow orchestrator (Based on FLOWCHART.drawio):
- Gmail uploader/verification
- Character-based videos (storytelling, vlogs, narratives)
- Info-based videos (educational, facts, tutorials)
- Niche discovery (URL-based, Auto-trend, Manual input)
- Parallel processing for 4-8x speedup
- Veo 3.1 consistency techniques
- Retention optimization
- AI metadata generation
- Multi-platform uploading
- Full pipeline: Gmail -> Niche -> Script -> Media -> Edit -> Optimize -> Upload

Usage:
    python master_manager.py --type character --idea "Detective mystery" --scenes 5
    python master_manager.py --type info --niche "Space discoveries" --ai-only
    python master_manager.py --type info --niche-mode url --url "https://youtube.com/watch?v=..."
    python master_manager.py --type info --niche-mode auto
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Gmail verification
try:
    from flowchart.common.gmail_verification import GmailVerifier
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("[WARNING] Gmail verification not available")

# Character pipeline imports
from flowchart.character.character_video_manager import CharacterVideoManager
from flowchart.character.character_orchestrator import WorkflowOrchestrator
import importlib
script_module = importlib.import_module("03_ideation_scripting.enhanced_script_generator")
EnhancedScriptGenerator = script_module.EnhancedScriptGenerator

# Info pipeline imports
try:
    from flowchart.info.info_orchestrator import InfoContentOrchestrator
    INFO_AVAILABLE = True
except ImportError:
    INFO_AVAILABLE = False
    print("[WARNING] Info pipeline not available")

# Niche discovery tools
try:
    from flowchart.common.video_url_analyzer import VideoURLAnalyzer
    from flowchart.common.trend_finder import TrendFinder
    from flowchart.common.video_analyzer import VideoAnalyzer
    NICHE_TOOLS_AVAILABLE = True
except ImportError:
    NICHE_TOOLS_AVAILABLE = False
    print("[WARNING] Niche discovery tools not available")

# Optimization and metadata tools
try:
    from flowchart.common.retention_optimizer import RetentionOptimizer
    from flowchart.common.retention_predictor import RetentionPredictor
    from flowchart.common.ai_metadata_generator import AIMetadataGenerator
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    print("[WARNING] Optimization tools not available")

# Upload tools
try:
    from flowchart.common.smart_uploader import SmartUploader
    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False
    print("[WARNING] Smart uploader not available")

# Consistency tools
from flowchart.common.identity_cards import IdentityCardManager
from flowchart.common.frame_controller import FrameController
from flowchart.common.prompt_builder import AnchorDeltaPromptBuilder
from flowchart.common.account_pool import AccountPoolManager


class MasterVideoAutomation:
    """
    Master orchestrator for complete video automation.
    
    Features:
    - Dual pipeline support (Character + Info)
    - Parallel processing enabled
    - Veo 3.1 consistency built-in
    - Complete workflow automation
    - Progress tracking and logging
    """
    
    def __init__(self, output_dir: str = "output", headless: bool = False, use_emotional_ai: bool = True, pool_size: int = 5):
        """
        Initialize master automation manager.
        
        Args:
            output_dir: Base output directory
            headless: Run browsers in headless mode
            use_emotional_ai: Enable emotional script generation (default: True)
            pool_size: Number of accounts in the pool (default: 5)
        """
        self.output_dir = output_dir
        self.headless = headless
        self.use_emotional_ai = use_emotional_ai
        self.pool_size = pool_size
        
        # Create output structure
        self.dirs = {
            'base': output_dir,
            'character': os.path.join(output_dir, 'character'),
            'info': os.path.join(output_dir, 'info'),
            'logs': os.path.join(output_dir, 'logs'),
            'metadata': os.path.join(output_dir, 'metadata')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize core managers
        self.character_manager = None
        self.info_manager = None
        self.frame_controller = FrameController()
        
        # Account Pool Manager (lazy — accounts created on first use)
        self.account_pool = AccountPoolManager(
            batch_size=pool_size,
            headless=headless
        )
        
        # Initialize flowchart tools
        if GMAIL_AVAILABLE:
            self.gmail_verifier = GmailVerifier()
        else:
            self.gmail_verifier = None
            
        if NICHE_TOOLS_AVAILABLE:
            self.video_url_analyzer = VideoURLAnalyzer()
            self.trend_finder = TrendFinder()
            self.video_analyzer = VideoAnalyzer()
        else:
            self.video_url_analyzer = None
            self.trend_finder = None
            self.video_analyzer = None
            
        if OPTIMIZATION_AVAILABLE:
            self.retention_optimizer = RetentionOptimizer()
            self.retention_predictor = RetentionPredictor()
            self.ai_metadata_generator = AIMetadataGenerator()
        else:
            self.retention_optimizer = None
            self.retention_predictor = None
            self.ai_metadata_generator = None
            
        if UPLOADER_AVAILABLE:
            self.smart_uploader = SmartUploader(account_pool=self.account_pool)
        else:
            self.smart_uploader = None
        
        print(f"[MASTER] Video Automation Manager initialized")
        print(f"[MASTER] Output: {output_dir}")
        print(f"[MASTER] Emotional AI: {'YES' if use_emotional_ai else 'NO'}")
        print(f"[MASTER] Pool Size: {pool_size}")
        print(f"[MASTER] Gmail: {'YES' if GMAIL_AVAILABLE else 'NO'}")
        print(f"[MASTER] Niche Tools: {'YES' if NICHE_TOOLS_AVAILABLE else 'NO'}")
        print(f"[MASTER] Optimization: {'YES' if OPTIMIZATION_AVAILABLE else 'NO'}")
        print(f"[MASTER] Uploader: {'YES' if UPLOADER_AVAILABLE else 'NO'}")
    
    
    def produce_character_video(
        self,
        video_idea: str,
        num_scenes: int = 5,
        use_consistency: bool = True,
        parallel: bool = False,
        pipeline_mode: bool = True,
        chained_consistency: bool = True,
        shared_session: bool = True,  # Forced to True in logic below
        character_ref: str = None,
        background_ref: str = None
    ) -> Dict:
        """
        Produce character-based video with full automation.
        
        Args:
            video_idea: Story/video concept
            num_scenes: Number of scenes
            use_consistency: Enable Veo 3.1 consistency
            parallel: Use parallel processing
            pipeline_mode: Use pipeline mode (workers start immediately after login) (default: True)
            chained_consistency: Use chained consistency (Scene N -> Scene N+1) (default: True)
            shared_session: Use shared session for image+video generators (default: True)
            character_ref: Optional character reference image path for consistent appearance
            background_ref: Optional background/style reference image for environmental consistency
        
        Returns:
            Production result dictionary
        """
        print("\n" + "="*80)
        print("CHARACTER VIDEO PRODUCTION")
        print("="*80)
        print(f"Idea: {video_idea}")
        print(f"Scenes: {num_scenes}")
        print(f"Consistency: {'Enabled (Veo 3.1)' if use_consistency else 'Disabled'}")
        print(f"Chained Consistency: {'ENABLED' if chained_consistency else 'DISABLED'}")
        print(f"Processing: {'Parallel' if parallel else 'Sequential'}")
        print("="*80 + "\n")
        
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        
        if True: # Always use pipeline mode for character videos
            parallel = True # Enforce parallel for character videos
            pipeline_mode = True 
            shared_session = True # Enforce shared session

            # HYBRID PIPELINE MODE: Persistent Workers
            print("[MODE] Using Hybrid Pipeline Mode - Persistent Workers")
            print("[INFO] Workers login once and stay alive for both phases")
            print("[PHASE 1] Parallel image generation (independent)")
            print("[PHASE 2] Sequential video generation (chained consistency)")
            
            import importlib
            script_module = importlib.import_module("03_ideation_scripting.enhanced_script_generator")
            EnhancedScriptGenerator = script_module.EnhancedScriptGenerator
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            import threading
            import os
            
            # Step 1: Generate script
            print("\n[STEP 1/3] Generating script...")
            script_gen = EnhancedScriptGenerator()
            overview_data = script_gen.generate_overview_with_identity_cards(video_idea)
            scenes = script_gen.generate_scenes_with_deltas(overview_data, num_scenes)
            print(f"[SCRIPT] [OK] Generated {len(scenes)} scenes")
            
            # Step 2: Generate character reference
            print("\n[STEP 2/3] Generating character reference...")
            character_ref = self._generate_character_reference(overview_data)
            
            # Step 3: Launch persistent workers (login once, handle both phases)
            print(f"\n[STEP 3/3] Launching {num_scenes} persistent workers...")
            
            results_dict = {}
            lock = threading.Lock()
            
            # Create video completion events for chained consistency
            video_ready_events = {i: threading.Event() for i in range(num_scenes)}
            
            # Launch workers (one per scene)
            workers = []
            for i in range(num_scenes):
                thread = threading.Thread(
                    target=self._hybrid_persistent_worker,
                    args=(i, scenes[i], character_ref, results_dict, video_ready_events, lock),
                    daemon=False
                )
                thread.start()
                workers.append(thread)
                
                # Stagger worker launches to prevent mail.tm 429 rate limiting
                if i < num_scenes - 1:
                    import time
                    print(f"[INFO] Waiting 25s before launching next worker to avoid rate limits...")
                    time.sleep(25)
            
            # Wait for all workers to complete both phases
            print("\n[PIPELINE] Waiting for all workers to complete...")
            for i, worker in enumerate(workers):
                worker.join()
                print(f"[PIPELINE] Worker {i} completed both phases")
            
            print("\n[PIPELINE] [DONE] All scenes processed!")
            
            # Sort results by scene ID
            sorted_scenes = [results_dict[i] for i in sorted(results_dict.keys())]
            
            # Combine videos
            print("\n[EDITING] Combining scene videos...")
            video_paths = [scene['video'] for scene in sorted_scenes if scene.get('video')]
            
            # Simple video combining using moviepy
            output_path = os.path.join(self.dirs['character'], f"{project_id}_final.mp4")
            clips = [VideoFileClip(path) for path in video_paths]
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Clean up
            for clip in clips:
                clip.close()
            final_clip.close()
            
            final_video = output_path
            
            result = {
                'status': 'completed',
                'video_path': final_video,
                'scenes': sorted_scenes,
                'script': {'overview': overview_data, 'scenes': scenes},
                'project_id': project_id,
                'num_scenes': num_scenes,
                'mode': 'hybrid_persistent_workers',
                'character_ref': character_ref,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save metadata
            self._save_production_metadata(result, 'character', project_id)
            
            return result
        
        # Sequential mode (default or fallback)
        print("[MODE] Using Sequential Character Manager")
        
        from flowchart.character.character_video_manager import CharacterVideoManager
        manager = CharacterVideoManager(
            output_dir=self.dirs['character'],
            headless=self.headless,
            use_chained_consistency=chained_consistency,
            use_shared_session=shared_session
        )
        
        result = manager.produce_video(
            video_idea=video_idea,
            num_scenes=num_scenes,
            use_chained_consistency=chained_consistency
        )
        
        # Save metadata
        self._save_production_metadata(result, 'character', project_id)
        
        return result
    
    
    def _hybrid_persistent_worker(self, scene_id, scene, character_ref, results_dict, video_ready_events, lock):
        """
        Persistent worker that handles BOTH image and video generation.
        
        Worker lifecycle:
        1. Login once
        2. PHASE 1: Generate image (parallel, independent)
        3. PHASE 2: Wait for turn, generate video (sequential, chained)
        4. Close browser
        
        Args:
            scene_id: Scene number (0, 1, 2, ...)
            scene: Scene dictionary with prompts
            character_ref: Path to character reference image
            results_dict: Shared results dictionary
            video_ready_events: Dict of threading events for video coordination
            lock: Threading lock for results_dict access
        """
        from flowchart.common.shared_session import SharedSessionManager
        from flowchart.character.image_generator import DreaminaGenerator
        from flowchart.character.video_generator import DreaminaVideoGenerator
        import time
        
        try:
            # Step 1: Get session from account pool (or fresh if pool empty)
            print(f"\n[WORKER {scene_id}] Getting session from account pool...")
            session = self.account_pool.get_active_session()
            
            if not session:
                # Fallback: create fresh session if pool fails
                print(f"[WORKER {scene_id}] Pool unavailable, using fresh profile...")
                session = SharedSessionManager(headless=self.headless, fresh_profile=True)
                if not session.login():
                    print(f"[WORKER {scene_id}] [FAIL] Login failed")
                    return
            
            img_gen = DreaminaGenerator(shared_session=session)
            video_gen = DreaminaVideoGenerator(shared_session=session)
            print(f"[WORKER {scene_id}] [OK] Session ready")
            
            # Determine reference based on smart auto-chain
            scene_ref = character_ref
            if scene.get('independent') and scene.get('id_card_primary'):
                scene_ref = scene['id_card_primary']
                print(f"[WORKER {scene_id}] [SMART] Using ID card primary (independent scene)")
            elif character_ref:
                print(f"[WORKER {scene_id}] [SMART] Using chained character reference")
            
            # PHASE 1: Generate image (parallel, all workers work simultaneously)
            print(f"\n[WORKER {scene_id}] [PHASE 1] Generating image...")
            
            img_filename = f"scene_{scene_id}_image.png"
            img_output_path = os.path.join(self.dirs['character'], img_filename)
            
            success = img_gen.generate_image(
                prompt=scene.get('image_prompt', scene.get('description', '')),
                output_path=img_output_path,
                reference_image=scene_ref
            )
            
            if success:
                img_path = img_output_path
                self.account_pool.track_generation()
                print(f"[WORKER {scene_id}] [PHASE 1] [OK] Image saved: {img_path}")
            else:
                img_path = None
                print(f"[WORKER {scene_id}] [PHASE 1] [FAIL] Image generation failed")
                # Check if failure is due to overload/limit
                try:
                    if session.overload_detector.check_for_overload(session.driver):
                        print(f"[WORKER {scene_id}] Overload detected — marking account exhausted")
                        self.account_pool.mark_exhausted("overload_detected")
                except:
                    pass
            
            # Store image result
            with lock:
                if scene_id not in results_dict:
                    results_dict[scene_id] = {}
                results_dict[scene_id]['image'] = img_path
                results_dict[scene_id]['scene'] = scene
            
            if not img_path:
                print(f"[WORKER {scene_id}] Aborting due to image generation failure")
                video_ready_events[scene_id].set() # Unblock others
                return

            # PHASE 2: Generate video (sequential with chained consistency)
            print(f"[WORKER {scene_id}] [PHASE 2] Waiting for turn to generate video...")
            
            # Wait for previous scene's video to complete (if not first scene)
            if scene_id > 0:
                print(f"[WORKER {scene_id}] [PHASE 2] Waiting for Scene {scene_id - 1} video...")
                video_ready_events[scene_id - 1].wait()
                print(f"[WORKER {scene_id}] [PHASE 2] Scene {scene_id - 1} ready!")
            
            # Get reference video from previous scene
            reference_video = None
            if scene_id > 0:
                reference_video_path = None
                with lock:
                    reference_video_path = results_dict[scene_id - 1].get('video')
                
                if reference_video_path and os.path.exists(reference_video_path):
                    reference_video = reference_video_path
                    print(f"[WORKER {scene_id}] [PHASE 2] Using Scene {scene_id - 1} video as reference")
                else:
                    print(f"[WORKER {scene_id}] [PHASE 2] [WARNING] Previous video missing, skipping chained consistency")
            
            # Generate video
            print(f"[WORKER {scene_id}] [PHASE 2] Generating video...")
            video_path = video_gen.generate_video(
                prompt=scene.get('video_prompt', scene.get('description', '')),
                first_frame=img_path,
                reference_video=reference_video  # Chained consistency!
            )
            
            if video_path:
                self.account_pool.track_generation()
                print(f"[WORKER {scene_id}] [PHASE 2] [OK] Video saved: {video_path}")
            else:
                print(f"[WORKER {scene_id}] [PHASE 2] [FAIL] Video generation failed")
            
            # Store video result and signal completion
            with lock:
                results_dict[scene_id]['video'] = video_path
            
            # Signal that this scene's video is ready for next scene
            video_ready_events[scene_id].set()
            
            print(f"[WORKER {scene_id}] [DONE] Both phases complete!")
            
        except Exception as e:
            print(f"[WORKER {scene_id}] [ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            
            # Set event even on failure so other workers don't hang
            video_ready_events[scene_id].set()
        
        finally:
            try:
                if 'session' in locals():
                    session.close()
            except:
                pass
            print(f"[WORKER {scene_id}] Browser closed")
    
    
    def _generate_character_reference(self, overview_data):
        """
        Generate single character reference image from script's identity cards.
        
        This reference will be used by all scenes for consistent character appearance.
        
        Args:
            overview_data: Script overview containing identity cards
            
        Returns:
            str: Path to character reference image, or None if generation fails
        """
        identity_cards = overview_data.get('identity_cards', [])
        if not identity_cards:
            print("[WARNING] No identity cards found, skipping character reference")
            return None
        
        # Handle both list and dict formats
        if isinstance(identity_cards, dict):
            # Get first character from dict
            main_char = list(identity_cards.values())[0] if identity_cards else None
        else:
            # Get first item from list
            main_char = identity_cards[0] if len(identity_cards) > 0 else None
        
        if not main_char:
            print("[WARNING] No main character found")
            return None
            
        char_description = main_char.get('anchor_attributes', '')
        
        if not char_description:
            print("[WARNING] No character description found")
            return None
        
        print(f"\n[CHARACTER REF] Generating reference for: {main_char.get('character_name', 'Unknown')}")
        print(f"[CHARACTER REF] Description: {char_description}")
        
        try:
            from flowchart.character.image_generator import DreaminaGenerator
            import os
            
            # Use account pool session for reference generation
            session = self.account_pool.get_active_session()
            
            if not session:
                # Fallback to fresh profile
                from flowchart.common.shared_session import SharedSessionManager
                session = SharedSessionManager(headless=self.headless, fresh_profile=True)
                if not session.login():
                    print("[ERROR] Failed to login for character reference generation")
                    return None
            
            ref_gen = DreaminaGenerator(shared_session=session)
            
            # Generate character reference portrait
            ref_filename = f"character_ref_{overview_data.get('project_id', 'temp')}.png"
            ref_output_path = os.path.join(self.dirs['character'], ref_filename)
            
            success = ref_gen.generate_image(
                prompt=f"Character reference portrait: {char_description}, professional headshot, clear details",
                output_path=ref_output_path,
                reference_image=None
            )
            
            self.account_pool.track_generation()
            
            if success:
                print(f"[CHARACTER REF] [OK] Generated: {ref_output_path}")
                return ref_output_path
            else:
                print("[CHARACTER REF] [FAIL] Generation failed")
                return None
            
        except Exception as e:
            print(f"[CHARACTER REF] [ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    
    def _sequential_video_phase(self, scenes, image_results):
        """
        Phase 2: Generate videos sequentially with chained consistency.
        
        Each video uses the previous video as reference for smooth transitions.
        Videos are generated in order: 0 -> 1 -> 2 -> 3 -> 4
        
        Args:
            scenes: List of scene dictionaries
            image_results: Results from Phase 1 containing images
            
        Returns:
            dict: {scene_id: {'image': path, 'video': path}}
        """
        from flowchart.common.shared_session import SharedSessionManager
        from flowchart.character.video_generator import DreaminaVideoGenerator
        
        print(f"\n[PHASE 2/2] Sequential Video Generation ({len(scenes)} scenes)")
        print(f"[INFO] Using chained consistency for smooth transitions")
        
        # Login single session for all videos
        session = SharedSessionManager(headless=self.headless, fresh_profile=True)
        if not session.login():
            print("[ERROR] Video phase login failed")
            return image_results
        
        video_gen = DreaminaVideoGenerator(shared_session=session)
        
        video_results = {}
        reference_video = None
        
        # Generate videos in sequential order
        for i in range(len(scenes)):
            scene = image_results[i]['scene']
            img_path = image_results[i]['image']
            
            print(f"\n[VIDEO {i+1}/{len(scenes)}] Generating Scene {i} video...")
            if reference_video:
                print(f"[VIDEO {i+1}/{len(scenes)}] Using Scene {i-1} video as reference")
            
            try:
                video_path = video_gen.generate_video(
                    prompt=scene.get('video_prompt', scene.get('description', '')),
                    first_frame=img_path,
                    reference_video=reference_video  # Uses previous video!
                )
                
                print(f"[VIDEO {i+1}/{len(scenes)}] [OK] Scene {i} video saved: {video_path}")
                
                video_results[i] = {
                    'image': img_path,
                    'video': video_path,
                    'scene': scene
                }
                
                # Next video uses this one as reference
                reference_video = video_path
                
            except Exception as e:
                print(f"[VIDEO {i+1}/{len(scenes)}] [ERROR] Error: {e}")
                import traceback
                traceback.print_exc()
                # Continue with next video even if one fails
                video_results[i] = {
                    'image': img_path,
                    'video': None,
                    'scene': scene
                }
        
        session.close()
        print(f"\n[PHASE 2] [DONE] All {len(video_results)} videos completed!")
        
        return video_results
    
    
    def _init_workers_pipeline(self, scene_queue, results_dict, num_workers: int = 4, stagger_delay: int = 10):
        """
        Initialize workers in pipeline mode - each worker processes scenes from queue immediately after login.
        
        Pipeline behavior:
        - Worker logs in
        - Immediately pulls next scene from queue
        - Generates image
        - Generates video
        - Repeats until queue empty
        
        Args:
            scene_queue: Queue of scenes to process
            results_dict: Shared dictionary to store results
            num_workers: Number of workers (default: 4)
            stagger_delay: Delay between worker launches (default: 10s)
            
        Returns:
            List of worker threads
        """
        import threading
        import time
        
        workers = []
        lock = threading.Lock()
        
        for i in range(num_workers):
            print(f"\n[WORKER {i}] Launching pipeline worker...")
            
            # Create worker thread
            thread = threading.Thread(
                target=self._worker_pipeline,
                args=(i, scene_queue, results_dict, lock),
                daemon=False
            )
            thread.start()
            workers.append(thread)
            
            # Stagger next worker launch
            if i < num_workers - 1:
                print(f"[STAGGER] Waiting {stagger_delay}s before launching Worker {i+1}...")
                time.sleep(stagger_delay)
        
        print(f"\n[WORKERS] Launched {len(workers)} pipeline workers")
        return workers
    
    
    
    def discover_niche_from_url(self, video_url: str) -> str:
        """
        Discover niche from a YouTube video URL (Flowchart path A).
        
        Args:
            video_url: YouTube video URL to analyze
            
        Returns:
            Discovered niche/topic
        """
        print(f"\n[NICHE DISCOVERY] Analyzing URL: {video_url}")
        
        if not self.video_url_analyzer:
            print("[ERROR] Video URL analyzer not available")
            return ""
        
        niche = self.video_url_analyzer.analyze_url(video_url)
        print(f"[NICHE DISCOVERED] {niche}")
        return niche
    
    def discover_niche_auto(self) -> str:
        """
        Automatically discover trending niche (Flowchart path B).
        
        Returns:
            Trending niche/topic
        """
        print("\n[NICHE DISCOVERY] Auto-discovering trending topics...")
        
        if not self.trend_finder:
            print("[ERROR] Trend finder not available")
            return ""
        
        niche = self.trend_finder.find_trending_niche()
        print(f"[TRENDING NICHE] {niche}")
        return niche
    
    def analyze_niche(self, niche: str) -> Dict:
        """
        Analyze a niche for video content ideas.
        
        Args:
            niche: Niche topic to analyze
            
        Returns:
            Analysis results
        """
        print(f"\n[NICHE ANALYSIS] Analyzing: {niche}")
        
        if not self.video_analyzer:
            print("[WARNING] Video analyzer not available, skipping analysis")
            return {'niche': niche}
        
        analysis = self.video_analyzer.analyze(niche)
        print(f"[ANALYSIS COMPLETE] Found {len(analysis.get('ideas', []))} content ideas")
        return analysis
    
    def produce_info_video(
        self,
        niche: Optional[str] = None,
        video_mode: str = 'ai',
        num_videos: int = 5,
        parallel: bool = True,
        niche_mode: str = 'manual',
        video_url: Optional[str] = None
    ) -> Dict:
        """
        Produce info/educational video with full automation.
        
        Args:
            niche: Topic/niche for content (required if niche_mode='manual')
            video_mode: 'ai', 'stock', or 'hybrid'
            num_videos: Number of video clips
            parallel: Use parallel processing
            niche_mode: 'url', 'auto', or 'manual' (flowchart paths A/B/C)
            video_url: YouTube URL (required if niche_mode='url')
        
        Returns:
            Production result dictionary
        """
        if not INFO_AVAILABLE:
            print("[ERROR] Info pipeline not available")
            return {'status': 'error', 'message': 'Info pipeline not installed'}
        
        # Niche discovery based on mode (Flowchart decision point)
        if niche_mode == 'url':
            if not video_url:
                print("[ERROR] video_url required for niche_mode='url'")
                return {'status': 'error', 'message': 'video_url required'}
            niche = self.discover_niche_from_url(video_url)
            if not niche:
                return {'status': 'error', 'message': 'Failed to discover niche from URL'}
                
        elif niche_mode == 'auto':
            niche = self.discover_niche_auto()
            if not niche:
                return {'status': 'error', 'message': 'Failed to auto-discover niche'}
                
        elif niche_mode == 'manual':
            if not niche:
                print("[ERROR] niche required for niche_mode='manual'")
                return {'status': 'error', 'message': 'niche required'}
        
        # Analyze niche (Flowchart: Video analyzer step)
        niche_analysis = self.analyze_niche(niche)
        
        print("\n" + "="*80)
        print("INFO VIDEO PRODUCTION")
        print("="*80)
        print(f"Niche: {niche}")
        print(f"Niche Mode: {niche_mode.upper()}")
        print(f"Mode: {video_mode.upper()}")
        print(f"Videos: {num_videos}")
        print(f"Processing: {'Parallel' if parallel else 'Sequential'}")
        print("="*80 + "\n")
        
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if parallel and video_mode == 'ai':
            print("[MODE] Parallel Info Director was removed. Falling back to default.")
            
        # Use standard InfoContentOrchestrator
        print("[MODE] Using Standard Info Orchestrator")
            
        if not self.info_manager:
            self.info_manager = InfoContentOrchestrator(
                output_dir=self.dirs['info'],
                video_mode=video_mode,
                headless=self.headless
            )
        
        result = self.info_manager.produce_content(niche=niche)
        
        # Post-production steps (Flowchart: Retention -> Thumbnail -> Metadata -> Upload)
        if result.get('status') == 'completed':
            result = self._apply_post_production(result, project_id)
        
        # Save metadata
        self._save_production_metadata(result, 'info', project_id)
        
        return result
    
    def batch_produce(
        self,
        batch_config: Dict
    ) -> List[Dict]:
        """
        Batch produce multiple videos.
        
        Args:
            batch_config: Configuration dict with video list
            
        Returns:
            List of production results
        """
        print("\n" + "="*80)
        print("BATCH PRODUCTION MODE")
        print("="*80)
        
        videos = batch_config.get('videos', [])
        print(f"Total videos: {len(videos)}\n")
        
        results = []
        
        for idx, video_config in enumerate(videos, 1):
            print(f"\n[{idx}/{len(videos)}] Processing: {video_config.get('idea', video_config.get('niche'))}")
            
            video_type = video_config.get('type', 'character')
            
            try:
                if video_type == 'character':
                    result = self.produce_character_video(
                        video_idea=video_config['idea'],
                        num_scenes=video_config.get('scenes', 5),
                        use_consistency=video_config.get('consistency', True),
                        parallel=video_config.get('parallel', False)
                    )
                else:
                    result = self.produce_info_video(
                        niche=video_config['niche'],
                        video_mode=video_config.get('mode', 'ai'),
                        num_videos=video_config.get('clips', 5),
                        parallel=video_config.get('parallel', True)
                    )
                
                results.append(result)
                
            except Exception as e:
                print(f"[ERROR] Video {idx} failed: {e}")
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'config': video_config
                })
        
        # Save batch summary
        self._save_batch_summary(results)
        
        return results
    
    def _apply_post_production(self, result: Dict, project_id: str) -> Dict:
        """
        Apply post-production steps from flowchart:
        - Retention optimization
        - AI metadata generation
        - Smart uploading
        
        Args:
            result: Production result dictionary
            project_id: Project identifier
            
        Returns:
            Updated result dictionary
        """
        print("\n" + "="*80)
        print("POST-PRODUCTION PIPELINE")
        print("="*80)
        
        video_path = result.get('video_path')
        if not video_path or not os.path.exists(video_path):
            print("[WARNING] Video path not found, skipping post-production")
            return result
        
        # Step 1: Retention Optimization (Flowchart step)
        if self.retention_optimizer and self.retention_predictor:
            print("\n[1/3] Retention Optimization...")
            try:
                # Predict retention
                retention_score = self.retention_predictor.predict(video_path)
                print(f"  Predicted retention: {retention_score:.1%}")
                
                # Optimize if needed
                if retention_score < 0.7:
                    print("  Applying retention optimization...")
                    optimized_path = self.retention_optimizer.optimize(video_path)
                    result['video_path'] = optimized_path
                    result['retention_optimized'] = True
                    print(f"  [OK] Optimized video saved")
                else:
                    print("  [OK] Retention already good, no optimization needed")
                    result['retention_optimized'] = False
                    
                result['retention_score'] = retention_score
            except Exception as e:
                print(f"  [WARNING] Retention optimization failed: {e}")
        else:
            print("[1/3] Retention Optimization - SKIPPED (not available)")
        
        # Step 2: AI Metadata Generation (Flowchart step)
        if self.ai_metadata_generator:
            print("\n[2/3] AI Metadata Generation...")
            try:
                metadata = self.ai_metadata_generator.generate(
                    video_path=result['video_path'],
                    niche=result.get('niche', result.get('video_idea', ''))
                )
                result['ai_metadata'] = metadata
                print(f"  [OK] Title: {metadata.get('title', 'N/A')}")
                print(f"  [OK] Tags: {len(metadata.get('tags', []))} generated")
                print(f"  [OK] Description generated")
            except Exception as e:
                print(f"  [WARNING] Metadata generation failed: {e}")
        else:
            print("[2/3] AI Metadata Generation - SKIPPED (not available)")
        
        # Step 3: Smart Uploader (Flowchart final step)
        if self.smart_uploader:
            print("\n[3/3] Smart Uploader...")
            try:
                upload_result = self.smart_uploader.upload(
                    video_path=result['video_path'],
                    thumbnail_path=result.get('thumbnail_path'),
                    metadata=result.get('ai_metadata', {}),
                    platforms=['youtube']  # Can be extended to TikTok, etc.
                )
                result['upload_result'] = upload_result
                print(f"  [OK] Uploaded to: {', '.join(upload_result.get('platforms', []))}")
            except Exception as e:
                print(f"  [WARNING] Upload failed: {e}")
        else:
            print("[3/3] Smart Uploader - SKIPPED (not available)")
        
        print("\n" + "="*80)
        print("POST-PRODUCTION COMPLETE")
        print("="*80 + "\n")
        
        return result
    
    def _save_production_metadata(self, result: Dict, pipeline_type: str, project_id: str):
        """Save production metadata to file."""
        metadata_file = os.path.join(
            self.dirs['metadata'],
            f"{pipeline_type}_{project_id}_metadata.json"
        )
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[METADATA] Saved to: {metadata_file}")
        except Exception as e:
            print(f"[WARNING] Could not save metadata: {e}")
    
    def _save_batch_summary(self, results: List[Dict]):
        """Save batch production summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(
            self.dirs['metadata'],
            f"batch_{timestamp}_summary.json"
        )
        
        summary = {
            'timestamp': timestamp,
            'total_videos': len(results),
            'successful': sum(1 for r in results if r.get('status') == 'completed'),
            'failed': sum(1 for r in results if r.get('status') == 'failed'),
            'results': results
        }
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n[BATCH SUMMARY] Saved to: {summary_file}")
        except Exception as e:
            print(f"[WARNING] Could not save batch summary: {e}")
    
    def print_summary(self):
        """Print system capabilities summary."""
        print("\n" + "="*80)
        print("VIDEO AUTOMATION SYSTEM - CAPABILITIES (FLOWCHART.drawio)")
        print("="*80)
        
        if GMAIL_AVAILABLE:
            print("\n[GMAIL VERIFICATION]")
            print("  [+] Gmail account verification")
            print("  [+] Multi-platform upload support")
        
        print("\n[CHARACTER PIPELINE]")
        print("  [+] Story-based videos")
        print("  [+] Character consistency (Veo 3.1)")
        print("  [+] Parallel processing (2-8x faster)")
        print("  [+] Identity cards + Multi-reference")
        
        if INFO_AVAILABLE:
            print("\n[INFO PIPELINE]")
            print("  [+] Educational videos")
            print("  [+] AI + Stock footage")
            print("  [+] Parallel generation (4x faster)")
        
        if NICHE_TOOLS_AVAILABLE:
            print("\n[NICHE DISCOVERY]")
            print("  [+] URL-based analysis (YouTube)")
            print("  [+] Auto trend finder")
            print("  [+] Manual niche input")
            print("  [+] Video content analyzer")
        
        print("\n[CORE FEATURES]")
        print("  [+] Automated scripting (LLM)")
        if self.use_emotional_ai:
            print("  [+] Emotional script generation (7 emotion categories)")
            print("  [+] Human-like storytelling & delivery hints")
        print("  [+] AI image generation (Dreamina)")
        print("  [+] AI video generation (Veo 3.1)")
        print("  [+] Thumbnail creation")
        print("  [+] Batch processing")
        
        if OPTIMIZATION_AVAILABLE:
            print("\n[POST-PRODUCTION]")
            print("  [+] Retention optimization")
            print("  [+] Retention prediction")
            print("  [+] AI metadata generation")
        
        if UPLOADER_AVAILABLE:
            print("\n[DISTRIBUTION]")
            print("  [+] Smart uploader (YouTube, TikTok)")
            print("  [+] Auto-metadata")
        
        print("\n[OUTPUT]")
        print(f"  Base: {self.output_dir}")
        print(f"  Character: {self.dirs['character']}")
        print(f"  Info: {self.dirs['info']}")
        print(f"  Logs: {self.dirs['logs']}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Command-line interface for master automation."""
    parser = argparse.ArgumentParser(
        description="Master Video Automation Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Character video with consistency
  python master_manager.py --type character --idea "Detective solves mystery" --scenes 5
  
  # Info video with manual niche
  python master_manager.py --type info --niche "Space discoveries" --mode ai --parallel
  
  # Info video with URL-based niche discovery
  python master_manager.py --type info --niche-mode url --url "https://youtube.com/watch?v=..."
  
  # Info video with auto trend discovery
  python master_manager.py --type info --niche-mode auto --mode ai
  
  # Batch production
  python master_manager.py --batch batch_config.json
  
  # Show capabilities
  python master_manager.py --summary
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['character', 'info'],
        help='Pipeline type'
    )
    
    parser.add_argument(
        '--idea',
        type=str,
        help='Video idea (for character videos)'
    )
    
    parser.add_argument(
        '--niche',
        type=str,
        help='Content niche (for info videos with niche-mode=manual)'
    )
    
    parser.add_argument(
        '--niche-mode',
        choices=['url', 'auto', 'manual'],
        default='manual',
        help='Niche discovery mode: url (analyze YouTube), auto (trending), manual (typed)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='YouTube URL for niche discovery (required if niche-mode=url)'
    )
    
    parser.add_argument(
        '--scenes',
        type=int,
        default=5,
        help='Number of scenes (character) or clips (info)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['ai', 'stock', 'hybrid'],
        default='ai',
        help='Video mode for info pipeline'
    )
    
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Use sequential processing (default: parallel)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Use parallel processing (default: True)'
    )
    
    parser.add_argument(
        '--pipeline',
        action='store_true',
        default=True,
        dest='pipeline_mode',
        help='Use pipeline mode - workers start immediately after login (default: True)'
    )
    
    parser.add_argument(
        '--consistency',
        action='store_true',
        default=True,
        help='Enable Veo 3.1 consistency (character)'
    )
    
    parser.add_argument(
        '--chained-consistency',
        action='store_true',
        default=True,
        dest='chained_consistency',
        help='Enable chained consistency (Scene N -> Scene N+1) (default: True)'
    )
    
    parser.add_argument(
        '--no-chained-consistency',
        action='store_false',
        dest='chained_consistency',
        help='Disable chained consistency, use pre-generated character images instead'
    )
    
    parser.add_argument(
        '--shared-session',
        action='store_true',
        default=True,
        dest='shared_session',
        help='Enable shared session (1 account for images+videos) (default: True)'
    )
    
    parser.add_argument(
        '--no-shared-session',
        action='store_false',
        dest='shared_session',
        help='Disable shared session, use separate accounts for image and video generators'
    )
    
    # Smart Reference System (NEW)
    parser.add_argument(
        '--character-ref',
        type=str,
        help='Character reference image for consistent appearance across scenes'
    )
    
    parser.add_argument(
        '--background-ref',
        type=str,
        help='Background/style reference image for environmental consistency'
    )
    
    parser.add_argument(
        '--batch',
        type=str,
        help='Batch config JSON file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browsers in headless mode'
    )
    
    parser.add_argument(
        '--no-emotion',
        action='store_true',
        help='Disable emotional script generation'
    )
    
    parser.add_argument(
        '--pool-size',
        type=int,
        default=5,
        help='Number of accounts in the account pool (default: 5)'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show system capabilities'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = MasterVideoAutomation(
        output_dir=args.output,
        headless=args.headless,
        use_emotional_ai=not args.no_emotion,
        pool_size=args.pool_size
    )
    
    # Show summary
    if args.summary:
        manager.print_summary()
        return 0
    
    # Batch mode
    if args.batch:
        print(f"[BATCH] Loading config from: {args.batch}")
        with open(args.batch, 'r') as f:
            batch_config = json.load(f)
        
        results = manager.batch_produce(batch_config)
        
        successful = sum(1 for r in results if r.get('status') == 'completed')
        print(f"\n[BATCH COMPLETE] {successful}/{len(results)} successful")
        
        return 0 if successful == len(results) else 1
    
    # Single video mode
    if args.type == 'character':
        if not args.idea:
            print("[ERROR] --idea required for character videos")
            return 1
        
        result = manager.produce_character_video(
            video_idea=args.idea,
            num_scenes=args.scenes,
            use_consistency=args.consistency,
            parallel=args.parallel and not args.sequential,
            pipeline_mode=args.pipeline_mode,
            chained_consistency=args.chained_consistency,
            shared_session=args.shared_session,
            character_ref=args.character_ref,  # NEW: Smart reference
            background_ref=args.background_ref  # NEW: Smart reference
        )
        
    elif args.type == 'info':
        # Validate niche mode requirements
        if args.niche_mode == 'url' and not args.url:
            print("[ERROR] --url required when using --niche-mode url")
            return 1
        elif args.niche_mode == 'manual' and not args.niche:
            print("[ERROR] --niche required when using --niche-mode manual")
            return 1
        
        result = manager.produce_info_video(
            niche=args.niche,
            video_mode=args.mode,
            num_videos=args.scenes,
            parallel=args.parallel and not args.sequential,
            niche_mode=args.niche_mode,
            video_url=args.url
        )
    
    else:
        parser.print_help()
        return 1
    
    # Check result
    if result.get('status') == 'completed':
        print("\n[DONE] VIDEO PRODUCTION COMPLETE!")
        return 0
    else:
        print("\n[FAIL] VIDEO PRODUCTION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
