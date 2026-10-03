"""
Going Merry — Kaggle T4 GPU Autonomous Render Worker
===================================================
Runs on Kaggle Cloud with 100% Free NVIDIA Tesla T4 GPU (30 hours/week).
Automatically starts Remotion render server, exposes Cloudflare tunnel,
and registers itself with Azure Master (https://app.sarkaricalc.me).
"""

import os
import sys
import time
import json
import re
import shutil
import subprocess
from pathlib import Path

WORKSPACE = Path("/kaggle/working")
REPO_DIR = WORKSPACE / "ai-video-automation"
REMOTION_DIR = REPO_DIR / "clipper" / "remotion"
CF_BIN = WORKSPACE / "cloudflared"

MASTER_URL = os.getenv("MASTER_URL", "https://app.sarkaricalc.me")
CLUSTER_TOKEN = os.getenv("CLUSTER_SECRET_TOKEN", "going_merry_gpu_secret_2026")

def log(msg: str):
    print(f"[KAGGLE_WORKER] {msg}", flush=True)

def setup_environment():
    log("⚡ Initializing Kaggle T4 GPU Environment...")
    
    # 1. Clone repository if not present
    if not REPO_DIR.exists():
        log("Cloning Going Merry repository...")
        subprocess.run(["git", "clone", "https://github.com/Madalior/ai-video-automation.git", str(REPO_DIR)], check=True)
    else:
        log("Pulling latest updates...")
        subprocess.run(["git", "-C", str(REPO_DIR), "pull", "origin", "main"])

    # 2. Install Python dependencies
    log("Installing Python dependencies (flask, requests, yt-dlp, faster-whisper)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "requests", "yt-dlp", "faster-whisper"], check=True)

    # 3. Setup Remotion & Chrome Headless
    log("Installing Remotion & Chrome Headless dependencies...")
    subprocess.run(["npm", "install", "--legacy-peer-deps"], cwd=str(REMOTION_DIR), check=True)
    subprocess.run(["npx", "remotion", "browser", "ensure"], cwd=str(REMOTION_DIR), check=True)

    # 4. Download Cloudflare tunnel binary if not present
    if not CF_BIN.exists():
        log("Downloading Cloudflare Tunnel binary...")
        subprocess.run([
            "curl", "-sL",
            "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
            "-o", str(CF_BIN)
        ], check=True)
        os.chmod(str(CF_BIN), 0o755)

    log("✅ All dependencies & Remotion GPU environment successfully verified!")

def start_services():
    log("🚀 Starting Going Merry GPU Render Server on port 8000...")
    server_env = os.environ.copy()
    server_env["CLUSTER_SECRET_TOKEN"] = CLUSTER_TOKEN
    
    server_proc = subprocess.Popen(
        [sys.executable, "render_server.py", "--port", "8000", "--host", "0.0.0.0"],
        cwd=str(REMOTION_DIR),
        env=server_env
    )
    time.sleep(3)

    log("🌐 Launching Cloudflare Quick Tunnel...")
    cf_proc = subprocess.Popen(
        [str(CF_BIN), "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read output until tunnel URL is found
    for line in iter(cf_proc.stdout.readline, ""):
        print(line, end="", flush=True)
        match = url_pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            log(f"🎉 Cloudflare Tunnel ACTIVE: {tunnel_url}")
            break

    if not tunnel_url:
        log("❌ Failed to obtain Cloudflare tunnel URL")
        return

    # Auto-register with Azure Master
    log(f"📡 Registering with Azure Master: {MASTER_URL}...")
    import requests
    reg_url = f"{MASTER_URL.rstrip('/')}/api/cluster/register"
    payload = {
        "url": tunnel_url,
        "name": "Kaggle NVIDIA T4 Worker",
        "auth_token": CLUSTER_TOKEN
    }
    
    registered = False
    for attempt in range(5):
        try:
            r = requests.post(reg_url, json=payload, timeout=10)
            if r.status_code == 200:
                log(f"🟢 SUCCESS! Registered with Master: {r.text}")
                registered = True
                break
            else:
                log(f"⚠️ Registration attempt {attempt+1} failed: HTTP {r.status_code}")
        except Exception as e:
            log(f"⚠️ Registration attempt {attempt+1} error: {e}")
        time.sleep(3)

    if not registered:
        log("⚠️ Could not reach Master directly, keeping tunnel alive.")

    log("=" * 60)
    log("🟢 KAGGLE GPU WORKER IS LIVE AND READY FOR RENDERS!")
    log(f"🔗 Public URL: {tunnel_url}")
    log("=" * 60)

    # Keep worker running for up to 9 hours (Kaggle max runtime)
    try:
        while True:
            time.sleep(30)
            if server_proc.poll() is not None:
                log("⚠️ Render server exited! Restarting...")
                server_proc = subprocess.Popen(
                    [sys.executable, "render_server.py", "--port", "8000"],
                    cwd=str(REMOTION_DIR)
                )
    except KeyboardInterrupt:
        log("Shutting down worker...")
        server_proc.terminate()
        cf_proc.terminate()

if __name__ == "__main__":
    setup_environment()
    start_services()
