#!/usr/bin/env python3
"""
Test Script: Woman Vlogging in US - Character Workflow
Duration: 1 minute (60 seconds)
Scenes: 3 (approximately 20 seconds each)
"""

import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# CRITICAL: Add flowchart/common as 'modules' so character_orchestrator can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowchart', 'common'))
# Allow importing flowchart package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowchart'))

from character.character_orchestrator import WorkflowOrchestrator

def test_woman_vlog():
    """
    Test the complete 8-step character workflow
    with a woman vlogging in the US
    """
    
    print("=" * 70)
    print("🎬 TESTING CHARACTER WORKFLOW")
    print("=" * 70)
    print("Scenario: Woman vlogging in US")
    print("Duration: 60 seconds (1 minute)")
    print("Scenes: 3")
    print("=" * 70)
    print()
    
    # Initialize the orchestrator
    print("[SETUP] Initializing WorkflowOrchestrator...")
    orchestrator = WorkflowOrchestrator(
        num_image_workers=2,    # 2 parallel image workers
        num_video_workers=4,    # 4 parallel video workers
        use_rag=True,           # Use RAG for learning
        use_multi_models=True,  # Use multiple AI models
        use_ai_editor=True,     # Use AI-powered editor
        output_dir="output"
    )
    print("✅ Orchestrator initialized!")
    print()
    
    # Execute the full workflow
    try:
        print("[EXECUTE] Running complete 8-step workflow...")
        print()
        
        result = orchestrator.execute_full_workflow(
            niche="Vlog",                           # Vlogging niche
            idea="Woman vlogging in US",            # Specific video idea
            reference_url=None,                     # No reference URL
            upload_platforms=None,                  # Skip upload for testing
            duration=60,                            # 1 minute
            num_scenes=3                            # 3 scenes
        )
        
        print()
        print("=" * 70)
        print("✅ WORKFLOW COMPLETED!")
        print("=" * 70)
        
        # Display results
        if result.get('success'):
            print("📊 RESULTS:")
            print(f"  Final Video: {result.get('final_video', 'N/A')}")
            print(f"  Thumbnail:   {result.get('thumbnail', 'N/A')}")
            print(f"  Script:      {result.get('script', {}).get('title', 'N/A')}")
            
            if result.get('upload_results'):
                print(f"  Uploads:     {result.get('upload_results')}")
        else:
            print("❌ WORKFLOW FAILED!")
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR OCCURRED!")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 70)
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_woman_vlog()
