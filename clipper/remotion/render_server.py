"""
Going Merry — High-Speed GPU Render Microservice
=================================================
Runs on Lightning AI (or any GPU server) to provide ultra-fast (35-45s)
Remotion caption & badge rendering for the Going Merry pipeline.

Usage:
    python render_server.py [--port 8000] [--host 0.0.0.0]
"""

import os
import sys
import json
import uuid
import shutil
import argparse
import subprocess
from pathlib import Path
from flask import Flask, request, send_file, jsonify

REMOTION_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = REMOTION_DIR / "public"
PUBLIC_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

def check_gpu():
    """Detect if an NVIDIA GPU is available."""
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False

AUTH_TOKEN = os.getenv("CLUSTER_SECRET_TOKEN", "going_merry_gpu_secret_2026")

@app.before_request
def verify_token():
    if request.path in ["/health", "/", "/favicon.ico"]:
        return None
    token = request.headers.get("X-Cluster-Token") or request.form.get("auth_token") or request.args.get("auth_token")
    if AUTH_TOKEN and token != AUTH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

@app.route("/", methods=["GET"])
def index():
    """Worker status landing page."""
    gpu_active = check_gpu()
    remotion_ready = (REMOTION_DIR / "node_modules").exists()
    status_color = "#10b981" if remotion_ready else "#f59e0b"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Going Merry GPU Worker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 32px; max-width: 480px; width: 90%; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); text-align: center; }}
            .badge {{ display: inline-block; padding: 6px 14px; border-radius: 9999px; font-weight: 600; font-size: 13px; margin: 8px 4px; }}
            .green {{ background: #065f46; color: #34d399; }}
            .yellow {{ background: #78350f; color: #fde68a; }}
            h1 {{ margin: 0 0 8px 0; font-size: 24px; color: #38bdf8; }}
            p {{ color: #94a3b8; font-size: 14px; margin: 4px 0; }}
            .status-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: {status_color}; margin-right: 6px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🎬 Going Merry Worker</h1>
            <p><span class="status-dot"></span>Microservice Online & Ready</p>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;">
            <div>
                <span class="badge {'green' if gpu_active else 'yellow'}">{'🟢 NVIDIA GPU Active' if gpu_active else '⚠️ CPU Fallback'}</span>
                <span class="badge {'green' if remotion_ready else 'yellow'}">{'🟢 Remotion Ready' if remotion_ready else '⏳ Setup Needed'}</span>
            </div>
            <p style="margin-top: 20px; font-size: 12px; color: #64748b;">Ready to accept render requests from Azure Master.</p>
        </div>
    </body>
    </html>
    """, 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint — reports GPU presence and Remotion readiness."""
    gpu_active = check_gpu()
    node_installed = shutil.which("node") is not None
    remotion_ready = (REMOTION_DIR / "node_modules").exists()
    
    return jsonify({
        "status": "healthy" if remotion_ready else "setup_required",
        "gpu_available": gpu_active,
        "node_installed": node_installed,
        "remotion_installed": remotion_ready,
        "service": "Going Merry GPU Render Node"
    }), 200

@app.route("/render", methods=["POST"])
def render_clip():
    """
    Renders word-by-word captions + Whop badge into the uploaded video clip.
    Receives:
      - 'video': multipart MP4 file
      - 'props_json': stringified JSON props for Composition.tsx
      - 'max_frames' (optional): integer to render only the first N frames
    """
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video_file = request.files["video"]
    props_str = request.form.get("props_json", "{}")
    max_frames = request.form.get("max_frames", None)
    
    job_id = uuid.uuid4().hex[:8]
    temp_input_name = f"temp_render_vid_{job_id}.mp4"
    temp_input_path = PUBLIC_DIR / temp_input_name
    temp_props_name = f"temp_props_{job_id}.json"
    temp_props_path = REMOTION_DIR / temp_props_name
    output_filename = f"rendered_output_{job_id}.mp4"
    output_path = REMOTION_DIR / output_filename

    try:
        # 1. Save uploaded video to Remotion public/
        video_file.save(str(temp_input_path))
        
        # 2. Parse props and bind local video filename
        try:
            props = json.loads(props_str)
        except Exception:
            props = {}
        props["videoPath"] = temp_input_name
        
        with open(temp_props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)
            
        # 3. Assemble Remotion CLI command with hardware acceleration
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "ViralCaptionComponent", str(output_path),
            "--props", temp_props_name,
            "--gl=angle"
        ]
        if max_frames:
            cmd.extend(["--frames", f"0-{int(max_frames)}"])
            
        print(f"\n[GPU_WORKER] 🚀 Starting render job {job_id}...")
        r = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            shell=(os.name == "nt")
        )
        
        if r.returncode != 0 or not output_path.exists():
            print(f"[GPU_WORKER] ❌ Render failed:\n{r.stderr[-2000:]}")
            return jsonify({
                "error": "Remotion render failed",
                "details": r.stderr[-2000:]
            }), 500
            
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"[GPU_WORKER] ✅ Render complete: {output_filename} ({size_mb:.1f} MB)")
        
        # Send completed file back
        return send_file(
            str(output_path),
            mimetype="video/mp4",
            as_attachment=True,
            download_name=f"captioned_{job_id}.mp4"
        )
        
    except Exception as e:
        print(f"[GPU_WORKER] ❌ Server exception: {e}")
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Clean up temporary input and props files
        if temp_input_path.exists():
            try: os.remove(temp_input_path)
            except Exception: pass
        if temp_props_path.exists():
            try: os.remove(temp_props_path)
            except Exception: pass


def discover_lightning_public_url(port: int = 8000) -> str:
    """Tries to expose the port and retrieve the public URL via lightning-sdk inside Studio."""
    try:
        from lightning_sdk import Studio
        studio = Studio()
        try:
            port_info = studio.add_ports(port)
            if port_info and hasattr(port_info[0], "urls") and port_info[0].urls:
                return port_info[0].urls[0]
        except Exception:
            pass
        try:
            url = studio.get_url(port=port)
            if url:
                return url
        except Exception:
            pass
    except Exception as e:
        print(f"[GPU_WORKER] Notice: lightning-sdk discovery ({e})")
    return None


def auto_register_with_master(master_url: str, public_url: str, worker_name: str, token: str):
    """Pings the Azure Master dashboard to register this worker in the live pool."""
    import requests
    endpoint = f"{master_url.rstrip('/')}/api/cluster/register"
    payload = {
        "url": public_url,
        "name": worker_name,
        "auth_token": token
    }
    try:
        res = requests.post(endpoint, json=payload, timeout=5)
        if res.status_code == 200:
            print(f"[GPU_WORKER] 🟢 Auto-registered with Master: {endpoint}")
        else:
            print(f"[GPU_WORKER] ⚠️ Master registration returned HTTP {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[GPU_WORKER] ⚠️ Could not reach Master at {master_url}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Going Merry GPU Render Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--name", default="Worker Node", help="Human-readable worker name (e.g. Worker 1)")
    parser.add_argument("--master-url", default="https://app.sarkaricalc.me", help="Azure master URL (default: https://app.sarkaricalc.me)")
    parser.add_argument("--public-url", default=None, help="This worker's public Lightning URL")
    parser.add_argument("--token", default=AUTH_TOKEN, help="Shared cluster security token")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"🎬 Going Merry — High-Speed GPU Render Node [{args.name}]")
    print(f"📍 Directory  : {REMOTION_DIR}")
    print(f"⚡ GPU Status : {'NVIDIA GPU DETECTED 🟢' if check_gpu() else 'CPU Fallback ⚠️'}")
    print(f"🌐 Listening  : http://{args.host}:{args.port}")

    public_url = args.public_url or discover_lightning_public_url(args.port)
    if public_url:
        print(f"🔗 Public URL : {public_url}")
    if args.master_url and public_url:
        print(f"📡 Master Hub : {args.master_url}")
        auto_register_with_master(args.master_url, public_url, args.name, args.token)
    elif args.master_url and not public_url:
        print(f"ℹ️ Tip: Pass --public-url <url> or copy the URL from Lightning Port Viewer")
    print("=" * 60)
    
    app.run(host=args.host, port=args.port, threaded=True)


