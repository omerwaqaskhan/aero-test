# SSL/TLS Certificate Setup Guide

This guide explains how to set up SSL/TLS certificates for the LuftWay platform using Let's Encrypt.

## Prerequisites

1. Domain name pointing to your server
2. Port 80 (HTTP) accessible from the internet
3. Root or sudo access on the server
4. Email address for Let's Encrypt notifications

## Quick Setup

### Step 1: Run the SSL Setup Script

```bash
sudo DOMAIN=your-domain.com EMAIL=your-email@example.com ./scripts/setup_ssl.sh
```

### Step 2: Update Nginx Configuration

1. Edit `nginx/nginx.conf`
2. Uncomment the HTTPS server block
3. Replace `your-domain.com` with your actual domain
4. Update SSL certificate paths if needed

### Step 3: Reload Nginx

```bash
sudo nginx -t  # Test configuration
sudo nginx -s reload  # Reload Nginx
```

## Manual Setup

If you prefer to set up certificates manually:

### 1. Install Certbot

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx

# macOS
brew install certbot
```

### 2. Obtain Certificate

```bash
sudo certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d your-domain.com \
  -d www.your-domain.com
```

### 3. Configure Auto-Renewal

Certbot automatically sets up a cron job, but you can verify:

```bash
sudo crontab -l | grep certbot
```

Expected output:
```
0 0,12 * * * certbot renew --quiet --deploy-hook /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh
```

## Certificate Locations

- **Certificate**: `/etc/letsencrypt/live/your-domain.com/fullchain.pem`
- **Private Key**: `/etc/letsencrypt/live/your-domain.com/privkey.pem`
- **Certificate Chain**: `/etc/letsencrypt/live/your-domain.com/chain.pem`

## Testing

### Test SSL Configuration

```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### Verify Certificate

Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com

### Test Auto-Renewal

```bash
sudo certbot renew --dry-run
```

## Troubleshooting

### Certificate Not Obtained

1. **Check DNS**: Ensure domain points to your server
   ```bash
   dig your-domain.com
   ```

2. **Check Port 80**: Ensure HTTP is accessible
   ```bash
   curl -I http://your-domain.com
   ```

3. **Check Nginx**: Ensure `.well-known/acme-challenge/` is accessible
   ```bash
   curl http://your-domain.com/.well-known/acme-challenge/test
   ```

### Certificate Renewal Fails

1. Check renewal logs:
   ```bash
   sudo certbot renew --dry-run --verbose
   ```

2. Check cron job:
   ```bash
   sudo crontab -l
   ```

3. Check certificate expiration:
   ```bash
   sudo certbot certificates
   ```

## Security Best Practices

1. **Use Strong Ciphers**: Already configured in nginx.conf
2. **Enable HSTS**: Already configured in HTTPS server block
3. **Regular Renewal**: Certbot auto-renews certificates
4. **Monitor Expiration**: Set up alerts for certificate expiration

## Production Checklist

- [ ] SSL certificates obtained
- [ ] HTTPS server block configured in nginx.conf
- [ ] HTTP to HTTPS redirect enabled
- [ ] HSTS header configured
- [ ] Auto-renewal cron job active
- [ ] Certificate expiration monitoring set up
- [ ] SSL Labs test passed (A+ rating)

## Notes

- Let's Encrypt certificates expire every 90 days
- Auto-renewal runs twice daily (at midnight and noon)
- Certificates are automatically renewed 30 days before expiration
- No downtime required for renewal (certbot reloads nginx)

