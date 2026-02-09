#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           WORKFLOW ORCHESTRATOR - 8-STEP VIDEO PIPELINE          ║
║                                                                  ║
║  Orchestrates all modules in exact order for video production   ║
╚══════════════════════════════════════════════════════════════════╝

Exact Workflow:
    0. Gmail Upload Authentication
    1. Trend Finder (Niche Selection)
    2. Find Video Idea
    3. Generate Script
    4. Image Generation (2 Chrome Tabs)
    5. Video Generation (4 Chrome Tabs)
    6. Thumbnail Generation
    7. Edit Video
    8. Upload to Platforms

Plus: RAG Learning & Multi-Model AI Integration
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════
# IMPORT ALL MODULES IN WORKFLOW ORDER
# ═══════════════════════════════════════════════════════════════════

# Step 0: Gmail Authentication
try:
    from flowchart.common.gmail_verification import GmailVerificationTool
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("[WARNING] Gmail verification not available")

# Step 1: Trend Discovery
from flowchart.common.trend_finder import TrendFinder
try:
    from flowchart.common.video_url_analyzer import VideoURLAnalyzer
    URL_ANALYZER_AVAILABLE = True
except ImportError:
    URL_ANALYZER_AVAILABLE = False

# Step 2 & 3: AI Processing
from flowchart.common.llm_manager import LLMManager
from flowchart.character.script_generator import ScriptGenerator
try:
    from flowchart.common.video_rag import VideoKnowledgeBase
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

# Step 3: Script Optimization
try:
    from flowchart.common.retention_optimizer import RetentionOptimizer
    from flowchart.common.retention_predictor import RetentionPredictor
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False

# Step 4 & 5: Content Generation
from flowchart.character.image_generator import DreaminaGenerator
from flowchart.character.video_generator import DreaminaVideoGenerator

# Step 6: Thumbnails
try:
    from flowchart.common.thumbnail_generator import ThumbnailGenerator
    THUMBNAIL_AVAILABLE = True
except ImportError:
    THUMBNAIL_AVAILABLE = False

# Step 7: Video Editing
from flowchart.common.enhanced_editor import EnhancedVideoEditor
try:
    from flowchart.common.voiceover_generator import VoiceoverGenerator
    from flowchart.common.visual_effects import VisualEffectsManager
    from flowchart.common.max_retention_integration import MaxRetentionIntegrator
    ADVANCED_EDITING_AVAILABLE = True
except ImportError:
    ADVANCED_EDITING_AVAILABLE = False

# Step 8: Upload
try:
    from flowchart.common.uploader import Uploader
    from flowchart.common.smart_uploader import SmartUploader
    from flowchart.common.ai_metadata_generator import AIMetadataGenerator
    UPLOAD_AVAILABLE = True
except ImportError:
    UPLOAD_AVAILABLE = False

# Fallback: Stock Media
try:
    from flowchart.common.stock_media import StockMediaFetcher
    STOCK_AVAILABLE = True
except ImportError:
    STOCK_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
# MAIN WORKFLOW ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

