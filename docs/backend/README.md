# WindWays Backend

> Backend services and APIs for the WindWays travel platform

## 🏗️ Backend Architecture

```
backend/
├── auth_module/              # Multi-tenant authentication module
│   ├── core/                # Configuration, DI, security utilities
│   ├── domain/              # Business logic, models, services
│   ├── infrastructure/      # Database, external services
│   ├── api/                 # FastAPI routers, middleware, schemas
│   ├── migrations/          # Alembic database migrations
│   └── main.py             # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── setup.py                # Package setup
├── pyproject.toml          # Project configuration
└── Dockerfile              # Backend container
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn auth_module.main:app --reload
```

### Using Docker

```bash
# Build and run backend
docker-compose up backend

# Or run from project root
cd ..
docker-compose up backend
```

## 🔐 Authentication Module

The WindWays authentication module is a production-ready, reusable authentication and authorization system with multi-tenancy support.

### Features

- **Multi-Tenant Architecture**: Support for subdomain, path, and header-based tenant resolution
- **Robust Authentication**: JWT tokens, MFA (TOTP, SMS, Email), social login (Google, Facebook, Apple)
- **Role-Based Access Control**: Hierarchical roles with fine-grained permissions
- **Security Controls**: Rate limiting, account lockout, password policies, audit logging
- **Clean Architecture**: Loosely coupled, dependency injection, repository pattern
- **Production Ready**: Comprehensive error handling, monitoring, health checks

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/forgot-password` - Password reset request
- `POST /api/v1/auth/reset-password` - Password reset
- `POST /api/v1/auth/mfa/setup` - MFA setup
- `POST /api/v1/auth/mfa/verify` - MFA verification
- `POST /api/v1/auth/social/{provider}` - Social login
- `POST /api/v1/auth/logout` - User logout

#### Tenant Management
- `POST /api/v1/tenants` - Create tenant
- `GET /api/v1/tenants/{slug}` - Get tenant
- `PUT /api/v1/tenants/{id}` - Update tenant

#### User Management
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/{id}` - Update user

#### System
- `GET /health` - Health check
- `GET /metrics` - System metrics

## 🛡️ Security Features

### Password Security
- Configurable strength requirements
- Password history prevention
- Breach detection (optional)

### Rate Limiting
- Per-endpoint rate limits
- IP-based and user-based limiting
- Progressive delays

### Account Protection
- Failed attempt tracking
- Account lockout
- Progressive delays

### Audit Logging
- Security event logging
- Immutable audit trail
- Compliance-ready

## 🏢 Multi-Tenancy

The module supports multiple tenant resolution strategies:

### Subdomain Strategy
```
tenant1.windways.com -> tenant1
tenant2.windways.com -> tenant2
```

### Path Strategy
```
windways.com/tenant1/api/v1/auth/login
windways.com/tenant2/api/v1/auth/login
```

### Header Strategy
```
X-Tenant-ID: tenant1
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=auth_module --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m security
pytest -m performance
```

## 📊 Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics
```

### Metrics

- Active users
- Failed logins
- Token validations
- Response times
- Cache hit rates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `60` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | `30` |
| `PASSWORD_MIN_LENGTH` | Minimum password length | `8` |
| `RATE_LIMIT_LOGIN` | Login rate limit | `5/minute` |
| `MAX_FAILED_LOGIN_ATTEMPTS` | Max failed attempts | `5` |

### Feature Flags

- `ENABLE_MFA` - Enable multi-factor authentication
- `ENABLE_SOCIAL_LOGIN` - Enable OAuth providers
- `ENABLE_PASSWORD_RESET` - Enable password reset
- `ENABLE_USER_REGISTRATION` - Enable user registration
- `ENABLE_TENANT_CREATION` - Enable tenant creation

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t windways-backend .

# Run container
docker run -p 8000:8000 windways-backend
```

### Production

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

## 📚 API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🤝 Contributing

1. Follow the project's code style guidelines
2. Write comprehensive tests
3. Update documentation
4. Submit a pull request

### Code Style

- Follow PEP 8
- Use Black for formatting
- Use isort for import sorting
- Add type hints
- Write docstrings

## 📄 License

MIT License - see [LICENSE](../LICENSE) file for details.
