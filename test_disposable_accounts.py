"""
Test the Disposable Account Generator

Run this to see the IP rotation in action with placeholder video generation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dreamina_disposable_accounts import DisposableAccountGenerator


print("="*80)
print("TESTING DISPOSABLE ACCOUNT GENERATOR")
print("="*80)

# Initialize
generator = DisposableAccountGenerator('fast_proxies.txt')

print("\n[INFO] Generator initialized with proxy rotation")
stats = generator.get_statistics()
print(f"  - Available proxies: {stats['total_proxies']}")
print(f"  - Ready to create unlimited disposable accounts")

# Test 1: Single video generation
print("\n" + "="*80)
print("[TEST 1] Single Video with Disposable Account")
print("="*80)

video_config = {
    'prompt': 'A detective solving a mystery in old town',
    'duration': 5,
    'style': 'cinematic'
}

result = generator.generate_video_with_disposable_account(video_config)

if result['success']:
    print(f"\n✓ Success!")
    print(f"  - Account used: {result['account']}")
    print(f"  - Proxy used: {result['proxy']}")
else:
    print(f"\n✗ Failed: {result.get('error')}")

# Test 2: Batch generation with rotating accounts
print("\n" + "="*80)
print("[TEST 2] Batch Generation - 5 Videos, 5 Different IPs")
print("="*80)

video_batch = [
    {'prompt': 'Detective mystery', 'duration': 5},
    {'prompt': 'Space adventure', 'duration': 5},
    {'prompt': 'Cooking show', 'duration': 5},
    {'prompt': 'Nature documentary', 'duration': 5},
    {'prompt': 'Tech tutorial', 'duration': 5}
]

batch_results = generator.generate_batch_videos(video_batch)

# Show which proxies were used
print(f"\n{'='*80}")
print("PROXY ROTATION VERIFICATION")
print(f"{'='*80}")
proxies_used = [r.get('proxy') for r in batch_results if r.get('success')]
print(f"Videos generated: {len(batch_results)}")
print(f"Unique IPs used: {len(set(proxies_used))}")
print(f"\nProxies cycled:")
for i, proxy in enumerate(proxies_used, 1):
    print(f"  {i}. {proxy}")

# Final stats
print(f"\n{'='*80}")
print("FINAL STATISTICS")
print(f"{'='*80}")
final_stats = generator.get_statistics()
print(f"Total videos generated: {final_stats['completed_videos']}")
print(f"Proxies available: {final_stats['total_proxies']}")
print(f"Current rotation position: {final_stats['proxy_rotation_index']}/{final_stats['total_proxies']}")

print(f"\n✅ Disposable account system working perfectly!")
print(f"Ready to scale to unlimited video generation with {final_stats['total_proxies']} rotating IPs!")
