"""
Master Video Automation Manager

Complete video automation workflow orchestrator (Based on FLOWCHART.drawio):
- Gmail uploader/verification
- Character-based videos (storytelling, vlogs, narratives)
- Info-based videos (educational, facts, tutorials)
- Niche discovery (URL-based, Auto-trend, Manual input)
- Parallel processing for 4-8x speedup
- Veo 3.1 consistency techniques
- Retention optimization
- AI metadata generation
- Multi-platform uploading
- Full pipeline: Gmail → Niche → Script → Media → Edit → Optimize → Upload

Usage:
    python master_manager.py --type character --idea "Detective mystery" --scenes 5
    python master_manager.py --type info --niche "Space discoveries" --ai-only
    python master_manager.py --type info --niche-mode url --url "https://youtube.com/watch?v=..."
    python master_manager.py --type info --niche-mode auto
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Gmail verification
try:
    from flowchart.common.gmail_verification import GmailVerifier
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("[WARNING] Gmail verification not available")

# Character pipeline imports
from flowchart.character.character_video_manager import CharacterVideoManager
from flowchart.character.character_orchestrator import WorkflowOrchestrator
from flowchart.character.enhanced_script_generator import EnhancedScriptGenerator

# Info pipeline imports
try:
    from flowchart.info.info_orchestrator import InfoContentOrchestrator
    from flowchart.info.parallel_info_director import ParallelInfoDirector
    INFO_AVAILABLE = True
except ImportError:
    INFO_AVAILABLE = False
    print("[WARNING] Info pipeline not available")

# Niche discovery tools
try:
    from flowchart.common.video_url_analyzer import VideoURLAnalyzer
    from flowchart.common.trend_finder import TrendFinder
    from flowchart.common.video_analyzer import VideoAnalyzer
    NICHE_TOOLS_AVAILABLE = True
except ImportError:
    NICHE_TOOLS_AVAILABLE = False
    print("[WARNING] Niche discovery tools not available")

# Optimization and metadata tools
try:
    from flowchart.common.retention_optimizer import RetentionOptimizer
    from flowchart.common.retention_predictor import RetentionPredictor
    from flowchart.common.ai_metadata_generator import AIMetadataGenerator
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    print("[WARNING] Optimization tools not available")

# Upload tools
try:
    from flowchart.common.smart_uploader import SmartUploader
    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False
    print("[WARNING] Smart uploader not available")

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
    
    def __init__(self, output_dir: str = "output", headless: bool = False, use_emotional_ai: bool = True, use_proxy: bool = False, proxy_file: str = "fast_proxies.txt", proxifly_api_key: str = None):
        """
        Initialize master automation manager.
        
        Args:
            output_dir: Base output directory
            headless: Run browsers in headless mode
            use_emotional_ai: Enable emotional script generation (default: True)
            use_proxy: Enable IP rotation with proxies (default: False)
            proxy_file: Path to proxy file (fallback if no API key)
            proxifly_api_key: Proxifly API key for reliable HTTPS proxies
        """
        self.output_dir = output_dir
        self.headless = headless
        self.use_emotional_ai = use_emotional_ai
        self.use_proxy = use_proxy
        
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
        
        # Initialize core managers
        self.character_manager = None
        self.info_manager = None
        self.frame_controller = FrameController()
        
        # Initialize proxy manager with validation
        # Priority: 1) Proxifly API (best), 2) File-based proxies (fallback)
        if use_proxy:
            self.proxifly_manager = None
            self.proxy_manager = None
            
            # Try Proxifly first (reliable HTTPS proxies)
            if proxifly_api_key:
                try:
                    from flowchart.common.proxifly_manager import ProxiflyManager
                    self.proxifly_manager = ProxiflyManager(api_key=proxifly_api_key)
                    print("[PROXIFLY] Using Proxifly API for proxy rotation")
                    
                    # Get and validate a working proxy
                    print("[PROXIFLY] Validating proxy connectivity...")
                    working_proxy = self.proxifly_manager.get_working_proxy(max_attempts=5)
                    if working_proxy:
                        print(f"[PROXIFLY] Validated working proxy: {working_proxy}")
                        self.validated_proxy = working_proxy
                    else:
                        raise RuntimeError(
                            "[PROXIFLY ERROR] No working proxies from API! "
                            "Check your API key or try --no-proxy flag."
                        )
                except ImportError:
                    print("[WARNING] Proxifly manager not available, using file-based proxies")
                    proxifly_api_key = None  # Fall through to file-based
            
            # Fallback to file-based proxies
            if not proxifly_api_key:
                from flowchart.common.proxy_manager import WorkerBatchProxy
                self.proxy_manager = WorkerBatchProxy(
                    proxy_file=proxy_file,
                    image_workers=2,
                    video_workers=4
                )
                total_proxies = self.proxy_manager.get_stats()['total_proxies']
                print(f"[PROXY] Loaded {total_proxies} file-based proxies")
                
                # Validate at least one proxy works before proceeding - STOP if none work
                if total_proxies > 0:
                    print("[PROXY] Validating proxy connectivity...")
                    working_proxy = self._find_working_proxy()
                    if working_proxy:
                        print(f"[PROXY] Validated working proxy: {working_proxy}")
                        self.validated_proxy = working_proxy
                    else:
                        raise RuntimeError(
                            "[PROXY ERROR] No working proxies found! "
                            "Cannot proceed without a working proxy. "
                            "Please use Proxifly API key or --no-proxy flag."
                        )
                else:
                    raise RuntimeError(
                        "[PROXY ERROR] No proxies in file! "
                        "Cannot proceed without proxies. "
                        "Please use Proxifly API key or --no-proxy flag."
                    )
        else:
            self.proxifly_manager = None
            self.proxy_manager = None
            self.validated_proxy = None
        
        # Initialize flowchart tools
        if GMAIL_AVAILABLE:
            self.gmail_verifier = GmailVerifier()
        else:
            self.gmail_verifier = None
            
        if NICHE_TOOLS_AVAILABLE:
            self.video_url_analyzer = VideoURLAnalyzer()
            self.trend_finder = TrendFinder()
            self.video_analyzer = VideoAnalyzer()
        else:
            self.video_url_analyzer = None
            self.trend_finder = None
            self.video_analyzer = None
            
        if OPTIMIZATION_AVAILABLE:
            self.retention_optimizer = RetentionOptimizer()
            self.retention_predictor = RetentionPredictor()
            self.ai_metadata_generator = AIMetadataGenerator()
        else:
            self.retention_optimizer = None
            self.retention_predictor = None
            self.ai_metadata_generator = None
            
        if UPLOADER_AVAILABLE:
            self.smart_uploader = SmartUploader()
        else:
            self.smart_uploader = None
        
        print(f"[MASTER] Video Automation Manager initialized")
        print(f"[MASTER] Output: {output_dir}")
        print(f"[MASTER] Emotional AI: {'YES' if use_emotional_ai else 'NO'}") 
        print(f"[MASTER] IP Rotation: {'YES' if use_proxy else 'NO'}")
        print(f"[MASTER] Gmail: {'YES' if GMAIL_AVAILABLE else 'NO'}")
        print(f"[MASTER] Niche Tools: {'YES' if NICHE_TOOLS_AVAILABLE else 'NO'}")
        print(f"[MASTER] Optimization: {'YES' if OPTIMIZATION_AVAILABLE else 'NO'}")
        print(f"[MASTER] Uploader: {'YES' if UPLOADER_AVAILABLE else 'NO'}")
    
    def _find_working_proxy(self, max_attempts: int = 10) -> Optional[str]:
        """
        Find a working proxy from the proxy list.
        
        Tests proxies against HTTPS sites (Google) since video generation
        requires HTTPS tunnel support.
        
        Args:
            max_attempts: Maximum number of proxies to test
            
        Returns:
            Working proxy URL or None if all failed
        """
        import requests
        
        if not self.proxy_manager:
            return None
        
        # Test against HTTPS site to ensure tunnel works for Google services
        test_urls = [
            'https://www.google.com',  # Primary - must work for Gemini
            'https://httpbin.org/ip',  # Fallback HTTPS test
        ]
        
        for i in range(max_attempts):
            proxy = self.proxy_manager.proxy_manager.get_next_proxy()
            if not proxy:
                break
                
            print(f"  [{i+1}/{max_attempts}] Testing: {proxy}...", end=" ")
            
            # Test against HTTPS endpoints
            works = False
            for test_url in test_urls:
                try:
                    response = requests.get(
                        test_url,
                        proxies={'http': proxy, 'https': proxy},
                        timeout=15,
                        allow_redirects=True
                    )
                    if response.status_code == 200:
                        print(f"OK (HTTPS verified)")
                        return proxy
                except requests.exceptions.Timeout:
                    continue  # Try next URL
                except requests.exceptions.ProxyError:
                    break  # Proxy error, try next proxy
                except requests.exceptions.SSLError:
                    break  # SSL/HTTPS tunnel failed
                except Exception:
                    continue  # Try next URL
            
            # If we get here, proxy failed
            print("FAILED (HTTPS tunnel not supported)")
        
        return None
    
    def validate_proxy(self) -> bool:
        """
        Validate that proxy is working before starting production.
        
        Call this before starting video production to ensure proxy works.
        
        Returns:
            True if proxy works (or proxy disabled), False otherwise
        """
        if not self.use_proxy or not self.proxy_manager:
            print("[PROXY] Proxy rotation disabled, proceeding without proxy")
            return True
        
        print("[PROXY] Validating proxy before production...")
        working = self._find_working_proxy(max_attempts=5)
        
        if working:
            print(f"[PROXY] Proxy validated: {working}")
            self.validated_proxy = working
            return True
        else:
            print("[PROXY ERROR] No working proxy found!")
            return False
    
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
            # Use WorkflowOrchestrator for parallel processing
            print("[MODE] Using Parallel Workflow Orchestrator")
            
            if not self.character_manager:
                self.character_manager = WorkflowOrchestrator(
                    num_image_workers=2,
                    num_video_workers=4,
                    output_dir=self.dirs['character'],
                    proxy_manager=self.proxy_manager
                )
            
            result = self.character_manager.execute_full_workflow(
                niche=video_idea,
                num_scenes=num_scenes
            )
            
        else:
            # Use CharacterVideoManager for sequential
            print("[MODE] Using Sequential Character Manager")
            
            manager = CharacterVideoManager(
                output_dir=self.dirs['character'],
                headless=self.headless,
                proxy_manager=self.proxy_manager
            )
            
            result = manager.produce_video(
                video_idea=video_idea,
                num_scenes=num_scenes
            )
        
        # Save metadata
        self._save_production_metadata(result, 'character', project_id)
        
        return result
    
    def discover_niche_from_url(self, video_url: str) -> str:
        """
        Discover niche from a YouTube video URL (Flowchart path A).
        
        Args:
            video_url: YouTube video URL to analyze
            
        Returns:
            Discovered niche/topic
        """
        print(f"\n[NICHE DISCOVERY] Analyzing URL: {video_url}")
        
        if not self.video_url_analyzer:
            print("[ERROR] Video URL analyzer not available")
            return ""
        
        niche = self.video_url_analyzer.analyze_url(video_url)
        print(f"[NICHE DISCOVERED] {niche}")
        return niche
    
    def discover_niche_auto(self) -> str:
        """
        Automatically discover trending niche (Flowchart path B).
        
        Returns:
            Trending niche/topic
        """
        print("\n[NICHE DISCOVERY] Auto-discovering trending topics...")
        
        if not self.trend_finder:
            print("[ERROR] Trend finder not available")
            return ""
        
        niche = self.trend_finder.find_trending_niche()
        print(f"[TRENDING NICHE] {niche}")
        return niche
    
    def analyze_niche(self, niche: str) -> Dict:
        """
        Analyze a niche for video content ideas.
        
        Args:
            niche: Niche topic to analyze
            
        Returns:
            Analysis results
        """
        print(f"\n[NICHE ANALYSIS] Analyzing: {niche}")
        
        if not self.video_analyzer:
            print("[WARNING] Video analyzer not available, skipping analysis")
            return {'niche': niche}
        
        analysis = self.video_analyzer.analyze(niche)
        print(f"[ANALYSIS COMPLETE] Found {len(analysis.get('ideas', []))} content ideas")
        return analysis
    
    def produce_info_video(
        self,
        niche: Optional[str] = None,
        video_mode: str = 'ai',
        num_videos: int = 5,
        parallel: bool = True,
        niche_mode: str = 'manual',
        video_url: Optional[str] = None
    ) -> Dict:
        """
        Produce info/educational video with full automation.
        
        Args:
            niche: Topic/niche for content (required if niche_mode='manual')
            video_mode: 'ai', 'stock', or 'hybrid'
            num_videos: Number of video clips
            parallel: Use parallel processing
            niche_mode: 'url', 'auto', or 'manual' (flowchart paths A/B/C)
            video_url: YouTube URL (required if niche_mode='url')
        
        Returns:
            Production result dictionary
        """
        if not INFO_AVAILABLE:
            print("[ERROR] Info pipeline not available")
            return {'status': 'error', 'message': 'Info pipeline not installed'}
        
        # Niche discovery based on mode (Flowchart decision point)
        if niche_mode == 'url':
            if not video_url:
                print("[ERROR] video_url required for niche_mode='url'")
                return {'status': 'error', 'message': 'video_url required'}
            niche = self.discover_niche_from_url(video_url)
            if not niche:
                return {'status': 'error', 'message': 'Failed to discover niche from URL'}
                
        elif niche_mode == 'auto':
            niche = self.discover_niche_auto()
            if not niche:
                return {'status': 'error', 'message': 'Failed to auto-discover niche'}
                
        elif niche_mode == 'manual':
            if not niche:
                print("[ERROR] niche required for niche_mode='manual'")
                return {'status': 'error', 'message': 'niche required'}
        
        # Analyze niche (Flowchart: Video analyzer step)
        niche_analysis = self.analyze_niche(niche)
        
        print("\n" + "="*80)
        print("INFO VIDEO PRODUCTION")
        print("="*80)
        print(f"Niche: {niche}")
        print(f"Niche Mode: {niche_mode.upper()}")
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
                num_workers=4,
                proxy_manager=self.proxy_manager
            )
            
            result = director.produce_video(niche=niche)
            
        else:
            # Use standard InfoContentOrchestrator
            print("[MODE] Using Standard Info Orchestrator")
            
            if not self.info_manager:
                self.info_manager = InfoContentOrchestrator(
                    output_dir=self.dirs['info'],
                    video_mode=video_mode,
                    headless=self.headless,
                    proxy_manager=self.proxy_manager
                )
            
            result = self.info_manager.produce_content(niche=niche)
        
        # Post-production steps (Flowchart: Retention → Thumbnail → Metadata → Upload)
        if result.get('status') == 'completed':
            result = self._apply_post_production(result, project_id)
        
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
    
    def _apply_post_production(self, result: Dict, project_id: str) -> Dict:
        """
        Apply post-production steps from flowchart:
        - Retention optimization
        - AI metadata generation
        - Smart uploading
        
        Args:
            result: Production result dictionary
            project_id: Project identifier
            
        Returns:
            Updated result dictionary
        """
        print("\n" + "="*80)
        print("POST-PRODUCTION PIPELINE")
        print("="*80)
        
        video_path = result.get('video_path')
        if not video_path or not os.path.exists(video_path):
            print("[WARNING] Video path not found, skipping post-production")
            return result
        
        # Step 1: Retention Optimization (Flowchart step)
        if self.retention_optimizer and self.retention_predictor:
            print("\n[1/3] Retention Optimization...")
            try:
                # Predict retention
                retention_score = self.retention_predictor.predict(video_path)
                print(f"  Predicted retention: {retention_score:.1%}")
                
                # Optimize if needed
                if retention_score < 0.7:
                    print("  Applying retention optimization...")
                    optimized_path = self.retention_optimizer.optimize(video_path)
                    result['video_path'] = optimized_path
                    result['retention_optimized'] = True
                    print(f"  ✓ Optimized video saved")
                else:
                    print("  ✓ Retention already good, no optimization needed")
                    result['retention_optimized'] = False
                    
                result['retention_score'] = retention_score
            except Exception as e:
                print(f"  [WARNING] Retention optimization failed: {e}")
        else:
            print("[1/3] Retention Optimization - SKIPPED (not available)")
        
        # Step 2: AI Metadata Generation (Flowchart step)
        if self.ai_metadata_generator:
            print("\n[2/3] AI Metadata Generation...")
            try:
                metadata = self.ai_metadata_generator.generate(
                    video_path=result['video_path'],
                    niche=result.get('niche', result.get('video_idea', ''))
                )
                result['ai_metadata'] = metadata
                print(f"  ✓ Title: {metadata.get('title', 'N/A')}")
                print(f"  ✓ Tags: {len(metadata.get('tags', []))} generated")
                print(f"  ✓ Description generated")
            except Exception as e:
                print(f"  [WARNING] Metadata generation failed: {e}")
        else:
            print("[2/3] AI Metadata Generation - SKIPPED (not available)")
        
        # Step 3: Smart Uploader (Flowchart final step)
        if self.smart_uploader:
            print("\n[3/3] Smart Uploader...")
            try:
                upload_result = self.smart_uploader.upload(
                    video_path=result['video_path'],
                    thumbnail_path=result.get('thumbnail_path'),
                    metadata=result.get('ai_metadata', {}),
                    platforms=['youtube']  # Can be extended to TikTok, etc.
                )
                result['upload_result'] = upload_result
                print(f"  ✓ Uploaded to: {', '.join(upload_result.get('platforms', []))}")
            except Exception as e:
                print(f"  [WARNING] Upload failed: {e}")
        else:
            print("[3/3] Smart Uploader - SKIPPED (not available)")
        
        print("\n" + "="*80)
        print("POST-PRODUCTION COMPLETE")
        print("="*80 + "\n")
        
        return result
    
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
        print("VIDEO AUTOMATION SYSTEM - CAPABILITIES (FLOWCHART.drawio)")
        print("="*80)
        
        if GMAIL_AVAILABLE:
            print("\n[GMAIL VERIFICATION]")
            print("  [+] Gmail account verification")
            print("  [+] Multi-platform upload support")
        
        print("\n[CHARACTER PIPELINE]")
        print("  [+] Story-based videos")
        print("  [+] Character consistency (Veo 3.1)")
        print("  [+] Parallel processing (2-8x faster)")
        print("  [+] Identity cards + Multi-reference")
        
        if INFO_AVAILABLE:
            print("\n[INFO PIPELINE]")
            print("  [+] Educational videos")
            print("  [+] AI + Stock footage")
            print("  [+] Parallel generation (4x faster)")
        
        if NICHE_TOOLS_AVAILABLE:
            print("\n[NICHE DISCOVERY]")
            print("  [+] URL-based analysis (YouTube)")
            print("  [+] Auto trend finder")
            print("  [+] Manual niche input")
            print("  [+] Video content analyzer")
        
        print("\n[CORE FEATURES]")
        print("  [+] Automated scripting (LLM)")
        if self.use_emotional_ai:
            print("  [+] Emotional script generation (7 emotion categories)")
            print("  [+] Human-like storytelling & delivery hints")
        print("  [+] AI image generation (Dreamina)")
        print("  [+] AI video generation (Veo 3.1)")
        print("  [+] Thumbnail creation")
        print("  [+] Batch processing")
        
        if OPTIMIZATION_AVAILABLE:
            print("\n[POST-PRODUCTION]")
            print("  [+] Retention optimization")
            print("  [+] Retention prediction")
            print("  [+] AI metadata generation")
        
        if UPLOADER_AVAILABLE:
            print("\n[DISTRIBUTION]")
            print("  [+] Smart uploader (YouTube, TikTok)")
            print("  [+] Auto-metadata")
        
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
  
  # Info video with manual niche
  python master_manager.py --type info --niche "Space discoveries" --mode ai --parallel
  
  # Info video with URL-based niche discovery
  python master_manager.py --type info --niche-mode url --url "https://youtube.com/watch?v=..."
  
  # Info video with auto trend discovery
  python master_manager.py --type info --niche-mode auto --mode ai
  
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
        help='Content niche (for info videos with niche-mode=manual)'
    )
    
    parser.add_argument(
        '--niche-mode',
        choices=['url', 'auto', 'manual'],
        default='manual',
        help='Niche discovery mode: url (analyze YouTube), auto (trending), manual (typed)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='YouTube URL for niche discovery (required if niche-mode=url)'
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
        '--sequential',
        action='store_true',
        help='Use sequential processing (default: parallel)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        default=True,
        help='Use parallel processing (default: True)'
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
        '--no-emotion',
        action='store_true',
        help='Disable emotional script generation'
    )
    
    parser.add_argument(
        '--proxy',
        action='store_true',
        default=True,
        help='Enable IP rotation with proxies (default: True)'
    )
    
    parser.add_argument(
        '--no-proxy',
        action='store_false',
        dest='proxy',
        help='Disable IP rotation'
    )
    
    parser.add_argument(
        '--proxy-file',
        type=str,
        default='fast_proxies.txt',
        help='Path to proxy file (fallback if no API key)'
    )
    
    parser.add_argument(
        '--proxifly-key',
        type=str,
        help='Proxifly API key for reliable HTTPS proxies (recommended)'
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
        headless=args.headless,
        use_emotional_ai=not args.no_emotion,
        use_proxy=args.proxy,
        proxy_file=args.proxy_file,
        proxifly_api_key=getattr(args, 'proxifly_key', None)
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
            parallel=args.parallel and not args.sequential
        )
        
    elif args.type == 'info':
        # Validate niche mode requirements
        if args.niche_mode == 'url' and not args.url:
            print("[ERROR] --url required when using --niche-mode url")
            return 1
        elif args.niche_mode == 'manual' and not args.niche:
            print("[ERROR] --niche required when using --niche-mode manual")
            return 1
        
        result = manager.produce_info_video(
            niche=args.niche,
            video_mode=args.mode,
            num_videos=args.scenes,
            parallel=args.parallel and not args.sequential,
            niche_mode=args.niche_mode,
            video_url=args.url
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
