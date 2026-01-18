"""
Example: Using Genkit AI Service with Character Video Pipeline

This example shows how to integrate Genkit features into your character-based
video generation workflow.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.genkit_client import genkit
import logging

logging.basicConfig(level=logging.INFO)

# Example video script
script = """
A luxury travel vlog showcasing exclusive destinations.
Scene 1: Woman arriving at 5-star resort
Scene 2: Touring the presidential suite
Scene 3: Private beach access
Scene 4: Fine dining experience
Scene 5: Spa and wellness center
Scene 6: Rooftop infinity pool
Scene 7: Sunset champagne toast
"""

# Example scenes (from your character orchestrator)
scenes = [
    {
        "duration": 8,
        "narration": "Welcome to paradise at the most exclusive resort in the Maldives",
        "visual_description": "Woman arriving at luxury resort entrance",
        "keywords": ["luxury", "resort", "arrival"]
    },
    {
        "duration": 8,
        "narration": "Step inside the presidential suite where luxury meets elegance",
        "visual_description": "Woman in presidential suite with ocean view",
        "keywords": ["suite", "luxury", "interior"]
    },
    # ... more scenes
]

def main():
    print("=" * 60)
    print("Genkit AI Service Integration Example")
    print("=" * 60)
    
    # 1. Validate content before production
    print("\n[1/5] Validating content...")
    validation = genkit.validate_content(
        script=script,
        scenes=scenes,
        duration=56
    )
    
    if validation:
        if validation['is_valid']:
            print("✓ Content validation passed!")
        else:
            print(f"⚠ Issues found: {validation['summary']}")
            for issue in validation['issues']:
                print(f"  - Scene {issue['scene_index']}: {issue['message']}")
                if issue.get('auto_fix'):
                    print(f"    Fix: {issue['auto_fix']}")
    
    # 2. Enhance prompts for better image quality
    print("\n[2/5] Enhancing image prompts...")
    basic_prompt = "woman at luxury resort entrance"
    
    enhanced = genkit.enhance_prompt(
        prompt=basic_prompt,
        style="cinematic",
        character_context="25yo woman, long brown hair, elegant style"
    )
    
    if enhanced:
        print(f"✓ Original: {basic_prompt}")
        print(f"✓ Enhanced: {enhanced['enhanced_prompt'][:150]}...")
        print(f"✓ Improvements: {len(enhanced['improvements'])} made")
    
    # 3. Optimize SEO for upload
    print("\n[3/5] Generating SEO metadata...")
    seo = genkit.optimize_seo(
        script=script,
        niche="luxury travel",
        target_audience="affluent millennials",
        duration=56
    )
    
    if seo:
        print(f"✓ Title: {seo['title']}")
        print(f"✓ Tags: {', '.join(seo['tags'][:8])}...")
        print(f"✓ Thumbnail: {seo['thumbnail_text']}")
    
    # 4. Simulate error and get recovery strategy
    print("\n[4/5] Testing error recovery...")
    recovery = genkit.recover_error(
        error="Timeout: Request took too long",
        context={
            "service": "dreamina",
            "scene_index": 2,
            "attempt": 1,
            "prompt": "luxury resort presidential suite with ocean view at sunset"
        }
    )
    
    if recovery:
        print(f"✓ Analysis: {recovery['analysis']}")
        print("✓ Recovery strategies:")
        for i, strategy in enumerate(recovery['strategies'], 1):
            print(f"  {i}. {strategy}")
    
    # 5. Discover related niches
    print("\n[5/5] Discovering trending niches...")
    niches = genkit.discover_niches(
        category="travel",
        competition_level="medium",
        monetization_potential="high"
    )
    
    if niches:
        print(f"✓ Found {len(niches['trending_niches'])} trending niches:")
        for niche in niches['trending_niches'][:3]:
            print(f"\n  {niche['name']} (Score: {niche['trend_score']}/10)")
            print(f"  → {niche['why_trending']}")
            print(f"  → CPM: {niche['estimated_cpm']}")
            print(f"  → Ideas: {', '.join(niche['content_ideas'][:2])}")
    
    print("\n" + "=" * 60)
    print("Example completed! All features tested successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
