#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         INFO CONTENT ORCHESTRATOR - STOCK + VOICEOVER            ║
║                                                                  ║
║  For Info/Documentary niches: Tech, Science, Facts, Educational ║
║  Uses: AI Graphics + Stock Footage + AI Voiceover               ║
╚══════════════════════════════════════════════════════════════════╝

Pipeline:
    1. Trend Finder (Niche Selection)
    2. Topic Research (Facts/Data Points)
    3. Generate Info Script (No Characters)
    4. AI Graphics Generation (Diagrams, Infographics)
    5. Stock Footage Fetching (Pexels/Pixabay B-Roll)
    6. Voiceover Generation (Gemini-TTS/gTTS)
    7. Video Editing (Combine All)
    8. Upload to Platforms
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════
# IMPORT MODULES
# ═══════════════════════════════════════════════════════════════════

# Core AI
from modules.llm_manager import LLMManager
from modules.trend_finder import TrendFinder

# INFO-SPECIFIC GENERATORS (NEW)
try:
    from modules.info_script_generator import InfoScriptGenerator
    INFO_SCRIPT_AVAILABLE = True
except ImportError:
    INFO_SCRIPT_AVAILABLE = False
    print("[WARNING] Info script generator not available")

try:
    from modules.generators.info_image_generator import InfoImageGenerator
    INFO_IMAGE_AVAILABLE = True
except ImportError:
    INFO_IMAGE_AVAILABLE = False
    print("[WARNING] Info image generator not available")

try:
    from modules.generators.info_video_generator import InfoVideoGenerator
    INFO_VIDEO_AVAILABLE = True
except ImportError:
    INFO_VIDEO_AVAILABLE = False
    print("[WARNING] Info video generator not available")

# HYBRID AI + STOCK VIDEO GENERATOR (NEW)
try:
    from modules.generators.hybrid_info_video_generator import HybridInfoVideoGenerator
    HYBRID_VIDEO_AVAILABLE = True
except ImportError:
    HYBRID_VIDEO_AVAILABLE = False
    print("[WARNING] Hybrid video generator not available")

try:
    from modules.info_thumbnail_generator import InfoThumbnailGenerator
    INFO_THUMBNAIL_AVAILABLE = True
except ImportError:
    INFO_THUMBNAIL_AVAILABLE = False
    print("[WARNING] Info thumbnail generator not available")

# Stock Media (fallback if InfoVideoGenerator not available)
try:
    from modules.stock_media import StockMediaFetcher
    STOCK_AVAILABLE = True
except ImportError:
    STOCK_AVAILABLE = False
    print("[WARNING] Stock media module not available")

# Voiceover
try:
    from modules.voiceover_generator import VoiceOverGenerator
    VOICEOVER_AVAILABLE = True
except ImportError:
    VOICEOVER_AVAILABLE = False
    print("[WARNING] Voiceover generator not available")

# Video Editing
try:
    from modules.enhanced_editor import EnhancedVideoEditor
    EDITOR_AVAILABLE = True
except ImportError:
    try:
        from modules.editor import VideoEditor as EnhancedVideoEditor
        EDITOR_AVAILABLE = True
    except ImportError:
        EDITOR_AVAILABLE = False
        print("[WARNING] Video editor not available")

# Upload
try:
    from modules.uploader import Uploader
    from modules.smart_uploader import SmartUploader
    from modules.ai_metadata_generator import AIMetadataGenerator
    UPLOAD_AVAILABLE = True
except ImportError:
    UPLOAD_AVAILABLE = False




# ═══════════════════════════════════════════════════════════════════
# INFO CONTENT ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

