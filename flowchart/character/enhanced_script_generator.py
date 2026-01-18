"""
Enhanced Script Generator with Identity Card System

Integrates Veo 3.1 consistency techniques:
- Generates character identity cards with anchor attributes
- Separates fixed traits from scene-specific deltas
- Maintains character consistency across scenes
"""

from flowchart.common.llm_manager import LLMManager
from flowchart.common.identity_cards import CharacterIdentityCard, IdentityCardManager
import json


class EnhancedScriptGenerator:
    """
    Script generator with built-in identity card system.
    Creates persistent character anchors for consistency.
    """
    
    def __init__(self):
        self.llm = LLMManager()
        self.card_manager = IdentityCardManager()
    
    def generate_overview_with_identity_cards(self, video_idea):
        """
        Generate overview WITH identity cards for character consistency.
        
        Returns:
            dict with 'overview' and 'identity_cards'
        """
        print(f"[AI] Creating overview with identity cards for '{video_idea}'...")
        
        prompt = f"""
        Create a detailed video plan for: "{video_idea}".
        
        For EACH character, create an IDENTITY CARD with unchangeable attributes (anchors).
        
        Return ONLY a JSON object:
        {{
            "title": "Catchy video title",
            "synopsis": "Brief summary",
            "Full_script": "Complete narration",
            "characters": {{
                "Character Name": {{
                    "anchor_attributes": {{
                        "facial_features": "Detailed: eyes, nose, mouth, face shape, skin tone",
                        "body_type": "Height, build, posture details",
                        "distinctive_marks": "Scars, tattoos, unique features",
                        "hair": "Color, style, length, texture",
                        "clothing_style": "Core wardrobe identity (not specific outfit)",
                        "age_appearance": "Apparent age",
                        "ethnicity": "Ethnic/racial appearance",
                        "gender_presentation": "Gender appearance"
                    }},
                    "voice_profile": {{
                        "tone": "Warm/cold/authoritative/friendly",
                        "pace": "Fast/slow/measured",
                        "accent": "Regional/standard",
                        "pitch": "High/low/medium",
                        "style": "Formal/casual/professional"
                    }}
                }}
            }}
        }}
        
        CRITICAL: Make anchor_attributes HIGHLY SPECIFIC. These define the character forever.
        """
        
        result = self.llm.generate(prompt, json_mode=True)
        
        if result and isinstance(result, dict):
            # Extract identity cards
            characters_data = result.get('characters', {})
            
            for char_name, char_data in characters_data.items():
                anchors = char_data.get('anchor_attributes', {})
                voice = char_data.get('voice_profile', {})
                
                card = CharacterIdentityCard(
                    name=char_name,
                    anchors=anchors,
                    voice_profile=voice
                )
                self.card_manager.add_card(card)
                print(f"   ✓ Identity card created for: {char_name}")
            
            # Format for compatibility
            overview = {
                'title': result.get('title', video_idea),
                'synopsis': result.get('synopsis', ''),
                'characters': list(characters_data.keys()),
                'character_description': {
                    name: data.get('anchor_attributes', {}) 
                    for name, data in characters_data.items()
                },
                'Full_script': result.get('Full_script', '')
            }
            
            return {
                'overview': overview,
                'identity_cards': self.card_manager.to_dict()
            }
        
        # Fallback
        print("[WARNING] Using fallback overview")
        return {
            'overview': {
                'title': video_idea,
                'synopsis': 'Automated generation',
                'characters': ['Narrator'],
                'character_description': {'Narrator': 'Professional narrator'},
                'Full_script': 'Auto-generated content'
            },
            'identity_cards': {}
        }
    
    def generate_scenes_with_deltas(self, overview_data, num_scenes=6):
        """
        Generate scenes with anchor/delta separation.
        
        Args:
            overview_data: Result from generate_overview_with_identity_cards()
            num_scenes: Number of scenes to generate
        
        Returns:
            List of scene dicts with delta attributes
        """
        overview = overview_data['overview']
        print(f"[AI] Generating {num_scenes} scenes with delta attributes...")
        
        prompt = f"""
        Create {num_scenes} scenes for "{overview['title']}".
        Characters: {overview.get('characters', [])}
        Synopsis: {overview['synopsis']}
        
        For EACH scene, provide DELTA (changeable) attributes:
        
        Rules:
        1. Each scene = EXACTLY 8 seconds
        2. Deltas are SCENE-SPECIFIC changes (pose, emotion, action, outfit)
        3. Anchors (character features) NEVER change - already defined
        4. Dialogue max 100 words
        5. Return ONLY a JSON list
        
        Format:
        [
            {{
                "scene_number": 1,
                "character_name": "Name from character list",
                "delta_attributes": {{
                    "pose": "Body position/stance",
                    "emotion": "Facial expression/mood",
                    "action": "What they're doing",
                    "clothing_details": "Specific outfit",
                    "lighting": "Scene lighting",
                    "camera_angle": "Shot type",
                    "background": "Setting description"
                }},
                "dialogue": "Spoken words (max 100)",
                "video_script": "Visual: [action]. Tone: [mood]. Duration: 8s"
            }}
        ]
        """
        
        result = self.llm.generate(prompt, json_mode=True)
        
        if result and isinstance(result, list):
            # Validate and enhance with identity card prompts
            enhanced_scenes = []
            
            for scene in result:
                char_name = scene.get('character_name', 'None')
                
                # Get identity card if exists
                card = self.card_manager.get_card(char_name)
                
                if card:
                    # Build anchor+delta prompt
                    deltas = scene.get('delta_attributes', {})
                    full_prompt = card.get_scene_prompt(deltas)
                    scene['consistency_prompt'] = full_prompt
                    scene['anchor_prompt'] = card.get_anchor_prompt()
                    scene['voice_prompt'] = card.get_voice_prompt()
                else:
                    scene['consistency_prompt'] = scene.get('character_description', '')
                    scene['anchor_prompt'] = ''
                    scene['voice_prompt'] = ''
                
                # Ensure all fields exist
                if 'dialogue' not in scene:
                    scene['dialogue'] = ''
                if 'video_script' not in scene:
                    scene['video_script'] = 'Auto-generated scene'
                if 'background' not in scene.get('delta_attributes', {}):
                    scene.setdefault('delta_attributes', {})['background'] = 'generic setting'
                
                enhanced_scenes.append(scene)
            
            return enhanced_scenes
        
        return []
    
    def get_character_card(self, name):
        """Get identity card for character."""
        return self.card_manager.get_card(name)
    
    def get_all_cards(self):
        """Get all identity cards."""
        return self.card_manager.get_all_cards()


