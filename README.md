# WindWays - Travel Platform

> A comprehensive meta-search and booking comparison platform with AI-powered trip planning, experiences, and multi-tenant features for travel agencies and hotels.

## 🌪️ About WindWays

WindWays is a modern travel platform that aggregates accommodation offers from multiple providers, enriches results with reviews and local experiences, and adds value through AI-powered itinerary planning and personalization. The platform includes multi-tenant portals for agencies and hotels with comprehensive authentication and authorization systems.

## 🏗️ Project Structure

```
windways/
├── backend/                 # Backend API and services
│   ├── auth_module/        # Multi-tenant authentication module
│   ├── requirements.txt    # Python dependencies
│   ├── setup.py           # Package setup
│   ├── pyproject.toml     # Project configuration
│   └── Dockerfile         # Backend container
├── frontend/               # Frontend applications (coming soon)
├── dev-phases/            # Development documentation
├── scripts/               # Setup and utility scripts
├── .github/               # CI/CD workflows
├── docker-compose.yml     # Full stack orchestration
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/windways/windways.git
cd windways

# Development environment
docker-compose up --build

# Production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# The API will be available at http://localhost:8000
# Frontend will be available at http://localhost:3000
# API documentation at http://localhost:8000/docs
```

> **Note**: We use the latest Docker Compose specification (no version field) following [Docker Compose best practices](https://docs.docker.com/compose/). See [DOCKER.md](DOCKER.md) for detailed Docker configuration.

### Local Development

```bash
# Setup backend
cd backend
./scripts/setup.sh

# Start database services
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start development server
uvicorn auth_module.main:app --reload
```

## 🔧 Backend Services

### Authentication Module

The WindWays authentication module provides:

- **Multi-tenant architecture** with subdomain, path, and header-based resolution
- **Robust authentication** with JWT tokens, MFA, and social login
- **Role-based access control** with hierarchical permissions
- **Security controls** including rate limiting, account lockout, and audit logging
- **Production-ready** with comprehensive error handling and monitoring

#### Key Features

- 🔐 **JWT Token Management** - Secure token generation and rotation
- 🛡️ **Multi-Factor Authentication** - TOTP, SMS, and email verification
- 🌐 **Social Login** - Google, Facebook, and Apple integration
- 👥 **Multi-Tenancy** - Isolated tenant environments
- 🔒 **Security Controls** - Rate limiting, password policies, audit logs
- 📊 **Monitoring** - Health checks, metrics, and observability

#### API Endpoints

- **Authentication**: `/api/v1/auth/*`
- **Tenant Management**: `/api/v1/tenants/*`
- **User Management**: `/api/v1/users/*`
- **Health & Metrics**: `/health`, `/metrics`

## 🏢 Multi-Tenancy

WindWays supports multiple tenant resolution strategies:

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

## 🛡️ Security Features

- **Password Security** - Configurable strength requirements and history prevention
- **Rate Limiting** - Per-endpoint and user-based limiting
- **Account Protection** - Failed attempt tracking and progressive lockouts
- **Audit Logging** - Comprehensive security event logging
- **CSRF Protection** - Cross-site request forgery prevention
- **Security Headers** - HSTS, CSP, and other protective headers

## 📊 Monitoring & Observability

- **Health Checks** - Service status monitoring
- **Metrics Collection** - Performance and usage metrics
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Error Tracking** - Comprehensive error handling and reporting

## 🧪 Testing

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=auth_module --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m security
pytest -m performance
```

## 🚀 Deployment

### Production Deployment

```bash
# Build and deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

### Environment Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/windways_auth

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 📚 Documentation

- [Backend API Documentation](backend/README.md)
- [Authentication Module Guide](backend/auth_module/README.md)
- [Development Phases](dev-phases/)
- [API Reference](http://localhost:8000/docs) (when running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use Black for code formatting
- Write comprehensive tests
- Update documentation
- Follow semantic versioning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/windways/windways/wiki)
- **Issues**: [GitHub Issues](https://github.com/windways/windways/issues)
- **Discussions**: [GitHub Discussions](https://github.com/windways/windways/discussions)
- **Email**: support@windways.com

## 🗺️ Roadmap

### Phase 1: Authentication & Core Platform ✅
- [x] Multi-tenant authentication system
- [x] User management and authorization
- [x] Security controls and monitoring

### Phase 2: Search & Booking (In Progress)
- [ ] Provider integrations (Booking.com, Expedia)
- [ ] Search and filtering system
- [ ] Booking flow and affiliate tracking

### Phase 3: AI & Intelligence
- [ ] AI-powered trip planning
- [ ] Personalized recommendations
- [ ] Natural language search

### Phase 4: Multi-Tenant Business Features
- [ ] Agency portals and white-labeling
- [ ] Vendor management system
- [ ] Business operations and analytics

### Phase 5: Mobile & Advanced UX
- [ ] Progressive Web App
- [ ] Native mobile applications
- [ ] Advanced user experience features

---

**WindWays** - Where every journey finds its way! 🌪️✈️