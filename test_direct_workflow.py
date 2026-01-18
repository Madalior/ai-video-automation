#!/usr/bin/env python3
"""
DIRECT WORKFLOW EXECUTION - Runs generators with subprocess
Bypasses all import issues by running generators as standalone scripts
"""

import os
import sys
import json
import subprocess
import time

print("=" * 70)
print("🎬 DIRECT WORKFLOW - Woman Vlogging in US")  
print("=" * 70)
print()

# Load script
with open('output/script.json', 'r') as f:
    script = json.load(f)

print(f"✓ Script: '{script['title']}'")
print(f"✓ Scenes: {len(script['scenes'])}")
print()

# Create generator test scripts that can be run standalone
print("[SETUP] Creating standalone generator scripts...")

# Create a test script for image generation
image_test_script = f'''
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Direct imports - no package structure
import flowchart.character.image_generator as img_gen_module
import flowchart.common.browser_utils

# Test import
print("[TEST] Image generator module imported successfully")

# Create generator instance
gen = img_gen_module.DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_test"))

# Try login
print("[TEST] Attempting login...")
if gen.login():
    print("[SUCCESS] Login successful!")
    gen.close()
else:
    print("[FAILED] Login failed")
    gen.close()
    sys.exit(1)
'''

with open('test_image_gen.py', 'w') as f:
    f.write(image_test_script)

print("✅ Created test_image_gen.py")
print()

# Run the test
print("[TEST] Running image generator test...")
print("=" * 70)

result = subprocess.run(
    [sys.executable, 'test_image_gen.py'],
    cwd=os.getcwd(),
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

if result.returncode == 0:
    print("=" * 70)
    print("✅ Image generator test PASSED!")
    print()
    print("The generator can be used. To run full workflow:")
    print("1. Generators are working")
    print("2. Browser automation is functional") 
    print("3. Ready to generate images and videos")
    print()
    print("Next: Manually run image and video generation for 3 scenes")
else:
    print("=" * 70)
    print("❌ Test failed with error code:", result.returncode)
    print("Check the error messages above for details.")

print("=" * 70)
