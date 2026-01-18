#!/usr/bin/env python3
"""
Full Character Pipeline Test

Tests the complete 8-step character video generation workflow:
1. Trend Finder
2. Video Idea Generation
3. Script Generation
4. Image Generation (2 parallel workers)
5. Video Generation (4 parallel workers)
6. Thumbnail Generation
7. Video Editing
8. Platform Upload

Usage:
    python test_character_full.py --niche "luxury travel" --duration 56 --scenes 7
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flowchart.character.character_orchestrator import WorkflowOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Test Full Character Video Pipeline")
    parser.add_argument("--niche", type=str, default=None, help="Video niche (e.g., 'luxury travel')")
    parser.add_argument("--duration", type=int, default=56, help="Video duration in seconds (default: 56)")
    parser.add_argument("--scenes", type=int, default=7, help="Number of scenes (default: 7)")
    parser.add_argument("--skip-upload", action="store_true", default=True, help="Skip upload step (default: True)")
    parser.add_argument("--num-image-workers", type=int, default=2, help="Image generation workers (default: 2)")
    parser.add_argument("--num-video-workers", type=int, default=4, help="Video generation workers (default: 4)")
    parser.add_argument("--output-dir", type=str, default="output_character_test", help="Output directory")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("  CHARACTER VIDEO PIPELINE - FULL TEST")
    print("="*80)
    print(f"\n📋 Configuration:")
    print(f"   Niche: {args.niche or 'Auto-detect'}")
    print(f"   Duration: {args.duration}s")
    print(f"   Scenes: {args.scenes}")
    print(f"   Image Workers: {args.num_image_workers}")
    print(f"   Video Workers: {args.num_video_workers}")
    print(f"   Output: {args.output_dir}")
    print(f"   Skip Upload: {args.skip_upload}")
    print("\n" + "-"*80)
    
    # Initialize orchestrator
    print("\n🔧 Initializing WorkflowOrchestrator...")
    try:
        orchestrator = WorkflowOrchestrator(
            num_image_workers=args.num_image_workers,
            num_video_workers=args.num_video_workers,
            use_rag=True,
            use_multi_models=True,
            use_ai_editor=True,
            output_dir=args.output_dir
        )
        print("✓ Orchestrator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize orchestrator: {e}")
        return 1
    
    # Start timer
    start_time = time.time()
    
    try:
        print("\n" + "="*80)
        print("  STARTING 8-STEP WORKFLOW")
        print("="*80)
        
        # Step 0: Gmail Authentication
        print("\n📧 STEP 0: Gmail Authentication")
        result = orchestrator.step_0_gmail_authentication()
        if not result:
            print("⚠️  Gmail auth failed, but continuing (optional step)")
        
        # Step 1: Trend Finder
        print("\n🔍 STEP 1: Trend Finder")
        trend = orchestrator.step_1_trend_finder(niche=args.niche)
        print(f"   Selected: {trend.get('niche', 'Unknown')}")
        
        # Step 2: Video Idea
        print("\n💡 STEP 2: Video Idea Generation")
        video_idea = orchestrator.step_2_find_video_idea(trend)
        print(f"   Idea: {video_idea.get('idea', 'N/A')[:80]}...")
        
        # Step 3: Script Generation
        print("\n📝 STEP 3: Script Generation")
        script = orchestrator.step_3_generate_script(
            video_idea,
            duration=args.duration,
            num_scenes=args.scenes
        )
        print(f"   Title: {script.get('title', 'N/A')}")
        print(f"   Scenes: {len(script.get('scenes', []))}")
        print(f"   Characters: {len(script.get('characters', []))}")
        
        # Step 4: Image Generation (2 workers)
        print(f"\n🎨 STEP 4: Image Generation ({args.num_image_workers} parallel workers)")
        reference_images = orchestrator.step_4_image_generation(script)
        print(f"   Generated: {len(reference_images)} images")
        
        # Step 5: Video Generation (4 workers)
        print(f"\n🎬 STEP 5: Video Generation ({args.num_video_workers} parallel workers)")
        video_clips = orchestrator.step_5_video_generation(script, reference_images)
        print(f"   Generated: {len(video_clips)} video clips")
        
        # Step 6: Thumbnail
        print("\n🖼️  STEP 6: Thumbnail Generation")
        thumbnail = orchestrator.step_6_thumbnail_generation(script, video_clips)
        print(f"   Thumbnail: {os.path.basename(thumbnail) if thumbnail else 'Failed'}")
        
        # Step 7: Video Editing
        print("\n✂️  STEP 7: Video Editing")
        final_video = orchestrator.step_7_edit_video(script, video_clips)
        print(f"   Final Video: {os.path.basename(final_video) if final_video else 'Failed'}")
        
        # Step 8: Upload (optional)
        if not args.skip_upload:
            print("\n📤 STEP 8: Platform Upload")
            upload_results = orchestrator.step_8_upload_platforms(
                script,
                final_video,
                thumbnail,
                platforms=['youtube']
            )
            print(f"   Upload Results: {upload_results}")
        else:
            print("\n📤 STEP 8: Upload (SKIPPED)")
        
        # Calculate time
        elapsed = time.time() - start_time
        
        # Final Summary
        print("\n" + "="*80)
        print("  ✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\n⏱️  Total Time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
        print(f"\n📁 Output Location: {os.path.abspath(args.output_dir)}")
        print(f"   - Images: {len(reference_images)}")
        print(f"   - Videos: {len(video_clips)}")
        print(f"   - Final: {os.path.basename(final_video) if final_video else 'N/A'}")
        print(f"   - Thumbnail: {os.path.basename(thumbnail) if thumbnail else 'N/A'}")
        
        # Performance stats
        if len(script.get('scenes', [])) > 0:
            avg_time_per_scene = elapsed / len(script['scenes'])
            print(f"\n📊 Performance:")
            print(f"   - Average per scene: {avg_time_per_scene:.2f}s")
            print(f"   - Image workers: {args.num_image_workers}")
            print(f"   - Video workers: {args.num_video_workers}")
            print(f"   - Parallelism gain: ~{args.num_video_workers}x theoretical")
        
        print("\n" + "="*80)
        print("🎉 All steps completed! Check output directory for results.")
        print("="*80 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        elapsed = time.time() - start_time
        print(f"Ran for {elapsed:.2f}s before interruption")
        return 130
        
    except Exception as e:
        print(f"\n\n❌ PIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        elapsed = time.time() - start_time
        print(f"\nFailed after {elapsed:.2f}s")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
