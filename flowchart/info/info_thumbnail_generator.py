#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              INFO THUMBNAIL GENERATOR                             ║
║                                                                   ║
║  Generates thumbnails for Info/Documentary niches                ║
║  Focus on text, stats, clean design (NO character faces)         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


class InfoThumbnailGenerator:
    """
    Thumbnail generator for INFO/DOCUMENTARY niches.
    
    Key differences from character-based ThumbnailGenerator:
    - No character faces
    - Focus on bold text and statistics
    - Clean, professional design
    - Number-focused (e.g., "10 Facts", "5 Tips")
    """
    
    # Thumbnail style presets
    STYLE_PRESETS = {
        "viral": {
            "colors": "vibrant red and yellow, high contrast",
            "text": "large bold white text with black outline",
            "style": "attention-grabbing, YouTube viral style"
        },
        "professional": {
            "colors": "blue gradient, corporate colors",
            "text": "clean white typography",
            "style": "professional, trustworthy, business"
        },
        "tech": {
            "colors": "dark background with neon accents, purple and blue",
            "text": "futuristic glowing text",
            "style": "modern tech aesthetic, digital"
        },
        "minimal": {
            "colors": "white background, single accent color",
            "text": "bold black typography",
            "style": "clean minimal design"
        },
        "dramatic": {
            "colors": "dark dramatic background, spotlight effect",
            "text": "large white text with dramatic shadow",
            "style": "cinematic, mysterious"
        }
    }
    
    def __init__(self, output_dir: str = "output_info/thumbnails"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Try to import image generator
        self._generator = None
        try:
            from .generators.info_image_generator import InfoImageGenerator
            self._generator_class = InfoImageGenerator
        except ImportError:
            try:
                from modules.generators.info_image_generator import InfoImageGenerator
                self._generator_class = InfoImageGenerator
            except ImportError:
                # Fallback to regular Dreamina
                try:
                    from .generators.image_generator import DreaminaGenerator
                    self._generator_class = DreaminaGenerator
                except:
                    self._generator_class = None
    
    def _get_generator(self):
        """Lazy load generator"""
        if self._generator is None and self._generator_class:
            self._generator = self._generator_class(headless=False)
        return self._generator
    
    def generate_thumbnail(self,
                           title: str,
                           key_number: str = None,
                           style: str = "viral",
                           output_path: str = None) -> Optional[str]:
        """
        Generate a thumbnail for info content.
        
        Args:
            title: Video title or main text
            key_number: Optional number to highlight (e.g., "10", "5")
            style: Style preset (viral, professional, tech, minimal, dramatic)
            output_path: Output file path
        
        Returns:
            Path to generated thumbnail or None
        """
        print(f"[INFO] Generating thumbnail: {title[:50]}...")
        
        preset = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["viral"])
        
        # Build prompt
        prompt_parts = [
            "YouTube thumbnail, 16:9 aspect ratio",
            f"main text: {title[:30]}",
            preset["colors"],
            preset["text"],
            preset["style"],
            "high quality, 4K, no watermarks"
        ]
        
        if key_number:
            prompt_parts.insert(2, f"featuring large number '{key_number}' prominently")
        
        prompt = ", ".join(prompt_parts)
        
        # Generate output path
        if not output_path:
            safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
            output_path = os.path.join(self.output_dir, f"{safe_title}_thumb.png")
        
        gen = self._get_generator()
        if gen:
            try:
                # Handle different generator types
                if hasattr(gen, 'generate_infographic'):
                    # InfoImageGenerator
                    result = gen.generate_infographic(
                        fact=title,
                        output_path=output_path,
                        style="bold"
                    )
                elif hasattr(gen, 'login'):
                    # DreaminaGenerator
                    if gen.login():
                        success = gen.generate_image(prompt, output_path)
                        if success:
                            result = output_path
                        else:
                            result = None
                else:
                    result = None
                
                if result:
                    print(f"   [OK] Thumbnail saved: {os.path.basename(output_path)}")
                    return output_path
                    
            except Exception as e:
                print(f"   [X] Thumbnail generation failed: {e}")
        
        return None
    
    def generate_variants(self,
                          title: str,
                          key_number: str = None,
                          styles: List[str] = None,
                          num_variants: int = 3) -> List[Dict]:
        """
        Generate multiple thumbnail variants.
        
        Args:
            title: Video title
            key_number: Optional number to highlight
            styles: List of styles to use (or auto-select)
            num_variants: Number of variants to generate
        
        Returns:
            List of dicts with 'path' and 'style'
        """
        print(f"\n[INFO] Generating {num_variants} thumbnail variants...")
        
        if not styles:
            styles = list(self.STYLE_PRESETS.keys())[:num_variants]
        
        variants = []
        
        for i, style in enumerate(styles[:num_variants]):
            safe_title = "".join(c if c.isalnum() else "_" for c in title[:20])
            output_path = os.path.join(self.output_dir, f"{safe_title}_{style}_thumb.png")
            
            result = self.generate_thumbnail(
                title=title,
                key_number=key_number,
                style=style,
                output_path=output_path
            )
            
            if result:
                variants.append({
                    'path': result,
                    'style': style,
                    'variant': i + 1
                })
        
        print(f"\n[OK] Generated {len(variants)}/{num_variants} variants")
        return variants
    
    def generate_from_script(self, script: Dict) -> Optional[str]:
        """
        Generate thumbnail from script data.
        
        Args:
            script: Script dict with 'title', 'key_facts', etc.
        
        Returns:
            Path to best thumbnail
        """
        title = script.get('title', 'Video')
        
        # Extract number from title if present
        import re
        numbers = re.findall(r'\d+', title)
        key_number = numbers[0] if numbers else None
        
        # Generate with viral style (best for engagement)
        return self.generate_thumbnail(
            title=title,
            key_number=key_number,
            style="viral"
        )
    
    def close(self):
        """Close the generator"""
        if self._generator and hasattr(self._generator, 'close'):
            self._generator.close()
            self._generator = None


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Info Thumbnail Generator")
    parser.add_argument('--title', type=str, required=True,
                       help='Video title')
    parser.add_argument('--number', type=str, default=None,
                       help='Key number to highlight')
    parser.add_argument('--style', type=str, default="viral",
                       choices=["viral", "professional", "tech", "minimal", "dramatic"],
                       help='Thumbnail style')
    parser.add_argument('--variants', type=int, default=1,
                       help='Number of variants to generate')
    
    args = parser.parse_args()
    
    generator = InfoThumbnailGenerator()
    
    try:
        if args.variants > 1:
            results = generator.generate_variants(
                title=args.title,
                key_number=args.number,
                num_variants=args.variants
            )
            print(f"\nGenerated {len(results)} thumbnails")
        else:
            result = generator.generate_thumbnail(
                title=args.title,
                key_number=args.number,
                style=args.style
            )
            if result:
                print(f"\n[OK] Thumbnail: {result}")
    finally:
        generator.close()
