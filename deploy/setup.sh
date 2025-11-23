#!/bin/bash
# LuftWay Production Setup Script
# Run this script on a fresh DigitalOcean Droplet

set -euo pipefail

echo "=========================================="
echo "🚀 LuftWay Production Setup"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo ""
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo ""
echo "📦 Installing required packages..."
apt-get install -y \
    curl \
    wget \
    git \
    docker.io \
    docker-compose-plugin \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    nano

# Start and enable Docker
echo ""
echo "🐳 Setting up Docker..."
systemctl start docker
systemctl enable docker

# Configure firewall
echo ""
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# Configure fail2ban
echo ""
echo "🛡️  Configuring fail2ban..."
systemctl start fail2ban
systemctl enable fail2ban

# Create application directory
echo ""
echo "📁 Creating application directory..."
APP_DIR="/opt/luftway"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/backups"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/certbot/conf"
mkdir -p "$APP_DIR/certbot/www"

# Set permissions
chown -R $SUDO_USER:$SUDO_USER "$APP_DIR"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository to $APP_DIR"
echo "2. Copy .env.production.example to .env.production"
echo "3. Fill in all environment variables"
echo "4. Run: ./deploy/deploy.sh"
echo ""
echo "=========================================="

