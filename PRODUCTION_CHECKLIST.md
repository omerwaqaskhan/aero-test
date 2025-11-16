# 🚀 LuftWay Production Deployment Checklist

## ✅ COMPLETED (Ready!)

- [x] Multi-tenant authentication system
- [x] JWT + MFA + RBAC
- [x] Database schema (all tables created)
- [x] Revenue module tables (subscriptions, leads, listings, ads)
- [x] Hotel search & booking system
- [x] Advanced web scraping (Booking.com, TripAdvisor, etc.)
- [x] Admin portal (user management, hotel management)
- [x] Monitoring dashboard
- [x] Docker containerization
- [x] Nginx reverse proxy
- [x] Frontend (React + Tailwind)
- [x] Automated setup scripts

## 🔴 CRITICAL - Must Do Before Launch (2-3 days)

### 1. **Populate Hotel Data** ✅ IN PROGRESS
```bash
# Run the automated script
./fix_and_populate.sh

# Check progress
./check_status.sh

# Monitor live
docker compose logs -f backend | grep -i "updated\|rooms"
```
**Status**: Scraper running in background (~15-20 min)  
**Goal**: Get 80%+ hotels with rooms and reviews

### 2. **Configure Stripe Payment Processing** 🔴
**Priority**: HIGH  
**Time**: 30 minutes

**Steps**:
1. Create Stripe account at https://stripe.com
2. Get API keys from Dashboard → Developers → API keys
3. Create price IDs for subscription tiers:
   - Premium tier: $9.99/month
   - Pro tier: $29.99/month
   - Enhanced listing: $49.99/month
   - Premium listing: $99.99/month

4. Update `docker-compose.yml`:
```yaml
environment:
  # Add these
  STRIPE_SECRET_KEY: sk_live_... # or sk_test_... for testing
  STRIPE_WEBHOOK_SECRET: whsec_...
  STRIPE_PREMIUM_PRICE_ID: price_...
  STRIPE_PRO_PRICE_ID: price_...
  STRIPE_ENHANCED_PRICE_ID: price_...
  STRIPE_PREMIUM_LISTING_PRICE_ID: price_...
```

5. Setup webhook endpoint:
   - URL: `https://yourdomain.com/api/v1/revenue/stripe/webhook`
   - Events: `customer.subscription.created`, `customer.subscription.updated`, `invoice.payment_succeeded`

### 3. **Setup HTTPS/SSL** 🔴
**Priority**: HIGH  
**Time**: 1 hour

**Option A: Let's Encrypt (Free, Recommended)**
```bash
# Install certbot
docker compose exec nginx apk add certbot certbot-nginx

# Get certificate
docker compose exec nginx certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (add to crontab)
0 0 * * * docker compose exec nginx certbot renew
```

**Option B: CloudFlare (Easiest)**
1. Add domain to CloudFlare
2. Enable "Full (strict)" SSL/TLS
3. CloudFlare handles certificates automatically
4. Point DNS to your server

### 4. **Configure Email Service** 🔴
**Priority**: HIGH  
**Time**: 30 minutes

**Recommended**: SendGrid (12k emails/month free)

1. Create SendGrid account: https://sendgrid.com
2. Get API key
3. Update `docker-compose.yml`:
```yaml
SMTP_HOST: smtp.sendgrid.net
SMTP_PORT: 587
SMTP_USERNAME: apikey
SMTP_PASSWORD: SG.your-api-key-here
EMAIL_FROM: noreply@yourdomain.com
EMAIL_FROM_NAME: LuftWay
```

**Alternative**: AWS SES (cheaper at scale)

### 5. **Move Secrets to .env File** 🔴
**Priority**: HIGH  
**Time**: 15 minutes

```bash
# Create .env file
cat > .env << 'EOF'
# Production Secrets
JWT_SECRET_KEY=<generate-with-openssl-rand-base64-32>
DATABASE_URL=postgresql://user:password@postgres:5432/luftway_auth_dev
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SMTP_PASSWORD=<your-sendgrid-api-key>

# OAuth (optional)
GOOGLE_CLIENT_SECRET=...
FACEBOOK_CLIENT_SECRET=...
EOF

# Update docker-compose.yml
# Add at top level:
#   env_file: .env
```

**Generate secure secrets**:
```bash
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 16  # For passwords
```

## 🟡 IMPORTANT - Should Do Before Launch (1-2 days)

### 6. **Database Backups** 🟡
**Priority**: MEDIUM  
**Time**: 30 minutes

