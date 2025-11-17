# Deployment Scripts

Quick reference for deployment scripts.

## Setup (First Time Only)

1. **Initial Server Setup** (`setup.sh`)
   - Installs Docker, certbot, firewall, etc.
   - Run once on a fresh droplet

2. **SSL Certificate Setup** (`setup-ssl.sh`)
   - Gets Let's Encrypt certificates
   - Run before first deployment

3. **Deploy Application** (`deploy.sh`)
   - Builds and starts all services
   - Run after every code update

## Usage

```bash
# First time setup
sudo ./deploy/setup.sh
sudo ./deploy/setup-ssl.sh

# Configure environment
cp .env.production.example .env.production
nano .env.production  # Fill in all values

# Deploy
./deploy/deploy.sh
```

## Script Details

### setup.sh
- Updates system packages
- Installs Docker, certbot, firewall tools
- Configures UFW firewall
- Sets up fail2ban
- Creates application directories

### setup-ssl.sh
- Requests Let's Encrypt SSL certificates
- Stores certificates in `./certbot/conf/`
- Must run BEFORE first deployment

### deploy.sh
- Validates environment variables
- Builds Docker images
- Starts all services
- Waits for health checks
- Shows deployment status

## Troubleshooting

**Services won't start:**
```bash
docker compose -f docker-compose.prod.yml logs
```

**SSL issues:**
```bash
sudo certbot certificates
sudo certbot renew
```

**Environment variables:**
```bash
cat .env.production
```

