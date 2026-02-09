"""
Test Script for Character Video Manager

This script tests the character_video_manager.py with a simple test prompt.
It will run through all phases of the pipeline with minimal setup.
"""

import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.character_video_manager import CharacterVideoManager


def test_character_video_manager():
    """
    Test the Character Video Manager with a simple prompt.
    """
    print("\n" + "="*80)
    print("TESTING CHARACTER VIDEO MANAGER")
    print("="*80 + "\n")
    
    # Test prompt
    test_video_idea = "A brave astronaut discovers a mysterious alien artifact on Mars"
    
    # Initialize manager
    print("[TEST] Initializing Character Video Manager...")
    manager = CharacterVideoManager(
        output_dir="output/test_character_videos",
        headless=False,  # Use visible browser for testing/debugging
        proxy_manager=None  # No proxy for testing
    )
    
    print(f"\n[TEST] Testing with video idea:")
    print(f"  '{test_video_idea}'")
    print(f"\n[TEST] Number of scenes: 3 (reduced for testing)")
    
    # Run the complete pipeline
    try:
        result = manager.produce_video(
            video_idea=test_video_idea,
            num_scenes=3  # Use fewer scenes for faster testing
        )
        
        # Print final result
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Status: {result['status']}")
        print(f"Project ID: {result['project_id']}")
        
        if result['status'] == 'completed':
            print("\n✅ TEST PASSED - All phases completed successfully!")
        else:
            print("\n❌ TEST FAILED - Pipeline did not complete")
            if result.get('errors'):
                print("\nErrors encountered:")
                for error in result['errors']:
                    print(f"  - {error}")
        
        print("\nGenerated outputs:")
        print(f"  - Scripts: {result['script'] is not None}")
        print(f"  - Images: {len([i for i in result.get('images', []) if i.get('status') == 'success'])}/{len(result.get('images', []))}")
        print(f"  - Videos: {len([v for v in result.get('videos', []) if v.get('status') == 'success'])}/{len(result.get('videos', []))}")
        print(f"  - Thumbnails: {len(result.get('thumbnails', []))}")
        print(f"  - Duration: {result.get('duration_seconds', 0):.1f} seconds")
        
        print("\n" + "="*80)
        
        return result['status'] == 'completed'
        
    except Exception as e:
        print(f"\n❌ TEST FAILED - Exception occurred:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_character_video_manager()
    sys.exit(0 if success else 1)
