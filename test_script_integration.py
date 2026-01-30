#!/usr/bin/env python3
"""
Comprehensive Test Suite for Script Generator Integration

Tests:
1. Backward compatibility (traditional mode)
2. Identity card mode
3. Full integration (identity cards + emotional AI)
4. Info generator (verify no regression)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.script_generator import ScriptGenerator
from flowchart.info.info_script_generator import InfoScriptGenerator


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, test_name):
        self.passed += 1
        self.tests.append((test_name, "PASS", None))
        print(f"  ✓ {test_name}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.tests.append((test_name, "FAIL", str(error)))
        print(f"  ✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY: {self.passed}/{total} passed")
        print(f"{'='*80}")
        if self.failed > 0:
            print("\nFailed Tests:")
            for name, status, error in self.tests:
                if status == "FAIL":
                    print(f"  - {name}: {error}")


def test_traditional_mode(results):
    """Test backward compatibility - traditional mode without identity cards"""
    print("\n[TEST 1] Traditional Mode (Backward Compatibility)")
    print("-" * 80)
    
    try:
        sg = ScriptGenerator(use_identity_cards=False, use_emotional_ai=False)
        
        # Test overview generation
        overview = sg.generate_overview("A space explorer discovers alien life")
        
        assert 'title' in overview, "Missing 'title' in overview"
        results.add_pass("Overview has title")
        
        assert 'characters' in overview, "Missing 'characters' in overview"
        results.add_pass("Overview has characters")
        
        assert 'character_description' in overview, "Missing 'character_description'"
        results.add_pass("Overview has character_description")
        
        # Test scene generation
        scenes = sg.generate_scenes(overview, num_scenes=3)
        
        assert len(scenes) == 3, f"Expected 3 scenes, got {len(scenes)}"
        results.add_pass("Generated correct number of scenes")
        
        assert 'character_name' in scenes[0], "Missing 'character_name' in scene"
        results.add_pass("Scene has character_name")
        
        assert 'background' in scenes[0], "Missing 'background' in scene"
        results.add_pass("Scene has background")
        
        assert 'dialogue' in scenes[0], "Missing 'dialogue' in scene"
        results.add_pass("Scene has dialogue")
        
        # Verify no identity card fields
        assert 'consistency_prompt' not in scenes[0], "Should not have consistency_prompt in traditional mode"
        results.add_pass("No identity card fields in traditional mode")
        
        # Verify no emotional fields
        assert 'emotion' not in scenes[0], "Should not have emotion in traditional mode"
        results.add_pass("No emotional fields in traditional mode")
        
    except Exception as e:
        results.add_fail("Traditional Mode", e)


def test_identity_card_mode(results):
    """Test identity card integration without emotional AI"""
    print("\n[TEST 2] Identity Card Mode")
    print("-" * 80)
    
    try:
        sg = ScriptGenerator(use_identity_cards=True, use_emotional_ai=False)
        
        # Test overview with identity cards
        overview = sg.generate_overview("A detective solves a mysterious case")
        
        assert 'title' in overview, "Missing 'title' in overview"
        results.add_pass("Overview has title")
        
        # Verify identity cards were created
        assert sg.card_manager is not None, "Card manager should exist"
        results.add_pass("Card manager initialized")
        
        cards = sg.get_all_cards()
        assert len(cards) > 0, "Should have created identity cards"
        results.add_pass(f"Identity cards created ({len(cards)} cards)")
        
        # Test scene generation with identity cards
        scenes = sg.generate_scenes(overview, num_scenes=3)
        
        assert len(scenes) == 3, f"Expected 3 scenes, got {len(scenes)}"
        results.add_pass("Generated scenes with identity cards")
        
        # Verify consistency prompts
        if scenes[0].get('character_name') != 'None':
            assert 'consistency_prompt' in scenes[0], "Should have consistency_prompt"
            results.add_pass("Scene has consistency_prompt")
            
            assert 'anchor_prompt' in scenes[0], "Should have anchor_prompt"
            results.add_pass("Scene has anchor_prompt")
            
            assert 'voice_prompt' in scenes[0], "Should have voice_prompt"
            results.add_pass("Scene has voice_prompt")
        
        # Verify no emotional fields (emotional AI disabled)
        assert 'emotion' not in scenes[0], "Should not have emotion when emotional AI disabled"
        results.add_pass("No emotional fields when disabled")
        
        # Test get_character_card method
        if overview['characters']:
            char_name = overview['characters'][0]
            card = sg.get_character_card(char_name)
            assert card is not None, f"Should retrieve card for {char_name}"
            results.add_pass(f"Retrieved identity card for '{char_name}'")
        
    except Exception as e:
        results.add_fail("Identity Card Mode", e)


def test_full_integration(results):
    """Test identity cards + emotional AI together"""
    print("\n[TEST 3] Full Integration (Identity Cards + Emotional AI)")
    print("-" * 80)
    
    try:
        sg = ScriptGenerator(use_identity_cards=True, use_emotional_ai=True)
        
        overview = sg.generate_overview("A chef discovers a magical recipe book")
        scenes = sg.generate_scenes(overview, num_scenes=3)
        
        # Verify identity cards
        cards = sg.get_all_cards()
        assert len(cards) > 0, "Should have identity cards"
        results.add_pass("Identity cards created in full mode")
        
        # Verify scenes generated
        assert len(scenes) == 3, f"Expected 3 scenes, got {len(scenes)}"
        results.add_pass("Scenes generated in full mode")
        
        # Check for both identity card AND emotional features
        scene = scenes[0]
        
        # Identity card features (if character exists)
        if scene.get('character_name') != 'None':
            if 'consistency_prompt' in scene:
                results.add_pass("Scene has consistency_prompt (identity card)")
            else:
                results.add_fail("Full Integration", "Missing consistency_prompt")
        
        # Emotional AI features
        if 'emotion' in scene:
            results.add_pass("Scene has emotion (emotional AI)")
        
        if 'pacing' in scene:
            results.add_pass("Scene has pacing (emotional AI)")
        
        if 'delivery_hint' in scene:
            results.add_pass("Scene has delivery_hint (emotional AI)")
        
    except Exception as e:
        results.add_fail("Full Integration", e)


def test_info_generator(results):
    """Verify info generator still works (no regression)"""
    print("\n[TEST 4] Info Generator (No Regression)")
    print("-" * 80)
    
    try:
        isg = InfoScriptGenerator(use_emotional_ai=False)
        
        script = isg.generate_full_script(
            topic="The Future of Artificial Intelligence",
            num_scenes=5,
            duration=30
        )
        
        assert 'overview' in script, "Missing 'overview' in script"
        results.add_pass("Info script has overview")
        
        assert 'scenes' in script, "Missing 'scenes' in script"
        results.add_pass("Info script has scenes")
        
        assert len(script['scenes']) == 5, f"Expected 5 scenes, got {len(script['scenes'])}"
        results.add_pass("Info script generated correct number of scenes")
        
        # Verify info-specific fields
        scene = script['scenes'][0]
        assert 'narration' in scene, "Missing 'narration' in info scene"
        results.add_pass("Info scene has narration")
        
        # Verify NO character fields (info videos don't have characters)
        assert 'character_name' not in scene or scene.get('character_name') is None, \
            "Info scenes should not have character_name"
        results.add_pass("Info scenes correctly have no characters")
        
    except Exception as e:
        results.add_fail("Info Generator", e)


def main():
    print("="*80)
    print("SCRIPT GENERATOR INTEGRATION TEST SUITE")
    print("="*80)
    
    results = TestResults()
    
    # Run all tests
    test_traditional_mode(results)
    test_identity_card_mode(results)
    test_full_integration(results)
    test_info_generator(results)
    
    # Show summary
    results.summary()
    
    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
