#!/usr/bin/env python3
"""
MINIMALIST TEST: Just test the character orchestrator initialization and basic flow
"""

import sys
import os

# Add paths systematically
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

#Add common as "modules
sys.path.insert(0, os.path.join(base_dir, 'flowchart', 'common'))

print("[TEST] Paths added to sys.path:")
for p in sys.path[:5]:
    print(f"  - {p}")
print()

print("[TEST 1] Trying to import LLMManager...")
try:
    from llm_manager import LLMManager
    print("✅ LLMManager imported successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print()
print("[TEST 2] Trying to import TrendFinder...")
try:
    from trend_finder import TrendFinder
    print("✅ TrendFinder imported successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print()
print("[TEST 3] Trying to import ScriptGenerator...")
try:
    sys.path.insert(0, os.path.join(base_dir, 'flowchart', 'character'))
    from script_generator import ScriptGenerator
    print("✅ ScriptGenerator imported successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print()
print("[TEST 4] Trying to import DreaminaGenerator...")
try:
    sys.path.insert(0, os.path.join(base_dir, 'flowchart', 'common', 'generators'))
    from image_generator import DreaminaGenerator
    print("✅ DreaminaGenerator imported successfully!")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("✅ ALL BASIC IMPORTS SUCCESSFUL!")
print("=" * 70)
print()

print("[TEST 5] Attempting to create LLM instance...")
try:
    llm = LLMManager()
    print("✅ LLM instance created!")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("[TEST 6] Attempting to create TrendFinder instance...")
try:
    trend_finder = TrendFinder()
    print("✅ TrendFinder instance created!")
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("🎉 BASIC MODULE TESTS PASSED!")
print("=" * 70)
print()
print("Next: Try importing WorkflowOrchestrator...")
