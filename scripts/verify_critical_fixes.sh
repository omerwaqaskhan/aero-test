#!/bin/bash
# Verification script for critical showstopper fixes
# This script verifies that all 6 critical fixes are properly implemented

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

check() {
    local name="$1"
    local command="$2"
    
    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Critical Showstopper Fixes Verification                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Fix 1: CORS Configuration
echo -e "${YELLOW}1. CORS Configuration${NC}"
check "CORS config in auth_module" "grep -q 'cors_origins' backend/auth_module/core/config.py"
check "CORS not allowing all origins in auth_module/main.py" "grep -q 'config.cors_origins' backend/auth_module/main.py && ! grep -q 'allow_origins=\[\"\\*\"\]' backend/auth_module/main.py"
check "CORS not allowing all origins in search_booking_module" "! grep -q 'allow_origins=\[\"\\*\"\]' backend/search_booking_module/main.py"

# Fix 2: SSL/TLS Setup
echo ""
echo -e "${YELLOW}2. SSL/TLS Certificates${NC}"
check "SSL setup script exists" "test -f scripts/setup_ssl.sh"
check "SSL setup script is executable" "test -x scripts/setup_ssl.sh"
check "Nginx HTTPS config exists" "grep -q 'ssl_certificate' nginx/nginx.conf"
check "SSL setup guide exists" "test -f scripts/SSL_SETUP_GUIDE.md"

# Fix 3: Sentry Integration
echo ""
echo -e "${YELLOW}3. Sentry Error Tracking${NC}"
check "Sentry SDK in requirements.txt" "grep -q 'sentry-sdk' backend/requirements.txt"
check "Sentry config in auth_module/config.py" "grep -q 'sentry_dsn' backend/auth_module/core/config.py"
check "Sentry initialization in auth_module/main.py" "grep -q 'sentry_sdk.init' backend/auth_module/main.py"
check "Sentry initialization in search_booking_module" "grep -q 'sentry_sdk.init' backend/search_booking_module/main.py"
check "Sentry setup guide exists" "test -f backend/SENTRY_SETUP_GUIDE.md"

# Fix 4: Enhanced Database Backups
echo ""
echo -e "${YELLOW}4. Automated Database Backups${NC}"
check "Enhanced backup script exists" "test -f backend/scripts/backup_database_enhanced.sh"
check "Enhanced backup script is executable" "test -x backend/scripts/backup_database_enhanced.sh"
check "Cron setup script exists" "test -f backend/scripts/setup_backup_cron.sh"
check "Cron setup script is executable" "test -x backend/scripts/setup_backup_cron.sh"
check "Backup guide exists" "test -f backend/scripts/BACKUP_SETUP_GUIDE.md"

# Fix 5: Frontend Testing
echo ""
echo -e "${YELLOW}5. Frontend Testing${NC}"
check "Vitest in package.json" "grep -q 'vitest' frontend/web-vite/package.json"
check "Testing Library in package.json" "grep -q '@testing-library/react' frontend/web-vite/package.json"
check "Vitest config exists" "test -f frontend/web-vite/vitest.config.js"
check "Test setup file exists" "test -f frontend/web-vite/src/test/setup.js"
check "Test files exist" "test -f frontend/web-vite/src/test/App.test.jsx"

# Fix 6: Environment Separation
echo ""
echo -e "${YELLOW}6. Environment Separation${NC}"
check "Development compose file exists" "test -f docker-compose.dev.yml"
check "Staging compose file exists" "test -f docker-compose.staging.yml"
check "Production compose file exists" "test -f docker-compose.prod.yml"
check "Environment setup guide exists" "test -f ENVIRONMENT_SETUP_GUIDE.md"
check "Production CORS configured" "grep -q 'CORS_ORIGINS' docker-compose.prod.yml"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Verification Summary                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total Checks: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: 0${NC}"
    echo ""
    echo -e "${GREEN}✅ All critical fixes verified successfully!${NC}"
    exit 0
fi

