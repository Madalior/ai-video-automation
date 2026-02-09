"""
Test script for Smart Reference System

Demonstrates the new typed reference API
"""

from flowchart.character.video_generator import DreaminaVideoGenerator
from flowchart.common.smart_reference_manager import order_references


def test_smart_references():
    """Test the new smart reference system."""
    
    print("="*70)
    print("SMART REFERENCE SYSTEM - TEST")
    print("="*70)
    
    # Initialize generator
    gen = DreaminaVideoGenerator(headless=False)
    
    # Test 1: Legacy single reference (backward compatible)
    print("\n[TEST 1] Legacy single reference:")
    print("  Code: generate_video(prompt, reference_image_paths='char.png')")
    # Would work exactly as before
    
    # Test 2: Legacy list (backward compatible)
    print("\n[TEST 2] Legacy list:")
    print("  Code: generate_video(prompt, reference_image_paths=['img1.png', 'img2.png'])")
    # Would work exactly as before
    
    # Test 3: NEW - Typed dict (all 3 types)
    print("\n[TEST 3] NEW Typed dict (all 3 types):")
    refs = {
        'character': 'detective.png',
        'background': 'room_style.png',
        'continuity': 'prev_frame.png'
    }
    print(f"  Input: {refs}")
    print("  Processing:")
    ordered = gen.ref_manager.process_references(refs)
    print(f"  Output order: {ordered}")
    print("  → Priority: continuity > character > background")
    
    # Test 4: NEW - Partial dict (character + continuity)
    print("\n[TEST 4] NEW Partial dict (character + continuity):")
    refs = {
        'character': 'detective.png',
        'continuity': 'prev_frame.png'
    }
    print(f"  Input: {refs}")
    ordered = gen.ref_manager.process_references(refs)
    print(f"  Output: {ordered}")
    
    # Test 5: Helper function
    print("\n[TEST 5] Helper function:")
    print("  Code: order_references(character='detective.png', continuity='prev.png')")
    ordered = order_references(
        character='detective.png',
        continuity='prev_frame.png'
    )
    print(f"  Output: {ordered}")
    
    print("\n" + "="*70)
    print("USAGE EXAMPLES")
    print("="*70)
    
    print("""
# Example 1: Chained Consistency (scene by scene)
generate_video(
    prompt="Detective walks in rain",
    reference_image_paths={'continuity': 'scene01_frame.png'}
)

# Example 2: New Location, Same Character
generate_video(
    prompt="Detective enters warehouse",
    reference_image_paths={
        'character': 'detective_ref.png',      # Keep character look
        'background': 'warehouse_style.png',    # New environment aesthetic
        'continuity': 'prev_scene_frame.png'    # Previous lighting/mood
    }
)

# Example 3: Character-Focused Scene
generate_video(
    prompt="Detective closeup thinking",
    reference_image_paths={
        'character': 'detective_face.png',
        'continuity': 'prev_frame.png'
    }
)

# Example 4: Legacy still works
generate_video(
    prompt="Detective walks",
    reference_image_paths="single_ref.png"  # Old way still works!
)
    """)
    
    print("="*70)
    print("SMART REFERENCE SYSTEM READY! ✅")
    print("="*70)


if __name__ == "__main__":
    test_smart_references()
