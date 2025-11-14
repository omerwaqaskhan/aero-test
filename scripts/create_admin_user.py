#!/usr/bin/env python3
"""Script to create an admin user for the LuftWay platform."""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from auth_module.infrastructure.db.database import SessionLocal
from auth_module.infrastructure.db.models import TenantModel, UserModel
from auth_module.core.security import PasswordManager
import uuid


def get_or_create_default_tenant(db: Session) -> TenantModel:
    """Get or create the default tenant."""
    # Try to get existing tenant
    tenant = db.query(TenantModel).filter(TenantModel.slug == "luftway").first()
    
    if not tenant:
        print("Creating default tenant 'luftway'...")
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
        db.refresh(tenant)
        print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
    else:
        print(f"✓ Using existing tenant: {tenant.name} (ID: {tenant.id})")
    
    return tenant


def create_admin_user(
    db: Session,
    tenant: TenantModel,
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
    role: str = "super_admin"
):
    """Create an admin user."""
    # Check if user already exists
    existing_user = db.query(UserModel).filter(
        UserModel.tenant_id == tenant.id,
        UserModel.email == email
    ).first()
    
    if existing_user:
        print(f"⚠ User with email '{email}' already exists.")
        response = input("Do you want to update the role to admin? (y/n): ").strip().lower()
        if response == 'y':
            existing_user.role = role
            existing_user.status = "active"
            existing_user.email_verified = True
            
            # Update password if provided
            if password:
                existing_user.password_hash = PasswordManager.hash_password(password)
            
            db.commit()
            print(f"✓ Updated user '{email}' to role '{role}'")
            return existing_user
        else:
            print("Cancelled.")
            return None
    
    # Create new admin user
    print(f"Creating admin user '{email}'...")
    
    password_hash = PasswordManager.hash_password(password)
    
    user = UserModel(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        role=role,
        status="active",
        email_verified=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✓ Created admin user: {email}")
    print(f"  - Name: {first_name} {last_name}")
    print(f"  - Role: {role}")
    print(f"  - Status: {user.status}")
    print(f"  - Email Verified: {user.email_verified}")
    print(f"  - User ID: {user.id}")
    
    return user


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create an admin user for LuftWay')
    parser.add_argument('--email', type=str, help='Admin email address')
    parser.add_argument('--password', type=str, help='Admin password')
    parser.add_argument('--first-name', type=str, default='Admin', help='First name (default: Admin)')
    parser.add_argument('--last-name', type=str, default='User', help='Last name (default: User)')
    parser.add_argument('--role', type=str, default='super_admin', choices=['super_admin', 'tenant_admin'],
                       help='User role (default: super_admin)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LuftWay Admin User Creation Script")
    print("=" * 60)
    print()
    
    # Get user input (interactive if not provided via args)
    if args.email:
        email = args.email
    else:
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email is required")
            return 1
    
    if args.password:
        password = args.password
    else:
        password = input("Enter admin password: ").strip()
        if not password:
            print("❌ Password is required")
            return 1
    
    if len(password) < 8:
        print("⚠ Warning: Password is less than 8 characters")
        if not args.password:  # Only prompt if interactive
            response = input("Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                return 1
        else:
            print("⚠ Continuing with short password (non-interactive mode)")
    
    first_name = args.first_name or "Admin"
    last_name = args.last_name or "User"
    role = args.role or "super_admin"
    
    print()
    print("Creating admin user...")
    print()
    
    # Create database session
    db: Session = SessionLocal()
    try:
        # Get or create default tenant
        tenant = get_or_create_default_tenant(db)
        print()
        
        # Create admin user
        user = create_admin_user(
            db=db,
            tenant=tenant,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        
        if user:
            print()
            print("=" * 60)
            print("✓ Admin user created successfully!")
            print("=" * 60)
            print()
            print("You can now log in with:")
            print(f"  Email: {email}")
            print(f"  Password: [the password you entered]")
            print()
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

