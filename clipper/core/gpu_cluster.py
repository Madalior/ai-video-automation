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
import sys
import time
import json
import requests
import threading
from typing import Optional, List, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
        self.token = os.getenv("CLUSTER_SECRET_TOKEN", "going_merry_gpu_secret_2026")
        self._persist_file = Path("data") / "cluster_workers.json"
        self._load_persisted_workers()

    def _load_persisted_workers(self):
        try:
            if self._persist_file.exists():
                with open(self._persist_file, "r") as f:
                    saved = json.load(f)
                    if isinstance(saved, list):
                        self._dynamic_workers.update(saved)
        except Exception:
            pass

    def _save_persisted_workers(self):
        try:
            self._persist_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persist_file, "w") as f:
                json.dump(list(self._dynamic_workers), f)
        except Exception:
            pass

    def register_worker(self, url: str, name: str = None):
        """Dynamically registers a worker URL (e.g. from remote self-announcement)."""
        w_clean = url.rstrip("/")
        if w_clean.endswith("/render"):
            w_clean = w_clean[:-7]
        with self._worker_lock:
            self._dynamic_workers.add(w_clean)
            self._save_persisted_workers()
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

        # Auto-discover active Kaggle worker from broadcast channel
        try:
            r = requests.get("https://ntfy.sh/going_merry_kaggle_t4/raw?poll=1", timeout=1.5)
            if r.status_code == 200 and "trycloudflare.com" in r.text:
                for line in r.text.strip().splitlines():
                    line = line.strip()
                    if "trycloudflare.com" in line and line.startswith("http"):
                        workers.append(line)
        except Exception:
            pass
            
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

    def trigger_kaggle_worker_if_needed(self) -> bool:
        """Uses official Kaggle API to autonomously dispatch a 30h/wk free T4 GPU worker container."""
        username = os.getenv("KAGGLE_USERNAME")
        key = os.getenv("KAGGLE_KEY")
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
        
        if not ((username and key) or kaggle_json.exists()):
            return False

        try:
            print("[CLUSTER] ⚡ No active GPU workers. Dispatching autonomous Kaggle T4 GPU worker...")
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()

            kernel_dir = Path(__file__).resolve().parent.parent.parent / "kaggle_worker"
            meta_file = kernel_dir / "kernel-metadata.json"
            if meta_file.exists():
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                effective_user = username or (json.load(open(kaggle_json)).get("username") if kaggle_json.exists() else None)
                if effective_user and "YOUR_KAGGLE_USERNAME" in meta.get("id", ""):
                    meta["id"] = f"{effective_user}/going-merry-gpu-worker"
                    with open(meta_file, "w") as f:
                        json.dump(meta, f, indent=2)

            api.kernel_push(str(kernel_dir))
            print("[CLUSTER] 🟢 Kaggle T4 GPU worker successfully pushed and started in cloud!")
            return True
        except Exception as e:
            print(f"[CLUSTER] ⚠️ Kaggle auto-trigger notice: {e}")
            return False

    def wake_up_studio_if_needed(self) -> bool:
        """Uses lightning-sdk to wake up a sleeping studio on a T4 GPU automatically."""
        api_key = os.getenv("LIGHTNING_API_KEY")
        studio_name = os.getenv("LIGHTNING_STUDIO_NAME", "scratch-studio-devbox")
        teamspace = os.getenv("LIGHTNING_TEAMSPACE")
        if not api_key:
            return False

        try:
            print(f"[CLUSTER] ⚡ Checking Lightning Studio '{studio_name}' state...")
            from lightning_sdk import Studio, Machine
            studio = Studio(name=studio_name, teamspace=teamspace)
            if getattr(studio, "status", "").lower() != "running":
                print(f"[CLUSTER] ⚡ Studio '{studio_name}' is sleeping. Waking up on T4 GPU...")
                studio.start(Machine.T4)
                print(f"[CLUSTER] 🟢 Studio '{studio_name}' successfully awakened on T4 GPU!")
                time.sleep(3)
            return True
        except Exception as e:
            print(f"[CLUSTER] ⚠️ Auto-wakeup notice: {e}")
            return False

    def get_next_healthy_worker(self) -> Optional[str]:
        """Returns the next healthy worker using round-robin routing."""
        workers = self.get_configured_workers()
        if not workers:
            # 1. Try Kaggle 30h/week free T4 GPU first
            if self.trigger_kaggle_worker_if_needed():
                print("[CLUSTER] ⏳ Waiting up to 60s for Kaggle GPU worker to register...")
                for _ in range(12):
                    time.sleep(5)
                    workers = self.get_configured_workers()
                    if workers:
                        break
            # 2. Fall back to Lightning AI
            elif os.getenv("LIGHTNING_API_KEY"):
                self.wake_up_studio_if_needed()
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
        
        # If all workers offline but SDK is configured, try waking it up
        if os.getenv("LIGHTNING_API_KEY"):
            if self.wake_up_studio_if_needed():
                for w in workers:
                    try:
                        res = requests.get(f"{w}/health", timeout=3.0)
                        if res.status_code == 200:
                            return w
                    except Exception:
                        pass
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

        print(f"[CLUSTER] 🚀 Routing job to {worker_url}...")
        headers = {"X-Cluster-Token": self.token}
        data = {
            "props_json": json.dumps(props, ensure_ascii=False),
            "auth_token": self.token
        }
        if max_frames:
            data["max_frames"] = str(max_frames)

        try:
            start_t = time.time()
            # 1. Try async job submission first (avoids Cloudflare 100s timeout)
            async_endpoint = f"{worker_url}/render_async"
            use_sync = False
            
            with open(video_path, "rb") as vf:
                files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
                res = requests.post(async_endpoint, files=files, data=data, headers=headers, timeout=60)
            
            if res.status_code == 202:
                job_id = res.json().get("job_id")
                print(f"[CLUSTER] ⏳ Async job queued (ID: {job_id}). Polling progress...")
                poll_url = f"{worker_url}/status/{job_id}"
                
                while True:
                    time.sleep(3)
                    try:
                        s_res = requests.get(poll_url, headers=headers, timeout=10)
                        if s_res.status_code != 200:
                            continue
                        job_data = s_res.json()
                        status = job_data.get("status")
                        if status == "completed":
                            dl_url = f"{worker_url}/download/{job_id}"
                            dl_res = requests.get(dl_url, headers=headers, stream=True, timeout=120)
                            if dl_res.status_code == 200:
                                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                                with open(output_path, "wb") as out_f:
                                    for chunk in dl_res.iter_content(chunk_size=16384):
                                        out_f.write(chunk)
                                elapsed = time.time() - start_t
                                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                                print(f"[CLUSTER] ✅ Finished on {worker_url} in {elapsed:.1f}s ({size_mb:.1f} MB)")
                                return output_path
                            else:
                                print(f"[CLUSTER] ⚠️ Download failed: HTTP {dl_res.status_code}")
                                return None
                        elif status == "failed":
                            print(f"[CLUSTER] ⚠️ Render job failed on worker: {job_data.get('error')}")
                            return None
                        else:
                            elapsed = time.time() - start_t
                            print(f"[CLUSTER] ⏳ Rendering on GPU... ({elapsed:.0f}s elapsed)")
                    except Exception as pe:
                        print(f"[CLUSTER] ⚠️ Poll notice: {pe}")
            elif res.status_code in (404, 405):
                use_sync = True
            else:
                print(f"[CLUSTER] ⚠️ Worker returned HTTP {res.status_code}, falling back to sync...")
                use_sync = True

            if use_sync:
                endpoint = f"{worker_url}/render"
                with open(video_path, "rb") as vf:
                    files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
                    res = requests.post(endpoint, files=files, data=data, headers=headers, timeout=600)
                if res.status_code == 200:
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
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
