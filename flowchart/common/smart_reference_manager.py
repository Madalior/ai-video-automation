"""
🔥🔥🔥 SMART REFERENCE MANAGER - GOD MASTER MODE 🔥🔥🔥

Ensures visual consistency across ALL scenes by intelligently managing
reference images, auto-chaining scene outputs, and locking visual styles.

OLD system: Just ordered references by priority
NEW system: Auto-chain + reference bank + style lock + scene tracker

Architecture:
  • AUTO-CHAIN: Each scene's output → next scene's continuity reference
  • REFERENCE BANK: Multiple angles per character (face, body, side)
  • STYLE LOCK: Scene 1 sets the style → ALL scenes match it
  • SMART SELECT: Choose best reference based on scene context
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Union, List, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCE_BANK_DIR = PROJECT_ROOT / 'reference_bank'


class SmartReferenceManager:
    """
    🧠 GOD MASTER MODE Reference Manager

    Manages ALL reference images for consistent AI generation.
    Works with identity cards to build optimal reference sets per scene.
    """

    PRIORITY_ORDER = ['continuity', 'character', 'style', 'background']

    def __init__(self, mode='auto_chain', project_dir: str = None):
        """
        Initialize reference manager.

        Args:
            mode: Processing mode
                - 'auto_chain': Auto-chain scene outputs (recommended)
                - 'smart_order': Order by priority only
                - 'reference_bank': Use multi-angle reference bank
            project_dir: Where to store reference bank files
        """
        self.mode = mode
        self.project_dir = Path(project_dir) if project_dir else REFERENCE_BANK_DIR

        # ═══ AUTO-CHAIN STATE ═══
        self.scene_chain = {}  # character_name -> [scene1_output, scene2_output, ...]
        self.last_outputs = {}  # character_name -> last output path

        # ═══ REFERENCE BANK ═══
        # character_name -> {'face': path, 'full_body': path, 'side': path, 'sheet': path}
        self.reference_bank = {}

        # ═══ VISUAL STYLE LOCK ═══
        self.style_locked = False
        self.locked_style = {
            'color_palette': '',
            'lighting': '',
            'art_style': '',
            'aspect_ratio': '16:9',
        }

        # ═══ SCENE TRACKER ═══
        self.scene_log = []  # [{scene_number, character, refs_used, output}]

    # ═══════════════════════════════════════════════════════════
    # 🔗 AUTO-CHAIN: Scene-to-Scene Continuity
    # ═══════════════════════════════════════════════════════════

    def chain_scene_output(self, character_name: str, scene_number: int,
                           output_path: str):
        """
        Register a scene's output as the continuity reference for the NEXT scene.
        Call this AFTER each scene is generated.

        If the output is a video (.mp4/.webm/.mov), extracts the LAST FRAME
        and stores that image as the continuity reference (not the whole video).

        Args:
            character_name: Which character this output shows
            scene_number: Scene number
            output_path: Path to the generated image/video
        """
        if not output_path or not os.path.exists(output_path):
            print(f"   ⚠️ Output path invalid: {output_path}")
            return

        # If it's a video file, extract the last frame as an image
        ref_path = output_path
        video_extensions = ('.mp4', '.webm', '.mov', '.avi', '.mkv')
        if output_path.lower().endswith(video_extensions):
            ref_path = self._extract_last_frame(output_path, scene_number)
            if not ref_path:
                print(f"   ⚠️ Could not extract last frame from {output_path}, skipping chain")
                return

        if character_name not in self.scene_chain:
            self.scene_chain[character_name] = []

        self.scene_chain[character_name].append({
            'scene': scene_number,
            'path': ref_path,
            'original_video': output_path if ref_path != output_path else None,
            'timestamp': datetime.now().isoformat(),
        })

        self.last_outputs[character_name] = ref_path

        self.scene_log.append({
            'scene_number': scene_number,
            'character': character_name,
            'output': ref_path,
            'original_video': output_path if ref_path != output_path else None,
            'chained': True,
        })

        print(f"   🔗 Chained scene {scene_number} output for {character_name} → {os.path.basename(ref_path)}")

    def _extract_last_frame(self, video_path: str, scene_number: int) -> str:
        """
        Extract the last frame from a video file using ffmpeg.
        
        Returns:
            Path to the extracted frame image, or None on failure.
        """
        frame_dir = os.path.join('output', 'frames_cache')
        os.makedirs(frame_dir, exist_ok=True)
        frame_path = os.path.join(frame_dir, f"scene_{scene_number}_last_frame.png")
        
        try:
            # Method 1: Use -sseof to seek from end (fast)
            result = subprocess.run([
                'ffmpeg', '-y',
                '-sseof', '-0.5',
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                frame_path
            ], capture_output=True, timeout=30)
            
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                print(f"   🎞️ Extracted last frame: {os.path.basename(frame_path)}")
                return frame_path
            
            # Method 2: Fallback — grab frame from last second
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', 'select=gte(n\\,1)',
                '-vframes', '1',
                '-q:v', '2',
                frame_path
            ], capture_output=True, timeout=30)
            
            if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                print(f"   🎞️ Extracted frame (fallback): {os.path.basename(frame_path)}")
                return frame_path
                
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ ffmpeg timeout extracting frame from {video_path}")
        except FileNotFoundError:
            print(f"   ⚠️ ffmpeg not found — cannot extract last frame")
        except Exception as e:
            print(f"   ⚠️ Frame extraction error: {e}")
        
        return None

    def get_continuity_ref(self, character_name: str) -> Optional[str]:
        """Get the last scene's output as continuity reference."""
        path = self.last_outputs.get(character_name)
        if path and os.path.exists(path):
            return path
        return None

    # ═══════════════════════════════════════════════════════════
    # 📦 REFERENCE BANK: Multi-Angle Character References
    # ═══════════════════════════════════════════════════════════

    def register_reference(self, character_name: str, ref_type: str, path: str):
        """
        Add a reference image to the character's bank.

        Args:
            character_name: Character name
            ref_type: Type of reference:
                - 'face': Close-up face reference
                - 'full_body': Full body reference
                - 'side': Side profile reference
                - 'sheet': Character sheet (multi-angle)
                - 'style': Art style reference
            path: Path to image
        """
        if not os.path.exists(path):
            print(f"   ⚠️ Reference not found: {path}")
            return

        if character_name not in self.reference_bank:
            self.reference_bank[character_name] = {}

        self.reference_bank[character_name][ref_type] = path

        # Save to bank directory
        bank_dir = self.project_dir / character_name.replace(' ', '_')
        bank_dir.mkdir(parents=True, exist_ok=True)

        # Copy reference to bank
        dest = bank_dir / f"{ref_type}{Path(path).suffix}"
        if not dest.exists() or str(dest) != str(path):
            try:
                shutil.copy2(path, dest)
            except Exception:
                pass  # Original path is fine

        print(f"   📦 Registered {ref_type} reference for {character_name}")

    def get_best_reference(self, character_name: str,
                           scene_type: str = 'default') -> Optional[str]:
        """
        Get the BEST reference image for a scene based on context.

        Args:
            character_name: Character name
            scene_type: Type of scene:
                - 'close_up': Use face reference
                - 'wide_shot': Use full body reference
                - 'action': Use full body reference
                - 'dialogue': Use face reference
                - 'default': Use sheet or face
        """
        bank = self.reference_bank.get(character_name, {})

        if scene_type in ('close_up', 'dialogue'):
            # Face close-up → use face reference
            for ref in ['face', 'sheet', 'full_body']:
                if ref in bank and os.path.exists(bank[ref]):
                    return bank[ref]

        elif scene_type in ('wide_shot', 'action'):
            # Wide/action → use full body
            for ref in ['full_body', 'sheet', 'face']:
                if ref in bank and os.path.exists(bank[ref]):
                    return bank[ref]

        else:
            # Default priority: sheet > face > full_body > side
            for ref in ['sheet', 'face', 'full_body', 'side', 'style']:
                if ref in bank and os.path.exists(bank[ref]):
                    return bank[ref]

        return None

    def load_bank(self, directory: str = None):
        """Load all references from the bank directory."""
        bank_dir = Path(directory) if directory else self.project_dir
        if not bank_dir.exists():
            return

        count = 0
        for char_dir in bank_dir.iterdir():
            if char_dir.is_dir():
                char_name = char_dir.name.replace('_', ' ')
                self.reference_bank[char_name] = {}
                for ref_file in char_dir.iterdir():
                    if ref_file.is_file() and ref_file.suffix in ('.png', '.jpg', '.jpeg', '.webp'):
                        ref_type = ref_file.stem  # face, full_body, etc.
                        self.reference_bank[char_name][ref_type] = str(ref_file)
                        count += 1

        if count:
            print(f"   📦 Loaded {count} references from bank")

    # ═══════════════════════════════════════════════════════════
    # 🔒 VISUAL STYLE LOCK
    # ═══════════════════════════════════════════════════════════

    def lock_style(self, color_palette: str = '', lighting: str = '',
                   art_style: str = '', aspect_ratio: str = ''):
        """
        Lock visual style for ALL subsequent scenes.
        Once locked, every scene prompt gets style injection.
        """
        if color_palette:
            self.locked_style['color_palette'] = color_palette
        if lighting:
            self.locked_style['lighting'] = lighting
        if art_style:
            self.locked_style['art_style'] = art_style
        if aspect_ratio:
            self.locked_style['aspect_ratio'] = aspect_ratio

        self.style_locked = True
        print(f"   🔒 Visual style LOCKED: {self.locked_style}")

    def get_style_injection(self) -> str:
        """
        Get visual style text to inject into every prompt.
        Returns empty string if style is not locked.
        """
        if not self.style_locked:
            return ""

        parts = []
        if self.locked_style['color_palette']:
            parts.append(f"Color palette: {self.locked_style['color_palette']}")
        if self.locked_style['lighting']:
            parts.append(f"Lighting: {self.locked_style['lighting']}")
        if self.locked_style['art_style']:
            parts.append(f"Art style: {self.locked_style['art_style']}")

        return "[STYLE LOCK] " + " | ".join(parts) if parts else ""

    # ═══════════════════════════════════════════════════════════
    # 🎯 MAIN: Build References for a Scene
    # ═══════════════════════════════════════════════════════════

    def process_references(
        self,
        references: Union[str, List[str], Dict[str, str]],
        scene_context: Optional[Dict] = None
    ) -> List[str]:
        """
        Process references into a Veo-compatible ordered list.
        GOD MASTER MODE: Also considers auto-chain and reference bank.

        Args:
            references: Input references (str, list, or typed dict)
            scene_context: Optional scene metadata:
                - character_name: Which character
                - scene_type: close_up, wide_shot, action, dialogue
                - scene_number: Scene number

        Returns:
            Ordered list of up to 3 validated image paths
        """
        if not references:
            # In auto_chain mode, try to build references from chain + bank
            if self.mode == 'auto_chain' and scene_context:
                return self._auto_build_references(scene_context)
            return []

        # Handle typed dict (new format)
        if isinstance(references, dict):
            return self._smart_order(references, scene_context)

        # Handle list (legacy)
        if isinstance(references, list):
            return self._validate_paths(references)[:3]

        # Handle string (legacy single path)
        return self._validate_paths([references])

    def should_chain_scene(self, current_scene: dict, previous_scene: dict) -> bool:
        """
        Decide if current scene should chain from previous scene's output,
        or use ID card primary reference instead.

        Chain when: same character + same/similar location (continuity matters)
        Independent when: different character, different location, act change

        Args:
            current_scene: Current scene dict with character_name, background, act
            previous_scene: Previous scene dict (None for first scene)

        Returns:
            True if scene should chain from previous output, False if independent
        """
        if not previous_scene:
            return False  # First scene is always independent

        # Different character → independent
        curr_char = current_scene.get('character_name', '')
        prev_char = previous_scene.get('character_name', '')
        if curr_char != prev_char:
            print(f"   🆔 Scene independent: character changed ({prev_char} → {curr_char})")
            return False

        # Different act → independent (major story transition)
        curr_act = current_scene.get('act', '')
        prev_act = previous_scene.get('act', '')
        if curr_act and prev_act and curr_act != prev_act:
            print(f"   🆔 Scene independent: act changed ({prev_act} → {curr_act})")
            return False

        # Different background/location → independent
        curr_bg = current_scene.get('background', '').lower().strip()
        prev_bg = previous_scene.get('background', '').lower().strip()
        if curr_bg and prev_bg and curr_bg != prev_bg:
            print(f"   🆔 Scene independent: location changed")
            return False

        # Same character, same act, same/unknown location → chain!
        print(f"   🔗 Scene chained: same character ({curr_char}) + same context")
        return True

    def _auto_build_references(self, scene_context: Dict,
                               previous_scene: Dict = None) -> List[str]:
        """
        Automatically build reference set from chain + bank.
        Uses should_chain_scene() to decide between chaining and ID card ref.
        """
        char_name = scene_context.get('character_name', '')
        scene_type = scene_context.get('scene_type', 'default')
        refs = []

        if self.should_chain_scene(scene_context, previous_scene):
            # Chain: use previous scene output for continuity
            continuity = self.get_continuity_ref(char_name)
            if continuity:
                refs.append(continuity)
        else:
            # Independent: use ID card primary reference from bank
            bank_ref = self.get_best_reference(char_name, scene_type)
            if bank_ref:
                refs.append(bank_ref)
                print(f"   🆔 Using ID card reference for {char_name}")
                return refs[:3]

        # Also add bank ref if not already there (supplementary)
        bank_ref = self.get_best_reference(char_name, scene_type)
        if bank_ref and bank_ref not in refs:
            refs.append(bank_ref)

        return refs[:3]

    def _smart_order(self, refs: Dict[str, str],
                     scene_context: Optional[Dict] = None) -> List[str]:
        """Order references by priority with auto-chain enhancement."""
        ordered = []

        # If auto-chain mode, inject continuity reference
        if self.mode == 'auto_chain' and scene_context:
            char_name = scene_context.get('character_name', '')
            if 'continuity' not in refs:
                continuity = self.get_continuity_ref(char_name)
                if continuity:
                    refs['continuity'] = continuity

        # Add in priority order
        for ref_type in self.PRIORITY_ORDER:
            if ref_type in refs and refs[ref_type]:
                path = refs[ref_type]
                if os.path.exists(path):
                    ordered.append(path)
                else:
                    print(f"   ⚠️ {ref_type} reference not found: {path}")

        result = ordered[:3]

        if result:
            print(f"   🎯 Ordered {len(result)} reference(s):")
            for i, path in enumerate(result, 1):
                ref_type = self._identify_type(path, refs)
                print(f"      {i}. [{ref_type}] {os.path.basename(path)}")

        return result

    def _identify_type(self, path: str, refs: Dict[str, str]) -> str:
        """Identify reference type from path."""
        for ref_type, ref_path in refs.items():
            if ref_path == path:
                return ref_type.upper()
        return "UNKNOWN"

    def _validate_paths(self, paths: List[str]) -> List[str]:
        """Validate that paths exist."""
        validated = []
        for path in paths:
            if path and os.path.exists(path):
                validated.append(path)
            elif path:
                print(f"   ⚠️ Reference not found: {path}")
        return validated

    def create_reference_dict(
        self,
        character: Optional[str] = None,
        background: Optional[str] = None,
        continuity: Optional[str] = None,
        style: Optional[str] = None,
    ) -> Dict[str, str]:
        """Helper to create typed reference dictionary."""
        refs = {}
        if character:
            refs['character'] = character
        if background:
            refs['background'] = background
        if continuity:
            refs['continuity'] = continuity
        if style:
            refs['style'] = style
        return refs

    # ═══════════════════════════════════════════════════════════
    # 📊 SCENE LOG & PERSISTENCE
    # ═══════════════════════════════════════════════════════════

    def save_state(self, filepath: str = None):
        """Save reference manager state to disk."""
        save_path = filepath or str(self.project_dir / 'reference_state.json')
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        state = {
            'mode': self.mode,
            'style_locked': self.style_locked,
            'locked_style': self.locked_style,
            'scene_chain': self.scene_chain,
            'last_outputs': self.last_outputs,
            'reference_bank': self.reference_bank,
            'scene_log': self.scene_log,
            'saved_at': datetime.now().isoformat(),
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"   💾 Reference state saved: {save_path}")

    def load_state(self, filepath: str = None):
        """Load reference manager state from disk."""
        load_path = filepath or str(self.project_dir / 'reference_state.json')
        if not os.path.exists(load_path):
            return

        with open(load_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        self.mode = state.get('mode', self.mode)
        self.style_locked = state.get('style_locked', False)
        self.locked_style = state.get('locked_style', self.locked_style)
        self.scene_chain = state.get('scene_chain', {})
        self.last_outputs = state.get('last_outputs', {})
        self.reference_bank = state.get('reference_bank', {})
        self.scene_log = state.get('scene_log', [])
        print(f"   📂 Reference state loaded from {load_path}")

    def get_chain_summary(self) -> Dict:
        """Get summary of all chains for debugging."""
        summary = {}
        for char, chain in self.scene_chain.items():
            summary[char] = {
                'total_scenes': len(chain),
                'last_scene': chain[-1]['scene'] if chain else None,
                'last_output': self.last_outputs.get(char, 'None'),
            }
        return summary

    def __repr__(self):
        chars = len(self.scene_chain)
        scenes = sum(len(c) for c in self.scene_chain.values())
        bank = sum(len(v) for v in self.reference_bank.values())
        return f"<SmartRefManager mode={self.mode} | {chars} chars | {scenes} scenes | {bank} refs>"


# ═══════════════════════════════════════════════════════════
# 🎮 CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════

def order_references(
    character: Optional[str] = None,
    background: Optional[str] = None,
    continuity: Optional[str] = None,
    style: Optional[str] = None,
) -> List[str]:
    """Quick helper to order references by priority."""
    manager = SmartReferenceManager(mode='smart_order')
    ref_dict = manager.create_reference_dict(character, background, continuity, style)
    return manager.process_references(ref_dict)


# ═══════════════════════════════════════════════════════════
# 🎮 STANDALONE DEMO
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 60)
    print("🔥 SMART REFERENCE MANAGER — GOD MASTER MODE")
    print("═" * 60)

    mgr = SmartReferenceManager(mode='auto_chain')

    # Simulate scene chain
    print("\n🔗 AUTO-CHAIN DEMO:")
    print("   (Simulating 3 scenes with auto-chaining)")

    # Scene 1: No continuity yet
    refs1 = mgr.process_references(
        {'character': 'test.png'},
        scene_context={'character_name': 'Ravi', 'scene_type': 'dialogue', 'scene_number': 1}
    )
    print(f"   Scene 1 refs: {refs1}")

    # Chain scene 1 output → becomes scene 2's continuity
    # (In real use, this is the generated image/video)
    print("\n   Chaining scene 1 output...")
    # mgr.chain_scene_output('Ravi', 1, 'output/scene_1.png')

    # Style lock
    print("\n🔒 STYLE LOCK DEMO:")
    mgr.lock_style(
        color_palette='Warm earthy tones',
        lighting='Golden hour natural',
        art_style='Realistic 3D animation'
    )
    print(f"   Style injection: {mgr.get_style_injection()}")

    # Summary
    print(f"\n✅ {repr(mgr)}")
    print("\n═" * 60)
    print("Smart Reference Manager GOD MASTER MODE Ready! ✅")
    print("═" * 60)
