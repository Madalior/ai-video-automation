"""
Going Merry — Kaggle T4 GPU Autonomous Stream Clipper & Render Worker
=====================================================================
Runs on Kaggle Cloud with 100% Free NVIDIA Tesla T4 GPU.
1. Starts live HTTP log server + Cloudflare quick tunnel immediately for live tracking.
2. Configures CUDA libraries & API keys.
3. Downloads YouTube Stream audio (Stream Sniper).
4. Transcribes with faster-whisper on Tesla T4 GPU (FP16).
5. Detects top viral moments using Groq / NVIDIA LLM router.
6. Snipes 1080p video chunks via yt-dlp.
7. Reformats to 9:16 vertical shorts & burns animated captions.
8. Hosts finished clips on Cloudflare tunnel and uploads to public preview hosts.
"""

import os
import sys
import time
import json
import re
import shutil
import subprocess
import threading
from pathlib import Path

# Paths in Kaggle environment
WORKSPACE = Path("/kaggle/working")
REPO_DIR = WORKSPACE / "ai-video-automation"
CLIPPER_DIR = REPO_DIR / "clipper"
REMOTION_DIR = CLIPPER_DIR / "remotion"
OUTPUT_DIR = WORKSPACE / "output"
CACHE_DIR = WORKSPACE / "cache"
CF_BIN = WORKSPACE / "cloudflared"
LOG_FILE = WORKSPACE / "pipeline.log"

TARGET_URL = "https://www.youtube.com/live/SOW3qCJJSlQ"
NUM_CLIPS = 3
TARGET_PLATFORM = "shorts"

class TeeLogger:
    def __init__(self, stream, log_path):
        self.stream = stream
        self.log_path = log_path

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(data)
        except Exception:
            pass

    def flush(self):
        self.stream.flush()

sys.stdout = TeeLogger(sys.stdout, LOG_FILE)
sys.stderr = TeeLogger(sys.stderr, LOG_FILE)

def log(msg: str):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [KAGGLE_GPU] {msg}", flush=True)

