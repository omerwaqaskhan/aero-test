# Creating Admin Users

This guide explains how to create admin users to access admin pages in the LuftWay platform.

## Quick Start

### Using the Script (Recommended)

The easiest way to create an admin user is using the provided script:

```bash
# From project root
python scripts/create_admin_user.py
```

The script will:
1. Prompt you for email, password, name, and role
2. Create the default tenant if it doesn't exist
3. Create the admin user with the specified role
4. Set the user status to active and email as verified

### Available Roles

- **super_admin**: Full system access across all tenants
- **tenant_admin**: Tenant-level admin access (for managing a specific tenant)

## Manual Creation

### Option 1: Using Python Script Directly

```python
from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from auth_module.infrastructure.db.models import TenantModel, UserModel
from auth_module.core.security import PasswordManager
import uuid

db: Session = SessionLocal()

# Get or create tenant
tenant = db.query(TenantModel).filter(TenantModel.slug == "luftway").first()
if not tenant:
    tenant = TenantModel(
        id=uuid.uuid4(),
        slug="luftway",
        name="LuftWay",
        status="active",
        settings={},
        branding={}
    )
    db.add(tenant)
    db.commit()

# Create admin user
password_hash = PasswordManager.hash_password("your_password_here")
user = UserModel(
    id=uuid.uuid4(),
    tenant_id=tenant.id,
    email="admin@example.com",
    password_hash=password_hash,
    first_name="Admin",
    last_name="User",
    role="super_admin",  # or "tenant_admin"
    status="active",
    email_verified=True
)
db.add(user)
db.commit()
```

### Option 2: Using SQL (Direct Database)

```sql
-- First, get or create tenant (if needed)
INSERT INTO tenants (id, slug, name, status, settings, branding, created_at, updated_at) 
VALUES (
    gen_random_uuid(), 
    'luftway', 
    'LuftWay', 
    'active', 
    '{}', 
    '{}', 
    NOW(), 
    NOW()
) ON CONFLICT (slug) DO NOTHING;

-- Get tenant ID
SELECT id FROM tenants WHERE slug = 'luftway';

-- Create admin user (replace TENANT_ID with actual tenant ID from above)
-- Note: You'll need to hash the password using bcrypt first
INSERT INTO users (
    id, 
    tenant_id, 
    email, 
    password_hash, 
    first_name, 
    last_name, 
    role, 
    status, 
    email_verified, 
    created_at, 
    updated_at
) VALUES (
    gen_random_uuid(),
    'TENANT_ID',  -- Replace with actual tenant ID
    'admin@example.com',
    '$2b$12$...',  -- Replace with bcrypt hash of your password
    'Admin',
    'User',
    'super_admin',  -- or 'tenant_admin'
    'active',
    true,
    NOW(),
    NOW()
);
```

**Note**: For SQL method, you'll need to generate the bcrypt hash separately. You can use Python:

```python
import bcrypt
password = "your_password"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
print(hashed.decode('utf-8'))
```

## Using Docker

If you're running the application in Docker:

```bash
# Execute the script inside the backend container
docker compose exec backend python /app/scripts/create_admin_user.py

# Or copy the script and run it
docker compose cp scripts/create_admin_user.py backend:/app/scripts/
docker compose exec backend python /app/scripts/create_admin_user.py
```

## Verification

After creating the admin user, verify it was created correctly:

1. **Check the database**:
   ```sql
   SELECT email, role, status, email_verified FROM users WHERE email = 'admin@example.com';
   ```

2. **Try logging in**:
   - Go to the login page
   - Use the email and password you created
   - You should be able to access admin pages

3. **Check admin access**:
   - After logging in, you should see "Admin" and "Monitoring" links in the navigation
   - Visit `/admin` for revenue analytics
   - Visit `/monitoring` for scraper monitoring dashboard

## Troubleshooting

### User Created But Can't Access Admin Pages

1. **Check role**: Ensure the user has `super_admin` or `tenant_admin` role
   ```sql
   SELECT role FROM users WHERE email = 'your_email';
   ```

2. **Check status**: User must be `active`
   ```sql
   SELECT status FROM users WHERE email = 'your_email';
   ```

3. **Check email verification**: Should be `true`
   ```sql
   SELECT email_verified FROM users WHERE email = 'your_email';
   ```

4. **Clear browser cache**: Sometimes cached tokens can cause issues

### Script Fails with Database Connection Error

1. **Check database is running**:
   ```bash
   docker compose ps postgres
   ```

2. **Check DATABASE_URL** environment variable is correct

3. **Verify database migrations are run**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

### Password Hash Issues

If you're manually creating users and having password issues:

1. Use the `PasswordManager.hash_password()` method from the codebase
2. Ensure you're using bcrypt with 12 rounds (default)
3. The hash should start with `$2b$12$`

## Security Notes

- **Change default passwords**: Always change default passwords in production
- **Use strong passwords**: Minimum 8 characters, preferably with mixed case, numbers, and special characters
- **Limit admin access**: Only create admin users for trusted personnel
- **Regular audits**: Periodically review admin user list and remove unused accounts

## Updating Existing User to Admin

If you already have a user account and want to make it an admin:

```sql
UPDATE users 
SET role = 'super_admin', status = 'active', email_verified = true 
WHERE email = 'user@example.com';
```

Or use the script - it will detect existing users and offer to update them.

