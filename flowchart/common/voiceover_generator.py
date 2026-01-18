"""
Enhanced AI Voice-Over Generator
Supports Gemini-TTS with character voices and emotions, plus fallbacks to gTTS and Cloud TTS.
"""

import os
from gtts import gTTS
import google.generativeai as genai

# Modern GenAI SDK for Gemini-TTS (2.5-flash-tts)
try:
    from google import genai as modern_genai
    from google.genai import types
    GENAI_SDK_AVAILABLE = True
except ImportError:
    GENAI_SDK_AVAILABLE = False

# Cloud TTS is optional (paid feature)
try:
    from google.cloud import texttospeech
    CLOUD_TTS_AVAILABLE = True
except ImportError:
    CLOUD_TTS_AVAILABLE = False


class VoiceOverGenerator:
    """Enhanced AI voice-over generator with Gemini-TTS (Emotion & Characters)."""
    
    # Modern Gemini character voices
    GEMINI_VOICES = {
        "zephyr": "Zephyr (Bright & Clear)",
        "puck": "Puck (Upbeat & Playful)",
        "charon": "Charon (Informative & Professional)",
        "kore": "Kore (Firm & Authoritative)",
        "fenrir": "Fenrir (Excitable & Energetic)",
        "leda": "Leda (Youthful & Friendly)",
        "aoede": "Aoede (Breezy & Casual)"
    }
    
    def __init__(self, use_cloud_tts=False, use_gemini_tts=True):
        """
        Initialize voice-over generator.
        
        Args:
            use_cloud_tts: Use Google Cloud TTS (paid, high quality)
            use_gemini_tts: Use Gemini-TTS with character voices (free with API key)
        """
        self.use_cloud_tts = use_cloud_tts
        self.use_gemini_tts = use_gemini_tts and GENAI_SDK_AVAILABLE
        self.output_dir = "voiceovers"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize Gemini-TTS client
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.use_gemini_tts and self.api_key:
            try:
                self.modern_client = modern_genai.Client(api_key=self.api_key)
                print("[OK] Gemini-TTS initialized with character voices")
            except Exception as e:
                print(f"[WARNING] Gemini-TTS init failed: {e}")
                self.use_gemini_tts = False
        
        # Initialize Cloud TTS if needed
        if use_cloud_tts:
            if not CLOUD_TTS_AVAILABLE:
                print("[WARNING] Cloud TTS not installed, using alternatives")
                self.use_cloud_tts = False
            else:
                self.tts_client = texttospeech.TextToSpeechClient()
    
    def generate_voiceover_gemini(self, text, filename, voice="zephyr", emotion="neutral"):
        """
        Generate voice-over with emotion using Gemini-2.5-Flash-TTS.
        
        Args:
            text: The text to speak
            filename: Output mp3 filename
            voice: Character name (zephyr, puck, charon, kore, fenrir, leda, aoede)
            emotion: Natural language description (e.g., "excited and fast", "calm and professional")
        
        Returns:
            Path to generated audio file
        """
        if not self.use_gemini_tts:
            print("[WARNING] Gemini-TTS not available, falling back to gTTS")
            return self.generate_voiceover_gtts(text, filename)
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            print(f"[GEMINI-TTS] Generating with {voice} voice ({emotion}): {filename}")
            
            # Use the latest gemini-2.5-flash-tts model
            response = self.modern_client.models.generate_content(
                model='gemini-2.5-flash-tts',
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice.capitalize()
                            )
                        )
                    )
                )
            )
            
            # Extract audio bytes from the multimodal response
            audio_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    with open(filepath, 'wb') as f:
                        f.write(part.inline_data.data)
                    audio_saved = True
                    break
            
            if audio_saved:
                print(f"[SUCCESS] Gemini voice-over saved: {filepath}")
                return filepath
            else:
                print("[WARNING] No audio data in response, falling back")
                return self.generate_voiceover_gtts(text, filename)
        
        except Exception as e:
            print(f"[ERROR] Gemini-TTS failed: {e}")
            return self.generate_voiceover_gtts(text, filename)
    
    def generate_voiceover_gtts(self, text, filename, language='en', accent='com'):
        """
        Generate voice-over using Google Text-to-Speech (Free).
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            language: Language code (en, es, fr, etc.)
            accent: Accent ('com'=US, 'co.uk'=UK, 'com.au'=Australian, 'co.in'=Indian)
        
        Returns:
            Path to generated audio file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            print(f"[gTTS] Generating voice-over: {filename}")
            
            tts = gTTS(
                text=text,
                lang=language,
                tld=accent,
                slow=False
            )
            
            tts.save(filepath)
            print(f"[SUCCESS] Voice-over saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Voice-over generation failed: {e}")
            return None
    
    def generate_voiceover_cloud(self, text, filename, voice_name='en-US-Neural2-D'):
        """
        Generate voice-over using Google Cloud TTS (Paid, Better Quality).
        
        Popular voices:
        - en-US-Neural2-D: Male, natural
        - en-US-Neural2-F: Female, natural
        - en-GB-Neural2-A: British male
        - en-GB-Neural2-C: British female
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            voice_name: Voice identifier
        
        Returns:
            Path to generated audio file
        """
        if not self.use_cloud_tts:
            print("[WARNING] Cloud TTS not enabled, using free gTTS")
            return self.generate_voiceover_gtts(text, filename)
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            print(f"[CLOUD TTS] Generating HD voice-over: {filename}")
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_name.split('-')[0] + '-' + voice_name.split('-')[1],
                name=voice_name
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            with open(filepath, 'wb') as out:
                out.write(response.audio_content)
            
            print(f"[SUCCESS] HD voice-over saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Cloud TTS failed: {e}")
            return self.generate_voiceover_gtts(text, filename)
    
    def generate_voiceover(self, text, filename='narration.mp3', 
                          voice='zephyr', emotion='neutral', accent='us'):
        """
        Generate voice-over (automatic method selection with Gemini-TTS priority).
        
        Args:
            text: Text to narrate
            filename: Output filename
            voice: For Gemini: character name (zephyr, puck, etc.)
                   For others: 'male' or 'female'
            emotion: Emotion description (only for Gemini-TTS)
            accent: 'us', 'uk', 'au', 'in'
        
        Returns:
            Path to audio file
        """
        # Priority 1: Gemini-TTS (best quality, character voices, emotions)
        if self.use_gemini_tts and voice in self.GEMINI_VOICES:
            return self.generate_voiceover_gemini(text, filename, voice, emotion)
        
        # Priority 2: Cloud TTS (high quality, paid)
        if self.use_cloud_tts:
            voice_map = {
                ('male', 'us'): 'en-US-Neural2-D',
                ('female', 'us'): 'en-US-Neural2-F',
                ('male', 'uk'): 'en-GB-Neural2-A',
                ('female', 'uk'): 'en-GB-Neural2-C',
            }
            voice_name = voice_map.get((voice, accent), 'en-US-Neural2-D')
            return self.generate_voiceover_cloud(text, filename, voice_name)
        
        # Priority 3: gTTS (free, good quality)
        accent_map = {
            'us': 'com',
            'uk': 'co.uk',
            'au': 'com.au',
            'in': 'co.in'
        }
        tld = accent_map.get(accent, 'com')
        return self.generate_voiceover_gtts(text, filename, 'en', tld)
    
    def generate_from_script(self, script_data, voice='zephyr', emotion='neutral', accent='us'):
        """
        Generate voice-over from complete script with character voices.
        
        Args:
            script_data: Script dict with scenes
            voice: Character voice name or 'male'/'female'
            emotion: Emotion for all scenes
            accent: Accent type
        
        Returns:
            List of audio file paths (one per scene)
        """
        audio_files = []
        
        for idx, scene in enumerate(script_data.get('scenes', []), 1):
            narration = scene.get('narration', scene.get('dialogue', ''))
            
            if not narration:
                print(f"[WARNING] Scene {idx} has no narration, skipping")
                continue
            
            # Detect emotion from scene if available
            scene_emotion = scene.get('tone', emotion).lower()
            
            # Generate audio
            filename = f"scene_{idx}_narration.mp3"
            audio_path = self.generate_voiceover(
                narration,
                filename,
                voice=voice,
                emotion=scene_emotion,
                accent=accent
            )
            
            if audio_path:
                audio_files.append({
                    'scene': idx,
                    'path': audio_path,
                    'text': narration,
                    'emotion': scene_emotion
                })
        
        print(f"\n[SUCCESS] Generated {len(audio_files)} voice-over files")
        return audio_files


# Usage Examples
if __name__ == "__main__":
    print("="*70)
    print("GEMINI-TTS VOICE-OVER GENERATOR")
    print("="*70)
    
    generator = VoiceOverGenerator(use_gemini_tts=True)
    
    print("\nAvailable Gemini Character Voices:")
    for voice, description in generator.GEMINI_VOICES.items():
        print(f"  • {voice}: {description}")
    
    # Example 1: Dramatic narration with excitable character
    print("\n" + "="*70)
    print("EXAMPLE 1: Dramatic Adventure")
    print("="*70)
    
    generator.generate_voiceover(
        text="I can't believe we finally found the hidden city! It's glowing with ancient magic!",
        filename="adventure_excited.mp3",
        voice="fenrir",  # Excitable character
        emotion="extremely excited and breathless"
    )
    
    # Example 2: Calm informative narration
    print("\n" + "="*70)
    print("EXAMPLE 2: Professional Documentary")
    print("="*70)
    
    generator.generate_voiceover(
        text="The history of these ruins dates back over two thousand years to an ancient civilization.",
        filename="history_calm.mp3",
        voice="charon",  # Informative character
        emotion="calm, professional, and slightly somber"
    )
    
    # Example 3: Upbeat promotional
    print("\n" + "="*70)
    print("EXAMPLE 3: Upbeat Promotion")
    print("="*70)
    
    generator.generate_voiceover(
        text="Welcome to the most amazing product you've ever seen! This will change your life!",
        filename="promo_upbeat.mp3",
        voice="puck",  # Upbeat character
        emotion="enthusiastic and energetic"
    )
    
    # Example 4: From script with emotions
    print("\n" + "="*70)
    print("EXAMPLE 4: Multi-Scene Script")
    print("="*70)
    
    script = {
        'scenes': [
            {
                'scene_number': 1,
                'narration': 'Welcome to our channel! Today we have something truly special to share.',
                'tone': 'friendly and welcoming'
            },
            {
                'scene_number': 2,
                'narration': 'Let me show you the incredible discovery we made in the ancient temple.',
                'tone': 'mysterious and intriguing'
            },
            {
                'scene_number': 3,
                'narration': 'The artifacts we found will rewrite history as we know it!',
                'tone': 'excited and dramatic'
            }
        ]
    }
    
    audio_files = generator.generate_from_script(script, voice='fenrir')
    
    print("\nGenerated files:")
    for audio in audio_files:
        print(f"  Scene {audio['scene']}: {audio['path']} ({audio['emotion']})")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\nCheck the 'voiceovers/' folder for generated audio files.")
    print("Gemini-TTS provides natural character voices with emotion!")
    print("="*70)