# Test/Demo
if __name__ == "__main__":
    gen = EnhancedScriptGenerator()
    
    print("="*80)
    print("ENHANCED SCRIPT GENERATOR WITH IDENTITY CARDS")
    print("="*80)
    
    # Generate with identity cards
    result = gen.generate_overview_with_identity_cards("A detective solves a mystery")
    
    print("\n[OVERVIEW]")
    print(f"Title: {result['overview']['title']}")
    print(f"Characters: {result['overview']['characters']}")
    
    print("\n[IDENTITY CARDS]")
    for name, card_data in result['identity_cards'].items():
        print(f"\n{name}:")
        print(f"  Anchors: {list(card_data['anchors'].keys())}")
        print(f"  Voice: {card_data['voice_profile']}")
    
    # Generate scenes with deltas
    scenes = gen.generate_scenes_with_deltas(result, num_scenes=3)
    
    print(f"\n[SCENES] Generated {len(scenes)} scenes")
    if scenes:
        scene1 = scenes[0]
        print(f"\nScene 1 Example:")
        print(f"  Character: {scene1.get('character_name')}")
        print(f"  Deltas: {list(scene1.get('delta_attributes', {}).keys())}")
        print(f"  Consistency Prompt: {scene1.get('consistency_prompt', '')[:100]}...")
