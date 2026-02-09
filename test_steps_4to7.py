#!/usr/bin/env python3
"""
TEST STEPS 4-7: Image/Video Generation for Woman Vlogging
Tests browser automation with Veo 3.1 for 8-second clips
"""

import os
import sys
import json
import time

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowchart'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowchart', 'character'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flowchart', 'common'))

print("=" * 70)
print("🎬 TESTING STEPS 4-7: Woman Vlogging in US")
print("=" * 70)
print()

# Load script
print("[LOAD] Loading script...")
with open('output/script.json', 'r') as f:
    script = json.load(f)

print(f"✅ Loaded: {script['title']}")
print(f"   Scenes: {len(script['scenes'])}")
print(f"   Duration: {script['total_duration']}s")
print()

# Test imports first
print("[TEST] Testing imports...")
try:
    # Try direct file imports
    import flowchart.character.image_generator as img_gen_mod
    import flowchart.character.video_generator as vid_gen_mod
    print("✅ Generators imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    print()
    print("Import error - trying alternative approach...")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("STEP 4: IMAGE GENERATION TEST")
print("=" * 70)
print()

# Test with just Scene 1 first
scene = script['scenes'][0]
print(f"Testing with Scene {scene['scene_number']}: {scene['dialogue']}")
print()

# Character reference generation
print("📸 [4.1] Generating Character Reference")
print(f"   Character: {script['characters'][0]}")
print(f"   Description: {script['character_description'][script['characters'][0]]}")
print()

char_ref_path = "output/images/Sarah_reference.png"
os.makedirs("output/images", exist_ok=True)

try:
    print("   Starting DreaminaGenerator (browser will open)...")
    gen = img_gen_mod.DreaminaGenerator(
        headless=False, 
        profile_path=os.path.abspath("chrome_data_img_test")
    )
    
    print("   [LOGIN] Attempting login...")
    if gen.login():
        print("   ✅ Login successful!")
        
        # Generate reference image
        prompt = f"Generate a photorealistic character portrait of {script['character_description'][script['characters'][0]]}. Professional photography style, highly detailed, 8K resolution."
        print(f"   [GENERATE] Prompt: {prompt[:60]}...")
        
        if gen.generate_image(prompt, char_ref_path):
            print(f"   ✅ Reference image saved: {char_ref_path}")
        else:
            print(f"   ❌ Generation failed")
    else:
        print("   ❌ Login failed")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        gen.close()
        print("   Browser closed")
    except:
        pass

print()
print("📸 [4.2] Generating Scene 1 Image")
print(f"   Scene: {scene['character_description']}")
print(f"   Background: {scene['background']}")
print()

scene_img_path = f"output/images/Sarah_scene_1.png"

try:
    gen = img_gen_mod.DreaminaGenerator(
        headless=False,
        profile_path=os.path.abspath("chrome_data_img_test")
    )
    
    if gen.login():
        # Use reference image
        prompt = f"Generate an image of {scene['character_description']} with {scene['background']}. Cinematic style, photorealistic, 8K resolution."
        print(f"   [GENERATE] Prompt: {prompt[:60]}...")
        
        if gen.generate_image(prompt, scene_img_path, reference_image=char_ref_path):
            print(f"   ✅ Scene image saved: {scene_img_path}")
        else:
            print(f"   ❌ Generation failed")
    else:
        print("   ❌ Login failed")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        gen.close()
    except:
        pass

print()
print("=" * 70)
print("STEP 5: VIDEO GENERATION TEST (Veo 3.1)")
print("=" * 70)
print()

print("🎥 [5.1] Generating Scene 1 Video (8 seconds)")
print(f"   Dialogue: \"{scene['dialogue']}\"")
print(f"   Script: {scene['video_script'][:60]}...")
print()

video_path = "output/videos/scene_1.mp4"
os.makedirs("output/videos", exist_ok=True)

try:
    print("   Starting DreaminaVideoGenerator...")
    vid_gen = vid_gen_mod.DreaminaVideoGenerator(
        headless=False,
        profile_path=os.path.abspath("chrome_data_vid_test")
    )
    
    if vid_gen.login():
        print("   ✅ Login successful!")
        
        # Upload reference images
        if os.path.exists(char_ref_path):
            print(f"   [UPLOAD] Reference: {os.path.basename(char_ref_path)}")
            vid_gen.upload_reference(char_ref_path)
        
        if os.path.exists(scene_img_path):
            print(f"   [UPLOAD] Scene: {os.path.basename(scene_img_path)}")
            vid_gen.upload_reference(scene_img_path)
        
        # Generate video with dialogue
        full_prompt = f"{scene['video_script']}. Dialogue: \"{scene['dialogue']}\""
        print(f"   [GENERATE] Creating 8-second video...")
        print(f"   Prompt: {full_prompt[:80]}...")
        
        if vid_gen.generate_video(full_prompt, None, video_path):
            print(f"   ✅ Video saved: {video_path}")
        else:
            print(f"   ❌ Video generation failed")
    else:
        print("   ❌ Login failed")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        vid_gen.close()
    except:
        pass

print()
print("=" * 70)
print("STEP 6: THUMBNAIL TEST")
print("=" * 70)
print()

print("🖼️  [6.1] Generating Thumbnail")
thumbnail_path = "output/thumbnails/Woman_vlogging_thumb.png"
os.makedirs("output/thumbnails", exist_ok=True)

try:
    gen = img_gen_mod.DreaminaGenerator(
        headless=False,
        profile_path=os.path.abspath("chrome_data_img_test")
    )
    
    if gen.login():
        prompt = f"Generate a YouTube thumbnail for a video titled '{script['title']}'. Feature a woman vlogger with vibrant colors, bold text overlay, and an eye-catching composition."
        print(f"   [GENERATE] Prompt: {prompt[:60]}...")
        
        if gen.generate_image(prompt, thumbnail_path):
            print(f"   ✅ Thumbnail saved: {thumbnail_path}")
        else:
            print(f"   ❌ Generation failed")
    else:
        print("   ❌ Login failed")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
finally:
    try:
        gen.close()
    except:
        pass

print()
print("=" * 70)
print("STEP 7: VIDEO EDITING (PREVIEW)")
print("=" * 70)
print()

print("✂️  [7.1] Video Editing Status")
if os.path.exists(video_path):
    print(f"   ✅ Scene 1 video ready: {video_path}")
    print(f"   ℹ️  For full editing, generate all 7 scenes first")
    print(f"   ℹ️  Then combine with EnhancedVideoEditor")
else:
    print(f"   ⏸️  No video file to edit yet")

print()
print("=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)
print()

print("📊 Results:")
print(f"   Script: ✅ Loaded")
print(f"   Reference Image: {'✅' if os.path.exists(char_ref_path) else '⏸️'} {char_ref_path}")
print(f"   Scene Image: {'✅' if os.path.exists(scene_img_path) else '⏸️'} {scene_img_path}")
print(f"   Scene Video: {'✅' if os.path.exists(video_path) else '⏸️'} {video_path}")
print(f"   Thumbnail: {'✅' if os.path.exists(thumbnail_path) else '⏸️'} {thumbnail_path}")

print()
print("🎯 Next Steps:")
print("   1. If successful, repeat for all 7 scenes")
print("   2. Generate 7 videos @ 8 seconds each")
print("   3. Combine with video editor")
print("=" * 70)
