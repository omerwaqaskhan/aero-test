#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from auth_module.infrastructure.db.models import TenantModel, UserModel
from auth_module.core.security import PasswordManager
import uuid

email = sys.argv[1] if len(sys.argv) > 1 else "admin@luftway.com"
password = sys.argv[2] if len(sys.argv) > 2 else "admin"
role = sys.argv[3] if len(sys.argv) > 3 else "super_admin"

db: Session = SessionLocal()
try:
    # Get or create tenant
    tenant = db.query(TenantModel).filter(TenantModel.slug == "luftway").first()
    if not tenant:
        tenant = TenantModel(id=uuid.uuid4(), slug="luftway", name="LuftWay", status="active", settings={}, branding={})
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"Created tenant: {tenant.id}")
    
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.tenant_id == tenant.id, UserModel.email == email).first()
    if user:
        user.role = role
        user.status = "active"
        user.email_verified = True
        user.password_hash = PasswordManager.hash_password(password)
        db.commit()
        print(f"Updated user: {email} -> {role}")
    else:
        user = UserModel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=email,
            password_hash=PasswordManager.hash_password(password),
            first_name="Admin",
            last_name="User",
            role=role,
            status="active",
            email_verified=True
        )
        db.add(user)
        db.commit()
        print(f"Created user: {email} -> {role}")
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    sys.exit(1)
finally:
    db.close()

