#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           HYBRID INFO VIDEO GENERATOR (AI + Stock)               ║
║                                                                   ║
║  Combines AI-generated videos (Veo3) with Stock footage for      ║
║  Info/Documentary niches - Best of both worlds!                  ║
╚══════════════════════════════════════════════════════════════════╝

Features:
- AI Video Generation (Veo3/Dreamina) for key scenes
- Stock Footage (Pexels/Pixabay) for B-roll and filler
- Smart scene assignment based on visual requirements
- Fallback system: AI fails → Stock, Stock fails → AI
"""

import os
import shutil
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class HybridInfoVideoGenerator:
    """
    Hybrid Video Generator for INFO/DOCUMENTARY niches.
    
    SMART CLASSIFICATION:
    - AI Generation → Abstract, conceptual, futuristic, fantasy (non-real-life)
    - Stock Footage → Real-life scenes (people, nature, cities, activities)
    
    Best for: Tech, Science, Facts, Educational, Documentary content.
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # SMART SCENE CLASSIFICATION KEYWORDS
    # ═══════════════════════════════════════════════════════════════════
    
    # Keywords that indicate REAL-LIFE content → Use Stock
    REAL_LIFE_KEYWORDS = [
        # People & Activities
        'person', 'people', 'man', 'woman', 'child', 'family', 'team', 'worker',
        'walking', 'running', 'talking', 'working', 'eating', 'sleeping',
        'meeting', 'interview', 'presentation', 'handshake', 'celebration',
        
        # Places & Locations
        'office', 'city', 'street', 'building', 'house', 'room', 'kitchen',
        'hospital', 'school', 'university', 'factory', 'warehouse', 'shop',
        'restaurant', 'cafe', 'park', 'beach', 'mountain', 'forest', 'ocean',
        'road', 'highway', 'airport', 'station', 'mall', 'gym',
        
        # Nature & Animals (real)
        'nature', 'animal', 'bird', 'dog', 'cat', 'wildlife', 'tree', 'flower',
        'river', 'lake', 'sunset', 'sunrise', 'rain', 'snow', 'clouds',
        
        # Real Objects & Activities
        'car', 'vehicle', 'phone', 'laptop', 'computer', 'desk', 'chair',
        'food', 'cooking', 'sports', 'exercise', 'travel', 'driving',
        'doctor', 'engineer', 'teacher', 'scientist', 'business',
        
        # Documentary style
        'documentary', 'real', 'actual', 'footage', 'timelapse', 'aerial'
    ]
    
    # Keywords that indicate NON-REAL/ABSTRACT content → Use AI
    AI_PREFERRED_KEYWORDS = [
        # Abstract Concepts
        'abstract', 'concept', 'idea', 'thought', 'imagination', 'dream',
        'visualization', 'representation', 'metaphor', 'symbol',
        
        # Futuristic & Sci-Fi
        'future', 'futuristic', 'sci-fi', 'space', 'galaxy', 'universe',
        'alien', 'robot', 'android', 'cyborg', 'hologram', 'virtual',
        'cyberpunk', 'neon', 'digital', 'matrix', 'simulation',
        
        # Technology & AI Concepts
        'ai', 'artificial intelligence', 'neural', 'network', 'algorithm',
        'data flow', 'coding', 'binary', 'circuit', 'microchip', 'quantum',
        'blockchain', 'crypto', 'metaverse', 'augmented', 'ar', 'vr',
        
        # Fantasy & Mythical
        'fantasy', 'magical', 'mythical', 'dragon', 'unicorn', 'fairy',
        'enchanted', 'supernatural', 'mystical', 'ethereal',
        
        # Visual Effects
        'particles', 'explosion', 'portal', 'transformation', 'morphing',
        'floating', 'glowing', 'energy', 'wave', 'pulse', 'aura',
        
        # Infographics & Diagrams
        'infographic', 'diagram', 'chart', 'graph', 'statistics', 'data',
        'process', 'workflow', 'timeline', 'comparison', 'versus',
        
        # Intro/Outro style
        'intro', 'outro', 'title', 'logo', 'brand', 'opening', 'closing'
    ]
    
    def __init__(self, 
                 output_dir: str = "output_info/videos",
                 ai_ratio: float = 0.4,  # Fallback ratio if classification unclear
                 use_parallel: bool = False,
                 num_workers: int = 4):
        """
        Initialize Hybrid Video Generator.
        
        Args:
            output_dir: Directory for output videos
            ai_ratio: Ratio of scenes to use AI generation (0.0 to 1.0)
            use_parallel: Use parallel AI generation (requires multiple Chrome profiles)
            num_workers: Number of parallel workers for AI generation
        """
        self.output_dir = output_dir
        self.ai_ratio = ai_ratio
        self.use_parallel = use_parallel
        self.num_workers = num_workers
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/ai", exist_ok=True)
        os.makedirs(f"{output_dir}/stock", exist_ok=True)
        
        # Lazy load generators
        self._ai_generator = None
        self._stock_generator = None
        self._parallel_ai_generator = None
        
        # Statistics
        self.stats = {
            'ai_generated': 0,
            'stock_fetched': 0,
            'ai_failed': 0,
            'stock_failed': 0,
            'total_scenes': 0
        }
        
        print(f"[HYBRID] Video Generator initialized")
        print(f"   - AI Ratio: {ai_ratio * 100:.0f}% AI / {(1-ai_ratio) * 100:.0f}% Stock")
        print(f"   - Parallel: {use_parallel} ({num_workers} workers)")
    
    def _get_ai_generator(self):
        """Lazy load AI video generator."""
        if self._ai_generator is None:
            try:
                from .video_generator import DreaminaVideoGenerator
                profile_path = os.path.abspath("chrome_data_info_video_0")
                self._ai_generator = DreaminaVideoGenerator(
                    headless=False, 
                    profile_path=profile_path
                )
            except ImportError:
                try:
                    from modules.generators.video_generator import DreaminaVideoGenerator
                    profile_path = os.path.abspath("chrome_data_info_video_0")
                    self._ai_generator = DreaminaVideoGenerator(
                        headless=False, 
                        profile_path=profile_path
                    )
                except ImportError:
                    print("[WARNING] AI Video Generator not available")
                    return None
        return self._ai_generator
    
    def _get_parallel_ai_generator(self):
        """Lazy load parallel AI video generator."""
        if self._parallel_ai_generator is None:
            try:
                from .video_generator import MultiVeo3Generator
                self._parallel_ai_generator = MultiVeo3Generator(
                    num_workers=self.num_workers,
                    headless=False
                )
            except ImportError:
                try:
                    from modules.generators.video_generator import MultiVeo3Generator
                    self._parallel_ai_generator = MultiVeo3Generator(
                        num_workers=self.num_workers,
                        headless=False
                    )
                except ImportError:
                    print("[WARNING] Parallel AI Video Generator not available")
                    return None
        return self._parallel_ai_generator
    
    def _get_stock_generator(self):
        """Lazy load stock video fetcher."""
        if self._stock_generator is None:
            try:
                from .info_video_generator import InfoVideoGenerator
                self._stock_generator = InfoVideoGenerator(
                    output_dir=f"{self.output_dir}/stock"
                )
            except ImportError:
                try:
                    from modules.generators.info_video_generator import InfoVideoGenerator
                    self._stock_generator = InfoVideoGenerator(
                        output_dir=f"{self.output_dir}/stock"
                    )
                except ImportError:
                    print("[WARNING] Stock Video Generator not available")
                    return None
        return self._stock_generator
    
    def assign_scene_sources(self, scenes: List[Dict]) -> List[Dict]:
        """
        SMART CLASSIFICATION: Assign AI or Stock based on content type.
        
        - REAL-LIFE content (people, nature, cities) → STOCK
        - ABSTRACT/FANTASY content (AI, concepts, futuristic) → AI
        
        Args:
            scenes: List of scene dicts with 'narration', 'stock_keywords', etc.
        
        Returns:
            Same scenes with 'video_source' field added ('ai' or 'stock')
        """
        print(f"\n[HYBRID] Smart Content Classification for {len(scenes)} scenes...")
        print(f"   Logic: Real-Life → Stock | Abstract/Fantasy → AI\n")
        
        ai_count = 0
        stock_count = 0
        
        for scene in scenes:
            scene_num = scene.get('scene_number', 0)
            
            # Analyze scene content
            classification = self._classify_scene_content(scene)
            
            scene['video_source'] = classification['source']
            scene['classification_reason'] = classification['reason']
            scene['classification_score'] = classification['score']
            
            if classification['source'] == 'ai':
                ai_count += 1
                symbol = "🤖"
            else:
                stock_count += 1
                symbol = "📹"
            
            print(f"   Scene {scene_num}: {symbol} {classification['source'].upper()} - {classification['reason']}")
        
        print(f"\n   Summary: AI={ai_count} | Stock={stock_count}")
        
        return scenes
    
    def _classify_scene_content(self, scene: Dict) -> Dict:
        """
        Analyze scene content and classify as real-life or abstract.
        
        Returns:
            {'source': 'ai'/'stock', 'reason': str, 'score': float}
        """
        # Gather all text content from scene
        narration = scene.get('narration', '').lower()
        keywords = scene.get('stock_keywords', [])
        scene_type = scene.get('scene_type', '').lower()
        visual_desc = scene.get('visual_description', '').lower()
        
        # Combine all searchable text
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords_text = ' '.join([k.lower() for k in keywords])
        
        all_text = f"{narration} {keywords_text} {scene_type} {visual_desc}"
        
        # Count matches for each category
        real_life_score = 0
        ai_preferred_score = 0
        
        real_life_matches = []
        ai_matches = []
        
        # Check for real-life keywords
        for keyword in self.REAL_LIFE_KEYWORDS:
            if keyword in all_text:
                real_life_score += 1
                real_life_matches.append(keyword)
        
        # Check for AI-preferred keywords
        for keyword in self.AI_PREFERRED_KEYWORDS:
            if keyword in all_text:
                ai_preferred_score += 1
                ai_matches.append(keyword)
        
        # Determine source based on scores
        if ai_preferred_score > real_life_score:
            return {
                'source': 'ai',
                'reason': f"Abstract content ({', '.join(ai_matches[:3])})",
                'score': ai_preferred_score
            }
        elif real_life_score > ai_preferred_score:
            return {
                'source': 'stock',
                'reason': f"Real-life content ({', '.join(real_life_matches[:3])})",
                'score': real_life_score
            }
        else:
            # Tie-breaker: Check scene type for intro/outro
            if scene_type in ['intro', 'outro', 'opening', 'closing']:
                return {
                    'source': 'ai',
                    'reason': f"Intro/Outro scene (best with custom AI)",
                    'score': 1
                }
            else:
                # Default to stock for unclear cases (more realistic)
                return {
                    'source': 'stock',
                    'reason': "General content (defaulting to stock)",
                    'score': 0
                }
    
    def generate_ai_prompt_for_scene(self, scene: Dict) -> str:
        """
        Generate an optimized AI prompt for info-style video generation.
        
        Args:
            scene: Scene dict with 'narration', 'stock_keywords', etc.
        
        Returns:
            Optimized prompt string for Veo3/Dreamina
        """
        narration = scene.get('narration', '')
        keywords = scene.get('stock_keywords', [])
        scene_type = scene.get('scene_type', 'generic')
        
        # Build prompt based on scene type
        if scene_type == 'intro':
            prompt = f"Cinematic intro shot: {narration[:100]}. Smooth camera movement, dramatic lighting, modern tech aesthetic."
        elif scene_type == 'outro':
            prompt = f"Professional outro: {narration[:50]}. Clean ending shot, subtle motion, polished look."
        elif scene_type == 'fact':
            # For facts, create abstract/conceptual visualizations
            keywords_str = ', '.join(keywords[:3]) if keywords else 'technology'
            prompt = f"Abstract visualization of: {keywords_str}. Modern infographic style, flowing motion, clean design."
        else:
            keywords_str = ', '.join(keywords[:3]) if keywords else 'modern technology'
            prompt = f"Professional stock footage: {keywords_str}. 4K quality, smooth motion, documentary style."
        
        return prompt
    
    def generate_scene_videos(self, 
                              scenes: List[Dict],
                              reference_images: Dict[int, str] = None) -> List[str]:
        """
        Generate videos for all scenes using hybrid AI + Stock approach.
        
        Args:
            scenes: List of scene dicts (run assign_scene_sources first)
            reference_images: Optional dict mapping scene_number to reference image path
        
        Returns:
            List of video paths (ordered by scene number)
        """
        print(f"\n{'='*70}")
        print(f"  HYBRID VIDEO GENERATION - {len(scenes)} SCENES")
        print(f"{'='*70}")
        
        self.stats['total_scenes'] = len(scenes)
        reference_images = reference_images or {}
        
        # Separate AI and Stock scenes
        ai_scenes = [s for s in scenes if s.get('video_source') == 'ai']
        stock_scenes = [s for s in scenes if s.get('video_source') == 'stock']
        
        print(f"\n[HYBRID] Distribution:")
        print(f"   - AI Scenes: {len(ai_scenes)}")
        print(f"   - Stock Scenes: {len(stock_scenes)}")
        
        # Generate all videos
        video_results = {}  # scene_number -> video_path
        
        # Step 1: Generate AI videos
        if ai_scenes:
            ai_results = self._generate_ai_scenes(ai_scenes, reference_images)
            video_results.update(ai_results)
        
        # Step 2: Fetch Stock videos
        if stock_scenes:
            stock_results = self._fetch_stock_scenes(stock_scenes)
            video_results.update(stock_results)
        
        # Step 3: Handle failures with fallback
        failed_scenes = [s for s in scenes if s['scene_number'] not in video_results]
        if failed_scenes:
            print(f"\n[HYBRID] Handling {len(failed_scenes)} failed scenes with fallback...")
            fallback_results = self._handle_fallbacks(failed_scenes, reference_images)
            video_results.update(fallback_results)
        
        # Sort by scene number and return paths
        sorted_paths = []
        for scene in scenes:
            scene_num = scene['scene_number']
            if scene_num in video_results:
                sorted_paths.append(video_results[scene_num])
            else:
                print(f"[WARNING] No video for scene {scene_num}")
        
        # Print stats
        print(f"\n{'='*70}")
        print(f"  GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"   Total Scenes: {self.stats['total_scenes']}")
        print(f"   AI Generated: {self.stats['ai_generated']}")
        print(f"   Stock Fetched: {self.stats['stock_fetched']}")
        print(f"   AI Failed: {self.stats['ai_failed']}")
        print(f"   Stock Failed: {self.stats['stock_failed']}")
        print(f"   Videos Produced: {len(sorted_paths)}")
        print(f"{'='*70}\n")
        
        return sorted_paths
    
    def _generate_ai_scenes(self, 
                            scenes: List[Dict], 
                            reference_images: Dict[int, str]) -> Dict[int, str]:
        """Generate AI videos for scenes."""
        print(f"\n[AI] Generating {len(scenes)} AI videos...")
        results = {}
        
        if self.use_parallel and len(scenes) > 1:
            # Parallel generation
            results = self._generate_ai_parallel(scenes, reference_images)
        else:
            # Sequential generation
            results = self._generate_ai_sequential(scenes, reference_images)
        
        return results
    
    def _generate_ai_sequential(self, 
                                 scenes: List[Dict], 
                                 reference_images: Dict[int, str]) -> Dict[int, str]:
        """Generate AI videos sequentially."""
        results = {}
        
        gen = self._get_ai_generator()
        if not gen:
            print("[ERROR] AI Generator not available")
            return results
        
        try:
            # Login once
            print("[AI] Logging in to AI video service...")
            if not gen.login():
                print("[ERROR] AI login failed")
                return results
            
            for scene in scenes:
                scene_num = scene['scene_number']
                prompt = self.generate_ai_prompt_for_scene(scene)
                ref_image = reference_images.get(scene_num)
                output_path = f"{self.output_dir}/ai/scene_{scene_num}_ai.mp4"
                
                print(f"\n[AI] Scene {scene_num}: {prompt[:50]}...")
                
                try:
                    success = gen.generate_video(prompt, ref_image, output_path)
                    if success and os.path.exists(output_path):
                        results[scene_num] = output_path
                        self.stats['ai_generated'] += 1
                        print(f"[OK] Scene {scene_num} AI generated")
                    else:
                        self.stats['ai_failed'] += 1
                        print(f"[X] Scene {scene_num} AI failed")
                except Exception as e:
                    print(f"[ERROR] Scene {scene_num}: {e}")
                    self.stats['ai_failed'] += 1
                    
        except Exception as e:
            print(f"[ERROR] AI generation error: {e}")
        
        return results
    
    def _generate_ai_parallel(self, 
                               scenes: List[Dict], 
                               reference_images: Dict[int, str]) -> Dict[int, str]:
        """Generate AI videos in parallel."""
        results = {}
        
        gen = self._get_parallel_ai_generator()
        if not gen:
            print("[WARNING] Parallel generator not available, falling back to sequential")
            return self._generate_ai_sequential(scenes, reference_images)
        
        # Build task list
        tasks = []
        for scene in scenes:
            scene_num = scene['scene_number']
            tasks.append({
                'prompt': self.generate_ai_prompt_for_scene(scene),
                'reference_image_path': reference_images.get(scene_num),
                'output_path': f"{self.output_dir}/ai/scene_{scene_num}_ai.mp4",
                'scene_number': scene_num
            })
        
        try:
            output_paths = gen.generate_batch(tasks)
            
            # Map results back to scene numbers
            for task in tasks:
                scene_num = task['scene_number']
                output_path = task['output_path']
                if os.path.exists(output_path):
                    results[scene_num] = output_path
                    self.stats['ai_generated'] += 1
                else:
                    self.stats['ai_failed'] += 1
                    
        except Exception as e:
            print(f"[ERROR] Parallel generation error: {e}")
        
        return results
    
    def _fetch_stock_scenes(self, scenes: List[Dict]) -> Dict[int, str]:
        """Fetch stock videos for scenes."""
        print(f"\n[STOCK] Fetching {len(scenes)} stock videos...")
        results = {}
        
        gen = self._get_stock_generator()
        if not gen:
            print("[ERROR] Stock Generator not available")
            return results
        
        for scene in scenes:
            scene_num = scene['scene_number']
            keywords = scene.get('stock_keywords', ['technology'])
            
            # Ensure keywords is a list
            if isinstance(keywords, str):
                keywords = [keywords]
            
            print(f"\n[STOCK] Scene {scene_num}: {keywords}")
            
            try:
                video_path = gen.fetch_video(keywords, duration_range=(5, 15))
                
                if video_path and os.path.exists(video_path):
                    # Copy to our output directory
                    dest_path = f"{self.output_dir}/stock/scene_{scene_num}_stock.mp4"
                    shutil.copy(video_path, dest_path)
                    results[scene_num] = dest_path
                    self.stats['stock_fetched'] += 1
                    print(f"[OK] Scene {scene_num} stock fetched")
                else:
                    self.stats['stock_failed'] += 1
                    print(f"[X] Scene {scene_num} stock not found")
                    
            except Exception as e:
                print(f"[ERROR] Scene {scene_num}: {e}")
                self.stats['stock_failed'] += 1
        
        return results
    
    def _handle_fallbacks(self, 
                          failed_scenes: List[Dict], 
                          reference_images: Dict[int, str]) -> Dict[int, str]:
        """Try alternate source for failed scenes."""
        results = {}
        
        for scene in failed_scenes:
            scene_num = scene['scene_number']
            original_source = scene.get('video_source', 'stock')
            
            print(f"\n[FALLBACK] Scene {scene_num}: Original was {original_source}")
            
            # Try the opposite source
            if original_source == 'ai':
                # Try stock as fallback
                gen = self._get_stock_generator()
                if gen:
                    keywords = scene.get('stock_keywords', ['technology'])
                    if isinstance(keywords, str):
                        keywords = [keywords]
                    
                    video_path = gen.fetch_video(keywords)
                    if video_path and os.path.exists(video_path):
                        dest_path = f"{self.output_dir}/stock/scene_{scene_num}_fallback.mp4"
                        shutil.copy(video_path, dest_path)
                        results[scene_num] = dest_path
                        self.stats['stock_fetched'] += 1
                        print(f"[OK] Scene {scene_num} fallback to stock")
            else:
                # Try AI as fallback
                gen = self._get_ai_generator()
                if gen:
                    prompt = self.generate_ai_prompt_for_scene(scene)
                    ref_image = reference_images.get(scene_num)
                    output_path = f"{self.output_dir}/ai/scene_{scene_num}_fallback.mp4"
                    
                    try:
                        success = gen.generate_video(prompt, ref_image, output_path)
                        if success and os.path.exists(output_path):
                            results[scene_num] = output_path
                            self.stats['ai_generated'] += 1
                            print(f"[OK] Scene {scene_num} fallback to AI")
                    except Exception as e:
                        print(f"[X] Fallback failed: {e}")
        
        return results
    
    def close(self):
        """Close all open generators."""
        if self._ai_generator:
            try:
                self._ai_generator.close()
            except:
                pass
        print("[HYBRID] Generators closed")


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Info Video Generator (AI + Stock)")
    parser.add_argument('--topic', type=str, required=True,
                       help='Topic for video generation')
    parser.add_argument('--scenes', type=int, default=5,
                       help='Number of scenes to generate')
    parser.add_argument('--ai-ratio', type=float, default=0.4,
                       help='Ratio of AI vs Stock (0.0-1.0)')
    parser.add_argument('--parallel', action='store_true',
                       help='Use parallel AI generation')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Create test scenes
    test_scenes = []
    for i in range(1, args.scenes + 1):
        scene_type = 'intro' if i == 1 else 'outro' if i == args.scenes else 'fact'
        test_scenes.append({
            'scene_number': i,
            'scene_type': scene_type,
            'narration': f"Test narration for scene {i} about {args.topic}",
            'stock_keywords': [args.topic, 'technology', 'modern']
        })
    
    # Generate
    generator = HybridInfoVideoGenerator(
        ai_ratio=args.ai_ratio,
        use_parallel=args.parallel,
        num_workers=args.workers
    )
    
    try:
        # Assign sources
        scenes = generator.assign_scene_sources(test_scenes)
        
        # Generate videos
        videos = generator.generate_scene_videos(scenes)
        
        print(f"\n[RESULT] Generated {len(videos)} videos:")
        for v in videos:
            print(f"   - {v}")
            
    finally:
        generator.close()
