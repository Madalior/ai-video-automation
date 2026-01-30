#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              INFO SCRIPT GENERATOR                                ║
║                                                                   ║
║  Generates fact-based scripts for Info/Documentary niches        ║
║  NO character_description - focuses on data, facts, visuals      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Import LLM Manager
try:
    from .llm_manager import LLMManager
    from .emotional_script_generator import EmotionalScriptGenerator
except ImportError:
    from modules.llm_manager import LLMManager
    try:
        from flowchart.common.emotional_script_generator import EmotionalScriptGenerator
    except ImportError:
        EmotionalScriptGenerator = None


class InfoScriptGenerator:
    """
    Script generator optimized for INFO/DOCUMENTARY niches.
    
    Key differences from character-based ScriptGenerator:
    - No character_description field
    - Focus on key_facts and data_points
    - Visual suggestions are stock keywords, not character scenes
    - Narration-first approach
    """
    
    # Suitable niches for this generator
    SUITABLE_NICHES = [
        "Technology", "Science", "Facts", "Educational",
        "Documentary", "History", "Business", "Finance",
        "Health", "Psychology", "Space", "AI News"
    ]
    
    def __init__(self, llm_provider: str = None, use_emotional_ai: bool = True):
        self.llm = LLMManager(provider=llm_provider) if llm_provider else LLMManager()
        self.emotional_gen = EmotionalScriptGenerator(use_genkit=use_emotional_ai) if (use_emotional_ai and EmotionalScriptGenerator) else None
    
    def generate_overview(self, topic: str) -> Dict:
        """
        Generate video overview with hook, facts, and conclusion.
        
        Args:
            topic: The main topic (e.g., "AI Technology")
        
        Returns:
            Dict with title, hook, key_facts, conclusion
        """
        print(f"[INFO] Generating overview for: {topic}")
        
        prompt = f"""
        Create a viral video overview for topic: {topic}
        
        Generate engaging, fact-based content optimized for YouTube/TikTok.
        
        Return as JSON:
        {{
            "title": "Catchy video title with numbers (e.g., '10 Mind-Blowing...')",
            "hook": "Attention-grabbing opening (first 3 seconds) - question or surprising statement",
            "key_facts": [
                {{
                    "fact": "Interesting fact or data point",
                    "source": "Where this fact comes from (optional)",
                    "visual_keywords": ["keyword1", "keyword2", "keyword3"]
                }}
            ],
            "conclusion": "Memorable closing with call to action",
            "target_audience": "Who this video is for",
            "estimated_engagement": "high/medium/low"
        }}
        
        Generate 5-8 key facts. Make them surprising and shareable.
        """
        
        result = self.llm.generate(prompt, json_mode=True)
        
        if not result or not isinstance(result, dict):
            # Fallback
            result = {
                "title": f"Amazing {topic} Facts You Didn't Know",
                "hook": f"Did you know this about {topic}?",
                "key_facts": [
                    {"fact": f"Fact about {topic}", "visual_keywords": [topic]}
                ],
                "conclusion": "Like and subscribe for more!",
                "target_audience": "General audience",
                "estimated_engagement": "medium"
            }
        
        print(f"   [OK] Title: {result.get('title', 'N/A')}")
        print(f"   [OK] Facts: {len(result.get('key_facts', []))}")
        
        return result
    
    def generate_scenes(self, overview: Dict, num_scenes: int = 10, 
                        duration: int = 60) -> List[Dict]:
        """
        Generate scene-by-scene script from overview.
        
        Args:
            overview: Dict from generate_overview()
            num_scenes: Number of scenes to generate
            duration: Target video duration in seconds
        
        Returns:
            List of scene dictionaries
        """
        print(f"[INFO] Generating {num_scenes} scenes...")
        
        key_facts = overview.get('key_facts', [])
        hook = overview.get('hook', '')
        conclusion = overview.get('conclusion', '')
        
        # Calculate timing
        scene_duration = max(4, duration // num_scenes)
        
        scenes = []
        
        # Scene 1: Hook/Intro
        scenes.append({
            'scene_number': 1,
            'scene_type': 'intro',
            'narration': hook,
            'visual_type': 'stock',
            'stock_keywords': overview.get('key_facts', [{}])[0].get('visual_keywords', ['technology']),
            'text_overlay': None,
            'duration': scene_duration,
            'transition': 'fade_in'
        })
        
        # Fact scenes
        for i, fact_data in enumerate(key_facts[:num_scenes-2], start=2):
            fact = fact_data.get('fact', '') if isinstance(fact_data, dict) else str(fact_data)
            keywords = fact_data.get('visual_keywords', ['technology']) if isinstance(fact_data, dict) else ['technology']
            
            scenes.append({
                'scene_number': i,
                'scene_type': 'fact',
                'narration': fact,
                'visual_type': 'stock',  # or 'graphic' for AI-generated infographic
                'stock_keywords': keywords,
                'text_overlay': self._extract_key_stat(fact),
                'duration': scene_duration,
                'transition': 'cut'
            })
        
        # Final scene: Conclusion
        scenes.append({
            'scene_number': len(scenes) + 1,
            'scene_type': 'outro',
            'narration': conclusion,
            'visual_type': 'stock',
            'stock_keywords': ['subscribe', 'like', 'social media'],
            'text_overlay': "SUBSCRIBE",
            'duration': scene_duration,
            'transition': 'fade_out'
        })
        
        # Enhance narration with emotional AI
        if self.emotional_gen:
            scenes = self._enhance_narration_with_emotion(scenes)
        
        print(f"   [OK] Generated {len(scenes)} scenes")
        return scenes
    
    def _enhance_narration_with_emotion(self, scenes: List[Dict]) -> List[Dict]:
        """
        Enhance scene narrations with emotional storytelling.
        """
        try:
            # Combine all narration for emotional enhancement
            full_narration = "\n".join([scene.get('narration', '') for scene in scenes])
            
            if not full_narration.strip():
                return scenes
            
            # Enhance with emotional AI
            enhanced = self.emotional_gen.enhance_script(
                script=full_narration,
                video_type="info",
                emotion_style="educational",  # Good default for info content
                num_scenes=len(scenes)
            )
            
            # Apply emotional enhancements to scenes
            if enhanced and 'enhanced_script' in enhanced:
                enhanced_scenes = enhanced['enhanced_script'].get('scenes', [])
                for i, scene in enumerate(scenes):
                    if i < len(enhanced_scenes):
                        emotional_scene = enhanced_scenes[i]
                        # Update narration with emotionally enhanced version
                        if emotional_scene.get('narration'):
                            scene['narration'] = emotional_scene['narration']
                        # Add emotional metadata
                        scene['emotion'] = emotional_scene.get('emotion', 'curiosity')
                        scene['pacing'] = emotional_scene.get('pacing', 'moderate')
                        scene['delivery_hint'] = emotional_scene.get('delivery_hint', '')
            
            return scenes
        except Exception as e:
            print(f"[WARNING] Emotional enhancement failed: {str(e)[:100]}")
            return scenes
    
    def _extract_key_stat(self, fact: str) -> Optional[str]:
        """Extract number/statistic from fact for text overlay"""
        import re
        # Find numbers with units
        matches = re.findall(r'\d+[\d,\.]*\s*(?:%|billion|million|trillion|years|days)?', fact, re.IGNORECASE)
        if matches:
            return matches[0].strip()
        return None
    
    def generate_full_script(self, topic: str, num_scenes: int = 10, 
                             duration: int = 60) -> Dict:
        """
        Generate complete script for info video.
        
        Args:
            topic: Main topic
            num_scenes: Number of scenes
            duration: Video duration in seconds
        
        Returns:
            Complete script dictionary
        """
        print(f"\n{'='*60}")
        print(f"   INFO SCRIPT GENERATOR")
        print(f"   Topic: {topic}")
        print(f"{'='*60}\n")
        
        # Generate overview
        overview = self.generate_overview(topic)
        
        # Generate scenes
        scenes = self.generate_scenes(overview, num_scenes, duration)
        
        # Build full script
        script = {
            'title': overview.get('title', topic),
            'topic': topic,
            'niche': 'info',
            'hook': overview.get('hook', ''),
            'conclusion': overview.get('conclusion', ''),
            'key_facts': overview.get('key_facts', []),
            'scenes': scenes,
            'total_scenes': len(scenes),
            'total_duration': duration,
            'target_audience': overview.get('target_audience', 'General'),
            # NO character_description - this is info content
        }
        
        print(f"\n   [OK] Script complete: '{script['title']}'")
        print(f"   [OK] Scenes: {len(scenes)}")
        print(f"   [OK] Duration: {duration}s")
        
        return script


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Info Script Generator")
    parser.add_argument('--topic', type=str, default="Artificial Intelligence",
                       help='Topic to generate script for')
    parser.add_argument('--scenes', type=int, default=8,
                       help='Number of scenes')
    parser.add_argument('--duration', type=int, default=60,
                       help='Video duration in seconds')
    parser.add_argument('--output', type=str, default=None,
                       help='Output JSON file path')
    
    args = parser.parse_args()
    
    generator = InfoScriptGenerator()
    script = generator.generate_full_script(
        topic=args.topic,
        num_scenes=args.scenes,
        duration=args.duration
    )
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Script saved to: {args.output}")
    else:
        print("\n" + json.dumps(script, indent=2, ensure_ascii=False))
