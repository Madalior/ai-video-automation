"""
Test Proxy Rotation System with Pre-Validation

Demonstrates how the WorkerBatchProxy validates proxies BEFORE assigning to workers.
"""

from flowchart.common.proxy_manager import WorkerBatchProxy

def test_proxy_rotation():
    """Test the batch proxy rotation system with pre-validation."""
    
    print("=" * 80)
    print("PROXY ROTATION TEST (WITH PRE-VALIDATION)")
    print("=" * 80)
    
    # Initialize with 2 image workers + 4 video workers (6 total per batch)
    proxy_manager = WorkerBatchProxy(
        proxy_file='fast_proxies.txt',
        image_workers=2,
        video_workers=4
    )
    
    # Show initial stats
    stats = proxy_manager.get_stats()
    print(f"\n[INIT] Total proxies loaded: {stats['total_proxies']}")
    print(f"[INIT] Workers per batch: {stats['workers_per_batch']}")
    print(f"  - Image workers: {stats['image_workers']}")
    print(f"  - Video workers: {stats['video_workers']}")
    
    # Simulate 2 batches with proxy validation
    num_batches = 2
    
    for batch_num in range(1, num_batches + 1):
        print(f"\n{'=' * 80}")
        print(f"BATCH {batch_num} - STARTING WITH PROXY VALIDATION")
        print('=' * 80)
        
        # Start new batch - NOW VALIDATES PROXY FIRST!
        proxy = proxy_manager.start_batch(validate=True, max_retries=5)
        
        if proxy is None:
            print(f"[ERROR] Could not start batch {batch_num} - no working proxies!")
            continue
        
        # Simulate workers using this validated proxy
        print(f"\nAll workers using validated proxy:")
        
        for worker_num in range(1, stats['workers_per_batch'] + 1):
            worker_type = "IMAGE" if worker_num <= stats['image_workers'] else "VIDEO"
            print(f"  Worker {worker_num} ({worker_type}): {proxy}")
            
            # Mark worker as complete
            batch_complete = proxy_manager.worker_complete()
            
            if batch_complete:
                print(f"\n[OK] Batch {batch_num} complete! Ready for next batch...")
    
    # Final stats
    print(f"\n{'=' * 80}")
    print("FINAL STATISTICS")
    print('=' * 80)
    
    final_stats = proxy_manager.get_stats()
    print(f"Batches completed: {final_stats['completed_batches']}")
    print(f"Proxies in pool: {final_stats['total_proxies']}")
    
    print(f"\n{'=' * 80}")
    print("TEST COMPLETE - Proxies are now validated before each batch!")
    print('=' * 80)

if __name__ == "__main__":
    test_proxy_rotation()
