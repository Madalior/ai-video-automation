"""
Test script for Character Video Manager

This demonstrates the complete character-based video production pipeline:
1. Script Generation
2. Image Generation (Character References)
3. Video Generation
4. Thumbnail Generation
"""

from flowchart.character.character_video_manager import CharacterVideoManager
import os

def test_character_video_production():
    """
    Test the complete character video production pipeline.
    """
    print("\n" + "="*80)
    print("CHARACTER VIDEO MANAGER - TEST")
    print("="*80 + "\n")
    
    # Initialize manager
    manager = CharacterVideoManager(
        output_dir="output/character_videos",
        headless=False  # Set to True for automation, False to see browser
    )
    
    # Test video ideas (choose one)
    video_ideas = [
        "The Lost City of Atlantis",
        "A Day in the Life of a Robot Chef",
        "Journey to the Center of the Earth",
        "The Secret Life of House Cats",
        "Time Traveler's First Day in 3024"
    ]
    
    # Select video idea
    selected_idea = video_ideas[0]  # Change index to test different ideas
    
    print(f"Testing with idea: '{selected_idea}'")
    print(f"Number of scenes: 6 (optimized for 8-second Veo 3.1 clips)")
    print()
    
    # Run the complete pipeline
    result = manager.produce_video(
        video_idea=selected_idea,
        num_scenes=6  # Each scene is 8 seconds for Veo 3.1
    )
    
    # Display results
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    if result['status'] == 'completed':
        print("[SUCCESS] Video production completed!")
        
        print(f"\n📁 Output Location: {manager.output_dir}")
        print(f"\n📄 Script File:")
        if result.get('script'):
            script_file = os.path.join(manager.dirs['scripts'], f"{result['project_id']}_script.json")
            print(f"   {script_file}")
        
        print(f"\n🖼️  Images Generated: {len([i for i in result['images'] if i.get('status') == 'success'])}")
        for img in result['images']:
            if img.get('status') == 'success':
                print(f"   ✓ Scene {img['scene_number']}: {img['image_path']}")
            else:
                print(f"   ✗ Scene {img['scene_number']}: Failed")
        
        print(f"\n🎬 Videos Generated: {len([v for v in result['videos'] if v.get('status') == 'success'])}")
        for vid in result['videos']:
            if vid.get('status') == 'success':
                print(f"   ✓ Scene {vid['scene_number']}: {vid['video_path']}")
            else:
                print(f"   ✗ Scene {vid['scene_number']}: Failed")
        
        print(f"\n🖼️  Thumbnails Generated: {len(result['thumbnails'])}")
        for thumb in result['thumbnails']:
            print(f"   ✓ {thumb}")
        
    else:
        print("[FAILED] Video production encountered errors")
        if result.get('errors'):
            print("\nErrors:")
            for error in result['errors']:
                print(f"   - {error}")
    
    print("\n" + "="*80 + "\n")
    
    return result


def test_minimal_script_only():
    """
    Test only the script generation phase (no browser automation needed).
    """
    print("\n" + "="*80)
    print("MINIMAL TEST - Script Generation Only")
    print("="*80 + "\n")
    
    manager = CharacterVideoManager(output_dir="output/test_minimal")
    
    # Test just script generation
    script_result = manager._generate_script(
        video_idea="A Robot's Day at School",
        num_scenes=4,
        project_id="test_001"
    )
    
    print("\n[SCRIPT OVERVIEW]")
    print(f"Title: {script_result['overview'].get('title')}")
    print(f"Synopsis: {script_result['overview'].get('synopsis')}")
    print(f"Characters: {script_result['overview'].get('characters')}")
    
    print(f"\n[SCENES] ({len(script_result['scenes'])} scenes)")
    for scene in script_result['scenes']:
        print(f"\nScene {scene['scene_number']}:")
        print(f"  Character: {scene.get('character_name')}")
        print(f"  Dialogue: {scene.get('dialogue')}")
        print(f"  Video Script: {scene.get('video_script')[:100]}...")
    
    return script_result


if __name__ == "__main__":
    # Run the test
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--minimal":
        # Run minimal test (script generation only)
        result = test_minimal_script_only()
    else:
        # Run full pipeline test
        print("\n💡 TIP: Run with '--minimal' flag to test script generation only (no browser)")
        print("   Example: python test_character_video_manager.py --minimal\n")
        
        result = test_character_video_production()
