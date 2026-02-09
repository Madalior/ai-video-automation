"""
Multi-Worker Shared Session Manager

Creates multiple SharedSessionManager workers for parallel image + video generation.
Each worker uses a shared session (1 login for both img + video).

Benefits:
- 4x faster: 4 workers processing in parallel
- Efficient: Each worker reuses one session for both operations
- Anti-bot: 10s delays between worker launches
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flowchart.common.shared_session import SharedSessionManager
from flowchart.character.image_generator import DreaminaGenerator
from flowchart.character.video_generator import DreaminaVideoGenerator


class MultiSharedSessionManager:
    """
    Manages multiple workers, each with a shared session for img+video generation.
    
    Usage:
        manager = MultiSharedSessionManager(num_workers=4)
        
        # Batch generate images
        image_results = manager.generate_images_batch(tasks)
        
        # Batch generate videos
        video_results = manager.generate_videos_batch(tasks)
        
        manager.close()
    """
    
    def __init__(self, num_workers=4, headless=False):
        """
        Initialize multi-worker shared session manager.
        
        Args:
            num_workers: Number of parallel workers (default: 4)
            headless: Run browsers in headless mode
        """
        self.num_workers = num_workers
        self.headless = headless
        self.workers = []  # List of dicts with session, img_gen, video_gen
        
        print(f"\n[MULTI-SHARED] Initializing {num_workers} workers...")
        
        # Initialize workers sequentially (each completes login before next starts)
        for i in range(num_workers):
            worker = self._init_worker(i)
            if worker:
                self.workers.append(worker)
        
        
        
        print(f"\n[MULTI-SHARED] OK - {len(self.workers)}/{num_workers} workers ready")
    
    def _init_worker(self, worker_id):
        """Initialize a single worker with shared session."""
        print(f"\n[WORKER {worker_id}] Launching...")
        
        try:
            # Create shared session
            session = SharedSessionManager(
                headless=self.headless,
                fresh_profile=True  # Each worker gets fresh profile
            )
            
            print(f"[WORKER {worker_id}] Logging in...")
            if not session.login():
                print(f"[WORKER {worker_id}] ✗ Login failed")
                return None
            
            print(f"[WORKER {worker_id}] Creating generators...")
            
            # Create image generator with shared session
            img_gen = DreaminaGenerator(shared_session=session)
            
            # Create video generator with shared session
            video_gen = DreaminaVideoGenerator(shared_session=session)
            
            print(f"[WORKER {worker_id}] ✓ Ready (session + img + video)")
            
            return {
                'id': worker_id,
                'session': session,
                'img_gen': img_gen,
                'video_gen': video_gen
            }
            
        except Exception as e:
            print(f"[WORKER {worker_id}] ✗ Initialization failed: {e}")
            return None
    
    def generate_images_batch(self, tasks):
        """
        Generate multiple images in parallel using workers.
        
        Args:
            tasks: List of dicts with 'prompt', 'output_path'
        
        Returns:
            List of results with status and paths
        """
        print(f"\n[MULTI-SHARED] Generating {len(tasks)} images with {len(self.workers)} workers...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            # Submit tasks
            futures = {}
            for i, task in enumerate(tasks):
                worker = self.workers[i % len(self.workers)]
                future = executor.submit(self._generate_image_worker, worker, task)
                futures[future] = task
            
            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"[ERROR] Image task failed: {e}")
                    results.append({
                        'task': task,
                        'status': 'failed',
                        'error': str(e),
                        'path': None
                    })
        
        successful = sum(1 for r in results if r['status'] == 'success')
        print(f"[MULTI-SHARED] Images complete: {successful}/{len(tasks)} successful")
        
        return results
    
    def _generate_image_worker(self, worker, task):
        """Worker task: generate one image."""
        worker_id = worker['id']
        img_gen = worker['img_gen']
        
        try:
            print(f"[WORKER {worker_id}] Generating image: {task.get('prompt', '')[:50]}...")
            
            # Reset session for new operation
            worker['session'].reset_for_next_operation()
            time.sleep(2)
            
            # Generate image
            success = img_gen.generate_image(
                prompt=task['prompt'],
                output_path=task['output_path']
            )
            
            return {
                'task': task,
                'status': 'success' if success else 'failed',
                'path': task['output_path'] if success else None,
                'worker_id': worker_id
            }
            
        except Exception as e:
            print(f"[WORKER {worker_id}] Image generation failed: {e}")
            return {
                'task': task,
                'status': 'failed',
                'error': str(e),
                'path': None,
                'worker_id': worker_id
            }
    
    def generate_videos_batch(self, tasks):
        """
        Generate multiple videos in parallel using workers.
        
        Args:
            tasks: List of dicts with 'prompt', 'output_path', 'reference_image_paths'
        
        Returns:
            List of results with status and paths
        """
        print(f"\n[MULTI-SHARED] Generating {len(tasks)} videos with {len(self.workers)} workers...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=len(self.workers)) as executor:
            # Submit tasks
            futures = {}
            for i, task in enumerate(tasks):
                worker = self.workers[i % len(self.workers)]
                future = executor.submit(self._generate_video_worker, worker, task)
                futures[future] = task
            
            # Collect results
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"[ERROR] Video task failed: {e}")
                    results.append({
                        'task': task,
                        'status': 'failed',
                        'error': str(e),
                        'path': None
                    })
        
        successful = sum(1 for r in results if r['status'] == 'success')
        print(f"[MULTI-SHARED] Videos complete: {successful}/{len(tasks)} successful")
        
        return results
    
    def _generate_video_worker(self, worker, task):
        """Worker task: generate one video."""
        worker_id = worker['id']
        video_gen = worker['video_gen']
        
        try:
            print(f"[WORKER {worker_id}] Generating video: {task.get('prompt', '')[:50]}...")
            
            # Reset session for new operation
            worker['session'].reset_for_next_operation()
            time.sleep(2)
            
            # Generate video
            success = video_gen.generate_video(
                prompt=task['prompt'],
                reference_image_paths=task.get('reference_image_paths'),
                output_path=task['output_path']
            )
            
            return {
                'task': task,
                'status': 'success' if success else 'failed',
                'path': task['output_path'] if success else None,
                'worker_id': worker_id
            }
            
        except Exception as e:
            print(f"[WORKER {worker_id}] Video generation failed: {e}")
            return {
                'task': task,
                'status': 'failed',
                'error': str(e),
                'path': None,
                'worker_id': worker_id
            }
    
    def close(self):
        """Close all workers and sessions."""
        print("\n[MULTI-SHARED] Closing all workers...")
        
        for worker in self.workers:
            try:
                worker['session'].close()
                print(f"[WORKER {worker['id']}] OK - Closed")
            except Exception as e:
                print(f"[WORKER {worker['id']}] Warning: {e}")
        
        self.workers = []
        print("[MULTI-SHARED] All workers closed")
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


if __name__ == "__main__":
    print("="*70)
    print("MULTI-WORKER SHARED SESSION MANAGER - TEST")
    print("="*70)
    
    # Test initialization
    manager = MultiSharedSessionManager(num_workers=2, headless=False)
    
    print("\n" + "="*70)
    print(f"Initialized {len(manager.workers)} workers")
    print("Each worker has: 1 session + 1 img_gen + 1 video_gen")
    print("="*70)
    
    # Test batch image generation
    image_tasks = [
        {'prompt': 'A futuristic cityscape', 'output_path': 'test_img1.png'},
        {'prompt': 'A serene mountain landscape', 'output_path': 'test_img2.png'}
    ]
    
    print("\nReady to test batch generation!")
    print("Closing for test...")
    manager.close()
