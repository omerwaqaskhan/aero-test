# OAuth Social Login Setup Guide

This guide will help you set up Google and Facebook OAuth for the WindWays authentication system.

## 🚀 Implementation Summary

The social login functionality has been fully implemented with the following features:

### Backend Implementation ✅
- **OAuth Service**: Complete OAuth verification for Google, Facebook, and Apple
- **AuthService**: Social login methods for user creation and authentication
- **API Endpoints**: Updated `/api/v1/auth/social/{provider}` endpoint
- **Security**: Rate limiting, audit logging, and error handling

### Frontend Implementation ✅
- **OAuth Utility**: Google and Facebook SDK integration
- **Social Components**: Updated login and register components
- **Auth Context**: Social login state management
- **Error Handling**: Comprehensive error handling with user-friendly messages

## 📋 Setup Instructions

### 1. Google OAuth Setup

#### Step 1: Create Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized origins:
   - `http://localhost:3000` (development)
   - `http://localhost:3002` (development direct)
   - Your production domain
7. Add authorized redirect URIs:
   - `http://localhost:3000` (development)
   - Your production domain

#### Step 2: Configure Environment Variables
Update your environment files:

**Backend (.env):**
```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

**Frontend (.env.development & .env.production):**
```bash
VITE_GOOGLE_CLIENT_ID=your-google-client-id-here
```

### 2. Facebook OAuth Setup

#### Step 1: Create Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add "Facebook Login" product
4. Configure Facebook Login:
   - Valid OAuth Redirect URIs:
     - `http://localhost:3000` (development)
     - Your production domain
   - App Domains: Add your domains
5. Get your App ID and App Secret

#### Step 2: Configure Environment Variables
Update your environment files:

**Backend (.env):**
```bash
# Facebook OAuth
FACEBOOK_CLIENT_ID=your-facebook-app-id-here
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret-here
```

**Frontend (.env.development & .env.production):**
```bash
VITE_FACEBOOK_APP_ID=your-facebook-app-id-here
```

### 3. Backend Configuration

#### Update Docker Compose Environment
Add OAuth variables to your `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      # ... existing variables ...
      
      # OAuth Configuration
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      FACEBOOK_CLIENT_ID: ${FACEBOOK_CLIENT_ID}
      FACEBOOK_CLIENT_SECRET: ${FACEBOOK_CLIENT_SECRET}
```

#### Create .env file in project root:
```bash
# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
FACEBOOK_CLIENT_ID=your-facebook-app-id-here
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret-here
```

### 4. Frontend Configuration

The frontend is already configured to use the environment variables. Just update the values in:
- `frontend/web-vite/.env.development`
- `frontend/web-vite/.env.production`

### 5. Testing the Implementation

#### Start the Services
```bash
# Start all services
docker compose up

# Or start individual services
docker compose up backend frontend nginx
```

#### Test Social Login
1. Navigate to `http://localhost/login` or `http://localhost/register`
2. Click on "Google" or "Facebook" buttons
3. Complete the OAuth flow
4. Verify successful login/registration

## 🔧 API Endpoints

### Social Login Endpoint
```
POST /api/v1/auth/social/{provider}
```

**Parameters:**
- `provider`: `google` or `facebook`
- `tenant_slug`: Tenant identifier (default: "windways")
- `access_token`: OAuth access token from provider
- `device_info`: Optional device information

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "user",
      "status": "active",
      "email_verified": true,
      "mfa_enabled": false,
      "last_login": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    "tokens": {
      "access_token": "jwt-token",
      "refresh_token": "refresh-token",
      "expires_in": 3600
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

## 🛡️ Security Features

### Rate Limiting
- Social login attempts are rate limited
- Prevents abuse and brute force attacks

### Audit Logging
- All social login attempts are logged
- Includes provider, success/failure, and user details

### Token Verification
- OAuth tokens are verified with provider APIs
- Invalid tokens are rejected immediately

### Error Handling
- Comprehensive error messages
- User-friendly error display
- Detailed logging for debugging

## 🚨 Troubleshooting

### Common Issues

#### 1. "Google OAuth not configured" Error
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Verify the environment variables are loaded correctly

#### 2. "Facebook OAuth not configured" Error
- Check that `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET` are set
- Verify the environment variables are loaded correctly

#### 3. "Invalid redirect URI" Error
- Check that your redirect URIs match exactly in the OAuth provider settings
- Ensure the domain is added to authorized origins

#### 4. Frontend OAuth Scripts Not Loading
- Check browser console for script loading errors
- Verify that the OAuth provider scripts are accessible
- Check network connectivity

#### 5. CORS Issues
- Ensure your frontend domain is added to OAuth provider settings
- Check that the backend CORS configuration allows your frontend domain

### Debug Mode
Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

## 📚 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login/)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)

## 🎯 Next Steps

1. **Configure OAuth Providers**: Set up Google and Facebook OAuth apps
2. **Update Environment Variables**: Add your OAuth credentials
3. **Test the Implementation**: Verify social login works correctly
4. **Deploy to Production**: Update production environment variables
5. **Monitor Usage**: Check logs for any issues or errors

The social login implementation is now complete and ready for use! 🚀