class InfoContentOrchestrator:
    """
    Orchestrates video production for INFO/DOCUMENTARY niches.
    
    Supports THREE video modes:
    - 'stock': Stock footage only (Pexels/Pixabay)
    - 'ai': AI-generated videos only (Veo3/Dreamina)
    - 'hybrid': AI + Stock combined (RECOMMENDED)
    
    Best for: Tech, Science, Facts, Educational, Documentary content.
    """
    
    # Niches optimized for this pipeline
    SUITABLE_NICHES = [
        "Technology", "Info Tech", "Science", "Facts",
        "Educational", "Documentary", "History Facts",
        "Space Facts", "Psychology Facts", "Health Tips",
        "Business", "Finance", "Crypto", "AI News"
    ]
    
    def __init__(self, 
                 output_dir="output_info",
                 use_ai_graphics=True,
                 num_stock_clips=5,
                 video_mode="hybrid",  # NEW: 'stock', 'ai', or 'hybrid'
                 ai_ratio=0.4,         # NEW: 40% AI, 60% Stock when hybrid
                 use_parallel=False,   # NEW: Parallel AI generation
                 num_ai_workers=4,     # NEW: Number of AI workers
                 headless=False):      # NEW: Headless browser mode
        
        self.output_dir = output_dir
        self.use_ai_graphics = use_ai_graphics and INFO_IMAGE_AVAILABLE
        self.num_stock_clips = num_stock_clips
        self.video_mode = video_mode
        self.ai_ratio = ai_ratio
        self.use_parallel = use_parallel
        self.num_ai_workers = num_ai_workers
        self.headless = headless
        
        # Create output directories
        self._setup_directories()
        
        # Initialize INFO-SPECIFIC generators
        self.llm = LLMManager()
        self.trend_finder = TrendFinder()
        
        # Info Script Generator (replaces character-based ScriptGenerator)
        self.script_gen = InfoScriptGenerator() if INFO_SCRIPT_AVAILABLE else None
        
        # Video Generator - based on mode
        self.video_gen = None
        self.hybrid_video_gen = None
        
        if video_mode == 'hybrid' and HYBRID_VIDEO_AVAILABLE:
            # Use hybrid AI + Stock generator
            self.hybrid_video_gen = HybridInfoVideoGenerator(
                output_dir=f"{output_dir}/videos",
                ai_ratio=ai_ratio,
                use_parallel=use_parallel,
                num_workers=num_ai_workers,
                headless=headless
            )
            print(f"[INFO] Video Mode: HYBRID (AI {ai_ratio*100:.0f}% + Stock {(1-ai_ratio)*100:.0f}%)")
        elif video_mode == 'stock' and INFO_VIDEO_AVAILABLE:
            # Stock only
            self.video_gen = InfoVideoGenerator(output_dir=f"{output_dir}/stock")
            print("[INFO] Video Mode: STOCK ONLY")
        elif video_mode == 'ai':
            # AI only - handled in step_5
            print("[INFO] Video Mode: AI ONLY")
        else:
            # Fallback to stock
            self.video_gen = InfoVideoGenerator(output_dir=f"{output_dir}/stock") if INFO_VIDEO_AVAILABLE else None
            print("[INFO] Video Mode: STOCK (fallback)")
        
        # Info Image Generator (infographics)
        self.image_gen = None  # Lazy loaded
        
        # Info Thumbnail Generator
        self.thumbnail_gen = InfoThumbnailGenerator(output_dir=f"{output_dir}/thumbnails") if INFO_THUMBNAIL_AVAILABLE else None
        
        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'steps_completed': [],
            'errors': [],
            'video_mode': video_mode
        }
    
    def _setup_directories(self):
        """Create all necessary directories"""
        dirs = [
            f"{self.output_dir}/stock",
            f"{self.output_dir}/graphics",
            f"{self.output_dir}/voiceovers",
            f"{self.output_dir}/final",
            f"{self.output_dir}/metadata",
            "logs"
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
    # STEP 1: TREND FINDER
    # ═══════════════════════════════════════════════════════════════
    
    def step_1_trend_finder(self, niche: Optional[str] = None) -> Dict:
        """Find trending topic in info niche"""
        self._log_step(1, "Trend Finder (Niche Selection)", "started")
        
        try:
            if niche:
                print(f"   Using provided niche: {niche}")
                trend = {'niche': niche, 'topic': niche}
            else:
                print("   Auto-searching for trending info topics...")
                selected_niche = self.trend_finder.select_niche()
                trend = {'niche': selected_niche, 'topic': selected_niche}
            
            print(f"   [OK] Niche Selected: {trend.get('niche')}")
            self._log_step(1, "Trend Finder", "completed")
            return trend
            
        except Exception as e:
            print(f"   [X] Trend finding failed: {e}")
            self.stats['errors'].append(f"Step 1: {e}")
            return {'niche': 'Technology', 'topic': 'Technology'}
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: TOPIC RESEARCH (Facts/Data)
    # ═══════════════════════════════════════════════════════════════
    
    def step_2_topic_research(self, trend: Dict) -> Dict:
        """Research topic and generate key facts/data points"""
        self._log_step(2, "Topic Research", "started")
        
        try:
            topic = trend.get('topic', 'technology')
            
            prompt = f"""
            Research the topic: {topic}
            
            Generate 5-8 interesting facts or data points that would make engaging video content.
            
            Return as JSON:
            {{
                "topic": "{topic}",
                "hook": "Attention-grabbing opening question or statement",
                "key_facts": [
                    {{"fact": "Interesting fact 1", "visual_keywords": ["keyword1", "keyword2"]}},
                    {{"fact": "Interesting fact 2", "visual_keywords": ["keyword1", "keyword2"]}}
                ],
                "conclusion": "Memorable closing statement"
            }}
            """
            
            research = self.llm.generate(prompt, json_mode=True)
            
            if not research or not isinstance(research, dict):
                research = {
                    "topic": topic,
                    "hook": f"Did you know these amazing facts about {topic}?",
                    "key_facts": [
                        {"fact": f"Fact about {topic}", "visual_keywords": [topic, "technology"]}
                    ],
                    "conclusion": f"That's all about {topic}!"
                }
            
            print(f"   [OK] Researched {len(research.get('key_facts', []))} facts")
            self._log_step(2, "Topic Research", "completed")
            return research
            
        except Exception as e:
            print(f"   [X] Research failed: {e}")
            self.stats['errors'].append(f"Step 2: {e}")
            return {"topic": trend.get('topic'), "key_facts": [], "hook": "", "conclusion": ""}
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: GENERATE INFO SCRIPT (No Characters)
    # ═══════════════════════════════════════════════════════════════
    
    def step_3_generate_info_script(self, research: Dict, duration: int = 60) -> Dict:
        """Generate info-style script with scenes (no characters)"""
        self._log_step(3, "Generate Info Script", "started")
        
        try:
            topic = research.get('topic', 'content')
            key_facts = research.get('key_facts', [])
            hook = research.get('hook', '')
            conclusion = research.get('conclusion', '')
            
            # Calculate scene timing
            num_facts = len(key_facts) if key_facts else 3
            scene_duration = max(5, duration // (num_facts + 2))  # +2 for intro/outro
            
            # Build scenes from facts
            scenes = []
            
            # Intro scene
            scenes.append({
                'scene_number': 1,
                'scene_type': 'intro',
                'narration': hook or f"Let's explore some amazing facts about {topic}!",
                'visual_type': 'stock',
                'stock_keywords': [topic, 'technology', 'modern'],
                'graphic_prompt': None,
                'duration': scene_duration
            })
            
            # Fact scenes
            for i, fact_data in enumerate(key_facts, start=2):
                fact = fact_data.get('fact', '') if isinstance(fact_data, dict) else str(fact_data)
                keywords = fact_data.get('visual_keywords', [topic]) if isinstance(fact_data, dict) else [topic]
                
                scenes.append({
                    'scene_number': i,
                    'scene_type': 'fact',
                    'narration': fact,
                    'visual_type': 'stock',  # Can be 'graphic' for AI-generated
                    'stock_keywords': keywords,
                    'graphic_prompt': f"Infographic visualization: {fact[:50]}",
                    'duration': scene_duration
                })
            
            # Outro scene
            scenes.append({
                'scene_number': len(scenes) + 1,
                'scene_type': 'outro',
                'narration': conclusion or f"Thanks for watching! Like and subscribe for more {topic} content!",
                'visual_type': 'stock',
                'stock_keywords': [topic, 'conclusion', 'subscribe'],
                'graphic_prompt': None,
                'duration': scene_duration
            })
            
            script = {
                'title': f"Amazing {topic} Facts",
                'niche': topic,
                'duration': duration,
                'scenes': scenes,
                'total_scenes': len(scenes)
            }
            
            print(f"   [OK] Generated script with {len(scenes)} scenes")
            self._log_step(3, "Generate Info Script", "completed")
            return script
            
        except Exception as e:
            print(f"   [X] Script generation failed: {e}")
            self.stats['errors'].append(f"Step 3: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: AI GRAPHICS GENERATION (Optional)
    # ═══════════════════════════════════════════════════════════════
    
    def step_4_generate_graphics(self, script: Dict) -> List[str]:
        """Generate AI graphics/infographics for scenes that need them"""
        self._log_step(4, "AI Graphics Generation", "started")
        
        if not self.use_ai_graphics:
            print("   [SKIP] AI graphics disabled")
            self._log_step(4, "AI Graphics Generation", "completed")
            return []
        
        try:
            graphics_paths = []
            scenes = script.get('scenes', [])
            
            # Find scenes that need graphics
            graphic_scenes = [s for s in scenes if s.get('visual_type') == 'graphic']
            
            if not graphic_scenes:
                print("   No scenes require AI graphics")
                self._log_step(4, "AI Graphics Generation", "completed")
                return []
            
            print(f"   Generating {len(graphic_scenes)} AI graphics...")
            
            # Use image generator
            profile_path = os.path.abspath("chrome_data_info_0")
            gen = DreaminaGenerator(headless=self.headless, profile_path=profile_path)
            
            try:
                if gen.login():
                    for scene in graphic_scenes:
                        scene_num = scene['scene_number']
                        prompt = scene.get('graphic_prompt', '')
                        
                        if prompt:
                            output_path = f"{self.output_dir}/graphics/scene_{scene_num}_graphic.png"
                            # Add info-graphic style modifiers
                            full_prompt = f"{prompt}, clean infographic style, modern design, blue and white color scheme, professional"
                            
                            success = gen.generate_image(full_prompt, output_path)
                            if success:
                                graphics_paths.append(output_path)
                                print(f"   [OK] Graphic for scene {scene_num}")
            finally:
                gen.close()
            
            print(f"   [OK] Generated {len(graphics_paths)} graphics")
            self._log_step(4, "AI Graphics Generation", "completed")
            return graphics_paths
            
        except Exception as e:
            print(f"   [X] Graphics generation failed: {e}")
            self.stats['errors'].append(f"Step 4: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 5: VIDEO GENERATION (HYBRID: AI + STOCK)
    # ═══════════════════════════════════════════════════════════════
    
    def step_5_generate_videos(self, script: Dict) -> List[str]:
        """
        Generate videos for all scenes using the configured video mode.
        
        Modes:
        - 'stock': Stock footage only (Pexels/Pixabay)
        - 'ai': AI-generated videos only (Veo3/Dreamina)
        - 'hybrid': AI + Stock combined (RECOMMENDED)
        
        Returns:
            List of video paths
        """
        mode_label = f"Video Generation ({self.video_mode.upper()})"
        self._log_step(5, mode_label, "started")
        
        scenes = script.get('scenes', [])
        
        if self.video_mode == 'hybrid' and self.hybrid_video_gen:
            # ═══════════════════════════════════════════════════════════
            # HYBRID MODE: AI + Stock Combined
            # ═══════════════════════════════════════════════════════════
            print(f"   [HYBRID] Generating videos with AI ({self.ai_ratio*100:.0f}%) + Stock ({(1-self.ai_ratio)*100:.0f}%)...")
            
            try:
                # Step 1: Assign sources (AI or Stock) to each scene
                scenes_with_sources = self.hybrid_video_gen.assign_scene_sources(scenes)
                
                # Step 2: Generate all videos
                video_paths = self.hybrid_video_gen.generate_scene_videos(scenes_with_sources)
                
                print(f"   [OK] Generated {len(video_paths)} videos (hybrid)")
                self._log_step(5, mode_label, "completed")
                return video_paths
                
            except Exception as e:
                print(f"   [X] Hybrid generation failed: {e}")
                self.stats['errors'].append(f"Step 5 (Hybrid): {e}")
                
                # Fallback to stock only
                print("   [FALLBACK] Trying stock-only mode...")
                return self._fetch_stock_only(scenes)
        
        elif self.video_mode == 'ai':
            # ═══════════════════════════════════════════════════════════
            # AI-ONLY MODE: Veo3/Dreamina (with optional parallel processing)
            # ═══════════════════════════════════════════════════════════
            
            # Sequential AI generation (fallback or default)
            print("   [AI] Generating all videos with AI (sequential)...")
            
            try:
                from modules.generators.video_generator import DreaminaVideoGenerator
                
                profile_path = os.path.abspath("chrome_data_info_video_0")
                gen = DreaminaVideoGenerator(headless=self.headless, profile_path=profile_path)
                
                video_paths = []
                
                try:
                    if gen.login():
                        for scene in scenes:
                            scene_num = scene['scene_number']
                            narration = scene.get('narration', '')
                            keywords = scene.get('stock_keywords', ['technology'])
                            
                            # Build prompt
                            keywords_str = ', '.join(keywords[:3]) if keywords else 'technology'
                            prompt = f"Professional documentary footage: {keywords_str}. {narration[:50]}. 4K quality, smooth motion."
                            
                            output_path = f"{self.output_dir}/videos/ai/scene_{scene_num}_ai.mp4"
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            
                            print(f"   Scene {scene_num}: {prompt[:50]}...")
                            
                            success = gen.generate_video(prompt, None, output_path)
                            if success and os.path.exists(output_path):
                                video_paths.append(output_path)
                                print(f"   [OK] Scene {scene_num} AI generated")
                            else:
                                print(f"   [X] Scene {scene_num} AI failed")
                finally:
                    gen.close()
                
                print(f"   [OK] Generated {len(video_paths)} AI videos")
                self._log_step(5, mode_label, "completed")
                return video_paths
                
            except Exception as e:
                print(f"   [X] AI generation failed: {e}")
                self.stats['errors'].append(f"Step 5 (AI): {e}")
                return []
        
        else:
            # ═══════════════════════════════════════════════════════════
            # STOCK-ONLY MODE: Pexels/Pixabay
            # ═══════════════════════════════════════════════════════════
            return self._fetch_stock_only(scenes)
    
    def _fetch_stock_only(self, scenes: List) -> List[str]:
        """Fetch stock footage for all scenes (internal helper)."""
        print("   [STOCK] Fetching stock footage...")
        
        if not STOCK_AVAILABLE:
            print("   [ERROR] Stock media module not available")
            return []
        
        try:
            stock_fetcher = StockMediaFetcher(
                pexels_api_key=os.getenv('PEXELS_API_KEY'),
                pixabay_api_key=os.getenv('PIXABAY_API_KEY')
            )
            
            video_paths = []
            
            print(f"   Fetching stock footage for {len(scenes)} scenes...")
            
            for scene in scenes:
                scene_num = scene['scene_number']
                keywords = scene.get('stock_keywords', ['technology'])
                
                # Try each keyword until we get a video
                video_path = None
                for keyword in keywords:
                    print(f"   Scene {scene_num}: Searching '{keyword}'...", end=" ")
                    
                    video_path = stock_fetcher.get_stock_video(
                        keyword=keyword,
                        duration_range=(5, 15)
                    )
                    
                    if video_path:
                        # Copy to our output directory with scene number
                        import shutil
                        dest_path = f"{self.output_dir}/stock/scene_{scene_num}_{os.path.basename(video_path)}"
                        shutil.copy(video_path, dest_path)
                        video_paths.append(dest_path)
                        print(f"OK")
                        break
                    else:
                        print(f"not found")
                
                if not video_path:
                    print(f"   [!] No video found for scene {scene_num}")
            
            print(f"   [OK] Fetched {len(video_paths)}/{len(scenes)} stock videos")
            self._log_step(5, "Video Generation (STOCK)", "completed")
            return video_paths
            
        except Exception as e:
            print(f"   [X] Stock fetching failed: {e}")
            self.stats['errors'].append(f"Step 5 (Stock): {e}")
            return []
    
    # Keep old method name for backward compatibility
    def step_5_fetch_stock_footage(self, script: Dict) -> List[str]:
        """DEPRECATED: Use step_5_generate_videos instead. Kept for backward compatibility."""
        return self.step_5_generate_videos(script)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 6: VOICEOVER GENERATION
    # ═══════════════════════════════════════════════════════════════
    
    def step_6_generate_voiceover(self, script: Dict, voice: str = "zephyr", 
                                   language: str = "en") -> List[str]:
        """Generate AI voiceover for all scenes"""
        self._log_step(6, "Voiceover Generation", "started")
        
        if not VOICEOVER_AVAILABLE:
            print("   [ERROR] Voiceover generator not available")
            self._log_step(6, "Voiceover Generation", "completed")
            return []
        
        try:
            voiceover_gen = VoiceOverGenerator(use_gemini_tts=True)
            
            voiceover_paths = []
            scenes = script.get('scenes', [])
            
            print(f"   Generating voiceovers for {len(scenes)} scenes...")
            
            for scene in scenes:
                scene_num = scene['scene_number']
                narration = scene.get('narration', '')
                
                if not narration:
                    continue
                
                print(f"   Scene {scene_num}: {narration[:50]}...")
                
                filename = f"scene_{scene_num}_voiceover.mp3"
                output_path = f"{self.output_dir}/voiceovers/{filename}"
                
                # Generate voiceover
                if language == "en":
                    audio_path = voiceover_gen.generate_voiceover(
                        text=narration,
                        filename=output_path,
                        voice=voice,
                        emotion="neutral"
                    )
                else:
                    # Use gTTS for other languages
                    audio_path = voiceover_gen.generate_voiceover_gtts(
                        text=narration,
                        filename=output_path,
                        language=language
                    )
                
                if audio_path:
                    voiceover_paths.append(audio_path)
                    print(f"   [OK] Voiceover for scene {scene_num}")
            
            print(f"   [OK] Generated {len(voiceover_paths)} voiceovers")
            self._log_step(6, "Voiceover Generation", "completed")
            return voiceover_paths
            
        except Exception as e:
            print(f"   [X] Voiceover generation failed: {e}")
            self.stats['errors'].append(f"Step 6: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 7: VIDEO EDITING
    # ═══════════════════════════════════════════════════════════════
    
    def step_7_edit_video(self, script: Dict, stock_videos: List[str], 
                          voiceovers: List[str], graphics: List[str] = None) -> str:
        """Combine stock footage + voiceovers + graphics into final video"""
        self._log_step(7, "Video Editing", "started")
        
        if not EDITOR_AVAILABLE:
            print("   [ERROR] Video editor not available")
            self._log_step(7, "Video Editing", "completed")
            return None
        
        try:
            title = script.get('title', 'info_video').replace(' ', '_')
            
            editor = EnhancedVideoEditor(output_dir=f"{self.output_dir}/final")
            
            print(f"   Combining {len(stock_videos)} clips with {len(voiceovers)} voiceovers...")
            
            # Create the final video
            final_path = editor.create_retention_optimized_video(
                scene_videos=stock_videos,
                voice_files=voiceovers,
                title=title,
                music_file=None
            )
            
            if final_path:
                print(f"   [OK] Final video: {os.path.basename(final_path)}")
            else:
                # Fallback to simple combine
                final_path = f"{self.output_dir}/final/{title}_final.mp4"
                editor.combine_clips(stock_videos, final_path)
                print(f"   [OK] Simple combine: {os.path.basename(final_path)}")
            
            self._log_step(7, "Video Editing", "completed")
            return final_path
            
        except Exception as e:
            print(f"   [X] Video editing failed: {e}")
            self.stats['errors'].append(f"Step 7: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 8: UPLOAD
    # ═══════════════════════════════════════════════════════════════
    
    def step_8_upload(self, script: Dict, final_video: str, 
                      platforms: List[str] = None) -> Dict:
        """Upload to platforms"""
        self._log_step(8, "Upload to Platforms", "started")
        
        if not UPLOAD_AVAILABLE:
            print("   [SKIP] Upload modules not available")
            self._log_step(8, "Upload to Platforms", "completed")
            return {}
        
        try:
            platforms = platforms or ['youtube']
            
            # Generate metadata
            metadata_gen = AIMetadataGenerator()
            metadata = metadata_gen.generate_all_metadata(
                video_title=script.get('title', 'Video'),
                niche=script.get('niche', 'Technology'),
                video_path=final_video
            )
            
            # Upload
            uploader = Uploader()
            results = {}
            
            for platform in platforms:
                try:
                    print(f"   Uploading to {platform}...")
                    if platform == 'youtube':
                        result = uploader.upload_to_youtube(
                            video_path=final_video,
                            metadata=metadata.get('youtube', {})
                        )
                        results[platform] = result
                except Exception as e:
                    results[platform] = {'status': 'failed', 'error': str(e)}
            
            self._log_step(8, "Upload to Platforms", "completed")
            return results
            
        except Exception as e:
            print(f"   [X] Upload failed: {e}")
            self.stats['errors'].append(f"Step 8: {e}")
            return {}
    
    # ═══════════════════════════════════════════════════════════════
    # FULL WORKFLOW EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    def execute_full_workflow(self, 
                              niche: Optional[str] = None,
                              duration: int = 60,
                              voice: str = "zephyr",
                              language: str = "en",
                              upload_platforms: List[str] = None,
                              skip_upload: bool = True) -> Dict:
        """
        Execute the complete Info Content workflow.
        
        Args:
            niche: Topic niche (e.g., "Technology", "Science")
            duration: Target video duration in seconds
            voice: Voice for voiceover (zephyr, puck, etc.)
            language: Language code (en, ta, hi, etc.)
            upload_platforms: Platforms to upload to
            skip_upload: Skip upload step (default True for testing)
        
        Returns:
            Result dictionary with final video path
        """
        print("\n" + "="*70)
        print("   INFO CONTENT ORCHESTRATOR - Stock + Voiceover Pipeline")
        print("="*70 + "\n")
        
        self.stats['start_time'] = datetime.now()
        
        try:
            # Step 1: Trend Finder
            trend = self.step_1_trend_finder(niche)
            
            # Step 2: Topic Research
            research = self.step_2_topic_research(trend)
            
            # Step 3: Generate Script
            script = self.step_3_generate_info_script(research, duration)
            
            # Step 4: AI Graphics (optional)
            graphics = []
            if self.use_ai_graphics:
                graphics = self.step_4_generate_graphics(script)
            else:
                print("\n[SKIP] Step 4: AI Graphics (disabled)")
            
            # Step 5: Stock Footage
            stock_videos = self.step_5_fetch_stock_footage(script)
            
            if not stock_videos:
                raise Exception("No stock videos fetched")
            
            # Step 6: Voiceover
            voiceovers = self.step_6_generate_voiceover(script, voice, language)
            
            # Step 7: Edit Video
            final_video = self.step_7_edit_video(script, stock_videos, voiceovers, graphics)
            
            if not final_video:
                raise Exception("Video editing failed")
            
            # Step 8: Upload (optional)
            upload_results = {}
            if not skip_upload and upload_platforms:
                upload_results = self.step_8_upload(script, final_video, upload_platforms)
            else:
                print("\n[SKIP] Step 8: Upload (skipped)")
            
            self.stats['end_time'] = datetime.now()
            duration_sec = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            print("\n" + "="*70)
            print("   WORKFLOW COMPLETE!")
            print("="*70)
            print(f"   Final Video: {final_video}")
            print(f"   Duration: {duration_sec:.1f} seconds")
            print(f"   Steps completed: {len(self.stats['steps_completed'])}/8")
            print("="*70 + "\n")
            
            return {
                'success': True,
                'final_video': final_video,
                'script': script,
                'stock_videos': stock_videos,
                'voiceovers': voiceovers,
                'graphics': graphics,
                'upload_results': upload_results,
                'stats': self.stats
            }
            
        except Exception as e:
            print(f"\n[ERROR] Workflow failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Info Content Orchestrator - AI + Stock Hybrid Video Pipeline"
    )
    parser.add_argument('--niche', type=str, default="Technology",
                       help='Info niche (Technology, Science, Facts, etc.)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Target video duration in seconds')
    parser.add_argument('--voice', type=str, default="zephyr",
                       help='Voice for voiceover (zephyr, puck, charon, etc.)')
    parser.add_argument('--language', type=str, default="en",
                       help='Language code (en, ta, hi, etc.)')
    parser.add_argument('--no-graphics', action='store_true',
                       help='Skip AI graphics generation')
    
    # NEW: Video mode options
    parser.add_argument('--video-mode', type=str, default="hybrid",
                       choices=['stock', 'ai', 'hybrid'],
                       help='Video mode: stock (Pexels/Pixabay), ai (Veo3), hybrid (AI+Stock)')
    parser.add_argument('--ai-ratio', type=float, default=0.4,
                       help='AI/Stock ratio for hybrid mode (0.0-1.0, default: 0.4 = 40%% AI)')
    parser.add_argument('--parallel', action='store_true',
                       help='Use parallel AI generation for faster processing')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel AI workers (default: 4)')
    
    # Upload options
    parser.add_argument('--upload', action='store_true',
                       help='Enable upload to platforms')
    parser.add_argument('--platforms', nargs='+', default=['youtube'],
                       help='Upload platforms')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate without actual API calls')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("   INFO CONTENT ORCHESTRATOR")
    print("="*70)
    print(f"   Niche: {args.niche}")
    print(f"   Duration: {args.duration}s")
    print(f"   Voice: {args.voice}")
    print(f"   Language: {args.language}")
    print(f"   AI Graphics: {not args.no_graphics}")
    print(f"   Video Mode: {args.video_mode.upper()}")
    if args.video_mode == 'hybrid':
        print(f"   AI Ratio: {args.ai_ratio*100:.0f}% AI / {(1-args.ai_ratio)*100:.0f}% Stock")
    print(f"   Parallel: {args.parallel} ({args.workers} workers)")
    print("="*70 + "\n")
    
    if args.dry_run:
        print("[DRY RUN MODE] Simulating workflow...\n")
        # TODO: Implement dry run
        sys.exit(0)
    
    # Create orchestrator with new options
    orchestrator = InfoContentOrchestrator(
        use_ai_graphics=not args.no_graphics,
        video_mode=args.video_mode,
        ai_ratio=args.ai_ratio,
        use_parallel=args.parallel,
        num_ai_workers=args.workers
    )
    
    # Execute workflow
    result = orchestrator.execute_full_workflow(
        niche=args.niche,
        duration=args.duration,
        voice=args.voice,
        language=args.language,
        upload_platforms=args.platforms if args.upload else None,
        skip_upload=not args.upload
    )
    
    sys.exit(0 if result['success'] else 1)

