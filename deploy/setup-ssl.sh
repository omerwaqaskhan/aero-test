#!/bin/bash
# SSL Certificate Setup Script (Let's Encrypt)
# Run this BEFORE deploying the application

set -euo pipefail

echo "=========================================="
echo "🔒 SSL Certificate Setup (Let's Encrypt)"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check domain
DOMAIN="luftway.com"
EMAIL="your-email@example.com"  # Change this to your email

echo ""
echo "📋 Domain: $DOMAIN"
echo "📧 Email: $EMAIL"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Create directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Start temporary nginx for ACME challenge
echo ""
echo "🌐 Starting temporary nginx for ACME challenge..."

# Create temporary nginx config
cat > /tmp/nginx-acme.conf <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

# Run temporary nginx container
docker run -d \
    --name nginx-acme \
    -p 80:80 \
    -v "$(pwd)/certbot/www:/var/www/certbot:ro" \
    -v /tmp/nginx-acme.conf:/etc/nginx/conf.d/default.conf:ro \
    nginx:alpine

sleep 5

# Request certificate
echo ""
echo "📜 Requesting SSL certificate from Let's Encrypt..."
certbot certonly \
    --webroot \
    --webroot-path="$(pwd)/certbot/www" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Stop temporary nginx
echo ""
echo "🛑 Stopping temporary nginx..."
docker stop nginx-acme
docker rm nginx-acme

# Copy certificates to certbot directory
echo ""
echo "📁 Copying certificates..."
cp -L /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./certbot/conf/live/$DOMAIN/fullchain.pem
cp -L /etc/letsencrypt/live/$DOMAIN/privkey.pem ./certbot/conf/live/$DOMAIN/privkey.pem
cp -L /etc/letsencrypt/live/$DOMAIN/chain.pem ./certbot/conf/live/$DOMAIN/chain.pem

# Set permissions
chmod 644 ./certbot/conf/live/$DOMAIN/fullchain.pem
chmod 600 ./certbot/conf/live/$DOMAIN/privkey.pem
chmod 644 ./certbot/conf/live/$DOMAIN/chain.pem

echo ""
echo "✅ SSL certificates installed!"
echo ""
echo "Note: Certificates expire in 90 days."
echo "Set up auto-renewal with: certbot renew --dry-run"
echo ""
echo "=========================================="

