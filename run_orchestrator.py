#!/usr/bin/env python3
"""
Run Character Orchestrator for Woman Vlogging
Uses the generated script and executes full workflow
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("🎬 RUNNING CHARACTER ORCHESTRATOR")
print("=" * 70)
print("Workflow: Woman Vlogging in US")
print("Duration: 56 seconds (7 scenes @ 8s each)")
print("=" * 70)
print()

try:
    # Import orchestrator
    print("[IMPORT] Loading WorkflowOrchestrator...")
    from flowchart.character.character_orchestrator import WorkflowOrchestrator
    print("✅ Orchestrator imported successfully")
    print()
    
    # Initialize
    print("[INIT] Creating orchestrator instance...")
    orchestrator = WorkflowOrchestrator(
        num_image_workers=2,    # 2 parallel image workers
        num_video_workers=4,    # 4 parallel video workers (Veo 3.1)
        use_rag=False,          # Disable RAG to avoid dependencies
        use_multi_models=True,  # Use multiple AI models
        use_ai_editor=True,     # Use AI-powered editor
        output_dir="output"
    )
    print("✅ Orchestrator initialized")
    print()
    
    # Execute workflow
    print("[EXECUTE] Starting full 8-step workflow...")
    print()
    
    result = orchestrator.execute_full_workflow(
        niche="Vlog",                           # Vlogging niche
        idea="Woman vlogging in US",            # Video idea
        reference_url=None,                     # No reference URL
        upload_platforms=None,                  # Skip upload for testing
        duration=56,                            # 56 seconds (7 scenes @ 8s)
        num_scenes=7                            # 7 scenes
    )
    
    print()
    print("=" * 70)
    print("✅ WORKFLOW COMPLETED!")
    print("=" * 70)
    print()
    
    # Display results
    if result.get('success'):
        print("📊 RESULTS:")
        print(f"  ✅ Success: {result.get('success')}")
        print(f"  📹 Final Video: {result.get('final_video', 'N/A')}")
        print(f"  🖼️  Thumbnail: {result.get('thumbnail', 'N/A')}")
        print(f"  📝 Script Title: {result.get('script', {}).get('title', 'N/A')}")
        
        if result.get('upload_results'):
            print(f"  📤 Uploads: {result.get('upload_results')}")
    else:
        print("❌ WORKFLOW FAILED!")
        print(f"  Error: {result.get('error', 'Unknown error')}")
    
    print("=" * 70)

except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print()
    print("The import chain still has issues.")
    print("Recommendation: Use manual generation with the web interface")
    print("All prompts are ready in output/script.json")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print()
    print("=" * 70)
    print("❌ ERROR OCCURRED!")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 70)
