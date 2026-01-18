from flowchart.common.llm_manager import LLMManager
import json

class ScriptGenerator:
    def __init__(self):
        self.llm = LLMManager()

    def generate_overview(self, video_idea):
        """
        Generates a high-level script overview using LLM Manager.
        Returns enhanced format with character_description dictionary.
        """
        print(f"[AI] Generative AI: Creating overview for '{video_idea}'...")
        
        prompt = f"""
        You are a professional video producer. Create a detailed video plan for the idea: "{video_idea}".
        Return ONLY a JSON object with this structure:
        {{
            "title": "Catchy Title",
            "synopsis": "Short summary",
            "characters": ["Character1 Name", "Character2 Name"],
            "character_description": {{
                "Character1 Name": "Detailed visual description for AI image generation - appearance, clothing, features",
                "Character2 Name": "Detailed visual description for AI image generation - appearance, clothing, features"
            }},
            "Full_script": "Complete narration/voiceover text for the entire video"
        }}
        """
        
        result = self.llm.generate(prompt, json_mode=True)
        
        # Validation
        if result and isinstance(result, dict) and 'title' in result:
            # Ensure all required fields exist
            if 'characters' not in result:
                result['characters'] = []
            if 'character_description' not in result:
                result['character_description'] = {}
            if 'Full_script' not in result:
                result['Full_script'] = result.get('synopsis', '')
            return result
        
        print("[WARNING] LLM returned invalid overview, using fallback.")
        return {
            "title": video_idea,
            "synopsis": "Automated video generation",
            "characters": ["Narrator"],
            "character_description": {
                "Narrator": "Professional narrator, neutral appearance"
            },
            "Full_script": "Automated video content"
        }

    def generate_scenes(self, overview, num_scenes=6):
        """
        Generates detailed scene breakdowns using LLM Manager.
        Returns enhanced format with character_name, character_description, background, and video_script.
        """
        print(f"[AI] Generative AI: Writing {num_scenes} scenes...")
        
        prompt = f"""
        Create a {num_scenes}-scene script for a video titled "{overview['title']}".
        Characters: {overview.get('characters', [])}
        Character Descriptions: {overview.get('character_description', {})}
        Synopsis: {overview['synopsis']}
        
        Rules:
        1. Each scene must be EXACTLY 8 seconds (optimized for Veo 3.1 video generation).
        2. Provide detailed, specific visual descriptions for AI video generation.
        3. Include character name, character description, background, dialogue, and video script.
        4. Keep actions simple and focused - 8 seconds is short!
        5. Dialogue can be detailed - max 100 words for rich character speech.
        6. Return ONLY a JSON list of objects.
        
        Format:
        [
            {{
                "scene_number": 1,
                "character_name": "Name of character in this scene (or 'None')",
                "character_description": "How the character appears/acts in THIS specific scene (detailed for consistency)",
                "background": "Detailed visual description of background/setting for video generation",
                "dialogue": "Character's spoken words (max 100 words for detailed speech)",
                "video_script": "Visual: [specific action/shot]. Tone: [mood]. Music: [style]. Duration: 8 seconds"
            }}
        ]
        
        IMPORTANT: 8 seconds = 1 simple action or moment. Focus on ONE clear visual per scene.
        """
        
        result = self.llm.generate(prompt, json_mode=True)
        
        # Validation and ensure all fields exist
        if result and isinstance(result, list):
            for scene in result:
                if 'character_name' not in scene:
                    scene['character_name'] = scene.get('character', 'None')
                if 'character_description' not in scene:
                    scene['character_description'] = ''
                if 'background' not in scene:
                    scene['background'] = scene.get('visual_prompt', '')
                if 'dialogue' not in scene:
                    # Try to extract from video_script or use empty
                    scene['dialogue'] = ''
                if 'video_script' not in scene:
                    # Build from existing fields if available
                    visual = scene.get('visual_prompt', '')
                    dialogue = scene.get('dialogue', '')
                    scene['video_script'] = f"Visual: {visual}. Dialogue: {dialogue}. Tone: Engaging. Music: Ambient. Duration: 8 seconds"
            return result
        
        return []

if __name__ == "__main__":
    sg = ScriptGenerator()
    overview = sg.generate_overview("The Lost City of Atlantis")
    scenes = sg.generate_scenes(overview)
    print(scenes[0])
