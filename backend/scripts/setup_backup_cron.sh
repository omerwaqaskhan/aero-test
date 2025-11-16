#!/bin/bash
# Setup automated database backup cron job
# This script sets up a daily backup cron job

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Automated Database Backup Cron Job Setup                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Error: This script must be run as root${NC}"
    echo "   Please run: sudo $0"
    exit 1
fi

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_database_enhanced.sh"
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"  # Default: 2 AM daily

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}❌ Error: Backup script not found: $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Make sure backup script is executable
chmod +x "$BACKUP_SCRIPT"

# Create cron job entry
CRON_JOB="$CRON_SCHEDULE $BACKUP_SCRIPT >> /var/log/luftway-backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
    read -p "Do you want to update it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab -
        # Add new cron job
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo -e "${GREEN}✅ Cron job updated${NC}"
    else
        echo -e "${GREEN}✅ Keeping existing cron job${NC}"
    fi
else
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✅ Cron job added${NC}"
fi

# Create log directory
mkdir -p /var/log
touch /var/log/luftway-backup.log
chmod 644 /var/log/luftway-backup.log

echo ""
echo -e "${GREEN}📋 Cron Job Details:${NC}"
echo "   Schedule: $CRON_SCHEDULE"
echo "   Script: $BACKUP_SCRIPT"
echo "   Log: /var/log/luftway-backup.log"
echo ""

# Display current cron jobs
echo -e "${GREEN}📜 Current Cron Jobs:${NC}"
crontab -l | grep -E "(luftway|backup)" || echo "   No matching cron jobs found"
echo ""

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "   1. Configure environment variables in /etc/environment or .env file:"
echo "      - POSTGRES_PASSWORD"
echo "      - S3_BUCKET (optional, for cloud storage)"
echo "      - AWS_ACCESS_KEY_ID (optional)"
echo "      - AWS_SECRET_ACCESS_KEY (optional)"
echo ""
echo "   2. Test the backup manually:"
echo "      sudo $BACKUP_SCRIPT"
echo ""
echo "   3. Monitor backup logs:"
echo "      tail -f /var/log/luftway-backup.log"
echo ""

