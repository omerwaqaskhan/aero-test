# Enhanced Database Backup Setup Guide

This guide explains how to set up automated database backups with S3 support for the LuftWay platform.

## Features

- ✅ Automated daily backups via cron
- ✅ S3/Cloud Storage support
- ✅ Backup verification
- ✅ Retention policy (configurable)
- ✅ Email notifications (optional)
- ✅ Compressed backups (gzip)

## Quick Setup

### Step 1: Set Up Cron Job

```bash
sudo ./backend/scripts/setup_backup_cron.sh
```

This will:
- Add a daily cron job (runs at 2 AM by default)
- Create log file at `/var/log/luftway-backup.log`
- Make backup script executable

### Step 2: Configure Environment Variables

Add to your `.env` file or system environment:

```bash
# Database Configuration
POSTGRES_DB=luftway_auth_dev
POSTGRES_USER=luftway_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Backup Configuration
BACKUP_DIR=/backups
RETENTION_DAYS=7

# S3 Configuration (optional)
S3_BUCKET=your-backup-bucket
S3_PREFIX=database-backups
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Email Notifications (optional)
NOTIFY_EMAIL=admin@example.com
```

### Step 3: Test Backup

```bash
sudo ./backend/scripts/backup_database_enhanced.sh
```

## Configuration Options

### Backup Schedule

Default schedule is 2 AM daily. To change:

```bash
# Edit cron schedule
sudo crontab -e

# Or set environment variable before running setup
CRON_SCHEDULE="0 3 * * *" sudo ./backend/scripts/setup_backup_cron.sh
```

Common schedules:
- `0 2 * * *` - Daily at 2 AM
- `0 */6 * * *` - Every 6 hours
- `0 2 * * 0` - Weekly on Sunday at 2 AM

### Retention Policy

Set `RETENTION_DAYS` environment variable:
- `7` - Keep backups for 7 days (default)
- `30` - Keep backups for 30 days
- `90` - Keep backups for 90 days

### S3 Configuration

#### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-backup-bucket --region us-east-1
```

#### 2. Set Up IAM Policy

Create IAM user with policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-backup-bucket/*"
    }
  ]
}
```

#### 3. Configure Credentials

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export S3_BUCKET=your-backup-bucket
```

## Monitoring

### View Backup Logs

```bash
# View recent logs
tail -f /var/log/luftway-backup.log

# View last 50 lines
tail -n 50 /var/log/luftway-backup.log

# Search for errors
grep -i error /var/log/luftway-backup.log
```

### Check Cron Job

```bash
# List all cron jobs
crontab -l

# Check cron service status
sudo systemctl status cron  # Ubuntu/Debian
sudo systemctl status crond  # CentOS/RHEL
```

### Verify Backups

```bash
# List local backups
ls -lh /backups/luftway_backup_*.sql.gz

# List S3 backups
aws s3 ls s3://your-backup-bucket/database-backups/

# Test restore (on a test database)
gunzip -c /backups/luftway_backup_YYYYMMDD_HHMMSS.sql.gz | psql -U user -d test_db
```

## Restore from Backup

### Local Backup

```bash
# Decompress and restore
gunzip -c /backups/luftway_backup_YYYYMMDD_HHMMSS.sql.gz | \
  psql -h localhost -U luftway_user -d luftway_auth_dev
```

### S3 Backup

```bash
# Download from S3
aws s3 cp s3://your-backup-bucket/database-backups/luftway_backup_YYYYMMDD_HHMMSS.sql.gz /tmp/

# Decompress and restore
gunzip -c /tmp/luftway_backup_YYYYMMDD_HHMMSS.sql.gz | \
  psql -h localhost -U luftway_user -d luftway_auth_dev
```

## Troubleshooting

### Backup Fails

1. **Check database connection:**
   ```bash
   psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
   ```

2. **Check disk space:**
   ```bash
   df -h /backups
   ```

3. **Check permissions:**
   ```bash
   ls -la /backups
   ```

### S3 Upload Fails

1. **Check AWS credentials:**
   ```bash
   aws sts get-caller-identity
   ```

2. **Check S3 bucket permissions:**
   ```bash
   aws s3 ls s3://your-backup-bucket/
   ```

3. **Check network connectivity:**
   ```bash
   ping s3.amazonaws.com
   ```

### Cron Job Not Running

1. **Check cron service:**
   ```bash
   sudo systemctl status cron
   ```

2. **Check cron logs:**
   ```bash
   sudo grep CRON /var/log/syslog
   ```

3. **Verify cron job exists:**
   ```bash
   crontab -l | grep backup
   ```

## Best Practices

1. **Test Restores Regularly**: Test restore procedure monthly
2. **Monitor Backup Size**: Alert if backup size changes significantly
3. **Use S3 Lifecycle Policies**: Automatically move old backups to Glacier
4. **Encrypt Backups**: Enable S3 server-side encryption
5. **Multiple Backup Locations**: Keep backups in multiple regions
6. **Document Restore Procedure**: Keep restore steps documented

## Security

- Store credentials securely (use secrets management)
- Encrypt backups at rest (S3 encryption)
- Use IAM roles instead of access keys when possible
- Restrict S3 bucket access with bucket policies
- Rotate access keys regularly

## Cost Optimization

- Use S3 Intelligent-Tiering for automatic cost optimization
- Set up lifecycle policies to move old backups to Glacier
- Compress backups (already done with gzip)
- Delete old backups automatically (retention policy)

