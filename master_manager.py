"""
Master Video Automation Manager

Complete video automation workflow orchestrator:
- Character-based videos (storytelling, vlogs, narratives)
- Info-based videos (educational, facts, tutorials)
- Parallel processing for 4-8x speedup
- Veo 3.1 consistency techniques
- Full pipeline: Idea → Script → Media → Edit → Upload

Usage:
    python master_manager.py --type character --idea "Detective mystery" --scenes 5
    python master_manager.py --type info --niche "Space discoveries" --ai-only
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Character pipeline imports
from flowchart.character.character_video_manager import CharacterVideoManager
from flowchart.character.character_orchestrator import CharacterOrchestrator
from flowchart.character.enhanced_script_generator import EnhancedScriptGenerator

# Info pipeline imports
try:
    from flowchart.info.info_orchestrator import InfoContentOrchestrator
    from flowchart.info.parallel_info_director import ParallelInfoDirector
    INFO_AVAILABLE = True
except ImportError:
    INFO_AVAILABLE = False
    print("[WARNING] Info pipeline not available")

# Consistency tools
from flowchart.common.identity_cards import IdentityCardManager
from flowchart.common.frame_controller import FrameController
from flowchart.common.prompt_builder import AnchorDeltaPromptBuilder


class MasterVideoAutomation:
    """
    Master orchestrator for complete video automation.
    
    Features:
    - Dual pipeline support (Character + Info)
    - Parallel processing enabled
    - Veo 3.1 consistency built-in
    - Complete workflow automation
    - Progress tracking and logging
    """
    
    def __init__(self, output_dir: str = "output", headless: bool = False):
        """
        Initialize master automation manager.
        
        Args:
            output_dir: Base output directory
            headless: Run browsers in headless mode
        """
        self.output_dir = output_dir
        self.headless = headless
        
        # Create output structure
        self.dirs = {
            'base': output_dir,
            'character': os.path.join(output_dir, 'character'),
            'info': os.path.join(output_dir, 'info'),
            'logs': os.path.join(output_dir, 'logs'),
            'metadata': os.path.join(output_dir, 'metadata')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Initialize managers
        self.character_manager = None
        self.info_manager = None
        self.frame_controller = FrameController()
        
        print(f"[MASTER] Video Automation Manager initialized")
        print(f"[MASTER] Output: {output_dir}")
    
    def produce_character_video(
        self,
        video_idea: str,
        num_scenes: int = 5,
        use_consistency: bool = True,
        parallel: bool = False
    ) -> Dict:
        """
        Produce character-based video with full automation.
        
        Args:
            video_idea: Story/video concept
            num_scenes: Number of scenes
            use_consistency: Enable Veo 3.1 consistency
            parallel: Use parallel processing
        
        Returns:
            Production result dictionary
        """
        print("\n" + "="*80)
        print("CHARACTER VIDEO PRODUCTION")
        print("="*80)
        print(f"Idea: {video_idea}")
        print(f"Scenes: {num_scenes}")
        print(f"Consistency: {'Enabled (Veo 3.1)' if use_consistency else 'Disabled'}")
        print(f"Processing: {'Parallel' if parallel else 'Sequential'}")
        print("="*80 + "\n")
        
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if parallel:
            # Use CharacterOrchestrator for parallel processing
            print("[MODE] Using Parallel Character Orchestrator")
            
            if not self.character_manager:
                self.character_manager = CharacterOrchestrator(
                    output_base_dir=self.dirs['character'],
                    num_image_workers=2,
                    num_video_workers=4,
                    headless=self.headless
                )
            
            result = self.character_manager.produce_video(
                video_idea=video_idea,
                num_scenes=num_scenes
            )
            
        else:
            # Use CharacterVideoManager for sequential
            print("[MODE] Using Sequential Character Manager")
            
            manager = CharacterVideoManager(
                output_dir=self.dirs['character'],
                headless=self.headless
            )
            
            result = manager.produce_video(
                video_idea=video_idea,
                num_scenes=num_scenes
            )
        
        # Save metadata
        self._save_production_metadata(result, 'character', project_id)
        
        return result
    
    def produce_info_video(
        self,
        niche: str,
        video_mode: str = 'ai',
        num_videos: int = 5,
        parallel: bool = True
    ) -> Dict:
        """
        Produce info/educational video with full automation.
        
        Args:
            niche: Topic/niche for content
            video_mode: 'ai', 'stock', or 'hybrid'
            num_videos: Number of video clips
            parallel: Use parallel processing
        
        Returns:
            Production result dictionary
        """
        if not INFO_AVAILABLE:
            print("[ERROR] Info pipeline not available")
            return {'status': 'error', 'message': 'Info pipeline not installed'}
        
        print("\n" + "="*80)
        print("INFO VIDEO PRODUCTION")
        print("="*80)
        print(f"Niche: {niche}")
        print(f"Mode: {video_mode.upper()}")
        print(f"Videos: {num_videos}")
        print(f"Processing: {'Parallel' if parallel else 'Sequential'}")
        print("="*80 + "\n")
        
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if parallel and video_mode == 'ai':
            # Use ParallelInfoDirector for AI-only mode
            print("[MODE] Using Parallel Info Director")
            
            director = ParallelInfoDirector(
                output_dir=self.dirs['info'],
                num_workers=4
            )
            
            result = director.produce_video(niche=niche)
            
        else:
            # Use standard InfoContentOrchestrator
            print("[MODE] Using Standard Info Orchestrator")
            
            if not self.info_manager:
                self.info_manager = InfoContentOrchestrator(
                    output_dir=self.dirs['info'],
                    video_mode=video_mode,
                    headless=self.headless
                )
            
            result = self.info_manager.produce_content(niche=niche)
        
        # Save metadata
        self._save_production_metadata(result, 'info', project_id)
        
        return result
    
    def batch_produce(
        self,
        batch_config: Dict
    ) -> List[Dict]:
        """
        Batch produce multiple videos.
        
        Args:
            batch_config: Configuration dict with video list
            
        Returns:
            List of production results
        """
        print("\n" + "="*80)
        print("BATCH PRODUCTION MODE")
        print("="*80)
        
        videos = batch_config.get('videos', [])
        print(f"Total videos: {len(videos)}\n")
        
        results = []
        
        for idx, video_config in enumerate(videos, 1):
            print(f"\n[{idx}/{len(videos)}] Processing: {video_config.get('idea', video_config.get('niche'))}")
            
            video_type = video_config.get('type', 'character')
            
            try:
                if video_type == 'character':
                    result = self.produce_character_video(
                        video_idea=video_config['idea'],
                        num_scenes=video_config.get('scenes', 5),
                        use_consistency=video_config.get('consistency', True),
                        parallel=video_config.get('parallel', False)
                    )
                else:
                    result = self.produce_info_video(
                        niche=video_config['niche'],
                        video_mode=video_config.get('mode', 'ai'),
                        num_videos=video_config.get('clips', 5),
                        parallel=video_config.get('parallel', True)
                    )
                
                results.append(result)
                
            except Exception as e:
                print(f"[ERROR] Video {idx} failed: {e}")
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'config': video_config
                })
        
        # Save batch summary
        self._save_batch_summary(results)
        
        return results
    
    def _save_production_metadata(self, result: Dict, pipeline_type: str, project_id: str):
        """Save production metadata to file."""
        metadata_file = os.path.join(
            self.dirs['metadata'],
            f"{pipeline_type}_{project_id}_metadata.json"
        )
        
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n[METADATA] Saved to: {metadata_file}")
        except Exception as e:
            print(f"[WARNING] Could not save metadata: {e}")
    
    def _save_batch_summary(self, results: List[Dict]):
        """Save batch production summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(
            self.dirs['metadata'],
            f"batch_{timestamp}_summary.json"
        )
        
        summary = {
            'timestamp': timestamp,
            'total_videos': len(results),
            'successful': sum(1 for r in results if r.get('status') == 'completed'),
            'failed': sum(1 for r in results if r.get('status') == 'failed'),
            'results': results
        }
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n[BATCH SUMMARY] Saved to: {summary_file}")
        except Exception as e:
            print(f"[WARNING] Could not save batch summary: {e}")
    
    def print_summary(self):
        """Print system capabilities summary."""
        print("\n" + "="*80)
        print("VIDEO AUTOMATION SYSTEM - CAPABILITIES")
        print("="*80)
        
        print("\n[CHARACTER PIPELINE]")
        print("  ✓ Story-based videos")
        print("  ✓ Character consistency (Veo 3.1)")
        print("  ✓ Parallel processing (2-8x faster)")
        print("  ✓ Identity cards + Multi-reference")
        
        if INFO_AVAILABLE:
            print("\n[INFO PIPELINE]")
            print("  ✓ Educational videos")
            print("  ✓ AI + Stock footage")
            print("  ✓ Parallel generation (4x faster)")
        
        print("\n[FEATURES]")
        print("  ✓ Automated scripting (LLM)")
        print("  ✓ AI image generation (Dreamina)")
        print("  ✓ AI video generation (Veo 3.1)")
        print("  ✓ Thumbnail creation")
        print("  ✓ Batch processing")
        
        print("\n[OUTPUT]")
        print(f"  Base: {self.output_dir}")
        print(f"  Character: {self.dirs['character']}")
        print(f"  Info: {self.dirs['info']}")
        print(f"  Logs: {self.dirs['logs']}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Command-line interface for master automation."""
    parser = argparse.ArgumentParser(
        description="Master Video Automation Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Character video with consistency
  python master_manager.py --type character --idea "Detective solves mystery" --scenes 5
  
  # Info video with parallel AI
  python master_manager.py --type info --niche "Space discoveries" --mode ai --parallel
  
  # Batch production
  python master_manager.py --batch batch_config.json
  
  # Show capabilities
  python master_manager.py --summary
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['character', 'info'],
        help='Pipeline type'
    )
    
    parser.add_argument(
        '--idea',
        type=str,
        help='Video idea (for character videos)'
    )
    
    parser.add_argument(
        '--niche',
        type=str,
        help='Content niche (for info videos)'
    )
    
    parser.add_argument(
        '--scenes',
        type=int,
        default=5,
        help='Number of scenes (character) or clips (info)'
    )
    
    parser.add_argument(
        '--mode',
        choices=['ai', 'stock', 'hybrid'],
        default='ai',
        help='Video mode for info pipeline'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Enable parallel processing'
    )
    
    parser.add_argument(
        '--consistency',
        action='store_true',
        default=True,
        help='Enable Veo 3.1 consistency (character)'
    )
    
    parser.add_argument(
        '--batch',
        type=str,
        help='Batch config JSON file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browsers in headless mode'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show system capabilities'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = MasterVideoAutomation(
        output_dir=args.output,
        headless=args.headless
    )
    
    # Show summary
    if args.summary:
        manager.print_summary()
        return 0
    
    # Batch mode
    if args.batch:
        print(f"[BATCH] Loading config from: {args.batch}")
        with open(args.batch, 'r') as f:
            batch_config = json.load(f)
        
        results = manager.batch_produce(batch_config)
        
        successful = sum(1 for r in results if r.get('status') == 'completed')
        print(f"\n[BATCH COMPLETE] {successful}/{len(results)} successful")
        
        return 0 if successful == len(results) else 1
    
    # Single video mode
    if args.type == 'character':
        if not args.idea:
            print("[ERROR] --idea required for character videos")
            return 1
        
        result = manager.produce_character_video(
            video_idea=args.idea,
            num_scenes=args.scenes,
            use_consistency=args.consistency,
            parallel=args.parallel
        )
        
    elif args.type == 'info':
        if not args.niche:
            print("[ERROR] --niche required for info videos")
            return 1
        
        result = manager.produce_info_video(
            niche=args.niche,
            video_mode=args.mode,
            num_videos=args.scenes,
            parallel=args.parallel
        )
    
    else:
        parser.print_help()
        return 1
    
    # Check result
    if result.get('status') == 'completed':
        print("\n✅ VIDEO PRODUCTION COMPLETE!")
        return 0
    else:
        print("\n❌ VIDEO PRODUCTION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
