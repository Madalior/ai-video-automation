#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          AI VIDEO AUTOMATION STUDIO - UNIFIED MAIN FILE          ║
║                                                                  ║
║  All-in-One Entry Point for Complete Video Generation Pipeline  ║
╚══════════════════════════════════════════════════════════════════╝

Author: Vijay
Description: Unified interface combining ParallelDirector, 
             Autonomous Studio, and Dashboard integration

Usage:
    python main.py                          # Interactive mode
    python main.py --quick                  # Quick single video
    python main.py --auto                   # Autonomous scheduling
    python main.py --dashboard              # Start web dashboard
    python main.py --niche ASMR --title "My Video"  # Custom video
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════════
# IMPORT CORE MODULES
# ═══════════════════════════════════════════════════════════════════

# Use the actual WorkflowOrchestrator from flowchart.character
from flowchart.character.character_orchestrator import WorkflowOrchestrator
from flowchart.common.trend_finder import TrendFinder
from flowchart.character.script_generator import ScriptGenerator
from flowchart.common.stock_media import StockMediaFetcher
from flowchart.common.enhanced_editor import EnhancedVideoEditor
from flowchart.common.ai_metadata_generator import AIMetadataGenerator

# Optional modules
try:
    from flowchart.common.video_rag import VideoKnowledgeBase
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("[INFO] RAG module not available")

try:
    from flowchart.common.smart_uploader import SmartUploader
    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False
    print("[INFO] Smart uploader not available")

try:
    from flowchart.common.gmail_verification import GmailVerificationTool
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("[INFO] Gmail verification not available")


# ═══════════════════════════════════════════════════════════════════
# URL REFERENCES - External Services
# ═══════════════════════════════════════════════════════════════════

URL_REFERENCES = {
    'dreamina_auth': 'https://auth.business.gemini.google/login?continueUrl=https://business.gemini.google/',
    'dreamina_base': 'https://business.gemini.google/',
    'veo3_auth': 'https://auth.business.gemini.google/login',
    'tempmail_api': 'https://api.mail.tm',
    'gmail_api': 'https://www.googleapis.com/auth/gmail.modify',
    'google_cloud': 'https://console.cloud.google.com/',
    'pexels_api': 'https://api.pexels.com/v1/',
    'youtube_api': 'https://www.googleapis.com/youtube/v3/',
    'tiktok_api': 'https://open-api.tiktok.com/',
    'dreamina_verify_sender': 'noreply@dreamina.com',
}

# ═══════════════════════════════════════════════════════════════════
# UNIFIED VIDEO AUTOMATION STUDIO
# ═══════════════════════════════════════════════════════════════════

