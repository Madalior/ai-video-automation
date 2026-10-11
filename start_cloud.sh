#!/bin/bash
# ==============================================================================
# Going Merry — Cloud Startup Script
# Boots up Virtual Display (Xvfb), noVNC WebSocket Stream, and Flask Dashboard.
# ==============================================================================

set -e

echo "========================================================"
echo "  🚀 STARTING GOING MERRY CLOUD PLATFORM"
echo "========================================================"

# Default display settings if not defined
SCREEN_WIDTH=${SCREEN_WIDTH:-1280}
SCREEN_HEIGHT=${SCREEN_HEIGHT:-800}
SCREEN_DEPTH=${SCREEN_DEPTH:-24}
DISPLAY_NUM=${DISPLAY_NUM:-99}

export DISPLAY=:${DISPLAY_NUM}

# 1. Clean up any existing lockfiles from previous container restarts
rm -f /tmp/.X${DISPLAY_NUM}-lock /tmp/.X11-unix/X${DISPLAY_NUM} 2>/dev/null || true

# 2. Start Xvfb (Virtual Screen in RAM)
echo "🖥️ Starting Xvfb Virtual Framebuffer on :${DISPLAY_NUM} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})..."
Xvfb :${DISPLAY_NUM} -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH} -ac +extension GLX +render -noreset &
sleep 1

# 3. Start Fluxbox (Window Manager to ensure popups & active windows focus properly)
echo "🪟 Starting Fluxbox window manager..."
mkdir -p /root/.fluxbox
cat << 'EOF' > /root/.fluxbox/apps
[app] (name=.*)
  [Maximized] {yes}
[end]
EOF
fluxbox &
sleep 1

# 4. Start x11vnc (Captures the Xvfb display to VNC on port 5900)
echo "📡 Starting x11vnc server on port 5900..."
x11vnc -display :${DISPLAY_NUM} -nopw -listen 127.0.0.1 -xkb -forever -shared &
sleep 1

# 5. Start websockify / noVNC (Streams VNC to HTML5 on port 6080 for Mobile Phone access)
echo "🌐 Starting noVNC HTML5 WebSocket server on port 6080..."
# Locate novnc web directory
NOVNC_DIR="/usr/share/novnc"
if [ ! -d "$NOVNC_DIR" ]; then
    NOVNC_DIR="/usr/local/share/novnc"
fi
websockify --web="$NOVNC_DIR" 6080 127.0.0.1:5900 &
sleep 1

# 5b. Start Nginx reverse proxy (Routes /vnc/, /websockify, and proxies web app to 5001)
echo "🔀 Configuring and starting Nginx reverse proxy on port 5000..."
if ! command -v nginx >/dev/null 2>&1; then
    apt-get update -qq && apt-get install -y -qq --no-install-recommends nginx
fi

mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
if [ -f "/app/deploy/nginx_cloud.conf" ]; then
    cp /app/deploy/nginx_cloud.conf /etc/nginx/sites-available/default
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
fi

nginx -t || true
service nginx restart 2>/dev/null || nginx 2>/dev/null || true

echo "========================================================"
echo "  ✅ VIRTUAL DISPLAY & REVERSE PROXY READY"
echo "  noVNC Stream available at: /vnc/vnc.html"
echo "  Flask Dashboard proxied on: http://0.0.0.0:5000 -> 127.0.0.1:5001"
echo "========================================================"

# 6. Initialize database tables if needed
python -c "from web_app.app import app, db; app.app_context().push(); db.create_all()" || true

# 6b. Ensure Remotion video rendering dependencies are ready
if [ -d "/app/clipper/remotion" ] && [ ! -d "/app/clipper/remotion/node_modules/@remotion" ]; then
    echo "📦 Initializing Remotion rendering dependencies..."
    (cd /app/clipper/remotion && npm install --legacy-peer-deps && npx remotion browser ensure) || true
fi

# 6c. Start Background Queue Worker Daemon (Flowchart: WORKERS layer)
echo "👷 Starting Background Queue Worker Daemon (worker.py)..."
mkdir -p /app/instance
python -u /app/worker.py > /app/instance/worker.log 2>&1 &

# 7. Start the Web Dashboard on 127.0.0.1:5001 (proxied by Nginx on port 5000)
if command -v gunicorn >/dev/null 2>&1; then
    exec gunicorn --bind 127.0.0.1:5001 --workers 1 --threads 8 --timeout 120 "web_app.app:create_app()"
else
    exec python -c "from web_app.app import app; app.run(host='127.0.0.1', port=5001, threaded=True)"
fi

