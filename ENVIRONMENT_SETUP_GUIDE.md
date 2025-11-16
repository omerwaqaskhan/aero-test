# Environment Separation Setup Guide

This guide explains how to use separate Docker Compose configurations for different environments (development, staging, production).

## Overview

The project now has separate Docker Compose override files for each environment:

- **Development**: `docker-compose.dev.yml`
- **Staging**: `docker-compose.staging.yml`
- **Production**: `docker-compose.prod.yml`

## Usage

### Development Environment

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Stop development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

**Features:**
- Hot reload enabled (code changes reflect immediately)
- Debug logging enabled
- Localhost CORS origins allowed
- Sentry disabled
- Development database: `luftway_auth_dev`

### Staging Environment

```bash
# Set environment variables
export CORS_ORIGINS="https://staging.luftway.com"
export SENTRY_DSN="your-sentry-dsn"
export POSTGRES_PASSWORD="strong-staging-password"

# Start staging environment
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

**Features:**
- Production-like configuration
- Sentry enabled (50% sample rate)
- Staging-specific CORS origins
- Resource limits configured
- Staging database: `luftway_auth_staging`

### Production Environment

```bash
# Create .env.prod file with all secrets
cp .env.example .env.prod
# Edit .env.prod with production values

# Load environment variables
export $(cat .env.prod | xargs)

# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Features:**
- Production logging (WARNING level)
- Sentry enabled (10% sample rate for performance)
- Strict CORS (production domains only)
- Resource limits and restart policies
- Production database: `luftway_auth_prod`
- Multiple replicas for high availability

## Environment Variables

### Required for All Environments

```bash
# Database
POSTGRES_DB=luftway_auth_<env>
POSTGRES_USER=luftway_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=<strong-password>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# JWT
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### Development-Specific

```bash
LOG_LEVEL=DEBUG
ENABLE_DEBUG_MODE=true
ENABLE_SENTRY=false
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

### Staging-Specific

```bash
LOG_LEVEL=INFO
ENABLE_SENTRY=true
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.5
CORS_ORIGINS="https://staging.luftway.com"
```

### Production-Specific

```bash
LOG_LEVEL=WARNING
ENABLE_SENTRY=true
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
CORS_ORIGINS="https://luftway.com,https://www.luftway.com"
```

## Database Separation

Each environment uses a separate database:

- **Development**: `luftway_auth_dev`
- **Staging**: `luftway_auth_staging`
- **Production**: `luftway_auth_prod`

This ensures:
- No data mixing between environments
- Safe testing in staging
- Production data protection

## Security Best Practices

### 1. Separate Secrets

**Never** use the same passwords/secrets across environments:

```bash
# Development (can be weaker, but still secure)
POSTGRES_PASSWORD=dev_password_123

# Staging (strong password)
POSTGRES_PASSWORD=Staging_P@ssw0rd_2024!

# Production (very strong, unique password)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 2. Environment Files

Create separate `.env` files:

```bash
# Development
.env.dev

# Staging
.env.staging

# Production
.env.prod  # NEVER commit this!
```

Add to `.gitignore`:
```
.env.prod
.env.staging
*.env.prod
*.env.staging
```

### 3. CORS Configuration

**Development:**
```bash
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
```

**Staging:**
```bash
CORS_ORIGINS="https://staging.luftway.com"
```

**Production:**
```bash
CORS_ORIGINS="https://luftway.com,https://www.luftway.com"
```

## Deployment Workflow

### 1. Development

```bash
# Local development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 2. Staging Deployment

```bash
# On staging server
git pull origin main
docker-compose -f docker-compose.yml -f docker-compose.staging.yml pull
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.staging.yml exec backend alembic upgrade head
```

### 3. Production Deployment

```bash
# On production server
git pull origin main
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Verification

### Check Environment

```bash
# Check which environment is running
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend env | grep SENTRY_ENVIRONMENT

# Check database name
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres psql -U luftway_user -l
```

### Health Check

```bash
# Development
curl http://localhost:8000/health

# Staging
curl https://staging-api.luftway.com/health

# Production
curl https://api.luftway.com/health
```

## Troubleshooting

### Wrong Environment Running

If you see the wrong database or configuration:

```bash
# Stop all containers
docker-compose down

# Start with correct environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Environment Variables Not Loading

```bash
# Check if variables are set
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config | grep -A 5 "environment:"

# Load from file
export $(cat .env.prod | grep -v '^#' | xargs)
```

## Quick Reference

| Command | Development | Staging | Production |
|---------|------------|---------|------------|
| Start | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d` | `docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |
| Stop | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml down` | `docker-compose -f docker-compose.yml -f docker-compose.staging.yml down` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml down` |
| Logs | `docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f` | `docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f` | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f` |
| Database | `luftway_auth_dev` | `luftway_auth_staging` | `luftway_auth_prod` |

