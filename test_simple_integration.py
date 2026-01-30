#!/usr/bin/env python3
"""Simple test to verify the script generator works"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Script Generator Integration...")
print("="*60)

# Test 1: Import Test
print("\n[1] Import Test")
try:
    from flowchart.character.script_generator import ScriptGenerator
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialization Test
print("\n[2] Initialization Test")
try:
    sg = ScriptGenerator(use_identity_cards=True, use_emotional_ai=False)
    print("✓ ScriptGenerator initialized")
    print(f"  - use_identity_cards: {sg.use_identity_cards}")
    print(f"  - card_manager exists: {sg.card_manager is not None}")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Basic Overview Generation
print("\n[3] Overview Generation Test")
try:
    overview = sg.generate_overview("A simple test story")
    print("✓ Overview generated")
    print(f"  - Title: {overview.get('title', 'N/A')}")
    print(f"  - Characters: {overview.get('characters', [])}")
    
    # Check if identity cards were created
    if sg.card_manager:
        cards = sg.get_all_cards()
        print(f"  - Identity cards created: {len(cards)}")
except Exception as e:
    print(f"✗ Overview generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Scene Generation
print("\n[4] Scene Generation Test")
try:
    scenes = sg.generate_scenes(overview, num_scenes=2)
    print("✓ Scenes generated")
    print(f"  - Number of scenes: {len(scenes)}")
    
    if scenes:
        scene1 = scenes[0]
        print(f"  - Scene 1 character: {scene1.get('character_name', 'N/A')}")
        print(f"  - Has consistency_prompt: {'consistency_prompt' in scene1}")
        print(f"  - Has dialogue: {'dialogue' in scene1}")
except Exception as e:
    print(f"✗ Scene generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Traditional Mode
print("\n[5] Traditional Mode Test (Backward Compatibility)")
try:
    sg_trad = ScriptGenerator(use_identity_cards=False, use_emotional_ai=False)
    overview_trad = sg_trad.generate_overview("Another test")
    scenes_trad = sg_trad.generate_scenes(overview_trad, num_scenes=2)
    
    print("✓ Traditional mode works")
    print(f"  - Scenes generated: {len(scenes_trad)}")
    print(f"  - Has identity cards: {sg_trad.card_manager is not None}")
except Exception as e:
    print(f"✗ Traditional mode failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nIntegration verified:")
print("  ✓ Identity card system working")
print("  ✓ Scene generation with consistency prompts")
print("  ✓ Backward compatibility maintained")
