"""Test script for email service configuration."""

import asyncio
import os
from auth_module.infrastructure.messaging import EmailService
from auth_module.core.config import config


async def test_email_configuration():
    """Test email service configuration."""
    print("=" * 60)
    print("Email Service Configuration Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking SMTP Configuration...")
    print(f"   SMTP Host: {config.smtp_host or 'NOT SET'}")
    print(f"   SMTP Port: {config.smtp_port}")
    print(f"   SMTP Username: {config.smtp_username or 'NOT SET'}")
    print(f"   SMTP Password: {'*' * len(config.smtp_password) if config.smtp_password else 'NOT SET'}")
    print(f"   SMTP Use TLS: {config.smtp_use_tls}")
    print(f"   From Email: {config.email_from}")
    print(f"   From Name: {config.email_from_name}")
    
    if not config.smtp_host:
        print("\n⚠️  WARNING: SMTP not configured!")
        print("   Set the following environment variables:")
        print("   - SMTP_HOST")
        print("   - SMTP_PORT (default: 587)")
        print("   - SMTP_USERNAME")
        print("   - SMTP_PASSWORD")
        print("   - EMAIL_FROM")
        print("   - EMAIL_FROM_NAME")
        return False
    
    # Test email service initialization
    print("\n2. Initializing Email Service...")
    try:
        email_service = EmailService()
        print("   ✅ Email service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize email service: {e}")
        return False
    
    # Test email sending (optional - only if configured)
    print("\n3. Testing Email Sending...")
    test_email = os.getenv("TEST_EMAIL", "test@example.com")
    
    if config.smtp_username and config.smtp_password:
        try:
            await email_service.send_email(
                to_email=test_email,
                subject="Test Email - Luftway",
                html_content="<h1>Test Email</h1><p>This is a test email from Luftway.</p>",
                text_content="Test Email\n\nThis is a test email from Luftway."
            )
            print(f"   ✅ Test email sent successfully to {test_email}")
            print("   Please check your inbox (and spam folder)")
        except Exception as e:
            print(f"   ❌ Failed to send test email: {e}")
            print("   This might be due to:")
            print("   - Incorrect SMTP credentials")
            print("   - Network/firewall issues")
            print("   - SMTP server configuration")
            return False
    else:
        print("   ⚠️  Skipping email send test (credentials not configured)")
    
    # Test email templates
    print("\n4. Testing Email Templates...")
    try:
        # Test verification email
        await email_service.send_verification_email(
            to_email=test_email,
            verification_token="test-token-12345"
        )
        print("   ✅ Verification email template works")
    except Exception as e:
        print(f"   ⚠️  Verification email template test: {e}")
    
    try:
        # Test password reset email
        await email_service.send_password_reset_email(
            to_email=test_email,
            reset_token="test-reset-token-12345"
        )
        print("   ✅ Password reset email template works")
    except Exception as e:
        print(f"   ⚠️  Password reset email template test: {e}")
    
    print("\n" + "=" * 60)
    print("Email Configuration Test Complete")
    print("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(test_email_configuration())


