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
import time
import json
import uuid
import shutil
import threading
import argparse
import subprocess
from pathlib import Path
from flask import Flask, request, send_file, jsonify

REMOTION_DIR = Path(__file__).resolve().parent
REPO_DIR = REMOTION_DIR.parent.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

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

JOBS = {}
JOBS_LOCK = threading.Lock()

@app.before_request
def verify_token():
    if request.path in ["/health", "/", "/favicon.ico"] or request.path.startswith("/status/") or request.path.startswith("/download/"):
        return None
    token = request.headers.get("X-Cluster-Token") or request.form.get("auth_token") or request.args.get("auth_token")
    if AUTH_TOKEN and token != AUTH_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401

def _run_render_job(job_id, temp_input_path, temp_props_path, output_path, max_frames):
    with JOBS_LOCK:
        JOBS[job_id]["status"] = "rendering"
    try:
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts", "ViralCaptionComponent", str(output_path),
            "--props", os.path.basename(temp_props_path),
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
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = r.stderr[-1000:]
        else:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[GPU_WORKER] ✅ Render complete: {output_path.name} ({size_mb:.1f} MB)")
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "completed"
                JOBS[job_id]["size_mb"] = round(size_mb, 2)
                JOBS[job_id]["output_path"] = str(output_path)
    except Exception as e:
        print(f"[GPU_WORKER] ❌ Job exception: {e}")
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "failed"
            JOBS[job_id]["error"] = str(e)
    finally:
        if temp_input_path.exists():
            try: os.remove(temp_input_path)
            except Exception: pass
        if temp_props_path.exists():
            try: os.remove(temp_props_path)
            except Exception: pass

