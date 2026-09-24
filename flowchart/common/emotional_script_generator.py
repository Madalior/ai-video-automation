"""
Emotional Script Generator

Enhances video scripts with emotional depth, human-like storytelling,
and natural conversational patterns. Integrates with Genkit AI service
for advanced emotional intelligence.
"""

import json
import re
import random
from typing import Dict, List, Optional
from modules.genkit_client import genkit

try:
    from flowchart.common.llm_manager import LLMManager
    _LLM_OK = True
except ImportError:
    _LLM_OK = False

class EmotionalScriptGenerator:
    """
    Creates emotionally engaging, human-like scripts for videos.
    
    Features:
    - 7 emotion categories (joy, sadness, excitement, curiosity, empathy, inspiration, nostalgia)
    - Human storytelling patterns and hooks
    - Conversational elements and delivery markers
    - Scene-by-scene emotion mapping
    - Pacing and vocal delivery suggestions
    """
    
    EMOTION_CATEGORIES = {
        "joy": {
            "description": "Uplifting, cheerful, light-hearted energy",
            "techniques": ["Playful language", "Positive imagery", "Bright tone"],
            "vocal_hints": "Bright tone, faster pace, energetic delivery"
        },
        "sadness": {
            "description": "Reflective, melancholic, poignant moments",
            "techniques": ["Gentle language", "Thoughtful pauses", "Emotional weight"],
            "vocal_hints": "Softer tone, slower pace, meaningful pauses"
        },
        "excitement": {
            "description": "High energy, enthusiasm, anticipation",
            "techniques": ["Dynamic language", "Builds momentum", "Sensory details"],
            "vocal_hints": "Varied pitch, crescendos, rapid fire delivery"
        },
        "curiosity": {
            "description": "Engaging questions, mystery, discovery",
            "techniques": ["Rhetorical questions", "What if scenarios", "Reveals"],
            "vocal_hints": "Inquisitive tone, strategic pauses, emphasis on questions"
        },
        "empathy": {
            "description": "Understanding, relatable, compassionate",
            "techniques": ["You language", "Shared experiences", "Vulnerability"],
            "vocal_hints": "Warm tone, conversational pace, genuine connection"
        },
        "inspiration": {
            "description": "Motivating, uplifting, transformative",
            "techniques": ["Power words", "Contrast", "Calls to action"],
            "vocal_hints": "Confident tone, deliberate pacing, emphasis on key phrases"
        },
        "nostalgia": {
            "description": "Wistful, reflective, memory-driven",
            "techniques": ["Past tense narratives", "Sensory memories", "Remember when"],
            "vocal_hints": "Gentle tone, reflective pauses, storytelling rhythm"
        }
    }
    
    def __init__(self, use_genkit: bool = True):
        """
        Initialize emotional script generator.
        
        Args:
            use_genkit: Whether to use Genkit AI service for enhancement
        """
        self.use_genkit = use_genkit
        self.genkit_client = genkit if use_genkit else None
        self._llm = LLMManager() if _LLM_OK else None
    
    def enhance_script(
        self,
        script: str,
        video_type: str = "info",
        emotion_style: str = "auto",
        num_scenes: int = 7
    ) -> Dict:
        """
        Enhance script with emotional depth and human-like storytelling.
        
        Args:
            script: Original script text (can be full script or scene narrations)
            video_type: "character" or "info"
            emotion_style: Target emotion or "auto" for automatic detection
            num_scenes: Number of scenes in the video
            
        Returns:
            Dict with enhanced_script, emotion_map, delivery_notes, pacing_hints
        """
        if self.use_genkit and self.genkit_client:
            try:
                print(f"[AI] 🎭 Enhancing script with {emotion_style} emotions...")
                result = self.genkit_client.enhance_script_emotions(
                    script=script,
                    video_type=video_type,
                    emotion_style=emotion_style,
                    num_scenes=num_scenes
                )
                
                if result:
                    print(f"[SUCCESS] ✓ Script enhanced with emotional storytelling!")
                    # Inject hook into Genkit result
                    result['hook'] = self.generate_hook(script, emotion_style)
                    return result
                else:
                    print("[WARNING] Genkit enhancement failed, using fallback...")
                    return self._fallback_enhancement(script, emotion_style, num_scenes)
                    
            except Exception as e:
                print(f"[WARNING] Genkit error: {str(e)[:100]}. Using fallback...")
                return self._fallback_enhancement(script, emotion_style, num_scenes)
        else:
            return self._fallback_enhancement(script, emotion_style, num_scenes)
    
    def _fallback_enhancement(
        self,
        script: str,
        emotion_style: str,
        num_scenes: int
    ) -> Dict:
        """
        Fallback enhancement when Genkit is unavailable.
        Adds basic emotional markers and suggestions.
        """
        # Detect emotion if auto
        if emotion_style == "auto":
            emotion_style = self._detect_emotion(script)
        
        # Get emotion info
        emotion_info = self.EMOTION_CATEGORIES.get(emotion_style, self.EMOTION_CATEGORIES["empathy"])
        
        # Add basic markers
        enhanced_script = self._add_delivery_markers(script, emotion_style)
        
        # Create basic scene breakdown
        scenes = []
        script_lines = script.split('\n')
        lines_per_scene = max(1, len(script_lines) // num_scenes)
        
        for i in range(num_scenes):
            start_idx = i * lines_per_scene
            end_idx = min((i + 1) * lines_per_scene, len(script_lines))
            scene_text = '\n'.join(script_lines[start_idx:end_idx])
            
            scenes.append({
                "scene_number": i + 1,
                "narration": scene_text,
                "emotion": emotion_style,
                "pacing": "moderate",
                "delivery_hint": emotion_info["vocal_hints"]
            })
        
        hook = self.generate_hook(script, emotion_style)

        return {
            "enhanced_script": {
                "full_text": enhanced_script,
                "scenes": scenes
            },
            "emotion_map": {
                "overall_arc": f"Consistent {emotion_style} tone throughout",
                "scene_emotions": [emotion_style] * num_scenes,
                "peak_moment": f"Scene {num_scenes // 2}",
                "resolution_tone": emotion_style
            },
            "delivery_notes": [
                f"Maintain {emotion_style} tone throughout",
                emotion_info["vocal_hints"],
                "Use natural pauses for emphasis",
                "Vary pace to maintain engagement"
            ],
            "pacing_hints": {
                "intro": "moderate - establish connection",
                "body": "varied - mix energy levels",
                "conclusion": "deliberate - memorable ending",
                "overall_rhythm": f"{emotion_style.capitalize()} with clear structure"
            },
            "storytelling_arc": f"Opens with hook, builds through {emotion_style} narrative, resolves with impact",
            "hook": hook,
        }
    
    def _detect_emotion(self, script: str) -> str:
        """
        Simple emotion detection based on keywords.
        """
        script_lower = script.lower()
        
        # Keyword-based detection
        if any(word in script_lower for word in ["amazing", "incredible", "wonderful", "fantastic", "awesome"]):
            return "excitement"
        elif any(word in script_lower for word in ["remember", "used to", "back then", "once upon"]):
            return "nostalgia"
        elif any(word in script_lower for word in ["why", "how", "what if", "discover", "explore"]):
            return "curiosity"
        elif any(word in script_lower for word in ["you can", "achieve", "transform", "become", "unlock"]):
            return "inspiration"
        elif any(word in script_lower for word in ["happy", "joy", "smile", "laugh", "fun"]):
            return "joy"
        elif any(word in script_lower for word in ["you know", "we all", "understand", "feel", "relate"]):
            return "empathy"
        else:
            return "empathy"  # Default to empathy for educational content
    
    def _add_delivery_markers(self, script: str, emotion: str) -> str:
        """
        Add basic delivery markers to script.
        """
        # Add strategic pauses
        enhanced = script.replace(". ", ". [PAUSE] ")
        enhanced = enhanced.replace("? ", "? [PAUSE] ")
        enhanced = enhanced.replace("! ", "! [PAUSE] ")
        
        # Add emphasis on key phrases based on emotion
        if emotion == "excitement":
            enhanced = enhanced.replace("incredible", "[EMPHASIS]incredible[/EMPHASIS]")
            enhanced = enhanced.replace("amazing", "[EMPHASIS]amazing[/EMPHASIS]")
        elif emotion == "inspiration":
            enhanced = enhanced.replace("you can", "[EMPHASIS]you can[/EMPHASIS]")
            enhanced = enhanced.replace("transform", "[EMPHASIS]transform[/EMPHASIS]")
        
        return enhanced
    
    # ─────────────────────────────────────────────────────────────────────────
    # HOOK GENERATION
    # ─────────────────────────────────────────────────────────────────────────

    def generate_hook(
        self,
        script: str,
        emotion_style: str = "auto",
        title: str = "",
    ) -> Dict:
        """
        Generate a hook block for the script.

        Returns a dict:
        {
            "hook_text"  : str  — Short, bold on-screen text (2-7 words)
                                   burned as overlay on the hook video
            "hook_visual": str  — Cinematic AI video generation prompt
                                   for HookVideoGenerator
            "hook_narration": str — Spoken opening line (voiceover for scene 0)
            "hook_style" : str  — visual style hint (dramatic/curiosity/shock)
        }

        Tries LLM first; falls back to rule-based generation.
        """
        if emotion_style == "auto":
            emotion_style = self._detect_emotion(script)

        # ── LLM-generated hook (best quality) ─────────────────────────────────
        if self._llm:
            try:
                hook = self._llm_generate_hook(script, emotion_style, title)
                if hook:
                    print(f"[HOOK] Generated via LLM: {hook['hook_text'][:60]}")
                    return hook
            except Exception as e:
                print(f"[HOOK] LLM failed ({e}), using fallback")

        # ── Rule-based fallback ────────────────────────────────────────────────
        return self._fallback_hook(script, emotion_style)

    def _llm_generate_hook(
        self,
        script: str,
        emotion_style: str,
        title: str = "",
    ) -> Dict:
        """Ask LLM to generate a hook block."""
        prompt = f"""You are a viral short-form content expert.

Given this video script excerpt and emotion style, generate a HOOK block.
The hook plays in the FIRST 3-5 SECONDS of the video to stop viewers from scrolling.

Script (first 400 chars):
{script[:400]}

Title: {title or 'Not specified'}
Emotion Style: {emotion_style}

Return JSON ONLY:
{{
    "hook_text": "2-7 words of bold on-screen text (e.g. 'Nobody knows this secret' or 'Wait — you need to see this')",
    "hook_visual": "Cinematic AI video generation prompt for the hook clip. 15-25 words, vivid, specific visual. E.g. 'A scientist discovers glowing alien artifact, dramatic close-up, cinematic lighting'",
    "hook_narration": "Spoken opening line for voiceover (1-2 sentences). Must hook immediately.",
    "hook_style": "One of: dramatic / curiosity / shock / mystery / inspiration"
}}
Return ONLY valid JSON."""

        try:
            result = self._llm.generate(prompt, json_mode=True)
            if isinstance(result, dict) and all(
                k in result for k in ("hook_text", "hook_visual", "hook_narration")
            ):
                return result
            if isinstance(result, str):
                m = re.search(r'\{.*\}', result, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
        except Exception:
            pass
        return None

    def _fallback_hook(
        self,
        script: str,
        emotion_style: str,
    ) -> Dict:
        """Rule-based hook generation — no LLM required."""
        HOOK_TEMPLATES = {
            "excitement": [
                ("This changes EVERYTHING!", "Crowd erupting in cheers, time-lapse explosion of light, cinematic"),
                ("You won't believe this!", "Person with jaw-dropping expression, neon-lit room, dramatic reveal"),
            ],
            "curiosity": [
                ("Nobody talks about this...", "Mysterious dark hallway with a single glowing door, cinematic"),
                ("The secret they hid from you", "Ancient library revealing hidden compartment, moody lighting"),
            ],
            "inspiration": [
                ("One decision changed everything", "Lone figure on mountaintop at sunrise, epic wide shot"),
                ("This will change your life!", "Person opening door to bright golden light, cinematic"),
            ],
            "sadness": [
                ("They never told you this...", "Rain-soaked empty street, single light flickering, moody"),
                ("The truth is heartbreaking", "Close-up of a tear running down a face, soft lighting"),
            ],
            "nostalgia": [
                ("Remember when this existed?", "Old photograph coming to life, warm vintage colors"),
                ("What we lost and forgot", "Dusty childhood toy in attic rays of light, cinematic"),
            ],
            "joy": [
                ("This will make your day!", "Puppy and child running through sunlit meadow, golden hour"),
                ("Prepare to smile!", "Group of friends laughing, confetti exploding, vibrant colors"),
            ],
            "empathy": [
                ("You are not alone in this", "Person sitting alone then light surrounds them, warm tones"),
                ("Everyone feels this way", "Time-lapse of people all looking at same sunset, cinematic"),
            ],
        }

        templates = HOOK_TEMPLATES.get(emotion_style, HOOK_TEMPLATES["curiosity"])
        hook_text, hook_visual = random.choice(templates)

        # Extract a punchy opening line from the script
        first_line = ""
        for ln in script.strip().splitlines():
            ln = ln.strip()
            if len(ln) > 20:
                first_line = ln[:120]
                break

        return {
            "hook_text":     hook_text,
            "hook_visual":   hook_visual,
            "hook_narration": first_line or hook_text,
            "hook_style":    emotion_style,
        }

    def get_emotion_info(self, emotion: str) -> Dict:
        """
        Get detailed information about an emotion category.
        """
        return self.EMOTION_CATEGORIES.get(emotion, {
            "description": "Unknown emotion",
            "techniques": [],
            "vocal_hints": "Natural delivery"
        })
    
    def list_emotions(self) -> List[str]:
        """
        Get list of available emotion categories.
        """
        return list(self.EMOTION_CATEGORIES.keys())


# Test/Demo
if __name__ == "__main__":
    gen = EmotionalScriptGenerator(use_genkit=True)
    
    # Test script
    test_script = """
    Artificial Intelligence is transforming our world.
    From healthcare to education, AI is making a difference.
    But what does this really mean for you?
    Today, we'll explore the incredible possibilities.
    """
    
    print("=" * 80)
    print("EMOTIONAL SCRIPT GENERATOR TEST")
    print("=" * 80)
    
    # Enhance with auto emotion detection
    result = gen.enhance_script(
        script=test_script,
        video_type="info",
        emotion_style="auto",
        num_scenes=4
    )
    
    print(f"\n✓ Enhanced Script:")
    print(f"  Storytelling Arc: {result['storytelling_arc']}")
    print(f"  Emotions: {', '.join(result['emotion_map']['scene_emotions'])}")
    print(f"  Scenes: {len(result['enhanced_script']['scenes'])}")
    print(f"\n  Sample Scene:")
    scene1 = result['enhanced_script']['scenes'][0]
    print(f"    Scene {scene1['scene_number']}: {scene1['emotion']}")
    print(f"    Pacing: {scene1['pacing']}")
    print(f"    Delivery: {scene1['delivery_hint'][:60]}...")