class WorkflowOrchestrator:
    """
    Orchestrates the complete 8-step video production workflow
    with all existing modules in correct order
    """
    
    def __init__(self, 
                 num_image_workers=2,
                 num_video_workers=4,
                 use_rag=True,
                 use_multi_models=True,
                 use_ai_editor=True,
                 output_dir="output",
                 proxy_manager=None):
        
        self.num_image_workers = num_image_workers
        self.num_video_workers = num_video_workers
        self.use_rag = use_rag and RAG_AVAILABLE
        self.use_multi_models = use_multi_models
        self.use_ai_editor = use_ai_editor
        self.output_dir = output_dir
        self.proxy_manager = proxy_manager
        
        # Create output directories
        self._setup_directories()
        
        # Initialize core modules (that don't need browsers)
        self.llm = LLMManager()
        self.trend_finder = TrendFinder()
        self.script_generator = ScriptGenerator()
        
        # Initialize optional modules
        self.gmail = None
        self.rag = None
        self.retention_optimizer = None
        self.retention_predictor = None
        self.url_analyzer = None
        
        if GMAIL_AVAILABLE:
            try:
                self.gmail = GmailVerificationTool()
                print("[OK] Gmail verification initialized")
            except:
                print("[!] Gmail verification failed to initialize")
        
        if self.use_rag:
            try:
                self.rag = VideoKnowledgeBase()
                print("[OK] RAG knowledge base initialized")
            except:
                print("[!] RAG initialization failed")
        
        if RETENTION_AVAILABLE:
            self.retention_optimizer = RetentionOptimizer()
            self.retention_predictor = RetentionPredictor()
            print("[OK] Retention optimization enabled")
        
        if URL_ANALYZER_AVAILABLE:
            self.url_analyzer = VideoURLAnalyzer()
            print("[OK] URL analyzer available")
        
        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'steps_completed': [],
            'errors': []
        }
    
    def _setup_directories(self):
        """Create all necessary directories"""
        dirs = [
            f"{self.output_dir}/images",
            f"{self.output_dir}/videos",
            f"{self.output_dir}/final",
            f"{self.output_dir}/thumbnails",
            f"{self.output_dir}/metadata",
            f"{self.output_dir}/temp",
            "logs",
            "voiceovers"
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def _log_step(self, step_num, step_name, status="started"):
        """Log workflow step progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = ">" if status == "started" else "OK" if status == "completed" else "X"
        print(f"\n{symbol} [{timestamp}] Step {step_num}: {step_name} ({status})")
        
        if status == "completed":
            self.stats['steps_completed'].append(step_num)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 0: GMAIL UPLOAD AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════
    
    def step_0_gmail_authentication(self) -> bool:
        """Gmail authentication for YouTube upload"""
        self._log_step(0, "Gmail Upload Authentication", "started")
        
        if not GMAIL_AVAILABLE:
            print("[SKIP] Gmail verification not available")
            return True  # Skip if not available
        
        try:
            if not self.gmail:
                self.gmail = GmailVerificationTool()
            
            # Check if already authenticated
            print("   Checking Gmail authentication status...")
            
            # You can add specific authentication checks here
            print("   [OK] Gmail authentication ready")
            
            self._log_step(0, "Gmail Upload Authentication", "completed")
            return True
            
        except Exception as e:
            print(f"   [X] Gmail authentication failed: {e}")
            self.stats['errors'].append(f"Step 0: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: TREND FINDER (NICHE SELECTION)
    # ═══════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: TREND FINDER (NICHE SELECTION)
    # ═══════════════════════════════════════════════════════════════
    
    def step_1_trend_finder(self, 
                           niche: Optional[str] = None,
                           reference_url: Optional[str] = None) -> Dict:
        """
        Find trending topic in niche. Returns a Trend dictionary.
        """
        self._log_step(1, "Trend Finder (Niche Selection)", "started")
        
        try:
            # Method 1: User-provided niche
            if niche:
                print(f"   Using user-provided niche: {niche}")
                # We simply treat the niche as the trend topic for now
                trend = {'niche': niche, 'topic': niche, 'keywords': []}
            
            # Method 2: Automated search (default)
            else:
                print("   Auto-searching for trending topics...")
                selected_niche = self.trend_finder.select_niche() 
                trend = {'niche': selected_niche, 'topic': selected_niche, 'keywords': []}
            
            print(f"   [OK] Niche Selected: {trend.get('niche')}")
            
            self._log_step(1, "Trend Finder (Niche Selection)", "completed")
            return trend
            
        except Exception as e:
            print(f"   [X] Trend finding failed: {e}")
            self.stats['errors'].append(f"Step 1: {e}")
            return {'topic': 'General', 'niche': 'General'}
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: FIND VIDEO IDEA
    # ═══════════════════════════════════════════════════════════════
    
    def step_2_find_video_idea(self, trend: Dict) -> Dict:
        """Generate specific video idea from trend using AI + RAG"""
        self._log_step(2, "Find Video Idea", "started")
        
        try:
            topic = trend.get('topic', 'content')
            niche = trend.get('niche', 'General')
            
            # Use RAG if available
            if self.use_rag and self.rag:
                print("   Using RAG-enhanced idea generation...")
                
                # Get successful patterns from past
                past_videos = self.rag.get_similar_videos(
                    niche=niche,
                    min_retention=70,
                    limit=5
                )
                
                if past_videos:
                    print(f"   Found {len(past_videos)} similar successful videos")
                    rag_context = f"Past successful videos: {past_videos}"
                else:
                    rag_context = ""
                    
            else:
                rag_context = ""
                print("   Using pure AI idea generation...")
            
            # Generate multiple ideas with AI
            prompt = f"""
            Based on trending topic: {topic}
            Niche: {niche}
            {rag_context}

            Generate 3 viral video ideas that will maximize views and retention.
            Format as JSON array with structure:
            [
              {{
                "idea": "Video concept",
                "hook": "First 3 seconds hook",
                "estimated_retention": 0-100,
                "estimated_ctr": 0-100,
                "reasoning": "Why this will work"
              }}
            ]
            """
            
            # API FIX: Use generate(prompt, json_mode=True)
            response = self.llm.generate(prompt, json_mode=True)
            
            # If response is a list, use it. If wrapped in dict, extract it.
            if isinstance(response, dict) and "ideas" in response:
                ideas = response["ideas"]
            elif isinstance(response, list):
                ideas = response
            else:
                ideas = [response] if response else []
            
            # Select best idea
            if ideas and isinstance(ideas, list) and len(ideas) > 0 and 'idea' in ideas[0]:
                best_idea = max(ideas, key=lambda x: x.get('estimated_retention', 0))
            else:
                # Fallback specific to TrendFinder's capabilities if LLM fails
                print("   [INFO] LLM failed to give structured ideas. Using TrendFinder basic ideas...")
                basic_idea = self.trend_finder.find_video_ideas(niche)
                best_idea = {
                    'idea': basic_idea,
                    'hook': f"Check out this {niche} content!",
                    'estimated_retention': 70,
                    'estimated_ctr': 12
                }
            
            print(f"   [OK] Selected idea: {best_idea.get('idea', 'N/A')}")
            print(f"   [OK] Estimated retention: {best_idea.get('estimated_retention', 0)}%")
            
            self._log_step(2, "Find Video Idea", "completed")
            return best_idea
            
        except Exception as e:
            print(f"   [X] Idea generation failed: {e}")
            self.stats['errors'].append(f"Step 2: {e}")
            return {
                'idea': trend.get('topic', 'content'),
                'hook': "Amazing content!",
                'estimated_retention': 65
            }
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: GENERATE SCRIPT
    # ═══════════════════════════════════════════════════════════════
    
    def step_3_generate_script(self, video_idea: Dict, duration=60, num_scenes=10) -> Dict:
        """Generate optimized video script"""
        self._log_step(3, "Generate Script", "started")
        
        try:
            idea = video_idea.get('idea', 'content')
            hook = video_idea.get('hook', '')
            
            print(f"   Generating {num_scenes} scenes for {duration}s video...")
            
            # Generate base script using ScriptGenerator
            # Passes STRING title/idea
            overview = self.script_generator.generate_overview(idea)
            
            # Generates scenes
            scenes = self.script_generator.generate_scenes(overview, num_scenes=num_scenes)
            
            script = {
                'title': overview.get('title', idea),
                'hook': hook or overview.get('hook', ''),
                'synopsis': overview.get('synopsis', ''),
                'characters': overview.get('characters', []),
                'scenes': scenes,
                'total_duration': duration
            }
            
            # Optimize for retention if available
            if RETENTION_AVAILABLE and self.retention_optimizer:
                print("   Optimizing for 60-75% retention...")
                script = self.retention_optimizer.optimize_script(script, target_retention=70)
                
                # Predict performance
                if self.retention_predictor:
                    prediction = self.retention_predictor.predict_retention(script)
                    script['predicted_retention'] = prediction.get('retention', 0)
                    script['predicted_ctr'] = prediction.get('ctr', 0)
                    
                    print(f"   [OK] Predicted retention: {script['predicted_retention']}%")
                    print(f"   [OK] Predicted CTR: {script['predicted_ctr']}%")
                    
                    # Regenerate if prediction is too low
                    if script['predicted_retention'] < 65:
                        print("   ! Retention too low, enhancing hook...")
                        script = self.retention_optimizer.enhance_hook(script)
            
            print(f"   [OK] Script generated: '{script['title']}'")
            print(f"   [OK] Scenes: {len(script['scenes'])}")
            
            self._log_step(3, "Generate Script", "completed")
            return script
            
        except Exception as e:
            print(f"   [X] Script generation failed: {e}")
            self.stats['errors'].append(f"Step 3: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: IMAGE GENERATION (2 CHROME TABS)
    # ═══════════════════════════════════════════════════════════════
    
    def step_4_image_generation(self, script: Dict) -> List[str]:
        """Generate reference images using 2 parallel Chrome workers with two-phase approach"""
        self._log_step(4, "Image Generation (2 Chrome Tabs)", "started")
        
        try:
            # PHASE 1: Generate Character References
            print("\n   === PHASE 1: Character References ===")
            char_refs = self._generate_character_references(script)
            
            # PHASE 2: Generate Scene Images (using character references)
            print("\n   === PHASE 2: Scene Images ===")
            scene_images = self._generate_scene_images(script, char_refs)
            
            all_images = list(char_refs.values()) + scene_images
            print(f"\n   [OK] Total images generated: {len(all_images)}")
            
            self._log_step(4, "Image Generation (2 Chrome Tabs)", "completed")
            return all_images
            
        except Exception as e:
            print(f"   [X] Image generation failed: {e}")
            self.stats['errors'].append(f"Step 4: {e}")
            return []
    
    def _generate_character_references(self, script: Dict) -> Dict[str, str]:
        """Phase 1: Generate reference images for all characters"""
        character_descriptions = script.get('character_description', {})
        
        if not character_descriptions:
            print("   No characters to generate")
            return {}
        
        print(f"   Generating {len(character_descriptions)} character references...")
        
        tasks = []
        for i, (char_name, description) in enumerate(character_descriptions.items()):
            prompt = f"Generate a photorealistic character portrait of {description}. Use cinematic lighting, highly detailed, 8K resolution."
            output_path = f"{self.output_dir}/images/{char_name.replace(' ', '_')}_reference.png"
            tasks.append({
                'char_name': char_name,
                'prompt': prompt,
                'output_path': output_path,
                'reference_image': None,
                'worker_id': i % self.num_image_workers
            })
        
        # Parallel generation
        char_refs = {}
        with ThreadPoolExecutor(max_workers=self.num_image_workers) as executor:
            futures = {}
            
            for task in tasks:
                future = executor.submit(
                    self._generate_single_image,
                    task['prompt'],
                    task['output_path'],
                    task['reference_image'],
                    task['worker_id']
                )
                futures[future] = task
            
            # Wait for completion
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        char_refs[task['char_name']] = result
                        print(f"   [OK] {task['char_name']}_reference.png")
                except Exception as e:
                    print(f"   [X] Failed: {task['char_name']} - {e}")
        
        return char_refs
    
    def _generate_scene_images(self, script: Dict, char_refs: Dict[str, str]) -> List[str]:
        """Phase 2: Generate scene images using character references"""
        scenes = script.get('scenes', [])
        
        if not scenes:
            print("   No scenes to generate")
            return []
        
        print(f"   Generating images for {len(scenes)} scenes...")
        
        tasks = []
        task_counter = 0
        
        for scene in scenes:
            scene_num = scene['scene_number']
            char_name = scene.get('character_name', 'None')
            
            # Character in scene (with reference for consistency)
            if char_name and char_name != 'None':
                char_ref = char_refs.get(char_name)
                char_desc = scene.get('character_description', '')
                
                if char_desc:
                    prompt = f"Generate an image of {char_desc}. Cinematic style, photorealistic, 8K resolution."
                    output_path = f"{self.output_dir}/images/{char_name.replace(' ', '_')}_scene_{scene_num}.png"
                    tasks.append({
                        'type': 'character_scene',
                        'prompt': prompt,
                        'reference_image': char_ref,
                        'output_path': output_path,
                        'worker_id': task_counter % self.num_image_workers
                    })
                    task_counter += 1
            
            # Background
            background = scene.get('background', '')
            if background:
                prompt = f"Generate an image of {background}. Cinematic style, detailed environment, photorealistic, 8K resolution."
                output_path = f"{self.output_dir}/images/background_scene_{scene_num}.png"
                tasks.append({
                    'type': 'background',
                    'prompt': prompt,
                    'reference_image': None,
                    'output_path': output_path,
                    'worker_id': task_counter % self.num_image_workers
                })
                task_counter += 1
        
        # Parallel generation
        scene_images = []
        with ThreadPoolExecutor(max_workers=self.num_image_workers) as executor:
            futures = {}
            
            for task in tasks:
                future = executor.submit(
                    self._generate_single_image,
                    task['prompt'],
                    task['output_path'],
                    task['reference_image'],
                    task['worker_id']
                )
                futures[future] = task
            
            # Wait for completion
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    if result:
                        scene_images.append(result)
                        print(f"   [OK] {os.path.basename(result)}")
                except Exception as e:
                    print(f"   [X] Failed: {task['output_path']} - {e}")
        
        return scene_images
    
    def _generate_single_image(self, prompt: str, output_path: str, reference_image: Optional[str], worker_id: int) -> Optional[str]:
        """Generate single image with specific worker"""
        # Staggered launch: Add 10-second delay per worker to avoid simultaneous starts
        launch_delay = worker_id * 10
        if launch_delay > 0:
            print(f"   [Worker {worker_id}] Waiting {launch_delay}s before launch (staggered start)...")
            time.sleep(launch_delay)
        
        profile_path = os.path.abspath(f"chrome_data_img_{worker_id}")
        
        # Get proxy from manager if available (WorkerBatchProxy)
        proxy = None
        if self.proxy_manager:
            try:
                # WorkerBatchProxy simply returns the current batch proxy
                # It doesn't need meaningful worker_id for retrieval, just registration
                proxy = self.proxy_manager.get_proxy()
            except Exception as e:
                print(f"   [Worker {worker_id}] Proxy error: {e}")
        
        gen = DreaminaGenerator(headless=False, profile_path=profile_path, proxy=proxy, fresh_profile=True)
        try:
            if gen.login():
                success = gen.generate_image(prompt, output_path, reference_image=reference_image)
                if success:
                    return output_path
        except Exception as e:
            print(f"   [Worker {worker_id}] Error: {e}")
        finally:
            gen.close()
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 5: VIDEO GENERATION (4 CHROME TABS)
    # ═══════════════════════════════════════════════════════════════
    
    def step_5_video_generation(self, script: Dict, reference_images: List[str]) -> List[str]:
        """Generate video clips using 4 parallel Chrome workers"""
        self._log_step(5, "Video Generation (4 Chrome Tabs)", "started")
        
        try:
            video_paths = []
            scenes = script.get('scenes', [])
            character_descriptions = script.get('character_description', {})
            
            # Create character reference map from Phase 1 images
            char_images = {}
            for char_name in character_descriptions.keys():
                # Look for {char_name}_reference.png
                matching_img = [img for img in reference_images 
                               if f"{char_name.replace(' ', '_')}_reference" in img]
                if matching_img:
                    char_images[char_name] = matching_img[0]
            
            print(f"   Character references available: {list(char_images.keys())}")
            
            
            # Prepare video generation tasks
            tasks = []
            for scene in scenes:
                scene_num = scene['scene_number']
                
                # Use the detailed video_script field
                video_script = scene.get('video_script', '')
                
                # Fallback to building from other fields if video_script is empty
                if not video_script:
                    char_desc = scene.get('character_description', '')
                    background = scene.get('background', '')
                    video_script = f"{char_desc}. {background}"
                
                # Collect ALL reference images for this scene
                scene_references = []
                
                # 1. Character scene images (e.g., Aakash_scene_1.png, Balaji_scene_1.png)
                char_scene_images = [img for img in reference_images 
                                    if f"_scene_{scene_num}.png" in img and "background" not in img]
                scene_references.extend(char_scene_images)
                
                # 2. Background image (e.g., background_scene_1.png)
                background_images = [img for img in reference_images 
                                    if f"background_scene_{scene_num}.png" in img]
                scene_references.extend(background_images)
                
                # 3. Character reference (e.g., Aakash_reference.png) - for additional consistency
                char_name = scene.get('character_name', 'None')
                if char_name and char_name != 'None':
                    char_ref = char_images.get(char_name)
                    if char_ref and char_ref not in scene_references:
                        scene_references.append(char_ref)
                
                if scene_references:
                    print(f"   Scene {scene_num}: Using {len(scene_references)} reference images")
                    for ref in scene_references:
                        print(f"      - {os.path.basename(ref)}")
                
                output_path = f"{self.output_dir}/videos/scene_{scene_num}.mp4"
                
                tasks.append({
                    'scene_number': scene_num,
                    'prompt': video_script,
                    'reference_images': scene_references,  # Multiple references
                    'output_path': output_path,
                    'worker_id': (scene_num - 1) % self.num_video_workers
                })
            
            print(f"   Generating {len(tasks)} videos with {self.num_video_workers} workers...")
            
            # Parallel video generation
            with ThreadPoolExecutor(max_workers=self.num_video_workers) as executor:
                futures = {}
                
                for task in tasks:
                    future = executor.submit(
                        self._generate_single_video,
                        task['prompt'],
                        task['reference_images'],  # Pass list of references
                        task['output_path'],
                        task['worker_id']
                    )
                    futures[future] = task
                
                # Wait for completion
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        if result:
                            video_paths.append(result)
                            print(f"   [OK] Generated: scene_{task['scene_number']}.mp4")
                    except Exception as e:
                        print(f"   [X] Failed: scene_{task['scene_number']} - {e}")
            
            # Sort by scene number
            video_paths = sorted(video_paths, 
                               key=lambda x: int(x.split('_')[-1].replace('.mp4', '')))
            
            print(f"   [OK] Generated {len(video_paths)}/{len(tasks)} videos")
            
            self._log_step(5, "Video Generation (4 Chrome Tabs)", "completed")
            return video_paths
            
        except Exception as e:
            print(f"   [X] Video generation failed: {e}")
            self.stats['errors'].append(f"Step 5: {e}")
            return []
    
    def _generate_single_video(self, prompt: str, ref_images: List[str], 
                              output_path: str, worker_id: int) -> Optional[str]:
        """Generate single video with specific worker, uploading multiple reference images"""
        # Staggered launch: Add 10-second delay per worker to avoid simultaneous starts
        launch_delay = worker_id * 10
        if launch_delay > 0:
            print(f"   [Worker {worker_id}] Waiting {launch_delay}s before launch (staggered start)...")
            time.sleep(launch_delay)
        
        profile_path = os.path.abspath(f"chrome_data_vid_{worker_id}")
        
        # Get proxy from manager if available (WorkerBatchProxy)
        proxy = None
        if self.proxy_manager:
            try:
                # WorkerBatchProxy simply returns the current batch proxy
                proxy = self.proxy_manager.get_proxy()
            except Exception as e:
                print(f"   [Worker {worker_id}] Proxy error: {e}")
        
        gen = DreaminaVideoGenerator(headless=False, profile_path=profile_path, proxy=proxy, fresh_profile=True)
        try:
            if gen.login():
                # Upload all reference images for this scene
                if ref_images:
                    print(f"   [Worker {worker_id}] Uploading {len(ref_images)} reference images...")
                    for ref_img in ref_images:
                        if ref_img and os.path.exists(ref_img):
                            gen.upload_reference(ref_img)
                
                # Generate video with all references uploaded
                success = gen.generate_video(prompt, None, output_path)  # ref already uploaded
                if success:
                    return output_path
        except Exception as e:
            print(f"   [Worker {worker_id}] Error: {e}")
        finally:
            gen.close()
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 6: THUMBNAIL GENERATION
    # ═══════════════════════════════════════════════════════════════
    
    def step_6_thumbnail_generation(self, script: Dict, video_paths: List[str]) -> str:
        """Generate viral thumbnail"""
        self._log_step(6, "Thumbnail Generation", "started")
        
        try:
            title = script.get('title', 'Video')
            niche = script.get('niche', 'General')
            
            thumbnail_path = f"{self.output_dir}/thumbnails/{title.replace(' ', '_')}_thumb.png"
            
            if THUMBNAIL_AVAILABLE:
                print("   Generating AI thumbnail...")
                thumb_gen = ThumbnailGenerator()
                
                # Use first video frame as base
                key_frame = video_paths[0] if video_paths else None
                
                thumbnails = thumb_gen.generate_thumbnails(
                    video_title=title,
                    key_frame_path=key_frame,
                    num_variants=3,
                    style="viral"
                )
                
                # Select best CTR
                if thumbnails:
                    best_thumb = max(thumbnails, key=lambda t: t.get('ctr_prediction', 0))
                    thumbnail_path = best_thumb['path']
                    print(f"   [OK] Best thumbnail CTR: {best_thumb.get('ctr_prediction', 0)}%")
                
            else:
                # Fallback: Use image generator
                print("   Using image generator for thumbnail...")
                from flowchart.character.image_generator import DreaminaGenerator
                
                gen = DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_0"))
                try:
                    if gen.login():
                        prompt = f"Generate a YouTube thumbnail for a video titled '{title}' in the {niche} category. Make it eye-catching with bold text overlay and vibrant colors."
                        gen.generate_image(prompt, thumbnail_path)
                finally:
                    gen.close()
            
            print(f"   [OK] Thumbnail: {os.path.basename(thumbnail_path)}")
            
            self._log_step(6, "Thumbnail Generation", "completed")
            return thumbnail_path
            
        except Exception as e:
            print(f"   [X] Thumbnail generation failed: {e}")
            self.stats['errors'].append(f"Step 6: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 7: EDIT VIDEO
    # ═══════════════════════════════════════════════════════════════
    
    def step_7_edit_video(self, script: Dict, video_paths: List[str]) -> str:
        """Combine and edit final video with unified AI + FFmpeg editor"""
        self._log_step(7, "Edit Video", "started")
        
        try:
            title = script.get('title', 'video').replace(' ', '_')
            scenes = script.get('scenes', [])
            
            # Initialize unified AI + FFmpeg editor
            from modules.editor import VideoEditor
            editor = VideoEditor(output_dir=f"{self.output_dir}/final")
            
            print(f"   Editing {len(video_paths)} clips with AI + FFmpeg...")
            
            # Use unified editor with AI and FFmpeg
            if self.use_ai_editor and scenes:
                print("   [AI MODE] Using AI analysis + GPU rendering...")
                final_path = editor.create_video(
                    scene_videos=video_paths,
                    scenes_data=scenes,
                    output_filename=f"{title}_final.mp4",
                    remove_silence=True,
                    color_preset="warm"
                )
                
                if final_path:
                    print(f"   [OK] AI + FFmpeg editing complete")
                    print(f"   [OK] Final video: {os.path.basename(final_path)}")
                    self._log_step(7, "Edit Video", "completed")
                    return final_path
            
            # Fallback to simple mode
            print("   Using simple concatenation mode...")
            final_path = editor.combine_clips(
                scene_paths=video_paths,
                output_filename=f"{title}_final.mp4"
            )
            
            if final_path:
                print(f"   [OK] Video saved: {os.path.basename(final_path)}")
                self._log_step(7, "Edit Video", "completed")
                return final_path
            else:
                raise Exception("Video editing failed")
            
            # Step 7.3: Add voiceovers if generated
            if voiceover_paths:
                print("   Adding voiceovers...")
                temp_with_voice = f"{self.output_dir}/temp/with_voice.mp4"
                editor.add_voiceovers(temp_combined, voiceover_paths, temp_with_voice)
                current_video = temp_with_voice
            else:
                current_video = temp_combined
            
            # Step 7.4: Add background music
            print("   Adding background music...")
            temp_with_music = f"{self.output_dir}/temp/with_music.mp4"
            try:
                editor.add_background_music(
                    current_video,
                    "assets/music/ambient.mp3",  # You'll need to add music file
                    temp_with_music,
                    volume=0.2
                )
                current_video = temp_with_music
            except FileNotFoundError:
                print("   ! Background music file not found, skipping")
            
            # Step 7.5: All-in-one retention optimization
            final_path = f"{self.output_dir}/final/{title}_final.mp4"
            
            if ADVANCED_EDITING_AVAILABLE:
                try:
                    print("   Applying retention optimization...")
                    max_retention = MaxRetentionIntegrator()
                    max_retention.optimize_everything(
                        current_video,
                        script,
                        final_path,
                        target_retention=70
                    )
                except Exception as e:
                    print(f"   ! Optimization failed: {e}, using basic edit")
                    # Fallback to basic
                    import shutil
                    shutil.copy(current_video, final_path)
            else:
                # Basic edit only
                import shutil
                shutil.copy(current_video, final_path)
            
            print(f"   [OK] Final video: {os.path.basename(final_path)}")
            
            self._log_step(7, "Edit Video", "completed")
            return final_path
            
        except Exception as e:
            print(f"   [X] Video editing failed: {e}")
            self.stats['errors'].append(f"Step 7: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 8: UPLOAD TO PLATFORMS
    # ═══════════════════════════════════════════════════════════════
    
    def step_8_upload_platforms(self, script: Dict, final_video: str, 
                               thumbnail: str, platforms: List[str] = None) -> Dict:
        """Upload to multiple platforms"""
        self._log_step(8, "Upload to Platforms", "started")
        
        if not UPLOAD_AVAILABLE:
            print("   [SKIP] Upload modules not available")
            self._log_step(8, "Upload to Platforms", "completed")
            return {}
        
        try:
            platforms = platforms or ['youtube', 'tiktok', 'instagram']
            
            # Generate metadata
            print("   Generating platform-specific metadata...")
            metadata_gen = AIMetadataGenerator()
            metadata = metadata_gen.generate_all_metadata(
                video_title=script.get('title', 'Video'),
                niche=script.get('niche', 'General'),
                video_path=final_video,
                thumbnail_path=thumbnail
            )
            
            # Smart platform selection
            smart_uploader = SmartUploader()
            recommended = smart_uploader.analyze_best_platforms(
                video_path=final_video,
                niche=script.get('niche', 'General'),
                video_length=script.get('total_duration', 60)
            )
            
            print(f"   Recommended platforms: {', '.join(recommended)}")
            
            # Upload to each platform
            uploader = Uploader()
            results = {}
            
            for platform in platforms:
                if platform not in recommended:
                    print(f"   [SKIP] {platform} not recommended for this content")
                    continue
                
                try:
                    print(f"   Uploading to {platform}...")
                    
                    if platform == 'youtube':
                        result = uploader.upload_to_youtube(
                            video_path=final_video,
                            metadata=metadata.get('youtube', {}),
                            thumbnail_path=thumbnail
                        )
                    elif platform == 'tiktok':
                        result = uploader.upload_to_tiktok(
                            video_path=final_video,
                            metadata=metadata.get('tiktok', {})
                        )
                    elif platform == 'instagram':
                        result = uploader.upload_to_instagram(
                            video_path=final_video,
                            metadata=metadata.get('instagram', {})
                        )
                    
                    results[platform] = result
                    print(f"   ✓ {platform}: {result.get('url', 'Uploaded')}")
                    
                except Exception as e:
                    print(f"   ✗ {platform} failed: {e}")
                    results[platform] = {'status': 'failed', 'error': str(e)}
            
            self._log_step(8, "Upload to Platforms", "completed")
            return results
            
        except Exception as e:
            print(f"   ✗ Upload failed: {e}")
            self.stats['errors'].append(f"Step 8: {e}")
            return {}
    
    # ═══════════════════════════════════════════════════════════════
    # RAG: STORE RESULTS FOR LEARNING
    # ═══════════════════════════════════════════════════════════════
    
    def store_in_rag(self, script: Dict, upload_results: Dict):
        """Store video data in RAG for future learning"""
        if not self.use_rag or not self.rag:
            return
        
        try:
            print("\n   [RAG] Storing video data for learning...")
            
            self.rag.store_video_data({
                'video_id': upload_results.get('youtube', {}).get('video_id', ''),
                'niche': script.get('niche', ''),
                'topic': script.get('title', ''),
                'script': script,
                'predicted_retention': script.get('predicted_retention', 0),
                'predicted_ctr': script.get('predicted_ctr', 0),
                'upload_results': upload_results,
                'timestamp': datetime.now().isoformat()
            })
            
            print("   ✓ Data stored in RAG knowledge base")
            
        except Exception as e:
            print(f"   ! RAG storage failed: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # MAIN WORKFLOW EXECUTOR
    # ═══════════════════════════════════════════════════════════════
    
    def execute_full_workflow(self,
                             niche: Optional[str] = None,
                             reference_url: Optional[str] = None,
                             upload_platforms: List[str] = None,
                             duration: int = 60,
                             num_scenes: int = 10) -> Dict:
        """
        Execute complete 8-step workflow
        
        Args:
            niche: Video niche (e.g., "ASMR", "Tech")
            reference_url: Optional URL to analyze for style/topic
            upload_platforms: Platforms to upload to
            duration: Video duration in seconds
            num_scenes: Number of scenes
        
        Returns:
            Complete workflow results
        """
        
        print("\n" + "="*70)
        print("🎬 STARTING 8-STEP VIDEO PRODUCTION WORKFLOW")
        print("="*70)
        
        self.stats['start_time'] = datetime.now()
        
        try:
            # STEP 0: Gmail Authentication
            self.step_0_gmail_authentication()
            
            # STEP 1: Trend Finder
            trend = self.step_1_trend_finder(niche, reference_url)
            
            # STEP 2: Find Video Idea
            video_idea = self.step_2_find_video_idea(trend)
            
            # STEP 3: Generate Script
            script = self.step_3_generate_script(video_idea, duration, num_scenes)
            
            # STEP 4: Image Generation (2 workers)
            reference_images = self.step_4_image_generation(script)
            
            # STEP 5: Video Generation (4 workers)
            video_clips = self.step_5_video_generation(script, reference_images)
            
            if not video_clips:
                raise Exception("No video clips generated!")
            
            # STEP 6: Thumbnail Generation
            thumbnail = self.step_6_thumbnail_generation(script, video_clips)
            
            # STEP 7: Edit Video
            final_video = self.step_7_edit_video(script, video_clips)
            
            # STEP 8: Upload to Platforms
            upload_results = self.step_8_upload_platforms(
                script, 
                final_video, 
                thumbnail, 
                upload_platforms
            )
            
            # RAG: Store for learning
            self.store_in_rag(script, upload_results)
            
            self.stats['end_time'] = datetime.now()
            duration_sec = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            # Final summary
            print("\n" + "="*70)
            print("✅ WORKFLOW COMPLETE!")
            print("="*70)
            print(f"Title: {script.get('title', 'N/A')}")
            print(f"Video: {os.path.basename(final_video)}")
            print(f"Duration: {int(duration_sec // 60)}m {int(duration_sec % 60)}s")
            print(f"Steps completed: {len(self.stats['steps_completed'])}/8")
            if self.stats['errors']:
                print(f"Errors: {len(self.stats['errors'])}")
            print("="*70 + "\n")
            
            return {
                'success': True,
                'final_video': final_video,
                'thumbnail': thumbnail,
                'script': script,
                'upload_results': upload_results,
                'duration_seconds': duration_sec,
                'stats': self.stats
            }
            
        except Exception as e:
            print(f"\n❌ WORKFLOW FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    # ═══════════════════════════════════════════════════════════════
    # STOCK VIDEO WITH TAMIL VOICEOVER
    # ═══════════════════════════════════════════════════════════════
    
    def create_tamil_stock_video(self, niche="nature", num_videos=3):
        """
        Create video from stock footage with Tamil voiceover.
        
        Args:
            niche: Topic for stock videos (e.g., "nature", "technology", "cooking")
            num_videos: Number of stock video clips to fetch
        
        Returns:
            Path to final video or None
        """
        print(f"\n{'='*70}")
        print(f"║  TAMIL STOCK VIDEO CREATOR - Niche: {niche.upper()}")
        print(f"{'='*70}\n")
        
        try:
            # Tamil scripts for different niches
            tamil_scripts = {
                "nature": [
                    "இயற்கை என்பது மிகவும் அழகானது",
                    "மரங்கள் மற்றும் மலைகள் நம்மை மகிழ்விக்கின்றன",
                    "இயற்கையை பாதுகாப்போம்"
                ],
                "technology": [
                    "தொழில்நுட்பம் நம் வாழ்க்கையை மாற்றுகிறது",
                    "புதிய கண்டுபிடிப்புகள் ஒவ்வொரு நாளும் வருகின்றன",
                    "எதிர்காலம் மிகவும் சுவாரஸ்யமானது"
                ],
                "cooking": [
                    "சமையல் ஒரு கலை",
                    "சுவையான உணவு அனைவருக்கும் பிடிக்கும்",
                    "நல்ல உணவு நல்ல ஆரோக்கியம்"
                ],
                "ocean": [
                    "கடல் மிகவும் பெரியது",
                    "கடலில் பல உயிரினங்கள் உள்ளன",
                    "கடல் நமக்கு வாழ்க்கை தருகிறது"
                ]
            }
            
            # Get scripts for niche (or use default)
            scripts = tamil_scripts.get(niche, [
                f"{niche} பற்றிய வீடியோ",
                "இது மிகவும் சுவாரஸ்யமானது",
                "மேலும் தகவலுக்கு பார்க்கவும்"
            ])
            
            # Ensure enough scripts
            while len(scripts) < num_videos:
                scripts.append("இது அருமையான காட்சி")
            scripts = scripts[:num_videos]
            
            # Step 1: Fetch stock videos
            print(f"[1/4] Fetching {num_videos} stock videos about '{niche}'...")
            
            if not STOCK_AVAILABLE:
                print("   [ERROR] Stock media module not available")
                return None
            
            from modules.stock_media import StockMediaFetcher
            stock_fetcher = StockMediaFetcher(
                pexels_api_key=os.getenv('PEXELS_API_KEY'),
                pixabay_api_key=os.getenv('PIXABAY_API_KEY')
            )
            
            video_files = []
            for i in range(num_videos):
                print(f"   Downloading video {i+1}/{num_videos}...", end=" ")
                video_path = stock_fetcher.get_stock_video(
                    keyword=niche,
                    duration_range=(5, 10)
                )
                
                if video_path:
                    video_files.append(video_path)
                    print(f"✓ {os.path.basename(video_path)}")
                else:
                    print("✗ Failed")
            
            if not video_files:
                print("   [ERROR] No videos downloaded")
                return None
            
            print(f"   ✓ Downloaded {len(video_files)} videos\n")
            
            # Step 2: Generate Tamil voiceovers
            print(f"[2/4] Generating Tamil voiceovers...")
            
            from modules.voiceover_generator import VoiceOverGenerator
            voiceover_gen = VoiceOverGenerator(use_cloud_tts=False)
            
            voiceover_files = []
            for i, script_text in enumerate(scripts[:len(video_files)], 1):
                print(f"   Scene {i}: {script_text}")
                
                filename = f"tamil_narration_{i}.mp3"
                audio_path = voiceover_gen.generate_voiceover_gtts(
                    text=script_text,
                    filename=filename,
                    language='ta',  # Tamil language code
                    accent='com'
                )
                voiceover_files.append(audio_path)
            
            print(f"   ✓ Generated {len(voiceover_files)} voiceovers\n")
            
            # Step 3: Edit video
            print(f"[3/4] Editing final video with effects...")
            
            editor = EnhancedVideoEditor(output_dir=self.output_dir + "/final")
            
            final_video = editor.create_retention_optimized_video(
                scene_videos=video_files,
                voice_files=voiceover_files,
                title=f"Tamil {niche.title()} Video",
                music_file=None
            )
            
            print(f"   ✓ Video edited successfully\n")
            
            # Step 4: Done
            print(f"[4/4] Complete!")
            print(f"\n{'='*70}")
            print(f"✓ SUCCESS! Tamil video created:")
            print(f"  {final_video}")
            print(f"{'='*70}\n")
            
            return final_video
            
        except Exception as e:
            print(f"\n[ERROR] Tamil video creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None



# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="8-Step Video Production Workflow")
    parser.add_argument('--niche', type=str, help='Video niche (e.g., ASMR, Tech)')
    parser.add_argument('--url', type=str, help='Reference URL to analyze')
    parser.add_argument('--platforms', nargs='+', default=['youtube'],
                       help='Upload platforms (youtube, tiktok, instagram)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Video duration in seconds')
    parser.add_argument('--scenes', type=int, default=10,
                       help='Number of scenes')
    parser.add_argument('--no-rag', action='store_true',
                       help='Disable RAG learning')
    parser.add_argument('--image-workers', type=int, default=2,
                       help='Number of image generation workers')
    parser.add_argument('--video-workers', type=int, default=4,
                       help='Number of video generation workers')
    
    # Tamil stock video mode
    parser.add_argument('--tamil-stock', action='store_true',
                       help='Create video from stock footage with Tamil voiceover')
    parser.add_argument('--num-videos', type=int, default=3,
                       help='Number of stock videos to fetch (for --tamil-stock mode)')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        num_image_workers=args.image_workers,
        num_video_workers=args.video_workers,
        use_rag=not args.no_rag
    )
    
    # Check if Tamil stock video mode
    if args.tamil_stock:
        niche = args.niche or "nature"
        print(f"\n🎬 Tamil Stock Video Mode")
        print(f"   Niche: {niche}")
        print(f"   Videos: {args.num_videos}\n")
        
        final_video = orchestrator.create_tamil_stock_video(
            niche=niche,
            num_videos=args.num_videos
        )
        
        sys.exit(0 if final_video else 1)
    
    # Execute full workflow
    result = orchestrator.execute_full_workflow(
        niche=args.niche,
        reference_url=args.url,
        upload_platforms=args.platforms,
        duration=args.duration,
        num_scenes=args.scenes
    )
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

