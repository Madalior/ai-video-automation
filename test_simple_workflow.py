#!/usr/bin/env python3
"""
SIMPLE TEST: Woman Vlogging in US - Character Workflow
Duration: 1 minute (60 seconds)
Scenes: 3 (approximately 20 seconds each)

This test bypasses main.py and directly calls the character workflow.
"""

import sys
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'flowchart'))
sys.path.insert(0, os.path.join(current_dir, 'flowchart', 'common'))
sys.path.insert(0, os.path.join(current_dir, 'flowchart', 'character'))

# Patch the relative imports in modules to work as absolute
import modules
modules.__path__.insert(0, os.path.join(current_dir, 'flowchart', 'common'))

print("=" * 70)
print("🎬 TESTING CHARACTER WORKFLOW - SIMPLIFIED")
print("=" * 70)
print("Scenario: Woman vlogging in US")
print("Duration: 60 seconds (1 minute)")
print("Scenes: 3")
print("=" * 70)
print()

try:
    # Import after path setup
    from character.character_orchestrator import WorkflowOrchestrator
    
    print("[SETUP] Initializing WorkflowOrchestrator...")
    orchestrator = WorkflowOrchestrator(
        num_image_workers=2,    # 2 parallel image workers
        num_video_workers=4,    # 4 parallel video workers
        use_rag=False,          # Disable RAG to avoid dependencies
        use_multi_models=True,  # Use multiple AI models
        use_ai_editor=True,     # Use AI-powered editor
        output_dir="output"
    )
    print("✅ Orchestrator initialized!")
    print()
    
    # Execute the full workflow
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

except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print()
    print("Trying alternative import method...")
    print()
   
    # If WorkflowOrchestrator import fails, we cannot proceed
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print()
    print("=" * 70)
    print("❌ ERROR OCCURRED!")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)
    sys.exit(1)
