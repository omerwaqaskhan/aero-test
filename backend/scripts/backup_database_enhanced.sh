#!/bin/bash
# Enhanced Database Backup Script for LuftWay
# Features:
# - Automated backups with cron scheduling
# - S3/Cloud Storage support
# - Backup verification
# - Retention policy
# - Email notifications (optional)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration from environment variables
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-luftway_auth_dev}"
DB_USER="${POSTGRES_USER:-luftway_user}"
DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"

# S3 Configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-database-backups}"
S3_REGION="${S3_REGION:-us-east-1}"
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

# Email notification (optional)
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USER="${SMTP_USER:-}"
SMTP_PASS="${SMTP_PASS:-}"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/luftway_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to send email notification
send_notification() {
    local subject="$1"
    local body="$2"
    local status="$3"
    
    if [ -z "$NOTIFY_EMAIL" ]; then
        return 0
    fi
    
    # Check if mail command is available
    if ! command -v mail &> /dev/null && ! command -v sendmail &> /dev/null; then
        warning "Email notification requested but mail/sendmail not available"
        return 0
    fi
    
    # Create email body
    local email_body="LuftWay Database Backup Report
    
Status: $status
Time: $(date)
Database: $DB_NAME
Backup File: $BACKUP_FILE

$body"
    
    # Try to send email (simplified - in production, use proper SMTP)
    if command -v mail &> /dev/null; then
        echo "$email_body" | mail -s "$subject" "$NOTIFY_EMAIL" 2>/dev/null || true
    fi
}

# Function to upload to S3
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        return 0
    fi
    
    log "Uploading backup to S3..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not installed. Install with: pip install awscli or apt-get install awscli"
        return 1
    fi
    
    # Set AWS credentials if provided
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        export AWS_ACCESS_KEY_ID
        export AWS_SECRET_ACCESS_KEY
    fi
    
    # Upload to S3
    local s3_path="s3://${S3_BUCKET}/${S3_PREFIX}/luftway_backup_${TIMESTAMP}.sql.gz"
    
    if aws s3 cp "$COMPRESSED_FILE" "$s3_path" --region "$S3_REGION" 2>/dev/null; then
        log "Backup uploaded to S3: $s3_path"
        
        # Also upload a latest symlink
        aws s3 cp "$COMPRESSED_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/latest.sql.gz" --region "$S3_REGION" 2>/dev/null || true
        
        return 0
    else
        error "Failed to upload backup to S3"
        return 1
    fi
}

# Function to verify backup
verify_backup() {
    log "Verifying backup integrity..."
    
    if [ ! -f "$COMPRESSED_FILE" ]; then
        error "Backup file not found: $COMPRESSED_FILE"
        return 1
    fi
    
    # Check file size (should be > 0)
    local file_size=$(stat -f%z "$COMPRESSED_FILE" 2>/dev/null || stat -c%s "$COMPRESSED_FILE" 2>/dev/null || echo "0")
    if [ "$file_size" -eq 0 ]; then
        error "Backup file is empty"
        return 1
    fi
    
    # Test decompression
    if ! gzip -t "$COMPRESSED_FILE" 2>/dev/null; then
        error "Backup file is corrupted (gzip test failed)"
        return 1
    fi
    
    log "Backup verification passed (size: $(du -h "$COMPRESSED_FILE" | cut -f1))"
    return 0
}

# Main backup function
main() {
    log "╔══════════════════════════════════════════════════════════════╗"
    log "║         LuftWay Database Backup - Enhanced Version          ║"
    log "╚══════════════════════════════════════════════════════════════╝"
    log ""
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    chmod 755 "$BACKUP_DIR"
    
    log "Configuration:"
    log "  Database: $DB_NAME"
    log "  Host: $DB_HOST:$DB_PORT"
    log "  User: $DB_USER"
    log "  Backup Directory: $BACKUP_DIR"
    log "  Retention: $RETENTION_DAYS days"
    if [ -n "$S3_BUCKET" ]; then
        log "  S3 Bucket: $S3_BUCKET"
        log "  S3 Prefix: $S3_PREFIX"
    fi
    log ""
    
    # Perform backup
    log "Starting database backup..."
    if ! PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        -f "$BACKUP_FILE" 2>/dev/null; then
        error "Database backup failed"
        send_notification "LuftWay Backup Failed" "Database backup failed. Please check logs." "FAILED"
        exit 1
    fi
    
    # Compress backup
    log "Compressing backup..."
    if ! gzip "$BACKUP_FILE"; then
        error "Failed to compress backup"
        send_notification "LuftWay Backup Failed" "Failed to compress backup file." "FAILED"
        exit 1
    fi
    
    # Verify backup
    if ! verify_backup; then
        error "Backup verification failed"
        send_notification "LuftWay Backup Failed" "Backup verification failed. Backup may be corrupted." "FAILED"
        exit 1
    fi
    
    log "Backup completed: $COMPRESSED_FILE"
    log "Backup size: $(du -h "$COMPRESSED_FILE" | cut -f1)"
    
    # Upload to S3 if configured
    if [ -n "$S3_BUCKET" ]; then
        if ! upload_to_s3; then
            warning "S3 upload failed, but local backup succeeded"
        fi
    fi
    
    # Remove old backups (local)
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    local deleted_count=$(find "$BACKUP_DIR" -name "luftway_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$deleted_count" -gt 0 ]; then
        log "Deleted $deleted_count old backup(s)"
    else
        log "No old backups to delete"
    fi
    
    # List current backups
    log ""
    log "Current backups:"
    ls -lh "$BACKUP_DIR"/luftway_backup_*.sql.gz 2>/dev/null | tail -5 || log "No backups found"
    
    log ""
    log "╔══════════════════════════════════════════════════════════════╗"
    log "║              ✅ Backup Process Completed!                     ║"
    log "╚══════════════════════════════════════════════════════════════╝"
    
    # Send success notification
    send_notification "LuftWay Backup Successful" "Database backup completed successfully.\n\nBackup: $COMPRESSED_FILE\nSize: $(du -h "$COMPRESSED_FILE" | cut -f1)" "SUCCESS"
    
    exit 0
}

# Run main function
main "$@"

