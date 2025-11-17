# 🚀 LuftWay Production Deployment Guide

Complete guide to deploy LuftWay to DigitalOcean Droplet with Cloudflare DNS/CDN.

## 📋 Prerequisites

- DigitalOcean account
- Domain name (luftway.com) registered on GoDaddy
- Cloudflare account (free)
- SSH access to your DigitalOcean droplet

## 🎯 Architecture

- **DigitalOcean Droplet**: Hosts Docker containers (PostgreSQL, Redis, FastAPI, React, Nginx)
- **Cloudflare**: DNS management, CDN, DDoS protection, SSL (optional - we use Let's Encrypt)

## 📦 Step 1: Create DigitalOcean Droplet

1. Go to [DigitalOcean](https://www.digitalocean.com/)
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: 
     - Minimum: 2GB RAM / 1 vCPU ($12/month) - for testing
     - Recommended: 4GB RAM / 2 vCPU ($24/month) - for production
   - **Region**: Choose closest to your users
   - **Authentication**: SSH keys (recommended) or password
   - **Hostname**: `luftway-production`

3. Note your droplet's IP address

## 🌐 Step 2: Configure Cloudflare DNS

1. Sign up at [Cloudflare](https://www.cloudflare.com/) (free)
2. Add your site: `luftway.com`
3. Cloudflare will scan your DNS records from GoDaddy
4. Update nameservers in GoDaddy:
   - Go to GoDaddy → Domain Settings → Nameservers
   - Replace with Cloudflare nameservers (e.g., `ns1.cloudflare.com`, `ns2.cloudflare.com`)
5. In Cloudflare DNS, add/verify these records:
   ```
   Type    Name    Content              Proxy
   A       @       YOUR_DROPLET_IP      Yes (orange cloud)
   A       www     YOUR_DROPLET_IP       Yes (orange cloud)
   ```
6. **SSL/TLS Settings**:
   - Go to SSL/TLS → Overview
   - Set to **"Full"** (not "Full (strict)" - we use Let's Encrypt)
   - This enables Cloudflare CDN and DDoS protection

## 🖥️ Step 3: Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

Run the setup script:
```bash
# Clone your repository
cd /opt
git clone YOUR_REPO_URL luftway
cd luftway

# Make scripts executable
chmod +x deploy/*.sh

# Run initial setup
sudo ./deploy/setup.sh
```

## 🔐 Step 4: Configure Environment Variables

1. Copy the example file:
```bash
cp .env.production.example .env.production
```

2. Edit `.env.production` and fill in ALL values:
```bash
nano .env.production
```

**Critical values to set:**
- `POSTGRES_PASSWORD`: Generate strong password: `openssl rand -base64 32`
- `REDIS_PASSWORD`: Generate strong password: `openssl rand -base64 32`
- `JWT_SECRET_KEY`: Generate: `openssl rand -hex 32`
- `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Your email service credentials
- `VITE_API_URL`: `https://www.luftway.com/api`

## 🔒 Step 5: Set Up SSL Certificates

**Before deploying**, get SSL certificates:

```bash
# Edit the email in setup-ssl.sh first
nano deploy/setup-ssl.sh

# Run SSL setup
sudo ./deploy/setup-ssl.sh
```

This will:
- Request Let's Encrypt certificates
- Store them in `./certbot/conf/live/luftway.com/`

## 🚀 Step 6: Deploy Application

```bash
# Deploy everything
./deploy/deploy.sh
```

This will:
- Build Docker images
- Start all services
- Wait for health checks
- Show status

## ✅ Step 7: Verify Deployment

1. **Check services are running:**
```bash
docker compose -f docker-compose.prod.yml ps
```

2. **Check logs:**
```bash
docker compose -f docker-compose.prod.yml logs -f
```

3. **Test endpoints:**
```bash
curl https://www.luftway.com/health
curl https://www.luftway.com/api/health
```

4. **Visit in browser:**
   - https://www.luftway.com
   - https://www.luftway.com/docs (API documentation)

## 🔄 Step 8: Set Up Auto-Renewal for SSL

SSL certificates expire in 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab (runs twice daily, renews if <30 days left)
sudo crontab -e
# Add this line:
0 0,12 * * * certbot renew --quiet --deploy-hook "docker compose -f /opt/luftway/docker-compose.prod.yml restart nginx"
```

## 📊 Monitoring & Maintenance

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Update Application
```bash
cd /opt/luftway
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Backup Database
```bash
# Manual backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U luftway_user luftway_prod > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose -f docker-compose.prod.yml exec -T postgres psql -U luftway_user luftway_prod < backups/backup_YYYYMMDD_HHMMSS.sql
```

### Set Up Automated Backups
```bash
# Add to crontab
sudo crontab -e
# Add this line (daily at 2 AM):
0 2 * * * cd /opt/luftway && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U luftway_user luftway_prod > backups/backup_$(date +\%Y\%m\%d).sql && find backups -name "backup_*.sql" -mtime +7 -delete
```

## 🛡️ Security Checklist

- [x] Firewall configured (UFW)
- [x] Fail2ban installed
- [x] Strong passwords set
- [x] SSL certificates installed
- [x] Security headers configured
- [x] Rate limiting enabled
- [x] Database backups scheduled
- [ ] SSH key authentication (disable password auth)
- [ ] Regular security updates

### Disable Password SSH (Recommended)
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PermitRootLogin no (create a non-root user first)

# Restart SSH
sudo systemctl restart sshd
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check if ports are in use
sudo netstat -tulpn | grep -E ':(80|443|5432|6379)'
```

### SSL certificate issues
```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew
```

### Database connection issues
```bash
# Check database is running
docker compose -f docker-compose.prod.yml ps postgres

# Check connection
docker compose -f docker-compose.prod.yml exec postgres psql -U luftway_user -d luftway_prod
```

### High memory usage
```bash
# Check resource usage
docker stats

# Adjust limits in docker-compose.prod.yml
```

## 📈 Performance Optimization

### Cloudflare Settings
1. **Caching**: Enable caching for static assets
2. **Auto Minify**: Enable for JS, CSS, HTML
3. **Brotli**: Enable compression
4. **Always Use HTTPS**: Enable
5. **HTTP/2**: Enable
6. **HTTP/3 (QUIC)**: Enable if available

### Database Optimization
```sql
-- Connect to database
docker compose -f docker-compose.prod.yml exec postgres psql -U luftway_user -d luftway_prod

-- Check slow queries
-- Add indexes as needed
```

## 💰 Cost Estimate

**Monthly costs:**
- DigitalOcean Droplet (4GB): $24/month
- Domain (GoDaddy): ~$15/year (~$1.25/month)
- Cloudflare: **FREE**
- **Total: ~$25/month**

## 📞 Support

If you encounter issues:
1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify environment variables: `cat .env.production`
3. Test connectivity: `curl https://www.luftway.com/health`
4. Check Cloudflare dashboard for any issues

## 🎉 You're Live!

Your application is now deployed and accessible at:
- **Production URL**: https://www.luftway.com
- **API Docs**: https://www.luftway.com/docs

Next steps:
1. Test all functionality
2. Set up monitoring (optional: UptimeRobot, Pingdom)
3. Configure backups
4. Set up error tracking (optional: Sentry)
5. **START GETTING CUSTOMERS!** 🚀

