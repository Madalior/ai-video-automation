#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              INFO IMAGE GENERATOR                                 ║
║                                                                   ║
║  Generates infographics and visual graphics for Info niches      ║
║  NO character portraits - focuses on data visualization          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class InfoImageGenerator:
    """
    Image generator optimized for INFO/DOCUMENTARY niches.
    
    Key differences from character-based DreaminaGenerator:
    - No character reference images
    - Focus on infographics, charts, data visualizations
    - Text overlay generation
    - Clean, professional style
    """
    
    # Style presets for info graphics
    STYLE_PRESETS = {
        "modern": "clean modern design, blue gradient background, white text, minimalist",
        "tech": "futuristic, dark background, neon accents, digital aesthetic",
        "corporate": "professional, clean lines, blue and white, business style",
        "bold": "vibrant colors, large bold text, high contrast, eye-catching",
        "minimal": "white background, simple icons, clean typography"
    }
    
    def __init__(self, headless: bool = False, profile_path: str = None):
        self.headless = headless
        self.profile_path = profile_path or os.path.abspath("chrome_data_info_img")
        self.output_dir = "output_info/graphics"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Try to import Dreamina generator for AI image generation
        self._dreamina = None
        try:
            from .generators.image_generator import DreaminaGenerator
            self._dreamina_class = DreaminaGenerator
        except ImportError:
            try:
                from modules.generators.image_generator import DreaminaGenerator
                self._dreamina_class = DreaminaGenerator
            except ImportError:
                self._dreamina_class = None
                print("[WARNING] Dreamina generator not available")
    
    def _get_generator(self):
        """Lazy load Dreamina generator"""
        if self._dreamina is None and self._dreamina_class:
            self._dreamina = self._dreamina_class(
                headless=self.headless,
                profile_path=self.profile_path
            )
        return self._dreamina
    
    def generate_infographic(self, 
                             fact: str, 
                             output_path: str,
                             style: str = "modern",
                             include_stat: str = None) -> Optional[str]:
        """
        Generate an infographic image for a fact.
        
        Args:
            fact: The fact to visualize
            output_path: Where to save the image
            style: Style preset (modern, tech, corporate, bold, minimal)
            include_stat: Optional statistic to highlight
        
        Returns:
            Path to generated image or None
        """
        print(f"[INFO] Generating infographic: {fact[:50]}...")
        
        style_modifier = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["modern"])
        
        # Build prompt for infographic
        prompt_parts = [
            "Infographic visualization",
            f"showing: {fact[:100]}",
            style_modifier,
            "professional quality, 4K, clear typography",
            "no watermarks, clean design"
        ]
        
        if include_stat:
            prompt_parts.append(f"featuring large number: {include_stat}")
        
        prompt = ", ".join(prompt_parts)
        
        gen = self._get_generator()
        if gen:
            try:
                if gen.login():
                    success = gen.generate_image(prompt, output_path)
                    if success:
                        print(f"   [OK] Saved: {os.path.basename(output_path)}")
                        return output_path
            except Exception as e:
                print(f"   [X] Generation failed: {e}")
        
        return None
    
    def generate_title_card(self,
                            title: str,
                            output_path: str,
                            style: str = "bold") -> Optional[str]:
        """
        Generate a title card image for video intro.
        
        Args:
            title: Video title text
            output_path: Where to save the image
            style: Style preset
        
        Returns:
            Path to generated image or None
        """
        print(f"[INFO] Generating title card: {title}")
        
        style_modifier = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["bold"])
        
        prompt = f"""
        Title card for video, text says "{title[:50]}",
        {style_modifier}, 
        YouTube thumbnail style, 16:9 aspect ratio,
        professional, high quality, no watermarks
        """
        
        gen = self._get_generator()
        if gen:
            try:
                if gen.login():
                    success = gen.generate_image(prompt.strip(), output_path)
                    if success:
                        return output_path
            except Exception as e:
                print(f"   [X] Title card generation failed: {e}")
        
        return None
    
    def generate_scene_graphics(self, 
                                scenes: List[Dict],
                                style: str = "modern") -> Dict[int, str]:
        """
        Generate graphics for multiple scenes.
        
        Args:
            scenes: List of scene dictionaries with 'narration' and 'scene_number'
            style: Style preset to use
        
        Returns:
            Dict mapping scene_number to image path
        """
        print(f"\n[INFO] Generating graphics for {len(scenes)} scenes...")
        
        graphics = {}
        gen = self._get_generator()
        
        if not gen:
            print("   [X] No image generator available")
            return graphics
        
        try:
            if not gen.login():
                print("   [X] Login failed")
                return graphics
            
            for scene in scenes:
                scene_num = scene.get('scene_number', 0)
                narration = scene.get('narration', '')
                text_overlay = scene.get('text_overlay', '')
                
                if not narration:
                    continue
                
                output_path = f"{self.output_dir}/scene_{scene_num}_graphic.png"
                
                result = self.generate_infographic(
                    fact=narration,
                    output_path=output_path,
                    style=style,
                    include_stat=text_overlay
                )
                
                if result:
                    graphics[scene_num] = result
                
                # Small delay between generations
                time.sleep(2)
                
        finally:
            if gen:
                gen.close()
        
        print(f"   [OK] Generated {len(graphics)}/{len(scenes)} graphics")
        return graphics
    
    def close(self):
        """Close the generator"""
        if self._dreamina:
            self._dreamina.close()
            self._dreamina = None


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Info Image Generator")
    parser.add_argument('--fact', type=str, required=True,
                       help='Fact to visualize')
    parser.add_argument('--output', type=str, default="infographic.png",
                       help='Output path')
    parser.add_argument('--style', type=str, default="modern",
                       choices=["modern", "tech", "corporate", "bold", "minimal"],
                       help='Visual style')
    
    args = parser.parse_args()
    
    generator = InfoImageGenerator(headless=False)
    try:
        result = generator.generate_infographic(
            fact=args.fact,
            output_path=args.output,
            style=args.style
        )
        if result:
            print(f"\n[OK] Generated: {result}")
        else:
            print("\n[X] Generation failed")
    finally:
        generator.close()
