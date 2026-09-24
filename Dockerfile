# ==============================================================================
# Going Merry — 100% Cloud-Native Production Dockerfile
# Bundles Python, Playwright Chromium, Virtual Display (Xvfb), noVNC Streamer,
# FFmpeg, Node.js (Remotion), and Flask Dashboard for Mobile Control.
# ==============================================================================
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Avoid interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV SCREEN_WIDTH=1280
ENV SCREEN_HEIGHT=800
ENV SCREEN_DEPTH=24

# 1. Install Virtual Display (Xvfb), VNC, noVNC, window manager, and media tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    fluxbox \
    ffmpeg \
    curl \
    wget \
    git \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js 20 (Required for Remotion video rendering)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir playwright-stealth psutil websockets

# 4. Install Playwright browser binaries
RUN playwright install chromium

# 5. Copy Remotion dependencies if package.json exists
COPY package*.json ./
RUN if [ -f package.json ]; then npm install --legacy-peer-deps; fi

# 6. Copy application source code
COPY . .

# 7. Make startup scripts executable
RUN chmod +x start_cloud.sh 2>/dev/null || true

# 8. Create persistent storage directories
RUN mkdir -p /app/output /app/uploader_profiles /app/instance

# Expose Web Dashboard (5000) and noVNC Mobile Stream (6080)
EXPOSE 5000 6080

CMD ["/bin/bash", "/app/start_cloud.sh"]