```bash
# Create backup script
cat > backup_database.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U luftway_user luftway_auth_dev | gzip > backups/backup_${DATE}.sql.gz
# Keep only last 7 days
find backups/ -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_database.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /path/to/backup_database.sh
```

### 7. **Setup Monitoring & Error Tracking** 🟡
**Priority**: MEDIUM  
**Time**: 1 hour

**Sentry (Error Tracking)**:
1. Create account: https://sentry.io (free tier)
2. Create Python project
3. Add to `docker-compose.yml`:
```yaml
SENTRY_DSN: https://...@sentry.io/...
```
4. Add to backend requirements.txt: `sentry-sdk[fastapi]==1.39.0`

**Uptime Monitoring**:
- UptimeRobot: https://uptimerobot.com (free, 50 monitors)
- Monitor: `https://yourdomain.com/health`

### 8. **Add Legal Pages** 🟡
**Priority**: MEDIUM  
**Time**: 2 hours

Create these pages (or use generator):
- Terms of Service
- Privacy Policy  
- Cookie Policy
- GDPR Compliance notice

**Tools**:
- https://www.termsfeed.com/
- https://www.iubenda.com/

### 9. **Configure CDN** 🟡
**Priority**: MEDIUM  
**Time**: 1 hour

**CloudFlare (Free, Recommended)**:
1. Add domain to CloudFlare
2. Update nameservers
3. Enable:
   - Auto Minify (JS, CSS, HTML)
   - Brotli compression
   - Browser cache TTL: 1 month
4. Configure caching rules

### 10. **Setup Analytics** 🟡
**Priority**: MEDIUM  
**Time**: 30 minutes

Add to `frontend/web-vite/index.html`:
```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## 🔵 NICE TO HAVE - Post-Launch Improvements

### 11. **CI/CD Pipeline** 🔵
- GitHub Actions for automated testing
- Automated deployments
- Code quality checks

### 12. **Real Booking Integration** 🔵
- Booking.com Affiliate API
- Expedia Partner Solutions
- Direct provider integrations

### 13. **Performance Optimization** 🔵
- Code splitting
- Lazy loading
- Image optimization (WebP)
- Redis caching strategy

### 14. **SEO Optimization** 🔵
- Meta tags
- Open Graph
- Sitemap.xml
- robots.txt
- Schema.org markup

### 15. **OAuth Providers** 🔵
- Google Login
- Facebook Login
- Apple Login

## 📊 Quick Status Check

Run anytime to check status:
```bash
./check_status.sh
```

## 🚀 Deployment Commands

### Initial Setup
```bash
# 1. Run automated setup
./fix_and_populate.sh

# 2. Check status
./check_status.sh

# 3. Monitor scraper
docker compose logs -f backend | grep -i "updated\|rooms"
```

### Production Deployment
```bash
# 1. Pull latest code
git pull origin main

# 2. Build and start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 3. Run migrations (if needed)
docker compose exec backend alembic upgrade head

# 4. Check health
curl https://yourdomain.com/health
```

### Rollback
```bash
# 1. Restore from backup
gunzip < backups/backup_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T postgres psql -U luftway_user luftway_auth_dev

# 2. Restart with previous version
docker compose down
git checkout previous-stable-tag
docker compose up -d
```

## 📝 Environment Variables Summary

### Required for Production
- `JWT_SECRET_KEY` - Strong random string
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `STRIPE_SECRET_KEY` - Stripe API key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `SMTP_PASSWORD` - Email service password
- `POSTGRES_PASSWORD` - Database password
- `REDIS_PASSWORD` - Redis password

### Optional (Recommended)
- `SENTRY_DSN` - Error tracking
- `GOOGLE_CLIENT_SECRET` - Google OAuth
- `FACEBOOK_CLIENT_SECRET` - Facebook OAuth
- Domain name configured in CloudFlare/DNS

## 📞 Support & Resources

- **Backend API Docs**: http://localhost:8000/docs
- **Monitoring Dashboard**: http://localhost/monitoring
- **Admin Portal**: http://localhost/admin-portal

## ✅ Launch Readiness Score

Current: **60%**

To reach 100%:
- [ ] Hotel data populated (currently running) - +15%
- [ ] Stripe configured - +10%
- [ ] HTTPS enabled - +10%
- [ ] Email configured - +5%
- [ ] Secrets moved to .env - +5%
- [ ] Database backups - +5%
- [ ] Monitoring setup - +5%
- [ ] Legal pages added - +5%

**Target for MVP Launch**: 85%+ (First 7 items)

---

**Last Updated**: 2025-11-16
**Next Review**: After hotel data scraping completes (~15-20 min)

