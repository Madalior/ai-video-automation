"""
Test Emotional Info Script Generation

Tests the emotional script generator with info/educational video scripts.
"""

from flowchart.info.info_script_generator import InfoScriptGenerator
import json

def test_emotional_info_script():
    """Test info script with emotional enhancement"""
    
    print("=" * 80)
    print("TESTING EMOTIONAL INFO SCRIPT GENERATION")
    print("=" * 80)
    
    # Initialize with emotional AI
    generator = InfoScriptGenerator(use_emotional_ai=True)
    
    # Generate full script
    topic = "The Fascinating World of Quantum Physics"
    print(f"\n[SCRIPT] Generating info script for: {topic}")
    
    script = generator.generate_full_script(
        topic=topic,
        num_scenes=8,
        duration=60
    )
    
    print(f"\n[OK] Title: {script['title']}")
    print(f"[OK] Scenes: {script['total_scenes']}")
    print(f"[OK] Duration: {script['total_duration']}s")
    
    # Display emotional metadata
    print("\n" + "=" * 80)
    print("EMOTIONAL ANALYSIS")
    print("=" * 80)
    
    scenes = script.get('scenes', [])
    for i, scene in enumerate(scenes3], 1):  # Show first 3 scenes
        print(f"\n[SCENE] Scene {i} ({scene.get('scene_type', 'N/A')}):")
        print(f"   Emotion: {scene.get('emotion', 'N/A')}")
        print(f"   Pacing: {scene.get('pacing', 'N/A')}")
        print(f"   Narration: {scene.get('narration', 'N/A')[:80]}...")
        if scene.get('delivery_hint'):
            print(f"   [DELIVERY] {scene['delivery_hint'][:80]}...")
    
    # Save complete script
    output_file = "output/test_emotional_info_script.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Complete script saved to: {output_file}")
    print("\n[SUCCESS] TEST PASSED: Emotional info script generated successfully!")
    
    return script

if __name__ == "__main__":
    try:
        test_emotional_info_script()
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
