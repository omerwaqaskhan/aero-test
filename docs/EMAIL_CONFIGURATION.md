# Email Service Configuration Guide

## Overview

The email service is implemented and ready to use. This guide explains how to configure it.

## Configuration

### Environment Variables

Set the following environment variables in your `.env` file or `docker-compose.yml`:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com          # Your SMTP server hostname
SMTP_PORT=587                     # SMTP port (587 for TLS, 465 for SSL)
SMTP_USERNAME=your-email@gmail.com # Your SMTP username
SMTP_PASSWORD=your-app-password   # Your SMTP password (use app password for Gmail)
SMTP_USE_TLS=true                 # Enable TLS (true for port 587)

# Email Settings
EMAIL_FROM=noreply@windways.com   # Sender email address
EMAIL_FROM_NAME=WindWays          # Sender display name
```

### Gmail Configuration Example

For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password in `SMTP_PASSWORD`

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=WindWays
```

### Other Email Providers

#### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

#### AWS SES
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
SMTP_USE_TLS=true
```

#### Mailgun
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-username
SMTP_PASSWORD=your-mailgun-password
SMTP_USE_TLS=true
```

## Testing Email Configuration

### Using the Test Script

Run the email configuration test:

```bash
# In Docker
docker compose run --rm backend python auth_module/tests/email_config_test.py

# Or directly
cd backend
python -m auth_module.tests.email_config_test
```

### Manual Testing

You can test email sending by calling the email service directly:

```python
from auth_module.infrastructure.messaging import EmailService

email_service = EmailService()

# Test basic email
await email_service.send_email(
    to_email="test@example.com",
    subject="Test Email",
    html_content="<h1>Test</h1><p>This is a test email.</p>",
    text_content="Test\n\nThis is a test email."
)

# Test verification email
await email_service.send_verification_email(
    to_email="test@example.com",
    verification_token="test-token-12345"
)

# Test password reset email
await email_service.send_password_reset_email(
    to_email="test@example.com",
    reset_token="test-reset-token-12345"
)
```

## Email Templates

The email service includes templates for:

1. **Email Verification** - Sent when user registers
2. **Password Reset** - Sent when user requests password reset
3. **MFA Code** - Sent when user requests MFA code via email
4. **General Notifications** - For other notifications

## Troubleshooting

### Common Issues

1. **"SMTP not configured" error**
   - Check that `SMTP_HOST` is set
   - Verify all required environment variables are set

2. **Authentication failed**
   - Verify `SMTP_USERNAME` and `SMTP_PASSWORD` are correct
   - For Gmail, use App Password, not regular password
   - Check that 2FA is enabled (for Gmail)

3. **Connection timeout**
   - Check firewall settings
   - Verify SMTP host and port are correct
   - Try different port (587 vs 465)

4. **Emails going to spam**
   - Set up SPF, DKIM, and DMARC records
   - Use a verified sender domain
   - Avoid spam trigger words

## Production Recommendations

1. **Use a dedicated email service** (SendGrid, AWS SES, Mailgun)
2. **Set up SPF/DKIM/DMARC** records for your domain
3. **Monitor email delivery** rates
4. **Use email templates** for consistent branding
5. **Implement retry logic** for failed sends
6. **Log email events** for debugging

## Next Steps

1. Configure SMTP credentials in your environment
2. Test email sending using the test script
3. Test email verification flow end-to-end
4. Test password reset flow end-to-end
5. Monitor email delivery in production


