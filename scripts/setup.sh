#!/bin/bash

# Luftway Backend Setup Script
# This script sets up the development environment for the Luftway backend

set -e

echo "🚀 Setting up Luftway Backend..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r backend/requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Create .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "⚙️ Creating .env file..."
    # Use env.example as template if it exists, otherwise create from scratch
    if [ -f "env.example" ]; then
        echo "   📋 Using env.example as template..."
        cp env.example backend/.env
        echo "✅ .env file created from env.example. Please update the configuration values."
    else
        cat > backend/.env << EOF
# Database
DATABASE_URL=postgresql://luftway_user:luftway_password@localhost:5432/luftway_auth

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ISSUER=luftway-auth
JWT_AUDIENCE=luftway-api

# Password Security
PASSWORD_MIN_LENGTH=8
PASSWORD_MAX_LENGTH=128
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
PASSWORD_FORBIDDEN_PATTERNS=["password", "123456", "qwerty", "admin"]
PASSWORD_HISTORY_COUNT=5
BCRYPT_ROUNDS=12

# Rate Limiting
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=3/hour
RATE_LIMIT_FORGOT_PASSWORD=3/hour
RATE_LIMIT_MFA_VERIFY=10/minute
RATE_LIMIT_REFRESH_TOKEN=20/minute
RATE_LIMIT_TENANT_CREATION=5/hour

# Account Lockout
MAX_FAILED_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PROGRESSIVE_DELAY_ENABLED=true

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
EMAIL_FROM=noreply@luftway.com
EMAIL_FROM_NAME=Luftway

# SMS Configuration (optional)
SMS_PROVIDER=twilio
SMS_API_KEY=your-twilio-account-sid
SMS_API_SECRET=your-twilio-auth-token

# OAuth Configuration (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_TEAM_ID=your-apple-team-id
APPLE_KEY_ID=your-apple-key-id
APPLE_PRIVATE_KEY=your-apple-private-key

# Tenant Configuration
TENANT_RESOLUTION_STRATEGY=subdomain
DEFAULT_TENANT_SLUG=default
TENANT_SLUG_PATTERN=^[a-z0-9-]+$

# Security Headers
ENABLE_CSRF_PROTECTION=false
ENABLE_HSTS=true
ENABLE_CSP=true

# Monitoring & Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
ENABLE_METRICS=true

# Feature Flags
ENABLE_MFA=true
ENABLE_SOCIAL_LOGIN=true
ENABLE_PASSWORD_RESET=true
ENABLE_USER_REGISTRATION=true
ENABLE_TENANT_CREATION=true
EOF
        echo "✅ .env file created. Please update the configuration values."
    fi
    echo ""
    echo "⚠️  IMPORTANT: Update backend/.env with your actual configuration values!"
    echo "   - Generate JWT_SECRET_KEY: openssl rand -hex 32"
    echo "   - Set secure database passwords"
    echo "   - Configure email/SMS/OAuth if needed"
fi

# Create logs directory
mkdir -p logs

# Initialize Alembic if not already done
if [ ! -d "backend/auth_module/migrations/versions" ] || [ -z "$(ls -A backend/auth_module/migrations/versions)" ]; then
    echo "🗄️ Initializing Alembic migrations..."
    cd backend/auth_module
    alembic init migrations
    cd ../..
fi

# Run code formatting
echo "🎨 Formatting code..."
black backend/auth_module/
isort backend/auth_module/

# Run linting
echo "🔍 Running linting..."
flake8 backend/auth_module/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 backend/auth_module/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# Run type checking
echo "🔬 Running type checking..."
mypy backend/auth_module/ --ignore-missing-imports

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update the backend/.env file with your configuration"
echo "2. Start PostgreSQL and Redis services"
echo "3. Run migrations: cd backend && alembic upgrade head"
echo "4. Start the development server: cd backend && uvicorn auth_module.main:app --reload"
echo "5. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For Docker setup, run: docker-compose up --build"
echo ""
echo "Happy coding! 🚀"