class UnifiedVideoStudio:
    """
    Unified interface for all video generation capabilities
    """
    
    def __init__(self, config_file='studio_config.json'):
        self.config_file = config_file
        self.config = self.load_or_create_config()
        
        # Initialize output directories
        self.ensure_directories()
        
        # Initialize Gmail verification if available
        self.gmail = None
        if GMAIL_AVAILABLE and self.config.get('use_gmail_verification', False):
            try:
                self.gmail = GmailVerificationTool()
                print("[INFO] Gmail verification initialized")
            except Exception as e:
               print(f"[WARNING] Gmail initialization failed: {e}")
        
        # Initialize uploader if available
        self.uploader = None
        if UPLOADER_AVAILABLE and self.config.get('enable_uploads', False):
            try:
                self.uploader = SmartUploader()
                print("[INFO] Smart uploader initialized")
            except Exception as e:
                print(f"[WARNING] Uploader initialization failed: {e}")
        
        # Statistics
        self.stats = {
            'total_videos': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'avg_retention': 0
        }
    
    def ensure_directories(self):
        """Create all necessary output directories"""
        dirs = [
            'output/images',
            'output/videos',
            'output/final',
            'output/thumbnails',
            'chrome_profiles'
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def load_or_create_config(self) -> Dict:
        """Load existing config or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        default_config = {
            'niche': 'ASMR',
            'videos_per_day': 3,
            'upload_times': ['09:00', '14:00', '19:00'],
            'video_duration': 60,
            'platforms': ['youtube', 'tiktok', 'instagram'],
            'use_stock': True,
            'use_rag': RAG_AVAILABLE,
            'quality_threshold': 65,
            'num_image_workers': 2,
            'num_video_workers': 4,
            'timezone': 'UTC',
            'use_gmail_verification': GMAIL_AVAILABLE,
            'enable_uploads': False,
            'upload_after_generation': False,
            'url_references': URL_REFERENCES
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict = None):
        """Save configuration to file"""
        cfg = config or self.config
        with open(self.config_file, 'w') as f:
            json.dump(cfg, f, indent=2)
        print(f"[INFO] Configuration saved to {self.config_file}")
    
    # ═══════════════════════════════════════════════════════════════
    # MODE 1: SINGLE VIDEO GENERATION
    # ═══════════════════════════════════════════════════════════════
    
    def generate_single_video(self, 
                            niche: Optional[str] = None,
                            title: Optional[str] = None,
                            num_scenes: int = 10,
                            use_parallel: bool = True,
                            use_full_workflow: bool = False,
                            reference_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a single video with full pipeline
        
        Args:
            niche: Video niche (e.g., "ASMR", "Tech")
            title: Video title/idea
            num_scenes: Number of scenes to generate
            use_parallel: Use parallel processing (faster)
            use_full_workflow: Use complete 8-step workflow (most comprehensive)
            reference_url: Optional URL to analyze for style/topic
        
        Returns:
            Dict with video metadata and paths
        """
        
        print("\n" + "="*70)
        print("🎬 SINGLE VIDEO GENERATION MODE")
        print("="*70)
        
        niche = niche or self.config.get('niche', 'ASMR')
        
        # MODE 1: Full 8-step workflow (most comprehensive)
        if use_full_workflow:
            print(f"[INFO] Using Complete 8-Step Workflow")
            print(f"       0. Gmail → 1. Trend → 2. Idea → 3. Script")
            print(f"       4. Images ({self.config['num_image_workers']} workers)")
            print(f"       5. Videos ({self.config['num_video_workers']} workers)")
            print(f"       6. Thumbnail → 7. Edit → 8. Upload")
            
            orchestrator = WorkflowOrchestrator(
                num_image_workers=self.config['num_image_workers'],
                num_video_workers=self.config['num_video_workers'],
                use_rag=self.config.get('use_rag', True)
            )
            
            workflow_result = orchestrator.execute_full_workflow(
                niche=niche,
                reference_url=reference_url,
                upload_platforms=self.config.get('platforms', ['youtube']),
                duration=self.config.get('video_duration', 60),
                num_scenes=num_scenes
            )
            
            result = {
                'success': workflow_result.get('success', False),
                'video_path': workflow_result.get('final_video'),
                'thumbnail_path': workflow_result.get('thumbnail'),
                'niche': niche,
                'title': workflow_result.get('script', {}).get('title', title or "Auto-generated"),
                'script': workflow_result.get('script'),
                'upload_results': workflow_result.get('upload_results', {}),
                'mode': 'full_8step_workflow'
            }
        
        # MODE 2: ParallelDirector (fast generation)
        elif use_parallel:
            # NOTE: ParallelDirector module not implemented yet
            # Falling back to full workflow mode
            print(f"[INFO] Parallel mode requested, using WorkflowOrchestrator instead")
            print(f"       Image Workers: {self.config['num_image_workers']}")
            print(f"       Video Workers: {self.config['num_video_workers']}")
            
            orchestrator = WorkflowOrchestrator(
                num_image_workers=self.config['num_image_workers'],
                num_video_workers=self.config['num_video_workers'],
                use_rag=self.config.get('use_rag', True)
            )
            
            workflow_result = orchestrator.execute_full_workflow(
                niche=niche,
                idea=title,
                reference_url=reference_url,
                upload_platforms=None,  # Skip upload in parallel mode
                duration=self.config.get('video_duration', 60),
                num_scenes=num_scenes
            )
            
            result = {
                'success': workflow_result.get('success', False),
                'video_path': workflow_result.get('final_video'),
                'thumbnail_path': workflow_result.get('thumbnail'),
                'niche': niche,
                'title': workflow_result.get('script', {}).get('title', title or "Auto-generated"),
                'mode': 'workflow_parallel'
            }
        else:
            # Sequential processing (simpler, more reliable)
            result = self._generate_sequential(niche, title, num_scenes)
        
        self.stats['total_videos'] += 1
        
        print("\n" + "="*70)
        print("✅ VIDEO GENERATION COMPLETE!")
        print("="*70)
        if result.get('video_path'):
            print(f"📁 Video: {result['video_path']}")
        print("="*70 + "\n")
        
        return result
    
    def _generate_sequential(self, niche: str, title: Optional[str], num_scenes: int) -> Dict:
        """Sequential video generation (fallback method)"""
        from modules.trend_finder import TrendFinder
        from modules.script_generator import ScriptGenerator
        from modules.stock_media import StockMediaFetcher
        from modules.enhanced_editor import EnhancedVideoEditor
        
        # 1. Find topic
        if not title:
            trend_finder = TrendFinder()
            topics = trend_finder.find_trending_topics(niche, limit=5)
            title = topics[0] if topics else f"{niche} content"
        
        print(f"[1/4] Topic: {title}")
        
        # 2. Generate script
        script_gen = ScriptGenerator()
        script = script_gen.generate(title, niche)
        print(f"[2/4] Script generated")
        
        # 3. Get media
        print(f"[3/4] Downloading {num_scenes} stock clips...")
        stock_fetcher = StockMediaFetcher()
        scenes = []
        for i in range(num_scenes):
            video = stock_fetcher.get_stock_video(
                f"{niche} {title} {i+1}",
                (8, 12)
            )
            if video:
                scenes.append(video)
        
        print(f"       Downloaded {len(scenes)} clips")
        
        # 4. Edit
        print(f"[4/4] Editing and combining...")
        editor = EnhancedVideoEditor()
        result = editor.create_viral_ready_video(
            scene_videos=scenes,
            title=title
        )
        
        return {
            'success': True,
            'video_path': result.get('video_path'),
            'niche': niche,
            'title': title,
            'retention_score': result.get('analysis', {}).get('retention_score', 0),
            'mode': 'sequential'
        }
    
    # ═══════════════════════════════════════════════════════════════
    # MODE 2: AUTONOMOUS SCHEDULING
    # ═══════════════════════════════════════════════════════════════
    
    def run_autonomous(self):
        """
        Run autonomous video generation on schedule
        Generates videos automatically at configured times
        """
        try:
            import schedule
            import time
        except ImportError:
            print("[ERROR] 'schedule' module not installed. Run: pip install schedule")
            return
        
        print("\n" + "="*70)
        print("🤖 AUTONOMOUS VIDEO STUDIO")
        print("="*70)
        print(f"Niche: {self.config['niche']}")
        print(f"Videos per day: {self.config['videos_per_day']}")
        print(f"Schedule: {', '.join(self.config['upload_times'])}")
        print("="*70)
        print("\n⏰ Scheduling jobs...")
        
        schedule.clear()
        
        for upload_time in self.config['upload_times']:
            schedule.every().day.at(upload_time).do(self._scheduled_generation)
            print(f"   ✓ Scheduled for {upload_time}")
        
        print("\n✅ Autonomous operation started!")
        print("💡 Press Ctrl+C to stop\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n⏸️ Autonomous operation stopped by user")
    
    def _scheduled_generation(self):
        """Called by scheduler"""
        print(f"\n{'='*70}")
        print(f"🎬 Scheduled Generation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        result = self.generate_single_video(
            niche=self.config['niche'],
            use_parallel=True
        )
        
        if result.get('success'):
            self.stats['successful_uploads'] += 1
        else:
            self.stats['failed_uploads'] += 1
    
    # ═══════════════════════════════════════════════════════════════
    # MODE 3: WEB DASHBOARD
    # ═══════════════════════════════════════════════════════════════
    
    def start_dashboard(self, port: int = 8000):
        """
        Start web dashboard for visual monitoring
        
        Args:
            port: Port number (default: 8000)
        """
        print("\n" + "="*70)
        print("🌐 STARTING WEB DASHBOARD")
        print("="*70)
        
        try:
            # Import dashboard backend
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'website'))
            from website.backend import app, socketio
            
            print(f"\n✅ Dashboard starting on http://localhost:{port}")
            print(f"📊 Dashboard: http://localhost:{port}/dashboard")
            print(f"🌐 API: http://localhost:{port}/api")
            print("\n💡 Press Ctrl+C to stop\n")
            
            socketio.run(app, host='0.0.0.0', port=port, debug=False)
            
        except ImportError as e:
            print(f"[ERROR] Dashboard not available: {e}")
            print("       Make sure Flask and SocketIO are installed:")
            print("       pip install flask flask-cors flask-socketio")
        except KeyboardInterrupt:
            print("\n\n⏸️ Dashboard stopped by user")
    
    # ═══════════════════════════════════════════════════════════════
    # MODE 4: INTERACTIVE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════
    
    def interactive_mode(self):
        """Interactive configuration and execution"""
        print("\n" + "="*70)
        print("🎯 AI VIDEO STUDIO - INTERACTIVE MODE")
        print("="*70)
        
        print("\nWhat would you like to do?\n")
        print("1. Generate a single video now")
        print("2. Configure and run autonomous mode")
        print("3. Start web dashboard")
        print("4. View current configuration")
        print("5. Update configuration")
        print("6. Setup Gmail verification")
        print("7. View URL references")
        print("8. Exit")
        
        choice = input("\nEnter choice (1-8): ").strip()
        
        if choice == '1':
            self._interactive_single_video()
        elif choice == '2':
            self._interactive_autonomous()
        elif choice == '3':
            self.start_dashboard()
        elif choice == '4':
            self._show_config()
        elif choice == '5':
            self._update_config_interactive()
        elif choice == '6':
            self.setup_gmail_verification()
            input("\nPress Enter to continue...")
            self.interactive_mode()
        elif choice == '7':
            self.get_url_references()
            input("\nPress Enter to continue...")
            self.interactive_mode()
        elif choice == '8':
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")
            self.interactive_mode()
    
    def _interactive_single_video(self):
        """Interactive single video generation"""
        print("\n📝 Video Configuration")
        
        niche = input(f"Niche [{self.config['niche']}]: ").strip() or self.config['niche']
        title = input("Video title/idea (leave empty for auto): ").strip() or None
        
        parallel = input("Use parallel processing? (Y/n): ").strip().lower()
        use_parallel = parallel != 'n'
        
        self.generate_single_video(
            niche=niche,
            title=title,
            use_parallel=use_parallel
        )
    
    def _interactive_autonomous(self):
        """Interactive autonomous setup"""
        print("\n🤖 Autonomous Mode Configuration")
        
        self._update_config_interactive()
        
        confirm = input("\nStart autonomous operation now? (Y/n): ").strip().lower()
        if confirm != 'n':
            self.run_autonomous()
    
    def _show_config(self):
        """Display current configuration"""
        print("\n📋 Current Configuration:")
        print("="*50)
        for key, value in self.config.items():
            print(f"  {key:20s}: {value}")
        print("="*50)
    
    def _update_config_interactive(self):
        """Interactive configuration update"""
        print("\n⚙️ Update Configuration (press Enter to keep current)")
        
        niche = input(f"Niche [{self.config['niche']}]: ").strip()
        if niche:
            self.config['niche'] = niche
        
        vpd = input(f"Videos per day [{self.config['videos_per_day']}]: ").strip()
        if vpd:
            self.config['videos_per_day'] = int(vpd)
        
        img_workers = input(f"Image workers [{self.config['num_image_workers']}]: ").strip()
        if img_workers:
            self.config['num_image_workers'] = int(img_workers)
        
        vid_workers = input(f"Video workers [{self.config['num_video_workers']}]: ").strip()
        if vid_workers:
            self.config['num_video_workers'] = int(vid_workers)
        
        self.save_config()
        print("\n✅ Configuration updated!")
    
    def _generate_metadata(self, video_result: Dict) -> Dict:
        """Generate metadata for video upload"""
        try:
            metadata_gen = AIMetadataGenerator()
            metadata = metadata_gen.generate_all_metadata(
                title=video_result.get('title', 'Untitled'),
                duration=60,
                niche=video_result.get('niche', 'General')
            )
            return metadata
        except Exception as e:
            print(f"[WARNING] Metadata generation failed: {e}")
            return {
                'title': video_result.get('title', 'Untitled'),
                'description': f"Generated video in {video_result.get('niche', 'General')} niche",
                'tags': [video_result.get('niche', 'video')]
            }
    
    def setup_gmail_verification(self):
        """Initialize Gmail verification for account creation"""
        if not GMAIL_AVAILABLE:
            print("[ERROR] Gmail verification module not available")
            print("        Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        
        try:
            self.gmail = GmailVerificationTool()
            print("✅ Gmail verification setup complete!")
            print(f"📧 Monitoring emails from: {URL_REFERENCES['gmail_api']}")
            return True
        except FileNotFoundError:
            print("[ERROR] credentials.json not found")
            print(f"       Get it from: {URL_REFERENCES['google_cloud']}")
            return False
        except Exception as e:
            print(f"[ERROR] Gmail setup failed: {e}")
            return False
    
    def get_url_references(self):
        """Display all URL references"""
        print("\n🔗 URL REFERENCES")
        print("=" * 70)
        for name, url in URL_REFERENCES.items():
            print(f"  {name:25s}: {url}")
        print("=" * 70)
        return URL_REFERENCES


# ═══════════════════════════════════════════════════════════════════
# COMMAND LINE INTERFACE
# ═══════════════════════════════════════════════════════════════════

def main():
    """Main entry point with CLI argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='AI Video Automation Studio - Unified Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive mode
  python main.py --quick                            # Quick single video
  python main.py --niche ASMR --title "My Video"    # Custom video
  python main.py --auto                             # Autonomous scheduling
  python main.py --dashboard                        # Web dashboard
  python main.py --dashboard --port 8080            # Dashboard on port 8080
        """
    )
    
    # Mode selection
    parser.add_argument('--quick', action='store_true',
                       help='Quick single video generation')
    parser.add_argument('--auto', action='store_true',
                       help='Run autonomous scheduling mode')
    parser.add_argument('--dashboard', action='store_true',
                       help='Start web dashboard')
    
    # Video parameters
    parser.add_argument('--niche', type=str,
                       help='Video niche (e.g., ASMR, Tech, Travel)')
    parser.add_argument('--title', type=str,
                       help='Video title/idea')
    parser.add_argument('--scenes', type=int, default=10,
                       help='Number of scenes (default: 10)')
    parser.add_argument('--sequential', action='store_true',
                       help='Use sequential processing (slower but more reliable)')
    parser.add_argument('--full-workflow', action='store_true',
                       help='Use complete 8-step workflow (Gmail, Trend, Idea, Script, Images, Videos, Thumbnail, Edit, Upload)')
    parser.add_argument('--url', type=str,
                       help='Reference URL to analyze for video style/topic')
    
    # Dashboard parameters
    parser.add_argument('--port', type=int, default=8000,
                       help='Dashboard port (default: 8000)')
    
    # Configuration
    parser.add_argument('--config', type=str, default='studio_config.json',
                       help='Configuration file path')
    parser.add_argument('--setup-gmail', action='store_true',
                       help='Setup Gmail verification')
    parser.add_argument('--show-urls', action='store_true',
                       help='Display URL references')
    parser.add_argument('--enable-upload', action='store_true',
                       help='Enable auto-upload after generation')
    
    args = parser.parse_args()
    
    # Initialize studio
    studio = UnifiedVideoStudio(config_file=args.config)
    
    # Enable upload if requested
    if args.enable_upload:
        studio.config['upload_after_generation'] = True
        studio.config['enable_uploads'] = True
        print("[INFO] Auto-upload enabled")
    
    # Route to appropriate mode
    if args.setup_gmail:
        studio.setup_gmail_verification()
    
    elif args.show_urls:
        studio.get_url_references()
    
    elif args.dashboard:
        studio.start_dashboard(port=args.port)
    
    elif args.auto:
        studio.run_autonomous()
    
    elif args.quick or args.niche or args.title or args.full_workflow or args.url:
        studio.generate_single_video(
            niche=args.niche,
            title=args.title,
            num_scenes=args.scenes,
            use_parallel=not args.sequential,
            use_full_workflow=args.full_workflow,
            reference_url=args.url
        )
    
    else:
        # No arguments - interactive mode
        studio.interactive_mode()


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Process interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
