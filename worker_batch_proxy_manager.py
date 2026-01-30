"""
Worker-Batch Proxy Manager

Strategy: One proxy handles multiple workers (batch processing)
- 1 Proxy → 2 Image Workers + 4 Video Workers
- Rotate to next proxy only when ALL workers finish
- More efficient, natural usage pattern

Example:
Proxy 1: Image1, Image2, Video1, Video2, Video3, Video4 → All complete → Next proxy
Proxy 2: Image3, Image4, Video5, Video6, Video7, Video8 → All complete → Next proxy
"""

import threading
import time
from flowchart.common.proxy_manager import ProxyManager


class WorkerBatchProxyManager:
    """Manages proxy assignment for worker batches."""
    
    def __init__(self, proxy_file='fast_proxies.txt', image_workers=2, video_workers=4):
        """
        Initialize worker-batch proxy manager.
        
        Args:
            proxy_file: Path to proxy list
            image_workers: Number of image generation workers per batch
            video_workers: Number of video generation workers per batch
        """
        self.proxy_manager = ProxyManager(proxy_file)
        self.image_workers = image_workers
        self.video_workers = video_workers
        self.total_workers_per_batch = image_workers + video_workers
        
        # Current batch tracking
        self.current_proxy = None
        self.active_workers = 0
        self.completed_batches = 0
        self.worker_lock = threading.Lock()
        
        print(f"[INIT] Worker-Batch Proxy Manager")
        print(f"  Batch size: {image_workers} image + {video_workers} video = {self.total_workers_per_batch} workers")
        print(f"  Proxies available: {self.proxy_manager.get_stats()['total_proxies']}")
        
    def start_batch(self):
        """
        Start a new worker batch with fresh proxy.
        
        Returns:
            str: Proxy URL for this batch
        """
        with self.worker_lock:
            # Get next proxy for this batch
            self.current_proxy = self.proxy_manager.get_next_proxy()
            self.active_workers = self.total_workers_per_batch  # Pre-allocate worker slots
            
            print(f"\n[BATCH {self.completed_batches + 1}] Starting new batch")
            print(f"  Proxy: {self.current_proxy}")
            print(f"  Workers: {self.total_workers_per_batch} ({self.image_workers} image + {self.video_workers} video)")
            
            return self.current_proxy
    
    def register_worker(self, worker_type):
        """
        Get proxy for worker (already registered in batch).
        Auto-starts batch if none active.
        
        Args:
            worker_type: 'image' or 'video'
            
        Returns:
            str: Proxy URL to use
        """
        if self.current_proxy is None:
            # Auto-start a new batch
            self.start_batch()
        
        return self.current_proxy
    
    def worker_complete(self, worker_type):
        """
        Mark worker as complete. Rotate proxy if batch finished.
        
        Args:
            worker_type: 'image' or 'video'
            
        Returns:
            dict: Status info
        """
        with self.worker_lock:
            self.active_workers -= 1
            
            print(f"  [{worker_type.upper()}] Worker complete. Active: {self.active_workers}/{self.total_workers_per_batch}")
            
            # Check if batch complete
            if self.active_workers == 0:
                self.completed_batches += 1
                print(f"\n[BATCH COMPLETE] All workers finished. Moving to next proxy...")
                print(f"  Batches completed: {self.completed_batches}")
                
                # Reset for next batch
                old_proxy = self.current_proxy
                self.current_proxy = None
                
                return {
                    'batch_complete': True,
                    'completed_batches': self.completed_batches,
                    'old_proxy': old_proxy
                }
            
            return {
                'batch_complete': False,
                'active_workers': self.active_workers
            }
    
    def run_batch_workflow(self, batch_data):
        """
        Run a complete batch workflow with workers.
        
        Args:
            batch_data: dict with 'images' and 'videos' to generate
            
        Returns:
            dict: Batch results
        """
        # Start new batch
        proxy = self.start_batch()
        
        # Simulate workers
        image_data = batch_data.get('images', [])
        video_data = batch_data.get('videos', [])
        
        results = {
            'proxy': proxy,
            'image_results': [],
            'video_results': []
        }
        
        # Process workers in order
        all_workers = []
        
        # Add image workers
        for i, img in enumerate(image_data[:self.image_workers], 1):
            all_workers.append(('image', img, i))
        
        # Add video workers  
        for i, vid in enumerate(video_data[:self.video_workers], 1):
            all_workers.append(('video', vid, i))
        
        # Execute workers
        print(f"\n[WORKERS] Processing {len(all_workers)} workers...")
        for worker_type, data, idx in all_workers:
            worker_proxy = self.register_worker(worker_type)
            
            # Simulate work
            print(f"    Generating {worker_type} {idx} with proxy {worker_proxy}...")
            time.sleep(0.3)  # Simulate work
            
            if worker_type == 'image':
                results['image_results'].append({
                    'image': data,
                    'proxy': worker_proxy,
                    'success': True
                })
            else:
                results['video_results'].append({
                    'video': data,
                    'proxy': worker_proxy,
                    'success': True
                })
            
            self.worker_complete(worker_type)
        
        return results
    
    def process_multiple_batches(self, batch_list):
        """
        Process multiple batches, rotating proxy between batches.
        
        Args:
            batch_list: List of batch_data dicts
            
        Returns:
            list: Results for all batches
        """
        print(f"\n{'='*80}")
        print(f"[MULTI-BATCH] Processing {len(batch_list)} batches")
        print(f"{'='*80}")
        
        all_results = []
        
        for i, batch_data in enumerate(batch_list, 1):
            print(f"\n{'='*80}")
            print(f"BATCH {i}/{len(batch_list)}")
            print(f"{'='*80}")
            
            result = self.run_batch_workflow(batch_data)
            all_results.append(result)
            
            # Small delay between batches
            if i < len(batch_list):
                time.sleep(1)
        
        return all_results
    
    def get_statistics(self):
        """Get manager statistics."""
        return {
            'total_proxies': self.proxy_manager.get_stats()['total_proxies'],
            'workers_per_batch': self.total_workers_per_batch,
            'image_workers': self.image_workers,
            'video_workers': self.video_workers,
            'completed_batches': self.completed_batches,
            'current_active_workers': self.active_workers,
            'current_proxy': self.current_proxy
        }


