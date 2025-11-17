# ⚡ Quick Deployment Checklist

Follow these steps in order to deploy LuftWay to production.

## ✅ Pre-Deployment Checklist

- [ ] DigitalOcean droplet created (4GB RAM recommended)
- [ ] Domain (luftway.com) added to Cloudflare
- [ ] Cloudflare nameservers updated in GoDaddy
- [ ] DNS records configured in Cloudflare (A records pointing to droplet IP)
- [ ] SSH access to droplet working

## 🚀 Deployment Steps

### 1. Initial Server Setup (One-time)
```bash
ssh root@YOUR_DROPLET_IP
cd /opt
git clone YOUR_REPO_URL luftway
cd luftway
sudo ./deploy/setup.sh
```

### 2. Configure Environment
```bash
cp .env.production.example .env.production
nano .env.production
```

**Generate secure passwords:**
```bash
# Database password
openssl rand -base64 32

# Redis password
openssl rand -base64 32

# JWT secret
openssl rand -hex 32
```

**Required values to fill:**
- ✅ `POSTGRES_PASSWORD` (use generated password)
- ✅ `REDIS_PASSWORD` (use generated password)
- ✅ `JWT_SECRET_KEY` (use generated key)
- ✅ `SMTP_HOST` (e.g., smtp.gmail.com)
- ✅ `SMTP_USERNAME` (your email)
- ✅ `SMTP_PASSWORD` (your email app password)
- ✅ `VITE_API_URL` (https://www.luftway.com/api)

### 3. Set Up SSL Certificates
```bash
# Edit email in script first
nano deploy/setup-ssl.sh
# Change: EMAIL="your-email@example.com"

# Run SSL setup
sudo ./deploy/setup-ssl.sh
```

### 4. Deploy Application
```bash
./deploy/deploy.sh
```

### 5. Verify Deployment
```bash
# Check services
docker compose -f docker-compose.prod.yml ps

# Test endpoints
curl https://www.luftway.com/health
curl https://www.luftway.com/api/health

# Visit in browser
# https://www.luftway.com
```

## 🔄 Updates

When you need to update the application:

```bash
cd /opt/luftway
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## 🐛 Common Issues

**"Services won't start"**
- Check logs: `docker compose -f docker-compose.prod.yml logs`
- Verify `.env.production` has all required values
- Check if ports 80/443 are available

**"SSL certificate error"**
- Make sure DNS is pointing to your droplet
- Wait 5-10 minutes after DNS changes
- Check: `sudo certbot certificates`

**"Can't connect to database"**
- Verify `DATABASE_URL` in `.env.production`
- Check postgres container: `docker compose -f docker-compose.prod.yml ps postgres`

## 📞 Need Help?

1. Check logs: `docker compose -f docker-compose.prod.yml logs -f`
2. Verify environment: `cat .env.production`
3. Test connectivity: `curl https://www.luftway.com/health`
4. See full guide: `DEPLOYMENT_GUIDE.md`

## 🎉 Success!

Once deployed, your app is live at:
- **Production**: https://www.luftway.com
- **API Docs**: https://www.luftway.com/docs

**Now go get customers!** 🚀

