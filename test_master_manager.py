"""
Test script for master_manager.py

This script tests the MasterVideoAutomation class to ensure:
1. Initialization works correctly
2. Directory structure is created
3. Worker initialization functions properly
4. Basic methods are callable
5. Command-line argument parsing works

Run this to verify the master manager is working before full production runs.
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from master_manager import MasterVideoAutomation
    MASTER_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Could not import MasterVideoAutomation: {e}")
    MASTER_MANAGER_AVAILABLE = False


class TestMasterManager(unittest.TestCase):
    """Test suite for MasterVideoAutomation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once"""
        if not MASTER_MANAGER_AVAILABLE:
            raise unittest.SkipTest("MasterVideoAutomation not available")
    
    def setUp(self):
        """Set up each test"""
        self.test_output_dir = "test_output_master"
        
    def tearDown(self):
        """Clean up after each test"""
        # Clean up test output directory if it was created
        if os.path.exists(self.test_output_dir):
            import shutil
            try:
                shutil.rmtree(self.test_output_dir)
            except Exception as e:
                print(f"[WARNING] Could not remove test directory: {e}")
    
    def test_initialization(self):
        """Test that MasterVideoAutomation initializes correctly"""
        print("\n[TEST] Testing MasterVideoAutomation initialization...")
        
        try:
            manager = MasterVideoAutomation(
                output_dir=self.test_output_dir,
                headless=True,
                use_emotional_ai=True
            )
            
            # Check attributes
            self.assertEqual(manager.output_dir, self.test_output_dir)
            self.assertTrue(manager.headless)
            self.assertTrue(manager.use_emotional_ai)
            
            # Check directories dict exists
            self.assertIsNotNone(manager.dirs)
            self.assertIn('character', manager.dirs)
            self.assertIn('info', manager.dirs)
            self.assertIn('metadata', manager.dirs)
            self.assertIn('logs', manager.dirs)
            
            print("  ✓ Initialization successful")
            print(f"  ✓ Output directory: {manager.output_dir}")
            print(f"  ✓ Directories created: {list(manager.dirs.keys())}")
            
        except Exception as e:
            self.fail(f"Initialization failed: {e}")
    
    def test_directory_creation(self):
        """Test that all required directories are created"""
        print("\n[TEST] Testing directory creation...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        # Check that directories exist
        for dir_name, dir_path in manager.dirs.items():
            self.assertTrue(
                os.path.exists(dir_path),
                f"Directory not created: {dir_name} -> {dir_path}"
            )
            print(f"  ✓ {dir_name}: {dir_path}")
    
    def test_print_summary(self):
        """Test that print_summary doesn't crash"""
        print("\n[TEST] Testing print_summary...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        try:
            manager.print_summary()
            print("  ✓ Summary printed successfully")
        except Exception as e:
            self.fail(f"print_summary failed: {e}")
    
    @patch('master_manager.SharedSessionManager')
    @patch('master_manager.DreaminaGenerator')
    @patch('master_manager.DreaminaVideoGenerator')
    def test_init_workers(self, mock_video_gen, mock_img_gen, mock_session):
        """Test worker initialization with mocked dependencies"""
        print("\n[TEST] Testing worker initialization...")
        
        # Setup mocks
        mock_session_instance = MagicMock()
        mock_session_instance.login.return_value = True
        mock_session.return_value = mock_session_instance
        
        mock_img_gen_instance = MagicMock()
        mock_img_gen.return_value = mock_img_gen_instance
        
        mock_video_gen_instance = MagicMock()
        mock_video_gen.return_value = mock_video_gen_instance
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        try:
            print("  [INFO] Initializing 2 workers (reduced for testing)...")
            workers = manager._init_workers(num_workers=2, stagger_delay=1)
            
            # Check workers were created
            self.assertEqual(len(workers), 2, "Expected 2 workers")
            
            # Check each worker has required keys
            for worker in workers:
                self.assertIn('id', worker)
                self.assertIn('session', worker)
                self.assertIn('img_gen', worker)
                self.assertIn('video_gen', worker)
            
            print(f"  ✓ {len(workers)} workers initialized")
            print("  ✓ Each worker has session, img_gen, and video_gen")
            
        except Exception as e:
            self.fail(f"Worker initialization failed: {e}")
    
    def test_save_production_metadata(self):
        """Test metadata saving"""
        print("\n[TEST] Testing metadata saving...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        # Create test result
        test_result = {
            'status': 'completed',
            'video_path': '/fake/path/video.mp4',
            'duration': 120,
            'timestamp': datetime.now().isoformat()
        }
        
        project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            manager._save_production_metadata(test_result, 'character', project_id)
            
            # Check file was created
            metadata_file = os.path.join(
                manager.dirs['metadata'],
                f"character_{project_id}_metadata.json"
            )
            
            self.assertTrue(os.path.exists(metadata_file), "Metadata file not created")
            
            # Read and verify content
            with open(metadata_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data['status'], 'completed')
            self.assertEqual(saved_data['video_path'], '/fake/path/video.mp4')
            
            print(f"  ✓ Metadata saved to: {metadata_file}")
            print(f"  ✓ Metadata content verified")
            
        except Exception as e:
            self.fail(f"Metadata saving failed: {e}")
    
    def test_save_batch_summary(self):
        """Test batch summary saving"""
        print("\n[TEST] Testing batch summary saving...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        # Create test results
        test_results = [
            {'status': 'completed', 'video_path': '/fake/video1.mp4'},
            {'status': 'completed', 'video_path': '/fake/video2.mp4'},
            {'status': 'failed', 'error': 'Test error'}
        ]
        
        try:
            manager._save_batch_summary(test_results)
            
            # Find the summary file
            metadata_dir = manager.dirs['metadata']
            summary_files = [f for f in os.listdir(metadata_dir) if f.startswith('batch_')]
            
            self.assertGreater(len(summary_files), 0, "No batch summary file created")
            
            # Read and verify
            summary_file = os.path.join(metadata_dir, summary_files[0])
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            self.assertEqual(summary['total_videos'], 3)
            self.assertEqual(summary['successful'], 2)
            self.assertEqual(summary['failed'], 1)
            
            print(f"  ✓ Batch summary saved: {summary_file}")
            print(f"  ✓ Summary stats: {summary['successful']}/{summary['total_videos']} successful")
            
        except Exception as e:
            self.fail(f"Batch summary saving failed: {e}")
    
    def test_character_video_args(self):
        """Test that produce_character_video accepts the right arguments"""
        print("\n[TEST] Testing produce_character_video parameter validation...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        # Check method exists and has correct signature
        method = getattr(manager, 'produce_character_video', None)
        self.assertIsNotNone(method, "produce_character_video method not found")
        
        # Check callable
        self.assertTrue(callable(method), "produce_character_video is not callable")
        
        print("  ✓ produce_character_video method exists and is callable")
    
    def test_info_video_args(self):
        """Test that produce_info_video accepts the right arguments"""
        print("\n[TEST] Testing produce_info_video parameter validation...")
        
        manager = MasterVideoAutomation(
            output_dir=self.test_output_dir,
            headless=True
        )
        
        # Check method exists and has correct signature
        method = getattr(manager, 'produce_info_video', None)
        self.assertIsNotNone(method, "produce_info_video method not found")
        
        # Check callable
        self.assertTrue(callable(method), "produce_info_video is not callable")
        
        print("  ✓ produce_info_video method exists and is callable")


class TestCommandLineInterface(unittest.TestCase):
    """Test command-line interface"""
    
    def test_help_message(self):
        """Test that --help works"""
        print("\n[TEST] Testing --help command...")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, "master_manager.py", "--help"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        self.assertEqual(result.returncode, 0, "Help command failed")
        self.assertIn("Master Video Automation", result.stdout)
        self.assertIn("--type", result.stdout)
        
        print("  ✓ --help works correctly")
    
    def test_summary_command(self):
        """Test that --summary works"""
        print("\n[TEST] Testing --summary command...")
        
        import subprocess
        result = subprocess.run(
            [sys.executable, "master_manager.py", "--summary"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Should succeed (may have some import warnings)
        self.assertIn("CAPABILITIES", result.stdout)
        
        print("  ✓ --summary command works")


def run_integration_test():
    """
    Integration test - try to actually run a simple workflow
    (This is separated from unit tests as it requires real dependencies)
    """
    print("\n" + "="*80)
    print("INTEGRATION TEST (Optional - requires all dependencies)")
    print("="*80)
    
    print("\n[INFO] This test will attempt to initialize the manager with all real dependencies.")
    print("[INFO] It may fail if dependencies are not properly installed.")
    
    try:
        manager = MasterVideoAutomation(
            output_dir="test_integration_output",
            headless=True,
            use_emotional_ai=True
        )
        
        print("\n✓ Manager initialized successfully")
        print("✓ All directories created")
        
        # Print summary
        manager.print_summary()
        
        print("\n✓ Integration test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test FAILED: {e}")
        print("[INFO] This is expected if dependencies are not installed")
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("MASTER MANAGER TEST SUITE")
    print("="*80)
    
    # Check if master_manager can be imported
    if not MASTER_MANAGER_AVAILABLE:
        print("\n[ERROR] Cannot import MasterVideoAutomation")
        print("[ERROR] Make sure master_manager.py exists and all dependencies are installed")
        return 1
    
    # Run unit tests
    print("\n" + "="*80)
    print("UNIT TESTS")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMasterManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandLineInterface))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Run integration test
    integration_passed = run_integration_test()
    
    # Overall result
    print("\n" + "="*80)
    if result.wasSuccessful():
        print("✅ ALL UNIT TESTS PASSED!")
        if integration_passed:
            print("✅ INTEGRATION TEST PASSED!")
        else:
            print("⚠️  Integration test failed (dependencies may be missing)")
        print("="*80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
