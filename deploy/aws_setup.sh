#!/bin/bash
# ==============================================================================
# Going Merry — AWS Master Cloud Provisioning Script
# Project: 100% Automated AI Video Pipeline & Anti-Ban Distribution
# Target: AWS Lightsail / EC2 (Ubuntu 22.04 / 24.04 LTS)
# Covers:
#   1. Dashboard & Account Management (Flask web app)
#   2. Kaggle Worker Cluster Coordinator (/api/cluster/register)
#   3. Video Ingestion & Output Storage
#   4. Multi-Platform Playwright Uploader with Home Residential SOCKS5 Support
#   5. Live View Tracking & Viral Detection
#   6. Instant Telegram Push Alerts
# ==============================================================================

set -euo pipefail

log_info() { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
log_ok()   { echo -e "\033[1;32m[OK]\033[0m    $*"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
log_fail() { echo -e "\033[1;31m[FAIL]\033[0m  $*" >&2; }

if [ "$(id -u)" -ne 0 ]; then
    log_fail "Please run with sudo: sudo bash $0"
    exit 1
fi

REAL_USER="${SUDO_USER:-ubuntu}"
REAL_HOME=$(eval echo "~${REAL_USER}")
APP_DIR="${REAL_HOME}/ai-video-automation"

echo "=============================================================================="
echo " 🏎️ Launching Going Merry AWS Master Setup (Ubuntu on AWS)"
echo " User: ${REAL_USER} | Target Dir: ${APP_DIR}"
echo "=============================================================================="

# ------------------------------------------------------------------------------
# 1. System Package Updates & Dependencies
# ------------------------------------------------------------------------------
log_info "Step 1/6: Updating package repositories and essential tools..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    git \
    ufw \
    net-tools \
    htop

# ------------------------------------------------------------------------------
# 2. Docker & Docker Compose Installation
# ------------------------------------------------------------------------------
log_info "Step 2/6: Verifying Docker and Docker Compose..."
if ! command -v docker &>/dev/null; then
    log_info "Installing Docker Engine..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    usermod -aG docker "${REAL_USER}"
    log_ok "Docker installed successfully."
else
    log_ok "Docker is already installed."
fi

# ------------------------------------------------------------------------------
# 3. Configure SSH GatewayPorts (CRITICAL FOR RESIDENTIAL SOCKS5 TUNNEL)
# ------------------------------------------------------------------------------
log_info "Step 3/6: Enabling SSH GatewayPorts for Home SOCKS5 Tunnel..."
SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_D_CONFIG="/etc/ssh/sshd_config.d/60-going-merry-gateway.conf"

mkdir -p /etc/ssh/sshd_config.d/
cat << 'EOF' > "${SSHD_D_CONFIG}"
# Going Merry: Allow reverse SSH tunnels (port 1080) to bind across Docker interfaces
GatewayPorts yes
ClientAliveInterval 30
ClientAliveCountMax 6
EOF

# Ensure main sshd_config includes GatewayPorts
if ! grep -q "^GatewayPorts yes" "${SSHD_CONFIG}"; then
    echo "GatewayPorts yes" >> "${SSHD_CONFIG}"
fi

systemctl restart ssh || systemctl restart sshd
log_ok "SSH GatewayPorts enabled (reverse tunnel port 1080 ready for Docker)."

# ------------------------------------------------------------------------------
# 4. Firewall Configuration (UFW)
# ------------------------------------------------------------------------------
log_info "Step 4/6: Configuring firewall rules..."
ufw allow 22/tcp    comment 'SSH'
ufw allow 80/tcp    comment 'HTTP Web Dashboard'
ufw allow 443/tcp   comment 'HTTPS Web Dashboard'
ufw allow 5000/tcp  comment 'Going Merry Flask Internal'
ufw allow 8080/tcp  comment 'noVNC Stream'
ufw --force enable
log_ok "Firewall configured."

# ------------------------------------------------------------------------------
# 5. Clone or Update Going Merry Repository
# ------------------------------------------------------------------------------
log_info "Step 5/6: Setting up Going Merry application code..."
if [ ! -d "${APP_DIR}" ]; then
    log_info "Cloning Going Merry repository..."
    sudo -u "${REAL_USER}" git clone https://github.com/Madalior/ai-video-automation.git "${APP_DIR}"
else
    log_info "Updating existing repository..."
    cd "${APP_DIR}"
    sudo -u "${REAL_USER}" git pull origin main || true
fi

cd "${APP_DIR}"

# ------------------------------------------------------------------------------
# 6. Start Docker Services
# ------------------------------------------------------------------------------
log_info "Step 6/6: Starting Going Merry Master Container on AWS..."
docker compose down || true
docker compose up -d --build

log_ok "Going Merry Master Container is RUNNING!"

IP_ADDR=$(curl -s https://api.ipify.org || hostname -I | awk '{print $1}')

echo ""
echo "=============================================================================="
echo " 🎉 GOING MERRY IS LIVE ON AWS!"
echo "=============================================================================="
echo " 🌐 Web Dashboard URL     : http://${IP_ADDR}:5000"
echo " 📡 Cluster Register URL  : http://${IP_ADDR}:5000/api/cluster/register"
echo ""
echo " 🛡️ TO ENABLE STEALTH RESIDENTIAL UPLOADS (Run on your home PC):"
echo "    ssh -R 0.0.0.0:1080 -i your-key.pem ubuntu@${IP_ADDR}"
echo "=============================================================================="
