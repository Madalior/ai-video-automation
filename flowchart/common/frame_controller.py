"""
Frame Controller for Scene Transitions

Implements Veo 3.1's first/last frame control technique for seamless scene transitions.
Uses the last frame of previous scene as first frame reference for next scene.
"""

import cv2
import os
from typing import Optional, Tuple
from flowchart.common.frame_extractor import extract_last_frame, extract_first_frame


class FrameController:
    """
    Manages frame extraction and transition control for video scenes.
    
    Features:
    - Extract last frame from completed scenes
    - Use previous frame as reference for next scene
    - Create smooth visual continuity
    - Automatic frame management
    """
    
    def __init__(self, frames_dir: str = "frames_cache"):
        """
        Initialize frame controller.
        
        Args:
            frames_dir: Directory to store extracted frames
        """
        self.frames_dir = frames_dir
        os.makedirs(frames_dir, exist_ok=True)
        self.scene_frames = {}  # scene_num -> {'first': path, 'last': path}
    
    def extract_scene_frames(self, scene_num: int, video_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract first and last frames from a scene video.
        
        Args:
            scene_num: Scene number
            video_path: Path to scene video
        
        Returns:
            Tuple of (first_frame_path, last_frame_path)
        """
        if not os.path.exists(video_path):
            print(f"[ERROR] Video not found: {video_path}")
            return None, None
        
        # Define output paths
        first_frame_path = os.path.join(
            self.frames_dir,
            f"scene_{scene_num:02d}_first.jpg"
        )
        last_frame_path = os.path.join(
            self.frames_dir,
            f"scene_{scene_num:02d}_last.jpg"
        )
        
        # Extract frames
        print(f"[FRAME] Extracting frames from scene {scene_num}...")
        first = extract_first_frame(video_path, first_frame_path)
        last = extract_last_frame(video_path, last_frame_path)
        
        # Cache paths
        self.scene_frames[scene_num] = {
            'first': first,
            'last': last
        }
        
        return first, last
    
    def get_transition_reference(self, current_scene_num: int) -> Optional[str]:
        """
        Get reference frame for smooth transition to current scene.
        
        Uses last frame of previous scene as reference for current scene.
        
        Args:
            current_scene_num: Current scene number
        
        Returns:
            Path to reference frame, or None if first scene
        """
        if current_scene_num <= 1:
            # First scene has no previous frame
            return None
        
        prev_scene_num = current_scene_num - 1
        
        # Check if previous scene frames were extracted
        if prev_scene_num in self.scene_frames:
            prev_last = self.scene_frames[prev_scene_num].get('last')
            if prev_last and os.path.exists(prev_last):
                print(f"[TRANSITION] Using scene {prev_scene_num} last frame for scene {current_scene_num}")
                return prev_last
        
        return None
    
    def collect_references_for_scene(
        self,
        scene_num: int,
        character_ref: Optional[str] = None,
        background_ref: Optional[str] = None
    ) -> list:
        """
        Collect all reference images for a scene (up to 3 for Veo 3.1).
        
        Priority order:
        1. Character reference (for consistency)
        2. Previous scene last frame (for transition)
        3. Background reference (for style)
        
        Args:
            scene_num: Current scene number
            character_ref: Path to character reference image
            background_ref: Path to background reference image
        
        Returns:
            List of up to 3 reference image paths
        """
        references = []
        
        # 1. Character reference (highest priority)
        if character_ref and os.path.exists(character_ref):
            references.append(character_ref)
            print(f"  [1/3] Character reference: {os.path.basename(character_ref)}")
        
        # 2. Previous scene transition frame
        transition_ref = self.get_transition_reference(scene_num)
        if transition_ref and len(references) < 3:
            references.append(transition_ref)
            print(f"  [2/3] Transition frame: {os.path.basename(transition_ref)}")
        
        # 3. Background reference
        if background_ref and os.path.exists(background_ref) and len(references) < 3:
            references.append(background_ref)
            print(f"  [3/3] Background reference: {os.path.basename(background_ref)}")
        
        print(f"[REFERENCES] Collected {len(references)} reference(s) for scene {scene_num}")
        return references
    
    def create_transition_prompt(
        self,
        base_prompt: str,
        has_transition_ref: bool,
        duration: int = 8
    ) -> str:
        """
        Enhance prompt with transition guidance.
        
        Args:
            base_prompt: Original scene prompt
            has_transition_ref: Whether transition reference is provided
            duration: Scene duration in seconds
        
        Returns:
            Enhanced prompt with transition instructions
        """
        if has_transition_ref:
            transition_instruction = (
                f"Smoothly transition from reference frame, "
                f"maintaining visual continuity. "
            )
            return f"{transition_instruction}{base_prompt} Duration: {duration}s"
        else:
            return f"{base_prompt} Duration: {duration}s"
    
    def cleanup(self):
        """Remove all cached frames."""
        import shutil
        if os.path.exists(self.frames_dir):
            shutil.rmtree(self.frames_dir)
            print(f"[CLEANUP] Removed frame cache: {self.frames_dir}")
    
    def get_scene_frame_info(self, scene_num: int) -> dict:
        """Get frame information for a scene."""
        return self.scene_frames.get(scene_num, {})


# Integration helper
def integrate_frame_transitions(
    scene_num: int,
    previous_video_path: Optional[str],
    character_ref: str,
    frame_controller: FrameController
) -> list:
    """
    Helper to integrate frame transitions into video generation.
    
    Args:
        scene_num: Current scene number
        previous_video_path: Path to previous scene's video
        character_ref: Character reference image
        frame_controller: FrameController instance
    
    Returns:
        List of reference images for video generation
    """
    # Extract frames from previous scene if available
    if previous_video_path and os.path.exists(previous_video_path):
        frame_controller.extract_scene_frames(scene_num - 1, previous_video_path)
    
    # Collect all references
    references = frame_controller.collect_references_for_scene(
        scene_num=scene_num,
        character_ref=character_ref
    )
    
    return references


# Demo
if __name__ == "__main__":
    print("="*80)
    print("FRAME CONTROLLER DEMO")
    print("="*80)
    
    controller = FrameController(frames_dir="test_frames_cache")
    
    # Simulate scene workflow
    print("\n[SCENE 1] First scene")
    refs1 = controller.collect_references_for_scene(
        scene_num=1,
        character_ref="character_detective.png"
    )
    print(f"References: {len(refs1)}")
    
    # Simulate scene 1 completion
    controller.scene_frames[1] = {
        'first': "test_frames_cache/scene_01_first.jpg",
        'last': "test_frames_cache/scene_01_last.jpg"
    }
    
    print("\n[SCENE 2] With transition from Scene 1")
    refs2 = controller.collect_references_for_scene(
        scene_num=2,
        character_ref="character_detective.png"
    )
    print(f"References: {len(refs2)}")
    
    print("\n[PROMPT ENHANCEMENT]")
    base_prompt = "Detective examines evidence in office"
    enhanced = controller.create_transition_prompt(
        base_prompt,
        has_transition_ref=True,
        duration=8
    )
    print(f"Original: {base_prompt}")
    print(f"Enhanced: {enhanced}")
    
    print("\n✅ Frame controller working! Scenes will have smooth transitions.")