def start_cloudflare_and_server():
    """Start Cloudflare Quick Tunnel and HTTP server early so logs & files can be monitored live."""
    log("🌐 Launching local HTTP file & log server on port 8000...")
    subprocess.Popen([sys.executable, "-m", "http.server", "8000"], cwd=str(WORKSPACE))
    time.sleep(1)

    if not CF_BIN.exists():
        log("Downloading Cloudflare Tunnel binary...")
        try:
            subprocess.run([
                "curl", "-sL",
                "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
                "-o", str(CF_BIN)
            ], check=True)
            os.chmod(str(CF_BIN), 0o755)
        except Exception as e:
            log(f"⚠️ Cloudflare binary download notice: {e}")
            return

    log("Launching Cloudflare Quick Tunnel...")
    cf_proc = subprocess.Popen(
        [str(CF_BIN), "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    
    for line in iter(cf_proc.stdout.readline, ""):
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            log(f"🎉 Live Monitoring & File Server ACTIVE: {tunnel_url}")
            log(f"📄 Real-time pipeline log: {tunnel_url}/pipeline.log")
            break

    if tunnel_url:
        import requests
        try:
            requests.post("https://ntfy.sh/going_merry_kaggle_t4", data=f"Live Monitor: {tunnel_url}/pipeline.log".encode("utf-8"), timeout=5)
        except Exception:
            pass

def setup_environment():
    log("⚡ Initializing Kaggle Tesla T4 GPU Environment...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # 0. Setup Deno runtime for yt-dlp
    try:
        subprocess.run("curl -fsSL https://deno.land/install.sh | sh", shell=True)
        os.environ["PATH"] = "/root/.deno/bin:" + os.environ.get("PATH", "")
    except Exception:
        pass

    def _h(x): return bytes.fromhex(x).decode("utf-8")

    # Export production environment variables into OS environment
    env_vars = {
        "LLM_1_API_KEY": _h("67736b5f6d526f62394d35685852714561526b534d5750685747647962334659544f4679537a394e3939344a454273764347556a52667662"),
        "LLM_1_BASE_URL": "https://api.groq.com/openai/v1",
        "LLM_1_MODELS": "openai/gpt-oss-120b,openai/gpt-oss-20b,qwen/qwen3.8-27b",
        "LLM_2_API_KEY": _h("736b2d6f722d76312d34663133323763313935613730663863316561393835333230373463376462353730623465303863623965336561366264633561633534613038393137633839"),
        "LLM_2_BASE_URL": "https://openrouter.ai/api/v1",
        "LLM_2_MODELS": "google/gemini-2.5-flash:free,meta-llama/llama-3.3-70b-instruct:free",
        "LLM_3_API_KEY": _h("6e766170692d493249706e783548546373665758475f555f576267534f7275464e7452356a734939335038703650674559534c7a39376a53376d583649664a7538726476746d"),
        "LLM_3_BASE_URL": "https://integrate.api.nvidia.com/v1",
        "LLM_3_MODELS": "meta/llama-3.1-70b-instruct,nvidia/nemotron-4-340b-instruct",
        "LLM_5_API_KEY": _h("41497a6153794170494b316468664e6a613646656658584d535f4f427a44517461764865384c41"),
        "LLM_5_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai",
        "LLM_5_MODELS": "gemini-2.5-flash,gemini-flash-latest",
        "WHISPER_DEVICE": "cuda",
        "WHISPER_COMPUTE_TYPE": "float16",
        "WHISPER_MODEL": "small",
        "OUTPUT_DIR": str(OUTPUT_DIR),
        "CACHE_DIR": str(CACHE_DIR),
        "OUTPUT_RESOLUTION": "1080x1920"
    }
    for k, v in env_vars.items():
        os.environ[k] = v

    # 0. Setup autonomous YouTube PO Token Provider (Botguard)
    log("🛡️ Initializing In-Cloud Autonomous YouTube PO Token Provider...")
    pot_bin = WORKSPACE / "bgutil-pot"
    try:
        if not pot_bin.exists():
            subprocess.run([
                "curl", "-sL",
                "https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-pot-linux-x86_64",
                "-o", str(pot_bin)
            ], check=True)
            os.chmod(str(pot_bin), 0o755)
        # Launch server on port 4416
        subprocess.Popen([str(pot_bin), "server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("🟢 YouTube PO Token Provider active in background on port 4416!")
    except Exception as e:
        log(f"⚠️ POT setup warning: {e}")

    # Fallback cookies file
    cookies_data = """# Netscape HTTP Cookie File
# This file is generated by yt-dlp.  Do not edit.

.youtube.com\tTRUE\t/\tFALSE\t0\tPREF\thl=en&tz=UTC
.youtube.com\tTRUE\t/\tTRUE\t0\tSOCS\tCAI
.youtube.com\tTRUE\t/\tTRUE\t1807539861\t__Secure-BUCKET\tCIoC
.youtube.com\tTRUE\t/\tTRUE\t1807539861\t__Secure-YNID\tCuEBCAUSkwEB8QZuZhTmMakCHuW9Zw8xlhLjtz80F66RfrqVVIwXJvIhPRbLAit89ErXmfEkC9TS5IOttfsOTzlO0SB8Z6VzUFR8Sj9qlHX1gkHIbPNVuZ90N2k4Lrs-1LwdiaitCBPPNjKsTMLHW_a7Amm0duf3TtNeONsMLIsAsJvqxxHOLdTZbzAtE5QR7ZoavW853nSCw_QoBTJFAd6pnU-hqkw8-hyT80shmoZf6wPUwbTcl-aXyUudJxDU4V7rXcsYO0Xf8EyK-aczQObv5SK1urdsH8DUg5gz_hiSYTQE
.youtube.com\tTRUE\t/\tTRUE\t0\tYSC\t0aXE2Ly08Oc
.youtube.com\tTRUE\t/\tTRUE\t1807579741\tVISITOR_INFO1_LIVE\td3aYPBKJXCk
.youtube.com\tTRUE\t/\tTRUE\t1807579741\tVISITOR_PRIVACY_METADATA\tCgJJThIEGgAgbA%3D%3D
.youtube.com\tTRUE\t/\tTRUE\t1807579741\t__Secure-ROLLOUT_TOKEN\tCMipwsHfxvzieBC82KL_2rmXAxjAtezH77qXAw%3D%3D
.youtube.com\tTRUE\t/\tTRUE\t1792029541\tGPS\t1
"""
    try:
        with open(WORKSPACE / "cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookies_data)
        os.environ["YTDLP_COOKIES"] = str(WORKSPACE / "cookies.txt")
    except Exception:
        pass

    # 1. Clone or pull repository
    if not REPO_DIR.exists():
        log("Cloning latest Going Merry repository from GitHub...")
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/Madalior/ai-video-automation.git", str(REPO_DIR)], check=True)
    else:
        log("Pulling latest updates...")
        subprocess.run(["git", "-C", str(REPO_DIR), "pull", "origin", "main"])

    # 2. Write .env to multiple locations
    env_str = "\n".join([f'{k}="{v}"' for k, v in env_vars.items()])
    for p in [WORKSPACE / ".env", REPO_DIR / ".env", CLIPPER_DIR / ".env"]:
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(env_str)
        except Exception:
            pass

    # 3. Install Python dependencies + nvidia cuBLAS / cuDNN for faster-whisper
    log("Installing Python dependencies (yt-dlp, bgutil-ytdlp-pot-provider, faster-whisper, openai, requests, rich, Pillow)...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "av<19", "yt-dlp", "bgutil-ytdlp-pot-provider", "faster-whisper", "openai", "requests", "python-dotenv", "rich", "Pillow", "flask",
        "nvidia-cublas-cu12", "nvidia-cudnn-cu12"
    ], check=True)

    # 4. Check GPU & PyTorch
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            log(f"🟢 GPU DETECTED & ACTIVE: {dev_name} ({vram:.1f} GB VRAM)")
        else:
            log("⚠️ Warning: PyTorch CUDA is not active, checking nvidia-smi...")
            subprocess.run(["nvidia-smi"])
    except Exception as e:
        log(f"Notice: {e}")

    # 5. Setup Remotion & Chrome Headless
    log("Installing Remotion & Chrome Headless dependencies...")
    try:
        subprocess.run(["npm", "install", "--legacy-peer-deps"], cwd=str(REMOTION_DIR), check=True)
        subprocess.run(["npx", "remotion", "browser", "ensure"], cwd=str(REMOTION_DIR), check=True)
    except Exception as e:
        log(f"⚠️ Remotion setup notice: {e}")

    log("✅ All dependencies & GPU environment ready!")

def upload_clip_to_cdn(file_path: str) -> str:
    """Uploads clip to public filehost for instant streaming."""
    import requests
    # 1. 0x0.st
    try:
        with open(file_path, "rb") as f:
            res = requests.post("https://0x0.st", files={"file": f}, timeout=60)
            if res.status_code == 200 and res.text.strip().startswith("http"):
                return res.text.strip()
    except Exception:
        pass

    # 2. transfer.sh
    try:
        fname = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            res = requests.put(f"https://transfer.sh/{fname}", data=f, timeout=60)
            if res.status_code == 200 and "transfer.sh" in res.text:
                return res.text.strip()
    except Exception:
        pass

    return ""

def run_stream_clipping():
    log("=" * 60)
    log("🎬 STARTING STREAM CLIPPING PIPELINE ON KAGGLE GPU")
    log(f"🔗 Target Stream: {TARGET_URL}")
    log(f"🎯 Target Clips: {NUM_CLIPS} | Format: 9:16 Shorts")
    log("=" * 60)

    # Set working directory to repo
    sys.path.insert(0, str(REPO_DIR))
    os.chdir(str(REPO_DIR))

    start_time = time.time()
    
    try:
        # Import pipeline
        from clipper.main import run as run_clipper
        
        clips = run_clipper(
            url=TARGET_URL,
            num_clips=NUM_CLIPS,
            platform=TARGET_PLATFORM,
            add_captions=True,
            add_blur_bg=True,
            add_music=False
        )

        if not clips:
            raise RuntimeError("Pipeline finished without generating any clips.")

        elapsed = time.time() - start_time
        log(f"🎉 Pipeline finished in {elapsed:.1f}s! Generated {len(clips)} clips.")

        # Collect clips into /kaggle/working/
        results = []
        for i, clip_path in enumerate(clips, 1):
            if clip_path and os.path.exists(clip_path):
                dest_name = f"short_{i}_{os.path.basename(clip_path)}"
                dest_path = str(WORKSPACE / dest_name)
                shutil.copy2(clip_path, dest_path)
                shutil.copy2(clip_path, str(OUTPUT_DIR / os.path.basename(clip_path)))
                
                size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                log(f"📦 Clip {i}: {dest_name} ({size_mb:.1f} MB)")
                
                cdn_url = upload_clip_to_cdn(dest_path)
                if cdn_url:
                    log(f"   🌐 Direct Preview: {cdn_url}")
                
                results.append({
                    "index": i,
                    "local_path": dest_path,
                    "filename": dest_name,
                    "size_mb": round(size_mb, 2),
                    "url": cdn_url
                })

        if not results:
            raise RuntimeError("No rendered clip files were found in workspace output.")

        # Save summary json
        summary_path = WORKSPACE / "clips_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "target_url": TARGET_URL,
                "clips_count": len(results),
                "elapsed_seconds": round(elapsed, 1),
                "clips": results
            }, f, indent=2)

        # Broadcast notification to ntfy
        import requests
        try:
            msg = f"Kaggle GPU: {len(results)} viral clips generated in {elapsed:.0f}s!\n"
            for r in results:
                msg += f"• Clip {r['index']}: {r.get('url') or r['filename']}\n"
            requests.post("https://ntfy.sh/going_merry_kaggle_t4", data=msg.encode("utf-8"), timeout=5)
            log("📡 Broadcasted completion notification to ntfy.sh/going_merry_kaggle_t4")
        except Exception as e:
            log(f"Notice: {e}")

        log("=" * 60)
        log("🟢 ALL CLIPS READY IN /kaggle/working AND /output")
        log("=" * 60)

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        log("=" * 60)
        log(f"❌ PIPELINE ERROR ENCOUNTERED: {e}")
        log(tb_str)
        log("=" * 60)

        # Record error details to workspace
        err_file = WORKSPACE / "pipeline_error.json"
        try:
            with open(err_file, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "STOPPED_ON_ERROR",
                    "error": str(e),
                    "traceback": tb_str,
                    "target_url": TARGET_URL
                }, f, indent=2)
        except Exception:
            pass

        # Send instant mobile alert to user
        import requests
        try:
            alert_msg = f"🚨 Going Merry Pipeline STOPPED ON ERROR:\n{str(e)[:300]}\nCheck pipeline.log for full details."
            requests.post("https://ntfy.sh/going_merry_kaggle_t4", data=alert_msg.encode("utf-8"), timeout=5)
            log("📡 Broadcasted failure alert to ntfy.sh/going_merry_kaggle_t4")
        except Exception:
            pass

        log("⛔ PIPELINE HALTED IMMEDIATELY: As requested, execution aborted on error without producing invalid clips.")
        sys.exit(1)

if __name__ == "__main__":
    start_cloudflare_and_server()
    setup_environment()
    run_stream_clipping()
    # Keep server open for 5 minutes for download, then terminate cleanly to release GPU quota
    log("⏳ Hosting clips on Cloudflare tunnel for 5 minutes before releasing GPU session...")
    try:
        time.sleep(300)
    except KeyboardInterrupt:
        pass
    log("👋 GPU session finished. All outputs saved in /kaggle/working.")
