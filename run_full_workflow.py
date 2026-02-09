#!/usr/bin/env python3
"""
FULL WORKFLOW EXECUTION: Woman Vlogging in US
Steps 1-8 with browser automation
"""

import os
import sys
import json
import time

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("🎬 FULL WORKFLOW EXECUTION - Woman Vlogging in US")
print("=" * 70)
print()

# Load the script we generated
with open('output/script.json', 'r') as f:
    script = json.load(f)

print(f"✓ Loaded script: '{script['title']}'")
print(f"✓ Scenes: {len(script['scenes'])}")
print(f"✓ Character: {script['characters'][0]}")
print()

# Import generators
print("[IMPORT] Loading generators...")
try:
    from flowchart.character.image_generator import DreaminaGenerator
    from flowchart.character.video_generator import DreaminaVideoGenerator
    print("✅ Generators imported successfully")
except Exception as e:
    print(f"❌ Failed to import generators: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("STEP 4: IMAGE GENERATION")
print("=" * 70)

# Phase 1: Generate character reference
print("\n📸 Phase 1: Character Reference Image")
print(f"   Character: Sarah")
print(f"   Description: {script['character_description']['Sarah']}")

char_ref_path = "output/images/Sarah_reference.png"
img_gen = DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_0"))

try:
    print("\n   [1/1] Logging into Dreamina...")
    if img_gen.login():
        print("   ✅ Login successful")
        
        prompt = f"Generate a photorealistic character portrait of {script['character_description']['Sarah']}. Use cinematic lighting, highly detailed, 8K resolution."
        print(f"\n   [1/1] Generating: Sarah_reference.png")
        print(f"   Prompt: {prompt[:60]}...")
        
        if img_gen.generate_image(prompt, char_ref_path, reference_image=None):
            print(f"   ✅ Generated: {char_ref_path}")
        else:
            print(f"   ❌ Failed to generate character reference")
    else:
        print("   ❌ Login failed")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    img_gen.close()

# Phase 2: Generate scene images
print("\n📸 Phase 2: Scene Images")
scene_images = []

for scene in script['scenes']:
    scene_num = scene['scene_number']
    char_desc = scene.get('character_description', '')
    background = scene.get('background', '')
    
    if char_desc:
        # Character scene image
        char_scene_path = f"output/images/Sarah_scene_{scene_num}.png"
        prompt = f"Generate an image of {char_desc}. Cinematic style, photorealistic, 8K resolution."
        
        print(f"\n   [{scene_num}/3] Generating: Sarah_scene_{scene_num}.png")
        print(f"   Prompt: {prompt[:60]}...")
        
        img_gen = DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_0"))
        try:
            if img_gen.login():
                if img_gen.generate_image(prompt, char_scene_path, reference_image=char_ref_path):
                    print(f"   ✅ Generated: {char_scene_path}")
                    scene_images.append(char_scene_path)
                else:
                    print(f"   ❌ Failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            img_gen.close()
        
        time.sleep(2)  # Brief pause between generations
    
    if background:
        # Background image
        bg_path = f"output/images/background_scene_{scene_num}.png"
        prompt = f"Generate an image of {background}. Cinematic style, detailed environment, photorealistic, 8K resolution."
        
        print(f"\n   [{scene_num}/3] Generating: background_scene_{scene_num}.png")
        print(f"   Prompt: {prompt[:60]}...")
        
        img_gen = DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_0"))
        try:
            if img_gen.login():
                if img_gen.generate_image(prompt, bg_path, reference_image=None):
                    print(f"   ✅ Generated: {bg_path}")
                    scene_images.append(bg_path)
                else:
                    print(f"   ❌ Failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        finally:
            img_gen.close()
        
        time.sleep(2)

print(f"\n✅ Image Generation Complete: {len(scene_images)} images")

print()
print("=" * 70)
print("STEP 5: VIDEO GENERATION")
print("=" * 70)

video_paths = []

for scene in script['scenes']:
    scene_num = scene['scene_number']
    video_script = scene.get('video_script', '')
    output_path = f"output/videos/scene_{scene_num}.mp4"
    
    # Collect reference images for this scene
    ref_images = [char_ref_path]  # Always include character reference
    ref_images.append(f"output/images/Sarah_scene_{scene_num}.png")
    ref_images.append(f"output/images/background_scene_{scene_num}.png")
    
    print(f"\n🎥 [{scene_num}/3] Generating: scene_{scene_num}.mp4")
    print(f"   Script: {video_script[:80]}...")
    print(f"   References: {len(ref_images)} images")
    
    vid_gen = DreaminaVideoGenerator(headless=False, profile_path=os.path.abspath(f"chrome_data_vid_{scene_num % 4}"))
    
    try:
        if vid_gen.login():
            print("   ✅ Logged in")
            
            # Upload reference images
            for ref_img in ref_images:
                if os.path.exists(ref_img):
                    vid_gen.upload_reference(ref_img)
                    print(f"   ✅ Uploaded: {os.path.basename(ref_img)}")
            
            # Generate video
            if vid_gen.generate_video(video_script, None, output_path):
                print(f"   ✅ Generated: {output_path}")
                video_paths.append(output_path)
            else:
                print(f"   ❌ Failed to generate video")
        else:
            print("   ❌ Login failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        vid_gen.close()
    
    time.sleep(5)  # Pause between video generations

print(f"\n✅ Video Generation Complete: {len(video_paths)} videos")

print()
print("=" * 70)
print("STEP 6: THUMBNAIL GENERATION")
print("=" * 70)

thumbnail_path = "output/thumbnails/Woman_vlogging_in_US_thumb.png"
print(f"\n🖼️  Generating thumbnail...")
print(f"   Using first video frame and character reference")

img_gen = DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_0"))
try:
    if img_gen.login():
        prompt = f"Generate a YouTube thumbnail for a video titled '{script['title']}' in the Vlog category. Feature a woman with camera, bold text, vibrant colors, eye-catching composition."
        if img_gen.generate_image(prompt, thumbnail_path):
            print(f"✅ Thumbnail generated: {thumbnail_path}")
        else:
            print(f"❌ Thumbnail generation failed")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    img_gen.close()

print()
print("=" * 70)
print("STEP 7: VIDEO EDITING")
print("=" * 70)

if video_paths:
    print(f"\n✂️  Combining {len(video_paths)} video clips...")
    
    try:
        from flowchart.common.enhanced_editor import EnhancedVideoEditor
        
        editor = EnhancedVideoEditor()
        final_path = "output/final/Woman_vlogging_in_US_final.mp4"
        
        # Combine videos
        result = editor.create_viral_ready_video(
            scene_videos=video_paths,
            title=script['title']
        )
        
        if result.get('video_path'):
            print(f"✅ Final video created: {result['video_path']}")
        else:
            print("❌ Video editing failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  No videos to edit - skipping")

print()
print("=" * 70)
print("✅ WORKFLOW COMPLETE!")
print("=" * 70)
print()
print("📁 Output Files:")
print(f"   Images: output/images/")
print(f"   Videos: output/videos/")
print(f"   Thumbnail: {thumbnail_path}")
print(f"   Final: output/final/")
print()
print("=" * 70)
