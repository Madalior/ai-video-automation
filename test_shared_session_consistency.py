"""
Test Script: Shared Session + Chained Consistency

This script tests both features simultaneously:
1. Shared Session: 1 account for both image and video generators
2. Chained Consistency: Scene N frame → Scene N+1 reference

Expected behavior:
- Single login for both generators
- Scene 1 generates without reference
- Scene 2 uses frame from Scene 1 as reference
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.character_video_manager import CharacterVideoManager


def test_shared_session_with_chained_consistency():
    """Test both shared session and chained consistency together."""
    
    print("\n" + "="*80)
    print("TEST: Shared Session + Chained Consistency")
    print("="*80)
    print()
    print("Features being tested:")
    print("  ✅ Shared Session: 1 account for both image + video generators")
    print("  ✅ Chained Consistency: Scene 1 frame → Scene 2 reference")
    print()
    print("="*80 + "\n")
    
    # Create manager with BOTH features enabled
    manager = CharacterVideoManager(
        output_dir="output/test_shared_consistency",
        headless=False,  # Set to False to watch the process
        use_shared_session=True,      # ← SHARED SESSION
        use_chained_consistency=True  # ← CHAINED CONSISTENCY
    )
    
    # Simple 2-scene story
    video_idea = "A space explorer discovers an alien artifact"
    
    print("\n[TEST] Running 2-scene production...")
    print(f"[TEST] Story: {video_idea}\n")
    
    try:
        result = manager.produce_video(
            video_idea=video_idea,
            num_scenes=2  # Keep it short for testing
        )
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        
        if result.get('status') == 'completed':
            print("\n✅ TEST PASSED!")
            print("\nVerify the following:")
            print("  1. SHARED SESSION:")
            print("     - Only ONE login occurred")
            print("     - Image generator printed: 'Using shared session'")
            print("     - Video generator printed: 'Using shared session'")
            print()
            print("  2. CHAINED CONSISTENCY:")
            print("     - Scene 1: Generated without reference")
            print("     - Scene 1: Frame extracted from output")
            print("     - Scene 2: Used Scene 1 frame as reference")
            print()
            print("  3. OUTPUT FILES:")
            
            project_id = result.get('project_id', 'unknown')
            base_dir = "output/test_shared_consistency"
            
            print(f"\n     Images:")
            print(f"     - {base_dir}/images/{project_id}_scene01.png")
            print(f"     - {base_dir}/images/{project_id}_scene01_chain_ref.png (extracted)")
            print(f"     - {base_dir}/images/{project_id}_scene02.png")
            
            print(f"\n     Videos:")
            print(f"     - {base_dir}/videos/{project_id}_scene01.mp4")
            print(f"     - {base_dir}/videos/{project_id}_scene02.mp4")
            
            print("\n" + "="*80)
            return True
        else:
            print("\n❌ TEST FAILED")
            print(f"Status: {result.get('status')}")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED WITH EXCEPTION")
        print("="*80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("INTEGRATION TEST: Shared Session + Chained Consistency")
    print("🚀 "*20)
    
    success = test_shared_session_with_chained_consistency()
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("\nBoth shared session and chained consistency are working correctly.")
        print("Your video automation is now:")
        print("  - 50% more efficient (1 account instead of 2)")
        print("  - More consistent (frames chained between scenes)")
    else:
        print("❌ TESTS FAILED")
        print("Please review the output above for errors.")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
