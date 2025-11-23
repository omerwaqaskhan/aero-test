#!/bin/bash
# SSL/TLS Certificate Setup Script for LuftWay
# This script sets up Let's Encrypt certificates using certbot

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     SSL/TLS Certificate Setup for LuftWay Platform          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
DOMAIN="${DOMAIN:-}"
EMAIL="${EMAIL:-}"
WEBROOT_PATH="${WEBROOT_PATH:-/var/www/certbot}"
CERTBOT_DIR="${CERTBOT_DIR:-/etc/letsencrypt}"
RENEWAL_HOOK="${RENEWAL_HOOK:-/etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Error: This script must be run as root${NC}"
    echo "   Please run: sudo $0"
    exit 1
fi

# Check if domain is provided
if [ -z "$DOMAIN" ]; then
    echo -e "${YELLOW}⚠️  Warning: DOMAIN environment variable not set${NC}"
    echo "   Usage: DOMAIN=example.com EMAIL=admin@example.com $0"
    echo ""
    read -p "Enter your domain name (e.g., luftway.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}❌ Error: Domain name is required${NC}"
        exit 1
    fi
fi

# Check if email is provided
if [ -z "$EMAIL" ]; then
    echo -e "${YELLOW}⚠️  Warning: EMAIL environment variable not set${NC}"
    read -p "Enter your email address for Let's Encrypt notifications: " EMAIL
    if [ -z "$EMAIL" ]; then
        echo -e "${RED}❌ Error: Email address is required${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}📋 Configuration:${NC}"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo "   Webroot: $WEBROOT_PATH"
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Installing certbot...${NC}"
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        yum install -y certbot python3-certbot-nginx
    elif command -v brew &> /dev/null; then
        brew install certbot
    else
        echo -e "${RED}❌ Error: Could not detect package manager${NC}"
        echo "   Please install certbot manually: https://certbot.eff.org/"
        exit 1
    fi
    echo -e "${GREEN}✅ Certbot installed${NC}"
else
    echo -e "${GREEN}✅ Certbot is already installed${NC}"
fi

# Create webroot directory
echo -e "${YELLOW}📁 Creating webroot directory...${NC}"
mkdir -p "$WEBROOT_PATH"
chmod 755 "$WEBROOT_PATH"
echo -e "${GREEN}✅ Webroot directory created${NC}"

# Create renewal hook directory
echo -e "${YELLOW}📁 Creating renewal hook directory...${NC}"
mkdir -p "$(dirname "$RENEWAL_HOOK")"
chmod 755 "$(dirname "$RENEWAL_HOOK")"

# Create renewal hook script
cat > "$RENEWAL_HOOK" << 'EOF'
#!/bin/bash
# Nginx reload hook for certbot renewal
# This script is called after certificate renewal

echo "Reloading Nginx after certificate renewal..."
if command -v nginx &> /dev/null; then
    nginx -t && nginx -s reload
    echo "Nginx reloaded successfully"
else
    echo "Warning: Nginx not found, skipping reload"
fi
EOF

chmod +x "$RENEWAL_HOOK"
echo -e "${GREEN}✅ Renewal hook created${NC}"

# Check if certificate already exists
if [ -d "$CERTBOT_DIR/live/$DOMAIN" ]; then
    echo -e "${YELLOW}⚠️  Certificate for $DOMAIN already exists${NC}"
    read -p "Do you want to renew it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🔄 Renewing certificate...${NC}"
        certbot renew --cert-name "$DOMAIN"
        echo -e "${GREEN}✅ Certificate renewed${NC}"
    else
        echo -e "${GREEN}✅ Using existing certificate${NC}"
    fi
else
    # Obtain new certificate
    echo -e "${YELLOW}🔐 Obtaining SSL certificate for $DOMAIN...${NC}"
    echo -e "${YELLOW}   Note: Make sure your domain points to this server and port 80 is accessible${NC}"
    echo ""
    
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT_PATH" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        -d "$DOMAIN" \
        -d "www.$DOMAIN" || {
        echo -e "${RED}❌ Error: Failed to obtain certificate${NC}"
        echo "   Make sure:"
        echo "   1. Domain DNS points to this server"
        echo "   2. Port 80 is open and accessible"
        echo "   3. Nginx is configured to serve /.well-known/acme-challenge/"
        exit 1
    }
    
    echo -e "${GREEN}✅ Certificate obtained successfully${NC}"
fi

# Display certificate information
echo ""
echo -e "${GREEN}📜 Certificate Information:${NC}"
echo "   Certificate: $CERTBOT_DIR/live/$DOMAIN/fullchain.pem"
echo "   Private Key: $CERTBOT_DIR/live/$DOMAIN/privkey.pem"
echo "   Expires: $(openssl x509 -enddate -noout -in "$CERTBOT_DIR/live/$DOMAIN/cert.pem" | cut -d= -f2)"
echo ""

# Set up auto-renewal cron job
echo -e "${YELLOW}⏰ Setting up auto-renewal cron job...${NC}"
CRON_JOB="0 0,12 * * * certbot renew --quiet --deploy-hook $RENEWAL_HOOK"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "certbot renew"; then
    echo -e "${GREEN}✅ Auto-renewal cron job already exists${NC}"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✅ Auto-renewal cron job added${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✅ SSL Setup Complete!                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "   1. Update nginx.conf to use SSL certificates"
echo "   2. Configure HTTPS server block"
echo "   3. Add HTTP to HTTPS redirect"
echo "   4. Test SSL configuration: openssl s_client -connect $DOMAIN:443"
echo "   5. Verify certificate: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""

