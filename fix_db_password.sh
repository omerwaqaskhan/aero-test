#!/bin/bash
# Fix database password mismatch

echo "=========================================="
echo "🔧 Fixing Database Password Mismatch"
echo "=========================================="

# Try to connect and update password
# First, let's try with the default password that might have been used
NEW_PASSWORD="${POSTGRES_PASSWORD:-CHANGE_ME_STRONG_PASSWORD}"

echo "Attempting to update database password..."
echo "New password will be: $NEW_PASSWORD"

# Try to connect without password first (if database allows it)
docker compose exec -T postgres psql -U postgres <<EOF_SQL 2>/dev/null || true
ALTER USER luftway_user WITH PASSWORD '$NEW_PASSWORD';
EOF_SQL

# If that doesn't work, try with postgres superuser
docker compose exec -T postgres psql -U postgres -d postgres <<EOF_SQL 2>/dev/null || true
ALTER USER luftway_user WITH PASSWORD '$NEW_PASSWORD';
EOF_SQL

echo ""
echo "✅ Password update attempted"
echo ""
echo "If this didn't work, you may need to:"
echo "1. Know the current password and connect manually"
echo "2. Or reset the database (loses data): docker compose down -v"
echo ""
echo "After fixing, restart backend:"
echo "  docker compose restart backend"