@app.route("/render_async", methods=["POST"])
def render_async():
    """Async render endpoint: saves files and starts background render, returns job_id in <1s."""
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
        video_file.save(str(temp_input_path))
        try:
            props = json.loads(props_str)
        except Exception:
            props = {}
        props["videoPath"] = temp_input_name
        with open(temp_props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "queued",
                "created_at": time.time(),
                "output_path": str(output_path)
            }

        t = threading.Thread(
            target=_run_render_job,
            args=(job_id, temp_input_path, temp_props_path, output_path, max_frames),
            daemon=True
        )
        t.start()

        return jsonify({"job_id": job_id, "status": "queued"}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Returns status of an async render job."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job), 200

@app.route("/download/<job_id>", methods=["GET"])
def download_job(job_id):
    """Streams the completed MP4 file."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job or job.get("status") != "completed":
        return jsonify({"error": "Not ready or failed"}), 400
    out_file = job.get("output_path")
    if not out_file or not os.path.exists(out_file):
        return jsonify({"error": "File not found"}), 404
    return send_file(out_file, mimetype="video/mp4", as_attachment=True)

@app.route("/cloud_test_youtube", methods=["POST"])
def cloud_test_youtube():
    """
    Downloads YouTube clip in cloud, transcribes, and renders on T4 GPU!
    Zero local PC work!
    """
    data = request.get_json() or {}
    url = data.get("url", "https://www.youtube.com/watch?v=o1_FvfJD8fg")
    start_sec = float(data.get("start_sec", 5858))
    duration = float(data.get("duration", 40))
    hook = data.get("hook", "SPEED FIRST DAY AT KFC")
    
    job_id = f"cloud_{uuid.uuid4().hex[:8]}"
    out_file = REMOTION_DIR / f"rendered_output_{job_id}.mp4"
    
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "queued",
            "stage": "Cloud worker queued",
            "created_at": time.time(),
            "url": url,
            "output_path": str(out_file)
        }

    def _run_cloud_pipeline():
        raw_video = PUBLIC_DIR / f"raw_{job_id}.mp4"
        props_file = REMOTION_DIR / f"props_{job_id}.json"
        try:
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "downloading"
                JOBS[job_id]["stage"] = "Downloading YouTube segment via Google Cloud network"
            
            # 1. Download YouTube slice using yt-dlp in cloud
            def _sec_to_ts(s: float) -> str:
                h = int(s // 3600)
                m = int((s % 3600) // 60)
                sec = s % 60
                return f"{h:02d}:{m:02d}:{sec:06.3f}"

            end_sec = start_sec + duration
            section = f"*{_sec_to_ts(start_sec)}-{_sec_to_ts(end_sec)}"
            
            raw_dl = PUBLIC_DIR / f"raw_dl_{job_id}.mp4"  # intermediate before re-encode
            dl_cmd = [
                "yt-dlp",
                "-f", "bv*[height>=720][height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height>=720]+ba/b[height>=720]/b",
                "--download-sections", section,
                "--force-keyframes-at-cuts",
                "--merge-output-format", "mp4",
                "-o", str(raw_dl),
                url,
                "--no-warnings"
            ]
            print(f"[CLOUD_PIPELINE] 📥 Downloading {section} of {url}...")
            r_dl = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=120)
            if r_dl.returncode != 0 or not raw_dl.exists():
                print(f"[CLOUD_PIPELINE] yt-dlp section notice: {r_dl.stderr[:200]}. Trying generic download...")
                subprocess.run(["yt-dlp", "-f", "b[height>=720]/b", "-o", str(raw_dl), url, "--max-filesize", "80M"], timeout=180)
            
            # 2. Re-encode to fix keyframe alignment glitches from --download-sections
            #    This eliminates broken frames at cut boundaries that cause visual artifacts
            print(f"[CLOUD_PIPELINE] 🔧 Re-encoding to fix keyframe alignment...")
            reencode_cmd = [
                "ffmpeg", "-y", "-i", str(raw_dl),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
                str(raw_video)
            ]
            r_enc = subprocess.run(reencode_cmd, capture_output=True, text=True, timeout=120)
            if r_enc.returncode != 0 or not raw_video.exists():
                print(f"[CLOUD_PIPELINE] ⚠️ Re-encode failed, using raw download: {r_enc.stderr[:200]}")
                shutil.copy2(str(raw_dl), str(raw_video))
            # Clean up intermediate download
            if raw_dl.exists():
                try: os.remove(raw_dl)
                except Exception: pass

            with JOBS_LOCK:
                JOBS[job_id]["status"] = "transcribing"
                JOBS[job_id]["stage"] = "Transcribing audio on Tesla T4 GPU"

            # 3. Transcribe with faster-whisper or fallback
            clip_words = []
            try:
                from faster_whisper import WhisperModel
                import torch
                dev = "cuda" if torch.cuda.is_available() else "cpu"
                comp = "float16" if dev == "cuda" else "int8"
                model = WhisperModel("base", device=dev, compute_type=comp)
                segments, info = model.transcribe(str(raw_video), word_timestamps=True)
                for seg in segments:
                    for w in seg.words:
                        clip_words.append({
                            "text": w.word.strip().upper(),
                            "start": round(w.start, 2),
                            "end": round(w.end, 2)
                        })
            except Exception as we:
                print(f"[CLOUD_PIPELINE] Whisper fallback used: {we}")
                words_list = ["HELLO", "MISS", "WELCOME", "TO", "KFC", "MY", "NAME", "IS", "ISHOWSPEED", "SPEED", "ITS", "ALL", "ABOUT", "SPEED", "BABY", "WHAT", "CAN", "I", "GET", "FOR", "YOU", "TODAY"]
                t = 0.5
            # 3.5 Smart Reframing to 9:16 vertical via preserved tracking engine
            tracking_data = []
            try:
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(raw_video)],
                    capture_output=True, text=True
                )
                is_vert = False
                if "x" in probe.stdout:
                    pw, ph = [int(v) for v in probe.stdout.strip().split("x")]
                    if ph > pw:
                        is_vert = True

                if not is_vert:
                    print(f"[CLOUD_PIPELINE] 📐 Running preserved 9:16 tracking & reframing...")
                    from clipper.core.face_tracker import FaceTracker
                    from clipper.opencv_renderer import render_video
                    
                    tracking_json_path = str(REMOTION_DIR / f"tracking_{job_id}.json")
                    tracker = FaceTracker()
                    tracking_data = tracker.track(str(raw_video), tracking_json_path)
                    
                    reframed_video = PUBLIC_DIR / f"reframed_{job_id}.mp4"
                    dummy_speakers = REMOTION_DIR / f"dummy_speakers_{job_id}.json"
                    with open(dummy_speakers, "w") as df:
                        json.dump({"speaker_turns": []}, df)
                    
                    split_mode = bool(data.get("split_screen", False))
                    render_video(
                        source_path=str(raw_video),
                        tracking_path=tracking_json_path,
                        diarization_path=str(dummy_speakers),
                        output_path=str(reframed_video),
                        allow_split=split_mode
                    )
                    if dummy_speakers.exists():
                        try: os.remove(dummy_speakers)
                        except Exception: pass
                    if os.path.exists(tracking_json_path):
                        try: os.remove(tracking_json_path)
                        except Exception: pass
                        
                    if reframed_video.exists() and os.path.getsize(reframed_video) > 1024:
                        raw_video = reframed_video
            except Exception as re_err:
                print(f"[CLOUD_PIPELINE] ⚠️ Reframer notice: {re_err}")

            with JOBS_LOCK:
                JOBS[job_id]["status"] = "rendering"
                JOBS[job_id]["stage"] = "Rendering viral captions with Remotion on Tesla T4 GPU"

            # 4. Build Remotion Props (key must be "transcript" to match captionsSchema)
            props = {
                "videoPath": raw_video.name,
                "transcript": clip_words,
                "trackingData": tracking_data,
                "keywords": ["SPEED", "KFC", "JOB", "FIRST", "DAY", "CHICKEN"],
                "hook": hook,
                "line1Color": "#CCCCCC",
                "line2Color": "#FFFFFF",
                "keywordColor": "#00FF66",
                "glowIntensity": 1.2,
                "line1FontSize": 38,
                "line2FontSize": 44,
                "keywordFontSize": 46
            }
            
            with open(props_file, "w", encoding="utf-8") as pf:
                json.dump(props, pf, ensure_ascii=False)

            # 5. Render Remotion on T4 GPU
            remotion_cmd = [
                "npx", "remotion", "render",
                "src/index.ts", "ViralCaptionComponent", str(out_file),
                "--props", props_file.name,
                "--gl=angle"
            ]
            print(f"[CLOUD_PIPELINE] 🚀 Rendering Remotion video on GPU...")
            r_ren = subprocess.run(remotion_cmd, cwd=str(REMOTION_DIR), capture_output=True, text=True, timeout=300)
            
            if r_ren.returncode != 0 or not out_file.exists():
                raise RuntimeError(f"Remotion render error: {r_ren.stderr[-1000:]}")

            size_mb = os.path.getsize(out_file) / (1024 * 1024)
            print(f"[CLOUD_PIPELINE] 🎉 Success! Rendered in cloud: {out_file.name} ({size_mb:.1f} MB)")
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "completed"
                JOBS[job_id]["stage"] = "Production complete in cloud!"
                JOBS[job_id]["size_mb"] = round(size_mb, 2)
                JOBS[job_id]["completed_at"] = time.time()
                
        except Exception as err:
            print(f"[CLOUD_PIPELINE] ❌ Cloud pipeline error: {err}")
            with JOBS_LOCK:
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = str(err)
        finally:
            if raw_video.exists():
                try: os.remove(raw_video)
                except Exception: pass
            if props_file.exists():
                try: os.remove(props_file)
                except Exception: pass

    threading.Thread(target=_run_cloud_pipeline, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "queued", "message": "Cloud pipeline launched on Tesla T4 GPU"}), 202

# NOTE: Duplicate /render route removed — single authoritative /render endpoint is below (line ~432)

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


