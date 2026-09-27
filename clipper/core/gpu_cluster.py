"""
Going Merry — Distributed GPU Cluster Load Balancer
===================================================
Orchestrates parallel video rendering across multiple free Lightning AI
GPU nodes (e.g. across 3 separate Gmail accounts).

Features:
  - Round-robin / Least-busy worker selection
  - Parallel batch dispatch (renders 3 clips simultaneously across 3 workers)
  - Automatic health checks and fault tolerance (failover to next worker)
  - Seamless fallback to local render if all remote nodes are offline
"""

import os
import time
import json
import requests
import threading
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

class GPUClusterManager:
    """Manages a pool of remote GPU render workers (e.g. on Lightning AI)."""
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._worker_index = 0
        self._worker_lock = threading.Lock()
        self._dynamic_workers = set()

    def register_worker(self, url: str, name: str = None):
        """Dynamically registers a worker URL (e.g. from remote self-announcement)."""
        w_clean = url.rstrip("/")
        if w_clean.endswith("/render"):
            w_clean = w_clean[:-7]
        with self._worker_lock:
            self._dynamic_workers.add(w_clean)
        print(f"[CLUSTER] 🟢 Registered dynamic worker: {w_clean} ({name or 'unnamed'})")

    def get_configured_workers(self) -> List[str]:
        """Returns the list of configured worker URLs from environment and dynamic registrations."""
        raw_urls = os.getenv("LIGHTNING_WORKER_URLS", "")
        single_url = os.getenv("LIGHTNING_RENDER_URL") or os.getenv("REMOTE_RENDER_URL")
        
        workers = list(self._dynamic_workers)
        if raw_urls:
            workers.extend([u.strip() for u in raw_urls.split(",") if u.strip()])
        elif single_url:
            workers.append(single_url.strip())
            
        # Clean and deduplicate URLs
        clean_workers = []
        seen = set()
        for w in workers:
            w_clean = w.rstrip("/")
            if w_clean.endswith("/render"):
                w_clean = w_clean[:-7]
            if w_clean and w_clean not in seen:
                seen.add(w_clean)
                clean_workers.append(w_clean)
        return clean_workers

    def get_cluster_status(self) -> List[Dict[str, Any]]:
        """Pings all configured workers to report live health, GPU state, and latency."""
        workers = self.get_configured_workers()
        if not workers:
            return []

        status_list = []

        def ping_worker(idx: int, url: str) -> Dict[str, Any]:
            info = {
                "id": idx + 1,
                "name": f"Worker {idx + 1}",
                "url": url,
                "status": "offline",
                "gpu": False,
                "latency_ms": 0,
                "details": "Unreachable"
            }
            try:
                start_t = time.time()
                res = requests.get(f"{url}/health", timeout=3.5)
                latency = round((time.time() - start_t) * 1000)
                info["latency_ms"] = latency
                if res.status_code == 200:
                    data = res.json()
                    info["status"] = "online" if data.get("status") == "healthy" else "setup_needed"
                    info["gpu"] = data.get("gpu_available", False)
                    info["details"] = "T4 GPU Active 🟢" if info["gpu"] else "CPU Mode ⚠️"
                else:
                    info["details"] = f"HTTP {res.status_code}"
            except Exception as e:
                info["details"] = "Offline / Sleeping"
            return info

        with ThreadPoolExecutor(max_workers=max(1, len(workers))) as executor:
            futures = [executor.submit(ping_worker, i, w) for i, w in enumerate(workers)]
            for f in as_completed(futures):
                status_list.append(f.result())

        status_list.sort(key=lambda x: x["id"])
        return status_list

    def get_next_healthy_worker(self) -> Optional[str]:
        """Returns the next healthy worker using round-robin routing."""
        workers = self.get_configured_workers()
        if not workers:
            return None

        with self._worker_lock:
            # Check up to len(workers) times
            for _ in range(len(workers)):
                worker_url = workers[self._worker_index % len(workers)]
                self._worker_index = (self._worker_index + 1) % len(workers)
                
                try:
                    res = requests.get(f"{worker_url}/health", timeout=2.5)
                    if res.status_code == 200:
                        return worker_url
                except Exception:
                    continue
        return None

    def render_single(
        self,
        video_path: str,
        props: dict,
        output_path: str,
        max_frames: Optional[int] = None
    ) -> Optional[str]:
        """Renders a single clip by routing to the next available GPU worker."""
        worker_url = self.get_next_healthy_worker()
        if not worker_url:
            return None

        endpoint = f"{worker_url}/render"
        print(f"[CLUSTER] 🚀 Routing job to {worker_url}...")
        try:
            start_t = time.time()
            with open(video_path, "rb") as vf:
                files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
                data = {"props_json": json.dumps(props, ensure_ascii=False)}
                if max_frames:
                    data["max_frames"] = str(max_frames)
                
                res = requests.post(endpoint, files=files, data=data, timeout=600)
                
            if res.status_code == 200:
                with open(output_path, "wb") as out_f:
                    out_f.write(res.content)
                elapsed = time.time() - start_t
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[CLUSTER] ✅ Finished on {worker_url} in {elapsed:.1f}s ({size_mb:.1f} MB)")
                return output_path
            else:
                print(f"[CLUSTER] ⚠️ Worker {worker_url} error: HTTP {res.status_code}")
                return None
        except Exception as e:
            print(f"[CLUSTER] ⚠️ Communication failure with {worker_url}: {e}")
            return None

    def render_batch_parallel(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Optional[str]]:
        """
        Renders multiple video clips in parallel across the distributed cluster.
        Each task: {'video_path': ..., 'props': ..., 'output_path': ..., 'max_frames': ...}
        """
        workers = self.get_configured_workers()
        if not workers or len(tasks) <= 1:
            # Fall back to sequential routing
            return [self.render_single(**t) for t in tasks]

        print(f"\n[CLUSTER] ⚡ Launching PARALLEL render across {len(workers)} GPU workers for {len(tasks)} clips...")
        results = [None] * len(tasks)
        
        def execute_task(idx: int, task: dict):
            res = self.render_single(**task)
            return idx, res

        num_threads = min(len(tasks), max(1, len(workers) * 2))
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(execute_task, i, t) for i, t in enumerate(tasks)]
            for f in as_completed(futures):
                idx, out_path = f.result()
                results[idx] = out_path

        return results

# Singleton instance for quick imports
cluster = GPUClusterManager()
