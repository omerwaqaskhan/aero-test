# WindWays Platform - Docker Configuration

This document explains how to use Docker Compose with the WindWays platform, following the latest [Docker Compose best practices](https://docs.docker.com/compose/).

## 🐳 Docker Compose Files

### Core Files
- **`docker-compose.yml`** - Main configuration file (no version field needed in latest Compose)
- **`docker-compose.override.yml`** - Development overrides (automatically loaded)
- **`docker-compose.prod.yml`** - Production configuration

### Key Features
- **Multi-stage builds** for optimized images
- **Health checks** for all services
- **Resource limits** and reservations
- **Custom network** for service isolation
- **Named volumes** for data persistence
- **Security best practices** (non-root users, secrets management)

## 🚀 Quick Start

### Development Environment
```bash
# Start all services in development mode
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Production Environment
```bash
# Start with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3
```

## 🏗️ Services Architecture

### Backend Service
- **Image**: Multi-stage build with production/development targets
- **Port**: 8000
- **Health Check**: HTTP endpoint `/health`
- **Resources**: 1GB memory, 0.5 CPU (production)
- **Features**: Auto-reload in development, multiple workers in production

### Frontend Service
- **Image**: React + Vite with optimized build
- **Port**: 3000
- **Health Check**: HTTP endpoint `/`
- **Resources**: 512MB memory, 0.25 CPU (production)
- **Features**: Hot reload in development, optimized build in production

### Database Services
- **PostgreSQL**: Version 16 with Alpine Linux
- **Redis**: Version 7 with authentication
- **Health Checks**: Built-in database health checks
- **Persistence**: Named volumes for data

### Nginx Reverse Proxy
- **Load Balancing**: Between backend and frontend
- **SSL Termination**: Ready for HTTPS
- **Health Checks**: Custom health endpoint

## 🔧 Configuration

### Environment Variables

#### Development (docker-compose.override.yml)
```yaml
# Automatically loaded for development
LOG_LEVEL: DEBUG
ENABLE_DEBUG_MODE: true
```

#### Production (docker-compose.prod.yml)
```yaml
# Use environment variables for secrets
JWT_SECRET_KEY: ${JWT_SECRET_KEY}
DATABASE_URL: ${DATABASE_URL}
REDIS_URL: ${REDIS_URL}
```

### Resource Management
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## 🌐 Networking

### Custom Network
- **Name**: `windways-network`
- **Driver**: Bridge
- **Subnet**: `172.20.0.0/16`
- **Isolation**: Services communicate through internal network

### Port Mapping
- **Frontend**: `3000:3000`
- **Backend**: `8000:8000`
- **PostgreSQL**: `5432:5432` (dev: `5433:5432`)
- **Redis**: `6379:6379` (dev: `6380:6379`)
- **Nginx**: `80:80`, `443:443`

## 💾 Data Persistence

### Named Volumes
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
```

### Data Directory Structure
```
data/
├── postgres/          # PostgreSQL data
└── redis/            # Redis data
```

## 🔒 Security Features

### Container Security
- **Non-root users**: All services run as non-root
- **Read-only volumes**: Configuration files mounted as read-only
- **Resource limits**: Prevent resource exhaustion
- **Network isolation**: Custom network for service communication

### Secrets Management
```bash
# Create .env file for production secrets
JWT_SECRET_KEY=your-production-secret
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://:password@host:6379/0
```

## 🛠️ Development Workflow

### Local Development
```bash
# Start development environment
docker-compose up --build

# Run tests
docker-compose exec backend pytest

# Access database
docker-compose exec postgres psql -U windways_user -d windways_auth

# View logs
docker-compose logs -f backend
```

### Database Migrations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Code Quality
```bash
# Format code
docker-compose exec backend black auth_module/

# Lint code
docker-compose exec backend flake8 auth_module/

# Type checking
docker-compose exec backend mypy auth_module/
```

## 🚀 Production Deployment

### Environment Setup
```bash
# Create production environment file
cp .env.example .env.prod

# Edit with production values
nano .env.prod
```

### Deployment Commands
```bash
# Deploy to production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale backend=3

# Update services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Monitoring
```bash
# View service status
docker-compose ps

# View resource usage
docker stats

# View logs
docker-compose logs -f --tail=100
```

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :3000

# Use different ports in override file
ports:
  - "3001:3000"
```

#### Permission Issues
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data/
```

#### Service Dependencies
```bash
# Check service health
docker-compose ps

# Restart specific service
docker-compose restart backend
```

### Debugging
```bash
# Access container shell
docker-compose exec backend bash

# View container logs
docker-compose logs backend

# Inspect container
docker inspect windways-backend
```

## 📊 Performance Optimization

### Image Optimization
- **Multi-stage builds**: Separate build and runtime environments
- **Layer caching**: Optimized layer ordering
- **Alpine Linux**: Minimal base images
- **Standalone builds**: Next.js optimized output

### Resource Tuning
```yaml
# Adjust based on your hardware
deploy:
  resources:
    limits:
      memory: 2G      # Increase for high traffic
      cpus: '1.0'     # Increase for CPU-intensive operations
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
# Build and test
- name: Build and test
  run: |
    docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
    docker-compose exec backend pytest
    docker-compose exec frontend npm test
```

### Production Deployment
```yaml
# Deploy to production
- name: Deploy to production
  run: |
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Next.js Docker Deployment](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/)

---

**WindWays Platform** - Modern, scalable, and production-ready Docker configuration! 🌪️🐳
