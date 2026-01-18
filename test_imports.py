#!/usr/bin/env python3
"""Debug script to test imports one by one"""

import sys
print("[1/10] Testing basic imports...")
try:
    import os
    import json
    import time
    print("✅ Basic Python imports work")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    sys.exit(1)

print("\n[2/10] Testing flowchart.common.trend_finder...")
try:
    from flowchart.common.trend_finder import TrendFinder
    print("✅ TrendFinder imported successfully")
except Exception as e:
    print(f"❌ TrendFinder import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[3/10] Testing flowchart.character.script_generator...")
try:
    from flowchart.character.script_generator import ScriptGenerator
    print("✅ ScriptGenerator imported successfully")
except Exception as e:
    print(f"❌ ScriptGenerator import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[4/10] Testing flowchart.character.character_orchestrator...")
try:
    from flowchart.character.character_orchestrator import WorkflowOrchestrator
    print("✅ WorkflowOrchestrator imported successfully")
except Exception as e:
    print(f"❌ WorkflowOrchestrator import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[5/10] Creating WorkflowOrchestrator instance...")
try:
    orchestrator = WorkflowOrchestrator(
        num_image_workers=2,
        num_video_workers=4,
        use_rag=False,use_multi_models=True,
        use_ai_editor=True,
        output_dir="output"
    )
    print("✅ WorkflowOrchestrator instance created")
except Exception as e:
    print(f"❌ WorkflowOrchestrator initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ ALL IMPORT TESTS PASSED!")
print("The module structure is working correctly.")
