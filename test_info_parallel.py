#!/usr/bin/env python3
"""
Test Info Pipeline Parallel Processing

Compares sequential vs parallel performance for info video generation.
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flowchart.info.info_orchestrator import InfoContentOrchestrator


def test_sequential():
    """Test sequential AI generation"""
    print("\n" + "="*70)
    print("TEST 1: SEQUENTIAL AI GENERATION (Baseline)")
    print("="*70)
    
    orchestrator = InfoContentOrchestrator(
        output_dir="output_info_seq",
        video_mode="ai",
        use_parallel=False  # Sequential mode
    )
    
    start_time = time.time()
    
    try:
        result = orchestrator.execute_full_workflow(
            niche="space facts",
            duration=56,  # 7 scenes * 8 seconds
            skip_upload=True
        )
        
        elapsed = time.time() - start_time
        print(f"\n✓ Sequential completed in: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        return elapsed
        
    except Exception as e:
        print(f"\n✗ Sequential failed: {e}")
        return None


def test_parallel():
    """Test parallel AI generation"""
    print("\n" + "="*70)
    print("TEST 2: PARALLEL AI GENERATION (4 Workers)")
    print("="*70)
    
    orchestrator = InfoContentOrchestrator(
        output_dir="output_info_parallel",
        video_mode="ai",
        use_parallel=True,  # Parallel mode
        num_ai_workers=4    # 4 chrome workers
    )
    
    start_time = time.time()
    
    try:
        result = orchestrator.execute_full_workflow(
            niche="space facts",
            duration=56,  # 7 scenes * 8 seconds
            skip_upload=True
        )
        
        elapsed = time.time() - start_time
        print(f"\n✓ Parallel completed in: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        return elapsed
        
    except Exception as e:
        print(f"\n✗ Parallel failed: {e}")
        return None


def main():
    """Run performance comparison"""
    print("\n" + "=" * 70)
    print("  INFO PIPELINE PARALLEL PROCESSING - PERFORMANCE TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Generate a 7-scene info video SEQUENTIALLY")
    print("  2. Generate the same video with 4 PARALLEL workers")
    print("  3. Compare the performance improvement")
    print("\n" + "-" * 70)
    
    # Option 1: Run sequential first
    seq_time = test_sequential()
    
    if seq_time:
        print("\n" + "="*70)
        print("Waiting 30 seconds before parallel test...")
        print("="*70)
        time.sleep(30)  # Cool down period
    
    # Option 2: Run parallel
    parallel_time = test_parallel()
    
    # Results
    print("\n" + "="*70)
    print("  PERFORMANCE COMPARISON RESULTS")
    print("="*70)
    
    if seq_time and parallel_time:
        speedup = seq_time / parallel_time
        time_saved = seq_time - parallel_time
        
        print(f"\nSequential:  {seq_time:.2f}s ({seq_time/60:.2f} min)")
        print(f"Parallel:    {parallel_time:.2f}s ({parallel_time/60:.2f} min)")
        print(f"\nSpeedup:     {speedup:.2f}x faster")
        print(f"Time Saved:  {time_saved:.2f}s ({time_saved/60:.2f} min)")
        print(f"Improvement: {((1 - parallel_time/seq_time) * 100):.1f}% faster")
        
        # Theoretical vs actual
        print(f"\nTheoretical max speedup: 4x (4 workers)")
        print(f"Actual speedup:          {speedup:.2f}x")
        print(f"Efficiency:              {(speedup/4 * 100):.1f}%")
        
    elif seq_time:
        print(f"\nSequential test completed: {seq_time:.2f}s")
        print("Parallel test failed - see errors above")
    elif parallel_time:
        print(f"\nParallel test completed: {parallel_time:.2f}s")
        print("Sequential test failed - see errors above")
    else:
        print("\nBoth tests failed - check configuration and try again")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n⚠️  NOTE: This test requires:")
    print("   - Working AI video generators (Veo3/Dreamina)")
    print("   - 4 Chrome profiles for parallel workers")
    print("   - Sufficient system resources (8GB+ RAM)")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
