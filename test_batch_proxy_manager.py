"""
Test WorkerBatchProxy from proxy_manager.py
"""

from flowchart.common.proxy_manager import WorkerBatchProxy

print("="*80)
print("TESTING WorkerBatchProxy FROM PROXY_MANAGER")
print("="*80)

# Initialize with fast proxies
batch_proxy = WorkerBatchProxy('fast_proxies.txt', image_workers=2, video_workers=4)

print("\n[TEST] Simulating 2 batches with worker-batch proxy rotation\n")

# Batch 1
print("BATCH 1:")
proxy = batch_proxy.start_batch()
print(f"  All workers using: {proxy}")

# Simulate 2 image workers
for i in range(2):
    print(f"    Image worker {i+1} complete")
    batch_proxy.worker_complete()

# Simulate 4 video workers  
for i in range(4):
    print(f"    Video worker {i+1} complete")
    is_complete = batch_proxy.worker_complete()
    if is_complete:
        print(f"    ✓ Batch complete - rotating to next proxy!\n")

# Batch 2
print("BATCH 2:")
proxy = batch_proxy.start_batch()
print(f"  All workers using: {proxy}")

# Simulate all workers
for i in range(6):
    worker_type = "Image" if i < 2 else "Video"
    print(f"    {worker_type} worker {i+1} complete")
    is_complete = batch_proxy.worker_complete()
    if is_complete:
        print(f"    ✓ Batch complete!\n")

# Show stats
print("="*80)
print("STATISTICS")
print("="*80)
stats = batch_proxy.get_stats()
print(f"Total proxies: {stats['total_proxies']}")
print(f"Workers per batch: {stats['workers_per_batch']} ({stats['image_workers']} image + {stats['video_workers']} video)")
print(f"Completed batches: {stats['completed_batches']}")

print(f"\n✅ WorkerBatchProxy integrated successfully into proxy_manager.py!")
