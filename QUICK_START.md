# 🚀 LuftWay - Quick Start Guide

## 🎯 Run This ONE Command

```bash
./fix_and_populate.sh
```

**What it does:**
1. ✅ Fixes all database tables
2. ✅ Verifies everything is working
3. ✅ Starts hotel data scraper (runs ~15-20 min in background)
4. ✅ Shows you how to monitor progress

---

## 📊 Check Status Anytime

```bash
./check_status.sh
```

Shows:
- How many hotels have rooms
- How many hotels have reviews  
- If scraper is still running
- Complete database stats

---

## 📝 What You Have Now

### ✅ **Working Features**
- User authentication (JWT + MFA)
- Hotel search & filtering
- Hotel details pages
- Admin portal
- Revenue tracking (subscriptions, leads, ads)
- Monitoring dashboard
- Advanced web scraping

### ⚠️ **In Progress**
- Hotel data population (scraper running)

### 🔴 **Needed for Production**
See `PRODUCTION_CHECKLIST.md` for detailed steps:
1. **Stripe** - Payment processing (30 min)
2. **HTTPS** - SSL certificates (1 hour)
3. **Email** - SendGrid or AWS SES (30 min)
4. **Secrets** - Move to .env file (15 min)
5. **Backups** - Automated DB backups (30 min)

---

## 🐛 Troubleshooting

### Scraper not working?
```bash
# Check if it's running
docker compose exec backend ps aux | grep rescrape

# Restart it
docker compose exec -d backend python -m search_booking_module.scraping.rescrape_hotels

# Check logs
docker compose logs backend | grep -i error
```

### Database issues?
```bash
# Check tables exist
docker compose exec backend python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT tablename FROM pg_tables WHERE schemaname=\'public\' ORDER BY tablename'))
    for row in result:
        print(row[0])
"
```

### Frontend not loading?
```bash
# Check container status
docker compose ps

# Restart frontend
docker compose restart frontend

# Check logs
docker compose logs frontend
```

### Backend errors?
```bash
# Check logs
docker compose logs backend | tail -100

# Restart backend
docker compose restart backend
```

---

## 📁 Important Files

- `fix_and_populate.sh` - Main setup script
- `check_status.sh` - Quick status checker
- `PRODUCTION_CHECKLIST.md` - Complete production guide
- `docker-compose.yml` - Main configuration
- `.env` - Secrets (create this before production!)

---

## 🔗 Access Your Site

- **Frontend**: http://localhost
- **API Docs**: http://localhost/docs
- **Admin Portal**: http://localhost/admin-portal
- **Monitoring**: http://localhost/monitoring

---

## 💡 Next Steps

1. **Wait 15-20 minutes** for scraper to finish
2. **Run `./check_status.sh`** to verify data is populated
3. **Read `PRODUCTION_CHECKLIST.md`** for production setup
4. **Configure Stripe** (highest priority)
5. **Setup HTTPS** (required for production)
6. **Deploy to production server**

---

## 📞 Common Commands

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f

# Restart a service
docker compose restart backend

# Check database stats
./check_status.sh

# Run scraper manually
docker compose exec backend python -m search_booking_module.scraping.rescrape_hotels

# Access database directly
docker compose exec postgres psql -U luftway_user luftway_auth_dev

# Create admin user
docker compose exec backend python scripts/create_admin_user.py
```

---

## ✅ Success Checklist

- [ ] Ran `./fix_and_populate.sh`
- [ ] Waited 15-20 minutes for scraper
- [ ] Ran `./check_status.sh` - shows 80%+ hotels with rooms
- [ ] Tested login at http://localhost
- [ ] Tested hotel search
- [ ] Tested hotel details page
- [ ] Checked admin portal works
- [ ] Read production checklist

**When all checked** → Ready to configure Stripe and deploy!

---

**Need help?** Check `PRODUCTION_CHECKLIST.md` for detailed instructions.

