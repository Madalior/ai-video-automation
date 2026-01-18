#!/usr/bin/env python3
"""
Direct execution of video generator bypassing imports
Reads the file and executes it directly
"""

import os
import sys

# Setup environment
os.chdir(r'c:\Users\vijay\OneDrive\Pictures\automation tool')
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'flowchart'))
sys.path.insert(0, os.path.join(os.getcwd(), 'flowchart', 'character'))
sys.path.insert(0, os.path.join(os.getcwd(), 'flowchart', 'common'))

print("=" * 70)
print("🎥 DIRECT VEO 3.1 VIDEO GENERATOR TEST")
print("=" * 70)
print()

# Read and execute browser_utils first (dependency)
print("[1/3] Loading browser utilities...")
with open('flowchart/common/browser_utils.py', 'r', encoding='utf-8') as f:
    browser_utils_code = f.read()
    # Replace relative import if any
    browser_utils_code = browser_utils_code.replace('from .', 'from flowchart.common.')
    exec(browser_utils_code, globals())
print("✅ Browser utils loaded")

# Read and execute video generator
print("[2/3] Loading video generator...")
with open('flowchart/character/video_generator.py', 'r', encoding='utf-8') as f:
    video_gen_code = f.read()
    # Fix the import at line 10
    video_gen_code = video_gen_code.replace(
        'from flowchart.common.browser_utils import',
        '# Already loaded - '
    )
    exec(video_gen_code, globals())
print("✅ Video generator loaded")

# Load script
print("[3/3] Loading woman vlogging script...")
import json
with open('output/script.json', 'r') as f:
    script = json.load(f)
print(f"✅ Script loaded: {script['title']}")
print()

# Test with Scene 1
scene = script['scenes'][0]
print("=" * 70)
print("TESTING SCENE 1: Video Generation")
print("=" * 70)
print(f"Dialogue: \"{scene['dialogue']}\"")
print(f"Duration: 8 seconds (Veo 3.1)")
print()

# Create generator instance
print("[CREATE] Initializing DreaminaVideoGenerator...")
gen = DreaminaVideoGenerator(
    headless=False,
    profile_path=os.path.abspath("chrome_data_vid_test")
)
print("✅ Generator created")
print()

# Login
print("[LOGIN] Logging in...")
if gen.login():
    print("✅ Login successful!")
    print()
    
    # Build prompt with dialogue
    full_prompt = f"{scene['video_script']} Character says: \"{scene['dialogue']}\""
    print(f"[GENERATE] Creating video...")
    print(f"Prompt: {full_prompt[:100]}...")
    print()
    
    # Generate video
    output_path = "output/videos/scene_1_test.mp4"
    os.makedirs("output/videos", exist_ok=True)
    
    if gen.generate_video(full_prompt, None, output_path):
        print()
        print("=" * 70)
        print("✅ VIDEO GENERATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"📹 Saved to: {output_path}")
        print(f"⏱️  Duration: 8 seconds")
        print(f"🎬 Scene 1 of 7 complete")
        print("=" * 70)
    else:
        print("❌ Video generation failed")
else:
    print("❌ Login failed")

# Cleanup
try:
    gen.close()
except:
    pass

print()
print("Test complete!")
