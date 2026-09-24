# Going Merry & Clipper 🚀
### 100% Cloud-Native Multi-Account Video Automation & Clipping Factory

An autonomous, 24/7 cloud content factory that monitors livestreams, extracts viral moments with Whisper and LLMs, generates 9:16 vertical shorts with Remotion & FFmpeg, and distributes them across social platforms with multi-account session isolation.

---

## ⚡ Architecture & Features

### 🎬 Autonomous AI Clipping Engine (`clipper/`)
- **Stream Auto-Monitoring:** Automatically monitors streamers and creators via `yt-dlp`.
- **Speech-to-Text:** Local Whisper AI transcription with word-level precision timestamps.
- **Viral Hook Detection:** LLM-based hook scoring (Gemini Flash / NVIDIA NIM / Groq).
- **Face Tracking & Smart Crop:** YOLOv8 face detection (`yolov8n-face.pt`) for dynamic 9:16 vertical framing.
- **Split-Screen Composition:** Dual-box layout for gameplay, reactions, and podcast interviews.
- **High-Production Subtitles:** Animated captions rendered with Remotion and FFmpeg.
- **Audio Ducking:** Automatic background music mixing and trending audio matching.

### 📱 Mobile Web Control Dashboard (`web_app/`)
- **Remote Mobile Touch Authentication:** Touchscreen browser login streamed to your mobile phone via `noVNC` on virtual display (`Xvfb`). Connect 30 accounts with Google 2FA approval directly from your phone.
- **Persistent Profiles:** Browser state, cookies, and tokens stored per account in `/uploader_profiles/`.
- **Anti-Flag Sequential Scheduler:** Posts are queued with randomized 20–30 minute human jitter to prevent datacenter IP bans.
- **YouTube API & Social Publishing:** Official YouTube Data API v3 OAuth + Playwright stealth automation for Instagram and TikTok.

---

## 📁 Repository Structure

```
.
├── web_app/               # Flask Web Dashboard & Mobile noVNC UI
│   ├── app.py             # Application factory & setup
│   ├── models.py          # Database models (User, Clip, SocialAccount, etc.)
│   ├── routes/            # Dashboard, Clips, Platform Auth, and Pipeline API
│   ├── static/            # CSS styles and frontend assets
│   └── templates/         # Mobile touch-enabled templates
│
├── clipper/               # AI Video Processing & Clipping Pipeline
│   ├── core/              # 22 modular processors (transcriber, face tracker, etc.)
│   ├── remotion/          # React/Remotion dynamic caption composition
│   ├── uploader/          # Multi-account dispatcher & sequential scheduler
│   └── utils/             # Downloader and LLM routing utilities
│
├── going_merry.py         # Unified end-to-end CLI video pipeline
├── yolov8n-face.pt        # YOLOv8 neural network weights for face tracking
├── Dockerfile             # Production Ubuntu Jammy + Playwright + Xvfb + noVNC
├── docker-compose.yml     # Cloud deployment specification (Ports 80 & 8080)
├── start_cloud.sh         # Cloud virtual display & service bootstrapper
└── requirements.txt       # Python production dependencies
```

---

## 🚀 Cloud Deployment

```bash
# 1. Clone repository
git clone https://github.com/Madalior/ai-video-automation.git
cd ai-video-automation

# 2. Launch production stack in background
docker compose up -d --build
```
Access dashboard at `http://<your-server-ip>` or via your custom Cloudflare domain!
