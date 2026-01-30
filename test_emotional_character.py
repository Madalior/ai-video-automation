"""
Test Emotional Character Script Generation

Tests the emotional script generator with character-based video scripts.
"""

from flowchart.character.script_generator import ScriptGenerator
import json

def test_emotional_character_script():
    """Test character script with emotional enhancement"""
    
    print("=" * 80)
    print("TESTING EMOTIONAL CHARACTER SCRIPT GENERATION")
    print("=" * 80)
    
    # Initialize with emotional AI
    generator = ScriptGenerator(use_emotional_ai=True)
    
    # Generate overview
    video_idea = "A Woman's Journey Through the Enchanted Forest"
    print(f"\n[SCRIPT] Generating overview for: {video_idea}")
    overview = generator.generate_overview(video_idea)
    
    print(f"[OK] Title: {overview['title']}")
    print(f"[OK] Characters: {', '.join(overview.get('characters', []))}")
    
    # Generate scenes with emotion
    print(f"\n[SCENES] Generating scenes with emotional enhancement...")
    scenes = generator.generate_scenes(overview, num_scenes=7)
    
    print(f"\n[OK] Generated {len(scenes)} scenes")
    
    # Display emotional metadata
    print("\n" + "=" * 80)
    print("EMOTIONAL ANALYSIS")
    print("=" * 80)
    
    for i, scene in enumerate(scenes[:3], 1):  # Show first 3 scenes
        print(f"\n[SCENE] Scene {i}:")
        print(f"   Character: {scene.get('character_name', 'N/A')}")
        print(f"   Emotion: {scene.get('emotion', 'N/A')}")
        print(f"   Pacing: {scene.get('pacing', 'N/A')}")
        print(f"   Dialogue: {scene.get('dialogue', 'N/A')[:80]}...")
        if scene.get('delivery_hint'):
            print(f"   [DELIVERY] {scene['delivery_hint'][:80]}...")
    
    # Save complete script
    output_file = "output/test_emotional_character_script.json"
    complete_script = {
        "overview": overview,
        "scenes": scenes,
        "total_scenes": len(scenes),
        "emotional_enhancement": True
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_script, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Complete script saved to: {output_file}")
    print("\n[SUCCESS] TEST PASSED: Emotional character script generated successfully!")
    
    return complete_script

if __name__ == "__main__":
    try:
        test_emotional_character_script()
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