# Example usage
if __name__ == "__main__":
    print("="*80)
    print("WORKER-BATCH PROXY MANAGER - DEMO")
    print("="*80)
    
    # Initialize manager
    manager = WorkerBatchProxyManager(
        proxy_file='fast_proxies.txt',
        image_workers=2,
        video_workers=4
    )
    
    # Create sample batches
    batches = [
        {
            'images': ['scene1_img', 'scene2_img'],
            'videos': ['scene1_vid', 'scene2_vid', 'scene3_vid', 'scene4_vid']
        },
        {
            'images': ['scene5_img', 'scene6_img'],
            'videos': ['scene5_vid', 'scene6_vid', 'scene7_vid', 'scene8_vid']
        },
        {
            'images': ['scene9_img', 'scene10_img'],
            'videos': ['scene9_vid', 'scene10_vid', 'scene11_vid', 'scene12_vid']
        }
    ]
    
    # Process batches (each batch uses one proxy)
    results = manager.process_multiple_batches(batches)
    
    # Show statistics
    print(f"\n{'='*80}")
    print("FINAL STATISTICS")
    print(f"{'='*80}")
    
    stats = manager.get_statistics()
    print(f"Batches completed: {stats['completed_batches']}")
    print(f"Workers per batch: {stats['workers_per_batch']}")
    print(f"  - Image workers: {stats['image_workers']}")
    print(f"  - Video workers: {stats['video_workers']}")
    
    # Show proxy usage
    print(f"\nProxy rotation:")
    for i, result in enumerate(results, 1):
        img_count = len(result['image_results'])
        vid_count = len(result['video_results'])
        print(f"  Batch {i}: {result['proxy']} → {img_count} images + {vid_count} videos")
    
    print(f"\n✅ Worker-batch proxy management working!")
    print(f"Each proxy handled {stats['workers_per_batch']} workers before rotating.")
